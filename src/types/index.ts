export interface Post {
  id: string;
  author: string;
  content: string;
  image_urls: string[];
  posted_at: string;
  created_at: string;
  updated_at: string;
}

export interface PostsResponse {
  data: Post[];
  count: number;
  hasMore: boolean;
}

export interface PostFilters {
  author?: string;
  searchTerm?: string;
  dateFrom?: string;
  dateTo?: string;
}

export interface PostSort {
  field: 'posted_at' | 'created_at' | 'author';
  order: 'asc' | 'desc';
}

export interface PaginationOptions {
  page: number;
  limit: number;
}