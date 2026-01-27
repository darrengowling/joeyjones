import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { formatCurrency } from "../utils/currency";
import { useSocketRoom } from "../hooks/useSocketRoom";
import BottomNav from "../components/BottomNav";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * LeagueDetailNew - Stitch-styled league detail page
 * Visual redesign only - all functionality matches LeagueDetail.js exactly
 */
export default function LeagueDetailNew() {
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
  const [uiHints, setUiHints] = useState({ assetLabel: "Club", assetPlural: "Clubs" });
  const [scoringOverrides, setScoringOverrides] = useState(null);
  const [editingScoring, setEditingScoring] = useState(false);
  const [savingScoring, setSavingScoring] = useState(false);
  const [availableAssets, setAvailableAssets] = useState([]);
  const [selectedAssetIds, setSelectedAssetIds] = useState([]);
  const [editingAssets, setEditingAssets] = useState(false);
  const [loadingAssetSelection, setLoadingAssetSelection] = useState(false);
  const [importingFixtures, setImportingFixtures] = useState(false);
  const [fixturesImported, setFixturesImported] = useState(false);
  const [startingAuction, setStartingAuction] = useState(false);
  const [competitionFilter, setCompetitionFilter] = useState("all");
  const [cricketTeamFilter, setCricketTeamFilter] = useState("all");
  const [cricketFranchises, setCricketFranchises] = useState([]);
  const [totalCricketPlayers, setTotalCricketPlayers] = useState(0);
  const [fixtures, setFixtures] = useState([]);
  const [loadingFixtures, setLoadingFixtures] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const { socket, connected, ready, listenerCount } = useSocketRoom('league', leagueId, { user });

  // Check if current user is the commissioner
  const isCommissioner = user && league && user.id === league.commissionerId;

  // Initial setup
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

  useEffect(() => {
    if (league) {
      document.title = `${league.name} - Competition | Sport X`;
    }
  }, [league]);

  // Socket listeners
  useEffect(() => {
    if (!user) return;

    socket.emit('join_league', { leagueId, userId: user.id }, (ack) => {
      if (ack && ack.ok) {
        console.log('✅ Joined league room');
      }
    });

    const handleMemberJoined = (data) => {
      if (data.leagueId === leagueId) {
        loadParticipants();
        toast.success(`${data.userName} joined!`);
      }
    };

    const handleParticipantUpdated = (data) => {
      if (data.leagueId === leagueId) {
        loadParticipants();
      }
    };

    const handleAuctionStarted = (data) => {
      if (data.leagueId === leagueId) {
        loadLeague();
        toast.success('Auction started!');
      }
    };

    socket.on('member_joined', handleMemberJoined);
    socket.on('participant_updated', handleParticipantUpdated);
    socket.on('auction_started', handleAuctionStarted);

    return () => {
      socket.off('member_joined', handleMemberJoined);
      socket.off('participant_updated', handleParticipantUpdated);
      socket.off('auction_started', handleAuctionStarted);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, leagueId, socket]);

  // Data loading functions (matching original exactly)
  const loadLeague = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}`);
      setLeague(response.data);
      
      if (response.data.sportKey) {
        const sportResponse = await axios.get(`${API}/sports/${response.data.sportKey}`);
        setSport(sportResponse.data);
        if (sportResponse.data.uiHints) {
          setUiHints(sportResponse.data.uiHints);
        }
      }
      setLoading(false);
    } catch (e) {
      console.error("Error loading league:", e);
      setLoading(false);
    }
  };

  const loadParticipants = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/participants`);
      setParticipants(response.data);
    } catch (e) {
      console.error("Error loading participants:", e);
    }
  };

  const loadStandings = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/standings`);
      setStandings(response.data);
    } catch (e) {
      console.error("Error loading standings:", e);
    }
  };

  const loadAssets = async () => {
    setLoadingAssets(true);
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/assets`);
      setAssets(response.data);
    } catch (e) {
      console.error("Error loading assets:", e);
    } finally {
      setLoadingAssets(false);
    }
  };

  const loadFixtures = async () => {
    setLoadingFixtures(true);
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/fixtures`);
      setFixtures(response.data);
      setFixturesImported(response.data && response.data.length > 0);
    } catch (e) {
      console.error("Error loading fixtures:", e);
    } finally {
      setLoadingFixtures(false);
    }
  };

  const loadAvailableAssets = async () => {
    if (!league) return;
    setLoadingAssetSelection(true);
    try {
      const pageSize = league.sportKey === 'cricket' ? 300 : 100;
      const response = await axios.get(`${API}/assets`, {
        params: { sportKey: league.sportKey, limit: pageSize }
      });
      const assetsData = response.data.assets || [];
      setAvailableAssets(assetsData);
      
      if (league.sportKey === 'cricket') {
        const franchises = [...new Set(assetsData.map(a => a.meta?.franchise).filter(Boolean))];
        setCricketFranchises(franchises.sort());
        setTotalCricketPlayers(assetsData.length);
      }
      
      const currentSelected = league.assetsSelected || [];
      setSelectedAssetIds(currentSelected);
    } catch (e) {
      console.error("Error loading available assets:", e);
    } finally {
      setLoadingAssetSelection(false);
    }
  };

  // Action handlers (matching original exactly)
  const goToAuction = () => {
    if (league.auctionId) {
      navigate(`/auction/${league.auctionId}`);
    } else if (league.activeAuctionId) {
      navigate(`/auction/${league.activeAuctionId}`);
    }
  };

  const startAuction = async () => {
    if (!isCommissioner) return;
    
    if (participants.length < league.minManagers) {
      toast.error(`Need at least ${league.minManagers} managers to start`);
      return;
    }

    setStartingAuction(true);
    try {
      const response = await axios.post(`${API}/leagues/${leagueId}/auction/start`, {
        commissionerId: user.id
      });
      toast.success("Auction started!");
      navigate(`/auction/${response.data.id}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to start auction");
    } finally {
      setStartingAuction(false);
    }
  };

  const enterWaitingRoom = async () => {
    if (!league.auctionId && !league.activeAuctionId) {
      toast.error("No auction created yet");
      return;
    }
    navigate(`/auction/${league.auctionId || league.activeAuctionId}`);
  };

  const importFixtures = async () => {
    if (!isCommissioner) return;
    setImportingFixtures(true);
    try {
      await axios.post(`${API}/leagues/${leagueId}/fixtures/import-from-api?commissionerId=${user.id}`);
      toast.success("Fixtures imported!");
      loadFixtures();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to import fixtures");
    } finally {
      setImportingFixtures(false);
    }
  };

  const saveSelectedAssets = async () => {
    if (!isCommissioner) return;
    setLoadingAssetSelection(true);
    try {
      await axios.put(`${API}/leagues/${leagueId}/assets-selected`, {
        commissionerId: user.id,
        assetIds: selectedAssetIds
      });
      toast.success(`${selectedAssetIds.length} ${uiHints.assetPlural} saved!`);
      setEditingAssets(false);
      loadLeague();
    } catch (e) {
      toast.error("Failed to save selection");
    } finally {
      setLoadingAssetSelection(false);
    }
  };

  const toggleAssetSelection = (assetId) => {
    setSelectedAssetIds(prev => 
      prev.includes(assetId) 
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    );
  };

  const selectAllFiltered = () => {
    const filteredIds = getFilteredAssets().map(a => a.id);
    setSelectedAssetIds(prev => [...new Set([...prev, ...filteredIds])]);
  };

  const deselectAllFiltered = () => {
    const filteredIds = getFilteredAssets().map(a => a.id);
    setSelectedAssetIds(prev => prev.filter(id => !filteredIds.includes(id)));
  };

  const getFilteredAssets = () => {
    let filtered = availableAssets;
    
    if (league?.sportKey === 'football' && competitionFilter !== 'all') {
      filtered = filtered.filter(a => a.competitionShort === competitionFilter);
    }
    
    if (league?.sportKey === 'cricket' && cricketTeamFilter !== 'all') {
      filtered = filtered.filter(a => a.meta?.franchise === cricketTeamFilter);
    }
    
    return filtered;
  };

  const recomputeScores = async () => {
    setLoadingScores(true);
    try {
      await axios.post(`${API}/leagues/${leagueId}/recompute-scores`);
      toast.success("Scores recomputed!");
      loadStandings();
    } catch (e) {
      toast.error("Failed to recompute scores");
    } finally {
      setLoadingScores(false);
    }
  };

  const deleteLeague = async () => {
    if (!isCommissioner) return;
    if (!window.confirm(`Are you sure you want to delete "${league.name}"? This cannot be undone.`)) return;
    
    try {
      await axios.delete(`${API}/leagues/${leagueId}?commissionerId=${user.id}`);
      toast.success("Competition deleted");
      navigate("/");
    } catch (e) {
      toast.error("Failed to delete");
    }
  };

  // Loading state
  if (loading || !league) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0F172A' }}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading competition...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen font-sans" style={{ background: '#0F172A', paddingBottom: '100px' }}>
      {/* Header */}
      <header 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-md z-40 px-4 py-4 flex items-center justify-between"
        style={{
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <button 
          onClick={() => navigate('/')}
          className="w-10 h-10 flex items-center justify-center rounded-full"
          style={{ background: 'rgba(255,255,255,0.05)' }}
        >
          <span className="material-symbols-outlined text-white">arrow_back</span>
        </button>
        <h1 className="text-sm font-black tracking-widest uppercase text-white truncate max-w-[200px]">
          {league.name}
        </h1>
        <div className="w-10"></div>
      </header>

      <main className="pt-20 px-4">
        {/* Live Auction Alert */}
        {league.status === "active" && league.activeAuctionId && (
          <button
            onClick={goToAuction}
            className="w-full mb-6 p-4 rounded-2xl flex items-center justify-between animate-pulse"
            style={{ 
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
            }}
          >
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-red-500 animate-ping"></div>
              <div>
                <p className="text-white font-bold text-sm">Auction is Live!</p>
                <p className="text-red-300 text-xs">Join the bidding now</p>
              </div>
            </div>
            <span className="material-symbols-outlined text-white">arrow_forward</span>
          </button>
        )}

        {/* Status Card */}
        <div 
          className="p-5 rounded-2xl mb-6"
          style={{ 
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Status</p>
              <span 
                className="px-3 py-1 rounded-full text-xs font-bold uppercase"
                style={{ 
                  background: league.status === 'active' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(6, 182, 212, 0.2)',
                  color: league.status === 'active' ? '#10B981' : '#06B6D4',
                }}
              >
                {league.status}
              </span>
            </div>
            <div className="text-right">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Managers</p>
              <p className="text-xl font-black text-white">
                {participants.length}<span className="text-slate-500">/{league.maxManagers}</span>
              </p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">Budget</p>
              <p className="text-lg font-bold text-white">{formatCurrency(league.budget)}</p>
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-1">{uiHints.assetPlural} Each</p>
              <p className="text-lg font-bold text-white">{league.clubSlots}</p>
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
            <span className="material-symbols-outlined" style={{ color: '#06B6D4' }}>group_add</span>
            <p className="text-white font-bold text-sm">Invite Friends</p>
          </div>
          <div className="flex items-center gap-2">
            <code 
              className="flex-1 px-3 py-2 rounded-lg font-mono text-sm text-center"
              style={{ background: 'rgba(0,0,0,0.3)', color: '#06B6D4' }}
            >
              {league.inviteToken}
            </code>
            <button
              onClick={() => {
                navigator.clipboard.writeText(league.inviteToken);
                toast.success("Copied!");
              }}
              className="px-4 py-2 rounded-lg font-bold text-sm"
              style={{ background: '#06B6D4', color: '#0F172A' }}
            >
              Copy
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {['overview', 'managers', uiHints.assetPlural.toLowerCase(), 'fixtures'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="px-4 py-2 rounded-full text-xs font-bold uppercase tracking-wider whitespace-nowrap transition-all"
              style={{
                background: activeTab === tab ? '#06B6D4' : 'rgba(255,255,255,0.05)',
                color: activeTab === tab ? '#0F172A' : '#94A3B8',
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-4">
            {/* Commissioner Actions */}
            {isCommissioner && league.status === "pending" && (
              <div 
                className="p-5 rounded-2xl space-y-4"
                style={{ 
                  background: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: '#06B6D4' }}>
                  Commissioner Actions
                </p>
                
                {/* Manage Teams Button */}
                <button
                  onClick={() => { setEditingAssets(true); loadAvailableAssets(); }}
                  className="w-full p-4 rounded-xl flex items-center justify-between"
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                >
                  <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-slate-400">tune</span>
                    <div className="text-left">
                      <p className="text-white font-bold text-sm">Manage {uiHints.assetPlural}</p>
                      <p className="text-slate-500 text-xs">{league.assetsSelected?.length || 0} selected</p>
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-slate-600">chevron_right</span>
                </button>

                {/* Import Fixtures */}
                {league.assetsSelected?.length > 0 && league.sportKey === 'football' && (
                  <button
                    onClick={importFixtures}
                    disabled={importingFixtures || fixturesImported}
                    className="w-full p-4 rounded-xl flex items-center justify-between disabled:opacity-50"
                    style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}
                  >
                    <div className="flex items-center gap-3">
                      <span className="material-symbols-outlined text-slate-400">calendar_month</span>
                      <div className="text-left">
                        <p className="text-white font-bold text-sm">Import Fixtures</p>
                        <p className="text-slate-500 text-xs">{fixturesImported ? 'Already imported' : 'Optional - for scoring'}</p>
                      </div>
                    </div>
                    {importingFixtures ? (
                      <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <span className="material-symbols-outlined text-slate-600">chevron_right</span>
                    )}
                  </button>
                )}

                {/* Start Auction */}
                <button
                  onClick={startAuction}
                  disabled={startingAuction || participants.length < league.minManagers}
                  className="w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-[0.98] disabled:opacity-50"
                  style={{ 
                    background: participants.length >= league.minManagers ? '#06B6D4' : 'rgba(255,255,255,0.1)',
                    color: participants.length >= league.minManagers ? '#0F172A' : '#64748B',
                  }}
                >
                  {startingAuction ? 'Starting...' : `Start Auction (${participants.length}/${league.minManagers} min)`}
                </button>
              </div>
            )}

            {/* Waiting Room Button (non-commissioner) */}
            {!isCommissioner && league.status === "pending" && league.auctionId && (
              <button
                onClick={enterWaitingRoom}
                className="w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm"
                style={{ background: '#06B6D4', color: '#0F172A' }}
              >
                Enter Waiting Room
              </button>
            )}

            {/* Standings Preview */}
            {standings.length > 0 && (
              <div 
                className="p-5 rounded-2xl"
                style={{ 
                  background: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                }}
              >
                <div className="flex items-center justify-between mb-4">
                  <p className="text-white font-bold text-sm">Standings</p>
                  {isCommissioner && (
                    <button
                      onClick={recomputeScores}
                      disabled={loadingScores}
                      className="text-xs font-bold uppercase tracking-widest"
                      style={{ color: '#06B6D4' }}
                    >
                      {loadingScores ? 'Computing...' : 'Refresh'}
                    </button>
                  )}
                </div>
                <div className="space-y-2">
                  {standings.slice(0, 5).map((entry, idx) => (
                    <div 
                      key={entry.odeon || idx}
                      className="flex items-center justify-between p-3 rounded-xl"
                      style={{ background: 'rgba(255,255,255,0.05)' }}
                    >
                      <div className="flex items-center gap-3">
                        <span 
                          className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                          style={{ 
                            background: idx === 0 ? '#FFD700' : idx === 1 ? '#C0C0C0' : idx === 2 ? '#CD7F32' : 'rgba(255,255,255,0.1)',
                            color: idx < 3 ? '#0F172A' : '#94A3B8',
                          }}
                        >
                          {idx + 1}
                        </span>
                        <span className="text-white font-medium text-sm">{entry.userName}</span>
                      </div>
                      <span className="text-cyan-400 font-bold">{entry.totalPoints || 0} pts</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Danger Zone */}
            {isCommissioner && (
              <button
                onClick={deleteLeague}
                className="w-full p-4 rounded-xl text-red-400 text-sm font-bold"
                style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' }}
              >
                Delete Competition
              </button>
            )}
          </div>
        )}

        {activeTab === 'managers' && (
          <div className="space-y-3">
            {participants.length === 0 ? (
              <div className="text-center py-10">
                <span className="material-symbols-outlined text-4xl text-slate-600 mb-2">group</span>
                <p className="text-slate-400">No managers yet</p>
              </div>
            ) : (
              participants.map((p, idx) => (
                <div 
                  key={p.userId}
                  className="p-4 rounded-xl flex items-center justify-between"
                  style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-full flex items-center justify-center font-bold"
                      style={{ background: 'rgba(6, 182, 212, 0.2)', color: '#06B6D4' }}
                    >
                      {p.userName?.charAt(0)?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <p className="text-white font-bold text-sm">{p.userName}</p>
                      {p.userId === league.commissionerId && (
                        <p className="text-[10px] font-bold uppercase tracking-widest text-cyan-400">Commissioner</p>
                      )}
                    </div>
                  </div>
                  <span className="text-slate-500 text-sm">{p.clubsWon?.length || 0} {uiHints.assetPlural}</span>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === uiHints.assetPlural.toLowerCase() && (
          <div className="space-y-3">
            {loadingAssets ? (
              <div className="text-center py-10">
                <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              </div>
            ) : assets.length === 0 ? (
              <div className="text-center py-10">
                <span className="material-symbols-outlined text-4xl text-slate-600 mb-2">sports_soccer</span>
                <p className="text-slate-400">No {uiHints.assetPlural.toLowerCase()} selected yet</p>
              </div>
            ) : (
              assets.map((asset) => (
                <div 
                  key={asset.id}
                  className="p-4 rounded-xl flex items-center justify-between"
                  style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
                >
                  <div>
                    <p className="text-white font-bold text-sm">{asset.name}</p>
                    {asset.meta?.franchise && (
                      <p className="text-cyan-400 text-xs">{asset.meta.franchise}</p>
                    )}
                    {asset.country && (
                      <p className="text-slate-500 text-xs">{asset.country}</p>
                    )}
                  </div>
                  {asset.ownerId && (
                    <span className="text-xs font-bold px-2 py-1 rounded" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981' }}>
                      Owned
                    </span>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'fixtures' && (
          <div className="space-y-3">
            {loadingFixtures ? (
              <div className="text-center py-10">
                <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              </div>
            ) : fixtures.length === 0 ? (
              <div className="text-center py-10">
                <span className="material-symbols-outlined text-4xl text-slate-600 mb-2">calendar_month</span>
                <p className="text-slate-400">No fixtures imported</p>
                {isCommissioner && league.sportKey === 'football' && (
                  <button
                    onClick={importFixtures}
                    disabled={importingFixtures}
                    className="mt-4 px-4 py-2 rounded-lg text-sm font-bold"
                    style={{ background: '#06B6D4', color: '#0F172A' }}
                  >
                    Import Fixtures
                  </button>
                )}
              </div>
            ) : (
              fixtures.slice(0, 10).map((fixture) => (
                <div 
                  key={fixture.id}
                  className="p-4 rounded-xl"
                  style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-white text-sm font-medium">{fixture.homeTeam}</span>
                    <span className="text-slate-500 text-xs">vs</span>
                    <span className="text-white text-sm font-medium">{fixture.awayTeam}</span>
                  </div>
                  <p className="text-slate-500 text-xs mt-1 text-center">
                    {new Date(fixture.date).toLocaleDateString()}
                  </p>
                </div>
              ))
            )}
          </div>
        )}
      </main>

      {/* Manage Assets Modal */}
      {editingAssets && (
        <div className="fixed inset-0 z-50 flex flex-col" style={{ background: '#0F172A' }}>
          {/* Modal Header */}
          <header className="px-4 py-4 flex items-center justify-between border-b border-white/10">
            <button onClick={() => setEditingAssets(false)} className="text-slate-400">
              <span className="material-symbols-outlined">close</span>
            </button>
            <h2 className="text-white font-bold text-sm uppercase tracking-widest">
              Manage {uiHints.assetPlural}
            </h2>
            <button
              onClick={saveSelectedAssets}
              disabled={loadingAssetSelection}
              className="text-sm font-bold"
              style={{ color: '#06B6D4' }}
            >
              {loadingAssetSelection ? 'Saving...' : 'Save'}
            </button>
          </header>

          {/* Selection Count */}
          <div className="px-4 py-3 border-b border-white/10">
            <p className="text-slate-400 text-sm">
              <span className="text-cyan-400 font-bold">{selectedAssetIds.length}</span> {uiHints.assetPlural.toLowerCase()} selected
            </p>
          </div>

          {/* Filter */}
          {league.sportKey === 'football' && (
            <div className="px-4 py-3 border-b border-white/10">
              <select
                value={competitionFilter}
                onChange={(e) => setCompetitionFilter(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-white text-sm"
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}
              >
                <option value="all">All Competitions</option>
                <option value="PL">Premier League</option>
                <option value="UCL">Champions League</option>
              </select>
            </div>
          )}

          {league.sportKey === 'cricket' && cricketFranchises.length > 0 && (
            <div className="px-4 py-3 border-b border-white/10">
              <select
                value={cricketTeamFilter}
                onChange={(e) => setCricketTeamFilter(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-white text-sm"
                style={{ background: 'rgba(255,255,255,0.1)', border: 'none' }}
              >
                <option value="all">All Franchises ({totalCricketPlayers})</option>
                {cricketFranchises.map(f => (
                  <option key={f} value={f}>{f}</option>
                ))}
              </select>
            </div>
          )}

          {/* Quick Actions */}
          <div className="px-4 py-2 flex gap-2">
            <button onClick={selectAllFiltered} className="text-xs font-bold text-cyan-400">Select All</button>
            <span className="text-slate-600">|</span>
            <button onClick={deselectAllFiltered} className="text-xs font-bold text-slate-400">Deselect All</button>
          </div>

          {/* Asset List */}
          <div className="flex-1 overflow-y-auto px-4 py-2">
            {loadingAssetSelection ? (
              <div className="text-center py-10">
                <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              </div>
            ) : (
              <div className="space-y-2">
                {getFilteredAssets().map((asset) => (
                  <button
                    key={asset.id}
                    onClick={() => toggleAssetSelection(asset.id)}
                    className="w-full p-3 rounded-xl flex items-center justify-between text-left transition-all"
                    style={{ 
                      background: selectedAssetIds.includes(asset.id) ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255,255,255,0.05)',
                      border: selectedAssetIds.includes(asset.id) ? '1px solid rgba(6, 182, 212, 0.3)' : '1px solid transparent',
                    }}
                  >
                    <div>
                      <p className="text-white font-medium text-sm">{asset.name}</p>
                      {asset.meta?.franchise && (
                        <p className="text-slate-400 text-xs">{asset.meta.franchise}</p>
                      )}
                      {asset.country && (
                        <p className="text-slate-400 text-xs">{asset.country}</p>
                      )}
                    </div>
                    <div 
                      className="w-6 h-6 rounded-full flex items-center justify-center"
                      style={{ 
                        background: selectedAssetIds.includes(asset.id) ? '#06B6D4' : 'rgba(255,255,255,0.1)',
                      }}
                    >
                      {selectedAssetIds.includes(asset.id) && (
                        <span className="material-symbols-outlined text-sm" style={{ color: '#0F172A' }}>check</span>
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
