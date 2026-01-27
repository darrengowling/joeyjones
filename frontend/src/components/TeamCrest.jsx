import { memo } from 'react';

/**
 * TeamCrest Component
 * 
 * Displays team/club crests with fallback to placeholder SVG.
 * Ready for real assets via URL pattern: /assets/clubs/{club_id}/crest.svg
 * 
 * Sizes:
 * - thumbnail: 48x48px (for lists, auction queue)
 * - watermark: 300px (for hero section background)
 * - avatar: 40px (for manager avatars)
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

// Sport-specific placeholder icons
const FootballIcon = ({ size = 48, color = '#94A3B8' }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="24" cy="24" r="20" stroke={color} strokeWidth="2" fill="none" />
    <path 
      d="M24 8V16M24 32V40M8 24H16M32 24H40M12 12L18 18M30 30L36 36M12 36L18 30M30 18L36 12" 
      stroke={color} 
      strokeWidth="1.5" 
      strokeLinecap="round"
    />
    <circle cx="24" cy="24" r="6" fill={color} fillOpacity="0.3" />
  </svg>
);

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
 * @param {string} clubId - The club/team ID for fetching real assets
 * @param {string} name - Team name (used for alt text and initials fallback)
 * @param {string} sportKey - 'football' or 'cricket' for sport-specific placeholders
 * @param {string} variant - 'thumbnail' (48px), 'watermark' (300px), 'small' (32px)
 * @param {boolean} isActive - Whether to show active state glow
 * @param {string} className - Additional CSS classes
 */
const TeamCrest = memo(({ 
  clubId, 
  name = 'Team', 
  sportKey = 'football',
  variant = 'thumbnail',
  isActive = false,
  className = ''
}) => {
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
  
  // For watermark variant, return with special styling
  if (variant === 'watermark') {
    return (
      <div 
        className={`absolute inset-0 flex items-center justify-center pointer-events-none ${className}`}
        style={{ 
          opacity: 0.15,
          filter: 'grayscale(100%) brightness(200%)'
        }}
      >
        <PlaceholderShield size={size} color="#FFFFFF" />
      </div>
    );
  }
  
  // Standard crest display
  const CrestIcon = sportKey === 'cricket' ? CricketIcon : 
                    sportKey === 'football' ? FootballIcon : 
                    PlaceholderShield;
  
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
export { PlaceholderShield, FootballIcon, CricketIcon };
export default TeamCrest;
