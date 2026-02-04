import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import BottomNav from '../components/BottomNav';
import { setUser as setSentryUser, addBreadcrumb } from '../utils/sentry';

const API = process.env.REACT_APP_BACKEND_URL + "/api";

/**
 * HomePage - New Stitch-styled home page
 * Dark theme with glassmorphism, bottom nav, and mobile-first design
 */
const HomePage = () => {
  const navigate = useNavigate();
  
  // User state
  const [user, setUser] = useState(null);
  const [leagues, setLeagues] = useState([]);
  const [leaguesLoading, setLeaguesLoading] = useState(false);
  
  // Modal states
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showJoinModal, setShowJoinModal] = useState(false);
  
  // Auth form state
  const [authStep, setAuthStep] = useState('email'); // 'email' or 'token'
  const [email, setEmail] = useState('');
  const [tokenInput, setTokenInput] = useState('');
  const [magicToken, setMagicToken] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState('');
  
  // Join form state
  const [inviteCode, setInviteCode] = useState('');
  const [joinLoading, setJoinLoading] = useState(false);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Error parsing user:', e);
      }
    }
  }, []);

  // Load user's leagues when user changes
  useEffect(() => {
    if (user) {
      loadUserLeagues();
    } else {
      setLeagues([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const loadUserLeagues = async () => {
    setLeaguesLoading(true);
    try {
      const response = await axios.get(`${API}/me/competitions`, {
        params: { userId: user.id }
      });
      
      // The /me/competitions endpoint already returns full league details
      // Transform to match the expected league structure
      const leagues = response.data.map(comp => ({
        id: comp.leagueId,
        name: comp.name,
        sportKey: comp.sportKey,
        status: comp.status === 'auction_live' ? 'auction_live' : 
                comp.status === 'auction_complete' ? 'completed' : 'pending',
        commissionerId: comp.isCommissioner ? user.id : null,
        activeAuctionId: comp.activeAuctionId,
        managersCount: comp.managersCount,
        timerSeconds: comp.timerSeconds,
        antiSnipeSeconds: comp.antiSnipeSeconds,
      }));
      
      setLeagues(leagues);
    } catch (e) {
      console.error('Error loading leagues:', e);
    } finally {
      setLeaguesLoading(false);
    }
  };

  // Auth handlers
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError('');

    if (authStep === 'email') {
      if (!email || !email.includes('@')) {
        setAuthError('Please enter a valid email address');
        setAuthLoading(false);
        return;
      }

      try {
        const response = await axios.post(`${API}/auth/magic-link`, {
          email: email.trim().toLowerCase(),
        });
        setMagicToken(response.data.token);
        setAuthStep('token');
        toast.success('Magic link generated! Enter the token below.');
      } catch (error) {
        setAuthError(error.response?.data?.detail || 'Unable to send magic link');
      } finally {
        setAuthLoading(false);
      }
    } else {
      // Verify token
      if (!tokenInput.trim()) {
        setAuthError('Please enter the token');
        setAuthLoading(false);
        return;
      }

      try {
        const response = await axios.post(`${API}/auth/verify-magic-link`, {
          email: email.trim().toLowerCase(),
          token: tokenInput.trim(),
        });

        const { accessToken, refreshToken, user: userData } = response.data;
        localStorage.setItem('accessToken', accessToken);
        localStorage.setItem('refreshToken', refreshToken);
        localStorage.setItem('user', JSON.stringify(userData));

        setUser(userData);
        setSentryUser(userData);
        addBreadcrumb('User signed in', { email: userData.email }, 'auth');
        closeAuthModal();
        toast.success('Successfully signed in!');
      } catch (error) {
        setAuthError(error.response?.data?.detail || 'Invalid or expired token');
      } finally {
        setAuthLoading(false);
      }
    }
  };

  const closeAuthModal = () => {
    setShowAuthModal(false);
    setEmail('');
    setTokenInput('');
    setMagicToken('');
    setAuthStep('email');
    setAuthError('');
  };

  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    setUser(null);
    setLeagues([]);
    toast.success('Logged out');
  };

  // Action handlers
  const handleJoinCompetition = () => {
    if (!user) {
      setShowAuthModal(true);
    } else {
      setShowJoinModal(true);
    }
  };

  const handleCreateCompetition = () => {
    if (!user) {
      setShowAuthModal(true);
    } else {
      navigate('/create-competition');
    }
  };

  const handleJoinSubmit = async (e) => {
    e.preventDefault();
    if (!inviteCode.trim()) {
      toast.error('Please enter an invite code');
      return;
    }

    setJoinLoading(true);
    try {
      const response = await axios.post(`${API}/leagues/join`, {
        inviteToken: inviteCode.trim(),
        userId: user.id,
        userName: user.name,
        userEmail: user.email,
      });
      
      toast.success('Successfully joined!');
      setShowJoinModal(false);
      setInviteCode('');
      navigate(`/league/${response.data.leagueId}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to join');
    } finally {
      setJoinLoading(false);
    }
  };

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
        <h1 className="text-2xl font-black tracking-tighter text-white">
          SPORT <span style={{ color: '#06B6D4' }}>X</span>
        </h1>
        <div className="flex gap-4 items-center">
          <button 
            onClick={() => navigate('/help')}
            className="text-xs font-bold text-slate-400 hover:text-white transition-colors tracking-widest uppercase"
          >
            Help
          </button>
          <div className="h-4 w-px bg-white/10"></div>
          {user ? (
            <button 
              onClick={handleLogout}
              className="text-xs font-black text-white hover:text-cyan-400 transition-colors tracking-widest uppercase"
            >
              Sign Out
            </button>
          ) : (
            <button 
              onClick={() => setShowAuthModal(true)}
              className="text-xs font-black text-white hover:text-cyan-400 transition-colors tracking-widest uppercase"
            >
              Sign In
            </button>
          )}
        </div>
      </header>

      <main className="pt-24 px-6 pb-6 space-y-8">
        {/* Hero Section */}
        <section 
          className="p-8 rounded-3xl space-y-6"
          style={{
            background: 'rgba(30, 41, 59, 0.45)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: '1px solid rgba(6, 182, 212, 0.15)',
            boxShadow: '0 0 40px rgba(6, 182, 212, 0.1)',
          }}
        >
          <div className="space-y-2">
            <h2 className="text-xs font-black tracking-[0.2em] uppercase" style={{ color: '#06B6D4' }}>
              Welcome to
            </h2>
            <h3 
              className="text-5xl font-black tracking-tight leading-none uppercase text-white"
              style={{ textShadow: '0 0 15px rgba(6, 182, 212, 0.5)' }}
            >
              SPORT <span style={{ color: '#06B6D4' }}>X</span>
            </h3>
          </div>
          
          <div className="space-y-4">
            <p className="text-xl font-bold text-slate-100 leading-tight">
              Sports Gaming with Friends.<br />
              <span className="text-slate-400">No Gambling. All Game.</span>
            </p>
            <p className="text-slate-400 leading-relaxed text-sm font-medium">
              Bid for exclusive ownership of players and teams who score your points. Experience the thrill of sports through strategic competition and community.
            </p>
          </div>

          <button 
            onClick={handleJoinCompetition}
            className="w-full py-4 rounded-2xl flex items-center justify-center gap-3 active:scale-[0.98] transition-all font-black text-white uppercase tracking-widest text-sm"
            style={{
              background: 'linear-gradient(135deg, #0ed7f7 0%, #06b6d4 50%, #0891b2 100%)',
              boxShadow: '0 4px 20px rgba(6, 182, 212, 0.25), inset 0 1px 1px rgba(255, 255, 255, 0.1)',
            }}
            data-testid="join-competition-btn"
          >
            <span>Join the Competition</span>
            <span className="material-symbols-outlined text-xl">arrow_forward</span>
          </button>
        </section>

        {/* Action Cards */}
        <section className="grid grid-cols-1 gap-4">
          {/* Create Competition Card */}
          <button 
            onClick={handleCreateCompetition}
            className="p-5 rounded-2xl flex items-center justify-between transition-all active:scale-[0.98] group text-left"
            style={{
              background: 'rgba(30, 41, 59, 0.45)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(6, 182, 212, 0.2)',
            }}
            data-testid="create-league-card"
          >
            <div className="flex items-center gap-4">
              <div 
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ 
                  background: 'rgba(6, 182, 212, 0.1)',
                  border: '1px solid rgba(6, 182, 212, 0.2)',
                }}
              >
                <span className="material-symbols-outlined" style={{ color: '#06B6D4' }}>add_box</span>
              </div>
              <div>
                <span className="block font-black text-white uppercase tracking-tight text-sm">Create Your Competition</span>
                <span className="block text-slate-500 text-[10px] font-bold uppercase tracking-widest">Host a private auction</span>
              </div>
            </div>
            <span className="material-symbols-outlined text-slate-600 group-hover:text-cyan-500 transition-colors">chevron_right</span>
          </button>

          {/* Explore Teams/Players Card */}
          <button 
            onClick={() => navigate('/clubs')}
            className="p-5 rounded-2xl flex items-center justify-between transition-all active:scale-[0.98] group text-left"
            style={{
              background: 'rgba(30, 41, 59, 0.45)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.05)',
            }}
            data-testid="browse-markets-card"
          >
            <div className="flex items-center gap-4">
              <div 
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ 
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.05)',
                }}
              >
                <span className="material-symbols-outlined text-slate-400">explore</span>
              </div>
              <div>
                <span className="block font-black text-white uppercase tracking-tight text-sm">Explore Available Teams/Players</span>
                <span className="block text-slate-500 text-[10px] font-bold uppercase tracking-widest">Browse the roster</span>
              </div>
            </div>
            <span className="material-symbols-outlined text-slate-600 group-hover:text-cyan-500 transition-colors">chevron_right</span>
          </button>
        </section>

        {/* Active Competitions Section */}
        <section className="space-y-5">
          <div className="flex items-end justify-between px-1">
            <h3 className="text-xl font-black uppercase tracking-tighter text-white">My Competitions</h3>
            {leagues.length > 0 && (
              <button 
                onClick={() => navigate('/app/my-competitions')}
                className="text-[10px] font-black uppercase tracking-widest pb-1 border-b transition-colors hover:text-white"
                style={{ color: '#06B6D4', borderColor: 'rgba(6, 182, 212, 0.3)' }}
              >
                View All
              </button>
            )}
          </div>

          {leaguesLoading ? (
            /* Loading State */
            <div 
              className="rounded-3xl p-10 flex flex-col items-center justify-center text-center space-y-4"
              style={{
                background: 'rgba(30, 41, 59, 0.45)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-xs text-slate-400 font-semibold uppercase tracking-widest">Loading competitions...</p>
            </div>
          ) : leagues.length === 0 ? (
            /* Empty State */
            <div 
              className="rounded-3xl p-10 flex flex-col items-center justify-center text-center space-y-6"
              style={{
                background: 'rgba(30, 41, 59, 0.45)',
                border: '2px dashed rgba(255, 255, 255, 0.1)',
              }}
            >
              <div className="relative">
                <div 
                  className="absolute inset-0 blur-3xl rounded-full"
                  style={{ background: 'rgba(6, 182, 212, 0.15)' }}
                ></div>
                <div 
                  className="relative w-20 h-20 rounded-3xl flex items-center justify-center rotate-12"
                  style={{ 
                    background: '#1E293B',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <span 
                    className="material-symbols-outlined text-4xl transform -rotate-12"
                    style={{ color: '#06B6D4' }}
                  >
                    trophy
                  </span>
                </div>
              </div>
              <div className="space-y-2">
                <p className="font-black text-white uppercase tracking-tight text-lg">
                  {user ? 'No Active Competitions' : 'Sign In to View Your Competitions'}
                </p>
                <p className="text-xs text-slate-400 font-semibold max-w-[240px] mx-auto leading-relaxed">
                  {user 
                    ? "You haven't joined any competitions yet. Create or join one to get started."
                    : "Sign in to create or join competitions and track your progress."
                  }
                </p>
              </div>
              <button 
                onClick={user ? handleJoinCompetition : () => setShowAuthModal(true)}
                className="px-8 py-3 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] transition-all hover:bg-white/10"
                style={{ 
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#06B6D4',
                }}
              >
                {user ? 'Join a Competition' : 'Sign In'}
              </button>
            </div>
          ) : (
            /* League Cards */
            <div className="space-y-3">
              {leagues.slice(0, 3).map((league) => (
                <button
                  key={league.id}
                  onClick={() => navigate(`/app/competitions/${league.id}`)}
                  className="w-full p-4 rounded-2xl flex items-center justify-between transition-all active:scale-[0.98] group text-left"
                  style={{
                    background: 'rgba(30, 41, 59, 0.45)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-xl flex items-center justify-center"
                      style={{ 
                        background: league.status === 'auction_live' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(6, 182, 212, 0.1)',
                        border: `1px solid ${league.status === 'auction_live' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(6, 182, 212, 0.2)'}`,
                      }}
                    >
                      <span 
                        className="material-symbols-outlined"
                        style={{ color: league.status === 'auction_live' ? '#10B981' : '#06B6D4' }}
                      >
                        {league.status === 'auction_live' ? 'gavel' : 'sports_soccer'}
                      </span>
                    </div>
                    <div>
                      <span className="block font-bold text-white text-sm">{league.name}</span>
                      <span 
                        className="text-[10px] font-bold uppercase tracking-widest"
                        style={{ color: league.status === 'auction_live' ? '#10B981' : '#64748B' }}
                      >
                        {league.status === 'auction_live' ? 'Live Auction' : league.status?.replace(/_/g, ' ')}
                      </span>
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-slate-600 group-hover:text-cyan-500 transition-colors">chevron_right</span>
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Footer */}
        <footer className="pt-8 pb-8 flex flex-col items-center justify-center gap-8 border-t border-white/5">
          <div className="flex items-center gap-4">
            <div 
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ 
                background: '#1E293B',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <span className="material-symbols-outlined" style={{ color: '#06B6D4' }}>verified</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-white">Premium Certified</span>
              <span className="text-[9px] font-bold uppercase tracking-[0.1em] text-slate-500">Enterprise Grade Security</span>
            </div>
          </div>
          <div className="flex gap-8 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-600">
            <a className="hover:text-cyan-500 transition-colors" href="#">Privacy</a>
            <a className="hover:text-cyan-500 transition-colors" href="#">Terms</a>
            <a onClick={() => navigate('/help')} className="hover:text-cyan-500 transition-colors cursor-pointer">Support</a>
          </div>
        </footer>
      </main>

      {/* Auth Modal */}
      {showAuthModal && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-6"
          style={{ background: 'rgba(0, 0, 0, 0.8)' }}
        >
          <div 
            className="w-full max-w-md rounded-3xl p-8 space-y-6"
            style={{
              background: '#0F172A',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-black text-white uppercase tracking-tight">Sign In</h2>
              <button onClick={closeAuthModal} className="text-slate-400 hover:text-white">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleAuthSubmit} className="space-y-4">
              {authStep === 'email' ? (
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-widest" style={{ color: '#06B6D4' }}>
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="w-full px-4 py-4 rounded-xl text-white placeholder:text-slate-600 focus:outline-none focus:ring-2"
                    style={{
                      background: 'rgba(30, 41, 59, 0.5)',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                    }}
                    data-testid="auth-email-input"
                  />
                </div>
              ) : (
                <div className="space-y-4">
                  <div 
                    className="p-4 rounded-xl"
                    style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}
                  >
                    <p className="text-xs text-slate-300 mb-2">Your magic token (pilot mode):</p>
                    <p className="font-mono text-sm break-all" style={{ color: '#06B6D4' }}>{magicToken}</p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-widest" style={{ color: '#06B6D4' }}>
                      Enter Token
                    </label>
                    <input
                      type="text"
                      value={tokenInput}
                      onChange={(e) => setTokenInput(e.target.value)}
                      placeholder="Paste your token here"
                      className="w-full px-4 py-4 rounded-xl text-white placeholder:text-slate-600 focus:outline-none focus:ring-2"
                      style={{
                        background: 'rgba(30, 41, 59, 0.5)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                      }}
                      data-testid="auth-token-input"
                    />
                  </div>
                </div>
              )}

              {authError && (
                <p className="text-sm" style={{ color: '#EF4444' }}>{authError}</p>
              )}

              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-[0.98] disabled:opacity-50"
                style={{
                  background: '#06B6D4',
                  color: '#0F172A',
                }}
                data-testid="auth-submit-btn"
              >
                {authLoading ? 'Loading...' : authStep === 'email' ? 'Send Magic Link' : 'Verify & Sign In'}
              </button>

              {authStep === 'token' && (
                <button
                  type="button"
                  onClick={() => { setAuthStep('email'); setAuthError(''); }}
                  className="w-full py-2 text-sm text-slate-400 hover:text-white transition-colors"
                >
                  ← Back to email
                </button>
              )}
            </form>
          </div>
        </div>
      )}

      {/* Join Modal */}
      {showJoinModal && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-6"
          style={{ background: 'rgba(0, 0, 0, 0.8)' }}
        >
          <div 
            className="w-full max-w-md rounded-3xl p-8 space-y-6"
            style={{
              background: '#0F172A',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-black text-white uppercase tracking-tight">Join Competition</h2>
              <button onClick={() => setShowJoinModal(false)} className="text-slate-400 hover:text-white">
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleJoinSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-widest" style={{ color: '#06B6D4' }}>
                  Invite Code
                </label>
                <input
                  type="text"
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value)}
                  placeholder="Enter invite code"
                  className="w-full px-4 py-4 rounded-xl text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 font-mono text-center text-xl tracking-widest"
                  style={{
                    background: 'rgba(30, 41, 59, 0.5)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  data-testid="join-invite-input"
                />
              </div>

              <button
                type="submit"
                disabled={joinLoading}
                className="w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-[0.98] disabled:opacity-50"
                style={{
                  background: '#06B6D4',
                  color: '#0F172A',
                }}
                data-testid="join-submit-btn"
              >
                {joinLoading ? 'Joining...' : 'Join League'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Bottom Navigation */}
      <BottomNav onFabClick={handleCreateCompetition} />
    </div>
  );
};

export default HomePage;
