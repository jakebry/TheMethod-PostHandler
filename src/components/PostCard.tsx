import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Calendar, Image as ImageIcon } from 'lucide-react';
import { Post } from '../types';

interface PostCardProps {
  post: Post;
}

const PostCard: React.FC<PostCardProps> = ({ post }) => {
  const [imageLoadErrors, setImageLoadErrors] = useState<Set<string>>(new Set());
  const [expandedImages, setExpandedImages] = useState<Set<string>>(new Set());

  const handleImageError = (imageUrl: string) => {
    setImageLoadErrors(prev => new Set([...prev, imageUrl]));
  };

  const toggleImageExpansion = (imageUrl: string) => {
    setExpandedImages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(imageUrl)) {
        newSet.delete(imageUrl);
      } else {
        newSet.add(imageUrl);
      }
      return newSet;
    });
  };

  const validImages = post.image_urls?.filter(url => !imageLoadErrors.has(url)) || [];

  return (
    <article className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-6 hover:shadow-xl hover:border-gray-600 transition-all duration-200">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex-1">
          <h3 className="font-semibold text-white">{post.author}</h3>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Calendar className="w-4 h-4" />
            <time dateTime={post.posted_at}>
              {formatDistanceToNow(new Date(post.posted_at), { addSuffix: true })}
            </time>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mb-4">
        <p className="text-gray-100 leading-relaxed whitespace-pre-wrap">
          {post.content}
        </p>
      </div>

      {/* Images */}
      {validImages.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <ImageIcon className="w-4 h-4" />
            <span>{validImages.length} image{validImages.length > 1 ? 's' : ''}</span>
          </div>
          
          <div className={`grid gap-3 ${
            validImages.length === 1 ? 'grid-cols-1' : 
            validImages.length === 2 ? 'grid-cols-2' : 
            'grid-cols-2 md:grid-cols-3'
          }`}>
            {validImages.map((imageUrl, index) => {
              const isExpanded = expandedImages.has(imageUrl);
              return (
                <div key={index} className="relative group">
                  <img
                    src={imageUrl}
                    alt={`Post image ${index + 1}`}
                    className={`
                      w-full rounded-lg cursor-pointer transition-all duration-300
                      ${isExpanded ? 'max-h-none' : 'max-h-48 object-cover'}
                      hover:brightness-110
                    `}
                    onError={() => handleImageError(imageUrl)}
                    onClick={() => toggleImageExpansion(imageUrl)}
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 rounded-lg transition-all duration-200 pointer-events-none" />
                  
                  {!isExpanded && (
                    <button
                      onClick={() => toggleImageExpansion(imageUrl)}
                      className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white px-2 py-1 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                    >
                      Expand
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="text-xs text-gray-500">
          Posted: {new Date(post.posted_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          })}
        </div>
      </div>
    </article>
  );
};

export default PostCard;