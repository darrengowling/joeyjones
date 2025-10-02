import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import io from "socket.io-client";
import { useAuctionClock } from "../hooks/useAuctionClock";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

let socket = null;

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

  // Use the new auction clock hook
  const { remainingMs } = useAuctionClock(socket, currentLotId);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    } else {
      alert("Please sign in first");
      navigate("/");
      return;
    }

    loadAuction();
    loadClubs();
    const cleanupSocket = initializeSocket();

    return () => {
      if (socket) {
        // Leave the auction room
        socket.emit("leave_auction", { auctionId });
        
        // Clean up all listeners
        if (cleanupSocket) {
          cleanupSocket();
        }
        
        // Disconnect socket
        socket.disconnect();
        socket = null;
      }
    };
  }, [auctionId]);

  const initializeSocket = () => {
    socket = io(BACKEND_URL, {
      path: "/api/socket.io",
      transports: ["polling", "websocket"], // Try polling first
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });
    
    // Define handlers as named functions for proper cleanup
    const handleConnectError = (error) => {
      console.error("Socket.IO connection error:", error);
    };

    const handleConnect = () => {
      console.log("Socket connected");
      socket.emit("join_auction", { auctionId });
    };

    const handleJoined = (data) => {
      console.log("Joined auction:", data);
    };

    const handleSyncState = (data) => {
      console.log("Received sync state:", data);
      // Update state with current auction data (timer handled by useAuctionClock)
      if (data.currentClub) {
        setCurrentClub(data.currentClub);
      }
      if (data.currentBids) {
        setBids(data.currentBids);
      }
      if (data.participants) {
        setParticipants(data.participants);
      }
      // Extract lot ID from auction data for the clock hook
      if (data.auction && data.auction.currentLotId) {
        setCurrentLotId(data.auction.currentLotId);
      }
    };

    const handleBidPlaced = (data) => {
      console.log("Bid placed:", data);
      setBids((prev) => [data.bid, ...prev]);
      loadAuction();
    };

    const handleLotStarted = (data) => {
      console.log("Lot started:", data);
      setCurrentClub(data.club);
      if (data.timer && data.timer.lotId) {
        setCurrentLotId(data.timer.lotId);
      }
    };

    const handleSold = (data) => {
      console.log("Lot sold:", data);
      
      if (data.unsold) {
        alert(`❌ Club went unsold! "${data.clubId}" will be offered again later.`);
      } else {
        const winnerName = data.winningBid ? data.winningBid.userName : "Unknown";
        const amount = data.winningBid ? `£${data.winningBid.amount.toLocaleString()}` : "";
        alert(`✅ Club sold to ${winnerName} for ${amount}!`);
      }
      
      setCurrentClub(null);
      setBidAmount("");
      if (data.participants) {
        setParticipants(data.participants);
      }
      loadAuction();
    };

    const handleAntiSnipe = (data) => {
      console.log("Anti-snipe triggered:", data);
      alert(`🔥 Anti-snipe! Timer extended!`);
    };

    const handleAuctionComplete = (data) => {
      console.log("Auction complete:", data);
      alert(data.message || "Auction complete! All clubs have been auctioned.");
    };

    const handleDisconnect = () => {
      console.log("Socket disconnected");
    };

    // Remove existing listeners before adding new ones (prevent duplicates)
    socket.off("connect_error", handleConnectError);
    socket.off("connect", handleConnect);
    socket.off("joined", handleJoined);
    socket.off("sync_state", handleSyncState);
    socket.off("bid_placed", handleBidPlaced);
    socket.off("lot_started", handleLotStarted);
    socket.off("sold", handleSold);
    socket.off("anti_snipe", handleAntiSnipe);
    socket.off("auction_complete", handleAuctionComplete);
    socket.off("disconnect", handleDisconnect);

    // Add listeners
    socket.on("connect_error", handleConnectError);
    socket.on("connect", handleConnect);
    socket.on("joined", handleJoined);
    socket.on("sync_state", handleSyncState);
    socket.on("bid_placed", handleBidPlaced);
    socket.on("lot_started", handleLotStarted);
    socket.on("sold", handleSold);
    socket.on("anti_snipe", handleAntiSnipe);
    socket.on("auction_complete", handleAuctionComplete);
    socket.on("disconnect", handleDisconnect);

    // Store cleanup function
    return () => {
      socket.off("connect_error", handleConnectError);
      socket.off("connect", handleConnect);
      socket.off("joined", handleJoined);
      socket.off("sync_state", handleSyncState);
      socket.off("bid_placed", handleBidPlaced);
      socket.off("lot_started", handleLotStarted);
      socket.off("sold", handleSold);
      socket.off("anti_snipe", handleAntiSnipe);
      socket.off("auction_complete", handleAuctionComplete);
      socket.off("disconnect", handleDisconnect);
    };
  };

  const loadAuction = async () => {
    try {
      const response = await axios.get(`${API}/auction/${auctionId}`);
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
      const response = await axios.get(`${API}/clubs`);
      setClubs(response.data);
    } catch (e) {
      console.error("Error loading clubs:", e);
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
      alert("Please enter a bid amount");
      return;
    }

    const amount = parseFloat(bidAmount);
    if (isNaN(amount) || amount <= 0) {
      alert("Please enter a valid bid amount");
      return;
    }

    // Check user's budget
    const userParticipant = participants.find((p) => p.userId === user.id);
    if (userParticipant && amount > userParticipant.budgetRemaining) {
      alert(`Insufficient budget. You have $${userParticipant.budgetRemaining} remaining`);
      return;
    }

    // Check if higher than current highest bid
    const currentBids = bids.filter((b) => b.clubId === currentClub.id);
    if (currentBids.length > 0) {
      const highestBid = Math.max(...currentBids.map((b) => b.amount));
      if (amount <= highestBid) {
        alert(`Bid must be higher than current highest bid: $${highestBid}`);
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading auction...</div>
      </div>
    );
  }

  const isCommissioner = league && user && league.commissionerId === user.id;
  const currentClubBids = currentClub ? bids.filter((b) => b.clubId === currentClub.id) : [];
  const highestBid = currentClubBids.length > 0 ? Math.max(...currentClubBids.map((b) => b.amount)) : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <button
            onClick={() => navigate("/")}
            className="text-white hover:underline mb-4"
          >
            ← Back to Home
          </button>

          {/* Auction Header */}
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  {league ? league.name : "Auction Room"}
                </h1>
                <p className="text-gray-600">Lot #{auction?.currentLot || 0}</p>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600">Bidding as</div>
                <div className="font-semibold text-gray-900">{user?.name}</div>
              </div>
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
                    <div className="text-2xl font-bold text-green-600">
                      ${p.budgetRemaining.toFixed(0)}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Spent: ${p.totalSpent.toFixed(0)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Clubs: {p.clubsWon.length}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            {/* Current Lot */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
              {currentClub ? (
                <div>
                  <h2 className="text-2xl font-bold mb-4 text-gray-900">Current Lot</h2>
                  
                  {/* Timer */}
                  <div className="bg-gradient-to-r from-red-500 to-orange-500 text-white p-6 rounded-lg mb-6 text-center">
                    <div className="text-5xl font-bold">
                      <span data-testid="auction-timer">
                        {(() => {
                          const s = Math.ceil((remainingMs ?? 0) / 1000);
                          const mm = String(Math.floor(s / 60)).padStart(2, "0");
                          const ss = String(s % 60).padStart(2, "0");
                          return `${mm}:${ss}`;
                        })()}
                      </span>
                    </div>
                    <div className="text-sm mt-2">Time Remaining</div>
                  </div>

                  {/* Club Info */}
                  <div className="bg-gray-50 p-6 rounded-lg mb-6">
                    <h3 className="text-3xl font-bold text-gray-900 mb-2">{currentClub.name}</h3>
                    <p className="text-xl text-gray-600">{currentClub.country}</p>
                    <p className="text-sm text-gray-500 mt-2">UEFA ID: {currentClub.uefaId}</p>
                  </div>

                  {/* Current Highest Bid */}
                  {highestBid > 0 && (
                    <div className="bg-green-50 border border-green-200 p-4 rounded-lg mb-6">
                      <div className="text-sm text-gray-600">Current Highest Bid</div>
                      <div className="text-3xl font-bold text-green-600">${highestBid}</div>
                      {currentClubBids[0] && (
                        <div className="text-sm text-gray-600 mt-1">
                          by {currentClubBids[0].userName}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Bid Input */}
                  <div>
                    <div className="flex gap-4 mb-2">
                      <input
                        type="number"
                        placeholder="Enter bid amount"
                        className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
                        value={bidAmount}
                        onChange={(e) => setBidAmount(e.target.value)}
                        data-testid="bid-amount-input"
                      />
                      <button
                        onClick={placeBid}
                        className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-semibold text-lg"
                        data-testid="place-bid-button"
                      >
                        Place Bid
                      </button>
                    </div>
                    {participants.find((p) => p.userId === user?.id) && (
                      <p className="text-sm text-gray-600">
                        Your remaining budget: ${participants.find((p) => p.userId === user.id).budgetRemaining.toFixed(0)}
                      </p>
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
                                <span className="text-green-600 font-bold">${bid.amount}</span>
                              </div>
                            ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="mt-6 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-gray-700">
                    ⏱️ Lot will auto-complete when timer expires. Next club will load automatically.
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">⏳</div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-4">
                    {auction?.status === "completed" ? "Auction Complete!" : "Loading Next Club..."}
                  </h2>
                  <p className="text-gray-600">
                    {auction?.status === "completed" 
                      ? "All clubs have been auctioned. Check the standings!" 
                      : "Clubs auto-load in random order. Next club starting soon..."}
                  </p>
                </div>
              )}
            </div>

            {/* Auction Progress */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-bold mb-4 text-gray-900">Auction Progress</h3>
              
              <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                <div className="text-sm text-gray-600 mb-2">Status</div>
                <div className="text-lg font-bold text-blue-600">
                  {currentClub ? "Live Auction" : "Between Lots"}
                </div>
                <div className="text-sm text-gray-600 mt-2">
                  Clubs load automatically in random order
                </div>
              </div>

              <div className="mb-4">
                <div className="text-sm text-gray-600 mb-2">Clubs Auctioned</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full transition-all"
                      style={{
                        width: `${clubs.length > 0 ? (bids.filter((b, i, arr) => arr.findIndex(a => a.clubId === b.clubId) === i).length / clubs.length) * 100 : 0}%`
                      }}
                    ></div>
                  </div>
                  <div className="text-sm font-semibold text-gray-900">
                    {bids.filter((b, i, arr) => arr.findIndex(a => a.clubId === b.clubId) === i).length}/{clubs.length}
                  </div>
                </div>
              </div>

              <div className="text-xs text-gray-500 space-y-1 mb-4">
                <p>🔄 Clubs auto-load in random order</p>
                <p>⏱️ 60 seconds per club</p>
                <p>🔥 Timer extends if bid in last 30s</p>
              </div>

              <h4 className="font-semibold text-gray-900 mb-2 text-sm">Recent Results</h4>
              <div className="max-h-[400px] overflow-y-auto space-y-2">
                {clubs.map((club) => {
                  const clubBids = bids.filter((b) => b.clubId === club.id);
                  const isCurrentClub = currentClub?.id === club.id;
                  const isSold = clubBids.length > 0;
                  const winner = isSold ? clubBids.sort((a, b) => b.amount - a.amount)[0] : null;
                  
                  if (!isCurrentClub && !isSold) return null;
                  
                  return (
                    <div
                      key={club.id}
                      className={`p-3 rounded-lg border ${
                        isCurrentClub
                          ? "bg-blue-50 border-blue-500"
                          : "bg-gray-50 border-gray-200"
                      }`}
                      data-testid={`club-item-${club.id}`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold text-gray-900">{club.name}</div>
                          <div className="text-xs text-gray-600">{club.country}</div>
                        </div>
                        {isCurrentClub && (
                          <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                            LIVE
                          </span>
                        )}
                        {isSold && !isCurrentClub && (
                          <div className="text-right">
                            <div className="text-xs text-green-600 font-semibold">✓ Sold</div>
                            {winner && (
                              <>
                                <div className="text-xs text-gray-600">{winner.userName}</div>
                                <div className="text-xs font-bold text-gray-900">${winner.amount}</div>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
