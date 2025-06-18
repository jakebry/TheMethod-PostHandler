import React, { useState, useEffect } from 'react';
import '../styles/glitchy-title.css';

interface GlitchyTitleProps {
  text: string;
  className?: string;
}

const GlitchyTitle: React.FC<GlitchyTitleProps> = ({ text, className = '' }) => {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isGlitching, setIsGlitching] = useState(false);
  const [showCursor, setShowCursor] = useState(true);

  useEffect(() => {
    const typeInterval = setInterval(() => {
      if (currentIndex < text.length) {
        // Random glitch effect
        if (Math.random() < 0.12) {
          setIsGlitching(true);
          setTimeout(() => setIsGlitching(false), 80);
        }
        
        setDisplayText(text.substring(0, currentIndex + 1));
        setCurrentIndex(prev => prev + 1);
      } else {
        clearInterval(typeInterval);
      }
    }, 120 + Math.random() * 80);

    return () => clearInterval(typeInterval);
  }, [text, currentIndex]);

  const glitchChars = ['█', '▓', '▒', '░', '▪', '▫', '◘', '◙', '○', '●', '0', '1'];
  const getRandomGlitchChar = () => glitchChars[Math.floor(Math.random() * glitchChars.length)];

  return (
    <div className={`glitchy-title-container ${className}`}>
      <div className="glitchy-title-inner">
        {/* Main text */}
        <span className={`glitchy-title-text ${isGlitching ? 'glitching' : ''}`}>
          {displayText}
          {(currentIndex < text.length || showCursor) && (
            <span className={`glitchy-title-cursor ${showCursor ? 'visible' : 'hidden'}`}>
              |
            </span>
          )}
        </span>

        {/* Glitch overlay effects */}
        {isGlitching && (
          <>
            <span className="glitch-overlay-red">
              {displayText.split('').map((char, i) => (
                <span key={`red-${i}`}>
                  {Math.random() < 0.25 ? getRandomGlitchChar() : char}
                </span>
              ))}
            </span>
            <span className="glitch-overlay-blue">
              {displayText.split('').map((char, i) => (
                <span key={`blue-${i}`}>
                  {Math.random() < 0.25 ? getRandomGlitchChar() : char}
                </span>
              ))}
            </span>
          </>
        )}
      </div>

      {/* Matrix-style background effect */}
      <div className="matrix-background">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="matrix-char"
            style={{
              left: `${Math.random() * 80}%`,
              top: `${Math.random() * 80}%`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${1.5 + Math.random() * 1.5}s`
            }}
          >
            {Math.random() < 0.5 ? '0' : '1'}
          </div>
        ))}
      </div>
    </div>
  );
};

export default GlitchyTitle;