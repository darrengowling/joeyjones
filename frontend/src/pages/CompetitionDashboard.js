import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { formatCurrency } from "../utils/currency";
import { getSocket, joinLeagueRoom, leaveLeagueRoom, setSocketUser } from "../utils/socket";
import BottomNav from "../components/BottomNav";

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

  // CSV upload state
  const [uploadingCSV, setUploadingCSV] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  
  // Loading states for specific actions
  const [updatingScores, setUpdatingScores] = useState(false);
  const [importingFixture, setImportingFixture] = useState(false);

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

  // Set page title
  useEffect(() => {
    if (summary && summary.league) {
      document.title = `${summary.league.name} - Dashboard | Sport X`;
    }
  }, [summary]);

  useEffect(() => {
    if (user && leagueId) {
      loadTabData(activeTab);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const handleUpdateScores = async () => {
    setUpdatingScores(true);
    try {
      // Step 1: Update fixtures from API-Football
      const response = await axios.post(`${API}/fixtures/update-scores`);
      
      if (response.data.updated > 0) {
        toast.success(`Updated ${response.data.updated} match results! Calculating league points...`);
        
        // Step 2: Trigger score recompute automatically
        try {
          await axios.post(`${API}/leagues/${leagueId}/score/recompute`);
          toast.success("League standings updated successfully!");
        } catch (recomputeError) {
          console.error("Error recomputing scores:", recomputeError);
          toast.warning("Scores updated but league calculation failed. Please refresh the page.");
        }
        
        // Step 3: Force reload fixtures and standings
        setFixtures(null);
        setStandings(null);
        
        const fixturesResponse = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
        setFixtures(fixturesResponse.data.fixtures || []);
        
        const standingsResponse = await axios.get(`${API}/leagues/${leagueId}/standings`);
        setStandings(standingsResponse.data);
        
      } else {
        toast.info("No new match results available yet. Check again after matches complete.");
      }
      
      // Show API usage info
      if (response.data.api_requests_remaining !== undefined) {
        console.log(`API requests remaining this minute: ${response.data.api_requests_remaining}/10`);
      }
    } catch (e) {
      console.error("Error updating scores:", e);
      const errorMsg = e.response?.data?.detail || "Failed to update scores. Check that fixtures have completed and try again in a few minutes. API rate limits may apply.";
      toast.error(errorMsg);
    } finally {
      setUpdatingScores(false);
    }
  };

  const handleUpdateCricketScores = async () => {
    setUpdatingScores(true);
    try {
      // Step 1: Update cricket fixtures from Cricbuzz API
      const response = await axios.post(`${API}/cricket/update-scores`);
      
      if (response.data.updated > 0) {
        toast.success(`Updated ${response.data.updated} cricket match results!`);
        
        // Step 2: Force reload fixtures
        setFixtures(null);
        
        const fixturesResponse = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
        setFixtures(fixturesResponse.data.fixtures || []);
        
      } else {
        toast.info(`No cricket fixtures updated. ${response.data.total_from_api} matches found from API.`);
      }
      
      // Show API usage info
      if (response.data.api_requests_remaining !== undefined) {
        console.log(`Cricbuzz API requests remaining: ${response.data.api_requests_remaining}/100`);
      }
    } catch (e) {
      console.error("Error updating cricket scores:", e);
      toast.error("Failed to update cricket scores. Please try again.");
    } finally {
      setUpdatingScores(false);
    }
  };

  const handleImportNextCricketFixture = async () => {
    setImportingFixture(true);
    try {
      const response = await axios.post(
        `${API}/leagues/${leagueId}/fixtures/import-next-cricket-fixture`
      );

      if (response.data.imported === 1) {
        const fixture = response.data.fixture;
        toast.success(`Imported: ${fixture.homeTeam} vs ${fixture.awayTeam} on ${new Date(fixture.startsAt).toLocaleDateString()}`);
        
        // Reload fixtures
        const fixturesResponse = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
        setFixtures(fixturesResponse.data.fixtures || []);
      } else if (response.data.skipped === 1) {
        toast.info(`Next fixture already imported.`);
      } else {
        toast.warning(`No upcoming Ashes fixtures found. All Tests may be complete or not yet scheduled.`);
      }

      // Log API usage
      if (response.data.api_requests_remaining !== undefined) {
        console.log(`Cricbuzz API requests remaining: ${response.data.api_requests_remaining}/100`);
      }
    } catch (e) {
      console.error("Error importing next cricket fixture:", e);
      const errorMsg = e.response?.data?.detail || "Failed to import fixture. No upcoming matches found or API rate limit reached. Try again later.";
      toast.error(errorMsg);
    } finally {
      setImportingFixture(false);
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

  const handleImportFixturesFromAPI = async (days) => {
    if (!user) return;

    setLoading(true);
    
    try {
      const response = await axios.post(
        `${API}/leagues/${leagueId}/fixtures/import-from-api?commissionerId=${user.id}&days=${days}`
      );

      const message = response.data.message || "Fixtures imported successfully!";
      const apiRemaining = response.data.apiRequestsRemaining;
      
      toast.success(
        `${message}\n\nAPI requests remaining this minute: ${apiRemaining}/10`,
        { duration: 6000 }
      );
      
      // Refresh fixtures list
      const fixturesResponse = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
      setFixtures(fixturesResponse.data.fixtures || []);
      
    } catch (e) {
      console.error("Error importing fixtures from API:", e);
      toast.error(e.response?.data?.detail || "Failed to import fixtures from API. Please try again.");
    } finally {
      setLoading(false);
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
      
      // Trigger score recompute automatically (for fixtures with scores)
      try {
        await axios.post(`${API}/leagues/${leagueId}/score/recompute`);
        toast.success("League standings updated!");
      } catch (recomputeError) {
        console.warn("Score recompute skipped or failed:", recomputeError);
      }
      
      // Refresh fixtures list and standings
      const fixturesResponse = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
      setFixtures(fixturesResponse.data.fixtures || []);
      
      // Reload standings
      setStandings(null);
      const standingsResponse = await axios.get(`${API}/leagues/${leagueId}/summary?userId=${user.id}`);
      setSummary(standingsResponse.data);
      
      // Clear file input
      event.target.value = "";
    } catch (e) {
      console.error("Error uploading CSV:", e);
      setUploadError(e.response?.data?.detail || "Failed to upload CSV. Check the file format matches the template (columns: matchId, playerName, runs, wickets, etc.).");
    } finally {
      setUploadingCSV(false);
    }
  };

  const renderSummaryTab = () => {
    if (loading && !summary) {
      return (
        <div className="text-center py-8">
          <div className="w-8 h-8 border-4 border-[#00F0FF] border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
      );
    }

    if (!summary) return null;

    const isCommissioner = user && summary.commissioner.id === user.id;
    const showCSVHint = isCommissioner && summary.status === "auction_complete" && fixtures?.length === 0;

    return (
      <div className="space-y-4">
        {/* League Info */}
        <div 
          className="rounded-xl p-4"
          style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
        >
          <div className="flex flex-col gap-3 mb-4">
            <div className="flex items-center gap-3">
              <span className="text-4xl flex-shrink-0">{getSportEmoji(summary.sportKey)}</span>
              <div className="flex-1 min-w-0">
                <h2 className="text-lg font-bold text-white truncate">{summary.name}</h2>
                <p className="text-sm text-white/40 capitalize">{summary.sportKey}</p>
              </div>
            </div>
            <span 
              className="px-3 py-1 rounded-full text-xs font-semibold w-fit"
              style={getStatusChipStyle(summary.status)}
            >
              {getStatusLabel(summary.status)}
            </span>
          </div>
          <div className="text-sm text-white/60 space-y-1">
            <p><span className="text-white/40">Commissioner:</span> {summary.commissioner.name}</p>
            <p><span className="text-white/40">Timer:</span> {summary.timerSeconds}s / {summary.antiSnipeSeconds}s anti-snipe</p>
            <p><span className="text-white/40">Budget:</span> {formatCurrency(summary.totalBudget)} | <span className="text-white/40">Slots:</span> {summary.clubSlots}</p>
          </div>
        </div>

        {/* CSV Import Hint for Commissioner */}
        {showCSVHint && (
          <div 
            className="rounded-xl p-4"
            style={{ background: 'rgba(0, 240, 255, 0.1)', border: '1px solid rgba(0, 240, 255, 0.2)' }}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl">📊</span>
              <div className="flex-1">
                <h3 className="font-semibold text-white mb-1">Import Fixtures</h3>
                <p className="text-sm text-white/60 mb-2">
                  Upload a CSV file to schedule fixtures for your competition.
                </p>
                <button
                  onClick={() => handleTabChange("fixtures")}
                  className="text-sm font-semibold hover:underline"
                  style={{ color: '#00F0FF' }}
                >
                  Go to Fixtures tab →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Your Roster */}
        <div 
          className="rounded-xl p-4"
          style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
          data-testid="summary-roster"
        >
          <h3 className="text-lg font-bold text-white mb-3">Your Roster</h3>
          {summary.yourRoster && summary.yourRoster.length > 0 ? (
            <div className="space-y-2">
              {summary.yourRoster.map((asset, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 rounded-lg gap-2"
                  style={{ background: 'rgba(0, 240, 255, 0.1)', border: '1px solid rgba(0, 240, 255, 0.2)' }}
                >
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span 
                      className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
                      style={{ background: 'rgba(0, 240, 255, 0.3)', color: '#00F0FF' }}
                    >
                      {idx + 1}
                    </span>
                    <span className="text-sm font-semibold text-white truncate">
                      {asset.name || `${uiHints.assetLabel} ${idx + 1}`}
                    </span>
                  </div>
                  <span className="text-sm font-bold whitespace-nowrap flex-shrink-0" style={{ color: '#00F0FF' }}>
                    {formatCurrency(asset.price)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-white/40 italic">No {uiHints.assetPlural.toLowerCase()} acquired yet</p>
          )}
        </div>

        {/* Your Budget */}
        <div 
          className="rounded-xl p-4"
          style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
          data-testid="summary-budget"
        >
          <h3 className="text-lg font-bold text-white mb-3">Your Budget</h3>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold" style={{ color: '#10B981' }}>
              {formatCurrency(summary.yourBudgetRemaining)}
            </span>
            <span className="text-sm text-white/40">remaining</span>
          </div>
          <div className="mt-2 text-sm text-white/60">
            Spent: {formatCurrency(summary.totalBudget - summary.yourBudgetRemaining)} / {formatCurrency(summary.totalBudget)}
          </div>
        </div>

        {/* Managers List with Rosters */}
        <div 
          className="rounded-xl p-4"
          style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
          data-testid="summary-managers"
        >
          <h3 className="text-lg font-bold text-white mb-3">Managers ({summary.managers.length})</h3>
          <div className="space-y-3">
            {summary.managers.map((manager) => {
              const managerRoster = manager.roster || [];
              const isCurrentUser = manager.id === user.id;
              
              return (
                <div
                  key={manager.id}
                  className="p-3 rounded-xl"
                  style={{ 
                    background: isCurrentUser ? 'rgba(0, 240, 255, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                    border: isCurrentUser ? '1px solid rgba(0, 240, 255, 0.3)' : '1px solid rgba(255, 255, 255, 0.1)'
                  }}
                >
                  {/* Manager Header */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
                        style={{ background: isCurrentUser ? '#00F0FF' : 'rgba(255, 255, 255, 0.2)' }}
                      >
                        {manager.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white">{manager.name}</span>
                          {isCurrentUser && (
                            <span 
                              className="text-xs px-2 py-0.5 rounded-full font-medium"
                              style={{ background: 'rgba(0, 240, 255, 0.3)', color: '#00F0FF' }}
                            >
                              You
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-white/40">
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
                          className="flex items-center justify-between p-2 rounded-lg"
                          style={{ background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                        >
                          <div className="flex items-center gap-2">
                            <span 
                              className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold"
                              style={{ background: isCurrentUser ? 'rgba(0, 240, 255, 0.3)' : 'rgba(255, 255, 255, 0.2)', color: isCurrentUser ? '#00F0FF' : 'white' }}
                            >
                              {idx + 1}
                            </span>
                            <span className="text-sm font-medium text-white">
                              {asset.name}
                            </span>
                          </div>
                          <span className="text-sm font-semibold text-white/60">
                            {formatCurrency(asset.price)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-white/40 italic mt-2">No {uiHints.assetPlural.toLowerCase()} acquired yet</p>
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
          <div className="w-8 h-8 border-4 border-[#00F0FF] border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
      );
    }

    if (!standings || !standings.table) return null;

    const isCricket = standings.sportKey === "cricket";

    return (
      <div 
        className="rounded-xl overflow-hidden"
        style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
      >
        <div className="overflow-x-auto" data-testid="table-grid">
          <table className="min-w-full">
            <thead style={{ background: 'rgba(0, 0, 0, 0.3)' }}>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                  Manager
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                  Points
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                  {isCricket ? "Runs" : "Goals"}
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                  {isCricket ? "Wickets" : "Wins"}
                </th>
                {!isCricket && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                    Draws
                  </th>
                )}
                {isCricket && (
                  <>
                    <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                      Catches
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                      Stumpings
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                      Run Outs
                    </th>
                  </>
                )}
                <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">
                  {uiHints.assetPlural}
                </th>
              </tr>
            </thead>
            <tbody>
              {standings.table.map((entry, index) => (
                <tr
                  key={entry.userId}
                  data-testid={`table-row-${entry.userId}`}
                  style={{ 
                    background: entry.userId === user?.id ? 'rgba(0, 240, 255, 0.1)' : 'transparent',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
                  }}
                >
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-white">
                    {index + 1}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                        style={{ background: entry.userId === user?.id ? '#00F0FF' : 'rgba(255, 255, 255, 0.2)', color: entry.userId === user?.id ? '#0B101B' : 'white' }}
                      >
                        {entry.displayName.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-sm font-medium text-white">
                        {entry.displayName}
                        {entry.userId === user?.id && (
                          <span 
                            className="ml-2 text-xs px-2 py-0.5 rounded-full"
                            style={{ background: 'rgba(0, 240, 255, 0.3)', color: '#00F0FF' }}
                          >
                            You
                          </span>
                        )}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-bold" style={{ color: '#00F0FF' }}>
                    {entry.points.toFixed(1)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-white/60">
                    {isCricket ? entry.tiebreakers.runs : entry.tiebreakers.goals}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-white/60">
                    {isCricket ? entry.tiebreakers.wickets : entry.tiebreakers.wins}
                  </td>
                  {!isCricket && (
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-white/60">
                      {entry.tiebreakers.draws || 0}
                    </td>
                  )}
                  {isCricket && (
                    <>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-white/60">
                        {entry.tiebreakers.catches || 0}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-white/60">
                        {entry.tiebreakers.stumpings || 0}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-white/60">
                        {entry.tiebreakers.runOuts || 0}
                      </td>
                    </>
                  )}
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-white/60">
                    {entry.assetsOwned.length}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {standings.table.length === 0 && (
          <div className="text-center py-8 text-white/40">
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
          <div className="w-8 h-8 border-4 border-[#00F0FF] border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
      );
    }

    const isCommissioner = user && summary && summary.commissioner.id === user.id;
    const groupedFixtures = fixtures ? groupFixturesByDate(fixtures) : {};
    const hasFixtures = fixtures && fixtures.length > 0;

    return (
      <div className="space-y-4">
        {/* Commissioner Fixtures & Scores Management */}
        {isCommissioner && (
          <>
            {/* PL/CL: API-based Fixtures & Scores */}
            {summary && summary.sportKey === "football" && summary.competitionCode !== 'AFCON' && (
              <div 
                className="rounded-xl p-4"
                style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
              >
                <h3 className="text-lg font-bold text-white mb-4">📊 Manage Fixtures & Scores</h3>
                
                {/* Import Fixtures Section */}
                <div className="mb-4">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="h-px flex-1" style={{ background: 'rgba(255, 255, 255, 0.1)' }}></div>
                    <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide">Import Fixtures</h4>
                    <div className="h-px flex-1" style={{ background: 'rgba(255, 255, 255, 0.1)' }}></div>
                  </div>
                  <p className="text-sm text-white/60 mb-3">Fetch upcoming matches from Football-Data.org</p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleImportFixturesFromAPI(7)}
                      disabled={loading}
                      className="px-4 py-2 rounded-lg font-semibold flex-1 text-sm disabled:opacity-50"
                      style={{ background: '#00F0FF', color: '#0B101B' }}
                    >
                      {loading ? "Importing..." : "Next 7 Days"}
                    </button>
                    <button
                      onClick={() => handleImportFixturesFromAPI(30)}
                      disabled={loading}
                      className="px-4 py-2 rounded-lg font-semibold flex-1 text-sm disabled:opacity-50"
                      style={{ background: 'rgba(0, 240, 255, 0.2)', color: '#00F0FF' }}
                    >
                      {loading ? "Importing..." : "Next 30 Days"}
                    </button>
                  </div>
                </div>

                {/* Update Scores Section */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="h-px bg-gray-300 flex-1"></div>
                    <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Update Scores</h4>
                    <div className="h-px bg-gray-300 flex-1"></div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">Get latest results for completed matches</p>
                  <div className="text-center">
                    <button
                      onClick={handleUpdateScores}
                      disabled={updatingScores}
                      className="bg-green-600 text-white px-8 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold inline-flex items-center gap-2"
                    >
                      {updatingScores && (
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      )}
                      {updatingScores ? "Updating..." : "Update All Scores"}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-3 text-center">💡 Scores update automatically from the API</p>
                </div>
              </div>
            )}

            {/* AFCON: CSV-based Fixtures & Scores */}
            {summary && summary.competitionCode === 'AFCON' && (
              <div className="bg-white rounded-lg shadow-md p-4">
                <h3 className="text-xl font-bold text-gray-900 mb-6">📊 Manage Fixtures & Scores (CSV)</h3>
                
                {/* Step 1: Download Template */}
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="h-px bg-gray-300 flex-1"></div>
                    <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Step 1: Download Template</h4>
                    <div className="h-px bg-gray-300 flex-1"></div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">Get pre-filled fixture list with all matches</p>
                  <a
                    href={`${API}/templates/afcon_2025_fixtures_with_names.csv`}
                    download="afcon_2025_fixtures_with_names.csv"
                    className="flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 font-semibold text-sm w-full"
                  >
                    <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span>Download Template</span>
                  </a>
                </div>

                {/* Step 2: Add Scores & Upload */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="h-px bg-gray-300 flex-1"></div>
                    <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Step 2: Add Scores & Upload</h4>
                    <div className="h-px bg-gray-300 flex-1"></div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">Fill in goalsHome/goalsAway in Excel, then upload</p>
                  
                  <div className="mb-3">
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
                    <div className="text-sm text-blue-600 text-center">Uploading...</div>
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

                  <p className="text-xs text-gray-500 mt-3 text-center">💡 Re-upload same file after each matchday</p>
                </div>
              </div>
            )}

            {/* Cricket: Hybrid Fixtures & Scores */}
            {summary && summary.sportKey === "cricket" && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-6">📊 Manage Fixtures & Scores</h3>
                
                {/* Import Next Fixture Section */}
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="h-px bg-gray-300 flex-1"></div>
                    <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Import Next Fixture</h4>
                    <div className="h-px bg-gray-300 flex-1"></div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">Add next Australia vs England Test match</p>
                  <div className="text-center">
                    <button
                      onClick={handleImportNextCricketFixture}
                      disabled={importingFixture}
                      className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold inline-flex items-center gap-2"
                    >
                      {importingFixture && (
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      )}
                      {importingFixture ? "Importing..." : "Import Next Ashes Fixture"}
                    </button>
                  </div>
                </div>

                {/* Update Player Scores Section */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className="h-px bg-gray-300 flex-1"></div>
                    <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">Update Player Scores</h4>
                    <div className="h-px bg-gray-300 flex-1"></div>
                  </div>
                  
                  {/* Option 1: API */}
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Option 1: Automatic (API)</p>
                    <div className="text-center">
                      <button
                        onClick={handleUpdateCricketScores}
                        disabled={loading}
                        className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
                      >
                        {loading ? "Updating..." : "Fetch Latest from Cricbuzz"}
                      </button>
                    </div>
                  </div>

                  {/* Option 2: CSV */}
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">Option 2: Manual (CSV)</p>
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

                  <p className="text-xs text-gray-500 mt-3 text-center">💡 Import one fixture at a time as matches complete</p>
                </div>
              </div>
            )}
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
                  <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">{date}</h3>
                  </div>
                  <div className="divide-y divide-gray-200">
                    {dateFixtures.map((fixture) => (
                      <div key={fixture.id} className="p-3 hover:bg-gray-50">
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center gap-2">
                            <div className="text-xs text-gray-500 flex-shrink-0">
                              {formatTime(fixture.startsAt || fixture.matchDate)}
                            </div>
                            {fixture.round && (
                              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded whitespace-nowrap">
                                R{fixture.round}
                              </span>
                            )}
                            <span
                              className={`text-xs px-2 py-1 rounded-full font-semibold whitespace-nowrap ml-auto ${
                                fixture.status === "completed" || fixture.status === "ft" || fixture.status === "final"
                                  ? "bg-green-100 text-green-700"
                                  : fixture.status === "live"
                                  ? "bg-red-100 text-red-700"
                                  : "bg-yellow-100 text-yellow-700"
                              }`}
                            >
                              {fixture.status === "completed" || fixture.status === "ft" || fixture.status === "final" ? "✅" : fixture.status === "live" ? "🔴" : "⏳"}
                            </span>
                          </div>
                          <div className="text-sm font-medium text-gray-900">
                            {fixture.homeTeam && fixture.awayTeam
                              ? (
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="truncate">{fixture.homeTeam}</span>
                                  {(fixture.status === "ft" || fixture.status === "completed" || fixture.status === "final") && fixture.goalsHome !== null && fixture.goalsAway !== null ? (
                                    <span className="font-bold text-base text-blue-600 flex-shrink-0">
                                      {fixture.goalsHome} - {fixture.goalsAway}
                                    </span>
                                  ) : (
                                    <span className="text-gray-400 flex-shrink-0">vs</span>
                                  )}
                                  <span className="truncate">{fixture.awayTeam}</span>
                                </div>
                              )
                              : fixture.homeAsset?.name || fixture.awayAsset?.name 
                              ? `${fixture.homeAsset?.name || fixture.homeAssetId || "Team A"} vs ${fixture.awayAsset?.name || fixture.awayAssetId || "Team B"}`
                              : fixture.round || fixture.externalMatchId || "Match"}
                          </div>
                          {fixture.venue && (
                            <div className="text-xs text-gray-500">
                              📍 {fixture.venue}
                            </div>
                          )}
                          {fixture.externalMatchId && (
                            <div className="text-xs text-gray-600 font-mono bg-gray-100 px-2 py-1 rounded inline-block w-fit">
                              ID: <span className="font-semibold text-blue-600">{fixture.externalMatchId}</span>
                            </div>
                          )}
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
          <div>
            <button
              onClick={() => navigate("/app/my-competitions")}
              className="text-blue-600 hover:text-blue-800 font-semibold"
            >
              ← My Competitions
            </button>
            <div className="text-xs uppercase tracking-wide text-gray-500 mt-1">Competition Dashboard</div>
          </div>
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
