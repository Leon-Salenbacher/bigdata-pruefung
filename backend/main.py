
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://xkcd:xkcd_dev_password@postgres:5432/xkcd",
)

pool = AsyncConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,
    open=False,
    kwargs={"row_factory": dict_row},
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open(wait=True)
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(
    title="XKCD Search API",
    description="Searchable XKCD comic database",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/api/health")
async def health():
    async with pool.connection() as conn:
        await conn.execute("SELECT 1")

    return {"status": "ok"}


@app.get("/api/comics/search")
async def search_comics(
    q: str = Query(min_length=1, max_length=200),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    offset = (page - 1) * limit

    search_query = """
        WITH query AS (
            SELECT websearch_to_tsquery(
                'english', %s
            ) AS tsq
        )
        SELECT
            c.id,
            c.title,
            c.alt,
            c.image_url,
            c.comic_url,
            c.year,
            c.month,
            c.day,
            ts_rank(
                to_tsvector(
                    'english',
                    COALESCE(c.search_text, '')
                ),
                query.tsq
            ) AS relevance
        FROM comics AS c
        CROSS JOIN query
        WHERE to_tsvector(
            'english',
            COALESCE(c.search_text, '')
        ) @@ query.tsq
        ORDER BY relevance DESC, c.id DESC
        LIMIT %s OFFSET %s
    """

    count_query = """
        SELECT COUNT(*) AS total
        FROM comics
        WHERE to_tsvector(
            'english',
            COALESCE(search_text, '')
        ) @@ websearch_to_tsquery('english', %s)
    """

    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                count_query, (q,)
            )
            total = (await cursor.fetchone())["total"]

            await cursor.execute(
                search_query,
                (q, limit, offset),
            )
            results = await cursor.fetchall()

    return {
        "query": q,
        "page": page,
        "limit": limit,
        "total": total,
        "results": results,
    }


@app.get("/api/comics/{comic_id}")
async def get_comic(comic_id: int):
    query = """
        SELECT
            id,
            title,
            safe_title,
            alt,
            transcript,
            image_url,
            comic_url,
            year,
            month,
            day
        FROM comics
        WHERE id = %s
    """

    async with pool.connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, (comic_id,))
            comic = await cursor.fetchone()

    if comic is None:
        raise HTTPException(
            status_code=404,
            detail="Comic not found",
        )

    return comic
