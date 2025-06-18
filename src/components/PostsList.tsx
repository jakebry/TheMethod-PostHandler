import React, { useEffect, useMemo } from 'react';
import { ChevronDown, RefreshCw, MessageSquare } from 'lucide-react';
import { usePosts } from '../hooks/usePosts';
import PostCard from './PostCard';
import PostFiltersComponent from './PostFilters';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

const PostsList: React.FC = () => {
  const {
    posts,
    loading,
    error,
    hasMore,
    total,
    filters,
    sort,
    loadMore,
    refresh,
    updateFilters,
    updateSort
  } = usePosts({ 
    initialLimit: 12, 
    autoRefresh: true, 
    refreshInterval: 60000 
  });

  // Extract unique authors for filter dropdown
  const authors = useMemo(() => {
    const uniqueAuthors = Array.from(new Set(posts.map(post => post.author)));
    return uniqueAuthors.sort();
  }, [posts]);

  const handleClearFilters = () => {
    updateFilters({
      author: undefined,
      searchTerm: undefined,
      dateFrom: undefined,
      dateTo: undefined
    });
  };

  // Intersection Observer for infinite scrolling
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    const loadMoreElement = document.getElementById('load-more-trigger');
    if (loadMoreElement) {
      observer.observe(loadMoreElement);
    }

    return () => observer.disconnect();
  }, [hasMore, loading, loadMore]);

  if (error && posts.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <ErrorMessage message={error} onRetry={refresh} />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Posts Feed</h1>
          <p className="text-gray-400">
            {total > 0 ? `Showing ${posts.length} of ${total} posts` : 'No posts found'}
          </p>
        </div>
        <button
          onClick={refresh}
          disabled={loading}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <PostFiltersComponent
        filters={filters}
        sort={sort}
        authors={authors}
        onFiltersChange={updateFilters}
        onSortChange={updateSort}
        onClearFilters={handleClearFilters}
      />

      {/* Posts Grid */}
      {posts.length > 0 ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>

          {/* Load More Trigger */}
          {hasMore && (
            <div id="load-more-trigger" className="flex justify-center py-8">
              {loading ? (
                <LoadingSpinner size="lg" />
              ) : (
                <button
                  onClick={loadMore}
                  className="flex items-center gap-2 bg-gray-700 text-gray-200 px-6 py-3 rounded-lg hover:bg-gray-600 transition-colors"
                >
                  <ChevronDown className="w-5 h-5" />
                  Load More Posts
                </button>
              )}
            </div>
          )}

          {/* End of Results */}
          {!hasMore && posts.length > 0 && (
            <div className="text-center py-8 text-gray-400">
              <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>You've reached the end of the posts!</p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-16">
          {loading ? (
            <LoadingSpinner size="lg" />
          ) : (
            <div className="text-gray-400">
              <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <h3 className="text-xl font-semibold mb-2 text-gray-300">No posts found</h3>
              <p>Try adjusting your filters or check back later for new content.</p>
            </div>
          )}
        </div>
      )}

      {/* Error Toast */}
      {error && posts.length > 0 && (
        <div className="fixed bottom-4 right-4 bg-red-700 text-white px-4 py-3 rounded-lg shadow-lg border border-red-600">
          <p className="font-medium">Error loading more posts</p>
          <p className="text-sm opacity-90">{error}</p>
        </div>
      )}
    </div>
  );
};

export default PostsList;