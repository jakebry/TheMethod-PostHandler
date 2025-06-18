import React from 'react';
import Header from './components/Header';
import PostsFeed from './components/PostsFeed';
import './index.css';

function App() {
  return (
    <div className="min-h-screen bg-navy-gradient">
      {/* Background Pattern */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-72 h-72 bg-blue-600 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute top-0 right-1/4 w-72 h-72 bg-orange-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/3 w-72 h-72 bg-white rounded-full mix-blend-multiply filter blur-xl opacity-10 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10">
        <Header />
        <main className="max-w-2xl mx-auto px-4 py-8">
          <PostsFeed />
        </main>
      </div>
    </div>
  );
}

export default App