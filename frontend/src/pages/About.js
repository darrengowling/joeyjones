import React from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * About Page - Sport X philosophy and gameplay
 * Based on Stitch Technical Design Specs v2.0
 */
const About = () => {
  const navigate = useNavigate();

  return (
    <div 
      className="min-h-screen pb-24"
      style={{ background: '#0F172A' }}
    >
      {/* Header */}
      <header 
        className="sticky top-0 z-40 px-4 flex items-center justify-between"
        style={{ 
          height: '64px',
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        <button 
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-white/60 hover:text-white transition-colors"
        >
          <span className="material-symbols-outlined">arrow_back</span>
          <span className="text-sm font-medium">Back</span>
        </button>
        <h1 className="text-lg font-black text-white uppercase tracking-tight">About</h1>
        <div className="w-16"></div>
      </header>

      {/* Content */}
      <div className="px-4 py-6 space-y-6 max-w-lg mx-auto">
        
        {/* Hero Section */}
        <div className="text-center py-6">
          <h2 className="text-3xl font-black text-white uppercase tracking-tight mb-2">
            SPORT <span style={{ color: '#06B6D4' }}>X</span>
          </h2>
          <p className="text-lg font-bold uppercase tracking-widest" style={{ color: '#06B6D4' }}>
            No Gambling. All Game.
          </p>
        </div>

        {/* Who We Are Card */}
        <div 
          className="rounded-2xl p-5 space-y-3"
          style={{
            background: 'rgba(30, 41, 59, 0.45)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(6, 182, 212, 0.15)',
          }}
        >
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: 'rgba(6, 182, 212, 0.1)' }}
            >
              <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>info</span>
            </div>
            <h3 className="font-black text-white uppercase tracking-tight text-sm">Who We Are</h3>
          </div>
          <p className="text-slate-400 text-sm leading-relaxed">
            Sport X is a premium social auction platform built for the modern sports fan. We&apos;ve stripped away the noise of gambling to focus on what actually matters: skill, strategy, and pure bragging rights.
          </p>
        </div>

        {/* Why We Do It Card */}
        <div 
          className="rounded-2xl p-5 space-y-3"
          style={{
            background: 'rgba(30, 41, 59, 0.45)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
          }}
        >
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: 'rgba(255, 255, 255, 0.05)' }}
            >
              <span className="material-symbols-outlined text-xl text-slate-400">favorite</span>
            </div>
            <h3 className="font-black text-white uppercase tracking-tight text-sm">Why We Do It</h3>
          </div>
          <p className="text-slate-400 text-sm leading-relaxed">
            We believe sports are better when shared with friends. Our mission is to create a high-intensity and competitive environment where your knowledge of the game is your only currency.
          </p>
        </div>

        {/* How It Works Card */}
        <div 
          className="rounded-2xl p-5 space-y-4"
          style={{
            background: 'rgba(30, 41, 59, 0.45)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.05)',
          }}
        >
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: 'rgba(255, 255, 255, 0.05)' }}
            >
              <span className="material-symbols-outlined text-xl text-slate-400">play_circle</span>
            </div>
            <h3 className="font-black text-white uppercase tracking-tight text-sm">How It Works</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: 'rgba(6, 182, 212, 0.15)' }}>
                <span className="text-xs font-black" style={{ color: '#06B6D4' }}>1</span>
              </div>
              <div>
                <span className="text-white font-bold text-sm">THE AUCTION</span>
                <p className="text-slate-400 text-sm leading-relaxed mt-1">Enter a high-tension live auction. Use your fixed budget to bid on teams in real-time.</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: 'rgba(6, 182, 212, 0.15)' }}>
                <span className="text-xs font-black" style={{ color: '#06B6D4' }}>2</span>
              </div>
              <div>
                <span className="text-white font-bold text-sm">THE ROSTER</span>
                <p className="text-slate-400 text-sm leading-relaxed mt-1">Once you win a bid, that team is yours and yours alone. Build a roster of elite clubs to compete in your private league.</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: 'rgba(6, 182, 212, 0.15)' }}>
                <span className="text-xs font-black" style={{ color: '#06B6D4' }}>3</span>
              </div>
              <div>
                <span className="text-white font-bold text-sm">THE TRACKER</span>
                <p className="text-slate-400 text-sm leading-relaxed mt-1">We sync with real-world matches. Every goal, win and draw in the real world earns you points in the app.</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: 'rgba(6, 182, 212, 0.15)' }}>
                <span className="text-xs font-black" style={{ color: '#06B6D4' }}>4</span>
              </div>
              <div>
                <span className="text-white font-bold text-sm">THE GLORY</span>
                <p className="text-slate-400 text-sm leading-relaxed mt-1">Outsmart your rivals, climb the standings and claim the ultimate championship badge.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Manifesto Card */}
        <div 
          className="rounded-2xl p-5 space-y-4"
          style={{
            background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(30, 41, 59, 0.45) 100%)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(6, 182, 212, 0.2)',
          }}
        >
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: 'rgba(6, 182, 212, 0.15)' }}
            >
              <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>star</span>
            </div>
            <h3 className="font-black uppercase tracking-tight text-sm" style={{ color: '#06B6D4' }}>The Sport X Manifesto</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-base mt-0.5" style={{ color: '#06B6D4' }}>check_circle</span>
              <div>
                <span className="text-white font-bold text-sm">SKILL OVER LUCK</span>
                <p className="text-slate-400 text-sm">Success is earned through scouting and strategy</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-base mt-0.5" style={{ color: '#06B6D4' }}>check_circle</span>
              <div>
                <span className="text-white font-bold text-sm">FRIENDS OVER HOUSES</span>
                <p className="text-slate-400 text-sm">We play against each other, never &quot;the house&quot;</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-base mt-0.5" style={{ color: '#06B6D4' }}>check_circle</span>
              <div>
                <span className="text-white font-bold text-sm">GLORY OVER MONEY</span>
                <p className="text-slate-400 text-sm">The prize is bragging rights</p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="pt-4">
          <button
            onClick={() => navigate('/')}
            className="w-full py-4 rounded-xl font-bold text-base transition-all active:scale-95"
            style={{ background: '#06B6D4', color: '#0F172A' }}
            data-testid="about-get-started-btn"
          >
            Get Started
          </button>
        </div>
      </div>
    </div>
  );
};

export default About;
