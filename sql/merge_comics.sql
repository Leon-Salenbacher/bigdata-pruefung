
BEGIN;

-- Abort if staging is empty
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM comics_staging
    ) THEN
        RAISE EXCEPTION 'Staging table is empty';
    END IF;
END;
$$;

INSERT INTO comics (
    id,
    year,
    month,
    day,
    title,
    safe_title,
    alt,
    transcript,
    image_url,
    comic_url,
    search_text
)
SELECT
    id,
    year,
    month,
    day,
    title,
    safe_title,
    alt,
    transcript,
    image_url,
    comic_url,
    search_text
FROM comics_staging

ON CONFLICT (id)
DO UPDATE SET
    year = EXCLUDED.year,
    month = EXCLUDED.month,
    day = EXCLUDED.day,
    title = EXCLUDED.title,
    safe_title = EXCLUDED.safe_title,
    alt = EXCLUDED.alt,
    transcript = EXCLUDED.transcript,
    image_url = EXCLUDED.image_url,
    comic_url = EXCLUDED.comic_url,
    search_text = EXCLUDED.search_text;

COMMIT;
