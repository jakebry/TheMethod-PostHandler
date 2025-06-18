import React, { useState } from 'react';
import { Search, Menu } from 'lucide-react';
import GlitchyTitle from './GlitchyTitle';

const Header: React.FC = () => {
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  return (
    <header className="sticky top-0 z-50 glass-navy border-b border-white/10">
      <div className="max-w-6xl mx-auto px-4">
        <div className="grid grid-cols-3 items-center h-16 gap-4">
          {/* Logo - Left section */}
          <div className="flex items-center justify-start">
            <GlitchyTitle 
              text="jakes parser" 
              className=""
            />
          </div>

          {/* Search Bar - Center section (truly centered) */}
          <div className="flex justify-center">
            <div className={`relative transition-all duration-300 w-full max-w-md ${isSearchFocused ? 'scale-105' : ''}`}>
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-300" />
              <input
                type="text"
                placeholder="Search"
                className="w-full pl-10 pr-4 py-3 rounded-2xl backdrop-blur-md bg-blue-900/20 border border-white/30 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-orange-400/50 focus:border-orange-400/50 transition-all duration-300"
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
              />
            </div>
          </div>

          {/* Actions - Right section */}
          <div className="flex items-center justify-end">
            <button className="p-2 rounded-full hover:bg-white/10 transition-all duration-300 group">
              <Menu className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;