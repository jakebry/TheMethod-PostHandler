import React from 'react';
import { usePosts } from '../hooks/usePosts';
import InstagramPost from './InstagramPost';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

const PostsFeed: React.FC = () => {
  const {
    posts,
    loading,
    error,
    hasMore,
    loadMore,
    refresh
  } = usePosts({ 
    initialLimit: 10, 
    autoRefresh: true, 
    refreshInterval: 60000 
  });

  if (error && posts.length === 0) {
    return <ErrorMessage message={error} onRetry={refresh} />;
  }

  return (
    <div className="space-y-8">
      {posts.map((post, index) => (
        <InstagramPost key={post.id} post={post} index={index} />
      ))}
      
      {loading && (
        <div className="flex justify-center py-8">
          <LoadingSpinner size="lg" />
        </div>
      )}
      
      {hasMore && !loading && (
        <div className="flex justify-center">
          <button
            onClick={loadMore}
            className="btn-orange shadow-glow-orange"
          >
            Load More Posts
          </button>
        </div>
      )}
      
      {!hasMore && posts.length > 0 && (
        <div className="text-center py-8">
          <p className="text-gray-300">You're all caught up!</p>
        </div>
      )}
    </div>
  );
};

export default PostsFeed;