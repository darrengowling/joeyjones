import { useState, useEffect, useRef, useMemo, useCallback, memo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { useAuctionClock } from "../hooks/useAuctionClock";
import { useSocketRoom } from "../hooks/useSocketRoom";
import { formatCurrency, parseCurrencyInput, isValidCurrencyInput } from "../utils/currency";
import { debounceSocketEvent } from "../utils/performance";
import { debugLogger } from "../utils/debugLogger";
import BottomNav from "../components/BottomNav";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * AuctionRoomStitched - Complete visual redesign with Stitch design system
 * 
 * IMPORTANT: This is a VISUAL REDESIGN ONLY.
 * All state, logic, API calls, socket events, and functionality are preserved exactly from AuctionRoom.js
 * Only the JSX structure and CSS classes have been changed to match the Stitch design.
 */

// Memoized sub-components for better performance
const BidHistoryItem = memo(({ bid, isWinning }) => (
  <div 
    className="p-3 rounded-xl flex justify-between items-center"
    style={{ 
      background: isWinning ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.05)',
      borderLeft: isWinning ? '3px solid #10B981' : '3px solid rgba(255,255,255,0.1)',
    }}
  >
    <div>
      <span className="font-medium text-sm" style={{ color: 'var(--text-primary, #fff)' }}>{bid.userName || 'Anonymous'}</span>
      <span className="text-xs block" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
        {new Date(bid.createdAt).toLocaleTimeString()}
      </span>
    </div>
    <span className="font-bold" style={{ color: '#10B981' }}>{formatCurrency(bid.amount)}</span>
  </div>
));

BidHistoryItem.displayName = 'BidHistoryItem';

function AuctionRoomStitched() {
  const { auctionId } = useParams();
  const navigate = useNavigate();
  
  // === ALL STATE VARIABLES (preserved exactly from original) ===
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
  const [participantCount, setParticipantCount] = useState(0);
  const [currentLotId, setCurrentLotId] = useState(null);
  const [sport, setSport] = useState(null);
  const [uiHints, setUiHints] = useState({ assetLabel: "Club", assetPlural: "Clubs" });
  const [currentBid, setCurrentBid] = useState(null);
  const [currentBidder, setCurrentBidder] = useState(null);
  const [bidSequence, setBidSequence] = useState(0);
  const [countdown, setCountdown] = useState(null);
  const [timerSettings, setTimerSettings] = useState({ timerSeconds: 30, antiSnipeSeconds: 10 });
  const [nextFixture, setNextFixture] = useState(null);
  const [isSubmittingBid, setIsSubmittingBid] = useState(false);

  // Use shared socket room hook
  const { socket, connected, ready, listenerCount } = useSocketRoom('auction', auctionId, { user });

  // Use the new auction clock hook
  const { remainingMs } = useAuctionClock(socket, currentLotId, auction?.status);

  // === ALL useEffect HOOKS (preserved exactly from original) ===

  // Polling fallback for waiting room
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
    loadAuction();
    loadClubs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auctionId]);

  // Socket event handlers - single useEffect with proper cleanup
  useEffect(() => {
    if (!user) return;

    console.log(`🎧 [AuctionRoom] Setting up socket listeners (Count: ${listenerCount})`);
    
    // Join auction room on connect
    socket.emit('join_auction', { auctionId, userId: user.id }, (ack) => {
      if (ack && ack.ok) {
        console.log(`✅ Joined auction room: ${ack.room}, size: ${ack.roomSize}`);
      }
    });

    // Handle auction_snapshot for late joiners
    const onAuctionSnapshot = (data) => {
      debugLogger.logSocketEvent('auction_snapshot', data);
      console.log("📸 Auction snapshot received:", data);
      
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

    // Handle sync_state (legacy)
    const onSyncState = (data) => {
      debugLogger.logSocketEvent('sync_state', data);
      console.log("Received sync state:", data);
      if (data.currentClub) setCurrentClub(data.currentClub);
      if (data.currentBids) setBids(data.currentBids);
      if (data.participants) setParticipants(data.participants);
      if (data.currentBid !== undefined) setCurrentBid(data.currentBid);
      if (data.currentBidder) setCurrentBidder(data.currentBidder);
      if (data.seq !== undefined) setBidSequence(data.seq);
      if (data.auction && data.auction.currentLotId) setCurrentLotId(data.auction.currentLotId);
      console.log("✅ Sync state processed");
    };

    // Handle bid_placed
    const onBidPlaced = (data) => {
      debugLogger.logSocketEvent('bid_placed', data);
      const receiveTime = performance.now();
      console.log("📥 bid_placed received:", {
        ...data,
        receiveTime: new Date().toISOString(),
        latencyMs: data.serverTime ? (Date.now() - new Date(data.serverTime).getTime()) : 'N/A'
      });
      setBids((prev) => [data.bid, ...prev]);
    };

    // Handle bid_update
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
      
      const seqGap = data.seq - bidSequence;
      if (seqGap > 1) {
        console.warn(`⚠️ Seq gap detected: expected ${bidSequence + 1}, got ${data.seq}. Resyncing...`);
        loadAuction();
      }
      
      if (data.seq >= bidSequence) {
        console.log(`✅ Applying bid update: ${formatCurrency(data.amount)} by ${data.bidder?.displayName} (seq: ${data.seq}, latency: ${serverLatency}ms)`);
        setCurrentBid(data.amount);
        setCurrentBidder(data.bidder);
        setBidSequence(data.seq);
        
        requestAnimationFrame(() => {
          const renderTime = performance.now();
          console.log(`🎨 bid_update rendered: totalMs=${Math.round(renderTime - receiveTime)}`);
        });
      } else {
        console.log(`⚠️ Ignoring stale bid update: seq=${data.seq}, current=${bidSequence}`);
      }
    };

    // Handle lot_started
    const onLotStarted = (data) => {
      debugLogger.logSocketEvent('lot_started', data);
      console.log("🚀 Lot started:", data);
      
      if (data.isUnsoldRetry) {
        toast(`🔄 Re-offering unsold ${uiHints.assetLabel.toLowerCase()}: ${data.club.name}!`, { duration: 4000 });
      }
      
      loadAuction();
      setCurrentClub(data.club);
      if (data.timer && data.timer.lotId) setCurrentLotId(data.timer.lotId);
      
      setCurrentBid(null);
      setCurrentBidder(null);
      setBidSequence(0);
      console.log("✅ Cleared bid state for new lot");
    };

    // Handle sold event
    const onSold = (data) => {
      debugLogger.logSocketEvent('sold', data);
      console.log("=== SOLD EVENT RECEIVED ===");
      
      const playerName = data.clubName || `Unknown ${uiHints.assetLabel.toLowerCase()}`;
      
      if (data.unsold) {
        toast.error(`${playerName} went unsold and will be offered again later.`);
      } else {
        const winnerName = data.winningBid ? data.winningBid.userName : "Unknown";
        const amount = data.winningBid ? formatCurrency(data.winningBid.amount) : "";
        toast.success(`${playerName} sold to ${winnerName} for ${amount}!`, { duration: 4000 });
        
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
      if (data.participants) setParticipants(data.participants);
      loadAuction();
    };

    // Handle anti-snipe event
    const onAntiSnipe = (data) => {
      debugLogger.logSocketEvent('anti_snipe', data);
      console.log("Anti-snipe triggered:", data);
      toast("🔥 Anti-snipe! Timer extended!", { duration: 3000 });
    };

    // Handle auction_complete event
    const onAuctionComplete = (data) => {
      debugLogger.logSocketEvent('auction_complete', data);
      console.log("Auction complete:", data);
      
      if (data.participants) setParticipants(data.participants);
      
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
        
        if (currentClub?.id === data.finalClubId) {
          setCurrentBid(null);
          setCurrentBidder(null);
        }
        
        loadAuction();
      } else {
        loadAuction();
        loadClubs();
      }
      
      toast.success(data.message || `Auction complete! All ${uiHints.assetPlural.toLowerCase()} have been auctioned.`, { duration: 5000 });
    };

    // Handle auction_paused event
    const onAuctionPaused = (data) => {
      debugLogger.logSocketEvent('auction_paused', data);
      console.log("Auction paused:", data);
      toast(`⏸️ ${data.message}`, { duration: 4000 });
      loadAuction();
    };

    // Handle auction_resumed event
    const onAuctionResumed = (data) => {
      debugLogger.logSocketEvent('auction_resumed', data);
      console.log("Auction resumed:", data);
      toast(`▶️ ${data.message}`, { duration: 4000 });
      loadAuction();
    };

    // Handle auction_deleted event
    const onAuctionDeleted = (data) => {
      debugLogger.logSocketEvent('auction_deleted', data);
      console.log("🗑️ Auction deleted by commissioner:", data);
      toast.error(data.message || "Auction has been deleted by the commissioner", { duration: 5000 });
      setCountdown(null);
      setTimeout(() => {
        navigate('/');
      }, 2000);
    };

    // Handle participants_changed
    const onParticipantsChanged = (data) => {
      debugLogger.logSocketEvent('participants_changed', data);
      console.log("👥 Participants changed:", data);
      if (auction?.leagueId) loadParticipants();
    };

    // Register all event listeners
    socket.on('auction_snapshot', onAuctionSnapshot);
    socket.on('sync_state', onSyncState);
    socket.on('bid_placed', onBidPlaced);
    socket.on('bid_update', onBidUpdate);
    socket.on('lot_started', onLotStarted);
    socket.on('sold', onSold);
    socket.on('anti_snipe', onAntiSnipe);
    socket.on('auction_complete', onAuctionComplete);
    socket.on('auction_paused', onAuctionPaused);
    socket.on('auction_resumed', onAuctionResumed);
    socket.on('auction_deleted', onAuctionDeleted);
    socket.on('participants_changed', onParticipantsChanged);
    
    // Resync on reconnect
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
        setCountdown(null);
      } else {
        setCountdown(data.seconds);
      }
    };
    socket.on('next_team_countdown', onNextTeamCountdown);

    // Cleanup function
    return () => {
      console.log('🧹 [AuctionRoom] Removing socket listeners');
      socket.off('auction_snapshot', onAuctionSnapshot);
      socket.off('sync_state', onSyncState);
      socket.off('bid_placed', onBidPlaced);
      socket.off('bid_update', onBidUpdate);
      socket.off('lot_started', onLotStarted);
      socket.off('sold', onSold);
      socket.off('anti_snipe', onAntiSnipe);
      socket.off('auction_complete', onAuctionComplete);
      socket.off('auction_paused', onAuctionPaused);
      socket.off('auction_resumed', onAuctionResumed);
      socket.off('auction_deleted', onAuctionDeleted);
      socket.off('participants_changed', onParticipantsChanged);
      socket.off('connect', onReconnect);
      socket.off('waiting_room_updated', onWaitingRoomUpdated);
      socket.off('next_team_countdown', onNextTeamCountdown);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auctionId, user, bidSequence, listenerCount]);

  // Pre-fill bid input with current bid amount
  useEffect(() => {
    if (!currentClub) {
      setBidAmount("");
      return;
    }
    if (currentBid && currentBid > 0) {
      setBidAmount((currentBid / 1000000).toString());
    } else {
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

  // Poll for auction existence when paused
  useEffect(() => {
    if (!auction || auction.status !== 'paused') return;

    const checkAuctionExists = async () => {
      try {
        await axios.get(`${API}/auction/${auctionId}`);
      } catch (e) {
        if (e.response && e.response.status === 404) {
          console.log("⚠️ Auction deleted while paused - showing reset message");
          setAuction(null);
        }
      }
    };

    const pollInterval = setInterval(checkAuctionExists, 3000);
    return () => clearInterval(pollInterval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auction?.status, auctionId]);

  // === ALL DATA LOADING FUNCTIONS (preserved exactly from original) ===

  const loadAuction = async () => {
    try {
      const response = await axios.get(`${API}/auction/${auctionId}`);
      console.log("Auction data loaded:", response.data);
      
      debugLogger.setAuctionId(auctionId);
      debugLogger.log('auction_start', {
        status: response.data.auction.status,
        currentLot: response.data.auction.currentLot,
        existingBids: response.data.bids.length
      });
      
      setAuction(response.data.auction);
      setBids(response.data.bids);
      if (response.data.currentClub) setCurrentClub(response.data.currentClub);
      if (response.data.auction.currentLotId) setCurrentLotId(response.data.auction.currentLotId);

      const leagueResponse = await axios.get(`${API}/leagues/${response.data.auction.leagueId}`);
      setLeague(leagueResponse.data);
      
      setTimerSettings({
        timerSeconds: leagueResponse.data.timerSeconds || 30,
        antiSnipeSeconds: leagueResponse.data.antiSnipeSeconds || 10
      });
      
      if (leagueResponse.data.sportKey) {
        try {
          const sportResponse = await axios.get(`${API}/sports/${leagueResponse.data.sportKey}`);
          setSport(sportResponse.data);
          setUiHints(sportResponse.data.uiHints);
        } catch (e) {
          console.error("Error loading sport info:", e);
        }
      }

      const participantsResponse = await axios.get(`${API}/leagues/${response.data.auction.leagueId}/participants`);
      console.log("📊 Participants loaded:", participantsResponse.data);
      setParticipantCount(participantsResponse.data.count || 0);
      setParticipants(participantsResponse.data.participants || []);
    } catch (e) {
      console.error("Error loading auction:", e);
      if (e.response && e.response.status === 404) {
        console.log("⚠️ Auction not found - likely reset by commissioner");
        setAuction(null);
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
      console.log("📊 Participants refreshed:", response.data);
      setParticipantCount(response.data.count || 0);
      setParticipants(response.data.participants || []);
    } catch (e) {
      console.error("Error loading participants:", e);
    }
  };

  const loadNextFixture = async (clubId) => {
    try {
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
      setNextFixture(null);
    }
  };

  // === ALL ACTION FUNCTIONS (preserved exactly from original) ===

  const placeBid = async () => {
    if (!user || !currentClub || !bidAmount) {
      toast.error("Please enter your strategic bid amount to claim ownership");
      return;
    }

    if (!isValidCurrencyInput(bidAmount)) {
      toast.error("Please enter a valid bid amount (e.g., 5m, £10m, 23m)");
      return;
    }
    
    const amount = parseCurrencyInput(bidAmount);
    const userParticipant = participants.find((p) => p.userId === user.id);
    const currentBids = bids.filter((b) => b.clubId === currentClub.id);
    const highestBid = currentBids.length > 0 ? Math.max(...currentBids.map((b) => b.amount)) : 0;

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
        timeout: 10000
      });
      
      const duration = performance.now() - startTime;
      
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
      
      if (e.code === 'ECONNABORTED' || e.message.includes('timeout')) {
        toast.error("Bid request timed out. Please try again.");
      } else if (e.response?.status === 429) {
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
        const errorMsg = e.response?.data?.detail || `Server error: ${e.response.status}`;
        toast.error(errorMsg);
        if (errorMsg.includes("already the highest bidder") && currentBid) {
          setBidAmount((currentBid / 1000000).toString());
        }
      } else if (e.request) {
        toast.error("No response from server. Check your connection.");
      } else {
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
      navigate("/");
    } catch (e) {
      console.error("Error deleting auction:", e);
      alert("Error deleting auction: " + (e.response?.data?.detail || e.message));
    }
  };

  // === LOADING STATE (Stitch styled) ===
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-base, #0F172A)' }}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-t-transparent rounded-full animate-spin mx-auto mb-4" style={{ borderColor: 'var(--color-primary, #06B6D4)', borderTopColor: 'transparent' }}></div>
          <p style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>Loading auction...</p>
        </div>
      </div>
    );
  }

  // === AUCTION RESET SCREEN (Stitch styled) ===
  if (!auction && !loading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6" style={{ background: 'var(--bg-base, #0F172A)' }}>
        <div 
          className="w-full max-w-md rounded-3xl p-8 text-center"
          style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.1)' }}
        >
          <div className="text-6xl mb-4">🔄</div>
          <h2 className="text-2xl font-bold mb-4" style={{ color: 'var(--text-primary, #fff)' }}>Auction Has Been Reset</h2>
          <p className="mb-6" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
            The commissioner has reset this auction. Please wait on the competition page for the commissioner to restart the auction.
          </p>
          <button
            onClick={() => navigate(-1)}
            className="w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-[0.98]"
            style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
          >
            Return to Competition Page
          </button>
        </div>
      </div>
    );
  }

  const isCommissioner = league && user && league.commissionerId === user.id;

  // === WAITING ROOM (Stitch styled) ===
  if (auction?.status === "waiting") {
    const handleBeginAuction = async () => {
      try {
        await axios.post(`${API}/auction/${auctionId}/begin`, null, {
          headers: { 'X-User-ID': user.id }
        });
        console.log("✅ Auction begin request sent");
      } catch (error) {
        console.error("Error starting auction:", error);
        alert(error.response?.data?.detail || "Failed to start auction");
      }
    };

    return (
      <div className="min-h-screen font-sans" style={{ background: 'var(--bg-base, #0F172A)', paddingBottom: '100px' }}>
        {/* Fixed Header */}
        <header 
          className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-md z-40 px-4 py-4 flex items-center justify-between"
          style={{
            background: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          }}
        >
          <button 
            onClick={() => navigate('/')}
            className="w-10 h-10 flex items-center justify-center rounded-full transition-all active:scale-95"
            style={{ background: 'rgba(255,255,255,0.05)' }}
          >
            <span className="material-symbols-outlined" style={{ color: 'var(--text-primary, #fff)' }}>arrow_back</span>
          </button>
          <h1 className="text-sm font-black tracking-widest uppercase" style={{ color: 'var(--text-primary, #fff)' }}>
            Waiting Room
          </h1>
          <div className="w-10"></div>
        </header>

        <main className="pt-24 px-4">
          <div className="max-w-md mx-auto">
            {/* Waiting Room Card */}
            <div 
              className="p-6 rounded-3xl text-center mb-6"
              style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.1)' }}
            >
              <div className="w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center" style={{ background: 'rgba(6, 182, 212, 0.2)' }}>
                <span className="material-symbols-outlined text-4xl" style={{ color: 'var(--color-primary, #06B6D4)' }}>hourglass_top</span>
              </div>
              <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary, #fff)' }}>Auction Waiting Room</h2>
              <p className="text-sm" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                {isCommissioner 
                  ? "Waiting for participants to join"
                  : "Waiting for commissioner to start"}
              </p>
            </div>

            {/* Participants Ready */}
            <div 
              className="p-5 rounded-2xl mb-6"
              style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}
            >
              <h3 className="font-bold text-sm mb-4" style={{ color: 'var(--text-primary, #fff)' }}>
                Participants Ready ({auction?.usersInWaitingRoom?.length || 0})
              </h3>
              <div className="flex flex-wrap gap-2">
                {participants
                  .filter(p => auction?.usersInWaitingRoom?.includes(p.userId))
                  .map(p => (
                    <div
                      key={p.userId}
                      className="flex items-center gap-2 px-3 py-2 rounded-full"
                      style={{ background: 'rgba(255,255,255,0.1)' }}
                    >
                      <div 
                        className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                        style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
                      >
                        {p.userName?.charAt(0).toUpperCase() || '?'}
                      </div>
                      <span className="text-sm font-medium" style={{ color: 'var(--text-primary, #fff)' }}>
                        {p.userName}
                      </span>
                      {p.userId === user.id && (
                        <span 
                          className="text-[10px] px-2 py-0.5 rounded-full"
                          style={{ background: 'rgba(6, 182, 212, 0.3)', color: 'var(--color-primary, #06B6D4)' }}
                        >
                          You
                        </span>
                      )}
                    </div>
                  ))}
                {(!auction?.usersInWaitingRoom || auction.usersInWaitingRoom.length === 0) && (
                  <p className="text-sm w-full text-center py-4" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                    {isCommissioner 
                      ? "Waiting for participants to join..."
                      : "Waiting for other participants..."}
                  </p>
                )}
              </div>
            </div>

            {/* Action Button */}
            {isCommissioner ? (
              <button
                onClick={handleBeginAuction}
                className="w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-[0.98]"
                style={{ background: '#10B981', color: '#fff' }}
                data-testid="begin-auction-button"
              >
                🚀 Begin Auction
              </button>
            ) : (
              <div className="text-center">
                <div className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center animate-pulse" style={{ background: 'rgba(255,255,255,0.1)' }}>
                  <span className="material-symbols-outlined text-3xl" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>schedule</span>
                </div>
                <p className="font-medium" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                  Waiting for commissioner to start...
                </p>
              </div>
            )}
          </div>
        </main>

        <BottomNav />
      </div>
    );
  }

  const currentClubBids = currentClub ? bids.filter((b) => b.clubId === currentClub.id) : [];
  const highestBid = currentClubBids.length > 0 ? Math.max(...currentClubBids.map((b) => b.amount)) : 0;

  // === AUTH REQUIRED SCREEN (Stitch styled) ===
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6" style={{ background: 'var(--bg-base, #0F172A)' }}>
        <div 
          data-testid="auth-required"
          className="w-full max-w-md rounded-3xl p-8 text-center"
          style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.1)' }}
        >
          <h2 className="text-2xl font-bold mb-4" style={{ color: 'var(--text-primary, #fff)' }}>Authentication Required</h2>
          <p className="mb-6" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>Please sign in to access the auction room.</p>
          <button
            onClick={() => navigate("/")}
            className="w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-[0.98]"
            style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  // === MAIN AUCTION ROOM (Stitch styled) ===
  return (
    <div className="min-h-screen font-sans" style={{ background: 'var(--bg-base, #0F172A)' }}>
      {/* Fixed Header */}
      <header 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-md z-40 px-4 py-3"
        style={{
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <div className="flex items-center justify-between">
          <button 
            onClick={() => navigate(`/league/${league?.id}`)}
            className="w-10 h-10 flex items-center justify-center rounded-full transition-all active:scale-95"
            style={{ background: 'rgba(255,255,255,0.05)' }}
          >
            <span className="material-symbols-outlined" style={{ color: 'var(--text-primary, #fff)' }}>arrow_back</span>
          </button>
          <div className="text-center flex-1 mx-4">
            <h1 className="text-xs font-black tracking-widest uppercase truncate" style={{ color: 'var(--text-primary, #fff)' }}>
              {league?.name || 'Auction'}
            </h1>
            <p className="text-[10px]" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
              Lot {auction?.currentLot || 0} / {auction?.clubQueue?.length || 0}
            </p>
          </div>
          {auction?.status === "paused" && (
            <span 
              className="px-2 py-1 rounded text-[10px] font-bold"
              style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#F59E0B' }}
            >
              PAUSED
            </span>
          )}
          {auction?.status === "completed" && (
            <span 
              className="px-2 py-1 rounded text-[10px] font-bold"
              style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981' }}
            >
              COMPLETE
            </span>
          )}
        </div>
      </header>

      {/* Countdown Overlay */}
      {countdown !== null && countdown > 0 && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(0,0,0,0.9)' }}
        >
          <div className="text-center">
            <div 
              className="text-8xl font-black mb-4"
              style={{ color: 'var(--color-primary, #06B6D4)' }}
            >
              {countdown}
            </div>
            <p className="text-xl" style={{ color: 'var(--text-primary, #fff)' }}>Next team in {countdown}...</p>
            <p className="text-sm mt-2" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Get ready to bid</p>
          </div>
        </div>
      )}

      <main className="pt-20 pb-24 px-4">
        {/* Current Lot Section */}
        {currentClub && auction?.status !== "completed" ? (
          <div className="space-y-4">
            {/* Timer + Current Bid Card */}
            <div 
              className="p-4 rounded-2xl"
              style={{ background: 'rgba(0,0,0,0.5)', border: '1px solid rgba(255,255,255,0.1)' }}
            >
              {/* Team Name + Timer Row */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex-1 min-w-0">
                  <h2 className="text-xl font-bold truncate" style={{ color: 'var(--text-primary, #fff)' }}>{currentClub.name}</h2>
                  {currentClub.meta?.franchise && (
                    <p className="text-sm" style={{ color: 'var(--color-primary, #06B6D4)' }}>{currentClub.meta.franchise}</p>
                  )}
                  {nextFixture && (
                    <p className="text-xs mt-1" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                      Next: {nextFixture.opponent} ({nextFixture.isHome ? 'H' : 'A'})
                    </p>
                  )}
                </div>
                
                {/* Timer */}
                <div className="text-center">
                  <div 
                    className="text-4xl font-black"
                    data-testid="auction-timer"
                    style={{ 
                      color: auction?.status === 'paused' 
                        ? '#F59E0B' 
                        : (remainingMs ?? 0) < 10000 
                          ? '#EF4444' 
                          : 'var(--text-primary, #fff)'
                    }}
                  >
                    {(() => {
                      const s = Math.ceil((remainingMs ?? 0) / 1000);
                      const mm = String(Math.floor(s / 60)).padStart(2, "0");
                      const ss = String(s % 60).padStart(2, "0");
                      return `${mm}:${ss}`;
                    })()}
                  </div>
                  <p className="text-[10px] uppercase tracking-widest" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                    {auction?.status === 'paused' ? 'PAUSED' : 'Time Left'}
                  </p>
                </div>
              </div>

              {/* Current Bid Display */}
              <div 
                className="p-4 rounded-xl"
                style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)' }}
              >
                {currentBid > 0 && currentBidder ? (
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[10px] uppercase tracking-widest mb-1" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Current Bid</p>
                      <p className="text-3xl font-black" style={{ color: '#10B981' }}>{formatCurrency(currentBid)}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-10 h-10 rounded-full flex items-center justify-center font-bold"
                        style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
                      >
                        {currentBidder.displayName.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-sm font-medium" style={{ color: 'var(--text-primary, #fff)' }}>{currentBidder.displayName}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-2">
                    <p style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>💰 No bids yet - Be the first!</p>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Bid Buttons */}
            <div className="flex gap-2 overflow-x-auto pb-2">
              {[1, 2, 5, 10, 20, 50].map((amount) => (
                <button
                  key={amount}
                  onClick={() => {
                    const currentInputValue = parseFloat(bidAmount) || 0;
                    const newBid = currentInputValue + amount;
                    setBidAmount(newBid.toString());
                  }}
                  disabled={!ready}
                  className="flex-shrink-0 px-5 py-3 rounded-xl font-bold text-sm transition-all active:scale-95 disabled:opacity-50"
                  style={{ background: 'rgba(255,255,255,0.1)', color: 'var(--text-primary, #fff)' }}
                >
                  +{amount}m
                </button>
              ))}
            </div>

            {/* Bid Input + Place Bid */}
            <div className="flex gap-3">
              <input
                type="text"
                readOnly
                placeholder="Use buttons above"
                className="flex-1 px-4 py-4 rounded-xl text-lg font-bold text-center"
                style={{ 
                  background: 'rgba(255,255,255,0.1)', 
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: 'var(--text-primary, #fff)',
                }}
                value={bidAmount ? `£${bidAmount}m` : ""}
                disabled={!ready}
                data-testid="bid-amount-input"
              />
              <button
                onClick={placeBid}
                disabled={!ready || isSubmittingBid || participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3)}
                className="px-6 py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-95 disabled:opacity-50"
                style={{ 
                  background: (!ready || isSubmittingBid || participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3))
                    ? 'rgba(255,255,255,0.1)' 
                    : 'var(--color-primary, #06B6D4)',
                  color: (!ready || isSubmittingBid || participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3))
                    ? 'var(--text-muted, rgba(255,255,255,0.4))'
                    : 'var(--bg-base, #0F172A)',
                }}
                data-testid="place-bid-button"
              >
                {!ready 
                  ? "..." 
                  : isSubmittingBid
                    ? "..."
                  : participants.find((p) => p.userId === user?.id)?.clubsWon?.length >= (league?.clubSlots || 3) 
                    ? "Full" 
                    : "Bid"
                }
              </button>
            </div>

            {/* Your Budget Info */}
            {participants.find((p) => p.userId === user?.id) && (
              <div 
                className="p-4 rounded-xl"
                style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-[10px] uppercase tracking-widest" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Your Budget</p>
                    <p className="text-xl font-bold" style={{ color: '#10B981' }}>
                      {formatCurrency(participants.find((p) => p.userId === user.id).budgetRemaining)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] uppercase tracking-widest" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Roster</p>
                    <p className="text-lg font-bold" style={{ color: 'var(--text-primary, #fff)' }}>
                      {participants.find((p) => p.userId === user.id).clubsWon?.length || 0} / {league?.clubSlots || 3}
                      <span className="ml-2">
                        {participants.find((p) => p.userId === user.id).clubsWon?.length >= (league?.clubSlots || 3) ? '🔒' : '📍'}
                      </span>
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Team Metadata */}
            <div 
              className="p-4 rounded-xl"
              style={{ background: 'rgba(255,255,255,0.05)' }}
            >
              {sport?.key === "football" && (
                <div className="flex items-center gap-3 text-sm">
                  <span style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{currentClub.country}</span>
                  {currentClub.uefaId && (
                    <span style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>UEFA ID: {currentClub.uefaId}</span>
                  )}
                </div>
              )}
              {sport?.key === "cricket" && currentClub.meta && (
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  {currentClub.meta.nationality && (
                    <span 
                      className="px-2 py-1 rounded text-xs font-semibold"
                      style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981' }}
                    >
                      {currentClub.meta.nationality}
                    </span>
                  )}
                  {currentClub.meta.role && (
                    <span style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>Role: {currentClub.meta.role}</span>
                  )}
                  {currentClub.meta.bowling && (
                    <span style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Bowling: {currentClub.meta.bowling}</span>
                  )}
                </div>
              )}
              {sport?.key !== "football" && sport?.key !== "cricket" && currentClub.country && (
                <span style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{currentClub.country}</span>
              )}
            </div>

            {/* Bid History */}
            <div 
              className="p-4 rounded-2xl"
              style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
            >
              <h3 className="font-bold text-sm mb-3" style={{ color: 'var(--text-primary, #fff)' }}>Bid History</h3>
              <div className="max-h-40 overflow-y-auto space-y-2">
                {currentClubBids.length === 0 ? (
                  <p className="text-sm text-center py-4" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>No bids yet</p>
                ) : (
                  currentClubBids
                    .sort((a, b) => b.amount - a.amount)
                    .map((bid) => (
                      <BidHistoryItem 
                        key={bid.id} 
                        bid={bid} 
                        isWinning={bid.amount === highestBid} 
                      />
                    ))
                )}
              </div>
            </div>

            {/* Manager Budgets (Horizontal Scroll) */}
            <div 
              className="p-4 rounded-2xl"
              style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
            >
              <h3 className="font-bold text-sm mb-3" style={{ color: 'var(--text-primary, #fff)' }}>Manager Budgets</h3>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {participants.map((p) => {
                  const isCurrentUser = user && p.userId === user.id;
                  return (
                    <div
                      key={p.id}
                      className="flex-shrink-0 w-32 p-3 rounded-xl"
                      style={{ 
                        background: isCurrentUser ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255,255,255,0.05)',
                        border: isCurrentUser ? '1px solid rgba(6, 182, 212, 0.3)' : '1px solid transparent',
                      }}
                    >
                      <p className="text-xs font-bold truncate mb-1" style={{ color: 'var(--text-primary, #fff)' }}>
                        {p.userName} {isCurrentUser && "(You)"}
                      </p>
                      <p className="text-lg font-bold" style={{ color: '#10B981' }}>
                        {formatCurrency(p.budgetRemaining)}
                      </p>
                      <p className="text-[10px]" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>
                        🏆 {p.clubsWon.length} {uiHints.assetPlural.toLowerCase()}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Clubs Overview */}
            <div 
              className="p-4 rounded-2xl"
              style={{ background: 'rgba(30, 41, 59, 0.5)', border: '1px solid rgba(255,255,255,0.08)' }}
            >
              <h3 className="font-bold text-sm mb-3" style={{ color: 'var(--text-primary, #fff)' }}>
                🏆 {uiHints.assetPlural} Overview
              </h3>
              
              {/* Stats Grid */}
              <div className="grid grid-cols-4 gap-2 mb-4">
                <div className="p-2 rounded-lg text-center" style={{ background: 'rgba(6, 182, 212, 0.1)' }}>
                  <p className="text-lg font-bold" style={{ color: 'var(--color-primary, #06B6D4)' }}>{clubs.length}</p>
                  <p className="text-[10px]" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Total</p>
                </div>
                <div className="p-2 rounded-lg text-center" style={{ background: 'rgba(16, 185, 129, 0.1)' }}>
                  <p className="text-lg font-bold" style={{ color: '#10B981' }}>{clubs.filter(c => c.status === 'sold').length}</p>
                  <p className="text-[10px]" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Sold</p>
                </div>
                <div className="p-2 rounded-lg text-center" style={{ background: 'rgba(245, 158, 11, 0.1)' }}>
                  <p className="text-lg font-bold" style={{ color: '#F59E0B' }}>{clubs.filter(c => c.status === 'current').length}</p>
                  <p className="text-[10px]" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Live</p>
                </div>
                <div className="p-2 rounded-lg text-center" style={{ background: 'rgba(255,255,255,0.05)' }}>
                  <p className="text-lg font-bold" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>{clubs.filter(c => c.status === 'upcoming').length}</p>
                  <p className="text-[10px]" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>Left</p>
                </div>
              </div>

              {/* Club List */}
              <div className="max-h-60 overflow-y-auto space-y-2">
                {clubs.map((club) => {
                  const statusColors = {
                    current: { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgba(245, 158, 11, 0.3)', text: '#F59E0B' },
                    upcoming: { bg: 'rgba(6, 182, 212, 0.1)', border: 'rgba(6, 182, 212, 0.2)', text: '#06B6D4' },
                    sold: { bg: 'rgba(16, 185, 129, 0.1)', border: 'rgba(16, 185, 129, 0.2)', text: '#10B981' },
                    unsold: { bg: 'rgba(239, 68, 68, 0.1)', border: 'rgba(239, 68, 68, 0.2)', text: '#EF4444' }
                  };
                  const statusIcons = { current: "🔥", upcoming: "⏳", sold: "✅", unsold: "❌" };
                  const colors = statusColors[club.status] || statusColors.upcoming;
                  
                  return (
                    <div
                      key={club.id}
                      className="p-3 rounded-xl"
                      style={{ background: colors.bg, border: `1px solid ${colors.border}` }}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate" style={{ color: 'var(--text-primary, #fff)' }}>{club.name}</p>
                          {sport?.key === "cricket" && club.meta?.franchise && (
                            <p className="text-xs truncate" style={{ color: 'var(--color-primary, #06B6D4)' }}>{club.meta.franchise}</p>
                          )}
                          {sport?.key === "football" && club.country && (
                            <p className="text-xs" style={{ color: 'var(--text-muted, rgba(255,255,255,0.4))' }}>{club.country}</p>
                          )}
                          {club.status === 'sold' && club.winner && (
                            <p className="text-xs mt-1" style={{ color: colors.text }}>
                              Won by {club.winner} • {formatCurrency(club.winningBid)}
                            </p>
                          )}
                        </div>
                        <span className="text-lg">{statusIcons[club.status]}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Commissioner Controls */}
            {isCommissioner && (
              <div 
                className="p-4 rounded-2xl"
                style={{ background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.2)' }}
              >
                <h3 className="font-bold text-sm mb-3" style={{ color: 'var(--text-primary, #fff)' }}>Commissioner Controls</h3>
                <div className="flex flex-wrap gap-2">
                  {auction?.status === "active" && (
                    <button
                      onClick={pauseAuction}
                      className="px-4 py-2 rounded-lg text-sm font-bold transition-all active:scale-95"
                      style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#F59E0B' }}
                    >
                      ⏸️ Pause
                    </button>
                  )}
                  {auction?.status === "paused" && (
                    <button
                      onClick={resumeAuction}
                      className="px-4 py-2 rounded-lg text-sm font-bold transition-all active:scale-95"
                      style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10B981' }}
                    >
                      ▶️ Resume
                    </button>
                  )}
                  {(auction?.status === "paused" || auction?.status === "completed") && (
                    <button
                      onClick={resetAuction}
                      className="px-4 py-2 rounded-lg text-sm font-bold transition-all active:scale-95"
                      style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#F59E0B' }}
                    >
                      🔄 Reset
                    </button>
                  )}
                  <button
                    onClick={completeLot}
                    className="px-4 py-2 rounded-lg text-sm font-bold transition-all active:scale-95"
                    style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#EF4444' }}
                  >
                    Complete Lot
                  </button>
                  <button
                    onClick={deleteAuction}
                    className="px-4 py-2 rounded-lg text-sm font-bold transition-all active:scale-95"
                    style={{ background: 'rgba(239, 68, 68, 0.3)', color: '#EF4444' }}
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Auction Complete or Waiting for Next Lot */
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="text-center">
              <div className="text-6xl mb-4">{auction?.status === "completed" ? "🎉" : "⏳"}</div>
              <h2 className="text-2xl font-bold mb-4" style={{ color: 'var(--text-primary, #fff)' }}>
                {auction?.status === "completed" ? "Auction Complete!" : "Preparing Next Strategic Opportunity..."}
              </h2>
              <p className="mb-6" style={{ color: 'var(--text-secondary, rgba(255,255,255,0.6))' }}>
                {auction?.status === "completed" 
                  ? `All ${uiHints.assetPlural.toLowerCase()} have been auctioned.` 
                  : `${uiHints.assetPlural} auto-load in random order. Next ${uiHints.assetLabel.toLowerCase()} starting soon...`}
              </p>
              {auction?.status === "completed" && (
                <button
                  onClick={() => navigate("/app/my-competitions")}
                  className="px-8 py-4 rounded-xl font-black uppercase tracking-widest text-sm transition-all active:scale-[0.98]"
                  style={{ background: 'var(--color-primary, #06B6D4)', color: 'var(--bg-base, #0F172A)' }}
                  data-testid="go-to-my-competitions"
                >
                  Go to My Competitions →
                </button>
              )}
            </div>
          </div>
        )}
      </main>

      <BottomNav />
    </div>
  );
}

export default memo(AuctionRoomStitched);
