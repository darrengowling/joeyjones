import { useState, useEffect, useRef, useMemo, useCallback, memo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { useAuctionClock } from "../hooks/useAuctionClock";
import { useSocketRoom } from "../hooks/useSocketRoom";
import { formatCurrency, parseCurrencyInput, isValidCurrencyInput } from "../utils/currency";
import { debounceSocketEvent } from "../utils/performance";
import { debugLogger } from "../utils/debugLogger";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Memoized sub-components for better performance (Production Hardening Day 11)
const BidHistoryItem = memo(({ bid, isWinning }) => (
  <div className={`p-3 border-l-4 ${isWinning ? 'border-green-500 bg-green-50' : 'border-gray-300 bg-white'} rounded`}>
    <div className="flex justify-between items-center">
      <span className="font-medium text-gray-900">{bid.userName || 'Anonymous'}</span>
      <span className="font-bold text-green-600">{formatCurrency(bid.amount)}</span>
    </div>
    <span className="text-xs text-gray-500">{new Date(bid.createdAt).toLocaleTimeString()}</span>
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
    if (!currentClub) {
      // No active lot, clear the input
      setBidAmount("");
      return;
    }

    if (currentBid && currentBid > 0) {
      // Show current bid amount in millions (e.g., "5" for £5m)
      setBidAmount((currentBid / 1000000).toString());
    } else {
      // No bids yet, keep input empty
      setBidAmount("");
    }
  }, [currentClub, currentBid]);


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
        
        // Reset input to current bid if user tried to outbid themselves
        if (errorMsg.includes("already the highest bidder") && currentBid) {
          setBidAmount((currentBid / 1000000).toString());
        }
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
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading auction...</div>
      </div>
    );
  }

  // If auction doesn't exist (e.g., after reset), show message and navigation
  if (!auction && !loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md text-center">
          <div className="text-6xl mb-4">🔄</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Auction Has Been Reset</h2>
          <p className="text-gray-600 mb-6">
            The commissioner has reset this auction. Please wait on the competition page for the commissioner to restart the auction.
          </p>
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Return to Competition Page
          </button>
        </div>
      </div>
    );
  }

  const isCommissioner = league && user && league.commissionerId === user.id;

  // Prompt E: Show waiting room if auction status is "waiting"
  if (auction?.status === "waiting") {
    const handleBeginAuction = async () => {
      try {
        await axios.post(`${API}/auction/${auctionId}/begin`, null, {
          headers: {
            'X-User-ID': user.id
          }
        });
        console.log("✅ Auction begin request sent");
        // State will update via lot_started event
      } catch (error) {
        console.error("Error starting auction:", error);
        alert(error.response?.data?.detail || "Failed to start auction");
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 py-8">
        <div className="container mx-auto px-4">
          <div className="max-w-2xl mx-auto">
            <button
              onClick={() => navigate("/")}
              className="text-white hover:underline mb-4"
            >
              ← Back to Home
            </button>
            
            <div className="bg-white rounded-lg shadow-xl p-8">
              <div className="text-center mb-6">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  ⏳ Auction Waiting Room
                </h1>
                <p className="text-gray-600">
                  {isCommissioner 
                    ? "Waiting for users to enter waiting room"
                    : "Waiting for other participants and commissioner to start"}
                </p>
              </div>

              {/* Participants List */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-bold text-gray-900 mb-3">
                  Participants Ready ({auction?.usersInWaitingRoom?.length || 0})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {participants
                    .filter(p => auction?.usersInWaitingRoom?.includes(p.userId))
                    .map(p => (
                      <div
                        key={p.userId}
                        className="flex items-center gap-2 bg-white px-3 py-2 rounded-full border border-gray-300"
                      >
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
                          {p.userName?.charAt(0).toUpperCase() || '?'}
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {p.userName}
                        </span>
                        {p.userId === user.id && (
                          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                            You
                          </span>
                        )}
                      </div>
                    ))}
                  {(!auction?.usersInWaitingRoom || auction.usersInWaitingRoom.length === 0) && (
                    <div className="text-center text-gray-500 py-4 w-full">
                      {isCommissioner 
                        ? "Waiting for participants to click 'Enter Auction'..."
                        : "Waiting for other participants..."}
                    </div>
                  )}
                </div>
              </div>

              {/* Commissioner or Participant View */}
              <div className="text-center">
                {isCommissioner ? (
                  <div>
                    <button
                      onClick={handleBeginAuction}
                      className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg text-lg shadow-lg transition-colors"
                    >
                      🚀 Begin Auction
                    </button>
                    <p className="text-sm text-gray-500 mt-3">
                      Start when all participants are ready
                    </p>
                  </div>
                ) : (
                  <div>
                    <div className="inline-block animate-pulse">
                      <div className="bg-gray-200 rounded-full p-4 mb-3">
                        <svg className="w-12 h-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                    </div>
                    <p className="text-lg font-medium text-gray-700">
                      Waiting for commissioner to start...
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      The auction will begin shortly
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
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

  // Prompt C: Soft guard - render message instead of redirecting
  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 py-8 flex items-center justify-center">
        <div 
          data-testid="auth-required" 
          className="bg-white rounded-lg shadow-xl p-8 max-w-md text-center"
        >
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Authentication Required</h2>
          <p className="text-gray-600 mb-6">Please sign in to access the auction room.</p>
          <button
            onClick={() => navigate("/")}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 overflow-hidden">
      {/* Header Section - Fixed */}
      <div className="flex-shrink-0 px-2 sm:px-4 pt-4 pb-2">
        <div className="max-w-6xl mx-auto w-full">
          {/* Breadcrumb Navigation */}
          <div className="flex items-center gap-2 text-sm text-white mb-4">
            <button onClick={() => navigate("/")} className="hover:underline">Home</button>
            <span>›</span>
            <button onClick={() => navigate("/app/my-competitions")} className="hover:underline">My Competitions</button>
            <span>›</span>
            {league && (
              <>
                <button onClick={() => navigate(`/league/${league.id}`)} className="hover:underline">{league.name}</button>
                <span>›</span>
              </>
            )}
            <span className="font-semibold">Auction Room</span>
          </div>

          {/* Prompt G: Top strip with league info and progress */}
          {league && auction && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 mb-4">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <div className="whitespace-nowrap">
                    <span className="text-xs font-medium text-blue-800">League:</span>
                    <span className="text-xs text-blue-600 ml-1">{league.name}</span>
                  </div>
                  <div className="whitespace-nowrap">
                    <span className="text-xs font-medium text-blue-800">Progress:</span>
                    <span className="text-xs text-blue-600 ml-1">
                      Lot {auction.currentLot || 0} / {auction.clubQueue?.length || 0}
                    </span>
                  </div>
                  <div className="w-full sm:w-auto">
                    <span className="text-xs font-medium text-blue-800">Managers with slots left:</span>
                    <span className="text-xs text-blue-600 ml-1 break-words">
                      {participants.filter(p => (p.clubsWon?.length || 0) < (league.clubSlots || 3)).map(p => {
                        const slotsLeft = (league.clubSlots || 3) - (p.clubsWon?.length || 0);
                        return `${p.userName}=${slotsLeft}`;
                      }).join(', ') || 'None'}
                    </span>
                  </div>
                </div>
                {auction.status === "completed" && (
                  <div className="bg-green-100 text-green-800 px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap">
                    ✅ Auction Complete
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Content Section - Scrollable */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-2 sm:px-4 pb-4">
        <div className="max-w-6xl mx-auto w-full">
          {/* Auction Header */}
          <div className="bg-white rounded-lg shadow-lg p-3 sm:p-4 mb-4">
            <div className="flex flex-col gap-3">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2 max-w-full">
                    <h1 className="text-lg sm:text-2xl font-bold text-gray-900 truncate min-w-0 flex-shrink">
                      {league ? league.name : "Strategic Competition Arena"}
                    </h1>
                    {league?.sportKey && (
                      <span className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded whitespace-nowrap flex-shrink-0 capitalize">
                        {league.sportKey}
                      </span>
                    )}
                    {auction?.status === "paused" && (
                      <span className="px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded whitespace-nowrap flex-shrink-0">
                        ⏸️ PAUSED
                      </span>
                    )}
                  </div>
                  <p className="text-xs sm:text-sm text-gray-600 mt-1">
                    Lot #{auction?.currentLot || 0}
                  </p>
                </div>
              </div>
              
              {/* Commissioner Controls */}
              {isCommissioner && (
                <div className="flex flex-wrap gap-2">
                  {auction?.status === "active" && (
                    <button
                      onClick={pauseAuction}
                      className="btn btn-secondary px-3 py-1.5 sm:px-4 sm:py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 text-sm"
                      title="Pause Auction"
                    >
                      ⏸️ Pause
                    </button>
                  )}
                  
                  {auction?.status === "paused" && (
                    <button
                      onClick={resumeAuction}
                      className="btn btn-secondary px-3 py-1.5 sm:px-4 sm:py-2 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
                      title="Resume Auction"
                    >
                      ▶️ Resume
                    </button>
                  )}
                  
                  {(auction?.status === "paused" || auction?.status === "completed") && (
                    <button
                      onClick={resetAuction}
                      className="btn btn-warning px-3 py-1.5 sm:px-4 sm:py-2 bg-orange-500 text-white rounded hover:bg-orange-600 text-sm"
                      title="Reset Auction"
                    >
                      🔄 Reset
                    </button>
                  )}
                  
                  <button
                    onClick={completeLot}
                    className="btn btn-danger px-3 py-1.5 sm:px-4 sm:py-2 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                    title="Complete Current Lot"
                  >
                    Complete Lot
                  </button>
                  
                  <button
                    onClick={deleteAuction}
                    className="btn btn-danger px-3 py-1.5 sm:px-4 sm:py-2 bg-red-700 text-white rounded hover:bg-red-800 text-sm"
                    title="Delete Entire Auction"
                  >
                    🗑️ Delete Auction
                  </button>
                </div>
              )}
              
              {/* Debug Tools - Available for all users */}
              {auction && (
                <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                  <button
                    onClick={async () => {
                      try {
                        debugLogger.log('report_submitted', {
                          auctionStatus: auction?.status,
                          totalBids: bids.length
                        });
                        toast("Submitting report...", { duration: 2000 });
                        const result = await debugLogger.submitReport();
                        toast.success(`Report submitted! Reference: ${result.referenceId}`, { duration: 8000 });
                      } catch (e) {
                        console.error("Report submission error:", e);
                        toast.error("Failed to submit report. Please try again.");
                      }
                    }}
                    className="px-3 py-1.5 sm:px-4 sm:py-2 bg-orange-500 text-white rounded hover:bg-orange-600 text-sm"
                    title="Report an issue - submits debug info to support team"
                  >
                    🚨 Report Issue
                  </button>
                  <span className="text-xs text-gray-600">
                    Stats: {debugLogger.getStats().totalAttempts} attempts, {debugLogger.getStats().totalSuccesses} successes
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Participant Budgets - Horizontal Scroll */}
          <div className="bg-white rounded-lg shadow-lg p-3 mb-4">
            <h2 className="text-lg font-bold mb-2 text-gray-900">Manager Budgets</h2>
            <div className="flex gap-3 overflow-x-auto pb-2" style={{scrollbarWidth: 'thin'}}>
              {participants.map((p) => {
                const isCurrentUser = user && p.userId === user.id;
                return (
                  <div
                    key={p.id}
                    className={`flex-shrink-0 w-32 sm:w-40 py-2 px-2.5 sm:p-3 rounded-lg border-2 ${
                      isCurrentUser
                        ? "bg-blue-50 border-blue-500"
                        : "bg-gray-50 border-gray-200"
                    }`}
                  >
                    <div className="font-semibold text-gray-900 text-[10px] sm:text-[var(--t-xs)] mb-1 truncate break-any line-clamp-2">
                      {p.userName} {isCurrentUser && "(You)"}
                    </div>
                    <div className="space-y-0.5 sm:space-y-1">
                      <div className="text-sm sm:text-lg font-bold text-green-600 truncate">
                        {formatCurrency(p.budgetRemaining)}
                      </div>
                      <div className="text-[10px] sm:text-xs text-gray-500 truncate">
                        Spent: {formatCurrency(p.totalSpent)}
                      </div>
                      <div className="text-[10px] sm:text-xs text-gray-500 whitespace-nowrap">
                        🏆 {uiHints.assetPlural}: {p.clubsWon.length}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Current Lot */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-4 app-card">
              {currentClub ? (
                <div>
                  <h2 className="h2 text-2xl font-bold mb-4 text-gray-900">🔥 Current {uiHints.assetLabel} Ownership</h2>
                  
                  {/* Countdown Overlay Between Lots */}
                  {countdown !== null && countdown > 0 && (
                    <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex items-center justify-center">
                      <div className="bg-white rounded-lg p-12 text-center shadow-2xl">
                        <div className="text-7xl font-bold text-blue-600 mb-4">
                          {countdown}
                        </div>
                        <div className="text-2xl text-gray-700">
                          Next team in {countdown}...
                        </div>
                        <div className="text-sm text-gray-500 mt-2">
                          Get ready to bid
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Compact Timer + Team + Current Bid */}
                  <div className="bg-black text-white p-4 rounded-lg mb-3 shadow-lg">
                    <div className="flex items-center justify-between gap-4 mb-3">
                      {/* Team Name */}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-2xl font-bold text-white truncate">{currentClub.name}</h3>
                        {/* Next Fixture - Inline */}
                        {nextFixture && (
                          <div className="text-xs text-gray-300 mt-1">
                            Next: {nextFixture.opponent} ({nextFixture.isHome ? 'H' : 'A'})
                          </div>
                        )}
                      </div>
                      
                      {/* Timer */}
                      <div className="text-center">
                        <div className="text-4xl font-bold">
                          {(() => {
                            const s = Math.ceil((remainingMs ?? 0) / 1000);
                            const mm = String(Math.floor(s / 60)).padStart(2, "0");
                            const ss = String(s % 60).padStart(2, "0");
                            const warn = (remainingMs ?? 0) < 10000;
                            const isPaused = auction?.status === 'paused';
                            return (
                              <span 
                                data-testid="auction-timer" 
                                className={
                                  isPaused 
                                    ? 'text-yellow-400' 
                                    : warn 
                                      ? 'text-red-400' 
                                      : 'text-white'
                                }
                              >
                                {mm}:{ss}
                                {isPaused && ' ⏸️'}
                              </span>
                            );
                          })()}
                        </div>
                        <div className="text-xs text-gray-300">
                          {auction?.status === 'paused' ? 'PAUSED' : 'Time Left'}
                        </div>
                      </div>
                    </div>
                    
                    {/* Current Bid or No Bids */}
                    <div className="border-t border-gray-600 pt-3">
                      {currentBid > 0 && currentBidder ? (
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                          <div className="text-center sm:text-left">
                            <div className="text-xs text-gray-300">Current Bid</div>
                            <div className="text-3xl sm:text-2xl font-bold text-green-400">{formatCurrency(currentBid)}</div>
                          </div>
                          <div className="flex items-center gap-2 justify-center sm:justify-end">
                            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                              {currentBidder.displayName.charAt(0).toUpperCase()}
                            </div>
                            <div className="text-sm text-gray-200">{currentBidder.displayName}</div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center">
                          <div className="text-sm text-gray-300">💰 No bids yet - Be the first!</div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Team Metadata */}
                  <div className="bg-gray-50 p-3 rounded-lg mb-3">
                    {/* Football: Show country and UEFA ID */}
                    {sport?.key === "football" && (
                      <div className="flex items-center gap-3 text-sm">
                        <span className="text-gray-700">{currentClub.country}</span>
                        {currentClub.uefaId && (
                          <span className="text-gray-500">UEFA ID: {currentClub.uefaId}</span>
                        )}
                      </div>
                    )}
                    
                    {/* Cricket: Show nationality and role */}
                    {sport?.key === "cricket" && currentClub.meta && (
                      <div className="flex flex-wrap items-center gap-2 text-sm">
                        {currentClub.meta.nationality && (
                          <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-semibold">
                            {currentClub.meta.nationality}
                          </span>
                        )}
                        {currentClub.meta.role && (
                          <span className="text-gray-700">Role: {currentClub.meta.role}</span>
                        )}
                        {currentClub.meta.bowling && (
                          <span className="text-gray-600">Bowling: {currentClub.meta.bowling}</span>
                        )}
                      </div>
                    )}
                    
                    {/* Fallback for other sports */}
                    {sport?.key !== "football" && sport?.key !== "cricket" && currentClub.country && (
                      <div className="text-sm text-gray-700">{currentClub.country}</div>
                    )}
                  </div>

                  {/* Bid Input with Quick Buttons */}
                  <div>
                    {/* Quick Bid Buttons */}
                    <div className="flex gap-2 mb-2 overflow-x-auto pb-2">
                      {[1, 2, 5, 10, 20, 50].map((amount) => (
                        <button
                          key={amount}
                          onClick={() => {
                            // Add to the current input value (in millions), not the auction's currentBid
                            const currentInputValue = parseFloat(bidAmount) || 0;
                            const newBid = currentInputValue + amount;
                            setBidAmount(newBid.toString());
                          }}
                          disabled={!ready}
                          className="flex-shrink-0 px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg text-sm font-medium border border-gray-300 disabled:opacity-50"
                        >
                          +{amount}m
                        </button>
                      ))}
                    </div>
                    
                    <div className="flex flex-col sm:flex-row gap-2 mb-2">
                      <input
                        type="text"
                        readOnly
                        placeholder="Use buttons above"
                        className="w-full sm:flex-1 px-3 py-3 border rounded-lg bg-gray-50 text-[16px] cursor-default"
                        value={bidAmount ? `£${bidAmount}m` : ""}
                        disabled={!ready}
                        data-testid="bid-amount-input"
                      />
                      <button
                        onClick={placeBid}
                        disabled={!ready || isSubmittingBid || participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3)}
                        className={`w-full sm:w-auto px-6 py-3 sm:py-2 rounded-lg font-semibold text-base ${
                          !ready || isSubmittingBid || participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3) 
                            ? 'bg-gray-400 cursor-not-allowed' 
                            : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                        data-testid="place-bid-button"
                        title={
                          !ready 
                            ? "Loading auction state..." 
                            : isSubmittingBid
                              ? "Placing bid..."
                            : participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3) 
                              ? "Roster full" 
                              : ""
                        }
                      >
                        {!ready 
                          ? "Loading..." 
                          : isSubmittingBid
                            ? "Placing..."
                          : participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3) 
                            ? "Roster Full" 
                            : "Place Bid"
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
            <div className="app-card bg-white rounded-lg shadow-lg p-4">
              <h3 className="h2 text-lg font-bold mb-3 text-gray-900">🏆 {uiHints.assetPlural} Available</h3>
              
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
                          {/* Football: Show country */}
                          {sport?.key === "football" && club.country && (
                            <div className="text-xs opacity-75">{club.country}</div>
                          )}
                          {/* Cricket: Show nationality */}
                          {sport?.key === "cricket" && club.meta?.nationality && (
                            <div className="text-xs opacity-75">{club.meta.nationality}</div>
                          )}
                          {/* Other sports: Show country if available */}
                          {sport?.key !== "football" && sport?.key !== "cricket" && club.country && (
                            <div className="text-xs opacity-75">{club.country}</div>
                          )}
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

export default memo(AuctionRoom);
