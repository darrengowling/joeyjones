import { useEffect, useRef, useState, useCallback } from "react";

export function useAuctionClock(socket, lotId) {
  const [remainingMs, setRemainingMs] = useState(null);
  const [endsAt, setEndsAt] = useState(null);
  const seqRef = useRef(0);
  const skewRef = useRef(0); // serverNow - clientNow
  const rafRef = useRef(null);

  const apply = useCallback((t) => {
    if (!t || (lotId && t.lotId !== lotId)) return;
    if (t.seq < seqRef.current) return; // ignore stale
    seqRef.current = t.seq;
    const clientNow = Date.now();
    skewRef.current = t.serverNow - clientNow;
    setEndsAt(t.endsAt);
  }, [lotId]);

  const onSync = useCallback((data) => {
    if (data.timer) {
      apply(data.timer);
    }
  }, [apply]);

  const onTick = useCallback((t) => apply(t), [apply]);
  const onAnti = useCallback((t) => apply(t), [apply]);
  const onSold = useCallback(() => { 
    seqRef.current = 0; 
    setEndsAt(null); 
    setRemainingMs(0); 
  }, []);

  useEffect(() => {
    if (socket) {
      // Remove existing listeners before adding new ones (prevent duplicates)
      socket.off("sync_state", onSync);
      socket.off("tick", onTick);
      socket.off("anti_snipe", onAnti);
      socket.off("sold", onSold);

      // Add listeners
      socket.on("sync_state", onSync);
      socket.on("tick", onTick);
      socket.on("anti_snipe", onAnti);
      socket.on("sold", onSold);

      function loop() {
        if (endsAt) {
          const clientNow = Date.now();
          const serverAlignedNow = clientNow + skewRef.current;
          const ms = Math.max(0, endsAt - serverAlignedNow);
          setRemainingMs(ms);
        }
        rafRef.current = window.requestAnimationFrame(loop);
      }
      rafRef.current = window.requestAnimationFrame(loop);

      return () => {
        socket.off("sync_state", onSync);
        socket.off("tick", onTick);
        socket.off("anti_snipe", onAnti);
        socket.off("sold", onSold);
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
      };
    } else {
      // Clean up RAF even if no socket
      return () => {
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
      };
    }
  }, [socket, lotId, endsAt, onSync, onTick, onAnti, onSold]);

  return { remainingMs };
}