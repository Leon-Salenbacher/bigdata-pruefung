
import type { ComicSearchResponse } from "../types/Comic";

export async function searchComics(
    query: string,
    page = 1,
    limit = 20,
    signal?:AbortSignal
): Promise<ComicSearchResponse> {
  const params = new URLSearchParams({
    q: query,
    page: String(page),
    limit: String(limit)
  });

  const response = await fetch(
    `/api/comics/search?${params}`,
    { signal }
  );

  if (!response.ok) {
    throw new Error(
      `Search failed: ${response.status}`
    );
  }
  return response.json()
}
