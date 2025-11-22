/**
 * Global Socket.IO instance with Enhanced Reconnection
 * Production Hardening - Days 9-10: Error Recovery & Resilience
 * Maintains one persistent connection with automatic reconnection and error handling
 */
import io from "socket.io-client";
import toast from "react-hot-toast";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Single global socket instance
let socket = null;
let currentUser = null;
let currentRooms = new Set(); // Track joined rooms for reconnection
let reconnectToastId = null;
let isManualDisconnect = false;

/**
 * Get or create the global socket instance with enhanced reconnection
 */
export const getSocket = () => {
  if (!socket) {
    socket = io(BACKEND_URL, {
      path: "/api/socket.io",
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 10, // Increased from 5
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
    });

    // Connection established
    socket.on("connect", () => {
      console.log("✅ Socket connected:", socket.id);
      
      // Clear any reconnection toast
      if (reconnectToastId) {
        toast.dismiss(reconnectToastId);
        reconnectToastId = null;
      }
      
      // Show success message if this was a reconnection
      if (!isManualDisconnect && currentRooms.size > 0) {
        toast.success("Connection restored!", { duration: 2000 });
      }
      
      // Rejoin all rooms after reconnect
      if (currentUser) {
        console.log("🔄 Rejoining rooms after reconnect:", Array.from(currentRooms));
        currentRooms.forEach(room => {
          if (room.startsWith("league_")) {
            const leagueId = room.replace("league_", "");
            socket.emit("join_league", { leagueId });
          } else if (room.startsWith("auction_")) {
            const auctionId = room.replace("auction_", "");
            socket.emit("join_auction", { auctionId });
          }
        });
      }
    });

    // Connection error
    socket.on("connect_error", (error) => {
      console.error("❌ Socket connection error:", error.message);
      
      if (!reconnectToastId && !isManualDisconnect) {
        reconnectToastId = toast.error(
          "Connection lost. Reconnecting...",
          { 
            duration: Infinity,
            icon: "🔄"
          }
        );
      }
    });

    // Disconnection
    socket.on("disconnect", (reason) => {
      console.log("❌ Socket disconnected:", reason);
      
      // Show toast only for unexpected disconnects
      if (!isManualDisconnect && reason !== "io client disconnect") {
        if (!reconnectToastId) {
          reconnectToastId = toast.error(
            "Connection lost. Reconnecting...",
            { 
              duration: Infinity,
              icon: "🔄"
            }
          );
        }
      }
    });

    // Reconnection attempt
    socket.io.on("reconnect_attempt", (attemptNumber) => {
      console.log(`🔄 Reconnection attempt ${attemptNumber}...`);
    });

    // Reconnection failed
    socket.io.on("reconnect_failed", () => {
      console.error("❌ Reconnection failed after all attempts");
      
      if (reconnectToastId) {
        toast.dismiss(reconnectToastId);
      }
      
      toast.error(
        "Unable to connect. Please check your internet connection and refresh the page.",
        { duration: 10000 }
      );
    });

    // Successful reconnection
    socket.io.on("reconnect", (attemptNumber) => {
      console.log(`✅ Reconnected after ${attemptNumber} attempts`);
    });

    // Server confirmation
    socket.on("connected", (data) => {
      console.log("✅ Socket connection confirmed:", data.sid);
    });

    // Error event from server
    socket.on("error", (error) => {
      console.error("❌ Socket error from server:", error);
      toast.error(error.message || "A server error occurred", { duration: 5000 });
    });
  }

  return socket;
};

/**
 * Set current user for room rejoining after reconnects
 */
export const setSocketUser = (user) => {
  currentUser = user;
  isManualDisconnect = false;
  console.log("👤 Socket user set:", user?.id);
};

/**
 * Clear socket user (on logout)
 */
export const clearSocketUser = () => {
  currentUser = null;
  currentRooms.clear();
  isManualDisconnect = true;
  console.log("👤 Socket user cleared");
};

/**
 * Join a league room
 */
export const joinLeagueRoom = (leagueId) => {
  const socket = getSocket();
  console.log("🟦 Joining league room:", leagueId);
  socket.emit("join_league", { leagueId });
  currentRooms.add(`league_${leagueId}`);
};

/**
 * Leave a league room
 */
export const leaveLeagueRoom = (leagueId) => {
  const socket = getSocket();
  console.log("🟦 Leaving league room:", leagueId);
  socket.emit("leave_league", { leagueId });
  currentRooms.delete(`league_${leagueId}`);
};

/**
 * Join an auction room
 */
export const joinAuctionRoom = (auctionId) => {
  const socket = getSocket();
  console.log("🟧 Joining auction room:", auctionId);
  socket.emit("join_auction", { auctionId });
  currentRooms.add(`auction_${auctionId}`);
};

/**
 * Leave an auction room
 */
export const leaveAuctionRoom = (auctionId) => {
  const socket = getSocket();
  console.log("🟧 Leaving auction room:", auctionId);
  // Note: No leave event needed, socket will disconnect or join other rooms
  currentRooms.delete(`auction_${auctionId}`);
};

/**
 * Check if socket is currently connected
 */
export const isSocketConnected = () => {
  return socket?.connected || false;
};

/**
 * Manually disconnect socket (for cleanup)
 */
export const disconnectSocket = () => {
  if (socket) {
    isManualDisconnect = true;
    socket.disconnect();
    socket = null;
    currentRooms.clear();
    console.log("🔌 Socket manually disconnected");
  }
};
