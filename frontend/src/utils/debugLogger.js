/**
 * Debug Logger for Auction Bidding
 * Captures all bid-related events for post-auction analysis
 */

class DebugLogger {
  constructor() {
    this.logs = [];
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

  getBidLogs() {
    return this.logs.filter(log => 
      log.event.includes('bid:') || 
      log.event === 'auction_start' ||
      log.event === 'auction_complete'
    );
  }

  getStats() {
    const bidLogs = this.getBidLogs();
    const attempts = bidLogs.filter(l => l.event === 'bid:attempt').length;
    const sent = bidLogs.filter(l => l.event === 'bid:sent').length;
    const successes = bidLogs.filter(l => l.event === 'bid:success').length;
    const errors = bidLogs.filter(l => l.event === 'bid:error').length;
    const rateLimited = bidLogs.filter(l => l.event === 'bid:rate_limited').length;
    
    return {
      totalAttempts: attempts,
      totalSent: sent,
      totalSuccesses: successes,
      totalErrors: errors,
      rateLimited,
      successRate: attempts > 0 ? ((successes / attempts) * 100).toFixed(1) + '%' : '0%',
      networkSuccessRate: sent > 0 ? ((successes / sent) * 100).toFixed(1) + '%' : '0%'
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
      events: this.getBidLogs(),
      allLogs: this.logs
    };
    
    return report;
  }

  downloadReport() {
    const report = this.generateReport();
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
    this.sessionStart = new Date().toISOString();
  }
}

// Export singleton instance
export const debugLogger = new DebugLogger();
