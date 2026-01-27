import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { formatCurrency } from "../utils/currency";
import BottomNav from "../components/BottomNav";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function MyCompetitions() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [competitions, setCompetitions] = useState([]);
  const [sports, setSports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedLeagues, setSelectedLeagues] = useState(new Set());
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Set page title
  useEffect(() => {
    document.title = "My Competitions | Sport X";
  }, []);

  useEffect(() => {
    // Get user from localStorage
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
        loadSports();
        loadCompetitions(userData.id);
      } catch (e) {
        console.error("Error parsing user data:", e);
        navigate("/");
      }
    } else {
      // Redirect to home if not logged in
      navigate("/");
    }
  }, [navigate]);

  const loadSports = async () => {
    try {
      const response = await axios.get(`${API}/sports`);
      setSports(response.data);
    } catch (e) {
      console.error("Error loading sports:", e);
    }
  };

  const loadCompetitions = async (userId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/me/competitions`, {
        params: { userId }
      });
      setCompetitions(response.data);
    } catch (e) {
      console.error("Error loading competitions:", e);
      const errorMsg = e.message === "Network Error" 
        ? "Connection lost. Check your internet and refresh the page."
        : "Failed to load your competitions. Please refresh the page.";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectLeague = (leagueId) => {
    const newSelected = new Set(selectedLeagues);
    if (newSelected.has(leagueId)) {
      newSelected.delete(leagueId);
    } else {
      newSelected.add(leagueId);
    }
    setSelectedLeagues(newSelected);
  };

  const toggleSelectAll = () => {
    // Only allow selection of leagues user is commissioner of and not active
    const selectableLeagues = competitions.filter(comp => 
      comp.isCommissioner && comp.status !== "active"
    );
    
    if (selectedLeagues.size === selectableLeagues.length) {
      setSelectedLeagues(new Set());
    } else {
      setSelectedLeagues(new Set(selectableLeagues.map(c => c.leagueId)));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedLeagues.size === 0) return;
    
    setDeleting(true);
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        `${API}/leagues/bulk-delete`,
        { leagueIds: Array.from(selectedLeagues) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      console.log("Bulk delete response:", response.data);
      
      // Show results
      const { results } = response.data;
      if (results.totalDeleted > 0) {
        alert(`✅ Successfully deleted ${results.totalDeleted} league(s)`);
      }
      if (results.totalFailed > 0) {
        const failedReasons = results.failed.map(f => `- ${f.leagueName || f.leagueId}: ${f.reason}`).join('\n');
        alert(`⚠️ Failed to delete ${results.totalFailed} league(s):\n${failedReasons}`);
      }
      
      // Reload competitions
      setSelectedLeagues(new Set());
      setShowDeleteModal(false);
      loadCompetitions(user.id);
    } catch (e) {
      console.error("Error deleting leagues:", e);
      alert("Failed to delete leagues. Please try again.");
    } finally {
      setDeleting(false);
    }
  };

  const getStatusChipStyle = (status) => {
    switch (status) {
      case "auction_live":
        return { background: 'rgba(239, 68, 68, 0.2)', color: '#EF4444', border: '1px solid rgba(239, 68, 68, 0.3)' };
      case "auction_complete":
        return { background: 'rgba(16, 185, 129, 0.2)', color: '#10B981', border: '1px solid rgba(16, 185, 129, 0.3)' };
      case "pre_auction":
        return { background: 'rgba(245, 158, 11, 0.2)', color: '#F59E0B', border: '1px solid rgba(245, 158, 11, 0.3)' };
      default:
        return { background: 'rgba(255, 255, 255, 0.1)', color: 'rgba(255, 255, 255, 0.6)', border: '1px solid rgba(255, 255, 255, 0.2)' };
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "auction_live":
        return "🔴 Auction Live";
      case "auction_complete":
        return "✅ Auction Complete";
      case "pre_auction":
        return "⏳ Pre-Auction";
      default:
        return status;
    }
  };

  const getSportEmoji = (sportKey) => {
    switch (sportKey) {
      case "football":
        return "⚽";
      case "cricket":
        return "🏏";
      default:
        return "🏆";
    }
  };

  const getUiHints = (sportKey) => {
    const sport = sports.find(s => s.key === sportKey);
    return sport?.uiHints || {
      assetLabel: "Team",
      assetPlural: "Teams"
    };
  };

  const formatRelativeTime = (dateString) => {
    if (!dateString) return null;
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = date - now;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffDays > 0) {
      return `in ${diffDays}d`;
    } else if (diffHours > 0) {
      return `in ${diffHours}h`;
    } else if (diffMs > 0) {
      return "soon";
    } else {
      return "passed";
    }
  };

  const formatExactDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  return (
    <div className="min-h-screen" style={{ background: '#0B101B', paddingBottom: '100px' }}>
      {/* Header */}
      <header 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-md z-40 px-4 py-4 flex items-center justify-between"
        style={{
          background: 'rgba(11, 16, 27, 0.95)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-white/60 hover:text-white transition-colors"
        >
          <span>←</span>
          <span className="text-xl font-black tracking-tighter">
            SPORT <span style={{ color: '#06B6D4' }}>X</span>
          </span>
        </button>
        {user && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-white/60">{user.name}</span>
          </div>
        )}
      </header>

      {/* Main Content */}
      <div className="pt-20 px-4" data-testid="my-competitions-page">
        <div className="max-w-2xl mx-auto">
          <div className="text-xs uppercase tracking-widest text-white/40 mb-1">Dashboard</div>
          <h1 className="text-2xl font-bold text-white mb-6">My Competitions</h1>

          {loading ? (
            <div className="text-center py-12">
              <div className="w-12 h-12 border-4 border-[#00F0FF] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-white/60">Loading your competitions...</p>
            </div>
          ) : error ? (
            <div 
              className="rounded-xl p-6 text-center"
              style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}
            >
              <p className="text-red-400">{error}</p>
              <button
                onClick={() => loadCompetitions(user.id)}
                className="mt-4 px-4 py-2 rounded-lg font-semibold transition"
                style={{ background: '#00F0FF', color: '#0B101B' }}
              >
                Retry
              </button>
            </div>
          ) : competitions.length === 0 ? (
            // Empty State
            <div 
              className="rounded-2xl p-8 text-center"
              style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
            >
              <div className="text-6xl mb-4">🏆</div>
              <h2 className="text-xl font-bold text-white mb-4">
                You&apos;re not in any competitions yet
              </h2>
              <p className="text-white/60 mb-8">
                Create your own competition or join an existing one with an invite code.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={() => navigate("/")}
                  className="px-6 py-3 rounded-xl font-bold transition"
                  style={{ background: '#00F0FF', color: '#0B101B' }}
                >
                  Create League
                </button>
                <button
                  onClick={() => navigate("/")}
                  className="px-6 py-3 rounded-xl font-bold transition"
                  style={{ background: 'rgba(255, 255, 255, 0.1)', color: 'white', border: '1px solid rgba(255, 255, 255, 0.2)' }}
                >
                  Enter Join Code
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Bulk Actions Toolbar */}
              {competitions.filter(c => c.isCommissioner && c.status !== "active").length > 0 && (
                <div 
                  className="rounded-xl p-4 mb-6 flex items-center justify-between"
                  style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                >
                  <div className="flex items-center gap-4">
                    <input
                      type="checkbox"
                      checked={selectedLeagues.size > 0 && selectedLeagues.size === competitions.filter(c => c.isCommissioner && c.status !== "active").length}
                      onChange={toggleSelectAll}
                      className="w-5 h-5 rounded"
                      style={{ accentColor: '#00F0FF' }}
                    />
                    <span className="text-sm text-white/60">
                      {selectedLeagues.size === 0 ? "Select leagues" : `${selectedLeagues.size} selected`}
                    </span>
                  </div>
                  {selectedLeagues.size > 0 && (
                    <button
                      onClick={() => setShowDeleteModal(true)}
                      className="px-4 py-2 rounded-lg font-semibold text-sm"
                      style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#EF4444' }}
                    >
                      🗑️ Delete ({selectedLeagues.size})
                    </button>
                  )}
                </div>
              )}

              {/* Competition Cards */}
              <div className="space-y-4">
                {competitions.map((comp) => (
                  <div
                    key={comp.leagueId}
                    data-testid={`comp-card-${comp.leagueId}`}
                    className="rounded-xl p-4 transition-all hover:scale-[1.01]"
                    style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                  >
                    <div className="flex flex-col gap-3 mb-4">
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        {/* Checkbox for commissioner's non-active leagues */}
                        {comp.isCommissioner && comp.status !== "active" && (
                          <input
                            type="checkbox"
                            checked={selectedLeagues.has(comp.leagueId)}
                            onChange={() => toggleSelectLeague(comp.leagueId)}
                            className="w-5 h-5 rounded flex-shrink-0"
                            style={{ accentColor: '#00F0FF' }}
                            onClick={(e) => e.stopPropagation()}
                          />
                        )}
                        <span className="text-3xl flex-shrink-0">{getSportEmoji(comp.sportKey)}</span>
                        <div className="min-w-0 flex-1">
                          <h2 className="text-lg font-bold text-white truncate">{comp.name}</h2>
                          <p className="text-xs text-white/40 capitalize">{comp.sportKey}</p>
                        </div>
                      </div>
                      <span
                        data-testid="comp-status"
                        className="px-3 py-1 rounded-full text-xs font-semibold self-start"
                        style={getStatusChipStyle(comp.status)}
                      >
                        {getStatusLabel(comp.status)}
                      </span>
                    </div>

                    {/* Your Teams/Players */}
                    <div className="mb-4">
                      <p className="text-sm font-semibold text-white/60 mb-2">
                        Your {getUiHints(comp.sportKey).assetPlural}:
                      </p>
                      {comp.assetsOwned && comp.assetsOwned.length > 0 ? (
                        <div className="space-y-2">
                          {comp.assetsOwned.slice(0, 4).map((asset, idx) => (
                            <div
                              key={idx}
                              className="flex items-center justify-between p-2 rounded-lg gap-2"
                              style={{ background: 'rgba(0, 240, 255, 0.1)', border: '1px solid rgba(0, 240, 255, 0.2)' }}
                            >
                              <span className="text-sm font-semibold text-white truncate">
                                {asset.name || `${getUiHints(comp.sportKey).assetLabel} ${idx + 1}`}
                              </span>
                              <span className="text-sm font-bold whitespace-nowrap" style={{ color: '#00F0FF' }}>
                                {formatCurrency(asset.price)}
                              </span>
                            </div>
                          ))}
                          {comp.assetsOwned.length > 4 && (
                            <div className="text-sm text-white/40 italic">
                              + {comp.assetsOwned.length - 4} more {getUiHints(comp.sportKey).assetPlural.toLowerCase()}
                            </div>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-white/40 italic">
                          No {getUiHints(comp.sportKey).assetPlural.toLowerCase()} acquired yet
                        </p>
                      )}
                    </div>

                    {/* Stats Row */}
                    <div className="flex items-center gap-4 mb-4 text-xs text-white/40">
                      <div className="flex items-center gap-1">
                        <span>👥</span>
                        <span>{comp.managersCount} managers</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span>⏱️</span>
                        <span>{comp.timerSeconds}s / {comp.antiSnipeSeconds}s</span>
                      </div>
                    </div>

                    {/* Next Fixture */}
                    {comp.nextFixtureAt && (
                      <div 
                        className="mb-4 p-3 rounded-lg"
                        style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)' }}
                      >
                        <p className="text-sm" style={{ color: '#10B981' }}>
                          <strong>Next fixture:</strong>{" "}
                          <span className="font-semibold">{formatRelativeTime(comp.nextFixtureAt)}</span>
                          {" "}({formatExactDate(comp.nextFixtureAt)})
                        </p>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex flex-col gap-2">
                      {comp.status === "auction_live" && comp.activeAuctionId && (
                        <button
                          data-testid="comp-auction-btn"
                          onClick={() => navigate(`/auction/${comp.activeAuctionId}`)}
                          className="w-full py-3 rounded-xl font-bold text-white animate-pulse"
                          style={{ background: 'linear-gradient(135deg, #EF4444, #DC2626)' }}
                        >
                          🔴 Join Auction Now
                        </button>
                      )}
                      <div className="flex gap-2">
                        <button
                          data-testid="comp-detail-btn"
                          onClick={() => navigate(`/league/${comp.leagueId}`)}
                          className="flex-1 py-2 rounded-xl font-semibold text-sm transition"
                          style={{ background: 'rgba(255, 255, 255, 0.1)', color: 'white' }}
                        >
                          League Detail
                        </button>
                        <button
                          data-testid="comp-view-btn"
                          onClick={() => navigate(`/competitions/${comp.leagueId}`)}
                          className="flex-1 py-2 rounded-xl font-semibold text-sm transition"
                          style={{ background: '#00F0FF', color: '#0B101B' }}
                        >
                          Dashboard
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div 
            className="rounded-2xl max-w-md w-full p-6"
            style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
          >
            <h3 className="text-xl font-bold text-white mb-4">⚠️ Delete Leagues?</h3>
            
            <p className="text-white/60 mb-4">
              You are about to permanently delete <strong className="text-white">{selectedLeagues.size} league(s)</strong>.
            </p>
            
            <div 
              className="rounded-xl p-4 mb-6"
              style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' }}
            >
              <p className="text-sm text-red-400 mb-2">
                <strong>This will delete:</strong>
              </p>
              <ul className="text-sm text-red-400/80 space-y-1 list-disc list-inside">
                <li>Selected leagues</li>
                <li>All participants</li>
                <li>All auction data & bids</li>
                <li>All fixtures & standings</li>
              </ul>
              <p className="text-sm text-red-400 font-semibold mt-3">
                ⚠️ This action cannot be undone!
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                disabled={deleting}
                className="flex-1 py-3 rounded-xl font-semibold transition"
                style={{ background: 'rgba(255, 255, 255, 0.1)', color: 'white' }}
              >
                Cancel
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={deleting}
                className="flex-1 py-3 rounded-xl font-semibold transition disabled:opacity-50"
                style={{ background: '#EF4444', color: 'white' }}
              >
                {deleting ? "Deleting..." : "Delete Forever"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Navigation */}
      <BottomNav onFabClick={() => navigate('/create-competition')} />
    </div>
  );
}
