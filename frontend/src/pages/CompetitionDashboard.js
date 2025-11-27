import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { formatCurrency } from "../utils/currency";
import { getSocket, joinLeagueRoom, leaveLeagueRoom, setSocketUser } from "../utils/socket";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CompetitionDashboard() {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [user, setUser] = useState(null);
  // Read tab from URL parameter, default to "summary"
  const [activeTab, setActiveTab] = useState(searchParams.get("tab") || "summary");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uiHints, setUiHints] = useState({ assetLabel: "Team", assetPlural: "Teams" }); // Default

  // Tab data (cached per session)
  const [summary, setSummary] = useState(null);
  const [standings, setStandings] = useState(null);
  const [fixtures, setFixtures] = useState(null);
  const [matchBreakdown, setMatchBreakdown] = useState(null);

  // CSV upload state
  const [uploadingCSV, setUploadingCSV] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");

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

    // Get global Socket.IO instance
    const socket = getSocket();
    
    // Set socket user for rejoining rooms after reconnect
    setSocketUser(user);

    // Join league room
    joinLeagueRoom(leagueId);

    // Prompt 4: Listen for league-level events
    
    // Event 1: league_status_changed → refresh summary header
    const handleLeagueStatusChanged = (data) => {
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
    };

    // Event 2: standings_updated → refetch standings
    const handleStandingsUpdated = (data) => {
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
    };

    // Event 3: fixtures_updated → refetch fixtures
    const handleFixturesUpdated = (data) => {
      console.log("📢 fixtures_updated event received:", data);
      if (data.leagueId === leagueId) {
        // Refetch fixtures
        axios.get(`${API}/leagues/${leagueId}/fixtures`)
        .then((response) => {
          setFixtures(response.data.fixtures || []);
          console.log(`✅ Fixtures refreshed (${data.countChanged} fixtures changed)`);
        })
        .catch((e) => {
          console.error("Error refreshing fixtures:", e);
          setFixtures([]);
        });
      }
    };

    // Remove existing listeners before adding new ones (prevent duplicates)
    socket.off("league_status_changed", handleLeagueStatusChanged);
    socket.off("standings_updated", handleStandingsUpdated);
    socket.off("fixtures_updated", handleFixturesUpdated);

    // Add event listeners
    socket.on("league_status_changed", handleLeagueStatusChanged);
    socket.on("standings_updated", handleStandingsUpdated);
    socket.on("fixtures_updated", handleFixturesUpdated);

    // Cleanup on unmount
    return () => {
      console.log("🧹 Cleaning up Dashboard Socket.IO connection");
      socket.off("league_status_changed", handleLeagueStatusChanged);
      socket.off("standings_updated", handleStandingsUpdated);
      socket.off("fixtures_updated", handleFixturesUpdated);
      leaveLeagueRoom(leagueId);
    };
  }, [leagueId, user]);

  const loadTabData = async (tab) => {
    // Don't refetch if already cached
    if (tab === "summary" && summary) return;
    if (tab === "table" && standings) return;
    if (tab === "fixtures" && fixtures) return;
    if (tab === "breakdown" && matchBreakdown) return;

    setLoading(true);
    setError("");

    try {
      if (tab === "summary") {
        const response = await axios.get(`${API}/leagues/${leagueId}/summary`, {
          params: { userId: user.id }
        });
        setSummary(response.data);
        
        // Load sport uiHints for dynamic terminology
        if (response.data.sportKey) {
          try {
            const sportResponse = await axios.get(`${API}/sports/${response.data.sportKey}`);
            setUiHints(sportResponse.data.uiHints);
          } catch (e) {
            console.error("Error loading sport info:", e);
          }
        }
      } else if (tab === "table") {
        const response = await axios.get(`${API}/leagues/${leagueId}/standings`);
        setStandings(response.data);
      } else if (tab === "fixtures") {
        const response = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
        setFixtures(response.data.fixtures || []);
      } else if (tab === "breakdown") {
        const response = await axios.get(`${API}/leagues/${leagueId}/match-breakdown`);
        setMatchBreakdown(response.data);
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

  // Using imported formatCurrency from utils

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
      const date = formatDate(fixture.startsAt || fixture.matchDate);
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(fixture);
    });
    return groups;
  };

  const handleScoreUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setUploadError("Please upload a CSV file");
      return;
    }

    setUploadingCSV(true);
    setUploadError("");
    setUploadSuccess("");

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `${API}/scoring/${leagueId}/ingest`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setUploadSuccess(`✅ Scores uploaded successfully! Processed ${response.data.processedRows} rows.`);
      
      // Reload standings after score upload
      setTimeout(() => {
        setStandings(null); // Clear cached standings
        if (activeTab === "standings") {
          loadTabData("standings");
        }
      }, 1000);

    } catch (err) {
      console.error("Score upload error:", err);
      setUploadError(err.response?.data?.detail || "Failed to upload scores. Please check your CSV format.");
    } finally {
      setUploadingCSV(false);
      event.target.value = ""; // Reset file input
    }
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

      // Prompt 6: Pass commissionerId for permission check
      const response = await axios.post(
        `${API}/leagues/${leagueId}/fixtures/import-csv?commissionerId=${user.id}`,
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
            <div className="space-y-2">
              {summary.yourRoster.map((asset, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 bg-blue-50 rounded-lg border border-blue-200"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 bg-blue-200 rounded-full flex items-center justify-center text-xs font-bold">
                      {idx + 1}
                    </span>
                    <span className="text-sm font-semibold text-blue-900">
                      {asset.name || `${uiHints.assetLabel} ${idx + 1}`}
                    </span>
                  </div>
                  <span className="text-sm text-blue-700 font-bold">
                    {formatCurrency(asset.price)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No {uiHints.assetPlural.toLowerCase()} acquired yet</p>
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

        {/* Managers List with Rosters - Everton Bug Fix 5 */}
        <div className="bg-white rounded-lg shadow p-6" data-testid="summary-managers">
          <h3 className="text-lg font-bold text-gray-900 mb-3">Managers ({summary.managers.length})</h3>
          <div className="space-y-4">
            {summary.managers.map((manager) => {
              const managerRoster = manager.roster || [];
              const isCurrentUser = manager.id === user.id;
              
              return (
                <div
                  key={manager.id}
                  className={`p-4 rounded-lg border-2 ${isCurrentUser ? 'bg-blue-50 border-blue-300' : 'bg-gray-50 border-gray-200'}`}
                >
                  {/* Manager Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${isCurrentUser ? 'bg-blue-600' : 'bg-gray-500'}`}>
                        {manager.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">{manager.name}</span>
                          {isCurrentUser && (
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">You</span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          {managerRoster.length} / {summary.clubSlots} {uiHints.assetPlural.toLowerCase()} • {formatCurrency(manager.budgetRemaining)} remaining
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Manager Roster */}
                  {managerRoster.length > 0 ? (
                    <div className="space-y-1 mt-2">
                      {managerRoster.map((asset, idx) => (
                        <div
                          key={idx}
                          className={`flex items-center justify-between p-2 rounded border ${isCurrentUser ? 'bg-white border-blue-200' : 'bg-white border-gray-200'}`}
                        >
                          <div className="flex items-center gap-2">
                            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${isCurrentUser ? 'bg-blue-200 text-blue-900' : 'bg-gray-300 text-gray-700'}`}>
                              {idx + 1}
                            </span>
                            <span className="text-sm font-medium text-gray-900">
                              {asset.name}
                            </span>
                          </div>
                          <span className="text-sm font-semibold text-gray-700">
                            {formatCurrency(asset.price)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 italic mt-2">No {uiHints.assetPlural.toLowerCase()} acquired yet</p>
                  )}
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
                {isCricket && (
                  <>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Catches
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stumpings
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Run Outs
                    </th>
                  </>
                )}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {uiHints.assetPlural}
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
                  {isCricket && (
                    <>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {entry.tiebreakers.catches || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {entry.tiebreakers.stumpings || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {entry.tiebreakers.runOuts || 0}
                      </td>
                    </>
                  )}
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
          <>
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
                    toast("Sample CSV format:\nstartsAt,homeAssetExternalId,awayAssetExternalId,venue,round,externalMatchId\n2025-01-15T19:00:00Z,MCI,LIV,Etihad Stadium,1,match001", {
                      duration: 6000,
                      style: { maxWidth: '600px' }
                    });
                  }}
                  className="text-blue-600 hover:underline"
                >
                  View sample CSV format
                </a>
              </div>
            </div>

            {/* Score Upload Panel */}
            <div className="bg-green-50 border-2 border-green-200 rounded-lg shadow p-6" data-testid="score-upload">
              <h3 className="text-lg font-bold text-green-900 mb-3">📊 Upload Match Scores (CSV)</h3>
              <p className="text-sm text-gray-700 mb-2">
                Upload match results after a game is complete. Required columns: matchId, playerExternalId, runs, wickets, catches, stumpings, runOuts
              </p>
              
              {/* Important Note about Match IDs */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                <p className="text-xs font-semibold text-blue-900 mb-1">📋 Important: Match ID Must Match Exactly</p>
                <p className="text-xs text-blue-800">
                  Use the <span className="font-mono font-semibold">Match ID</span> shown below each fixture in your CSV. 
                  The fixture will automatically be marked as "Completed" after upload.
                </p>
              </div>
              
              <div className="mb-4">
                <label className="block">
                  <span className="sr-only">Choose Scores CSV file</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleScoreUpload}
                    disabled={uploadingCSV}
                    className="block w-full text-sm text-gray-700
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-lg file:border-0
                      file:text-sm file:font-semibold
                      file:bg-green-100 file:text-green-800
                      hover:file:bg-green-200
                      disabled:opacity-50"
                  />
                </label>
              </div>

              {uploadingCSV && (
                <div className="text-sm text-green-700">Uploading scores...</div>
              )}
              
              {uploadSuccess && (
                <div className="text-sm text-green-800 bg-green-100 border border-green-300 rounded p-3 font-semibold">
                  {uploadSuccess}
                </div>
              )}
              
              {uploadError && (
                <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
                  {uploadError}
                </div>
              )}

              <div className="mt-4 text-sm text-gray-600">
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    toast("Sample Scoring CSV format:\nmatchId,playerExternalId,runs,wickets,catches,stumpings,runOuts\nnz-eng-odi-1-2025,harry-brook,67,0,1,0,0\nnz-eng-odi-1-2025,matt-henry,0,2,0,0,0", {
                      duration: 6000,
                      style: { maxWidth: '600px' }
                    });
                  }}
                  className="text-green-700 hover:underline font-medium"
                >
                  View sample scoring CSV format
                </a>
              </div>
            </div>
          </>
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
                              {formatTime(fixture.startsAt || fixture.matchDate)}
                            </div>
                            <div className="flex-1">
                              <div className="text-sm font-medium text-gray-900">
                                {fixture.homeTeam && fixture.awayTeam
                                  ? `${fixture.homeTeam} vs ${fixture.awayTeam}`
                                  : fixture.homeAsset?.name || fixture.awayAsset?.name 
                                  ? `${fixture.homeAsset?.name || fixture.homeAssetId || "Team A"} vs ${fixture.awayAsset?.name || fixture.awayAssetId || "Team B"}`
                                  : fixture.round || fixture.externalMatchId || "Match"}
                              </div>
                              {fixture.venue && (
                                <div className="text-xs text-gray-500 mt-1">
                                  📍 {fixture.venue}
                                </div>
                              )}
                              {/* Display Match ID for CSV reference */}
                              {fixture.externalMatchId && (
                                <div className="text-xs text-gray-600 mt-1 font-mono bg-gray-100 px-2 py-1 rounded inline-block">
                                  Match ID: <span className="font-semibold text-blue-600">{fixture.externalMatchId}</span>
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
                                fixture.status === "completed"
                                  ? "bg-green-100 text-green-700"
                                  : fixture.status === "live"
                                  ? "bg-red-100 text-red-700"
                                  : fixture.status === "final"
                                  ? "bg-gray-100 text-gray-700"
                                  : "bg-yellow-100 text-yellow-700"
                              }`}
                            >
                              {fixture.status === "completed" ? "✅ Completed" : fixture.status === "live" ? "🔴 Live" : fixture.status === "final" ? "✅ Final" : "⏳ Scheduled"}
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

  const renderMatchBreakdownTab = () => {
    if (!matchBreakdown) return <div>Loading match breakdown...</div>;
    
    const { managers, matchNames, fixtureCount } = matchBreakdown;
    
    if (fixtureCount === 0) {
      return (
        <div className="bg-white rounded-lg p-8 text-center">
          <div className="text-6xl mb-4">📊</div>
          <p className="text-gray-600 text-lg mb-2">No completed matches yet</p>
          <p className="text-sm text-gray-500">
            Match-by-match scoring will appear here once fixtures are completed
          </p>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-xl font-bold text-gray-900">Match-by-Match Breakdown</h3>
          <p className="text-sm text-gray-600 mt-1">
            View individual {uiHints.assetLabel.toLowerCase()} scores across all completed matches
          </p>
        </div>

        {/* Horizontal scroll container for mobile */}
        <div className="overflow-x-auto">
          <div className="min-w-max">
            {managers.map((manager, managerIdx) => (
              <div key={manager.userId} className={managerIdx > 0 ? "border-t-4 border-gray-300" : ""}>
                {/* Manager Header */}
                <div className="bg-blue-50 px-6 py-4 border-b border-blue-200">
                  <div className="flex items-center justify-between">
                    <h4 className="text-lg font-bold text-blue-900">
                      {manager.userName}
                    </h4>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-900">
                        {manager.overallTotal}
                      </div>
                      <div className="text-xs text-blue-700 uppercase">Total Points</div>
                    </div>
                  </div>
                </div>

                {/* Match Scores Table */}
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-100 border-b border-gray-200">
                      <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider sticky left-0 bg-gray-100">
                        {uiHints.assetLabel}
                      </th>
                      {matchNames.map((matchName, idx) => (
                        <th key={idx} className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          {matchName}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {manager.assets.map((asset, assetIdx) => (
                      <tr key={asset.assetId} className={assetIdx % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 sticky left-0 bg-inherit">
                          {asset.assetName}
                        </td>
                        {matchNames.map((_, matchIdx) => {
                          const score = asset.matchScores[`match_${matchIdx}`] || 0;
                          return (
                            <td key={matchIdx} className="px-4 py-4 text-center text-sm text-gray-900">
                              <span className={score === 0 ? "text-gray-400 font-normal" : "font-semibold"}>
                                {score}
                              </span>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                    {/* Total Row */}
                    <tr className="bg-blue-100 border-t-2 border-blue-300 font-bold">
                      <td className="px-6 py-4 text-sm text-blue-900 sticky left-0 bg-blue-100">
                        Total
                      </td>
                      {matchNames.map((_, matchIdx) => {
                        const total = manager.matchTotals[`match_${matchIdx}`] || 0;
                        return (
                          <td key={matchIdx} className="px-4 py-4 text-center text-sm text-blue-900">
                            {total}
                          </td>
                        );
                      })}
                    </tr>
                  </tbody>
                </table>
              </div>
            ))}
          </div>
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
              <button
                data-testid="tab-breakdown"
                onClick={() => handleTabChange("breakdown")}
                className={`py-4 px-6 text-sm font-semibold border-b-2 transition-colors ${
                  activeTab === "breakdown"
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Match Breakdown
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-gray-50 rounded-b-lg p-6">
          {activeTab === "summary" && renderSummaryTab()}
          {activeTab === "table" && renderLeagueTableTab()}
          {activeTab === "fixtures" && renderFixturesTab()}
          {activeTab === "breakdown" && renderMatchBreakdownTab()}
        </div>
      </div>
    </div>
  );
}
