import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { formatCurrency } from "../utils/currency";
import { useSocketRoom } from "../hooks/useSocketRoom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LeagueDetail() {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  const [league, setLeague] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [standings, setStandings] = useState([]);
  const [assets, setAssets] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingScores, setLoadingScores] = useState(false);
  const [loadingAssets, setLoadingAssets] = useState(false);
  const [sport, setSport] = useState(null);
  const [uiHints, setUiHints] = useState({ assetLabel: "Club", assetPlural: "Clubs" }); // Default to football
  const [scoringOverrides, setScoringOverrides] = useState(null);
  const [editingScoring, setEditingScoring] = useState(false);
  const [savingScoring, setSavingScoring] = useState(false);
  // Prompt E: Team management state
  const [availableAssets, setAvailableAssets] = useState([]);
  const [selectedAssetIds, setSelectedAssetIds] = useState([]);
  const [editingAssets, setEditingAssets] = useState(false);
  const [loadingAssetSelection, setLoadingAssetSelection] = useState(false);
  const [importingFixtures, setImportingFixtures] = useState(false);
  const [fixturesImported, setFixturesImported] = useState(false);
  const [startingAuction, setStartingAuction] = useState(false);
  // Fixtures state
  const [fixtures, setFixtures] = useState([]);
  const [loadingFixtures, setLoadingFixtures] = useState(false);

  // Use shared socket room hook
  const { socket, connected, ready, listenerCount } = useSocketRoom('league', leagueId, { user });

  // Initial setup: load user and data
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
    }
    loadLeague();
    loadParticipants();
    loadStandings();
    loadFixtures();
    loadAssets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leagueId]);

  // Set page title
  useEffect(() => {
    if (league) {
      document.title = `${league.name} - Competition | Sport X`;
    } else {
      document.title = "Competition Details | Sport X";
    }
  }, [league]);

  // Socket event handlers - single useEffect with proper cleanup
  useEffect(() => {
    if (!user) return;

    console.log(`🎧 [LeagueDetail] Setting up socket listeners (Count: ${listenerCount})`);
    
    // Prompt D: Join league room on connect
    socket.emit('join_league', { leagueId, userId: user.id }, (ack) => {
      if (ack && ack.ok) {
        console.log(`✅ Joined league room: ${ack.room}, size: ${ack.roomSize}`);
      }
    });

    // Handle member updates (upsert pattern)
    const onMemberJoined = (data) => {
      console.log('📢 Member joined event received:', data);
      setParticipants(prev => {
        const existingIndex = prev.findIndex(p => p.userId === data.userId);
        
        const newMember = {
          userId: data.userId,
          userName: data.displayName,
          joinedAt: data.joinedAt
        };
        
        if (existingIndex >= 0) {
          console.log('🔄 Updating existing member:', data.userId);
          const updated = [...prev];
          updated[existingIndex] = newMember;
          return updated;
        } else {
          console.log('✅ Adding new member to list:', newMember);
          return [...prev, newMember];
        }
      });
    };
    
    // Handle sync_members for reconciliation (source of truth)
    const onSyncMembers = (data) => {
      console.log('🔄 Sync members received:', data);
      if (data.members && Array.isArray(data.members)) {
        const updatedParticipants = data.members.map(member => ({
          userId: member.userId,
          userName: member.displayName,
          joinedAt: member.joinedAt
        }));
        console.log(`✅ Replacing participants with ${updatedParticipants.length} members from sync_members`);
        setParticipants(updatedParticipants);
      }
    };
    
    // Handle league status changes for instant auction start/complete notifications
    const onLeagueStatusChanged = (data) => {
      console.log('🎯 League status changed event received:', data);
      if (data.leagueId === leagueId) {
        if (data.status === 'auction_created' || data.status === 'auction_started' || data.status === 'auction_active') {
          console.log('✅ Auction created/started/active - updating league data');
          setLeague(prev => ({
            ...prev,
            status: 'active',
            activeAuctionId: data.auctionId
          }));
        } else if (data.status === 'auction_complete') {
          console.log('✅ Auction completed - updating league data');
          setLeague(prev => ({
            ...prev,
            status: 'completed',
            activeAuctionId: null
          }));
        }
      }
    };
    
    // Register event listeners
    socket.on('member_joined', onMemberJoined);
    socket.on('sync_members', onSyncMembers);
    socket.on('league_status_changed', onLeagueStatusChanged);
    
    // Setup aggressive 3s polling for real-time updates (EVERTON FIX)
    // Socket.IO should work, but this ensures UI updates even if events are missed
    const pollInterval = setInterval(() => {
      console.log('🔄 Polling league status...');
      loadLeague();
      loadParticipants();
    }, 3000);
    
    // Cleanup function
    return () => {
      console.log('🧹 [LeagueDetail] Removing socket listeners');
      socket.off('member_joined', onMemberJoined);
      socket.off('sync_members', onSyncMembers);
      socket.off('league_status_changed', onLeagueStatusChanged);
      clearInterval(pollInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leagueId, user, listenerCount]);

  const loadLeague = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}`);
      console.log('📋 League loaded:', response.data);
      console.log('   Status:', response.data.status);
      console.log('   Active Auction:', response.data.activeAuctionId);
      setLeague(response.data);
      
      // CRITICAL FIX: Check for active auction after loading league
      // This ensures users who just joined see the "Join Auction Room" button
      try {
        const auctionsResponse = await axios.get(`${API}/auctions?leagueId=${leagueId}`);
        const activeAuction = auctionsResponse.data.find(a => a.status === 'active');
        if (activeAuction) {
          console.log('✅ Active auction detected:', activeAuction.id);
          // Update league status to reflect active auction
          setLeague(prev => ({ ...prev, status: 'active', activeAuctionId: activeAuction.id }));
        }
      } catch (auctionError) {
        console.error("Error checking for active auction:", auctionError);
      }
      
      // Load sport information based on league's sportKey
      if (response.data.sportKey) {
        try {
          const sportResponse = await axios.get(`${API}/sports/${response.data.sportKey}`);
          setSport(sportResponse.data);
          setUiHints(sportResponse.data.uiHints);
        } catch (e) {
          console.error("Error loading sport info:", e);
          // Keep default uiHints for clubs
        }
      }
    } catch (e) {
      console.error("Error loading league:", e);
      toast.error("League not found");
      navigate("/");
    } finally {
      setLoading(false);
    }
  };

  const loadParticipants = async () => {
    try {
      // Use /members endpoint for ordered member list (source of truth)
      const response = await axios.get(`${API}/leagues/${leagueId}/members`);
      // Convert to participant format
      const members = response.data.map(m => ({
        userId: m.userId,
        userName: m.displayName,
        joinedAt: m.joinedAt
      }));
      setParticipants(members);
    } catch (e) {
      console.error("Error loading participants:", e);
    }
  };

  const loadStandings = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/standings`);
      // The endpoint returns { leagueId, sportKey, table: [...] }
      // Extract the table array for backwards compatibility with existing code
      setStandings(response.data.table || []);
    } catch (e) {
      console.error("Error loading standings:", e);
      setStandings([]); // Set empty array on error
    }
  };

  const loadFixtures = async () => {
    setLoadingFixtures(true);
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
      setFixtures(response.data.fixtures || []);
    } catch (e) {
      console.error("Error loading fixtures:", e);
      setFixtures([]); // Set empty array on error to prevent undefined
    } finally {
      setLoadingFixtures(false);
    }
  };

  const handleUpdateScores = async () => {
    setLoadingFixtures(true);
    try {
      const response = await axios.post(`${API}/fixtures/update-scores`);
      
      if (response.data.updated > 0) {
        toast.success(`Updated ${response.data.updated} match results! Refresh to see scores.`);
        // Reload fixtures to show updated scores
        await loadFixtures();
      } else {
        toast.info("No new match results available yet. Check again after matches complete.");
      }
      
      // Show API usage info
      if (response.data.api_requests_remaining !== undefined) {
        console.log(`API requests remaining this minute: ${response.data.api_requests_remaining}/10`);
      }
    } catch (e) {
      console.error("Error updating scores:", e);
      toast.error(e.response?.data?.detail || "Failed to update scores. Please try again.");
    } finally {
      setLoadingFixtures(false);
    }
  };

  const loadAssets = async () => {
    setLoadingAssets(true);
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/assets`);
      setAssets(response.data.assets || []);
    } catch (e) {
      console.error("Error loading assets:", e);
      setAssets([]);
    } finally {
      setLoadingAssets(false);
    }
  };

  const recomputeScores = async () => {
    setLoadingScores(true);
    try {
      await axios.post(`${API}/leagues/${leagueId}/score/recompute`);
      await loadStandings();
      toast.success("Scores recomputed successfully!");
    } catch (e) {
      console.error("Error recomputing scores:", e);
      toast.error(e.response?.data?.detail || "Error recomputing scores");
    } finally {
      setLoadingScores(false);
    }
  };

  // Prompt E: Team management functions
  const loadAvailableAssets = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/available-assets`);
      setAvailableAssets(response.data);
      
      // Set current selection
      if (league?.assetsSelected) {
        setSelectedAssetIds(league.assetsSelected);
      } else {
        setSelectedAssetIds(response.data.map(asset => asset.id)); // Default: all selected
      }
    } catch (e) {
      console.error("Error loading available assets:", e);
      toast.error("Error loading available teams");
    }
  };

  const handleAssetToggle = (assetId) => {
    setSelectedAssetIds(prev => {
      if (prev.includes(assetId)) {
        return prev.filter(id => id !== assetId);
      } else {
        return [...prev, assetId];
      }
    });
  };

  const saveAssetSelection = async () => {
    if (selectedAssetIds.length === 0) {
      toast.error("You must select at least one team for the auction");
      return;
    }

    setLoadingAssetSelection(true);
    try {
      await axios.put(`${API}/leagues/${leagueId}/assets`, selectedAssetIds);
      toast.success(`Team selection updated! ${selectedAssetIds.length} teams selected for auction.`);
      setEditingAssets(false);
      await loadLeague(); // Reload league data
      await loadAssets(); // Reload assets to show selected teams
    } catch (e) {
      console.error("Error saving asset selection:", e);
      toast.error(e.response?.data?.detail || "Error saving team selection");
    } finally {
      setLoadingAssetSelection(false);
    }
  };

  const handleImportFootballFixtures = async () => {
    if (!user) {
      toast.error("Please sign in first");
      return;
    }
    
    setImportingFixtures(true);
    try {
      const response = await axios.post(
        `${API}/leagues/${leagueId}/fixtures/import-from-api?commissionerId=${user.id}&days=7`
      );
      setFixturesImported(true);
      const totalFixtures = (response.data.fixturesImported || 0) + (response.data.fixturesUpdated || 0);
      toast.success(`✅ Imported ${totalFixtures} fixtures successfully (${response.data.fixturesImported || 0} new, ${response.data.fixturesUpdated || 0} updated)`);
    } catch (error) {
      console.error("Error importing fixtures:", error);
      const errorMsg = error.response?.data?.detail || "Failed to import fixtures. This might be due to API rate limits or no upcoming matches for your selected teams. Try again in a few minutes.";
      toast.error(errorMsg);
    } finally {
      setImportingFixtures(false);
    }
  };

  const handleImportCricketFixture = async () => {
    if (!user) {
      toast.error("Please sign in first");
      return;
    }
    
    setImportingFixtures(true);
    try {
      await axios.post(
        `${API}/leagues/${leagueId}/fixtures/import-next-cricket-fixture?commissionerId=${user.id}`
      );
      setFixturesImported(true);
      toast.success(`✅ Imported next cricket fixture successfully`);
    } catch (error) {
      console.error("Error importing fixture:", error);
      const errorMsg = error.response?.data?.detail || "Failed to import fixture";
      toast.error(`❌ ${errorMsg}`);
    } finally {
      setImportingFixtures(false);
    }
  };

  const startAuction = async () => {
    if (!user) {
      toast.error("Please sign in first");
      return;
    }

    if (league.commissionerId !== user.id) {
      toast.error("Only the league commissioner can start the auction");
      return;
    }

    setStartingAuction(true);
    try {
      const response = await axios.post(`${API}/leagues/${leagueId}/auction/start`);
      toast.success("Auction started!");
      navigate(`/auction/${response.data.auctionId}`);
    } catch (e) {
      console.error("Error starting auction:", e);
      const errorMsg = e.response?.data?.detail || "Unable to start auction. Make sure you have at least 2 participants and teams selected.";
      toast.error(errorMsg);
    } finally {
      setStartingAuction(false);
    }
  };

  const goToAuction = async () => {
    try {
      // Use activeAuctionId from league state if available (from real-time event)
      if (league.activeAuctionId) {
        navigate(`/auction/${league.activeAuctionId}`);
        return;
      }
      
      // Fallback to API call if activeAuctionId not in state
      const response = await axios.get(`${API}/leagues/${leagueId}/auction`);
      navigate(`/auction/${response.data.auctionId}`);
    } catch (e) {
      console.error("Error getting auction:", e);
      toast.error("No auction found for this league");
    }
  };

  const deleteLeague = async () => {
    if (!user) {
      toast.error("Please sign in first");
      return;
    }

    if (league.commissionerId !== user.id) {
      toast.error("Only the league commissioner can delete this league");
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to delete "${league.name}"? This will remove all participants, auction data, and bids. This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await axios.delete(`${API}/leagues/${leagueId}?user_id=${user.id}`);
      toast.success("League deleted successfully");
      navigate("/");
    } catch (e) {
      console.error("Error deleting league:", e);
      toast.error(e.response?.data?.detail || "Error deleting league");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading...</div>
      </div>
    );
  }

  if (!league) {
    return null;
  }

  const isCommissioner = user && league.commissionerId === user.id;
  const canStartAuction = participants.length >= league.minManagers;

  // Helper functions for cricket scoring configuration
  const getDefaultCricketScoring = () => ({
    type: "perPlayerMatch",
    rules: {
      run: 1,
      wicket: 25,
      catch: 10,
      stumping: 15,
      runOut: 10
    },
    milestones: {
      halfCentury: {
        enabled: true,
        threshold: 50,
        points: 10
      },
      century: {
        enabled: true,
        threshold: 100,
        points: 25
      },
      fiveWicketHaul: {
        enabled: true,
        threshold: 5,
        points: 25
      }
    }
  });

  const getCurrentScoringDisplay = () => {
    const currentScoring = league.scoringOverrides || (sport ? sport.scoringSchema : getDefaultCricketScoring());
    const rules = currentScoring.rules || {};
    const milestones = currentScoring.milestones || {};
    
    return [
      { label: "Run", value: `${rules.run || 0} pts` },
      { label: "Wicket", value: `${rules.wicket || 0} pts` },
      { label: "Catch", value: `${rules.catch || 0} pts` },
      { label: "Stumping", value: `${rules.stumping || 0} pts` },
      { label: "Run Out", value: `${rules.runOut || 0} pts` },
      { label: "Half Century", value: milestones.halfCentury?.enabled ? `+${milestones.halfCentury.points} pts` : "Disabled" },
      { label: "Century", value: milestones.century?.enabled ? `+${milestones.century.points} pts` : "Disabled" },
      { label: "Five Wicket Haul", value: milestones.fiveWicketHaul?.enabled ? `+${milestones.fiveWicketHaul.points} pts` : "Disabled" }
    ];
  };

  const updateScoringRule = (rule, value) => {
    setScoringOverrides(prev => ({
      ...prev,
      rules: {
        ...prev?.rules,
        [rule]: value
      }
    }));
  };

  const updateMilestone = (milestone, field, value) => {
    setScoringOverrides(prev => ({
      ...prev,
      milestones: {
        ...prev?.milestones,
        [milestone]: {
          ...prev?.milestones?.[milestone],
          threshold: milestone === "halfCentury" ? 50 : milestone === "century" ? 100 : 5,
          [field]: value
        }
      }
    }));
  };

  const handleSaveScoring = async () => {
    if (!isCommissioner) {
      toast.error("Only commissioners can modify scoring rules");
      return;
    }

    setSavingScoring(true);
    try {
      const response = await axios.put(`${API}/leagues/${leagueId}/scoring-overrides`, {
        scoringOverrides: scoringOverrides
      });

      if (response.data) {
        setLeague(prev => ({ ...prev, scoringOverrides: scoringOverrides }));
        setEditingScoring(false);
        toast.success("Scoring rules updated successfully!");
      }
    } catch (error) {
      console.error("Error saving scoring overrides:", error);
      toast.error("Failed to save scoring rules. Please try again.");
    } finally {
      setSavingScoring(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 py-8">
      <div className="container-narrow mx-auto px-4">
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
          {/* Breadcrumb Navigation */}
          <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
            <button onClick={() => navigate("/")} className="hover:text-blue-600">Home</button>
            <span>›</span>
            <button onClick={() => navigate("/app/my-competitions")} className="hover:text-blue-600">My Competitions</button>
            <span>›</span>
            <span className="text-gray-900 font-semibold">{league.name || "Competition"}</span>
          </div>

          {/* Active Auction Alert */}
          {league.status === "active" && league.activeAuctionId && (
            <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4 mb-6 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🔴</span>
                  <div>
                    <h3 className="font-bold text-red-800">Auction is Live!</h3>
                    <p className="text-sm text-red-700">Don&apos;t miss out - join the bidding now</p>
                  </div>
                </div>
                <button
                  onClick={goToAuction}
                  className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold shadow-lg"
                >
                  Join Auction Now →
                </button>
              </div>
            </div>
          )}

          <div className="flex justify-between items-start mb-6">
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Competition Detail Page</div>
              <h1 className="h1 text-3xl font-bold text-gray-900 mb-2">{league.name}</h1>
              <div className="stack-md">
                <div className="row-gap-md flex items-center">
                  <span
                    className={`chip px-3 py-1 rounded-full text-sm font-semibold ${
                      league.status === "active"
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {league.status}
                  </span>
                  <span className="subtle text-sm text-gray-600">
                    {participants.length}/{league.maxManagers} managers
                  </span>
                </div>
                <div className="subtle text-sm text-gray-600">
                  Invite Token: <code className="chip bg-gray-100 px-2 py-1 rounded font-mono">{league.inviteToken}</code>
                </div>
              </div>
            </div>

            {/* Optional: Import Fixtures Before Auction */}
            {league.status === "pending" && isCommissioner && league.assetsSelected && league.assetsSelected.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 text-2xl">
                    📅
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 text-sm mb-1">
                      Import Fixtures (Optional)
                    </h3>
                    <p className="text-xs text-gray-600 mb-2">
                      <strong>After selecting your teams,</strong> import fixtures so managers see opponents during bidding.
                    </p>
                    
                    {importingFixtures ? (
                      <div className="flex items-center gap-2 text-xs text-blue-700">
                        <div className="animate-spin rounded-full h-3 w-3 border-2 border-blue-700 border-t-transparent"></div>
                        <span>Importing...</span>
                      </div>
                    ) : fixturesImported ? (
                      <div className="text-xs text-green-700 font-medium">
                        ✅ Fixtures imported
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        {league.sportKey === 'football' && (
                          <button 
                            onClick={handleImportFootballFixtures}
                            className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                          >
                            Import Fixtures
                          </button>
                        )}
                        
                        {league.sportKey === 'cricket' && (
                          <button 
                            onClick={handleImportCricketFixture}
                            className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700"
                          >
                            Import Next Match
                          </button>
                        )}
                        <span className="text-xs text-gray-500">or skip for now</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              {league.status === "pending" && isCommissioner && (
                <div>
                  <button
                    onClick={startAuction}
                    disabled={!canStartAuction || startingAuction}
                    className={`btn btn-primary px-6 py-3 rounded-lg font-semibold flex items-center gap-2 ${
                      canStartAuction && !startingAuction
                        ? "bg-green-600 text-white hover:bg-green-700"
                        : "bg-gray-300 text-gray-500 cursor-not-allowed"
                    }`}
                    data-testid="start-auction-button"
                  >
                    {startingAuction && (
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    )}
                    {startingAuction ? "Starting..." : "Begin Strategic Competition"}
                  </button>
                  {!canStartAuction && (
                    <p className="text-sm text-red-600 mt-2">
                      Need {league.minManagers - participants.length} more strategic competitors to begin
                    </p>
                  )}
                </div>
              )}
              
              {league.status === "active" && (
                <button
                  onClick={goToAuction}
                  className="btn btn-primary px-6 py-3 rounded-lg font-semibold bg-blue-600 text-white hover:bg-blue-700"
                  data-testid="go-to-auction-button"
                >
                  Enter Auction Room
                </button>
              )}
              
              {isCommissioner && (league.status === "pending" || league.status === "completed") && (
                <button
                  onClick={deleteLeague}
                  className="btn btn-danger px-6 py-3 rounded-lg font-semibold bg-red-600 text-white hover:bg-red-700"
                  data-testid="delete-league-button"
                >
                  Delete League
                </button>
              )}
            </div>
          </div>

          {/* Participants */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">League Participants</h3>
            {participants.length === 0 ? (
              <p className="text-gray-600">No participants yet. Share the invite token to get started!</p>
            ) : (
              <div className="space-y-2">
                {participants.map((p) => (
                  <div
                    key={p.id}
                    className="flex justify-between items-center bg-white p-3 rounded"
                  >
                    <div>
                      <span className="font-semibold text-gray-900">{p.userName}</span>
                      {p.userId === league.commissionerId && (
                        <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                          Commissioner
                        </span>
                      )}
                    </div>
                    <span className="text-sm text-gray-600">{p.userEmail}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Available Assets/Players */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Available {uiHints.assetPlural} in Competition
            </h3>
            {loadingAssets ? (
              <p className="text-gray-600">Loading {uiHints.assetPlural.toLowerCase()}...</p>
            ) : assets.length === 0 ? (
              <p className="text-gray-600">No {uiHints.assetPlural.toLowerCase()} available.</p>
            ) : (
              <>
                <p className="text-gray-600 mb-4">
                  {assets.length} {uiHints.assetPlural.toLowerCase()} available for auction in this competition.
                </p>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                  {assets.map((asset) => (
                    <div key={asset.id} className="bg-white border rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900">{asset.name}</h4>
                      {asset.country && (
                        <p className="text-sm text-gray-600">{asset.country}</p>
                      )}
                      {asset.meta && asset.meta.franchise && (
                        <p className="text-sm text-blue-600">{asset.meta.franchise}</p>
                      )}
                      {asset.meta && asset.meta.role && (
                        <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mt-2">
                          {asset.meta.role}
                        </span>
                      )}
                      {asset.uefaId && (
                        <p className="text-xs text-gray-500 mt-1">UEFA ID: {asset.uefaId}</p>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* League Details */}
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="bg-gray-50 p-6 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">League Settings</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Budget per Manager:</span>
                  <span className="chip font-semibold">{formatCurrency(league.budget)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Min Managers:</span>
                  <span className="font-semibold">{league.minManagers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Managers:</span>
                  <span className="font-semibold">{league.maxManagers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">{uiHints.assetLabel} Slots:</span>
                  <span className="font-semibold">{league.clubSlots}</span>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 p-6 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Auction Info</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Bid Timer:</span>
                  <span className="font-semibold">{league.timerSeconds || 30} seconds</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Anti-Snipe:</span>
                  <span className="font-semibold">{league.antiSnipeSeconds || 5} seconds</span>
                </div>
                <div className="text-sm text-gray-500 mt-4">
                  * Timer extends by {league.antiSnipeSeconds || 5} seconds if bid placed in last {league.antiSnipeSeconds || 5} seconds
                </div>
              </div>
            </div>
          </div>

          {/* Prompt E: Team Management for Commissioner */}
          {league && user && league.commissionerId === user.id && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 mb-8">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Manage {uiHints.assetPlural}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Choose which {uiHints.assetPlural.toLowerCase()} will be available in your auction
                  </p>
                </div>
                {!editingAssets ? (
                  <button
                    onClick={() => {
                      setEditingAssets(true);
                      loadAvailableAssets();
                    }}
                    className="btn-secondary px-4 py-2 text-sm"
                    data-testid="manage-teams-button"
                  >
                    Select {uiHints.assetPlural}
                  </button>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={saveAssetSelection}
                      disabled={loadingAssetSelection}
                      className="btn-primary px-4 py-2 text-sm"
                      data-testid="save-teams-button"
                    >
                      {loadingAssetSelection ? "Saving..." : "Save Selection"}
                    </button>
                    <button
                      onClick={() => setEditingAssets(false)}
                      className="btn-secondary px-4 py-2 text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>

              {editingAssets ? (
                <div>
                  <div className="mb-4 p-3 bg-blue-50 rounded">
                    <div className="text-sm font-medium text-blue-800">
                      Selected: {selectedAssetIds.length} / {availableAssets.length}
                    </div>
                    <div className="text-xs text-blue-600 mt-1">
                      ⚠️ Changes are locked after auction starts
                    </div>
                  </div>
                  
                  {/* Competition Filter for Football */}
                  {league.sportKey === "football" && (
                    <div className="mb-3">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Competition</label>
                      <select
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
                        onChange={async (e) => {
                          const filter = e.target.value;
                          try {
                            let response;
                            if (filter === "all") {
                              response = await axios.get(`${API}/clubs?sportKey=football`);
                            } else {
                              response = await axios.get(`${API}/clubs?sportKey=football&competition=${filter}`);
                            }
                            setAvailableAssets(response.data);
                            // Auto-select all teams in filtered view
                            if (filter !== "all") {
                              setSelectedAssetIds(response.data.map(t => t.id));
                            }
                          } catch (error) {
                            console.error("Error filtering clubs:", error);
                          }
                        }}
                      >
                        <option value="all">All Teams ({availableAssets.length})</option>
                        <option value="EPL">Premier League Only (20)</option>
                        <option value="UCL">Champions League Only (36)</option>
                        <option value="AFCON">AFCON Only (24)</option>
                      </select>
                    </div>
                  )}

                  {/* Competition Filter for Cricket */}
                  {league.sportKey === "cricket" && (
                    <div className="mb-3">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Series</label>
                      <select
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 mb-2"
                        onChange={async (e) => {
                          const filter = e.target.value;
                          try {
                            let response;
                            if (filter === "all") {
                              response = await axios.get(`${API}/clubs?sportKey=cricket`);
                            } else {
                              response = await axios.get(`${API}/clubs?sportKey=cricket&competition=${filter}`);
                            }
                            setAvailableAssets(response.data);
                            // Auto-select all players in filtered view
                            if (filter !== "all") {
                              setSelectedAssetIds(response.data.map(p => p.id));
                            }
                          } catch (error) {
                            console.error("Error filtering players:", error);
                          }
                        }}
                      >
                        <option value="all">All Players (53)</option>
                        <option value="ASHES">🏴󠁧󠁢󠁥󠁮󠁧󠁿🇦🇺 The Ashes 2025/26 (30)</option>
                        <option value="NZ_ENG">🇳🇿🏴 NZ vs England ODI (23)</option>
                      </select>
                    </div>
                  )}
                  
                  {/* Quick Action Buttons */}
                  <div className="mb-3 flex gap-2">
                    <button
                      type="button"
                      onClick={() => setSelectedAssetIds(availableAssets.map(a => a.id))}
                      className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold"
                    >
                      Select All
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedAssetIds([])}
                      className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-semibold"
                    >
                      Clear All
                    </button>
                  </div>
                  
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-96 overflow-y-auto">
                    {availableAssets.map((asset) => (
                      <label
                        key={asset.id}
                        className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedAssetIds.includes(asset.id)
                            ? 'bg-purple-100 border-purple-300'
                            : 'bg-white border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedAssetIds.includes(asset.id)}
                          onChange={() => handleAssetToggle(asset.id)}
                          className="mr-3"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{asset.name}</div>
                          {/* Football: Show country */}
                          {asset.country && (
                            <div className="text-sm text-gray-600">{asset.country}</div>
                          )}
                          {/* Cricket: Show nationality and role */}
                          {league.sportKey === "cricket" && asset.meta?.nationality && (
                            <div className="text-xs text-gray-600 mt-1">
                              <span className="bg-gray-200 px-2 py-0.5 rounded mr-1">
                                {asset.meta.nationality}
                              </span>
                              {asset.meta.role && (
                                <span className="text-gray-500">
                                  {asset.meta.role}
                                </span>
                              )}
                            </div>
                          )}
                          {asset.meta && asset.meta.franchise && (
                            <div className="text-sm text-purple-600">{asset.meta.franchise}</div>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              ) : (
                <div>
                  {league.assetsSelected ? (
                    <div className="text-sm text-gray-600">
                      <span className="font-medium text-gray-900">
                        {league.assetsSelected.length}
                      </span> {uiHints.assetPlural.toLowerCase()} selected for auction
                    </div>
                  ) : (
                    <div className="text-sm text-gray-600">
                      All available {uiHints.assetPlural.toLowerCase()} will be included in the auction
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Cricket Scoring Configuration */}
          {league && league.sportKey === "cricket" && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Advanced: Scoring (Cricket)</h3>
                {!editingScoring ? (
                  <button
                    onClick={() => {
                      setEditingScoring(true);
                      // Initialize form with current overrides or sport defaults
                      const currentOverrides = league.scoringOverrides || (sport ? sport.scoringSchema : null);
                      setScoringOverrides(currentOverrides ? JSON.parse(JSON.stringify(currentOverrides)) : getDefaultCricketScoring());
                    }}
                    className="btn-secondary px-4 py-2 text-sm"
                    data-testid="edit-scoring-button"
                  >
                    Edit Scoring Rules
                  </button>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleSaveScoring}
                      disabled={savingScoring}
                      className="btn-primary px-4 py-2 text-sm"
                      data-testid="save-scoring-button"
                    >
                      {savingScoring ? "Saving..." : "Save Changes"}
                    </button>
                    <button
                      onClick={() => {
                        setEditingScoring(false);
                        setScoringOverrides(null);
                      }}
                      className="btn-secondary px-4 py-2 text-sm"
                      data-testid="cancel-scoring-button"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>

              {!editingScoring ? (
                <div>
                  <p className="text-gray-600 text-sm mb-4">
                    {league.scoringOverrides ? 
                      "Using custom scoring rules for this league." : 
                      "Using default cricket scoring rules."}
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    {getCurrentScoringDisplay().map((item, index) => (
                      <div key={index} className="flex justify-between">
                        <span className="text-gray-600">{item.label}:</span>
                        <span className="font-semibold">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Base Points</h4>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Run</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.run || 0}
                          onChange={(e) => updateScoringRule("run", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-run-input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Wicket</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.wicket || 0}
                          onChange={(e) => updateScoringRule("wicket", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-wicket-input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Catch</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.catch || 0}
                          onChange={(e) => updateScoringRule("catch", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-catch-input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Stumping</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.stumping || 0}
                          onChange={(e) => updateScoringRule("stumping", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-stumping-input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Run Out</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.runOut || 0}
                          onChange={(e) => updateScoringRule("runOut", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-runout-input"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Milestone Bonuses</h4>
                    <div className="space-y-4">
                      {["halfCentury", "century", "fiveWicketHaul"].map((milestone) => {
                        const milestoneData = scoringOverrides?.milestones?.[milestone];
                        const label = milestone === "halfCentury" ? "Half Century (50+ runs)" : 
                                    milestone === "century" ? "Century (100+ runs)" : 
                                    "Five Wicket Haul (5+ wickets)";
                        
                        return (
                          <div key={milestone} className="flex items-center space-x-4">
                            <label className="flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={milestoneData?.enabled || false}
                                onChange={(e) => updateMilestone(milestone, "enabled", e.target.checked)}
                                className="mr-2"
                                data-testid={`milestone-${milestone}-enabled`}
                              />
                              <span className="text-sm text-gray-700">{label}</span>
                            </label>
                            {milestoneData?.enabled && (
                              <div className="flex items-center space-x-2">
                                <span className="text-sm text-gray-600">Points:</span>
                                <input
                                  type="number"
                                  min="0"
                                  step="1"
                                  value={milestoneData?.points || 0}
                                  onChange={(e) => updateMilestone(milestone, "points", parseInt(e.target.value) || 0)}
                                  className="w-20 px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  data-testid={`milestone-${milestone}-points`}
                                />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Note:</strong> Changes will apply to future score ingests. Leave fields blank to use default cricket scoring rules.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Instructions */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">How It Works</h3>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                The commissioner starts the auction and selects {uiHints.assetPlural.toLowerCase()} to bid on
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                Each {uiHints.assetLabel.toLowerCase()} is auctioned for {league.timerSeconds} seconds
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                If a bid is placed in the last {league.antiSnipeSeconds} seconds, the timer extends by {league.antiSnipeSeconds} seconds
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                The highest bidder wins the {uiHints.assetLabel.toLowerCase()} when the timer expires
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                Each manager can bid up to their budget across multiple {uiHints.assetPlural.toLowerCase()}
              </li>
            </ul>
          </div>

          {/* Fixtures Section */}
          {fixtures.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6 mt-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Match Fixtures</h3>
                {isCommissioner && (
                  <button
                    onClick={handleUpdateScores}
                    disabled={loadingFixtures}
                    className={`px-4 py-2 rounded-lg font-semibold text-sm ${
                      loadingFixtures
                        ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                        : "bg-green-600 text-white hover:bg-green-700"
                    }`}
                  >
                    {loadingFixtures ? "Updating..." : "Update Match Scores"}
                  </button>
                )}
              </div>
              
              {loadingFixtures ? (
                <p className="text-gray-500 text-center py-4">Loading fixtures...</p>
              ) : (
                <div className="space-y-4">
                  {/* Upcoming Fixtures */}
                  {fixtures.filter(f => f.status === 'scheduled').length > 0 && (
                    <div>
                      <h4 className="text-md font-semibold text-gray-700 mb-2">Upcoming Matches</h4>
                      <div className="space-y-2">
                        {fixtures.filter(f => f.status === 'scheduled').map((fixture) => (
                          <div key={fixture.id} className="flex items-center justify-between border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex items-center space-x-4 flex-1">
                              <div className={`text-right flex-1 ${fixture.homeTeamInLeague ? 'font-semibold text-blue-600' : 'text-gray-700'}`}>
                                {fixture.homeTeam}
                              </div>
                              <div className="text-gray-400 font-semibold">vs</div>
                              <div className={`text-left flex-1 ${fixture.awayTeamInLeague ? 'font-semibold text-blue-600' : 'text-gray-700'}`}>
                                {fixture.awayTeam}
                              </div>
                            </div>
                            <div className="text-sm text-gray-500 ml-4">
                              {new Date(fixture.matchDate || fixture.startsAt).toLocaleDateString('en-GB', { 
                                weekday: 'short', 
                                day: 'numeric', 
                                month: 'short',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Completed Fixtures */}
                  {fixtures.filter(f => f.status !== 'scheduled').length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-md font-semibold text-gray-700 mb-2">Completed Matches</h4>
                      <div className="space-y-2">
                        {fixtures.filter(f => f.status !== 'scheduled').map((fixture) => (
                          <div key={fixture.id} className="flex items-center justify-between border border-gray-200 rounded-lg p-4 bg-gray-50">
                            <div className="flex items-center space-x-4 flex-1">
                              <div className={`text-right flex-1 ${fixture.homeTeamInLeague ? 'font-semibold text-blue-600' : 'text-gray-700'}`}>
                                {fixture.homeTeam}
                                {fixture.goalsHome !== null && fixture.goalsHome !== undefined && (
                                  <span className={`ml-2 text-lg ${fixture.winner === fixture.homeTeam ? 'text-green-600 font-bold' : 'text-gray-600'}`}>
                                    {fixture.goalsHome}
                                  </span>
                                )}
                              </div>
                              <div className="text-gray-400 font-semibold">-</div>
                              <div className={`text-left flex-1 ${fixture.awayTeamInLeague ? 'font-semibold text-blue-600' : 'text-gray-700'}`}>
                                {fixture.goalsAway !== null && fixture.goalsAway !== undefined && (
                                  <span className={`mr-2 text-lg ${fixture.winner === fixture.awayTeam ? 'text-green-600 font-bold' : 'text-gray-600'}`}>
                                    {fixture.goalsAway}
                                  </span>
                                )}
                                {fixture.awayTeam}
                              </div>
                            </div>
                            <div className="text-sm text-gray-500 ml-4">
                              <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-semibold">
                                {fixture.status === 'ft' || fixture.status === 'finished' ? 'FT' : fixture.status.toUpperCase()}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {isCommissioner && (
                    <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm text-blue-800">
                        <strong>Commissioner:</strong> After matches complete, click <strong>&quot;Update Match Scores&quot;</strong> above to fetch latest results. 
                        Then click <strong>&quot;Recompute Scores&quot;</strong> in the Standings section to update league rankings.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Standings */}
          {league.status === "active" && (
            <div className="bg-white border border-gray-200 rounded-lg p-6 mt-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">League Standings</h3>
                {isCommissioner && (
                  <button
                    onClick={recomputeScores}
                    disabled={loadingScores}
                    className={`btn btn-secondary px-4 py-2 rounded-lg font-semibold text-sm ${
                      loadingScores
                        ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                        : "bg-blue-600 text-white hover:bg-blue-700"
                    }`}
                    data-testid="recompute-scores-button"
                  >
                    {loadingScores ? "Computing..." : "🔄 Recompute Scores"}
                  </button>
                )}
              </div>

              {standings.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No scores yet. {uiHints.assetPlural} need to be won in the auction first, then scores can be computed based on competition results.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Rank
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          {uiHints.assetLabel}
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          W
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          D
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          L
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          GF
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          GA
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          GD
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider font-bold">
                          Points
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {standings.map((club, index) => {
                        const goalDiff = club.goalsScored - club.goalsConceded;
                        return (
                          <tr key={club.id} className={index < 3 ? "bg-green-50" : ""}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {index + 1}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                              {club.clubName}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.wins}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.draws}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.losses}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.goalsScored}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.goalsConceded}
                            </td>
                            <td className={`px-6 py-4 whitespace-nowrap text-sm text-center font-semibold ${
                              goalDiff > 0 ? "text-green-600" : goalDiff < 0 ? "text-red-600" : "text-gray-600"
                            }`}>
                              {goalDiff > 0 ? "+" : ""}{goalDiff}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center font-bold text-blue-600">
                              {club.totalPoints}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  <div className="mt-4 text-xs text-gray-500 space-y-1">
                    <p>📊 <strong>Scoring:</strong> Win = 3 pts | Draw = 1 pt | Goal Scored = 1 pt</p>
                    <p>🏆 <strong>Legend:</strong> W=Wins | D=Draws | L=Losses | GF=Goals For | GA=Goals Against | GD=Goal Difference</p>
                    <p className="text-green-600">Green rows = Top 3 positions</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {isCommissioner && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-900 font-semibold">
                🎯 You are the commissioner of this league
              </p>
              <p className="text-blue-700 text-sm mt-1">
                {league.status === "pending" 
                  ? "You can start the auction when ready"
                  : league.status === "active"
                  ? "Auction is currently running. Click 'Go to Auction' to participate."
                  : "You can recompute scores to update standings based on latest Champions League results"}
              </p>
            </div>
          )}
          
          {!isCommissioner && league.status === "active" && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-900 font-semibold">
                🎮 Auction is Live!
              </p>
              <p className="text-green-700 text-sm mt-1">
                Click &quot;Go to Auction&quot; to join the bidding and compete for {uiHints.assetPlural.toLowerCase()}.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
