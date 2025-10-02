import { useEffect, useRef, useState } from "react";

export function useAuctionClock(socket, lotId) {
  const [remainingMs, setRemainingMs] = useState(null);
  const [endsAt, setEndsAt] = useState(null);
  const seqRef = useRef(0);
  const skewRef = useRef(0); // serverNow - clientNow
  const rafRef = useRef(null);

  useEffect(() => {
    function apply(t) {
      if (!t || (lotId && t.lotId !== lotId)) return;
      if (t.seq < seqRef.current) return; // ignore stale
      seqRef.current = t.seq;
      const clientNow = Date.now();
      skewRef.current = t.serverNow - clientNow;
      setEndsAt(t.endsAt);
    }

    const onSync = (data) => {
      if (data.timer) {
        apply(data.timer);
      }
    };
    const onTick = (t) => apply(t);
    const onAnti = (t) => apply(t);
    const onSold = () => { 
      seqRef.current = 0; 
      setEndsAt(null); 
      setRemainingMs(0); 
    };

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
    }
  }, [socket, lotId, endsAt]);

  return { remainingMs };
}