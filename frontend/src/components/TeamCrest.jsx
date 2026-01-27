import { memo, useState } from 'react';

/**
 * TeamCrest Component
 * 
 * Displays team/club crests from Football-Data.org with fallback to placeholder SVG.
 * 
 * Football-Data.org crest URL pattern: https://crests.football-data.org/{apiFootballId}.svg
 * 
 * Sizes:
 * - small: 32px (for auction queue)
 * - thumbnail: 48x48px (for lists)
 * - medium: 64px
 * - large: 96px  
 * - watermark: 300px (for hero section background)
 */

// Default placeholder SVG - a generic shield icon
const PlaceholderShield = ({ size = 48, color = '#94A3B8', className = '' }) => (
  <svg 
    width={size} 
    height={size} 
    viewBox="0 0 48 48" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    {/* Shield outline */}
    <path 
      d="M24 4L6 12V22C6 33.1 13.7 43.3 24 46C34.3 43.3 42 33.1 42 22V12L24 4Z" 
      stroke={color}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="none"
    />
    {/* Inner shield decoration */}
    <path 
      d="M24 10L12 15V22C12 29.7 17.2 36.6 24 39C30.8 36.6 36 29.7 36 22V15L24 10Z" 
      stroke={color}
      strokeWidth="1.5"
      strokeOpacity="0.5"
      fill="none"
    />
    {/* Center star */}
    <path 
      d="M24 18L25.5 23H30.5L26.5 26L28 31L24 28L20 31L21.5 26L17.5 23H22.5L24 18Z" 
      fill={color}
      fillOpacity="0.6"
    />
  </svg>
);

// Cricket-specific placeholder icon
const CricketIcon = ({ size = 48, color = '#94A3B8' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Cricket bat */}
    <rect x="20" y="8" width="8" height="28" rx="2" stroke={color} strokeWidth="2" fill="none" />
    <rect x="22" y="36" width="4" height="8" fill={color} fillOpacity="0.5" />
    {/* Ball */}
    <circle cx="36" cy="14" r="6" stroke={color} strokeWidth="2" fill="none" />
    <path d="M33 11C35 13 37 15 39 17" stroke={color} strokeWidth="1.5" />
  </svg>
);

/**
 * TeamCrest - Main component for displaying team crests
 * 
 * @param {string} clubId - The club/team ID (internal)
 * @param {string} apiFootballId - The Football-Data.org team ID for fetching crests
 * @param {string} name - Team name (used for alt text)
 * @param {string} sportKey - 'football' or 'cricket' for sport-specific placeholders
 * @param {string} variant - 'small' (32px), 'thumbnail' (48px), 'watermark' (300px), etc.
 * @param {boolean} isActive - Whether to show active state glow
 * @param {string} className - Additional CSS classes
 */
const TeamCrest = memo(({ 
  clubId, 
  apiFootballId,
  name = 'Team', 
  sportKey = 'football',
  variant = 'thumbnail',
  isActive = false,
  className = ''
}) => {
  const [imgError, setImgError] = useState(false);
  
  // Size based on variant
  const sizes = {
    small: 32,
    thumbnail: 48,
    medium: 64,
    large: 96,
    watermark: 300
  };
  const size = sizes[variant] || sizes.thumbnail;
  
  // Color based on active state
  const color = isActive ? '#06B6D4' : '#94A3B8';
  
  // Football-Data.org crest URL - DISABLED until apiFootballId mapping is verified
  // The current apiFootballId values in the database are incorrect (showing wrong team crests)
  // TODO: Re-enable when correct team IDs are sourced and verified
  // const crestUrl = apiFootballId ? `https://crests.football-data.org/${apiFootballId}.svg` : null;
  const crestUrl = null; // Always use placeholder for now
  const hasCrest = false; // Disabled until IDs are corrected
  
  // For watermark variant, return with special styling
  if (variant === 'watermark') {
    return (
      <div 
        className={`absolute inset-0 flex items-center justify-center pointer-events-none ${className}`}
        style={{ 
          opacity: 0.12,
          filter: 'grayscale(100%) brightness(200%)'
        }}
      >
        {hasCrest ? (
          <img 
            src={crestUrl} 
            alt={name}
            width={size}
            height={size}
            onError={() => setImgError(true)}
            style={{ objectFit: 'contain' }}
          />
        ) : (
          <PlaceholderShield size={size} color="#FFFFFF" />
        )}
      </div>
    );
  }
  
  // Standard crest display with real image or fallback
  if (hasCrest) {
    return (
      <div 
        className={`flex items-center justify-center ${className}`}
        style={{
          width: size,
          height: size,
          filter: isActive ? 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.4))' : 'none',
          transition: 'filter 200ms ease-out'
        }}
        title={name}
      >
        <img 
          src={crestUrl} 
          alt={name}
          width={size * 0.85}
          height={size * 0.85}
          onError={() => setImgError(true)}
          style={{ 
            objectFit: 'contain',
            filter: isActive ? 'drop-shadow(0 0 4px rgba(6, 182, 212, 0.3))' : 'none'
          }}
        />
      </div>
    );
  }
  
  // Fallback to placeholder icons
  const CrestIcon = sportKey === 'cricket' ? CricketIcon : PlaceholderShield;
  
  return (
    <div 
      className={`flex items-center justify-center ${className}`}
      style={{
        width: size,
        height: size,
        filter: isActive ? 'drop-shadow(0 0 8px rgba(6, 182, 212, 0.4))' : 'none',
        transition: 'filter 200ms ease-out'
      }}
      title={name}
    >
      <CrestIcon size={size} color={color} />
    </div>
  );
});

TeamCrest.displayName = 'TeamCrest';

// Export individual icons for direct use
export { PlaceholderShield, CricketIcon };
export default TeamCrest;
