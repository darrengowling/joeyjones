import { useEffect, useRef, useState } from "react";

type Tick = { lotId: string; seq: number; endsAt: number; serverNow: number };

export function useAuctionClock(socket: any, lotId: string | null) {
  const [remainingMs, setRemainingMs] = useState<number | null>(null);
  const [endsAt, setEndsAt] = useState<number | null>(null);
  const seqRef = useRef(0);
  const skewRef = useRef(0); // serverNow - clientNow
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    function apply(t: Tick) {
      if (!t || (lotId && t.lotId !== lotId)) return;
      if (t.seq < seqRef.current) return; // ignore stale
      seqRef.current = t.seq;
      const clientNow = Date.now();
      skewRef.current = t.serverNow - clientNow;
      setEndsAt(t.endsAt);
    }

    const onSync = (data: any) => {
      if (data.timer) {
        apply(data.timer);
      }
    };
    const onTick = (t: Tick) => apply(t);
    const onAnti = (t: Tick) => apply(t);
    const onSold = () => { 
      seqRef.current = 0; 
      setEndsAt(null); 
      setRemainingMs(0); 
    };

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
  }, [socket, lotId, endsAt]);

  return { remainingMs };
}