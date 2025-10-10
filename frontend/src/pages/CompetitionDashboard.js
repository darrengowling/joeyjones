import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import io from "socket.io-client";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CompetitionDashboard() {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("summary");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Tab data (cached per session)
  const [summary, setSummary] = useState(null);
  const [standings, setStandings] = useState(null);
  const [fixtures, setFixtures] = useState(null);

  // CSV upload state
  const [uploadingCSV, setUploadingCSV] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");

  // Socket.IO connection (Prompt 4)
  const socketRef = useRef(null);

  useEffect(() => {
    // Get user from localStorage
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
      } catch (e) {
        console.error("Error parsing user data:", e);
        navigate("/");
      }
    } else {
      navigate("/");
    }
  }, [navigate]);

  useEffect(() => {
    if (user && leagueId) {
      loadTabData(activeTab);
    }
  }, [user, leagueId, activeTab]);

  // Prompt 4: Socket.IO real-time updates for league events
  useEffect(() => {
    if (!leagueId || !user) return;

    // Initialize Socket.IO connection
    const socket = io(BACKEND_URL, {
      path: "/api/socket.io",
      transports: ["websocket", "polling"]
    });

    socketRef.current = socket;

    socket.on("connect", () => {
      console.log("✅ Dashboard Socket.IO connected");
      
      // Join league room
      socket.emit("join_league_room", { leagueId });
    });

    socket.on("disconnect", () => {
      console.log("❌ Dashboard Socket.IO disconnected");
    });

    // Prompt 4: Listen for league-level events
    
    // Event 1: league_status_changed → refresh summary header
    socket.on("league_status_changed", (data) => {
      console.log("📢 league_status_changed event received:", data);
      if (data.leagueId === leagueId) {
        // Refetch summary to get updated status
        axios.get(`${API}/leagues/${leagueId}/summary`, {
          params: { userId: user.id }
        })
        .then((response) => {
          setSummary(response.data);
          console.log("✅ Summary refreshed with new status");
        })
        .catch((e) => {
          console.error("Error refreshing summary:", e);
        });
      }
    });

    // Event 2: standings_updated → refetch standings
    socket.on("standings_updated", (data) => {
      console.log("📢 standings_updated event received:", data);
      if (data.leagueId === leagueId) {
        // Refetch standings
        axios.get(`${API}/leagues/${leagueId}/standings`)
        .then((response) => {
          setStandings(response.data);
          console.log("✅ Standings refreshed");
        })
        .catch((e) => {
          console.error("Error refreshing standings:", e);
        });
      }
    });

    // Event 3: fixtures_updated → refetch fixtures
    socket.on("fixtures_updated", (data) => {
      console.log("📢 fixtures_updated event received:", data);
      if (data.leagueId === leagueId) {
        // Refetch fixtures
        axios.get(`${API}/leagues/${leagueId}/fixtures`)
        .then((response) => {
          setFixtures(response.data);
          console.log(`✅ Fixtures refreshed (${data.countChanged} fixtures changed)`);
        })
        .catch((e) => {
          console.error("Error refreshing fixtures:", e);
        });
      }
    });

    // Cleanup on unmount
    return () => {
      console.log("🧹 Cleaning up Dashboard Socket.IO connection");
      
      // Leave league room
      if (socket.connected) {
        socket.emit("leave_league", { leagueId });
      }
      
      // Disconnect socket
      socket.disconnect();
      socketRef.current = null;
    };
  }, [leagueId, user]);

  const loadTabData = async (tab) => {
    // Don't refetch if already cached
    if (tab === "summary" && summary) return;
    if (tab === "table" && standings) return;
    if (tab === "fixtures" && fixtures) return;

    setLoading(true);
    setError("");

    try {
      if (tab === "summary") {
        const response = await axios.get(`${API}/leagues/${leagueId}/summary`, {
          params: { userId: user.id }
        });
        setSummary(response.data);
      } else if (tab === "table") {
        const response = await axios.get(`${API}/leagues/${leagueId}/standings`);
        setStandings(response.data);
      } else if (tab === "fixtures") {
        const response = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
        setFixtures(response.data);
      }
    } catch (e) {
      console.error(`Error loading ${tab} data:`, e);
      setError(`Failed to load ${tab} data. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
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

  const formatCurrency = (amount) => {
    return `£${(amount / 1000000).toFixed(1)}M`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const groupFixturesByDate = (fixturesList) => {
    const groups = {};
    fixturesList.forEach((fixture) => {
      const date = formatDate(fixture.startsAt);
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(fixture);
    });
    return groups;
  };

  const handleCSVUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploadingCSV(true);
    setUploadError("");
    setUploadSuccess("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(
        `${API}/leagues/${leagueId}/fixtures/import-csv`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        }
      );

      setUploadSuccess(response.data.message || "Fixtures imported successfully!");
      
      // Refresh fixtures list
      const fixturesResponse = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
      setFixtures(fixturesResponse.data);
      
      // Clear file input
      event.target.value = "";
    } catch (e) {
      console.error("Error uploading CSV:", e);
      setUploadError(e.response?.data?.detail || "Failed to upload CSV. Please check the format.");
    } finally {
      setUploadingCSV(false);
    }
  };

  const renderSummaryTab = () => {
    if (loading && !summary) {
      return (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!summary) return null;

    const isCommissioner = user && summary.commissioner.id === user.id;
    const showCSVHint = isCommissioner && summary.status === "auction_complete" && fixtures?.length === 0;

    return (
      <div className="space-y-6">
        {/* League Info */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center gap-4 mb-4">
            <span className="text-4xl">{getSportEmoji(summary.sportKey)}</span>
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-gray-900">{summary.name}</h2>
              <p className="text-sm text-gray-500 capitalize">{summary.sportKey}</p>
            </div>
            <span className={`px-4 py-2 rounded-full text-sm font-semibold border ${getStatusChipStyle(summary.status)}`}>
              {getStatusLabel(summary.status)}
            </span>
          </div>
          <div className="text-sm text-gray-600">
            <p><strong>Commissioner:</strong> {summary.commissioner.name}</p>
            <p><strong>Timer Settings:</strong> {summary.timerSeconds}s bidding / {summary.antiSnipeSeconds}s anti-snipe</p>
            <p><strong>Total Budget:</strong> {formatCurrency(summary.totalBudget)} | <strong>Slots:</strong> {summary.clubSlots}</p>
          </div>
        </div>

        {/* CSV Import Hint for Commissioner */}
        {showCSVHint && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📊</span>
              <div className="flex-1">
                <h3 className="font-semibold text-blue-900 mb-1">Import Fixtures</h3>
                <p className="text-sm text-blue-800 mb-2">
                  Upload a CSV file to schedule fixtures for your competition.
                </p>
                <button
                  onClick={() => handleTabChange("fixtures")}
                  className="text-sm text-blue-600 hover:underline font-semibold"
                >
                  Go to Fixtures tab →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Your Roster */}
        <div className="bg-white rounded-lg shadow p-6" data-testid="summary-roster">
          <h3 className="text-lg font-bold text-gray-900 mb-3">Your Roster</h3>
          {summary.yourRoster && summary.yourRoster.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {summary.yourRoster.map((assetId, idx) => (
                <span
                  key={idx}
                  className="px-4 py-2 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-200 flex items-center gap-2"
                >
                  <span className="w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center text-xs font-bold">
                    {idx + 1}
                  </span>
                  Team {idx + 1}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No teams acquired yet</p>
          )}
        </div>

        {/* Your Budget */}
        <div className="bg-white rounded-lg shadow p-6" data-testid="summary-budget">
          <h3 className="text-lg font-bold text-gray-900 mb-3">Your Budget</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-green-600">
              {formatCurrency(summary.yourBudgetRemaining)}
            </span>
            <span className="text-sm text-gray-500">remaining</span>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            Spent: {formatCurrency(summary.totalBudget - summary.yourBudgetRemaining)} / {formatCurrency(summary.totalBudget)}
          </div>
        </div>

        {/* Managers List */}
        <div className="bg-white rounded-lg shadow p-6" data-testid="summary-managers">
          <h3 className="text-lg font-bold text-gray-900 mb-3">Managers ({summary.managers.length})</h3>
          <div className="space-y-2">
            {summary.managers.map((manager) => {
              const managerRoster = summary.yourRoster; // TODO: Get actual manager roster
              return (
                <div
                  key={manager.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                      {manager.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="font-semibold text-gray-900">{manager.name}</span>
                    {manager.id === user.id && (
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">You</span>
                    )}
                  </div>
                  <span className="text-sm text-gray-500">
                    {summary.yourRoster.length} / {summary.clubSlots} teams
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  const renderLeagueTableTab = () => {
    if (loading && !standings) {
      return (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!standings || !standings.table) return null;

    const isCricket = standings.sportKey === "cricket";

    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto" data-testid="table-grid">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Manager
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Points
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {isCricket ? "Runs" : "Goals"}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {isCricket ? "Wickets" : "Wins"}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Teams
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {standings.table.map((entry, index) => (
                <tr
                  key={entry.userId}
                  data-testid={`table-row-${entry.userId}`}
                  className={entry.userId === user?.id ? "bg-blue-50" : ""}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {index + 1}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                        {entry.displayName.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-sm font-medium text-gray-900">
                        {entry.displayName}
                        {entry.userId === user?.id && (
                          <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">You</span>
                        )}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-900">
                    {entry.points.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {isCricket ? entry.tiebreakers.runs : entry.tiebreakers.goals}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {isCricket ? entry.tiebreakers.wickets : entry.tiebreakers.wins}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {entry.assetsOwned.length}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {standings.table.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No standings data available yet.
          </div>
        )}
      </div>
    );
  };

  const renderFixturesTab = () => {
    if (loading && !fixtures) {
      return (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    const isCommissioner = user && summary && summary.commissioner.id === user.id;
    const groupedFixtures = fixtures ? groupFixturesByDate(fixtures) : {};
    const hasFixtures = fixtures && fixtures.length > 0;

    return (
      <div className="space-y-6">
        {/* Commissioner CSV Upload Panel */}
        {isCommissioner && (
          <div className="bg-white rounded-lg shadow p-6" data-testid="fixtures-upload">
            <h3 className="text-lg font-bold text-gray-900 mb-3">Import Fixtures (CSV)</h3>
            <p className="text-sm text-gray-600 mb-4">
              Upload a CSV file to schedule fixtures. Required columns: startsAt, homeAssetExternalId, awayAssetExternalId, venue, round, externalMatchId
            </p>
            
            <div className="mb-4">
              <label className="block">
                <span className="sr-only">Choose CSV file</span>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleCSVUpload}
                  disabled={uploadingCSV}
                  className="block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-lg file:border-0
                    file:text-sm file:font-semibold
                    file:bg-blue-50 file:text-blue-700
                    hover:file:bg-blue-100
                    disabled:opacity-50"
                />
              </label>
            </div>

            {uploadingCSV && (
              <div className="text-sm text-blue-600">Uploading...</div>
            )}
            
            {uploadSuccess && (
              <div className="text-sm text-green-600 bg-green-50 border border-green-200 rounded p-3">
                {uploadSuccess}
              </div>
            )}
            
            {uploadError && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
                {uploadError}
              </div>
            )}

            <div className="mt-4 text-sm text-gray-500">
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  alert("Sample CSV format:\nstartsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId\n2025-01-15T19:00:00Z,MCI,LIV,Etihad Stadium,1,match001");
                }}
                className="text-blue-600 hover:underline"
              >
                View sample CSV format
              </a>
            </div>
          </div>
        )}

        {/* Fixtures List */}
        <div data-testid="fixtures-list">
          {!hasFixtures ? (
            <div className="bg-white rounded-lg shadow p-12 text-center" data-testid="fixtures-empty">
              <div className="text-6xl mb-4">📅</div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">No fixtures scheduled yet</h3>
              <p className="text-gray-600">
                {isCommissioner
                  ? "Upload a CSV file above to schedule fixtures for your competition."
                  : "The commissioner will schedule fixtures soon."}
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(groupedFixtures).map(([date, dateFixtures]) => (
                <div key={date} className="bg-white rounded-lg shadow overflow-hidden">
                  <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">{date}</h3>
                  </div>
                  <div className="divide-y divide-gray-200">
                    {dateFixtures.map((fixture) => (
                      <div key={fixture.id} className="p-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 flex-1">
                            <div className="text-sm text-gray-500 w-16">
                              {formatTime(fixture.startsAt)}
                            </div>
                            <div className="flex-1">
                              <div className="text-sm font-medium text-gray-900">
                                Home Team {fixture.homeAssetId} vs {fixture.awayAssetId ? `Away Team ${fixture.awayAssetId}` : "TBD"}
                              </div>
                              {fixture.venue && (
                                <div className="text-xs text-gray-500 mt-1">
                                  📍 {fixture.venue}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            {fixture.round && (
                              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                Round {fixture.round}
                              </span>
                            )}
                            <span
                              className={`text-xs px-3 py-1 rounded-full font-semibold ${
                                fixture.status === "live"
                                  ? "bg-red-100 text-red-700"
                                  : fixture.status === "final"
                                  ? "bg-gray-100 text-gray-700"
                                  : "bg-green-100 text-green-700"
                              }`}
                            >
                              {fixture.status === "live" ? "🔴 Live" : fixture.status === "final" ? "✅ Final" : "⏳ Scheduled"}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-md">
        <div className="container-narrow mx-auto px-4 py-4 flex justify-between items-center">
          <button
            onClick={() => navigate("/app/my-competitions")}
            className="text-blue-600 hover:text-blue-800 font-semibold"
          >
            ← My Competitions
          </button>
          {user && (
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/")}
                className="text-gray-600 hover:text-gray-900"
              >
                Home
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="container-narrow mx-auto px-4 py-8" data-testid="comp-dashboard">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-800">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-t-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                data-testid="tab-summary"
                onClick={() => handleTabChange("summary")}
                className={`py-4 px-6 text-sm font-semibold border-b-2 transition-colors ${
                  activeTab === "summary"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Summary
              </button>
              <button
                data-testid="tab-table"
                onClick={() => handleTabChange("table")}
                className={`py-4 px-6 text-sm font-semibold border-b-2 transition-colors ${
                  activeTab === "table"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                League Table
              </button>
              <button
                data-testid="tab-fixtures"
                onClick={() => handleTabChange("fixtures")}
                className={`py-4 px-6 text-sm font-semibold border-b-2 transition-colors ${
                  activeTab === "fixtures"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Fixtures
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-gray-50 rounded-b-lg p-6">
          {activeTab === "summary" && renderSummaryTab()}
          {activeTab === "table" && renderLeagueTableTab()}
          {activeTab === "fixtures" && renderFixturesTab()}
        </div>
      </div>
    </div>
  );
}
