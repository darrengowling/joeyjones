import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { formatCurrency } from "../utils/currency";
import { useSocketRoom } from "../hooks/useSocketRoom";
import BottomNav from "../components/BottomNav";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * LeagueDetailStitched - Complete visual redesign with Stitch design system
 * 
 * IMPORTANT: This is a VISUAL REDESIGN ONLY.
 * All state, logic, API calls, and functionality are preserved exactly from LeagueDetail.js
 * Only the JSX structure and CSS classes have been changed to match the Stitch design.
 */
export default function LeagueDetailStitched() {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  
  // === ALL STATE VARIABLES (preserved exactly from original) ===
  const [league, setLeague] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [standings, setStandings] = useState([]);
  const [assets, setAssets] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingScores, setLoadingScores] = useState(false);
  const [loadingAssets, setLoadingAssets] = useState(false);
  const [sport, setSport] = useState(null);
  const [uiHints, setUiHints] = useState({ assetLabel: "Club", assetPlural: "Clubs" });
  const [scoringOverrides, setScoringOverrides] = useState(null);
  const [editingScoring, setEditingScoring] = useState(false);
  const [savingScoring, setSavingScoring] = useState(false);
  // Team management state
  const [availableAssets, setAvailableAssets] = useState([]);
  const [selectedAssetIds, setSelectedAssetIds] = useState([]);
  const [editingAssets, setEditingAssets] = useState(false);
  const [loadingAssetSelection, setLoadingAssetSelection] = useState(false);
  const [importingFixtures, setImportingFixtures] = useState(false);
  const [fixturesImported, setFixturesImported] = useState(false);
  const [startingAuction, setStartingAuction] = useState(false);
  // Filter state for Manage Clubs modal
  const [competitionFilter, setCompetitionFilter] = useState("all");
  // Cricket filter state
  const [cricketTeamFilter, setCricketTeamFilter] = useState("all");
  const [cricketFranchises, setCricketFranchises] = useState([]);
  const [totalCricketPlayers, setTotalCricketPlayers] = useState(0);
  // Fixtures state
  const [fixtures, setFixtures] = useState([]);
  const [loadingFixtures, setLoadingFixtures] = useState(false);
  // Tab state for the redesigned UI
  const [activeTab, setActiveTab] = useState('overview');

  // Use shared socket room hook (preserved exactly)
  const { socket, connected, ready, listenerCount } = useSocketRoom('league', leagueId, { user });

  // === ALL useEffect HOOKS (preserved exactly from original) ===
  
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

  // Socket event handlers - single useEffect with proper cleanup (preserved exactly)
  useEffect(() => {
    if (!user) return;

    console.log(`[LeagueDetail] Setting up socket listeners (Count: ${listenerCount})`);
    
    // Join league room on connect
    socket.emit('join_league', { leagueId, userId: user.id }, (ack) => {
      if (ack && ack.ok) {
        console.log(`Joined league room: ${ack.room}, size: ${ack.roomSize}`);
      }
    });

    // Handle member updates (upsert pattern)
    const onMemberJoined = (data) => {
      console.log('Member joined event received:', data);
      setParticipants(prev => {
        const existingIndex = prev.findIndex(p => p.userId === data.userId);
        
        const newMember = {
          userId: data.userId,
          userName: data.displayName,
          joinedAt: data.joinedAt
        };
        
        if (existingIndex >= 0) {
          console.log('Updating existing member:', data.userId);
          const updated = [...prev];
          updated[existingIndex] = newMember;
          return updated;
        } else {
          console.log('Adding new member to list:', newMember);
          return [...prev, newMember];
        }
      });
    };
    
    // Handle sync_members for reconciliation (source of truth)
    const onSyncMembers = (data) => {
      console.log('Sync members received:', data);
      if (data.members && Array.isArray(data.members)) {
        const updatedParticipants = data.members.map(member => ({
          userId: member.userId,
          userName: member.displayName,
          joinedAt: member.joinedAt
        }));
        console.log(`Replacing participants with ${updatedParticipants.length} members from sync_members`);
        setParticipants(updatedParticipants);
      }
    };
    
    // Handle league status changes for instant auction start/complete notifications
    const onLeagueStatusChanged = (data) => {
      console.log('League status changed event received:', data);
      if (data.leagueId === leagueId) {
        if (data.status === 'auction_created' || data.status === 'auction_started' || data.status === 'auction_active') {
          console.log('Auction created/started/active - updating league data');
          setLeague(prev => ({
            ...prev,
            status: 'active',
            activeAuctionId: data.auctionId
          }));
        } else if (data.status === 'auction_complete') {
          console.log('Auction completed - updating league data');
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
    
    // Setup aggressive 3s polling for real-time updates
    const pollInterval = setInterval(() => {
      console.log('Polling league status...');
      loadLeague();
      loadParticipants();
    }, 3000);
    
    // Cleanup function
    return () => {
      console.log('[LeagueDetail] Removing socket listeners');
      socket.off('member_joined', onMemberJoined);
      socket.off('sync_members', onSyncMembers);
      socket.off('league_status_changed', onLeagueStatusChanged);
      clearInterval(pollInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leagueId, user, listenerCount]);

  // === ALL DATA LOADING FUNCTIONS (preserved exactly from original) ===

  const loadLeague = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}`);
      console.log('League loaded:', response.data);
      console.log('   Status:', response.data.status);
      console.log('   Active Auction:', response.data.activeAuctionId);
      setLeague(response.data);
      
      // Check for active auction using the correct endpoint
      // The league already contains activeAuctionId, so we just verify it exists if set
      if (response.data.activeAuctionId) {
        try {
          const auctionResponse = await axios.get(`${API}/auction/${response.data.activeAuctionId}`);
          if (auctionResponse.data.auction && auctionResponse.data.auction.status !== 'completed') {
            console.log('Active auction verified:', response.data.activeAuctionId);
            setLeague(prev => ({ ...prev, status: 'active' }));
          }
        } catch (auctionError) {
          // Auction doesn't exist anymore, clear activeAuctionId
          console.log('Auction no longer exists, clearing activeAuctionId');
          setLeague(prev => ({ ...prev, activeAuctionId: null }));
        }
      }
      
      // Load sport information based on league's sportKey
      if (response.data.sportKey) {
        try {
          const sportResponse = await axios.get(`${API}/sports/${response.data.sportKey}`);
          setSport(sportResponse.data);
          setUiHints(sportResponse.data.uiHints);
        } catch (e) {
          console.error("Error loading sport info:", e);
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
      const response = await axios.get(`${API}/leagues/${leagueId}/members`);
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
      setStandings(response.data.table || []);
    } catch (e) {
      console.error("Error loading standings:", e);
      setStandings([]);
    }
  };

  const loadFixtures = async () => {
    setLoadingFixtures(true);
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
      setFixtures(response.data.fixtures || []);
    } catch (e) {
      console.error("Error loading fixtures:", e);
      setFixtures([]);
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
        await loadFixtures();
      } else {
        toast.info("No new match results available yet. Check again after matches complete.");
      }
      
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

  // === TEAM MANAGEMENT FUNCTIONS (preserved exactly from original) ===

  const loadAvailableAssets = async () => {
    try {
      const sportKey = league?.sportKey || 'football';
      
      if (sportKey === 'cricket') {
        const selectedIds = league?.assetsSelected || [];
        
        if (selectedIds.length > 0) {
          const response = await axios.get(`${API}/leagues/${league.id}/assets`);
          const players = response.data.assets || [];
          
          setAvailableAssets(players);
          setTotalCricketPlayers(players.length);
          
          const franchises = [...new Set(players.map(p => p.meta?.franchise).filter(Boolean))].sort();
          setCricketFranchises(franchises);
          
          setSelectedAssetIds(selectedIds);
        } else {
          setAvailableAssets([]);
          setTotalCricketPlayers(0);
          setCricketFranchises([]);
          setSelectedAssetIds([]);
        }
        setCricketTeamFilter('all');
      } else {
        const response = await axios.get(`${API}/clubs?sportKey=${sportKey}`);
        setAvailableAssets(response.data);
        
        if (league?.assetsSelected && league.assetsSelected.length > 0) {
          setSelectedAssetIds(league.assetsSelected);
          
          if (league?.competitionCode && sportKey === 'football') {
            const comp = league.competitionCode.toUpperCase();
            if (comp === 'PL' || comp === 'EPL') {
              setCompetitionFilter('EPL');
            } else if (comp === 'CL' || comp === 'UCL') {
              setCompetitionFilter('UCL');
            } else if (comp === 'AFCON') {
              setCompetitionFilter('AFCON');
            } else {
              setCompetitionFilter('all');
            }
          }
        } else if (league?.competitionCode && sportKey === 'football') {
          const comp = league.competitionCode.toUpperCase();
          let competitionName = null;
          if (comp === 'PL' || comp === 'EPL') {
            competitionName = 'English Premier League';
            setCompetitionFilter('EPL');
          } else if (comp === 'CL' || comp === 'UCL') {
            competitionName = 'UEFA Champions League';
            setCompetitionFilter('UCL');
          } else if (comp === 'AFCON') {
            competitionName = 'Africa Cup of Nations';
            setCompetitionFilter('AFCON');
          }
          
          if (competitionName) {
            const filteredIds = response.data
              .filter(asset => asset.competitions?.includes(competitionName) || 
                             (comp === 'PL' && asset.competitionShort === 'EPL') ||
                             (comp === 'CL' && asset.competitionShort === 'UCL') ||
                             (comp === 'AFCON' && asset.competitionShort === 'AFCON'))
              .map(asset => asset.id);
            setSelectedAssetIds(filteredIds);
          } else {
            setSelectedAssetIds(response.data.map(asset => asset.id));
            setCompetitionFilter('all');
          }
        } else {
          setSelectedAssetIds(response.data.map(asset => asset.id));
          setCompetitionFilter('all');
        }
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
      await loadLeague();
      await loadAssets();
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
      toast.success(`Imported ${totalFixtures} fixtures successfully (${response.data.fixturesImported || 0} new, ${response.data.fixturesUpdated || 0} updated)`);
      await loadFixtures();
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
      toast.success(`Imported next cricket fixture successfully`);
      await loadFixtures();
    } catch (error) {
      console.error("Error importing fixture:", error);
      const errorMsg = error.response?.data?.detail || "Failed to import fixture";
      toast.error(`${errorMsg}`);
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
      if (league.activeAuctionId) {
        navigate(`/auction/${league.activeAuctionId}`);
        return;
      }
      
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

  // === CRICKET SCORING HELPER FUNCTIONS (preserved exactly from original) ===

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

  // === COMPUTED VALUES (preserved exactly from original) ===
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-base, #0F172A)' }}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4" style={{ borderColor: 'var(--color-primary, #06B6D4)', borderTopColor: 'transparent' }}></div>
          <p style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>Loading competition...</p>
        </div>
      </div>
    );
  }

  if (!league) {
    return null;
  }

  const isCommissioner = user && league.commissionerId === user.id;
  const canStartAuction = participants.length >= league.minManagers;

  // Filter assets for the manage modal
  const getFilteredAssets = () => {
    let filtered = availableAssets;
    
    if (league?.sportKey === 'football' && competitionFilter !== 'all') {
      if (competitionFilter === 'EPL') {
        filtered = filtered.filter(a => a.competitionShort === 'EPL' || a.competitions?.includes('English Premier League'));
      } else if (competitionFilter === 'UCL') {
        filtered = filtered.filter(a => a.competitionShort === 'UCL' || a.competitions?.includes('UEFA Champions League'));
      } else if (competitionFilter === 'AFCON') {
        filtered = filtered.filter(a => a.competitionShort === 'AFCON' || a.competitions?.includes('Africa Cup of Nations'));
      }
    }
    
    if (league?.sportKey === 'cricket' && cricketTeamFilter !== 'all') {
      filtered = filtered.filter(a => a.meta?.franchise === cricketTeamFilter);
    }
    
    return filtered;
  };

  // === STITCH-STYLED JSX (visual redesign) ===
  
  return (
    <div className="min-h-screen font-sans" style={{ background: 'var(--bg-base, #0F172A)', paddingBottom: '100px' }}>
      {/* Fixed Header */}
      <header 
        className="fixed top-0 left-0 right-0 z-40 px-4 py-4 flex items-center justify-between"
        style={{
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <button 
          onClick={() => navigate('/')}
          className="w-10 h-10 flex items-center justify-center rounded-full transition-all active:scale-95"
          style={{ background: 'rgba(255,255,255,0.05)' }}
          data-testid="back-button"
        >
          <span className="material-symbols-outlined" style={{ color: 'var(--text-primary, #fff)' }}>arrow_back</span>
        </button>
        <h1 className="text-sm font-black tracking-widest uppercase truncate max-w-[200px]" style={{ color: 'var(--text-primary, #fff)' }}>
          {league.name}
        </h1>
        <div className="w-10"></div>
      </header>

      <main className="pt-20 px-4">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs mb-4" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
          <button onClick={() => navigate("/")} className="hover:underline">Home</button>
          <span>›</span>
          <button onClick={() => navigate("/app/my-competitions")} className="hover:underline">My Competitions</button>
          <span>›</span>
          <span style={{ color: 'var(--text-primary, #fff)' }}>{league.name}</span>
        </div>

        {/* Active Auction Alert - CRITICAL: preserved exactly */}
        {league.status === "active" && league.activeAuctionId && (
          <button
            onClick={goToAuction}
            className="w-full mb-6 p-4 rounded-2xl flex items-center justify-between"
            style={{ 
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              animation: 'pulse 2s infinite',
            }}
            data-testid="join-auction-alert"
          >
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full animate-ping" style={{ background: 'var(--color-timer-red, #EF4444)' }}></div>
              <div className="text-left">
                <p className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>Auction is Live!</p>
                <p className="text-xs" style={{ color: '#FCA5A5' }}>Don&apos;t miss out - join the bidding now</p>
              </div>
            </div>
            <span className="material-symbols-outlined" style={{ color: 'var(--text-primary, #fff)' }}>arrow_forward</span>
          </button>
        )}

        {/* League Header Card */}
        <div 
          className="p-5 rounded-2xl mb-6"
          style={{ 
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <p className="text-[10px] font-bold uppercase tracking-widest mb-2" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
            Competition Detail Page
          </p>
          <h2 className="text-2xl font-bold mb-3" style={{ color: 'var(--text-primary, #fff)' }}>{league.name}</h2>
          
          <div className="flex items-center gap-3 mb-4">
            <span 
              className="px-3 py-1 rounded-full text-xs font-bold uppercase"
              style={{ 
                background: league.status === 'active' ? 'rgba(16, 185, 129, 0.2)' : league.status === 'completed' ? 'rgba(107, 114, 128, 0.2)' : 'rgba(6, 182, 212, 0.2)',
                color: league.status === 'active' ? '#10B981' : league.status === 'completed' ? '#9CA3AF' : '#06B6D4',
              }}
            >
              {league.status}
            </span>
            <span className="text-sm" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
              {participants.length}/{league.maxManagers} managers
            </span>
          </div>

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Budget</p>
              <p className="text-lg font-bold" style={{ color: 'var(--text-primary, #fff)' }}>{formatCurrency(league.budget)}</p>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>{uiHints.assetPlural} Each</p>
              <p className="text-lg font-bold" style={{ color: 'var(--text-primary, #fff)' }}>{league.clubSlots}</p>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Bid Timer</p>
              <p className="text-lg font-bold" style={{ color: 'var(--text-primary, #fff)' }}>{league.timerSeconds || 30}s</p>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Anti-Snipe</p>
              <p className="text-lg font-bold" style={{ color: 'var(--text-primary, #fff)' }}>{league.antiSnipeSeconds || 5}s</p>
            </div>
          </div>
        </div>

        {/* Invite Section */}
        <div 
          className="p-5 rounded-2xl mb-6"
          style={{ 
            background: 'rgba(6, 182, 212, 0.1)',
            border: '1px solid rgba(6, 182, 212, 0.2)',
          }}
        >
          <div className="flex items-center gap-2 mb-3">
            <span className="material-symbols-outlined" style={{ color: 'var(--color-primary, #06B6D4)' }}>group_add</span>
            <p className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>Invite Friends</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>Token:</span>
            <code 
              className="px-3 py-1.5 rounded font-mono text-sm"
              style={{ background: 'rgba(0,0,0,0.3)', color: 'var(--color-primary, #06B6D4)' }}
            >
              {league.inviteToken}
            </code>
            <button
              onClick={() => {
                navigator.clipboard.writeText(league.inviteToken);
                toast.success("Token copied!");
              }}
              className="px-3 py-1.5 rounded text-sm font-medium transition-all active:scale-95"
              style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
              data-testid="copy-token-button"
            >
              Copy
            </button>
            {navigator.share && (
              <button
                onClick={() => {
                  navigator.share({
                    title: `Join ${league.name}`,
                    text: `Join my league on Sport X! Use token: ${league.inviteToken}\n\n${window.location.origin}`
                  }).catch((err) => {
                    if (err.name !== 'AbortError') {
                      navigator.clipboard.writeText(league.inviteToken);
                      toast.success("Token copied!");
                    }
                  });
                }}
                className="px-3 py-1.5 rounded text-sm font-medium transition-all active:scale-95"
                style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981', border: '1px solid rgba(16, 185, 129, 0.3)' }}
                data-testid="share-button"
              >
                Share
              </button>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {['overview', 'managers', uiHints.assetPlural.toLowerCase(), 'fixtures'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="px-4 py-2 rounded-full text-sm font-bold uppercase tracking-wide whitespace-nowrap transition-all"
              style={{
                background: activeTab === tab ? 'var(--color-primary, #06B6D4)' : 'rgba(255,255,255,0.05)',
                color: activeTab === tab ? 'var(--bg-base, #0F172A)' : 'var(--text-secondary, rgba(255,255,255,0.6))',
              }}
              data-testid={`tab-${tab}`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* === TAB CONTENT === */}

        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Commissioner Actions */}
            {isCommissioner && league.status === "pending" && (
              <div 
                className="p-5 rounded-2xl space-y-4"
                style={{ 
                  background: 'rgba(139, 92, 246, 0.1)',
                  border: '1px solid rgba(139, 92, 246, 0.2)',
                }}
              >
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined" style={{ color: '#A78BFA' }}>admin_panel_settings</span>
                  <p className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>Commissioner Actions</p>
                </div>

                {/* Manage Teams Button */}
                <button
                  onClick={() => {
                    setEditingAssets(true);
                    loadAvailableAssets();
                  }}
                  className="w-full p-4 rounded-xl flex items-center justify-between transition-all active:scale-[0.98]"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                  data-testid="manage-teams-button"
                >
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                      {league.sportKey === 'cricket' ? 'sports_cricket' : 'sports_soccer'}
                    </span>
                    <div className="text-left">
                      <p className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>Manage {uiHints.assetPlural}</p>
                      <p className="text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                        {league.assetsSelected?.length || 0} selected for auction
                      </p>
                    </div>
                  </div>
                  <span className="material-symbols-outlined" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>chevron_right</span>
                </button>

                {/* Import Fixtures Button (Football only, not AFCON) */}
                {league.assetsSelected && league.assetsSelected.length > 0 && league.sportKey === 'football' && league.competitionCode !== 'AFCON' && (
                  <button
                    onClick={handleImportFootballFixtures}
                    disabled={importingFixtures || fixturesImported}
                    className="w-full p-4 rounded-xl flex items-center justify-between transition-all active:scale-[0.98] disabled:opacity-50"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                    data-testid="import-fixtures-button"
                  >
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>calendar_month</span>
                      <div className="text-left">
                        <p className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>Import Fixtures</p>
                        <p className="text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                          {fixturesImported ? 'Fixtures imported' : 'Optional - for scoring'}
                        </p>
                      </div>
                    </div>
                    {importingFixtures ? (
                      <div className="w-5 h-5 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: 'var(--color-primary, #06B6D4)', borderTopColor: 'transparent' }}></div>
                    ) : (
                      <span className="material-symbols-outlined" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>chevron_right</span>
                    )}
                  </button>
                )}

                {/* Import Cricket Fixture Button */}
                {league.assetsSelected && league.assetsSelected.length > 0 && league.sportKey === 'cricket' && (
                  <button
                    onClick={handleImportCricketFixture}
                    disabled={importingFixtures}
                    className="w-full p-4 rounded-xl flex items-center justify-between transition-all active:scale-[0.98] disabled:opacity-50"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                    data-testid="import-cricket-fixture-button"
                  >
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>calendar_month</span>
                      <div className="text-left">
                        <p className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>Import Next Fixture</p>
                        <p className="text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Import cricket fixture</p>
                      </div>
                    </div>
                    {importingFixtures ? (
                      <div className="w-5 h-5 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: 'var(--color-primary, #06B6D4)', borderTopColor: 'transparent' }}></div>
                    ) : (
                      <span className="material-symbols-outlined" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>chevron_right</span>
                    )}
                  </button>
                )}

                {/* Start Auction Button */}
                <button
                  onClick={startAuction}
                  disabled={startingAuction || !canStartAuction}
                  className="w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-[0.98] disabled:opacity-50"
                  style={{ 
                    background: canStartAuction ? 'var(--color-primary, #06B6D4)' : 'rgba(255,255,255,0.1)',
                    color: canStartAuction ? 'var(--bg-base, #0F172A)' : 'var(--text-muted, rgba(255,255,255,0.4))',
                  }}
                  data-testid="start-auction-button"
                >
                  {startingAuction ? 'Starting...' : canStartAuction ? 'Start Auction' : `Need ${league.minManagers - participants.length} more manager(s)`}
                </button>
              </div>
            )}

            {/* Go to Auction Button (non-commissioner, auction active) */}
            {league.status === "active" && league.activeAuctionId && (
              <button
                onClick={goToAuction}
                className="w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-[0.98]"
                style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
                data-testid="go-to-auction-button"
              >
                Go to Auction
              </button>
            )}

            {/* Available Assets in Competition */}
            <div 
              className="p-5 rounded-2xl"
              style={{ 
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <h3 className="font-bold text-sm mb-4" style={{ color: 'var(--text-primary, #fff)' }}>
                Available {uiHints.assetPlural} in Competition
              </h3>
              {loadingAssets ? (
                <div className="text-center py-4">
                  <div className="w-6 h-6 border-2 border-t-transparent rounded-full animate-spin mx-auto" style={{ borderColor: 'var(--color-primary, #06B6D4)', borderTopColor: 'transparent' }}></div>
                </div>
              ) : assets.length === 0 ? (
                <p className="text-sm" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                  No {uiHints.assetPlural.toLowerCase()} selected yet. {isCommissioner && 'Use "Manage ' + uiHints.assetPlural + '" to select.'}
                </p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {assets.slice(0, 10).map((asset) => (
                    <div 
                      key={asset.id}
                      className="p-3 rounded-xl flex items-center justify-between"
                      style={{ background: 'rgba(255,255,255,0.05)' }}
                    >
                      <div>
                        <p className="font-medium text-sm" style={{ color: 'var(--text-primary, #fff)' }}>{asset.name}</p>
                        {asset.country && (
                          <p className="text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>{asset.country}</p>
                        )}
                        {asset.meta?.franchise && (
                          <p className="text-xs" style={{ color: 'var(--color-primary, #06B6D4)' }}>{asset.meta.franchise}</p>
                        )}
                        {asset.meta?.role && (
                          <p className="text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>{asset.meta.role}</p>
                        )}
                      </div>
                    </div>
                  ))}
                  {assets.length > 10 && (
                    <p className="text-xs text-center py-2" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                      +{assets.length - 10} more
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Cricket Scoring Configuration */}
            {league.sportKey === "cricket" && (
              <div 
                className="p-5 rounded-2xl"
                style={{ 
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                }}
              >
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>Scoring Rules (Cricket)</h3>
                  {isCommissioner && !editingScoring && (
                    <button
                      onClick={() => {
                        setEditingScoring(true);
                        const currentOverrides = league.scoringOverrides || (sport ? sport.scoringSchema : null);
                        setScoringOverrides(currentOverrides ? JSON.parse(JSON.stringify(currentOverrides)) : getDefaultCricketScoring());
                      }}
                      className="text-xs font-bold uppercase tracking-widest"
                      style={{ color: 'var(--color-primary, #06B6D4)' }}
                      data-testid="edit-scoring-button"
                    >
                      Edit
                    </button>
                  )}
                </div>

                {!editingScoring ? (
                  <div className="grid grid-cols-2 gap-3">
                    {getCurrentScoringDisplay().map((item, index) => (
                      <div key={index} className="flex justify-between">
                        <span className="text-xs" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{item.label}:</span>
                        <span className="text-xs font-bold" style={{ color: 'var(--text-primary, #fff)' }}>{item.value}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      {['run', 'wicket', 'catch', 'stumping', 'runOut'].map((rule) => (
                        <div key={rule}>
                          <label className="text-xs block mb-1" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                            {rule.charAt(0).toUpperCase() + rule.slice(1).replace(/([A-Z])/g, ' $1')}
                          </label>
                          <input
                            type="number"
                            min="0"
                            step="0.1"
                            value={scoringOverrides?.rules?.[rule] || 0}
                            onChange={(e) => updateScoringRule(rule, parseFloat(e.target.value) || 0)}
                            className="w-full px-3 py-2 rounded-lg text-sm"
                            style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'var(--text-primary, #fff)' }}
                            data-testid={`scoring-${rule}-input`}
                          />
                        </div>
                      ))}
                    </div>
                    
                    <div className="space-y-2">
                      <p className="text-xs font-bold" style={{ color: 'var(--text-primary, #fff)' }}>Milestones</p>
                      {["halfCentury", "century", "fiveWicketHaul"].map((milestone) => {
                        const milestoneData = scoringOverrides?.milestones?.[milestone];
                        const label = milestone === "halfCentury" ? "Half Century (50+)" : 
                                    milestone === "century" ? "Century (100+)" : 
                                    "Five Wickets (5+)";
                        
                        return (
                          <div key={milestone} className="flex items-center justify-between">
                            <label className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={milestoneData?.enabled || false}
                                onChange={(e) => updateMilestone(milestone, "enabled", e.target.checked)}
                                className="rounded"
                                data-testid={`milestone-${milestone}-enabled`}
                              />
                              <span className="text-xs" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{label}</span>
                            </label>
                            {milestoneData?.enabled && (
                              <input
                                type="number"
                                min="0"
                                value={milestoneData?.points || 0}
                                onChange={(e) => updateMilestone(milestone, "points", parseInt(e.target.value) || 0)}
                                className="w-16 px-2 py-1 rounded text-xs text-center"
                                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'var(--text-primary, #fff)' }}
                                data-testid={`milestone-${milestone}-points`}
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveScoring}
                        disabled={savingScoring}
                        className="flex-1 py-2 rounded-lg text-sm font-bold transition-all active:scale-[0.98]"
                        style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
                        data-testid="save-scoring-button"
                      >
                        {savingScoring ? 'Saving...' : 'Save'}
                      </button>
                      <button
                        onClick={() => {
                          setEditingScoring(false);
                          setScoringOverrides(null);
                        }}
                        className="flex-1 py-2 rounded-lg text-sm font-bold transition-all active:scale-[0.98]"
                        style={{ background: 'rgba(255,255,255,0.1)', color: 'var(--text-primary, #fff)' }}
                        data-testid="cancel-scoring-button"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Standings Section (only when auction is active/completed) */}
            {(league.status === "active" || league.status === "completed") && standings.length > 0 && (
              <div 
                className="p-5 rounded-2xl"
                style={{ 
                  background: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>League Standings</h3>
                  {isCommissioner && (
                    <button
                      onClick={recomputeScores}
                      disabled={loadingScores}
                      className="text-xs font-bold uppercase tracking-widest"
                      style={{ color: 'var(--color-primary, #06B6D4)' }}
                      data-testid="recompute-scores-button"
                    >
                      {loadingScores ? 'Computing...' : 'Refresh'}
                    </button>
                  )}
                </div>
                
                {/* Standings Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                        <th className="text-left py-2">#</th>
                        <th className="text-left py-2">{uiHints.assetLabel}</th>
                        <th className="text-center py-2">W</th>
                        <th className="text-center py-2">D</th>
                        <th className="text-center py-2">L</th>
                        <th className="text-center py-2">GF</th>
                        <th className="text-center py-2">GA</th>
                        <th className="text-center py-2">GD</th>
                        <th className="text-center py-2 font-bold">Pts</th>
                      </tr>
                    </thead>
                    <tbody>
                      {standings.map((club, index) => {
                        const goalDiff = club.goalsScored - club.goalsConceded;
                        return (
                          <tr 
                            key={club.id}
                            className="border-t"
                            style={{ 
                              borderColor: 'rgba(255,255,255,0.05)',
                              background: index < 3 ? 'rgba(16, 185, 129, 0.1)' : 'transparent',
                            }}
                          >
                            <td className="py-2 font-bold" style={{ color: 'var(--text-primary, #fff)' }}>{index + 1}</td>
                            <td className="py-2 font-medium" style={{ color: 'var(--text-primary, #fff)' }}>{club.clubName}</td>
                            <td className="py-2 text-center" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{club.wins}</td>
                            <td className="py-2 text-center" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{club.draws}</td>
                            <td className="py-2 text-center" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{club.losses}</td>
                            <td className="py-2 text-center" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{club.goalsScored}</td>
                            <td className="py-2 text-center" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{club.goalsConceded}</td>
                            <td 
                              className="py-2 text-center font-medium"
                              style={{ color: goalDiff > 0 ? '#10B981' : goalDiff < 0 ? '#EF4444' : 'var(--text-secondary, rgba(255,255,255,0.6))' }}
                            >
                              {goalDiff > 0 ? '+' : ''}{goalDiff}
                            </td>
                            <td className="py-2 text-center font-bold" style={{ color: 'var(--color-primary, #06B6D4)' }}>{club.totalPoints}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                
                <div className="mt-4 text-[10px] space-y-1" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                  <p>Scoring: Win = 3 pts | Draw = 1 pt | Goal Scored = 1 pt</p>
                  <p style={{ color: '#10B981' }}>Green rows = Top 3 positions</p>
                </div>
              </div>
            )}

            {/* How It Works */}
            <div 
              className="p-5 rounded-2xl"
              style={{ 
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.2)',
              }}
            >
              <h3 className="font-bold text-sm mb-3" style={{ color: 'var(--text-primary, #fff)' }}>How It Works</h3>
              <ul className="space-y-2 text-xs" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                <li className="flex items-start gap-2">
                  <span style={{ color: 'var(--color-primary, #06B6D4)' }}>•</span>
                  The commissioner starts the auction and selects {uiHints.assetPlural.toLowerCase()} to bid on
                </li>
                <li className="flex items-start gap-2">
                  <span style={{ color: 'var(--color-primary, #06B6D4)' }}>•</span>
                  Each {uiHints.assetLabel.toLowerCase()} is auctioned for {league.timerSeconds} seconds
                </li>
                <li className="flex items-start gap-2">
                  <span style={{ color: 'var(--color-primary, #06B6D4)' }}>•</span>
                  If a bid is placed in the last {league.antiSnipeSeconds} seconds, the timer extends
                </li>
                <li className="flex items-start gap-2">
                  <span style={{ color: 'var(--color-primary, #06B6D4)' }}>•</span>
                  The highest bidder wins when the timer expires
                </li>
                <li className="flex items-start gap-2">
                  <span style={{ color: 'var(--color-primary, #06B6D4)' }}>•</span>
                  Each manager can bid up to their budget across multiple {uiHints.assetPlural.toLowerCase()}
                </li>
              </ul>
            </div>

            {/* Commissioner Info Box */}
            {isCommissioner && (
              <div 
                className="p-4 rounded-xl"
                style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}
              >
                <p className="text-sm font-bold" style={{ color: 'var(--color-primary, #06B6D4)' }}>
                  You are the commissioner of this league
                </p>
                <p className="text-xs mt-1" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                  {league.status === "pending" 
                    ? "You can start the auction when ready"
                    : league.status === "active"
                    ? "Auction is currently running. Click 'Go to Auction' to participate."
                    : "You can recompute scores to update standings"}
                </p>
              </div>
            )}

            {/* Non-Commissioner Active Auction Info */}
            {!isCommissioner && league.status === "active" && (
              <div 
                className="p-4 rounded-xl"
                style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)' }}
              >
                <p className="text-sm font-bold" style={{ color: '#10B981' }}>
                  Auction is Live!
                </p>
                <p className="text-xs mt-1" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                  Click &quot;Go to Auction&quot; to join the bidding and compete for {uiHints.assetPlural.toLowerCase()}.
                </p>
              </div>
            )}

            {/* Delete League Button (Commissioner only) */}
            {isCommissioner && (
              <button
                onClick={deleteLeague}
                className="w-full p-4 rounded-xl text-sm font-bold transition-all active:scale-[0.98]"
                style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: '#EF4444' }}
                data-testid="delete-league-button"
              >
                Delete Competition
              </button>
            )}
          </div>
        )}

        {/* MANAGERS TAB */}
        {activeTab === 'managers' && (
          <div className="space-y-3">
            {participants.length === 0 ? (
              <div className="text-center py-10">
                <span className="material-symbols-outlined text-4xl mb-2" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>group</span>
                <p style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>No managers have joined yet</p>
                <p className="text-xs mt-1" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Share the invite token to get started</p>
              </div>
            ) : (
              participants.map((participant, idx) => (
                <div 
                  key={participant.userId}
                  className="p-4 rounded-xl flex items-center justify-between"
                  style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm"
                      style={{ background: 'rgba(6, 182, 212, 0.2)', color: 'var(--color-primary, #06B6D4)' }}
                    >
                      {participant.userName?.charAt(0)?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <p className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>{participant.userName}</p>
                      {participant.userId === league.commissionerId && (
                        <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: 'var(--color-primary, #06B6D4)' }}>Commissioner</p>
                      )}
                    </div>
                  </div>
                  <span className="text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                    #{idx + 1}
                  </span>
                </div>
              ))
            )}
          </div>
        )}

        {/* TEAMS/PLAYERS TAB */}
        {activeTab === uiHints.assetPlural.toLowerCase() && (
          <div className="space-y-3">
            {loadingAssets ? (
              <div className="text-center py-10">
                <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin mx-auto" style={{ borderColor: 'var(--color-primary, #06B6D4)', borderTopColor: 'transparent' }}></div>
              </div>
            ) : assets.length === 0 ? (
              <div className="text-center py-10">
                <span className="material-symbols-outlined text-4xl mb-2" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                  {league.sportKey === 'cricket' ? 'sports_cricket' : 'sports_soccer'}
                </span>
                <p style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>No {uiHints.assetPlural.toLowerCase()} selected yet</p>
                {isCommissioner && (
                  <button
                    onClick={() => {
                      setEditingAssets(true);
                      loadAvailableAssets();
                    }}
                    className="mt-4 px-4 py-2 rounded-lg text-sm font-bold"
                    style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
                  >
                    Select {uiHints.assetPlural}
                  </button>
                )}
              </div>
            ) : (
              assets.map((asset) => (
                <div 
                  key={asset.id}
                  className="p-4 rounded-xl flex items-center justify-between"
                  style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
                >
                  <div>
                    <p className="font-bold text-sm" style={{ color: 'var(--text-primary, #fff)' }}>{asset.name}</p>
                    {asset.country && (
                      <p className="text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>{asset.country}</p>
                    )}
                    {asset.meta?.franchise && (
                      <p className="text-xs" style={{ color: 'var(--color-primary, #06B6D4)' }}>{asset.meta.franchise}</p>
                    )}
                    {asset.meta?.nationality && (
                      <span className="text-[10px] px-2 py-0.5 rounded mr-1" style={{ background: 'rgba(255,255,255,0.1)', color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                        {asset.meta.nationality}
                      </span>
                    )}
                    {asset.meta?.role && (
                      <span className="text-[10px]" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>{asset.meta.role}</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* FIXTURES TAB */}
        {activeTab === 'fixtures' && (
          <div className="space-y-4">
            {/* Update Scores Button (Commissioner) */}
            {isCommissioner && fixtures.length > 0 && (
              <button
                onClick={handleUpdateScores}
                disabled={loadingFixtures}
                className="w-full py-3 rounded-xl text-sm font-bold transition-all active:scale-[0.98] disabled:opacity-50"
                style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981', border: '1px solid rgba(16, 185, 129, 0.3)' }}
              >
                {loadingFixtures ? 'Updating...' : 'Update Match Scores'}
              </button>
            )}

            {loadingFixtures ? (
              <div className="text-center py-10">
                <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin mx-auto" style={{ borderColor: 'var(--color-primary, #06B6D4)', borderTopColor: 'transparent' }}></div>
              </div>
            ) : fixtures.length === 0 ? (
              <div className="text-center py-10">
                <span className="material-symbols-outlined text-4xl mb-2" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>calendar_month</span>
                <p style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>No fixtures imported</p>
                {isCommissioner && league.sportKey === 'football' && league.competitionCode !== 'AFCON' && (
                  <button
                    onClick={handleImportFootballFixtures}
                    disabled={importingFixtures}
                    className="mt-4 px-4 py-2 rounded-lg text-sm font-bold"
                    style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
                  >
                    {importingFixtures ? 'Importing...' : 'Import Fixtures'}
                  </button>
                )}
                {isCommissioner && league.sportKey === 'cricket' && (
                  <button
                    onClick={handleImportCricketFixture}
                    disabled={importingFixtures}
                    className="mt-4 px-4 py-2 rounded-lg text-sm font-bold"
                    style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
                  >
                    {importingFixtures ? 'Importing...' : 'Import Next Fixture'}
                  </button>
                )}
              </div>
            ) : (
              <>
                {/* Upcoming Fixtures */}
                {fixtures.filter(f => f.status === 'scheduled').length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Upcoming Matches</h4>
                    <div className="space-y-2">
                      {fixtures.filter(f => f.status === 'scheduled').map((fixture) => (
                        <div 
                          key={fixture.id}
                          className="p-4 rounded-xl"
                          style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
                        >
                          <div className="flex items-center justify-between">
                            <span 
                              className="text-sm font-medium flex-1 text-right"
                              style={{ color: fixture.homeTeamInLeague ? 'var(--color-primary, #06B6D4)' : 'var(--text-primary, #fff)' }}
                            >
                              {fixture.homeTeam}
                            </span>
                            <span className="px-3 text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>vs</span>
                            <span 
                              className="text-sm font-medium flex-1 text-left"
                              style={{ color: fixture.awayTeamInLeague ? 'var(--color-primary, #06B6D4)' : 'var(--text-primary, #fff)' }}
                            >
                              {fixture.awayTeam}
                            </span>
                          </div>
                          <p className="text-center text-xs mt-2" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                            {new Date(fixture.matchDate || fixture.startsAt).toLocaleDateString('en-GB', { 
                              weekday: 'short', 
                              day: 'numeric', 
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Completed Fixtures */}
                {fixtures.filter(f => f.status !== 'scheduled').length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Completed Matches</h4>
                    <div className="space-y-2">
                      {fixtures.filter(f => f.status !== 'scheduled').map((fixture) => (
                        <div 
                          key={fixture.id}
                          className="p-4 rounded-xl"
                          style={{ background: 'rgba(30, 41, 59, 0.3)', border: '1px solid rgba(255,255,255,0.05)' }}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1 text-right">
                              <span 
                                className="text-sm font-medium"
                                style={{ color: fixture.homeTeamInLeague ? 'var(--color-primary, #06B6D4)' : 'var(--text-primary, #fff)' }}
                              >
                                {fixture.homeTeam}
                              </span>
                              {fixture.goalsHome !== null && fixture.goalsHome !== undefined && (
                                <span 
                                  className="ml-2 text-lg font-bold"
                                  style={{ color: fixture.winner === fixture.homeTeam ? '#10B981' : 'var(--text-secondary, rgba(255,255,255,0.6))' }}
                                >
                                  {fixture.goalsHome}
                                </span>
                              )}
                            </div>
                            <span className="px-3 text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>-</span>
                            <div className="flex-1 text-left">
                              {fixture.goalsAway !== null && fixture.goalsAway !== undefined && (
                                <span 
                                  className="mr-2 text-lg font-bold"
                                  style={{ color: fixture.winner === fixture.awayTeam ? '#10B981' : 'var(--text-secondary, rgba(255,255,255,0.6))' }}
                                >
                                  {fixture.goalsAway}
                                </span>
                              )}
                              <span 
                                className="text-sm font-medium"
                                style={{ color: fixture.awayTeamInLeague ? 'var(--color-primary, #06B6D4)' : 'var(--text-primary, #fff)' }}
                              >
                                {fixture.awayTeam}
                              </span>
                            </div>
                          </div>
                          <div className="text-center mt-2">
                            <span 
                              className="text-[10px] font-bold uppercase px-2 py-1 rounded"
                              style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981' }}
                            >
                              {fixture.status === 'ft' || fixture.status === 'finished' ? 'FT' : fixture.status.toUpperCase()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Commissioner Instructions */}
                {isCommissioner && (
                  <div 
                    className="p-4 rounded-xl"
                    style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}
                  >
                    <p className="text-xs" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                      <strong style={{ color: 'var(--color-primary, #06B6D4)' }}>Commissioner:</strong> After matches complete, click &quot;Update Match Scores&quot; to fetch latest results. 
                      Then click &quot;Refresh&quot; in the Standings section to update league rankings.
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </main>

      {/* === MANAGE ASSETS MODAL (Full Screen) === */}
      {editingAssets && (
        <div className="fixed inset-0 z-50 flex flex-col" style={{ background: 'var(--bg-base, #0F172A)' }}>
          {/* Modal Header */}
          <header 
            className="px-4 py-4 flex items-center justify-between"
            style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}
          >
            <button 
              onClick={() => setEditingAssets(false)} 
              className="w-10 h-10 flex items-center justify-center"
            >
              <span className="material-symbols-outlined" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>close</span>
            </button>
            <h2 className="font-bold text-sm uppercase tracking-widest" style={{ color: 'var(--text-primary, #fff)' }}>
              Manage {uiHints.assetPlural}
            </h2>
            <button
              onClick={saveAssetSelection}
              disabled={loadingAssetSelection}
              className="text-sm font-bold"
              style={{ color: 'var(--color-primary, #06B6D4)' }}
              data-testid="save-teams-button"
            >
              {loadingAssetSelection ? 'Saving...' : 'Save'}
            </button>
          </header>

          {/* Selection Count */}
          <div className="px-4 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            <p className="text-sm" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
              <span className="font-bold" style={{ color: 'var(--color-primary, #06B6D4)' }}>{selectedAssetIds.length}</span> / {availableAssets.length} {uiHints.assetPlural.toLowerCase()} selected
            </p>
            <p className="text-[10px] mt-1" style={{ color: 'var(--color-timer-amber, #F59E0B)' }}>
              Changes are locked after auction starts
            </p>
          </div>

          {/* Filters */}
          {league.sportKey === 'football' && (
            <div className="px-4 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <select
                value={competitionFilter}
                onChange={(e) => setCompetitionFilter(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-sm"
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'var(--text-primary, #fff)' }}
              >
                <option value="all">All Teams ({availableAssets.length})</option>
                <option value="EPL">Premier League Only (20)</option>
                <option value="UCL">Champions League Only (36)</option>
                <option value="AFCON">AFCON Only (24)</option>
              </select>
            </div>
          )}

          {league.sportKey === 'cricket' && cricketFranchises.length > 0 && (
            <div className="px-4 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <select
                value={cricketTeamFilter}
                onChange={(e) => setCricketTeamFilter(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-sm"
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'var(--text-primary, #fff)' }}
              >
                <option value="all">All Franchises ({totalCricketPlayers})</option>
                {cricketFranchises.map(f => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </div>
          )}

          {/* Quick Actions */}
          <div className="px-4 py-2 flex gap-3">
            <button 
              onClick={() => setSelectedAssetIds(getFilteredAssets().map(a => a.id))}
              className="text-xs font-bold"
              style={{ color: 'var(--color-primary, #06B6D4)' }}
            >
              Select All
            </button>
            <span style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>|</span>
            <button 
              onClick={() => setSelectedAssetIds([])}
              className="text-xs font-bold"
              style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}
            >
              Clear All
            </button>
          </div>

          {/* Asset List */}
          <div className="flex-1 overflow-y-auto px-4 py-2">
            {loadingAssetSelection ? (
              <div className="text-center py-10">
                <div className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin mx-auto" style={{ borderColor: 'var(--color-primary, #06B6D4)', borderTopColor: 'transparent' }}></div>
              </div>
            ) : (
              <div className="space-y-2 pb-20">
                {getFilteredAssets().map((asset) => (
                  <button
                    key={asset.id}
                    onClick={() => handleAssetToggle(asset.id)}
                    className="w-full p-3 rounded-xl flex items-center justify-between text-left transition-all"
                    style={{ 
                      background: selectedAssetIds.includes(asset.id) ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255,255,255,0.05)',
                      border: selectedAssetIds.includes(asset.id) ? '1px solid rgba(6, 182, 212, 0.3)' : '1px solid transparent',
                    }}
                  >
                    <div>
                      <p className="font-medium text-sm" style={{ color: 'var(--text-primary, #fff)' }}>{asset.name}</p>
                      {asset.country && (
                        <p className="text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>{asset.country}</p>
                      )}
                      {asset.meta?.franchise && (
                        <p className="text-xs" style={{ color: 'var(--color-primary, #06B6D4)' }}>{asset.meta.franchise}</p>
                      )}
                      {asset.meta?.nationality && (
                        <span className="text-[10px] px-2 py-0.5 rounded mr-1" style={{ background: 'rgba(255,255,255,0.1)', color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                          {asset.meta.nationality}
                        </span>
                      )}
                      {asset.meta?.role && (
                        <span className="text-[10px]" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>{asset.meta.role}</span>
                      )}
                    </div>
                    <div 
                      className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0"
                      style={{ 
                        background: selectedAssetIds.includes(asset.id) ? 'var(--color-primary, #06B6D4)' : 'rgba(255,255,255,0.1)',
                      }}
                    >
                      {selectedAssetIds.includes(asset.id) && (
                        <span className="material-symbols-outlined text-sm" style={{ color: 'var(--bg-base, #0F172A)' }}>check</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <BottomNav />
    </div>
  );
}
