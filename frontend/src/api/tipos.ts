export type Paginado<T> = {
  count: number;
  total_pages: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
