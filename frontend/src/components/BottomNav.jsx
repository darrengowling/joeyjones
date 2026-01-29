import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

/**
 * BottomNav - Fixed bottom navigation with floating action button
 * Based on Stitch Technical Design Specs v2.0
 * 
 * Props:
 * - onFabClick: Function to call when FAB is pressed (optional)
 * - fabIcon: Icon name for FAB (default: "add")
 */
const BottomNav = ({ onFabClick, fabIcon = "add" }) => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Navigation items configuration
  // Placeholder routes for items not yet implemented
  const navItems = [
    { id: 'home', icon: 'home', label: 'Home', path: '/' },
    { id: 'stats', icon: 'analytics', label: 'Stats', path: '/stats' },
    // FAB goes here (index 2)
    { id: 'teams', icon: 'shield', label: 'Teams', path: '/clubs' },
    { id: 'profile', icon: 'person', label: 'Profile', path: '/profile' },
  ];
  
  // Check if a nav item is active
  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };
  
  // Handle nav item click
  const handleNavClick = (path) => {
    navigate(path);
  };
  
  // Handle FAB click
  const handleFabClick = () => {
    if (onFabClick) {
      onFabClick();
    } else {
      // Default: navigate to create competition or show modal
      navigate('/?create=true');
    }
  };

  return (
    <nav 
      className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-md z-50"
      style={{
        background: 'rgba(15, 23, 42, 0.95)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
      }}
      data-testid="bottom-nav"
    >
      <div className="flex justify-between items-center px-6 pt-3 pb-8">
        {/* Left side nav items */}
        {navItems.slice(0, 2).map((item) => (
          <NavItem
            key={item.id}
            icon={item.icon}
            label={item.label}
            isActive={isActive(item.path)}
            onClick={() => handleNavClick(item.path)}
          />
        ))}
        
        {/* Center FAB */}
        <div className="relative -mt-12">
          <button
            onClick={handleFabClick}
            className="flex items-center justify-center transition-transform active:scale-90"
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '9999px',
              background: '#06B6D4',
              boxShadow: '0 0 20px rgba(6, 182, 212, 0.4)',
              border: '6px solid #0F172A',
            }}
            data-testid="bottom-nav-fab"
          >
            <span 
              className="material-symbols-outlined text-3xl font-bold"
              style={{ color: '#0F172A' }}
            >
              {fabIcon}
            </span>
          </button>
        </div>
        
        {/* Right side nav items */}
        {navItems.slice(2).map((item) => (
          <NavItem
            key={item.id}
            icon={item.icon}
            label={item.label}
            isActive={isActive(item.path)}
            onClick={() => handleNavClick(item.path)}
          />
        ))}
      </div>
      
      {/* Home indicator bar (iOS style) */}
      <div 
        className="absolute bottom-1 left-1/2 -translate-x-1/2 w-32 h-1 rounded-full"
        style={{ background: 'rgba(255, 255, 255, 0.2)' }}
      />
    </nav>
  );
};

/**
 * NavItem - Individual navigation item
 */
const NavItem = ({ icon, label, isActive, onClick }) => {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center justify-center w-12 h-12 transition-colors"
      style={{
        color: isActive ? '#06B6D4' : 'rgba(255, 255, 255, 0.4)',
      }}
      title={label}
    >
      <span 
        className="material-symbols-outlined text-2xl"
        style={{
          fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
        }}
      >
        {icon}
      </span>
    </button>
  );
};

export default BottomNav;
