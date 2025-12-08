# Socket.IO Debugging Plan

## Issue Summary
- Bids succeed via REST API (HTTP 200)
- But Socket.IO broadcast events (`bid_update`, `bid_placed`) don't reach clients
- Frontend debug report shows NO Socket.IO events received after bid placement
- Multiple `auction_start` events suggest connection instability

## Verified Working
✅ Socket.IO endpoint accessible at `/api/socket.io/`
✅ REST API for bids working correctly
✅ Backend correctly emits to room `auction:{auctionId}`
✅ Frontend correctly joins room via `join_auction` event

## Suspected Issues
1. **Socket disconnecting during bid** - Client loses connection between bid placement and broadcast
2. **Room not properly joined** - Socket joins room but something clears it
3. **Event emission timing** - Broadcast happens before all clients are ready
4. **Multiple socket instances** - Client creating multiple connections causing confusion

## Next Debug Steps
1. Enable detailed Socket.IO logging (DONE - logger=True, engineio_logger=True)
2. Test with a real auction and monitor backend logs for:
   - Client connection/disconnection events
   - Room join confirmations
   - Bid emission logs with room size
3. Check if Socket.IO events are being emitted at all
4. Verify room membership at time of bid placement

