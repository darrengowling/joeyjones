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
      setError("Failed to load your competitions. Please try again.");
    } finally {
      setLoading(false);
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
            ← Friends of PIFA
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
      <div className="container-narrow mx-auto px-4 py-8" data-testid="my-competitions-page">
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
              You're not in any competitions yet
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
          // Competition Cards
          <div className="grid gap-6">
            {competitions.map((comp) => (
              <div
                key={comp.leagueId}
                data-testid={`comp-card-${comp.leagueId}`}
                className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{getSportEmoji(comp.sportKey)}</span>
                    <div>
                      <h2 className="h2 text-xl font-bold text-gray-900">{comp.name}</h2>
                      <p className="text-sm text-gray-500 capitalize">{comp.sportKey}</p>
                    </div>
                  </div>
                  <span
                    data-testid="comp-status"
                    className={`px-3 py-1 rounded-full text-sm font-semibold border ${getStatusChipStyle(comp.status)}`}
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
                          className="flex items-center justify-between p-2 bg-blue-50 rounded-lg border border-blue-200"
                        >
                          <span className="text-sm font-semibold text-blue-900">
                            {asset.name || `${getUiHints(comp.sportKey).assetLabel} ${idx + 1}`}
                          </span>
                          <span className="text-sm text-blue-700 font-bold">
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
                <div className="flex gap-3">
                  <button
                    data-testid="comp-view-btn"
                    onClick={() => navigate(`/competitions/${comp.leagueId}`)}
                    className="btn btn-primary bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 font-semibold flex-1"
                  >
                    View Dashboard
                  </button>
                  <button
                    onClick={() => navigate(`/app/competitions/${comp.leagueId}?tab=fixtures`)}
                    className="btn btn-secondary bg-gray-100 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-200 font-semibold"
                  >
                    Fixtures
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
