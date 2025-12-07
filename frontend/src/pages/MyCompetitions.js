import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { formatCurrency } from "../utils/currency";

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
        return "bg-green-100 text-green-800 border-green-300";
      case "auction_complete":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "pre_auction":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-md app-header">
        <div className="container-narrow mx-auto px-4 py-4 flex justify-between items-center">
          <button
            onClick={() => navigate("/")}
            className="h2 text-blue-600 hover:text-blue-800 cursor-pointer"
          >
            ← Sport X
          </button>
          {user && (
            <div className="flex items-center gap-4">
              <span className="text-gray-700">
                <strong>{user.name}</strong>
              </span>
              <button
                onClick={() => navigate("/")}
                className="btn btn-secondary text-sm text-blue-600 hover:underline"
                data-testid="nav-my-competitions"
              >
                Home
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="container-narrow mx-auto px-2 py-8" data-testid="my-competitions-page">
        <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">My Competitions</div>
        <h1 className="h1 text-3xl font-bold mb-6 text-gray-900">My Competitions</h1>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading your competitions...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-800">{error}</p>
            <button
              onClick={() => loadCompetitions(user.id)}
              className="mt-4 btn btn-primary bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        ) : competitions.length === 0 ? (
          // Empty State
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <div className="text-6xl mb-4">🏆</div>
            <h2 className="h2 text-2xl font-bold mb-4 text-gray-900">
              You&apos;re not in any competitions yet
            </h2>
            <p className="text-gray-600 mb-8">
              Create your own competition or join an existing one with an invite code.
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => navigate("/")}
                className="btn btn-primary bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 font-semibold"
              >
                Create League
              </button>
              <button
                onClick={() => navigate("/")}
                className="btn btn-secondary bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold"
              >
                Enter Join Code
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Bulk Actions Toolbar */}
            {competitions.filter(c => c.isCommissioner && c.status !== "active").length > 0 && (
              <div className="bg-white rounded-lg shadow p-4 mb-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <input
                    type="checkbox"
                    checked={selectedLeagues.size > 0 && selectedLeagues.size === competitions.filter(c => c.isCommissioner && c.status !== "active").length}
                    onChange={toggleSelectAll}
                    className="w-5 h-5 text-blue-600 rounded"
                  />
                  <span className="text-sm text-gray-600">
                    {selectedLeagues.size === 0 ? "Select leagues" : `${selectedLeagues.size} selected`}
                  </span>
                </div>
                {selectedLeagues.size > 0 && (
                  <button
                    onClick={() => setShowDeleteModal(true)}
                    className="btn btn-danger bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-semibold"
                  >
                    🗑️ Delete Selected ({selectedLeagues.size})
                  </button>
                )}
              </div>
            )}

            {/* Competition Cards */}
            <div className="grid gap-6">
              {competitions.map((comp) => (
                <div
                key={comp.leagueId}
                data-testid={`comp-card-${comp.leagueId}`}
                className="bg-white rounded-lg shadow-lg p-4 hover:shadow-xl transition-shadow"
              >
                <div className="flex flex-col gap-2 mb-4">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    {/* Checkbox for commissioner's non-active leagues */}
                    {comp.isCommissioner && comp.status !== "active" && (
                      <input
                        type="checkbox"
                        checked={selectedLeagues.has(comp.leagueId)}
                        onChange={() => toggleSelectLeague(comp.leagueId)}
                        className="w-5 h-5 text-blue-600 rounded flex-shrink-0"
                        onClick={(e) => e.stopPropagation()}
                      />
                    )}
                    <span className="text-3xl flex-shrink-0">{getSportEmoji(comp.sportKey)}</span>
                    <div className="min-w-0 flex-1">
                      <h2 className="h2 text-[var(--t-lg)] font-bold text-gray-900 truncate">{comp.name}</h2>
                      <p className="text-[var(--t-sm)] text-gray-500 capitalize">{comp.sportKey}</p>
                    </div>
                  </div>
                  <span
                    data-testid="comp-status"
                    className={`px-2 py-1 rounded-full text-xs font-semibold border whitespace-nowrap flex-shrink-0 ${getStatusChipStyle(comp.status)}`}
                  >
                    {getStatusLabel(comp.status)}
                  </span>
                </div>

                {/* Your Teams/Players */}
                <div className="mb-4">
                  <p className="text-sm font-semibold text-gray-700 mb-2">
                    Your {getUiHints(comp.sportKey).assetPlural}:
                  </p>
                  {comp.assetsOwned && comp.assetsOwned.length > 0 ? (
                    <div className="space-y-2">
                      {comp.assetsOwned.slice(0, 4).map((asset, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-2 bg-blue-50 rounded-lg border border-blue-200 gap-2"
                        >
                          <span className="text-[var(--t-sm)] font-semibold text-blue-900 truncate break-any">
                            {asset.name || `${getUiHints(comp.sportKey).assetLabel} ${idx + 1}`}
                          </span>
                          <span className="text-[var(--t-sm)] text-blue-700 font-bold whitespace-nowrap">
                            {formatCurrency(asset.price)}
                          </span>
                        </div>
                      ))}
                      {comp.assetsOwned.length > 4 && (
                        <div className="text-sm text-gray-600 italic">
                          + {comp.assetsOwned.length - 4} more {getUiHints(comp.sportKey).assetPlural.toLowerCase()}
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 italic">
                      No {getUiHints(comp.sportKey).assetPlural.toLowerCase()} acquired yet
                    </p>
                  )}
                </div>

                {/* Stats Row */}
                <div className="flex items-center gap-6 mb-4 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <span>👥</span>
                    <span>{comp.managersCount} managers</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>⏱️</span>
                    <span>{comp.timerSeconds}s bidding / {comp.antiSnipeSeconds}s anti-snipe</span>
                  </div>
                </div>

                {/* Next Fixture */}
                {comp.nextFixtureAt && (
                  <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
                    <p className="text-sm text-green-800">
                      <strong>Next fixture:</strong>{" "}
                      <span className="font-semibold">{formatRelativeTime(comp.nextFixtureAt)}</span>
                      {" "}({formatExactDate(comp.nextFixtureAt)})
                    </p>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 flex-wrap">
                  {comp.status === "auction_live" && comp.activeAuctionId && (
                    <button
                      data-testid="comp-auction-btn"
                      onClick={() => navigate(`/auction/${comp.activeAuctionId}`)}
                      className="btn btn-primary bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 font-semibold flex-1 animate-pulse"
                    >
                      🔴 Join Auction Now
                    </button>
                  )}
                  <button
                    data-testid="comp-detail-btn"
                    onClick={() => navigate(`/league/${comp.leagueId}`)}
                    className="btn btn-secondary bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 font-semibold"
                  >
                    League Detail
                  </button>
                  <button
                    data-testid="comp-view-btn"
                    onClick={() => navigate(`/competitions/${comp.leagueId}`)}
                    className="btn btn-primary bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-semibold flex-1"
                  >
                    View Dashboard
                  </button>
                </div>
              </div>
            ))}
          </div>
          </>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">⚠️ Delete Leagues?</h3>
            
            <p className="text-gray-700 mb-4">
              You are about to permanently delete <strong>{selectedLeagues.size} league(s)</strong>.
            </p>
            
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-sm text-red-800 mb-2">
                <strong>This will delete:</strong>
              </p>
              <ul className="text-sm text-red-700 space-y-1 list-disc list-inside">
                <li>Selected leagues</li>
                <li>All participants</li>
                <li>All auction data & bids</li>
                <li>All fixtures & standings</li>
              </ul>
              <p className="text-sm text-red-900 font-semibold mt-3">
                ⚠️ This action cannot be undone!
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                disabled={deleting}
                className="flex-1 btn btn-secondary bg-gray-100 text-gray-700 px-4 py-3 rounded-lg hover:bg-gray-200 font-semibold"
              >
                Cancel
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={deleting}
                className="flex-1 btn btn-danger bg-red-600 text-white px-4 py-3 rounded-lg hover:bg-red-700 font-semibold disabled:opacity-50"
              >
                {deleting ? "Deleting..." : "Delete Forever"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
