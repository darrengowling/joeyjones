import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import BottomNav from '../components/BottomNav';

const API = process.env.REACT_APP_BACKEND_URL;

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [displayName, setDisplayName] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    // Load user from localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      setUser(parsed);
      setDisplayName(parsed.name || '');
    }
  }, []);

  const handleSave = async () => {
    if (!displayName.trim()) {
      setError('Display name cannot be empty');
      return;
    }
    if (displayName.trim().length < 2 || displayName.trim().length > 30) {
      setError('Display name must be between 2 and 30 characters');
      return;
    }

    setIsSaving(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.patch(
        `${API}/api/users/${user.id}`,
        { name: displayName.trim() },
        { headers: { 'X-User-ID': user.id } }
      );

      // Update local storage and state
      const updatedUser = { ...user, name: response.data.name };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      setDisplayName(response.data.name);
      setIsEditing(false);
      setSuccess('Profile updated successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/');
    window.location.reload();
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0F172A' }}>
        <div className="text-white/60">Loading...</div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen pb-32"
      style={{ 
        background: '#0F172A',
        fontFamily: 'Inter, sans-serif'
      }}
    >
      {/* Header */}
      <header className="p-4 flex items-center justify-between">
        <button 
          onClick={() => navigate(-1)}
          className="flex items-center justify-center w-10 h-10 rounded-xl"
          style={{ 
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <span className="material-symbols-outlined text-white">chevron_left</span>
        </button>
        <h1 className="text-white font-bold text-lg">Profile</h1>
        <div className="w-10"></div>
      </header>

      <div className="max-w-md mx-auto px-4 pt-4">
        {/* Avatar Section */}
        <div className="flex flex-col items-center mb-8">
          <div 
            className="w-24 h-24 rounded-full flex items-center justify-center text-3xl font-bold mb-4"
            style={{ 
              background: '#06B6D4',
              color: '#0F172A'
            }}
          >
            {user.name?.charAt(0).toUpperCase() || '?'}
          </div>
          <p className="text-white/60 text-sm">{user.email}</p>
        </div>

        {/* Profile Card */}
        <div 
          className="rounded-xl p-6 mb-6"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <h2 className="text-white/60 text-xs font-semibold uppercase tracking-wider mb-4">
            Account Details
          </h2>

          {/* Display Name Field */}
          <div className="mb-4">
            <label className="text-white/40 text-xs uppercase tracking-wider mb-2 block">
              Display Name
            </label>
            {isEditing ? (
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                maxLength={30}
                className="w-full px-4 py-3 rounded-xl text-white outline-none transition-all"
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  border: '1px solid rgba(6, 182, 212, 0.5)'
                }}
                autoFocus
              />
            ) : (
              <div 
                className="flex items-center justify-between px-4 py-3 rounded-xl"
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}
              >
                <span className="text-white">{user.name}</span>
                <button
                  onClick={() => setIsEditing(true)}
                  className="text-xs font-semibold px-3 py-1 rounded-lg transition-all"
                  style={{ 
                    background: 'rgba(6, 182, 212, 0.2)',
                    color: '#06B6D4'
                  }}
                >
                  Edit
                </button>
              </div>
            )}
          </div>

          {/* Email Field (Read-only) */}
          <div className="mb-4">
            <label className="text-white/40 text-xs uppercase tracking-wider mb-2 block">
              Email
            </label>
            <div 
              className="flex items-center justify-between gap-2 px-4 py-3 rounded-xl"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <span className="text-white/60 truncate">{user.email}</span>
              <span className="text-[10px] text-white/30 flex-shrink-0">Locked</span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div 
              className="px-4 py-3 rounded-xl mb-4 text-sm"
              style={{ 
                background: 'rgba(239, 68, 68, 0.2)',
                color: '#EF4444',
                border: '1px solid rgba(239, 68, 68, 0.3)'
              }}
            >
              {error}
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div 
              className="px-4 py-3 rounded-xl mb-4 text-sm"
              style={{ 
                background: 'rgba(16, 185, 129, 0.2)',
                color: '#10B981',
                border: '1px solid rgba(16, 185, 129, 0.3)'
              }}
            >
              {success}
            </div>
          )}

          {/* Save/Cancel Buttons */}
          {isEditing && (
            <div className="flex gap-3 mt-4">
              <button
                onClick={() => {
                  setIsEditing(false);
                  setDisplayName(user.name || '');
                  setError('');
                }}
                className="flex-1 py-3 rounded-xl font-semibold transition-all"
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  color: 'white'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex-1 py-3 rounded-xl font-semibold transition-all disabled:opacity-50"
                style={{
                  background: '#06B6D4',
                  color: '#0F172A'
                }}
              >
                {isSaving ? 'Saving...' : 'Save'}
              </button>
            </div>
          )}
        </div>

        {/* Future Auth Section Placeholder */}
        <div 
          className="rounded-xl p-6 mb-6"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
          }}
        >
          <h2 className="text-white/60 text-xs font-semibold uppercase tracking-wider mb-4">
            Sign-in Methods
          </h2>
          
          <div className="space-y-3">
            {/* Magic Link */}
            <div 
              className="flex items-center justify-between px-4 py-3 rounded-xl"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-white/60">mail</span>
                <span className="text-white">Magic Link</span>
              </div>
              <span 
                className="text-xs font-semibold px-2 py-1 rounded"
                style={{ 
                  background: 'rgba(16, 185, 129, 0.2)',
                  color: '#10B981'
                }}
              >
                Active
              </span>
            </div>

            {/* Google OAuth - Coming Soon */}
            <div 
              className="flex items-center justify-between px-4 py-3 rounded-xl opacity-50"
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <div className="flex items-center gap-3">
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span className="text-white">Google</span>
              </div>
              <span className="text-xs text-white/40">Coming Soon</span>
            </div>
          </div>
        </div>

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="w-full py-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2"
          style={{
            background: 'rgba(239, 68, 68, 0.2)',
            color: '#EF4444',
            border: '1px solid rgba(239, 68, 68, 0.3)'
          }}
        >
          <span className="material-symbols-outlined">logout</span>
          Sign Out
        </button>

        {/* App Info */}
        <div className="text-center mt-8 mb-4">
          <p className="text-white/30 text-xs">Sport X v1.0</p>
          <p className="text-white/20 text-xs mt-1">No Gambling. All game.</p>
        </div>
      </div>

      <BottomNav />
    </div>
  );
};

export default Profile;
