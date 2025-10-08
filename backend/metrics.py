# backend/metrics.py
import os
from prometheus_client import Counter, Histogram, Gauge
import logging

logger = logging.getLogger(__name__)

ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"

# Bid processing metrics
BID_ACCEPTED = Counter("bids_accepted_total", "Total accepted bids", ["auction_id"])
BID_REJECTED = Counter("bids_rejected_total", "Total rejected bids", ["reason"])
BID_LATENCY  = Histogram("bid_latency_seconds", "Bid processing latency in seconds")

# Timer and auction metrics
TIMER_TICKS  = Counter("timer_ticks_total", "Emitted timer_update events", ["auction_id"])
AUCTION_STARTED = Counter("auctions_started_total", "Total auctions started")
AUCTION_COMPLETED = Counter("auctions_completed_total", "Total auctions completed", ["reason"])

# Socket.IO connection metrics
SOCKET_CONN  = Counter("socket_connections_total", "Socket connections")
SOCKET_DISC  = Counter("socket_disconnects_total", "Socket disconnections")
ACTIVE_CONNECTIONS = Gauge("socket_active_connections", "Currently active socket connections")

# League and participant metrics
LEAGUES_CREATED = Counter("leagues_created_total", "Total leagues created", ["sport"])
PARTICIPANTS_JOINED = Counter("participants_joined_total", "Total participants joined")

# API endpoint metrics
API_REQUESTS = Counter("api_requests_total", "Total API requests", ["method", "endpoint", "status"])
API_LATENCY = Histogram("api_request_duration_seconds", "API request duration", ["method", "endpoint"])

# Rate limiting metrics
RATE_LIMITED_REQUESTS = Counter("rate_limited_requests_total", "Total rate limited requests", ["endpoint"])

if ENABLE_METRICS:
    logger.info("✅ Prometheus metrics enabled")
else:
    logger.info("📝 Prometheus metrics disabled")

def increment_bid_accepted(auction_id: str):
    """Increment bid accepted counter"""
    if ENABLE_METRICS:
        BID_ACCEPTED.labels(auction_id=auction_id).inc()

def increment_bid_rejected(reason: str):
    """Increment bid rejected counter"""
    if ENABLE_METRICS:
        BID_REJECTED.labels(reason=reason).inc()

def observe_bid_latency(latency: float):
    """Record bid processing latency"""
    if ENABLE_METRICS:
        BID_LATENCY.observe(latency)

def increment_timer_tick(auction_id: str):
    """Increment timer tick counter"""
    if ENABLE_METRICS:
        TIMER_TICKS.labels(auction_id=auction_id).inc()

def increment_socket_connection():
    """Increment socket connection counter"""
    if ENABLE_METRICS:
        SOCKET_CONN.inc()
        ACTIVE_CONNECTIONS.inc()

def increment_socket_disconnection():
    """Increment socket disconnection counter"""
    if ENABLE_METRICS:
        SOCKET_DISC.inc()
        ACTIVE_CONNECTIONS.dec()

def increment_league_created(sport: str):
    """Increment league creation counter"""
    if ENABLE_METRICS:
        LEAGUES_CREATED.labels(sport=sport).inc()

def increment_participant_joined():
    """Increment participant joined counter"""
    if ENABLE_METRICS:
        PARTICIPANTS_JOINED.inc()

def record_api_request(method: str, endpoint: str, status: int, duration: float):
    """Record API request metrics"""
    if ENABLE_METRICS:
        API_REQUESTS.labels(method=method, endpoint=endpoint, status=status).inc()
        API_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

def increment_rate_limited(endpoint: str):
    """Increment rate limited requests"""
    if ENABLE_METRICS:
        RATE_LIMITED_REQUESTS.labels(endpoint=endpoint).inc()