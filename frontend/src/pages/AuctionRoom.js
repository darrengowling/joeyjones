import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuctionClock } from "../hooks/useAuctionClock";
import { useSocketRoom } from "../hooks/useSocketRoom";
import { formatCurrency, parseCurrencyInput, isValidCurrencyInput } from "../utils/currency";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AuctionRoom() {
  const { auctionId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [auction, setAuction] = useState(null);
  const [clubs, setClubs] = useState([]);
  const [currentClub, setCurrentClub] = useState(null);
  const [bids, setBids] = useState([]);
  const [bidAmount, setBidAmount] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedClubForLot, setSelectedClubForLot] = useState(null);
  const [league, setLeague] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [currentLotId, setCurrentLotId] = useState(null);
  const [sport, setSport] = useState(null);
  const [uiHints, setUiHints] = useState({ assetLabel: "Club", assetPlural: "Clubs" }); // Default to football
  const [currentBid, setCurrentBid] = useState(null);
  const [currentBidder, setCurrentBidder] = useState(null);
  const [bidSequence, setBidSequence] = useState(0);
  const [timerSettings, setTimerSettings] = useState({ timerSeconds: 30, antiSnipeSeconds: 10 }); // Everton Bug Fix 3

  // Use shared socket room hook
  const { socket, connected, ready, listenerCount } = useSocketRoom('auction', auctionId, { user });

  // Use the new auction clock hook with socket from useSocketRoom
  const { remainingMs } = useAuctionClock(socket, currentLotId);

  // Initial setup: load user and data
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
    } else {
      alert("Please sign in first");
      navigate("/");
      return;
    }

    loadAuction();
    loadClubs();
  }, [auctionId]);

  // Socket event handlers - single useEffect with proper cleanup
  useEffect(() => {
    if (!user) return;

    console.log(`🎧 [AuctionRoom] Setting up socket listeners (Count: ${listenerCount})`);

    // Prompt E: Handle auction_snapshot for late joiners (replaces sync_state)
    const onAuctionSnapshot = (data) => {
      console.log("📸 Auction snapshot received:", data);
      
      // Hydrate full state from snapshot
      if (data.status) setAuction(prev => ({ ...prev, status: data.status }));
      if (data.currentClub) setCurrentClub(data.currentClub);
      if (data.currentBid !== undefined) setCurrentBid(data.currentBid);
      if (data.currentBidder) setCurrentBidder(data.currentBidder);
      if (data.seq !== undefined) setBidSequence(data.seq);
      if (data.participants) setParticipants(data.participants);
      if (data.currentBids) setBids(data.currentBids);
      if (data.timer && data.timer.lotId) setCurrentLotId(data.timer.lotId);
      
      console.log("✅ State hydrated from auction_snapshot");
    };

    // Handle sync_state (legacy) - same as auction_snapshot
    const onSyncState = (data) => {
      console.log("Received sync state:", data);
      if (data.currentClub) {
        setCurrentClub(data.currentClub);
      }
      if (data.currentBids) {
        setBids(data.currentBids);
      }
      if (data.participants) {
        setParticipants(data.participants);
      }
      if (data.currentBid !== undefined) {
        setCurrentBid(data.currentBid);
      }
      if (data.currentBidder) {
        setCurrentBidder(data.currentBidder);
      }
      if (data.seq !== undefined) {
        setBidSequence(data.seq);
      }
      if (data.auction && data.auction.currentLotId) {
        setCurrentLotId(data.auction.currentLotId);
      }
      console.log("✅ Sync state processed");
    };

    // Handle bid_placed (adds to bid history)
    const onBidPlaced = (data) => {
      console.log("Bid placed event received:", data);
      setBids((prev) => [data.bid, ...prev]);
      loadAuction();
      loadClubs();
    };

    // Handle bid_update (updates current bid display) - prevents stale updates
    const onBidUpdate = (data) => {
      console.log("🔔 Bid update received:", data);
      
      // Only accept bid updates with seq >= current seq (prevents stale updates)
      if (data.seq >= bidSequence) {
        console.log(`✅ Updating current bid: ${formatCurrency(data.amount)} by ${data.bidder?.displayName} (seq: ${data.seq})`);
        setCurrentBid(data.amount);
        setCurrentBidder(data.bidder);
        setBidSequence(data.seq);
        // Note: Bid history list will be refreshed on next lot or page load
      } else {
        console.log(`⚠️ Ignoring stale bid update: seq=${data.seq}, current=${bidSequence}`);
      }
    };

    // Handle lot_started (new club on auction block)
    const onLotStarted = (data) => {
      console.log("Lot started:", data);
      
      if (data.isUnsoldRetry) {
        alert(`🔄 Re-offering unsold club: ${data.club.name}!`);
      }
      
      setCurrentClub(data.club);
      if (data.timer && data.timer.lotId) {
        setCurrentLotId(data.timer.lotId);
      }
      
      // Clear bid state when new lot starts
      setCurrentBid(null);
      setCurrentBidder(null);
      setBidSequence(0);
      console.log("✅ Cleared bid state for new lot");
    };

    // Handle sold event
    const onSold = (data) => {
      console.log("Lot sold:", data);
      
      if (data.unsold) {
        alert(`❌ Club went unsold! "${data.clubId}" will be offered again later.`);
      } else {
        const winnerName = data.winningBid ? data.winningBid.userName : "Unknown";
        const amount = data.winningBid ? formatCurrency(data.winningBid.amount) : "";
        alert(`✅ Club sold to ${winnerName} for ${amount}!`);
        
        // CRITICAL FIX: Immediately update club status to 'sold' in local state
        // DON'T reload clubs - rely on this update to avoid race conditions
        if (data.clubId && data.winningBid) {
          console.log(`✅ Marking club ${data.clubId} as sold to ${winnerName}`);
          setClubs(prevClubs => {
            const updated = prevClubs.map(club => 
              club.id === data.clubId 
                ? { ...club, status: 'sold', winner: winnerName, winningBid: data.winningBid.amount }
                : club
            );
            const soldCount = updated.filter(c => c.status === 'sold').length;
            console.log(`📊 Current sold count: ${soldCount}/${updated.length}`);
            return updated;
          });
        }
      }
      
      setCurrentClub(null);
      setBidAmount("");
      if (data.participants) {
        setParticipants(data.participants);
      }
      loadAuction();
      // REMOVED: loadClubs() - we trust the sold event data instead of reloading
    };

    // Handle anti-snipe event
    const onAntiSnipe = (data) => {
      console.log("Anti-snipe triggered:", data);
      alert(`🔥 Anti-snipe! Timer extended!`);
    };

    // Handle auction_complete event
    const onAuctionComplete = (data) => {
      console.log("Auction complete:", data);
      console.log("Final club ID:", data.finalClubId);
      console.log("Final winning bid:", data.finalWinningBid);
      
      // Update participants with final state
      if (data.participants) {
        setParticipants(data.participants);
      }
      
      // CRITICAL FIX: Update final club status immediately and DON'T reload clubs
      // Reloading causes race condition - trust the event data
      if (data.finalClubId && data.finalWinningBid) {
        console.log("✅ Updating final club status to 'sold' (no reload)");
        setClubs(prevClubs => {
          const updated = prevClubs.map(club => 
            club.id === data.finalClubId 
              ? { ...club, status: 'sold', winner: data.finalWinningBid.userName, winningBid: data.finalWinningBid.amount }
              : club
          );
          const soldCount = updated.filter(c => c.status === 'sold').length;
          console.log(`📊 Clubs after final update: ${soldCount} sold out of ${updated.length} total`);
          return updated;
        });
        
        // Clear current bid if it's the final club
        if (currentClub?.id === data.finalClubId) {
          setCurrentBid(null);
          setCurrentBidder(null);
        }
        
        // Only reload auction status, NOT clubs (to preserve our manual update)
        loadAuction();
      } else {
        // No final club info, reload everything
        loadAuction();
        loadClubs();
      }
      
      alert(data.message || "Auction complete! All clubs have been auctioned.");
    };

    // Handle auction_paused event
    const onAuctionPaused = (data) => {
      console.log("Auction paused:", data);
      alert(`⏸️ ${data.message}`);
      loadAuction();
    };

    // Handle auction_resumed event
    const onAuctionResumed = (data) => {
      console.log("Auction resumed:", data);
      alert(`▶️ ${data.message}`);
      loadAuction();
    };

    // Register all event listeners
    socket.on('auction_snapshot', onAuctionSnapshot);
    socket.on('sync_state', onSyncState);  // Legacy support
    socket.on('bid_placed', onBidPlaced);
    socket.on('bid_update', onBidUpdate);
    socket.on('lot_started', onLotStarted);
    socket.on('sold', onSold);
    socket.on('anti_snipe', onAntiSnipe);
    socket.on('auction_complete', onAuctionComplete);
    socket.on('auction_paused', onAuctionPaused);
    socket.on('auction_resumed', onAuctionResumed);

    // Cleanup function - remove all listeners
    return () => {
      console.log('🧹 [AuctionRoom] Removing socket listeners');
      socket.off('sync_state', onSyncState);
      socket.off('bid_placed', onBidPlaced);
      socket.off('bid_update', onBidUpdate);
      socket.off('lot_started', onLotStarted);
      socket.off('sold', onSold);
      socket.off('anti_snipe', onAntiSnipe);
      socket.off('auction_complete', onAuctionComplete);
      socket.off('auction_paused', onAuctionPaused);
      socket.off('auction_resumed', onAuctionResumed);
    };
  }, [auctionId, user, bidSequence, listenerCount]);

  const loadAuction = async () => {
    try {
      const response = await axios.get(`${API}/auction/${auctionId}`);
      console.log("Auction data loaded:", response.data);
      console.log("Bids from API:", response.data.bids);
      setAuction(response.data.auction);
      setBids(response.data.bids);
      if (response.data.currentClub) {
        setCurrentClub(response.data.currentClub);
      }
      
      // Set lot ID for timer hook
      if (response.data.auction.currentLotId) {
        setCurrentLotId(response.data.auction.currentLotId);
      }

      // Load league
      const leagueResponse = await axios.get(`${API}/leagues/${response.data.auction.leagueId}`);
      setLeague(leagueResponse.data);
      
      // Everton Bug Fix 3: Load timer settings from league
      setTimerSettings({
        timerSeconds: leagueResponse.data.timerSeconds || 30,
        antiSnipeSeconds: leagueResponse.data.antiSnipeSeconds || 10
      });
      
      // Load sport information based on league's sportKey
      if (leagueResponse.data.sportKey) {
        try {
          const sportResponse = await axios.get(`${API}/sports/${leagueResponse.data.sportKey}`);
          setSport(sportResponse.data);
          setUiHints(sportResponse.data.uiHints);
        } catch (e) {
          console.error("Error loading sport info:", e);
          // Keep default uiHints for clubs
        }
      }

      // Load participants
      const participantsResponse = await axios.get(`${API}/leagues/${response.data.auction.leagueId}/participants`);
      setParticipants(participantsResponse.data);
    } catch (e) {
      console.error("Error loading auction:", e);
    } finally {
      setLoading(false);
    }
  };

  const loadClubs = async () => {
    try {
      const response = await axios.get(`${API}/auction/${auctionId}/clubs`);
      setClubs(response.data.clubs);
      console.log("Loaded clubs:", response.data);
    } catch (error) {
      console.error("Error loading clubs:", error);
    }
  };

  const loadParticipants = async () => {
    try {
      if (!auction) return;
      const leagueId = auction.leagueId;
      const response = await axios.get(`${API}/leagues/${leagueId}/participants`);
      setParticipants(response.data);
    } catch (e) {
      console.error("Error loading participants:", e);
    }
  };

  const placeBid = async () => {
    if (!user || !currentClub || !bidAmount) {
      alert("Please enter your strategic bid amount to claim ownership");
      return;
    }

    // Parse £m input (e.g., "5m", "£5m", "5")
    if (!isValidCurrencyInput(bidAmount)) {
      alert("Please enter a valid bid amount (e.g., 5m, £10m, 23m)");
      return;
    }
    
    const amount = parseCurrencyInput(bidAmount);

    // Check user's budget
    const userParticipant = participants.find((p) => p.userId === user.id);
    if (userParticipant && amount > userParticipant.budgetRemaining) {
      alert(`Strategic budget exceeded. You have ${formatCurrency(userParticipant.budgetRemaining)} remaining for team ownership`);
      return;
    }

    // Check if higher than current highest bid
    const currentBids = bids.filter((b) => b.clubId === currentClub.id);
    if (currentBids.length > 0) {
      const highestBid = Math.max(...currentBids.map((b) => b.amount));
      if (amount <= highestBid) {
        alert(`Strategic bid must exceed current leading bid: ${formatCurrency(highestBid)}`);
        return;
      }
    }

    try {
      await axios.post(`${API}/auction/${auctionId}/bid`, {
        userId: user.id,
        clubId: currentClub.id,
        amount,
      });
      setBidAmount("");
    } catch (e) {
      console.error("Error placing bid:", e);
      alert(e.response?.data?.detail || "Error placing bid");
    }
  };

  const startLot = async (clubId) => {
    try {
      await axios.post(`${API}/auction/${auctionId}/start-lot/${clubId}`);
      setSelectedClubForLot(null);
    } catch (e) {
      console.error("Error starting lot:", e);
      alert("Error starting lot");
    }
  };

  const completeLot = async () => {
    try {
      await axios.post(`${API}/auction/${auctionId}/complete-lot`);
    } catch (e) {
      console.error("Error completing lot:", e);
    }
  };

  const pauseAuction = async () => {
    try {
      const result = await axios.post(`${API}/auction/${auctionId}/pause`);
      console.log("Auction paused:", result.data);
    } catch (e) {
      console.error("Error pausing auction:", e);
      alert("Error pausing auction: " + (e.response?.data?.detail || e.message));
    }
  };

  const resumeAuction = async () => {
    try {
      const result = await axios.post(`${API}/auction/${auctionId}/resume`);
      console.log("Auction resumed:", result.data);
    } catch (e) {
      console.error("Error resuming auction:", e);
      alert("Error resuming auction: " + (e.response?.data?.detail || e.message));
    }
  };

  const deleteAuction = async () => {
    if (!window.confirm(
      `Are you sure you want to delete this auction? This will:\n` +
      `• Remove all auction data and bids\n` +
      `• Reset all participant budgets\n` +
      `• Return the league to ready state\n\n` +
      `This action cannot be undone.`
    )) {
      return;
    }

    try {
      const result = await axios.delete(`${API}/auction/${auctionId}`);
      console.log("Auction deleted:", result.data);
      alert("Auction deleted successfully!");
      navigate("/"); // Go back to homepage
    } catch (e) {
      console.error("Error deleting auction:", e);
      alert("Error deleting auction: " + (e.response?.data?.detail || e.message));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading auction...</div>
      </div>
    );
  }

  const isCommissioner = league && user && league.commissionerId === user.id;
  const currentClubBids = currentClub ? bids.filter((b) => b.clubId === currentClub.id) : [];
  
  // Debug logging for bid display
  if (currentClub) {
    console.log("Current club ID:", currentClub.id);
    console.log("All bids:", bids);
    console.log("Current club bids:", currentClubBids);
  }
  const highestBid = currentClubBids.length > 0 ? Math.max(...currentClubBids.map((b) => b.amount)) : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <button
            onClick={() => navigate("/")}
            className="btn btn-secondary text-white hover:underline mb-4"
          >
            ← Back to Home
          </button>

          {/* Prompt G: Top strip with league info and progress */}
          {league && auction && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-6">
                  <div>
                    <span className="text-sm font-medium text-blue-800">League:</span>
                    <span className="text-sm text-blue-600 ml-1">{league.name}</span>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-blue-800">Progress:</span>
                    <span className="text-sm text-blue-600 ml-1">
                      Lot {auction.currentLot || 0} / {auction.clubQueue?.length || 0}
                    </span>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-blue-800">Managers with slots left:</span>
                    <span className="text-sm text-blue-600 ml-1">
                      {participants.filter(p => (p.clubsWon?.length || 0) < (league.clubSlots || 3)).map(p => {
                        const slotsLeft = (league.clubSlots || 3) - (p.clubsWon?.length || 0);
                        return `${p.userName}=${slotsLeft}`;
                      }).join(', ') || 'None'}
                    </span>
                  </div>
                </div>
                {auction.status === "completed" && (
                  <div className="bg-green-100 text-green-800 px-3 py-1 rounded text-sm font-medium">
                    ✅ Auction Complete
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Auction Header */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex justify-between items-center">
              <div>
                <div className="stack-md">
                  <h1 className="h1 text-3xl font-bold text-gray-900">
                    {league ? league.name : "Strategic Competition Arena"}
                  </h1>
                  <p className="subtle text-gray-600">
                    Lot #{auction?.currentLot || 0} • Status: {auction?.status || "Unknown"}
                    {auction?.status === "paused" && (
                      <span className="chip ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-sm rounded">⏸️ PAUSED</span>
                    )}
                  </p>
                </div>
              </div>
              
              {/* Commissioner Controls */}
              {isCommissioner && (
                <div className="row-gap-md flex">
                  {auction?.status === "active" && (
                    <button
                      onClick={pauseAuction}
                      className="btn btn-secondary px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
                      title="Pause Auction"
                    >
                      ⏸️ Pause
                    </button>
                  )}
                  
                  {auction?.status === "paused" && (
                    <button
                      onClick={resumeAuction}
                      className="btn btn-secondary px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                      title="Resume Auction"
                    >
                      ▶️ Resume
                    </button>
                  )}
                  
                  <button
                    onClick={completeLot}
                    className="btn btn-danger px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                    title="Complete Current Lot"
                  >
                    Complete Lot
                  </button>
                  
                  <button
                    onClick={deleteAuction}
                    className="btn btn-danger px-4 py-2 bg-red-700 text-white rounded hover:bg-red-800"
                    title="Delete Entire Auction"
                  >
                    🗑️ Delete Auction
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Participant Budgets */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-xl font-bold mb-4 text-gray-900">Manager Budgets</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {participants.map((p) => {
                const isCurrentUser = user && p.userId === user.id;
                return (
                  <div
                    key={p.id}
                    className={`p-4 rounded-lg border-2 ${
                      isCurrentUser
                        ? "bg-blue-50 border-blue-500"
                        : "bg-gray-50 border-gray-200"
                    }`}
                  >
                    <div className="font-semibold text-gray-900 text-sm mb-1">
                      {p.userName} {isCurrentUser && "(You)"}
                    </div>
                    <div className="stack-md">
                      <div className="chip text-2xl font-bold text-green-600">
                        {formatCurrency(p.budgetRemaining)}
                      </div>
                      <div className="subtle text-xs text-gray-500">
                        Spent: {formatCurrency(p.totalSpent)}
                      </div>
                      <div className="subtle text-xs text-gray-500">
                        🏆 Clubs: {p.clubsWon.length}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Current Lot */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6 app-card">
              {currentClub ? (
                <div>
                  <h2 className="h2 text-2xl font-bold mb-4 text-gray-900">🔥 Current Team Ownership</h2>
                  
                  {/* Timer - WHITE ON BLACK for maximum visibility */}
                  <div className="bg-black text-white p-6 rounded-lg mb-6 text-center shadow-lg border-2 border-white">
                    <div className="text-5xl font-bold">
                      {(() => {
                        const s = Math.ceil((remainingMs ?? 0) / 1000);
                        const mm = String(Math.floor(s / 60)).padStart(2, "0");
                        const ss = String(s % 60).padStart(2, "0");
                        const warn = (remainingMs ?? 0) < 10000;
                        return (
                          <span data-testid="auction-timer" className={warn ? 'text-red-400' : 'text-white'}>
                            {mm}:{ss}
                          </span>
                        );
                      })()}
                    </div>
                    <div className="text-sm mt-2 text-white">Time Remaining</div>
                    <div className="text-xs mt-1 text-gray-300">
                      {timerSettings.timerSeconds}s per team | Extends by {timerSettings.antiSnipeSeconds}s on late bids
                    </div>
                  </div>

                  {/* Club Info */}
                  <div className="app-card bg-gray-50 p-6 rounded-lg mb-6">
                    <div className="stack-md">
                      <h3 className="h1 text-3xl font-bold text-gray-900">{currentClub.name}</h3>
                      <p className="h2 text-xl text-gray-600">{currentClub.country}</p>
                      <p className="subtle text-sm text-gray-500">UEFA ID: {currentClub.uefaId}</p>
                    </div>
                  </div>

                  {/* Current Bid Panel (Prompt G: Enhanced with bidder info) */}
                  {currentBid > 0 && currentBidder && (
                    <div className="app-card bg-green-50 border border-green-200 p-4 rounded-lg mb-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="subtle text-sm text-gray-600">💰 Current Bid</div>
                          <div className="text-3xl font-bold text-green-600">{formatCurrency(currentBid)}</div>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                              {currentBidder.displayName.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {currentBidder.displayName}
                              </div>
                              <div className="text-xs text-gray-500">Leading bidder</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Fallback: Show no bids message */}
                  {!currentBid && (
                    <div className="app-card bg-blue-50 border border-blue-200 p-4 rounded-lg mb-6">
                      <div className="subtle text-sm text-gray-600">💰 No bids yet</div>
                      <div className="text-lg text-gray-600">Be the first to claim ownership!</div>
                    </div>
                  )}

                  {/* Bid Input */}
                  <div>
                    <div className="flex gap-4 mb-2">
                      <input
                        type="number"
                        placeholder="e.g., 5m, £10m, 23m"
                        className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
                        value={bidAmount}
                        onChange={(e) => setBidAmount(e.target.value)}
                        disabled={!ready}
                        data-testid="bid-amount-input"
                      />
                      <button
                        onClick={placeBid}
                        disabled={!ready || participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3)}
                        className={`btn btn-primary px-8 py-3 rounded-lg font-semibold text-lg ${
                          !ready || participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3) 
                            ? 'bg-gray-400 cursor-not-allowed' 
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                        data-testid="place-bid-button"
                        title={
                          !ready 
                            ? "Loading auction state..." 
                            : participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3) 
                              ? "Roster full" 
                              : ""
                        }
                      >
                        {!ready 
                          ? "Loading..." 
                          : participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3) 
                            ? "Roster Full" 
                            : "Claim Ownership"
                        }
                      </button>
                    </div>
                    {participants.find((p) => p.userId === user?.id) && (
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>
                          Your strategic budget remaining: {formatCurrency(participants.find((p) => p.userId === user.id).budgetRemaining)}
                        </p>
                        <p className="flex items-center">
                          <span>Roster:</span>
                          <span className="ml-1 font-medium">
                            {participants.find((p) => p.userId === user.id).clubsWon?.length || 0} / {league?.clubSlots || 3}
                          </span>
                          <span className="ml-2">
                            {participants.find((p) => p.userId === user.id).clubsWon?.length >= (league?.clubSlots || 3) 
                              ? '🔒 Full' 
                              : '📍 Active'
                            }
                          </span>
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Bid History for Current Club */}
                  <div className="mt-6">
                    <h4 className="font-semibold text-gray-900 mb-3">Bid History</h4>
                    <div className="max-h-64 overflow-y-auto">
                      {currentClubBids.length === 0 ? (
                        <p className="text-gray-500">No bids yet</p>
                      ) : (
                        <div className="space-y-2">
                          {currentClubBids
                            .sort((a, b) => b.amount - a.amount)
                            .map((bid) => (
                              <div
                                key={bid.id}
                                className="flex justify-between items-center p-3 bg-gray-50 rounded"
                              >
                                <span className="font-semibold">{bid.userName}</span>
                                <span className="text-green-600 font-bold">{formatCurrency(bid.amount)}</span>
                              </div>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-gray-700">
                    ⏱️ Ownership opportunity will auto-complete when timer expires. Next team will load automatically for strategic bidding.
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">⏳</div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">
                    {auction?.status === "completed" ? "Auction Complete!" : "Preparing Next Strategic Opportunity..."}
                  </h2>
                  <p className="text-gray-600">
                    {auction?.status === "completed" 
                      ? `All ${uiHints.assetPlural.toLowerCase()} have been auctioned. Check the standings!` 
                      : `${uiHints.assetPlural} auto-load in random order. Next ${uiHints.assetLabel.toLowerCase()} starting soon...`}
                  </p>
                </div>
              )}
            </div>

            {/* Clubs Overview */}
            <div className="app-card bg-white rounded-lg shadow-lg p-6">
              <h3 className="h2 text-xl font-bold mb-4 text-gray-900">🏆 {uiHints.assetPlural} Available for Ownership</h3>
              
              {/* Summary Stats */}
              <div className="stack-md">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="chip bg-blue-50 p-2 rounded">
                    <div className="font-semibold text-blue-800">Total</div>
                    <div className="text-blue-600">{clubs.length}</div>
                  </div>
                  <div className="chip bg-green-50 p-2 rounded">
                    <div className="font-semibold text-green-800">✅ Sold</div>
                    <div className="text-green-600">{clubs.filter(c => c.status === 'sold').length}</div>
                  </div>
                  <div className="chip bg-yellow-50 p-2 rounded">
                    <div className="font-semibold text-yellow-800">🔥 Current</div>
                    <div className="text-yellow-600">{clubs.filter(c => c.status === 'current').length}</div>
                  </div>
                  <div className="chip bg-gray-50 p-2 rounded">
                    <div className="font-semibold text-gray-800">⏳ Remaining</div>
                    <div className="text-gray-600">{clubs.filter(c => c.status === 'upcoming').length}</div>
                  </div>
                </div>
              </div>

              {/* Club List */}
              <div className="max-h-[500px] overflow-y-auto space-y-1">
                {clubs.map((club) => {
                  const statusColors = {
                    current: "bg-yellow-100 border-yellow-300 text-yellow-800",
                    upcoming: "bg-blue-50 border-blue-200 text-blue-800",
                    sold: "bg-green-50 border-green-200 text-green-800",
                    unsold: "bg-red-50 border-red-200 text-red-800"
                  };
                  
                  const statusIcons = {
                    current: "🔥",
                    upcoming: "⏳",
                    sold: "✅",
                    unsold: "❌"
                  };
                  
                  return (
                    <div
                      key={club.id}
                      className={`p-2 rounded-lg border text-xs ${statusColors[club.status] || 'bg-gray-50 border-gray-200'}`}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold truncate">{club.name}</div>
                          <div className="text-xs opacity-75">{club.country}</div>
                        </div>
                        <div className="ml-2 flex flex-col items-end">
                          <div className="flex items-center gap-1">
                            <span>{statusIcons[club.status]}</span>
                            {/* Hide lot number to keep draw order secret */}
                          </div>
                          {club.status === 'sold' && club.winningBid && (
                            <div className="text-xs font-semibold">
                              {formatCurrency(club.winningBid)}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {club.status === 'sold' && club.winner && (
                        <div className="text-xs mt-1 opacity-75">
                          Won by {club.winner}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="mt-4 text-xs text-gray-500 space-y-1 border-t pt-3">
                <p>🔥 Current lot • ⏳ Upcoming • ✅ Sold • ❌ Unsold</p>
                <p>Order is randomized - use for strategy only</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
