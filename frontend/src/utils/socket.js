/**
 * Global Socket.IO instance
 * Maintains one persistent connection across the entire app
 */
import io from "socket.io-client";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Single global socket instance
let socket = null;
let currentUser = null;

/**
 * Get or create the global socket instance
 */
export const getSocket = () => {
  if (!socket) {
    socket = io(BACKEND_URL, {
      path: "/api/socket.io",
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    // Handle reconnection
    socket.on("connect", () => {
      console.log("✅ Socket connected:", socket.id);
      
      // Rejoin rooms after reconnect
      if (currentUser) {
        socket.emit("rejoin_rooms", { userId: currentUser.id });
      }
    });

    socket.on("disconnect", () => {
      console.log("❌ Socket disconnected");
    });

    socket.on("connected", (data) => {
      console.log("✅ Socket connection confirmed:", data.sid);
    });
  }

  return socket;
};

/**
 * Set current user for room rejoining after reconnects
 */
export const setSocketUser = (user) => {
  currentUser = user;
  console.log("👤 Socket user set:", user?.id);
};

/**
 * Join a league room
 */
export const joinLeagueRoom = (leagueId) => {
  const socket = getSocket();
  console.log("🟦 Joining league room:", leagueId);
  socket.emit("join_league", { leagueId });
};

/**
 * Leave a league room
 */
export const leaveLeagueRoom = (leagueId) => {
  const socket = getSocket();
  console.log("🟦 Leaving league room:", leagueId);
  socket.emit("leave_league", { leagueId });
};

/**
 * Join an auction room
 */
export const joinAuctionRoom = (auctionId) => {
  const socket = getSocket();
  console.log("🟧 Joining auction room:", auctionId);
  socket.emit("join_auction", { auctionId });
};

/**
 * Leave an auction room
 */
export const leaveAuctionRoom = (auctionId) => {
  const socket = getSocket();
  console.log("🟧 Leaving auction room:", auctionId);
  // Note: No leave event needed, socket will disconnect or join other rooms
};
