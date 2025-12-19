/**
 * Debug Logger for Auction Bidding
 * Captures all bid-related events AND socket events for post-auction analysis
 */

class DebugLogger {
  constructor() {
    this.logs = [];
    this.socketEvents = [];
    this.sessionStart = new Date().toISOString();
    this.auctionId = null;
  }

  setAuctionId(auctionId) {
    this.auctionId = auctionId;
  }

  log(event, data) {
    const entry = {
      timestamp: new Date().toISOString(),
      timestampMs: Date.now(),
      event,
      auctionId: this.auctionId,
      ...data
    };
    
    this.logs.push(entry);
    
    // Keep only last 500 entries to prevent memory issues
    if (this.logs.length > 500) {
      this.logs.shift();
    }
  }

  // NEW: Log socket events for debugging
  logSocketEvent(eventName, data) {
    const entry = {
      timestamp: new Date().toISOString(),
      timestampMs: Date.now(),
      eventName,
      auctionId: this.auctionId,
      data: this.sanitizeData(data)
    };
    
    this.socketEvents.push(entry);
    
    // Keep only last 200 socket events
    if (this.socketEvents.length > 200) {
      this.socketEvents.shift();
    }
  }

  // Sanitize data to avoid circular references
  sanitizeData(data) {
    try {
      return JSON.parse(JSON.stringify(data));
    } catch {
      return { error: 'Could not serialize data' };
    }
  }

  getBidLogs() {
    return this.logs.filter(log => 
      log.event.includes('bid:') || 
      log.event === 'auction_start' ||
      log.event === 'auction_complete'
    );
  }

  getSocketEvents() {
    return this.socketEvents;
  }

  getStats() {
    const bidLogs = this.getBidLogs();
    const attempts = bidLogs.filter(l => l.event === 'bid:attempt').length;
    const sent = bidLogs.filter(l => l.event === 'bid:sent').length;
    const successes = bidLogs.filter(l => l.event === 'bid:success').length;
    const errors = bidLogs.filter(l => l.event === 'bid:error').length;
    const rateLimited = bidLogs.filter(l => l.event === 'bid:rate_limited').length;
    
    // Socket event stats
    const socketStats = {};
    this.socketEvents.forEach(e => {
      socketStats[e.eventName] = (socketStats[e.eventName] || 0) + 1;
    });
    
    return {
      totalAttempts: attempts,
      totalSent: sent,
      totalSuccesses: successes,
      totalErrors: errors,
      rateLimited,
      successRate: attempts > 0 ? ((successes / attempts) * 100).toFixed(1) + '%' : '0%',
      networkSuccessRate: sent > 0 ? ((successes / sent) * 100).toFixed(1) + '%' : '0%',
      socketEventsReceived: this.socketEvents.length,
      socketEventsByType: socketStats
    };
  }

  getErrorSummary() {
    const errorLogs = this.logs.filter(l => l.event === 'bid:error');
    const errorTypes = {};
    
    errorLogs.forEach(log => {
      const errorType = log.status || log.code || 'unknown';
      errorTypes[errorType] = (errorTypes[errorType] || 0) + 1;
    });
    
    return errorTypes;
  }

  generateReport() {
    const report = {
      metadata: {
        sessionStart: this.sessionStart,
        reportGenerated: new Date().toISOString(),
        auctionId: this.auctionId,
        userAgent: navigator.userAgent,
        screenSize: `${window.screen.width}x${window.screen.height}`,
        connection: navigator.connection ? {
          effectiveType: navigator.connection.effectiveType,
          downlink: navigator.connection.downlink,
          rtt: navigator.connection.rtt
        } : 'unknown'
      },
      statistics: this.getStats(),
      errorSummary: this.getErrorSummary(),
      bidEvents: this.getBidLogs(),
      socketEvents: this.getSocketEvents(),
      allLogs: this.logs,
      // Instructions for getting server-side data
      serverDebugInstructions: {
        note: "To get full server-side state, call these endpoints:",
        auctionState: this.auctionId 
          ? `/api/debug/auction-state/${this.auctionId}`
          : "/api/debug/auction-state/{auction_id}",
        bidLogs: this.auctionId
          ? `/api/debug/bid-logs/${this.auctionId}`
          : "/api/debug/bid-logs/{auction_id}"
      }
    };
    
    return report;
  }

  async downloadReport() {
    const report = this.generateReport();
    
    // Fetch server-side state if auction ID is available
    if (this.auctionId) {
      try {
        const API_URL = process.env.REACT_APP_BACKEND_URL || '';
        const response = await fetch(`${API_URL}/api/debug/auction-state/${this.auctionId}`);
        if (response.ok) {
          const serverState = await response.json();
          report.serverState = serverState;
          report.serverStateFetched = true;
        } else {
          report.serverState = null;
          report.serverStateFetched = false;
          report.serverStateError = `HTTP ${response.status}: ${response.statusText}`;
        }
      } catch (error) {
        report.serverState = null;
        report.serverStateFetched = false;
        report.serverStateError = error.message;
      }
    } else {
      report.serverState = null;
      report.serverStateFetched = false;
      report.serverStateError = 'No auction ID available';
    }
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `auction-debug-${this.auctionId || 'unknown'}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  clear() {
    this.logs = [];
    this.socketEvents = [];
    this.sessionStart = new Date().toISOString();
  }
}

// Export singleton instance
export const debugLogger = new DebugLogger();
