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
      console.log("Bid placed event received:", data);
      console.log("Current bids before update:", bids);
      console.log("Current club:", currentClub);
      setBids((prev) => {
        const newBids = [data.bid, ...prev];
        console.log("New bids after update:", newBids);
        return newBids;
      });
      loadAuction();
      loadClubs(); // Reload clubs to update status
    };

    const handleLotStarted = (data) => {
      console.log("Lot started:", data);
      
      if (data.isUnsoldRetry) {
        alert(`🔄 Re-offering unsold club: ${data.club.name}!`);
      }
      
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
      loadClubs(); // Reload clubs to update status
    };

    const handleAntiSnipe = (data) => {
      console.log("Anti-snipe triggered:", data);
      alert(`🔥 Anti-snipe! Timer extended!`);
    };

    const handleAuctionComplete = (data) => {
      console.log("Auction complete:", data);
      alert(data.message || "Auction complete! All clubs have been auctioned.");
    };

    const handleAuctionPaused = (data) => {
      console.log("Auction paused:", data);
      alert(`⏸️ ${data.message}`);
      loadAuction(); // Reload to show paused state
    };

    const handleAuctionResumed = (data) => {
      console.log("Auction resumed:", data);
      alert(`▶️ ${data.message}`);
      loadAuction(); // Reload to show resumed state
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
    socket.off("auction_paused", handleAuctionPaused);
    socket.off("auction_resumed", handleAuctionResumed);
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
    socket.on("auction_paused", handleAuctionPaused);
    socket.on("auction_resumed", handleAuctionResumed);
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
      socket.off("auction_paused", handleAuctionPaused);
      socket.off("auction_resumed", handleAuctionResumed);
      socket.off("disconnect", handleDisconnect);
    };
  };

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
      alert(`Insufficient budget. You have £${userParticipant.budgetRemaining.toLocaleString()} remaining`);
      return;
    }

    // Check if higher than current highest bid
    const currentBids = bids.filter((b) => b.clubId === currentClub.id);
    if (currentBids.length > 0) {
      const highestBid = Math.max(...currentBids.map((b) => b.amount));
      if (amount <= highestBid) {
        alert(`Bid must be higher than current highest bid: £${highestBid.toLocaleString()}`);
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
                        £{p.budgetRemaining.toLocaleString()}
                      </div>
                      <div className="subtle text-xs text-gray-500">
                        Spent: £{p.totalSpent.toLocaleString()}
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
                  
                  {/* Timer */}
                  <div className="bg-gradient-to-r from-red-500 to-orange-500 text-white p-6 rounded-lg mb-6 text-center">
                    <div className="text-5xl font-bold">
                      {(() => {
                        const s = Math.ceil((remainingMs ?? 0) / 1000);
                        const mm = String(Math.floor(s / 60)).padStart(2, "0");
                        const ss = String(s % 60).padStart(2, "0");
                        const warn = (remainingMs ?? 0) < 10000;
                        return (
                          <span data-testid="auction-timer" className={`chip ${warn ? 'warn' : ''}`}>
                            {mm}:{ss}
                          </span>
                        );
                      })()}
                    </div>
                    <div className="text-sm mt-2">Time Remaining</div>
                  </div>

                  {/* Club Info */}
                  <div className="app-card bg-gray-50 p-6 rounded-lg mb-6">
                    <div className="stack-md">
                      <h3 className="h1 text-3xl font-bold text-gray-900">{currentClub.name}</h3>
                      <p className="h2 text-xl text-gray-600">{currentClub.country}</p>
                      <p className="subtle text-sm text-gray-500">UEFA ID: {currentClub.uefaId}</p>
                    </div>
                  </div>

                  {/* Current Highest Bid */}
                  {highestBid > 0 && (
                    <div className="app-card bg-green-50 border border-green-200 p-4 rounded-lg mb-6">
                      <div className="subtle text-sm text-gray-600">💰 Leading Strategic Bid</div>
                      <div className="text-3xl font-bold text-green-600">£{highestBid.toLocaleString()}</div>
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
                        className="btn btn-primary bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-semibold text-lg"
                        data-testid="place-bid-button"
                      >
                        Claim Ownership
                      </button>
                    </div>
                    {participants.find((p) => p.userId === user?.id) && (
                      <p className="text-sm text-gray-600">
                        Your remaining budget: £{participants.find((p) => p.userId === user.id).budgetRemaining.toLocaleString()}
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
                                <span className="text-green-600 font-bold">£{bid.amount.toLocaleString()}</span>
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

            {/* Clubs Overview */}
            <div className="app-card bg-white rounded-lg shadow-lg p-6">
              <h3 className="h2 text-xl font-bold mb-4 text-gray-900">🏆 All Clubs in Auction</h3>
              
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
                              £{club.winningBid.toLocaleString()}
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
