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
  
  // Admin reports state
  const [isAdmin, setIsAdmin] = useState(false);
  const [reports, setReports] = useState([]);
  const [loadingReports, setLoadingReports] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [showReportModal, setShowReportModal] = useState(false);

  useEffect(() => {
    // Load user from localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      setUser(parsed);
      setDisplayName(parsed.name || '');
      
      // Check if user is admin and load reports
      checkAdminAndLoadReports(parsed.id);
    }
  }, []);
  
  const checkAdminAndLoadReports = async (userId) => {
    try {
      const response = await axios.get(`${API}/api/admin/reports`, {
        headers: { 'X-User-ID': userId }
      });
      setIsAdmin(true);
      setReports(response.data);
    } catch (err) {
      // Not admin or error - that's fine, just don't show reports section
      setIsAdmin(false);
    }
  };
  
  const loadFullReport = async (reportId) => {
    setLoadingReports(true);
    try {
      const response = await axios.get(`${API}/api/admin/reports/${reportId}`, {
        headers: { 'X-User-ID': user.id }
      });
      setSelectedReport(response.data);
      setShowReportModal(true);
    } catch (err) {
      console.error('Failed to load report:', err);
    } finally {
      setLoadingReports(false);
    }
  };
  
  const downloadReportCSV = async (reportId, leagueName) => {
    try {
      const response = await axios.get(`${API}/api/admin/reports/${reportId}/csv`, {
        headers: { 'X-User-ID': user.id },
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `auction_report_${leagueName.replace(/\s+/g, '_')}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download report:', err);
    }
  };
  
  const formatCurrency = (amount) => {
    if (!amount) return '£0';
    return `£${(amount / 1000000).toFixed(1)}m`;
  };
  
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

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

        {/* Auction Reports Section - Admin Only */}
        {isAdmin && (
          <div 
            className="rounded-xl p-6 mb-6"
            style={{
              background: 'rgba(6, 182, 212, 0.05)',
              border: '1px solid rgba(6, 182, 212, 0.2)'
            }}
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-cyan-400">analytics</span>
              <h2 className="text-cyan-400 text-xs font-semibold uppercase tracking-wider">
                Auction Reports
              </h2>
            </div>
            
            {reports.length === 0 ? (
              <p className="text-white/40 text-sm">No auction reports yet. Reports are auto-generated when auctions complete.</p>
            ) : (
              <div className="space-y-3">
                {reports.map((report) => (
                  <div 
                    key={report.id}
                    className="rounded-xl p-4"
                    style={{
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid rgba(255, 255, 255, 0.1)'
                    }}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="text-white font-semibold">{report.leagueName}</h3>
                        <p className="text-white/40 text-xs">{formatDate(report.generatedAt)}</p>
                      </div>
                      <span 
                        className="text-xs px-2 py-1 rounded"
                        style={{ 
                          background: report.sportKey === 'football' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(168, 85, 247, 0.2)',
                          color: report.sportKey === 'football' ? '#22C55E' : '#A855F7'
                        }}
                      >
                        {report.sportKey}
                      </span>
                    </div>
                    
                    {/* Quick Stats */}
                    <div className="grid grid-cols-3 gap-2 mb-3 text-center">
                      <div className="py-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)' }}>
                        <div className="text-white font-bold">{report.summary?.totalParticipants || 0}</div>
                        <div className="text-white/40 text-xs">Users</div>
                      </div>
                      <div className="py-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)' }}>
                        <div className="text-white font-bold">{report.summary?.totalClubsSold || 0}</div>
                        <div className="text-white/40 text-xs">Sold</div>
                      </div>
                      <div className="py-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)' }}>
                        <div className="text-cyan-400 font-bold">{formatCurrency(report.summary?.totalRevenue)}</div>
                        <div className="text-white/40 text-xs">Revenue</div>
                      </div>
                    </div>
                    
                    {/* Actions */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => loadFullReport(report.id)}
                        disabled={loadingReports}
                        className="flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 transition-all"
                        style={{ 
                          background: 'rgba(255, 255, 255, 0.1)',
                          color: 'white'
                        }}
                      >
                        <span className="material-symbols-outlined text-sm">visibility</span>
                        View
                      </button>
                      <button
                        onClick={() => downloadReportCSV(report.id, report.leagueName)}
                        className="flex-1 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-1 transition-all"
                        style={{ 
                          background: '#06B6D4',
                          color: '#0F172A'
                        }}
                      >
                        <span className="material-symbols-outlined text-sm">download</span>
                        CSV
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

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

      {/* Report Detail Modal */}
      {showReportModal && selectedReport && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0, 0, 0, 0.8)' }}
          onClick={() => setShowReportModal(false)}
        >
          <div 
            className="w-full max-w-lg max-h-[80vh] overflow-y-auto rounded-2xl p-6"
            style={{ background: '#1E293B' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-white font-bold text-lg">{selectedReport.leagueName}</h2>
                <p className="text-white/40 text-sm">{formatDate(selectedReport.generatedAt)}</p>
              </div>
              <button 
                onClick={() => setShowReportModal(false)}
                className="text-white/60 hover:text-white"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            
            {/* Summary Stats */}
            <div className="rounded-xl p-4 mb-4" style={{ background: 'rgba(6, 182, 212, 0.1)' }}>
              <h3 className="text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-3">Summary</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-white/60">Duration:</span> <span className="text-white">{selectedReport.summary?.durationFormatted || 'N/A'}</span></div>
                <div><span className="text-white/60">Participants:</span> <span className="text-white">{selectedReport.summary?.totalParticipants}</span></div>
                <div><span className="text-white/60">Lots:</span> <span className="text-white">{selectedReport.summary?.totalLots}</span></div>
                <div><span className="text-white/60">Sold:</span> <span className="text-white">{selectedReport.summary?.totalClubsSold}</span></div>
                <div><span className="text-white/60">Total Bids:</span> <span className="text-white">{selectedReport.summary?.totalBids}</span></div>
                <div><span className="text-white/60">Avg Bids/Lot:</span> <span className="text-white">{selectedReport.summary?.avgBidsPerLot}</span></div>
                <div><span className="text-white/60">Total Revenue:</span> <span className="text-cyan-400 font-bold">{formatCurrency(selectedReport.summary?.totalRevenue)}</span></div>
                <div><span className="text-white/60">Highest Bid:</span> <span className="text-cyan-400 font-bold">{formatCurrency(selectedReport.summary?.highestBid)}</span></div>
              </div>
            </div>
            
            {/* User Summaries */}
            <div className="mb-4">
              <h3 className="text-white/60 text-xs font-semibold uppercase tracking-wider mb-3">User Results</h3>
              <div className="space-y-2">
                {selectedReport.userSummaries?.map((userSum, idx) => (
                  <div 
                    key={idx}
                    className="rounded-lg p-3"
                    style={{ background: 'rgba(255, 255, 255, 0.05)' }}
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-white font-semibold">{userSum.userName}</span>
                      <span className="text-cyan-400 font-bold">{formatCurrency(userSum.totalSpent)}</span>
                    </div>
                    <div className="text-white/60 text-xs">
                      {userSum.teamsWon} teams won • {userSum.totalBidsPlaced} bids • {userSum.winRate}% win rate
                    </div>
                    {userSum.teamsWonNames?.length > 0 && (
                      <div className="text-white/40 text-xs mt-1">
                        Teams: {userSum.teamsWonNames.join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Lots Breakdown - Collapsible */}
            <details className="mb-4">
              <summary className="text-white/60 text-xs font-semibold uppercase tracking-wider mb-3 cursor-pointer hover:text-white">
                Lots Breakdown ({selectedReport.lotsBreakdown?.length || 0} lots)
              </summary>
              <div className="space-y-1 mt-3 max-h-60 overflow-y-auto">
                {selectedReport.lotsBreakdown?.map((lot, idx) => (
                  <div 
                    key={idx}
                    className="flex justify-between items-center py-2 px-3 rounded text-sm"
                    style={{ background: lot.sold ? 'rgba(255, 255, 255, 0.03)' : 'rgba(239, 68, 68, 0.1)' }}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-white/40 text-xs w-6">#{lot.queuePosition}</span>
                      <span className={lot.sold ? 'text-white' : 'text-red-400'}>{lot.clubName}</span>
                    </div>
                    <div className="text-right">
                      {lot.sold ? (
                        <>
                          <span className="text-cyan-400 font-medium">{formatCurrency(lot.winningBid)}</span>
                          <span className="text-white/40 text-xs ml-2">{lot.winnerName}</span>
                        </>
                      ) : (
                        <span className="text-red-400 text-xs">Unsold</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </details>
            
            {/* Download Button */}
            <button
              onClick={() => {
                downloadReportCSV(selectedReport.id, selectedReport.leagueName);
                setShowReportModal(false);
              }}
              className="w-full py-3 rounded-xl font-semibold flex items-center justify-center gap-2"
              style={{ background: '#06B6D4', color: '#0F172A' }}
            >
              <span className="material-symbols-outlined">download</span>
              Download Full CSV
            </button>
          </div>
        </div>
      )}

      <BottomNav />
    </div>
  );
};

export default Profile;
