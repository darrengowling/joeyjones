import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

/**
 * PlaceholderPage - Coming soon page for features not yet implemented
 */
const PlaceholderPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get page name from path
  const pageName = location.pathname.replace('/', '').replace('-', ' ') || 'Page';
  const formattedName = pageName.charAt(0).toUpperCase() + pageName.slice(1);

  return (
    <div 
      className="min-h-screen font-sans"
      style={{ 
        background: '#0F172A',
        paddingBottom: '100px',
      }}
    >
      {/* Header */}
      <header 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-md z-40 px-6 py-5 flex items-center justify-between"
        style={{
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <button 
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
        >
          <span className="material-symbols-outlined">arrow_back</span>
        </button>
        <h1 className="text-sm font-black tracking-widest uppercase text-white">
          {formattedName}
        </h1>
        <div className="w-6"></div>
      </header>

      {/* Content */}
      <main className="pt-24 px-6 flex flex-col items-center justify-center min-h-[70vh]">
        <div 
          className="rounded-3xl p-10 flex flex-col items-center justify-center text-center space-y-6 max-w-sm w-full"
          style={{
            background: 'rgba(30, 41, 59, 0.45)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          {/* Icon */}
          <div className="relative">
            <div 
              className="absolute inset-0 blur-3xl rounded-full"
              style={{ background: 'rgba(6, 182, 212, 0.2)' }}
            ></div>
            <div 
              className="relative w-20 h-20 rounded-3xl flex items-center justify-center"
              style={{ 
                background: '#1E293B',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <span 
                className="material-symbols-outlined text-4xl"
                style={{ color: '#06B6D4' }}
              >
                construction
              </span>
            </div>
          </div>

          {/* Text */}
          <div className="space-y-3">
            <h2 className="text-2xl font-black text-white uppercase tracking-tight">
              Coming Soon
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed">
              We're working hard to bring you the <span className="text-cyan-400 font-semibold">{formattedName}</span> feature. Stay tuned!
            </p>
          </div>

          {/* Back Home Button */}
          <button 
            onClick={() => navigate('/')}
            className="px-8 py-3 rounded-xl font-black text-sm uppercase tracking-widest transition-all active:scale-[0.98]"
            style={{
              background: '#06B6D4',
              color: '#0F172A',
            }}
            data-testid="back-home-btn"
          >
            Back to Home
          </button>
        </div>
      </main>

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  );
};

export default PlaceholderPage;
