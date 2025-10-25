import { useEffect, useState, useRef } from 'react';
import { getSocket, setSocketUser } from '../utils/socket';

// Track active listeners globally for debugging
const activeListeners = new Map();

/**
 * Shared Socket.IO room management hook
 * Handles room joining/leaving, reconnection, and readiness tracking
 * 
 * @param {string} roomType - Type of room: 'league' or 'auction'
 * @param {string} roomId - ID of the room (leagueId or auctionId)
 * @param {object} options - Optional configuration
 * @returns {object} { socket, connected, ready, readyPromise }
 */
export function useSocketRoom(roomType, roomId, options = {}) {
  const [connected, setConnected] = useState(false);
  const [ready, setReady] = useState(false);
  const readyResolveRef = useRef(null);
  const readyPromiseRef = useRef(null);
  const listenerCountRef = useRef(0);

  // Create ready promise that resolves after first sync
  if (!readyPromiseRef.current) {
    readyPromiseRef.current = new Promise((resolve) => {
      readyResolveRef.current = resolve;
    });
  }

  useEffect(() => {
    const socket = getSocket();
    const roomKey = `${roomType}:${roomId}`;

    // Set user for reconnection if provided
    if (options.user) {
      setSocketUser(options.user);
    }

    console.log(`🏠 [useSocketRoom] Joining ${roomKey}`);
    
    // Track this hook instance
    const hookId = `${roomKey}-${Date.now()}`;
    activeListeners.set(hookId, { roomKey, timestamp: Date.now() });
    
    // Log active listener count
    const activeCount = Array.from(activeListeners.values())
      .filter(l => l.roomKey === roomKey).length;
    console.log(`📊 [useSocketRoom] Active listeners for ${roomKey}: ${activeCount}`);
    listenerCountRef.current = activeCount;

    // Join room
    const joinRoom = () => {
      if (roomType === 'league') {
        socket.emit('join_league', { leagueId: roomId });
      } else if (roomType === 'auction') {
        socket.emit('join_auction', { auctionId: roomId });
        // Request sync_state for auctions
        socket.emit('sync_state', { auctionId: roomId });
      }
    };

    // Handle connection state
    const handleConnect = () => {
      console.log(`✅ [useSocketRoom] Socket connected for ${roomKey}`);
      setConnected(true);
      setReady(false); // Reset ready state on reconnect
      joinRoom();
    };

    const handleDisconnect = () => {
      console.log(`❌ [useSocketRoom] Socket disconnected for ${roomKey}`);
      setConnected(false);
      setReady(false);
    };

    // Handle sync_state for auction rooms (marks as ready)
    const handleSyncState = (data) => {
      if (roomType === 'auction' && data.auction?.id === roomId) {
        console.log(`🔄 [useSocketRoom] Sync state received for ${roomKey} - marking as ready`);
        setReady(true);
        if (readyResolveRef.current) {
          readyResolveRef.current();
          readyResolveRef.current = null; // Only resolve once
        }
      }
    };

    // Handle auction_snapshot for auction rooms (also marks as ready)
    const handleAuctionSnapshot = (data) => {
      if (roomType === 'auction') {
        console.log(`📸 [useSocketRoom] Auction snapshot received for ${roomKey} - marking as ready`);
        setReady(true);
        if (readyResolveRef.current) {
          readyResolveRef.current();
          readyResolveRef.current = null; // Only resolve once
        }
      }
    };

    // Handle room_joined for league rooms (marks as ready)
    const handleRoomJoined = (data) => {
      if (roomType === 'league' && data.leagueId === roomId) {
        console.log(`🔄 [useSocketRoom] Room joined confirmation for ${roomKey} - marking as ready`);
        setReady(true);
        if (readyResolveRef.current) {
          readyResolveRef.current();
          readyResolveRef.current = null;
        }
      }
    };

    // Register event listeners
    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    
    if (roomType === 'auction') {
      socket.on('sync_state', handleSyncState);
      socket.on('auction_snapshot', handleAuctionSnapshot);
    } else if (roomType === 'league') {
      socket.on('room_joined', handleRoomJoined);
    }

    // Initial join if already connected
    if (socket.connected) {
      setConnected(true);
      joinRoom();
    }

    // Cleanup on unmount
    return () => {
      console.log(`🧹 [useSocketRoom] Cleaning up ${roomKey}`);
      
      // Remove from active listeners
      activeListeners.delete(hookId);
      const remainingCount = Array.from(activeListeners.values())
        .filter(l => l.roomKey === roomKey).length;
      console.log(`📊 [useSocketRoom] Remaining listeners for ${roomKey}: ${remainingCount}`);

      // Leave room
      if (roomType === 'league') {
        socket.emit('leave_league', { leagueId: roomId });
      } else if (roomType === 'auction') {
        socket.emit('leave_auction', { auctionId: roomId });
      }

      // Clean up event listeners
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      
      if (roomType === 'auction') {
        socket.off('sync_state', handleSyncState);
        socket.off('auction_snapshot', handleAuctionSnapshot);
      } else if (roomType === 'league') {
        socket.off('room_joined', handleRoomJoined);
      }
    };
  }, [roomType, roomId, options.user]);

  return {
    socket: getSocket(),
    connected,
    ready,
    readyPromise: readyPromiseRef.current,
    listenerCount: listenerCountRef.current
  };
}

/**
 * Get current listener statistics for debugging
 */
export function getListenerStats() {
  const stats = {};
  activeListeners.forEach((value, key) => {
    const roomKey = value.roomKey;
    stats[roomKey] = (stats[roomKey] || 0) + 1;
  });
  return stats;
}
