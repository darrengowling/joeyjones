import React from 'react';
import BottomNav from '../components/BottomNav';

/**
 * DesignPreview - Test page to preview new Stitch components
 * Access at /design-preview
 */
const DesignPreview = () => {
  return (
    <div 
      className="min-h-screen"
      style={{ 
        background: '#0F172A',
        paddingBottom: '100px' // Space for bottom nav
      }}
    >
      {/* Header */}
      <header 
        className="sticky top-0 z-40 px-6 py-4 flex items-center justify-between"
        style={{
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <h1 className="text-white text-xl font-bold tracking-tight">
          SPORT <span style={{ color: '#06B6D4' }}>X</span>
        </h1>
        <span className="text-xs text-white/40 font-mono">Design Preview</span>
      </header>

      {/* Content */}
      <main className="p-6 space-y-8">
        {/* Typography Section */}
        <section>
          <p className="text-[10px] font-bold uppercase tracking-widest text-cyan-500 mb-4">
            01 Typography
          </p>
          <div 
            className="p-6 rounded-xl space-y-6"
            style={{
              background: 'rgba(15, 23, 42, 0.6)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <div>
              <p className="text-[10px] text-white/40 mb-1 font-mono">H1 - 32px / 700</p>
              <h1 className="text-white text-[32px] font-bold leading-tight">Elite Performance</h1>
            </div>
            <div>
              <p className="text-[10px] text-white/40 mb-1 font-mono">Body - 16px / 400</p>
              <p className="text-white text-base">Place your bid on premium assets with real-time tracking.</p>
            </div>
            <div>
              <p className="text-[10px] text-white/40 mb-1 font-mono">Label - 12px / 700 / Uppercase</p>
              <p className="text-white/60 text-xs font-bold uppercase">Current High Bidder</p>
            </div>
          </div>
        </section>

        {/* Buttons Section */}
        <section>
          <p className="text-[10px] font-bold uppercase tracking-widest text-cyan-500 mb-4">
            02 Button States
          </p>
          <div 
            className="p-6 rounded-xl space-y-4"
            style={{
              background: 'rgba(15, 23, 42, 0.6)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            {/* Primary Button */}
            <div>
              <p className="text-[10px] text-white/40 mb-2 font-mono">Primary: Default</p>
              <button 
                className="w-full py-3.5 rounded-xl text-sm font-bold uppercase transition-all hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] active:scale-[0.98]"
                style={{ background: '#06B6D4', color: '#0F172A' }}
              >
                Place Bid
              </button>
            </div>
            
            {/* Primary Disabled */}
            <div>
              <p className="text-[10px] text-white/40 mb-2 font-mono">Primary: Disabled</p>
              <button 
                className="w-full py-3.5 rounded-xl text-sm font-bold uppercase cursor-not-allowed"
                style={{ background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.2)' }}
                disabled
              >
                Auction Ended
              </button>
            </div>
            
            {/* Secondary Button */}
            <div>
              <p className="text-[10px] text-white/40 mb-2 font-mono">Secondary: Outline</p>
              <button 
                className="w-full py-3.5 rounded-xl text-sm font-bold text-white uppercase transition-all hover:bg-white/5 active:scale-[0.98]"
                style={{ border: '1px solid rgba(255,255,255,0.2)' }}
              >
                Team Details
              </button>
            </div>
            
            {/* Danger/Pass Button */}
            <div>
              <p className="text-[10px] text-white/40 mb-2 font-mono">Danger: Pass</p>
              <button 
                className="w-full py-3.5 rounded-xl text-sm font-bold uppercase transition-all hover:bg-red-500/10 active:scale-[0.98]"
                style={{ border: '1px solid #EF4444', color: '#EF4444' }}
              >
                Pass Turn
              </button>
            </div>
          </div>
        </section>

        {/* Glass Card Section */}
        <section>
          <p className="text-[10px] font-bold uppercase tracking-widest text-cyan-500 mb-4">
            03 Glass Card
          </p>
          <div 
            className="p-5 rounded-xl"
            style={{
              background: 'rgba(15, 23, 42, 0.6)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h4 className="text-white font-bold text-lg">London Lions</h4>
                <p className="text-xs text-white/50">Current Bid: £45,200</p>
              </div>
              <span 
                className="text-[10px] font-bold px-2 py-1 rounded"
                style={{ background: 'rgba(249, 115, 22, 0.2)', color: '#F97316' }}
              >
                HOT
              </span>
            </div>
            <div className="h-1 bg-white/10 rounded-full overflow-hidden">
              <div className="h-full bg-cyan-500 w-2/3"></div>
            </div>
          </div>
        </section>

        {/* Spacing Info */}
        <section>
          <p className="text-[10px] font-bold uppercase tracking-widest text-cyan-500 mb-4">
            04 Spacing & Radius
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div 
              className="p-4 rounded-xl"
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.05)',
              }}
            >
              <p className="text-[9px] text-white/40 uppercase mb-1">Base Unit</p>
              <p className="text-xl font-mono text-cyan-500">8px</p>
            </div>
            <div 
              className="p-4 rounded-xl"
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.05)',
              }}
            >
              <p className="text-[9px] text-white/40 uppercase mb-1">Corner Radius</p>
              <p className="text-xl font-mono text-cyan-500">12px</p>
            </div>
          </div>
        </section>
      </main>

      {/* Bottom Navigation */}
      <BottomNav 
        onFabClick={() => alert('FAB clicked!')}
      />
    </div>
  );
};

export default DesignPreview;
