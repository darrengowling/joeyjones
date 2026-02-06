import { useState, useEffect, useRef, useMemo, useCallback, memo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { useAuctionClock } from "../hooks/useAuctionClock";
import { useSocketRoom } from "../hooks/useSocketRoom";
import { formatCurrency, parseCurrencyInput, isValidCurrencyInput } from "../utils/currency";
import { debounceSocketEvent } from "../utils/performance";
import { debugLogger } from "../utils/debugLogger";
import TeamCrest from "../components/TeamCrest";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Memoized sub-components for better performance (Production Hardening Day 11)
const BidHistoryItem = memo(({ bid, isWinning }) => (
  <div 
    className={`p-3 rounded-xl ${isWinning ? 'bg-[#00F0FF]/20 border-l-4 border-[#00F0FF]' : 'bg-white/5 border-l-4 border-white/10'}`}
  >
    <div className="flex justify-between items-center">
      <span className="font-medium text-white">{bid.userName || 'Anonymous'}</span>
      <span className="font-bold text-[#00F0FF]">{formatCurrency(bid.amount)}</span>
    </div>
    <span className="text-xs text-white/40">{new Date(bid.createdAt).toLocaleTimeString()}</span>
  </div>
));

BidHistoryItem.displayName = 'BidHistoryItem';

function AuctionRoom() {
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
  const [participantCount, setParticipantCount] = useState(0); // Prompt A: Server-authoritative count
  const [currentLotId, setCurrentLotId] = useState(null);
  const [sport, setSport] = useState(null);
  const [uiHints, setUiHints] = useState({ assetLabel: "Club", assetPlural: "Clubs" }); // Default to football
  const [currentBid, setCurrentBid] = useState(null);
  const [currentBidder, setCurrentBidder] = useState(null);
  const [bidSequence, setBidSequence] = useState(0);
  const [countdown, setCountdown] = useState(null); // For 3-second pause between lots
  const [timerSettings, setTimerSettings] = useState({ timerSeconds: 30, antiSnipeSeconds: 10 }); // Everton Bug Fix 3
  const [nextFixture, setNextFixture] = useState(null); // Next fixture for current club
  const [isSubmittingBid, setIsSubmittingBid] = useState(false); // Prevent double-submission
  const [showAllTeamsModal, setShowAllTeamsModal] = useState(false); // View All teams modal
  const [showBudgetsModal, setShowBudgetsModal] = useState(false); // Show all user budgets

  // Use shared socket room hook
  const { socket, connected, ready, listenerCount } = useSocketRoom('auction', auctionId, { user });

  // Use the new auction clock hook with socket from useSocketRoom
  const { remainingMs } = useAuctionClock(socket, currentLotId, auction?.status);

  // Prompt E: Polling fallback for waiting room (top-level hook, conditional inside)
  useEffect(() => {
    if (auction?.status === "waiting") {
      console.log("⏳ Starting waiting room polling (every 2s)");
      const pollInterval = setInterval(() => {
        console.log("🔄 Polling auction status from waiting room...");
        loadAuction();
      }, 2000);

      return () => {
        console.log("🛑 Stopping waiting room polling");
        clearInterval(pollInterval);
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auction?.status]);

  // Set page title
  useEffect(() => {
    document.title = `Auction Room | Sport X`;
  }, []);

  // Initial setup: load user and data
  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
    }
    // Prompt C: No hard redirect - will show soft guard below if no user

    loadAuction();
    loadClubs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auctionId]);

  // Socket event handlers - single useEffect with proper cleanup
  useEffect(() => {
    if (!user) return;

    console.log(`🎧 [AuctionRoom] Setting up socket listeners (Count: ${listenerCount})`);
    
    // Prompt D: Join auction room on connect
    socket.emit('join_auction', { auctionId, userId: user.id }, (ack) => {
      if (ack && ack.ok) {
        console.log(`✅ Joined auction room: ${ack.room}, size: ${ack.roomSize}`);
      }
    });

    // Prompt E: Handle auction_snapshot for late joiners (replaces sync_state)
    const onAuctionSnapshot = (data) => {
      debugLogger.logSocketEvent('auction_snapshot', data);
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
      debugLogger.logSocketEvent('sync_state', data);
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
    // PERF FIX: Removed loadAuction() and loadClubs() - these caused 2 HTTP GETs per bid per client
    // Trust socket events as source of truth; resync only on reconnect or seq gap
    const onBidPlaced = (data) => {
      debugLogger.logSocketEvent('bid_placed', data);
      const receiveTime = performance.now();
      console.log("📥 bid_placed received:", {
        ...data,
        receiveTime: new Date().toISOString(),
        latencyMs: data.serverTime ? (Date.now() - new Date(data.serverTime).getTime()) : 'N/A'
      });
      setBids((prev) => [data.bid, ...prev]);
      // Note: Full reload removed for performance - bid_update handles UI state
    };

    // Handle bid_update (updates current bid display) - prevents stale updates
    const onBidUpdate = (data) => {
      debugLogger.logSocketEvent('bid_update', data);
      const receiveTime = performance.now();
      const serverLatency = data.serverTime ? (Date.now() - new Date(data.serverTime).getTime()) : null;
      
      console.log("🔔 bid_update received:", {
        seq: data.seq,
        amount: data.amount,
        bidder: data.bidder?.displayName,
        receiveTime: new Date().toISOString(),
        serverLatencyMs: serverLatency
      });
      
      // PERF FIX: Detect seq gaps (missed events) - trigger resync if gap > 1
      const seqGap = data.seq - bidSequence;
      if (seqGap > 1) {
        console.warn(`⚠️ Seq gap detected: expected ${bidSequence + 1}, got ${data.seq}. Resyncing...`);
        loadAuction();
      }
      
      // Only accept bid updates with seq >= current seq (prevents stale updates)
      if (data.seq >= bidSequence) {
        console.log(`✅ Applying bid update: ${formatCurrency(data.amount)} by ${data.bidder?.displayName} (seq: ${data.seq}, latency: ${serverLatency}ms)`);
        setCurrentBid(data.amount);
        setCurrentBidder(data.bidder);
        setBidSequence(data.seq);
        
        // PERF INSTRUMENTATION: Log render timing
        requestAnimationFrame(() => {
          const renderTime = performance.now();
          console.log(`🎨 bid_update rendered: totalMs=${Math.round(renderTime - receiveTime)}`);
        });
      } else {
        console.log(`⚠️ Ignoring stale bid update: seq=${data.seq}, current=${bidSequence}`);
      }
    };

    // Handle lot_started (new club on auction block)
    const onLotStarted = (data) => {
      debugLogger.logSocketEvent('lot_started', data);
      console.log("🚀 Lot started:", data);
      
      if (data.isUnsoldRetry) {
        toast(`🔄 Re-offering unsold ${uiHints.assetLabel.toLowerCase()}: ${data.club.name}!`, { duration: 4000 });
      }
      
      // Prompt E: Load auction to transition from waiting to active
      loadAuction();
      
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
      debugLogger.logSocketEvent('sold', data);
      console.log("=== SOLD EVENT RECEIVED ===");
      console.log("  clubId:", data.clubId);
      console.log("  clubName:", data.clubName);
      console.log("  unsold:", data.unsold);
      console.log("  winningBid:", data.winningBid);
      
      const playerName = data.clubName || `Unknown ${uiHints.assetLabel.toLowerCase()}`;
      
      if (data.unsold) {
        toast.error(`${playerName} went unsold and will be offered again later.`);
      } else {
        const winnerName = data.winningBid ? data.winningBid.userName : "Unknown";
        const amount = data.winningBid ? formatCurrency(data.winningBid.amount) : "";
        toast.success(`${playerName} sold to ${winnerName} for ${amount}!`, { duration: 4000 });
        
        // CRITICAL FIX: Immediately update club status to 'sold' in local state
        // DON'T reload clubs - rely on this update to avoid race conditions
        if (data.clubId && data.winningBid) {
          console.log(`✅ Marking ${uiHints.assetLabel.toLowerCase()} ${data.clubId} as sold to ${winnerName}`);
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
      setCurrentBid(null);
      setCurrentBidder(null);
      if (data.participants) {
        setParticipants(data.participants);
      }
      loadAuction();
      // REMOVED: loadClubs() - we trust the sold event data instead of reloading
    };

    // Handle anti-snipe event
    const onAntiSnipe = (data) => {
      debugLogger.logSocketEvent('anti_snipe', data);
      console.log("Anti-snipe triggered:", data);
      toast("🔥 Anti-snipe! Timer extended!", { duration: 3000, icon: '⏱️' });
    };

    // Handle auction_complete event
    const onAuctionComplete = (data) => {
      debugLogger.logSocketEvent('auction_complete', data);
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
      
      toast.success(data.message || `Auction complete! All ${uiHints.assetPlural.toLowerCase()} have been auctioned.`, { duration: 5000 });
    };

    // Handle auction_paused event
    const onAuctionPaused = (data) => {
      debugLogger.logSocketEvent('auction_paused', data);
      console.log("Auction paused:", data);
      toast(`⏸️ ${data.message}`, { duration: 4000, icon: '⏸️' });
      loadAuction();
    };

    // Handle auction_resumed event
    const onAuctionResumed = (data) => {
      debugLogger.logSocketEvent('auction_resumed', data);
      console.log("Auction resumed:", data);
      toast(`▶️ ${data.message}`, { duration: 4000, icon: '▶️' });
      loadAuction();
    };

    // Handle auction_deleted event - CRITICAL for stuck users
    const onAuctionDeleted = (data) => {
      debugLogger.logSocketEvent('auction_deleted', data);
      console.log("🗑️ Auction deleted by commissioner:", data);
      toast.error(data.message || "Auction has been deleted by the commissioner", { duration: 5000 });
      
      // Clear any countdown overlay
      setCountdown(null);
      
      // Navigate back to home after short delay
      setTimeout(() => {
        navigate('/');
      }, 2000);
    };

    // Prompt A: Handle participants_changed for live count updates
    const onParticipantsChanged = (data) => {
      debugLogger.logSocketEvent('participants_changed', data);
      console.log("👥 Participants changed:", data);
      
      // Re-fetch participants from API to get latest data
      if (auction?.leagueId) {
        loadParticipants();
      }
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
    socket.on('auction_deleted', onAuctionDeleted); // CRITICAL: Handle deletion
    socket.on('participants_changed', onParticipantsChanged); // Prompt A
    
    // PERF FIX: Resync on reconnect - only time we do full reload now
    const onReconnect = () => {
      debugLogger.logSocketEvent('reconnect', { timestamp: new Date().toISOString() });
      console.log('🔄 Socket reconnected - resyncing auction state');
      loadAuction();
      loadClubs();
    };
    socket.on('connect', onReconnect);
    
    // Handle waiting room updates
    const onWaitingRoomUpdated = (data) => {
      debugLogger.logSocketEvent('waiting_room_updated', data);
      console.log('🚪 Waiting room updated:', data.usersInWaitingRoom);
      setAuction(prev => ({ ...prev, usersInWaitingRoom: data.usersInWaitingRoom }));
    };
    socket.on('waiting_room_updated', onWaitingRoomUpdated);
    
    // Handle countdown between lots
    const onNextTeamCountdown = (data) => {
      debugLogger.logSocketEvent('next_team_countdown', data);
      console.log('⏱️ Countdown:', data.seconds);
      if (data.seconds === 0) {
        // Immediately clear overlay when countdown reaches 0
        setCountdown(null);
      } else {
        setCountdown(data.seconds);
      }
    };
    socket.on('next_team_countdown', onNextTeamCountdown);

    // Cleanup function - remove all listeners
    return () => {
      console.log('🧹 [AuctionRoom] Removing socket listeners');
      socket.off('auction_snapshot', onAuctionSnapshot);
      socket.off('sync_state', onSyncState);  // Legacy
      socket.off('bid_placed', onBidPlaced);
      socket.off('bid_update', onBidUpdate);
      socket.off('lot_started', onLotStarted);
      socket.off('sold', onSold);
      socket.off('anti_snipe', onAntiSnipe);
      socket.off('auction_complete', onAuctionComplete);
      socket.off('auction_paused', onAuctionPaused);
      socket.off('auction_resumed', onAuctionResumed);
      socket.off('auction_deleted', onAuctionDeleted); // CRITICAL
      socket.off('participants_changed', onParticipantsChanged); // Prompt A
      socket.off('connect', onReconnect); // PERF FIX
      socket.off('waiting_room_updated', onWaitingRoomUpdated);
      socket.off('next_team_countdown', onNextTeamCountdown);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auctionId, user, bidSequence, listenerCount]);

  // Pre-fill bid input with current bid amount
  useEffect(() => {
    // When club changes, clear any pending bid input
    // User must actively click +£1m/+£5m/+£10m to build their bid
    setBidAmount("");
  }, [currentClub?.id]); // Only trigger on club change, not on every currentBid update


  // Load next fixture when current club changes
  useEffect(() => {
    if (currentClub && currentClub.id) {
      loadNextFixture(currentClub.id);
    } else {
      setNextFixture(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentClub]);


  // Poll for auction existence when paused (to detect reset without refresh)
  useEffect(() => {
    if (!auction || auction.status !== 'paused') {
      return; // Only poll when paused
    }

    const checkAuctionExists = async () => {
      try {
        await axios.get(`${API}/auction/${auctionId}`);
        // Auction still exists, do nothing
      } catch (e) {
        if (e.response && e.response.status === 404) {
          console.log("⚠️ Auction deleted while paused - showing reset message");
          setAuction(null); // Trigger reset message screen
        }
      }
    };

    // Check every 3 seconds while paused
    const pollInterval = setInterval(checkAuctionExists, 3000);

    return () => clearInterval(pollInterval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auction?.status, auctionId]);



  const loadAuction = async () => {
    try {
      const response = await axios.get(`${API}/auction/${auctionId}`);
      console.log("Auction data loaded:", response.data);
      console.log("Bids from API:", response.data.bids);
      
      // Initialize debug logger with auction ID
      debugLogger.setAuctionId(auctionId);
      debugLogger.log('auction_start', {
        status: response.data.auction.status,
        currentLot: response.data.auction.currentLot,
        existingBids: response.data.bids.length
      });
      
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

      // Prompt A: Load participants with new API format (count + participants array)
      const participantsResponse = await axios.get(`${API}/leagues/${response.data.auction.leagueId}/participants`);
      console.log("📊 Participants loaded:", participantsResponse.data);
      
      // Set both count and participants from server response
      setParticipantCount(participantsResponse.data.count || 0);
      setParticipants(participantsResponse.data.participants || []);
    } catch (e) {
      console.error("Error loading auction:", e);
      
      // If auction no longer exists (404 - likely reset by commissioner), clear auction state
      if (e.response && e.response.status === 404) {
        console.log("⚠️ Auction not found - likely reset by commissioner");
        setAuction(null); // This will trigger the reset message screen
      }
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
      
      // Prompt A: Use new API format with count and participants
      console.log("📊 Participants refreshed:", response.data);
      setParticipantCount(response.data.count || 0);
      setParticipants(response.data.participants || []);
    } catch (e) {
      console.error("Error loading participants:", e);
    }
  };

  const loadNextFixture = async (clubId) => {
    try {
      // Use league ID from auction to filter fixtures by competition
      const leagueId = auction?.leagueId || league?.id;
      const url = leagueId 
        ? `${API}/assets/${clubId}/next-fixture?leagueId=${leagueId}`
        : `${API}/assets/${clubId}/next-fixture`;
      
      const response = await axios.get(url);
      if (response.data.fixture) {
        setNextFixture(response.data.fixture);
        console.log("📅 Next fixture loaded:", response.data.fixture);
      } else {
        setNextFixture(null);
        console.log("📅 No upcoming fixtures for this team");
      }
    } catch (error) {
      console.error("Error loading next fixture:", error);
      setNextFixture(null); // Fail gracefully
    }
  };


  const placeBid = async () => {
    if (!user || !currentClub || !bidAmount) {
      toast.error("Please enter your strategic bid amount to claim ownership");
      return;
    }

    // Parse £m input (e.g., "5m", "£5m", "5")
    if (!isValidCurrencyInput(bidAmount)) {
      toast.error("Please enter a valid bid amount (e.g., 5m, £10m, 23m)");
      return;
    }
    
    const amount = parseCurrencyInput(bidAmount);
    
    // Get current state for logging (not validation)
    const userParticipant = participants.find((p) => p.userId === user.id);
    const currentBids = bids.filter((b) => b.clubId === currentClub.id);
    const highestBid = currentBids.length > 0 ? Math.max(...currentBids.map((b) => b.amount)) : 0;

    // Detailed logging for diagnostics
    const attemptData = {
      auctionId,
      clubId: currentClub.id,
      clubName: currentClub.name,
      amount,
      amountFormatted: formatCurrency(amount),
      userBudget: userParticipant?.budgetRemaining,
      highestBid,
      existingBidsCount: currentBids.length,
      timestamp: new Date().toISOString()
    };
    
    console.log("🔵 bid:attempt", attemptData);
    debugLogger.log('bid:attempt', attemptData);

    // Prevent double-submission
    if (isSubmittingBid) {
      console.log("⚠️ bid:blocked (already submitting)");
      debugLogger.log('bid:blocked', { reason: 'double_submission' });
      return;
    }

    setIsSubmittingBid(true);
    const startTime = performance.now();

    try {
      console.log("📤 bid:sent", { auctionId, clubId: currentClub.id, amount });
      debugLogger.log('bid:sent', { clubId: currentClub.id, amount });
      
      const response = await axios.post(`${API}/auction/${auctionId}/bid`, {
        userId: user.id,
        clubId: currentClub.id,
        amount,
      }, {
        timeout: 10000 // 10 second timeout
      });
      
      const duration = performance.now() - startTime;
      
      // PERF INSTRUMENTATION: Enhanced timing metrics
      console.log("✅ bid:success", { 
        auctionId, 
        clubId: currentClub.id, 
        amount,
        tapToAckMs: Math.round(duration),
        response: response.data 
      });
      
      debugLogger.log('bid:success', { 
        clubId: currentClub.id, 
        amount,
        tapToAckMs: Math.round(duration),
        response: response.data 
      });
      
      toast.success(`Bid placed: ${formatCurrency(amount)}`);
      setBidAmount("");
      
    } catch (e) {
      const duration = performance.now() - startTime;
      const errorData = {
        auctionId,
        clubId: currentClub.id,
        amount,
        error: e.message,
        response: e.response?.data,
        status: e.response?.status,
        code: e.code,
        durationMs: Math.round(duration)
      };
      
      console.error("❌ bid:error", errorData);
      debugLogger.log('bid:error', errorData);
      
      // Detailed error handling
      if (e.code === 'ECONNABORTED' || e.message.includes('timeout')) {
        toast.error("Bid request timed out. Please try again.");
      } else if (e.response?.status === 429) {
        // Rate limit exceeded
        console.warn("⚠️ evt=bid:rate_limited", {
          auctionId,
          clubId: currentClub.id,
          amount,
          retryAfter: e.response?.headers?.['retry-after']
        });
        debugLogger.log('bid:rate_limited', {
          clubId: currentClub.id,
          amount,
          retryAfter: e.response?.headers?.['retry-after']
        });
        const errorMsg = e.response?.data?.detail || "Rate limit exceeded. Please wait a moment and try again.";
        toast.error(errorMsg, { duration: 5000 });
      } else if (e.response) {
        // Server responded with error - show backend message
        const errorMsg = e.response?.data?.detail || `Server error: ${e.response.status}`;
        toast.error(errorMsg);
        
        // Clear input on error - user can re-enter if needed
        setBidAmount("");
      } else if (e.request) {
        // Request made but no response
        toast.error("No response from server. Check your connection.");
      } else {
        // Something else went wrong
        toast.error("Failed to place bid. Please try again.");
      }
    } finally {
      setIsSubmittingBid(false);
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


  const resetAuction = async () => {
    if (!window.confirm(
      `Reset this auction? This will:\n` +
      `• Clear all bids and auction history\n` +
      `• Reset all participant budgets and rosters\n` +
      `• Allow you to start a fresh auction\n\n` +
      `Participants will remain in the league. This action cannot be undone.`
    )) {
      return;
    }

    try {
      const result = await axios.post(
        `${API}/leagues/${league?.id}/auction/reset?commissioner_id=${user?.id}`
      );
      console.log("Auction reset:", result.data);
      toast.success("Auction reset successfully! Redirecting to league setup...");
      
      // Redirect to Competition Detail Page to start fresh
      setTimeout(() => {
        navigate(`/league/${league?.id}`);
      }, 1500);
    } catch (e) {
      console.error("Error resetting auction:", e);
      const errorMsg = e.response?.data?.detail || "Failed to reset auction. Please try again.";
      toast.error(errorMsg);
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
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0F172A' }}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#00F0FF] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-white/60 text-lg">Loading auction...</div>
        </div>
      </div>
    );
  }

  // If auction doesn't exist (e.g., after reset), show message and navigation
  if (!auction && !loading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ background: '#0F172A' }}>
        <div className="rounded-2xl p-8 max-w-md text-center" style={{ background: '#151C2C', border: '1px solid rgba(255,255,255,0.1)' }}>
          <div className="text-6xl mb-4">🔄</div>
          <h2 className="text-2xl font-bold text-white mb-4">Auction Has Been Reset</h2>
          <p className="text-white/60 mb-6">
            The commissioner has reset this auction. Please wait on the competition page for the commissioner to restart the auction.
          </p>
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-3 rounded-xl font-bold text-black transition"
            style={{ background: '#00F0FF' }}
          >
            Return to Competition Page
          </button>
        </div>
      </div>
    );
  }

  const isCommissioner = league && user && league.commissionerId === user.id;

  // Prompt C: Soft guard - render message instead of redirecting (moved before waiting room check)
  if (!user) {
    return (
      <div className="min-h-screen py-8 flex items-center justify-center" style={{ background: '#0F172A' }}>
        <div 
          data-testid="auth-required" 
          className="rounded-2xl p-8 max-w-md text-center"
          style={{ background: '#151C2C', border: '1px solid rgba(255,255,255,0.1)' }}
        >
          <h2 className="text-2xl font-bold text-white mb-4">Authentication Required</h2>
          <p className="text-white/60 mb-6">Please sign in to access the auction room.</p>
          <button
            onClick={() => navigate("/")}
            className="px-6 py-3 rounded-xl text-black font-bold transition"
            style={{ background: '#00F0FF' }}
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  // Wait for league data before rendering waiting room (needed for isCommissioner check)
  if (!league && auction?.status === "waiting") {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0F172A' }}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#06B6D4] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-white/60 text-lg">Loading lobby...</div>
        </div>
      </div>
    );
  }

  // Prompt E: Show waiting room if auction status is "waiting"
  if (auction?.status === "waiting") {
    const handleBeginAuction = async () => {
      try {
        await axios.post(`${API}/auction/${auctionId}/begin`, null, {
          headers: {
            'X-User-ID': user.id
          }
        });
        console.log("✅ Auction started");
      } catch (error) {
        console.error("Error starting auction:", error);
        alert(error.response?.data?.detail || "Failed to start auction");
      }
    };

    const waitingRoomParticipants = participants.filter(p => 
      auction?.usersInWaitingRoom?.includes(p.userId)
    );
    const totalParticipants = participants.length;
    const joinedCount = waitingRoomParticipants.length;

    return (
      <div 
        className="min-h-screen relative overflow-hidden"
        style={{ 
          background: '#0F172A',
          fontFamily: 'Inter, sans-serif'
        }}
      >
        {/* Light Beam Effect */}
        <div 
          className="absolute pointer-events-none"
          style={{
            top: '-20%',
            left: '-10%',
            width: '150%',
            height: '150%',
            background: `
              radial-gradient(circle at 20% 20%, rgba(6, 182, 212, 0.15) 0%, transparent 40%),
              radial-gradient(circle at 80% 80%, rgba(6, 182, 212, 0.1) 0%, transparent 40%)
            `,
            zIndex: 0
          }}
        />

        <div className="relative z-10 flex flex-col min-h-screen pb-32 max-w-md mx-auto">
          {/* Header */}
          <header className="flex items-center p-4 justify-between">
            <button 
              onClick={() => navigate("/")}
              className="flex items-center justify-center w-10 h-10 rounded-xl"
              style={{ 
                background: 'rgba(255, 255, 255, 0.05)',
                backdropFilter: 'blur(12px)',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}
            >
              <span className="material-symbols-outlined text-white">chevron_left</span>
            </button>
            <h2 className="text-white/40 text-xs font-semibold uppercase tracking-widest leading-tight flex-1 text-center pr-10">
              No Gambling. All game.
            </h2>
          </header>

          {/* Headline Section */}
          <section className="flex flex-col items-center px-4 pt-4 pb-2">
            <h1 className="text-white tracking-tight text-3xl font-bold leading-tight text-center uppercase">
              AUCTION LOBBY
            </h1>
            {/* Participant Count Pill */}
            <div 
              className="flex items-center gap-2 mt-3 px-4 py-2 rounded-xl"
              style={{ 
                background: 'rgba(6, 182, 212, 0.1)',
                border: '1px solid rgba(6, 182, 212, 0.2)'
              }}
            >
              <span 
                className="material-symbols-outlined text-xl"
                style={{ color: '#06B6D4' }}
              >
                check_circle
              </span>
              <p 
                className="text-sm font-semibold leading-normal"
                style={{ color: '#06B6D4' }}
              >
                {joinedCount}/{totalParticipants} Managers Joined
              </p>
            </div>
          </section>

          {/* Main Glassmorphic Card */}
          <main 
            className="mx-4 mt-6 rounded-xl p-6 relative overflow-hidden"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
          >
            {/* Center Icon - Only for non-commissioner */}
            {!isCommissioner && (
              <div className="flex flex-col items-center justify-center mb-8">
                <div 
                  className="p-5 rounded-full"
                  style={{ 
                    background: 'rgba(6, 182, 212, 0.2)',
                    filter: 'drop-shadow(0 0 12px rgba(6, 182, 212, 0.6))'
                  }}
                >
                  <span 
                    className="material-symbols-outlined text-5xl"
                    style={{ color: '#06B6D4' }}
                  >
                    hourglass_empty
                  </span>
                </div>
                <p className="mt-4 text-white/60 text-sm font-medium">
                  Waiting for Commissioner to Start
                </p>
              </div>
            )}

            {/* Commissioner Header */}
            {isCommissioner && (
              <div className="flex flex-col items-center justify-center mb-6">
                <div 
                  className="p-4 rounded-full mb-3"
                  style={{ 
                    background: 'rgba(16, 185, 129, 0.2)',
                    filter: 'drop-shadow(0 0 12px rgba(16, 185, 129, 0.6))'
                  }}
                >
                  <span 
                    className="material-symbols-outlined text-4xl"
                    style={{ color: '#10B981' }}
                  >
                    shield_person
                  </span>
                </div>
                <p className="text-white/60 text-sm font-medium">
                  You are the Commissioner
                </p>
              </div>
            )}

            {/* Participant Grid */}
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-4">
              {waitingRoomParticipants.map((p) => {
                const isCurrentUser = user && p.userId === user.id;
                return (
                  <div key={p.userId} className="flex flex-col items-center gap-2">
                    <div className="relative">
                      {/* Avatar Circle */}
                      <div 
                        className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold"
                        style={{ 
                          background: isCurrentUser ? '#06B6D4' : 'rgba(6, 182, 212, 0.2)',
                          color: isCurrentUser ? '#0F172A' : '#06B6D4',
                          border: '2px solid rgba(6, 182, 212, 0.3)'
                        }}
                      >
                        {p.userName?.charAt(0).toUpperCase() || '?'}
                      </div>
                      {/* Status Dot */}
                      <div 
                        className="absolute bottom-0 right-0 w-3 h-3 rounded-full"
                        style={{ 
                          background: '#06B6D4',
                          boxShadow: '0 0 8px #06B6D4',
                          border: '2px solid #0F172A'
                        }}
                      />
                    </div>
                    <p className="text-xs font-medium text-white/90 text-center truncate w-full">
                      {p.userName?.split(' ')[0] || 'Unknown'}
                    </p>
                    <span 
                      className="text-[9px] font-bold uppercase tracking-tight"
                      style={{ color: '#06B6D4' }}
                    >
                      {isCurrentUser ? 'You' : 'Ready'}
                    </span>
                  </div>
                );
              })}

              {/* Empty State or "More" placeholder */}
              {waitingRoomParticipants.length === 0 && (
                <div className="col-span-full text-center py-8">
                  <span className="material-symbols-outlined text-4xl text-white/20 mb-2">group</span>
                  <p className="text-white/40 text-sm">
                    {isCommissioner 
                      ? "Waiting for participants to enter..."
                      : "Waiting for others to join..."}
                  </p>
                </div>
              )}

              {/* Show remaining count if some haven't joined */}
              {waitingRoomParticipants.length > 0 && joinedCount < totalParticipants && (
                <div className="flex flex-col items-center gap-2 opacity-50">
                  <div 
                    className="w-12 h-12 rounded-full flex items-center justify-center"
                    style={{ 
                      background: 'rgba(255, 255, 255, 0.1)',
                      border: '2px dashed rgba(255, 255, 255, 0.2)'
                    }}
                  >
                    <span className="material-symbols-outlined text-sm text-white/40">more_horiz</span>
                  </div>
                  <p className="text-xs font-medium text-white/40">
                    {totalParticipants - joinedCount} More...
                  </p>
                </div>
              )}
            </div>
          </main>
        </div>

        {/* Fixed Bottom Action Area */}
        <div 
          className="fixed bottom-0 left-0 right-0 p-4 pb-8 max-w-md mx-auto"
          style={{
            background: 'linear-gradient(to top, #0F172A 60%, transparent)',
            zIndex: 50
          }}
        >
          {isCommissioner ? (
            <div className="flex flex-col gap-3">
              <button
                onClick={handleBeginAuction}
                data-testid="begin-auction-button"
                className="w-full font-bold py-4 rounded-xl text-lg transition-all active:scale-[0.98] flex items-center justify-center gap-2"
                style={{ 
                  background: '#06B6D4',
                  color: '#0F172A',
                  boxShadow: '0 0 20px rgba(6, 182, 212, 0.4)',
                  position: 'relative',
                  zIndex: 51
                }}
              >
                <span className="tracking-wide uppercase">BEGIN AUCTION</span>
                <span className="material-symbols-outlined font-bold">play_arrow</span>
              </button>
              <p className="text-center text-white/40 text-xs">
                Start when all participants are ready
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              {/* Pulsing Waiting Indicator */}
              <div 
                className="w-full py-4 rounded-xl flex items-center justify-center gap-3"
                style={{ 
                  background: 'rgba(6, 182, 212, 0.1)',
                  border: '1px solid rgba(6, 182, 212, 0.2)',
                  animation: 'pulse 2s infinite'
                }}
              >
                <span 
                  className="material-symbols-outlined text-2xl animate-spin"
                  style={{ color: '#06B6D4', animationDuration: '3s' }}
                >
                  progress_activity
                </span>
                <span 
                  className="font-semibold tracking-wide"
                  style={{ color: '#06B6D4' }}
                >
                  Waiting for Host...
                </span>
              </div>
              <p className="text-white/40 text-xs">
                The auction will begin shortly
              </p>
            </div>
          )}
        </div>

        {/* Pulse Animation Keyframes */}
        <style>{`
          @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(6, 182, 212, 0.4); }
            50% { box-shadow: 0 0 0 8px rgba(6, 182, 212, 0); }
          }
        `}</style>
      </div>
    );
  }
  const currentClubBids = currentClub ? bids.filter((b) => b.clubId === currentClub.id) : [];
  
  // Debug logging for bid display
  if (currentClub) {
    console.log("Current club ID:", currentClub.id);
    console.log("All bids:", bids);
    console.log("Current club bids:", currentClubBids);
  }
  const highestBid = currentClubBids.length > 0 ? Math.max(...currentClubBids.map((b) => b.amount)) : 0;

  // Get clubs in auction queue for the horizontal scroll
  // IMPORTANT: Shuffle the display order so users can't determine auction sequence
  // The shuffle is seeded by auction ID so it's consistent during the session but random per auction
  const auctionQueue = auction?.clubQueue || [];
  
  // Seeded shuffle function - consistent within session but hides real order
  const seededShuffle = (arr) => {
    if (!arr.length || !auctionId) return arr;
    const seed = auctionId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    const shuffled = [...arr];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(((seed * (i + 1)) % 1000) / 1000 * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
  };
  
  const clubsInQueue = auctionQueue.map(id => clubs.find(c => c.id === id)).filter(Boolean);
  const queueClubs = seededShuffle(clubsInQueue).slice(0, 8);

  // Shuffled clubs list for "View All" modal - hides auction order
  const shuffledClubsForModal = seededShuffle(clubs);

  // Find current user's participant data
  const currentUserParticipant = participants.find((p) => p.userId === user?.id);
  const userRosterCount = currentUserParticipant?.clubsWon?.length || 0;
  const maxSlots = league?.clubSlots || 3;
  const userBudgetRemaining = currentUserParticipant?.budgetRemaining || 0;

  return (
    <div className="h-[100dvh] flex flex-col overflow-hidden" style={{ background: '#0F172A' }}>
      
      {/* ========== STICKY HEADER (Compact for small screens) ========== */}
      <header 
        className="flex-shrink-0 px-4 flex items-center justify-between"
        style={{ 
          height: '64px',
          minHeight: '64px',
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderBottom: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        {/* User Roster */}
        <div className="flex items-center gap-2">
          <span className="text-white/60 text-xs uppercase tracking-wider">User Roster</span>
          <span className="text-white font-bold">{userRosterCount}/{maxSlots}</span>
        </div>
        
        {/* Live Status */}
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
          <span className="text-white text-sm font-semibold uppercase tracking-wider">
            Live Auction Room {auction?.currentLot ? String(auction.currentLot).padStart(2, '0') : '00'}
          </span>
        </div>
        
        {/* Budget Left */}
        <div className="flex items-center gap-2 ml-4">
          <span className="text-white/60 text-xs uppercase tracking-wider">Budget</span>
          <span className="text-white font-bold">{formatCurrency(userBudgetRemaining)}</span>
        </div>
      </header>

      {/* ========== TEAMS/PLAYERS IN AUCTION SCROLL (80px) ========== */}
      <div 
        className="flex-shrink-0 h-20 px-4 flex items-center"
        style={{ background: 'rgba(15, 23, 42, 0.5)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}
      >
        <div className="flex-1 overflow-x-auto flex items-center gap-2" style={{ scrollbarWidth: 'none' }}>
          <span className="text-white/40 text-xs uppercase tracking-wider flex-shrink-0 mr-2">
            {sport?.key === 'cricket' ? 'Players' : 'Teams'}
          </span>
          {queueClubs.map((club, idx) => {
            const isCurrent = club.id === currentClub?.id;
            return (
              <div 
                key={club.id}
                className="flex-shrink-0 w-14 h-14 rounded-lg flex items-center justify-center transition-all"
                style={{ 
                  background: isCurrent ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255,255,255,0.05)',
                  border: isCurrent ? '2px solid #06B6D4' : '1px solid rgba(255,255,255,0.1)'
                }}
                title={club.name}
              >
                <TeamCrest 
                  clubId={club.id}
                  apiFootballId={club.apiFootballId}
                  name={sport?.key === 'cricket' 
                    ? (club.meta?.franchise || club.meta?.team || club.meta?.iplTeam || club.name)
                    : club.name
                  }
                  sportKey={sport?.key || 'football'} 
                  variant="small"
                  isActive={isCurrent}
                />
              </div>
            );
          })}
        </div>
        <button 
          onClick={() => setShowAllTeamsModal(true)}
          className="flex-shrink-0 ml-3 text-xs uppercase tracking-wider font-semibold"
          style={{ color: '#06B6D4' }}
          data-testid="view-all-teams-button"
        >
          View All
        </button>
      </div>

      {/* ========== VIEW ALL TEAMS/PLAYERS MODAL ========== */}
      {showAllTeamsModal && (
        <div 
          className="fixed inset-0 z-50 flex items-end justify-center"
          style={{ background: 'rgba(0,0,0,0.7)' }}
          onClick={() => setShowAllTeamsModal(false)}
        >
          <div 
            className="w-full max-w-md max-h-[70vh] rounded-t-3xl overflow-hidden"
            style={{ background: '#0F172A' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 px-4 py-4 flex items-center justify-between" style={{ background: '#0F172A', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <h3 className="text-lg font-bold text-white">
                {sport?.key === 'cricket' ? 'Players' : 'Teams'} in Auction
              </h3>
              <button 
                onClick={() => setShowAllTeamsModal(false)}
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ background: 'rgba(255,255,255,0.1)' }}
              >
                <span className="text-white text-xl">×</span>
              </button>
            </div>
            
            {/* Teams List - using shuffled order to hide auction sequence */}
            <div className="overflow-y-auto p-4 space-y-2" style={{ maxHeight: 'calc(70vh - 60px)' }}>
              {shuffledClubsForModal.map((club, idx) => {
                const isCurrent = club.id === currentClub?.id;
                const isSold = club.winner && club.winner !== 'unsold';
                const isUnsold = club.winner === 'unsold';
                const inQueue = auction?.clubQueue?.includes(club.id);
                
                return (
                  <div 
                    key={club.id}
                    className="flex items-center gap-3 p-3 rounded-xl"
                    style={{ 
                      background: isCurrent ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255,255,255,0.05)',
                      border: isCurrent ? '2px solid #06B6D4' : '1px solid rgba(255,255,255,0.1)'
                    }}
                  >
                    <TeamCrest 
                      clubId={club.id}
                      apiFootballId={club.apiFootballId}
                      name={sport?.key === 'cricket' 
                        ? (club.meta?.franchise || club.meta?.team || club.meta?.iplTeam || club.name)
                        : club.name
                      }
                      sportKey={sport?.key || 'football'} 
                      variant="thumbnail"
                      isActive={isCurrent}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-semibold truncate">{club.name}</p>
                      {/* For cricket, show franchise name below player name */}
                      {sport?.key === 'cricket' && (club.meta?.franchise || club.meta?.team) && (
                        <p className="text-xs text-cyan-400 truncate">{club.meta?.franchise || club.meta?.team}</p>
                      )}
                      <p className="text-xs text-white/50">
                        {isCurrent ? 'Currently on the block' : 
                         isSold ? `Won by ${club.winner} for ${formatCurrency(club.winningBid)}` : 
                         isUnsold ? 'Went unsold' :
                         inQueue ? 'In auction' : 
                         'Not in queue'}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      {isCurrent && (
                        <span className="px-2 py-1 rounded-full text-[10px] font-bold uppercase" style={{ background: '#06B6D4', color: '#0F172A' }}>
                          Live
                        </span>
                      )}
                      {isSold && (
                        <span className="px-2 py-1 rounded-full text-[10px] font-bold uppercase" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981' }}>
                          Sold
                        </span>
                      )}
                      {isUnsold && (
                        <span className="px-2 py-1 rounded-full text-[10px] font-bold uppercase" style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#EF4444' }}>
                          Unsold
                        </span>
                      )}
                      {!isCurrent && !isSold && !isUnsold && inQueue && (
                        <span className="px-2 py-1 rounded-full text-[10px] font-bold uppercase" style={{ background: 'rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.6)' }}>
                          Pending
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ========== ALL BUDGETS MODAL ========== */}
      {showBudgetsModal && (
        <div 
          className="fixed inset-0 z-50 flex items-end justify-center"
          style={{ background: 'rgba(0,0,0,0.7)' }}
          onClick={() => setShowBudgetsModal(false)}
        >
          <div 
            className="w-full max-w-md max-h-[70vh] rounded-t-3xl overflow-hidden"
            style={{ background: '#0F172A' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 px-4 py-4 flex items-center justify-between" style={{ background: '#0F172A', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <h3 className="text-lg font-bold text-white">
                All Budgets
              </h3>
              <button 
                onClick={() => setShowBudgetsModal(false)}
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ background: 'rgba(255,255,255,0.1)' }}
              >
                <span className="text-white text-xl">×</span>
              </button>
            </div>
            
            {/* Participants List */}
            <div className="overflow-y-auto p-4 space-y-2" style={{ maxHeight: 'calc(70vh - 60px)' }}>
              {participants
                .sort((a, b) => (b.budgetRemaining || 0) - (a.budgetRemaining || 0))
                .map((p) => {
                  const isCurrentUser = user && p.userId === user.id;
                  const teamsWon = p.clubsWon?.length || 0;
                  
                  return (
                    <div 
                      key={p.id || p.odbc}
                      className="flex items-center gap-3 p-3 rounded-xl"
                      style={{ 
                        background: isCurrentUser ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255,255,255,0.05)',
                        border: isCurrentUser ? '2px solid #06B6D4' : '1px solid rgba(255,255,255,0.1)'
                      }}
                    >
                      {/* Avatar */}
                      <div 
                        className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                        style={{ 
                          background: isCurrentUser ? '#06B6D4' : 'rgba(255,255,255,0.1)',
                          color: isCurrentUser ? '#0F172A' : 'white'
                        }}
                      >
                        {p.userName?.substring(0, 2).toUpperCase() || '??'}
                      </div>
                      
                      {/* Name & Teams Won */}
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-semibold truncate">
                          {p.userName || 'Unknown User'}
                          {isCurrentUser && <span className="text-cyan-400 text-xs ml-2">(You)</span>}
                        </p>
                        <p className="text-xs text-white/50">
                          {teamsWon} {teamsWon === 1 ? 'team' : 'teams'} won
                        </p>
                      </div>
                      
                      {/* Budget */}
                      <div className="text-right flex-shrink-0">
                        <p className="text-cyan-400 font-bold">
                          {formatCurrency(p.budgetRemaining || 0)}
                        </p>
                        <p className="text-[10px] text-white/40 uppercase">remaining</p>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        </div>
      )}

      {/* ========== HERO SECTION (Flexible ~40%) ========== */}
      <div className="flex-1 flex flex-col items-center justify-center relative px-4 overflow-hidden">
        
        {/* Team Crest Watermark Background */}
        {/* For cricket, use franchise name for logo lookup; for football, use team name */}
        {currentClub && (
          <TeamCrest 
            clubId={currentClub.id}
            apiFootballId={currentClub.apiFootballId}
            name={sport?.key === 'cricket' 
              ? (currentClub.meta?.franchise || currentClub.meta?.team || currentClub.meta?.iplTeam || currentClub.name)
              : currentClub.name
            }
            sportKey={sport?.key || 'football'}
            variant="watermark"
          />
        )}

        {/* Countdown Overlay Between Lots */}
        {countdown !== null && countdown > 0 && (
          <div className="absolute inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(11, 16, 27, 0.95)' }}>
            <div className="text-center">
              <div className="text-9xl font-black" style={{ color: '#06B6D4', fontFamily: 'Roboto, sans-serif' }}>
                {countdown}
              </div>
              <div className="text-xl text-white/60 mt-4">
                Next {sport?.key === 'cricket' ? 'player' : 'team'} loading...
              </div>
            </div>
          </div>
        )}

        {currentClub && auction?.status !== "completed" ? (
          <div className="relative z-10 text-center w-full max-w-md">
            {/* Timer - Large Orange (responsive size) */}
            <div 
              className="mb-4"
              style={{ fontFamily: 'Roboto, sans-serif' }}
            >
              <div 
                className="text-5xl sm:text-6xl md:text-7xl font-black tracking-tight"
                style={{ 
                  color: auction?.status === 'paused' ? '#FF8A00' : (remainingMs ?? 0) < 10000 ? '#EF4444' : '#EF4444',
                  textShadow: '0 0 40px rgba(239, 68, 68, 0.4)'
                }}
                data-testid="auction-timer"
              >
                {(() => {
                  const s = Math.ceil((remainingMs ?? 0) / 1000);
                  const mm = String(Math.floor(s / 60)).padStart(2, "0");
                  const ss = String(s % 60).padStart(2, "0");
                  return `${mm}:${ss}`;
                })()}
              </div>
              {auction?.status === 'paused' && (
                <div className="text-sm uppercase tracking-wider mt-1" style={{ color: '#FF8A00' }}>⏸️ Paused</div>
              )}
            </div>

            {/* Team Name */}
            <h2 
              className="text-2xl sm:text-3xl font-extrabold text-white mb-1"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              {currentClub.name}
            </h2>
            
            {/* Next Match Info */}
            {nextFixture && (
              <p className="text-sm mb-6" style={{ color: '#94A3B8', fontFamily: 'Inter, sans-serif' }}>
                Next Match: {nextFixture.opponent} ({nextFixture.isHome ? 'H' : 'A'})
              </p>
            )}
            {!nextFixture && currentClub.meta?.franchise && (
              <p className="text-sm mb-6" style={{ color: '#94A3B8' }}>
                {currentClub.meta.franchise} • {currentClub.meta.role || 'Player'}
              </p>
            )}
            {!nextFixture && !currentClub.meta?.franchise && (
              <p className="text-sm mb-6" style={{ color: '#94A3B8' }}>
                {currentClub.country || 'International'}
              </p>
            )}

            {/* Current Highest Bid */}
            <div className="mb-2">
              <div className="text-xs uppercase tracking-widest mb-1 font-bold" style={{ color: '#06B6D4' }}>
                Current Highest Bid
              </div>
              <div 
                className="text-4xl sm:text-5xl font-extrabold animate-bid-pop"
                style={{ 
                  color: '#06B6D4', 
                  fontFamily: 'Inter, sans-serif',
                  animation: currentBid > 0 ? 'bidPop 300ms ease-out' : 'none'
                }}
                key={currentBid} /* Key change triggers animation */
                data-testid="current-bid-display"
              >
                {currentBid > 0 ? formatCurrency(currentBid) : '£0'}
              </div>
              {currentBidder && (
                <div className="text-sm mt-1" style={{ color: '#06B6D4' }}>
                  {currentBidder.displayName} leading
                </div>
              )}
              {!currentBidder && currentBid === 0 && (
                <div className="text-sm mt-1 text-white/40">
                  No bids yet - be the first!
                </div>
              )}
            </div>
          </div>
        ) : auction?.status === "completed" ? (
          <div className="text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full flex items-center justify-center" style={{ background: 'rgba(6, 182, 212, 0.2)' }}>
              <span className="material-symbols-outlined text-4xl" style={{ color: '#06B6D4' }}>check_circle</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Auction Complete!</h2>
            <button
              onClick={() => navigate('/app/my-competitions')}
              className="px-8 py-3 rounded-xl font-bold"
              style={{ background: '#06B6D4', color: '#0F172A' }}
            >
              Go to My Competitions →
            </button>
          </div>
        ) : (
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center" style={{ background: 'rgba(255, 255, 255, 0.1)' }}>
              <span className="material-symbols-outlined text-3xl text-white/60">hourglass_empty</span>
            </div>
            <h2 className="text-2xl font-bold text-white">Preparing next lot...</h2>
          </div>
        )}
      </div>

      {/* ========== CONTROL PANEL (Sticky Bottom - Compact for small screens) ========== */}
      <div 
        className="flex-shrink-0 px-3 py-3"
        style={{ 
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          borderTop: '1px solid rgba(255,255,255,0.1)'
        }}
      >
        {/* Active Managers Row - Compact & Tappable */}
        <div className="flex items-center justify-between mb-3">
          <button 
            onClick={() => setShowBudgetsModal(true)}
            className="flex items-center gap-2 overflow-x-auto flex-1 mr-2"
            style={{ scrollbarWidth: 'none' }}
          >
            {participants.slice(0, 6).map((p) => {
              const isLeading = currentBidder && p.userId === currentBidder.id;
              const isCurrentUser = user && p.userId === user.id;
              return (
                <div key={p.id} className="flex flex-col items-center flex-shrink-0">
                  <div 
                    className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold"
                    style={{ 
                      background: isCurrentUser ? '#06B6D4' : 'rgba(255,255,255,0.1)',
                      color: isCurrentUser ? '#0F172A' : 'white',
                      border: isLeading ? '2px solid #06B6D4' : '2px solid transparent',
                      boxShadow: isLeading ? '0 0 12px rgba(6, 182, 212, 0.5)' : 'none'
                    }}
                  >
                    {p.userName?.substring(0, 2).toUpperCase() || '??'}
                  </div>
                  <span className="text-[9px] text-white/60 mt-0.5 truncate w-10 text-center">
                    {p.userName?.split(' ')[0] || 'User'}
                  </span>
                </div>
              );
            })}
            {participants.length > 6 && (
              <div className="flex flex-col items-center flex-shrink-0">
                <div 
                  className="w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold"
                  style={{ background: 'rgba(255,255,255,0.1)', color: 'white' }}
                >
                  +{participants.length - 6}
                </div>
              </div>
            )}
          </button>
          <button 
            onClick={() => setShowBudgetsModal(true)}
            className="flex items-center gap-1 flex-shrink-0 px-2 py-1 rounded-lg"
            style={{ background: 'rgba(255,255,255,0.05)' }}
          >
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="text-xs text-white/60">{participants.length}</span>
            <span className="material-symbols-outlined text-white/40 text-sm">expand_more</span>
          </button>
        </div>

        {/* Quick Bid Buttons - Two rows of 3 equal buttons */}
        <div className="grid grid-cols-3 gap-1.5 mb-1.5">
          {[1, 5, 10].map((amount) => (
            <button
              key={amount}
              onClick={() => {
                // Add increment to CURRENT BID (not to input value)
                // This makes it easy to outbid: +£1m on £32m = £33m
                const currentBidInMillions = (currentBid || 0) / 1000000;
                const newBid = currentBidInMillions + amount;
                setBidAmount(newBid.toString());
                // Haptic feedback
                if (navigator.vibrate) navigator.vibrate(50);
              }}
              disabled={!ready || userRosterCount >= maxSlots}
              className="h-10 rounded-xl font-bold text-sm transition-all active:scale-95 disabled:opacity-40"
              style={{ 
                background: 'rgba(6, 182, 212, 0.1)', 
                color: '#06B6D4', 
                border: '1px solid #06B6D4' 
              }}
            >
              +£{amount}m
            </button>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-1.5 mb-2">
          {[20, 50].map((amount) => (
            <button
              key={amount}
              onClick={() => {
                const currentBidInMillions = (currentBid || 0) / 1000000;
                const newBid = currentBidInMillions + amount;
                setBidAmount(newBid.toString());
                if (navigator.vibrate) navigator.vibrate(50);
              }}
              disabled={!ready || userRosterCount >= maxSlots}
              className="h-10 rounded-xl font-bold text-sm transition-all active:scale-95 disabled:opacity-40"
              style={{ 
                background: 'rgba(6, 182, 212, 0.1)', 
                color: '#06B6D4', 
                border: '1px solid #06B6D4' 
              }}
            >
              +£{amount}m
            </button>
          ))}
          {/* Pass button in same row */}
          <button
            onClick={() => toast("Pass This Round - Coming soon!", { duration: 2000 })}
            disabled={userRosterCount >= maxSlots}
            className="h-10 rounded-xl font-bold text-sm transition-all active:scale-95 disabled:opacity-40"
            style={{ 
              background: 'rgba(239, 68, 68, 0.1)', 
              color: '#EF4444', 
              border: '1px solid #EF4444' 
            }}
          >
            Pass
          </button>
        </div>

        {/* Place Bid Button */}
        {bidAmount && (
          <button
            onClick={() => {
              placeBid();
              if (navigator.vibrate) navigator.vibrate(50);
            }}
            disabled={!ready || isSubmittingBid || userRosterCount >= maxSlots}
            className="w-full h-12 rounded-xl font-bold text-base mb-2 transition-all active:scale-95 disabled:opacity-40"
            style={{ 
              background: (!ready || isSubmittingBid || userRosterCount >= maxSlots) ? 'rgba(255,255,255,0.1)' : '#06B6D4',
              color: (!ready || isSubmittingBid || userRosterCount >= maxSlots) ? 'rgba(255,255,255,0.4)' : '#0F172A'
            }}
            data-testid="place-bid-button"
          >
            {isSubmittingBid ? 'Placing...' : `Place Bid: £${bidAmount}m`}
          </button>
        )}

        {/* Commissioner Controls - Compact */}
        {isCommissioner && (
          <div className="flex gap-2 mt-3 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            {auction?.status === "active" && (
              <button onClick={pauseAuction} className="flex-1 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1" style={{ background: 'rgba(255, 138, 0, 0.2)', color: '#FF8A00' }}>
                <span className="material-symbols-outlined text-sm">pause</span> Pause
              </button>
            )}
            {auction?.status === "paused" && (
              <button onClick={resumeAuction} className="flex-1 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1" style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981' }}>
                <span className="material-symbols-outlined text-sm">play_arrow</span> Resume
              </button>
            )}
            <button onClick={completeLot} className="flex-1 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1" style={{ background: 'rgba(255, 77, 77, 0.2)', color: '#FF4D4D' }}>
              <span className="material-symbols-outlined text-sm">skip_next</span> Skip
            </button>
            <button onClick={deleteAuction} className="flex-1 py-2 rounded-lg text-xs font-medium flex items-center justify-center gap-1" style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#EF4444' }}>
              <span className="material-symbols-outlined text-sm">delete</span> End
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(AuctionRoom);