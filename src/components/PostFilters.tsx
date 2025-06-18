import React from 'react';
import { Search, Filter, Calendar, User, X } from 'lucide-react';
import { PostFilters, PostSort } from '../types';

interface PostFiltersProps {
  filters: PostFilters;
  sort: PostSort;
  onFiltersChange: (filters: Partial<PostFilters>) => void;
  onSortChange: (sort: PostSort) => void;
  onClearFilters: () => void;
  authors: string[];
}

const PostFiltersComponent: React.FC<PostFiltersProps> = ({
  filters,
  sort,
  onFiltersChange,
  onSortChange,
  onClearFilters,
  authors
}) => {
  const hasActiveFilters = Object.values(filters).some(value => value);

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg border border-gray-700 p-4 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-5 h-5 text-gray-400" />
        <h2 className="font-semibold text-white">Filters & Sorting</h2>
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="ml-auto flex items-center gap-1 text-sm text-red-400 hover:text-red-300 transition-colors"
          >
            <X className="w-4 h-4" />
            Clear All
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search posts..."
            value={filters.searchTerm || ''}
            onChange={(e) => onFiltersChange({ searchTerm: e.target.value || undefined })}
            className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white placeholder-gray-400"
          />
        </div>

        {/* Author Filter */}
        <div className="relative">
          <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={filters.author || ''}
            onChange={(e) => onFiltersChange({ author: e.target.value || undefined })}
            className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none text-white"
          >
            <option value="">All authors</option>
            {authors.map((author) => (
              <option key={author} value={author}>
                {author}
              </option>
            ))}
          </select>
        </div>

        {/* Date From */}
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="date"
            value={filters.dateFrom || ''}
            onChange={(e) => onFiltersChange({ dateFrom: e.target.value || undefined })}
            className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
          />
        </div>

        {/* Date To */}
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="date"
            value={filters.dateTo || ''}
            onChange={(e) => onFiltersChange({ dateTo: e.target.value || undefined })}
            className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
          />
        </div>
      </div>

      {/* Sorting */}
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-700">
        <span className="text-sm font-medium text-gray-300">Sort by:</span>
        <div className="flex items-center gap-2">
          <select
            value={sort.field}
            onChange={(e) => onSortChange({ ...sort, field: e.target.value as PostSort['field'] })}
            className="bg-gray-700 border border-gray-600 rounded-md px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
          >
            <option value="posted_at">Posted Date</option>
            <option value="created_at">Created Date</option>
            <option value="author">Author</option>
          </select>
          <select
            value={sort.order}
            onChange={(e) => onSortChange({ ...sort, order: e.target.value as PostSort['order'] })}
            className="bg-gray-700 border border-gray-600 rounded-md px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent text-white"
          >
            <option value="desc">Newest First</option>
            <option value="asc">Oldest First</option>
          </select>
        </div>
      </div>
    </div>
  );
};

export default PostFiltersComponent;