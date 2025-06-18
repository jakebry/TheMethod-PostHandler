import React, { useState } from 'react';
import { MoreHorizontal } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Post } from '../types';

interface InstagramPostProps {
  post: Post;
  index: number;
}

const InstagramPost: React.FC<InstagramPostProps> = ({ post, index }) => {
  const [showFullContent, setShowFullContent] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  const nextImage = () => {
    setCurrentImageIndex((prev) => 
      prev === post.image_urls.length - 1 ? 0 : prev + 1
    );
  };

  const prevImage = () => {
    setCurrentImageIndex((prev) => 
      prev === 0 ? post.image_urls.length - 1 : prev - 1
    );
  };

  const truncatedContent = post.content.length > 150 
    ? post.content.substring(0, 150) + '...' 
    : post.content;

  return (
    <article className="card-navy-dark overflow-hidden shadow-glow-navy group hover:shadow-glow-orange transition-all duration-500 hover:scale-[1.02]">
      {/* Header */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center space-x-3">
          <div>
            <h3 className="font-semibold text-white">{post.author}</h3>
            <p className="text-xs text-gray-300">
              {formatDistanceToNow(new Date(post.posted_at), { addSuffix: true })}
            </p>
          </div>
        </div>
        <button className="p-2 rounded-full hover:bg-white/10 transition-all duration-300">
          <MoreHorizontal className="w-5 h-5 text-gray-300" />
        </button>
      </div>

      {/* Images */}
      {post.image_urls && post.image_urls.length > 0 && (
        <div className="relative aspect-square bg-gradient-to-br from-slate-800 to-slate-900">
          <img
            src={post.image_urls[currentImageIndex]}
            alt={`Post image ${currentImageIndex + 1}`}
            className="w-full h-full object-cover"
            loading="lazy"
          />
          
          {/* Image Navigation */}
          {post.image_urls.length > 1 && (
            <>
              <button
                onClick={prevImage}
                className="absolute left-2 top-1/2 transform -translate-y-1/2 w-8 h-8 rounded-full bg-blue-900/70 backdrop-blur-sm flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-all duration-300 hover:bg-orange-500/70"
              >
                ‹
              </button>
              <button
                onClick={nextImage}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 w-8 h-8 rounded-full bg-blue-900/70 backdrop-blur-sm flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-all duration-300 hover:bg-orange-500/70"
              >
                ›
              </button>
              
              {/* Dots Indicator */}
              <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-1">
                {post.image_urls.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentImageIndex(idx)}
                    className={`w-2 h-2 rounded-full transition-all duration-300 ${
                      idx === currentImageIndex 
                        ? 'bg-orange-400' 
                        : 'bg-white/50 hover:bg-white/70'
                    }`}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Content */}
      <div className="px-4 py-4">
        <div className="text-white leading-relaxed">
          <span className="font-semibold mr-2 text-orange-300">{post.author}</span>
          <span className="text-gray-100">
            {showFullContent ? post.content : truncatedContent}
            {post.content.length > 150 && (
              <button
                onClick={() => setShowFullContent(!showFullContent)}
                className="text-orange-400 ml-1 hover:text-orange-300 transition-colors font-medium"
              >
                {showFullContent ? 'less' : 'more'}
              </button>
            )}
          </span>
        </div>
      </div>
    </article>
  );
};

export default InstagramPost;