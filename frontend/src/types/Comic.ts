
export interface Comic {
  num: number;
  title: string;
  alt: string | null;
  image_url: string;
  comic_url: string;

  year: number | string;
  month: number | string;
  day: number | string;
  relevance: number;
}

export interface ComicSearchResponse {
  query: string;
  page: number;
  limit: number;
  total: number;
  results: Comic[];
}