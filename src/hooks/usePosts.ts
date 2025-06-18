import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabase';
import { Post, PostFilters, PostSort, PaginationOptions, PostsResponse } from '../types';

interface UsePostsOptions {
  initialLimit?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const usePosts = (options: UsePostsOptions = {}) => {
  const { initialLimit = 10, autoRefresh = false, refreshInterval = 30000 } = options;
  
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);
  
  const [filters, setFilters] = useState<PostFilters>({});
  const [sort, setSort] = useState<PostSort>({ field: 'posted_at', order: 'desc' });
  const [pagination, setPagination] = useState<PaginationOptions>({ page: 1, limit: initialLimit });

  const fetchPosts = useCallback(async (reset = false) => {
    try {
      setLoading(true);
      setError(null);

      let query = supabase
        .from('posts')
        .select('*', { count: 'exact' });

      // Apply filters
      if (filters.author) {
        query = query.eq('author', filters.author);
      }
      
      if (filters.searchTerm) {
        query = query.ilike('content', `%${filters.searchTerm}%`);
      }
      
      if (filters.dateFrom) {
        query = query.gte('posted_at', filters.dateFrom);
      }
      
      if (filters.dateTo) {
        query = query.lte('posted_at', filters.dateTo);
      }

      // Apply sorting
      query = query.order(sort.field, { ascending: sort.order === 'asc' });

      // Apply pagination
      const from = reset ? 0 : (pagination.page - 1) * pagination.limit;
      const to = from + pagination.limit - 1;
      query = query.range(from, to);

      const { data, count, error: fetchError } = await query;

      if (fetchError) throw fetchError;

      const newPosts = data || [];
      
      if (reset) {
        setPosts(newPosts);
      } else {
        setPosts(prev => [...prev, ...newPosts]);
      }
      
      setTotal(count || 0);
      setHasMore(newPosts.length === pagination.limit);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch posts');
    } finally {
      setLoading(false);
    }
  }, [filters, sort, pagination]);

  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      setPagination(prev => ({ ...prev, page: prev.page + 1 }));
    }
  }, [loading, hasMore]);

  const refresh = useCallback(() => {
    setPagination({ page: 1, limit: pagination.limit });
    fetchPosts(true);
  }, [fetchPosts, pagination.limit]);

  const updateFilters = useCallback((newFilters: Partial<PostFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setPagination({ page: 1, limit: pagination.limit });
  }, [pagination.limit]);

  const updateSort = useCallback((newSort: PostSort) => {
    setSort(newSort);
    setPagination({ page: 1, limit: pagination.limit });
  }, [pagination.limit]);

  // Initial load and dependency changes
  useEffect(() => {
    fetchPosts(pagination.page === 1);
  }, [fetchPosts]);

  // Auto-refresh setup
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, refresh]);

  // Real-time subscriptions
  useEffect(() => {
    const channel = supabase
      .channel('posts_changes')
      .on('postgres_changes', { 
        event: '*', 
        schema: 'public', 
        table: 'posts' 
      }, () => {
        refresh();
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [refresh]);

  return {
    posts,
    loading,
    error,
    hasMore,
    total,
    filters,
    sort,
    pagination,
    loadMore,
    refresh,
    updateFilters,
    updateSort
  };
};