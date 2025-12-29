# Payment Integration Plan

**Last Updated:** December 13, 2025  
**Status:** PLANNING (Post-Pilot)  
**Purpose:** Capture requirements and architecture for competition entry fees

---

## Business Context

The platform will enable charitable fundraising through competition entry fees:
- Users pay to enter competitions
- Funds split between charity (90%) and platform (10%)
- **This is NOT gambling** - users do not receive winnings
- Charity partner already has Stripe enabled

---

## Confirmed Requirements

| Requirement | Detail | Status |
|-------------|--------|--------|
| Split ratio | 90% charity / 10% platform | ✅ Confirmed |
| Charity Stripe | Already enabled | ✅ Confirmed |
| Entry fee | Commissioner-set, variable options | ✅ Confirmed |
| Per-user variance | Same competition, different fees (£10 vs £5) | ✅ Confirmed |
| User winnings | None - not gambling | ✅ Confirmed |
| Regulatory | Researched, not gambling | ✅ Confirmed |
| Timeline | Post-pilot | ✅ Confirmed |

---

## Open Questions (Awaiting Answers)

| # | Question | Options | Answer |
|---|----------|---------|--------|
| 1 | Multiple charities? | Single charity across all, or per-competition selection | TBD |
| 2 | Refund policy | User leaves early? Competition cancelled? | TBD |
| 3 | Commissioner flexibility | Preset options only (£5/£10/£20) or custom amounts? | TBD |
| 4 | Free competitions | Still supported alongside paid? | TBD |
| 5 | Payment timing | Pay at join, or pay before auction starts? | TBD |

---

## Technical Architecture

### Stripe Connect Model

```
Your Platform (Stripe account)
    ↓
Connected Account: Charity (their existing Stripe)
    ↓
User pays £10 → Stripe splits automatically:
    → £9 direct to Charity
    → £1 to Platform
```

**Connect type:** "Destination charges" with automatic split - simplest model since charity already has Stripe.

---

### Data Model Changes

#### League Collection (new fields)

```javascript
{
  // Existing fields...
  
  // Payment configuration
  entryFeeEnabled: Boolean,            // true = paid competition
  entryFeeOptions: [Number],           // Array of amounts in pence, e.g., [500, 1000, 2000]
  entryFeeDefault: Number,             // Default selection in pence
  charityId: String,                   // Charity's Stripe Connected Account ID
  charitySplit: Number,                // Percentage to charity (default 90)
  platformSplit: Number                // Percentage to platform (default 10)
}
```

**Example:**
```javascript
{
  name: "Premier League Fantasy 2025",
  entryFeeEnabled: true,
  entryFeeOptions: [500, 1000, 2000],  // £5, £10, £20
  entryFeeDefault: 1000,               // £10
  charityId: "acct_xxxxx",
  charitySplit: 90,
  platformSplit: 10
}
```

#### LeagueParticipant Collection (new fields)

```javascript
{
  // Existing fields...
  
  // Payment tracking
  entryFeePaid: Number,                // Amount this user paid (pence)
  paymentStatus: String,               // "pending" | "paid" | "refunded" | "failed"
  stripePaymentId: String,             // Stripe PaymentIntent ID for refunds/audit
  paidAt: Date                         // When payment was confirmed
}
```

**Example:**
```javascript
{
  leagueId: "league_123",
  userId: "user_456",
  entryFeePaid: 1000,                  // £10
  paymentStatus: "paid",
  stripePaymentId: "pi_3abc123xyz",
  paidAt: "2025-01-15T10:00:00Z"
}
```

---

### User Flow

```
1. User clicks "Join Competition"
           ↓
2. System checks: entryFeeEnabled?
           ↓
   [No]  → Standard join flow (free)
   [Yes] → Continue to payment
           ↓
3. Show entry fee selection
   [ ] £5  [●] £10 (default)  [ ] £20
           ↓
4. Stripe Checkout / Payment Sheet opens
           ↓
5. User completes payment
           ↓
6. Stripe webhook confirms payment
           ↓
7. User added to league_participants with paymentStatus: "paid"
           ↓
8. User granted access to competition
```

---

### API Endpoints (New)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/leagues/{id}/payment/create` | Create Stripe PaymentIntent |
| POST | `/api/webhooks/stripe` | Handle Stripe payment webhooks |
| GET | `/api/leagues/{id}/payments` | List all payments (commissioner/admin) |
| POST | `/api/leagues/{id}/payments/{paymentId}/refund` | Process refund |

#### POST /api/leagues/{id}/payment/create

**Request:**
```json
{
  "amount": 1000,
  "userId": "user_456"
}
```

**Response:**
```json
{
  "clientSecret": "pi_xxx_secret_xxx",
  "paymentIntentId": "pi_xxx"
}
```

#### POST /api/webhooks/stripe

Handles:
- `payment_intent.succeeded` → Update participant paymentStatus to "paid"
- `payment_intent.payment_failed` → Update paymentStatus to "failed"
- `charge.refunded` → Update paymentStatus to "refunded"

---

### Frontend Components (New/Modified)

| Component | Changes |
|-----------|---------|
| `CreateLeague.js` | Add entry fee configuration section |
| `LeagueDetail.js` | Show entry fee before join, payment flow |
| `JoinLeagueModal.js` (new) | Fee selection + Stripe payment UI |
| `PaymentsDashboard.js` (new) | Commissioner view of all payments |

---

### Implementation Phases

#### Phase 1: Stripe Connect Setup
- Platform Stripe account setup
- Connect charity's existing Stripe account
- Test destination charges in Stripe test mode

#### Phase 2: Backend Implementation
- Database schema updates
- Payment create endpoint
- Webhook handler
- Refund endpoint
- Join flow modification (block without payment)

#### Phase 3: Frontend Implementation
- Commissioner UI for fee configuration
- User payment flow at join
- Stripe Elements / Checkout integration
- Payment confirmation UI

#### Phase 4: Admin & Reporting
- Payments dashboard for commissioners
- Admin overview across all competitions
- Export functionality for accounting

#### Phase 5: Testing
- End-to-end payment flow testing
- Refund flow testing
- Edge cases (failed payments, duplicate attempts)
- Stripe test mode → live mode transition

---

### Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1: Stripe Connect | 2-3 hours |
| Phase 2: Backend | 6-8 hours |
| Phase 3: Frontend | 6-8 hours |
| Phase 4: Admin | 4-6 hours |
| Phase 5: Testing | 4-6 hours |
| **Total** | **22-31 hours** |

---

### Dependencies

| Dependency | Status |
|------------|--------|
| Platform Stripe account | TBD |
| Charity Stripe Connected Account ID | TBD (they have Stripe, need to connect) |
| Stripe API keys (test + live) | TBD |

---

### Security Considerations

1. **Webhook verification** - Verify Stripe webhook signatures
2. **Payment intent validation** - Server-side amount validation
3. **Idempotency** - Prevent duplicate charges
4. **PCI compliance** - Use Stripe Elements (no raw card data touches our servers)
5. **Audit trail** - Store all payment events for reconciliation

---

### Stripe Resources

- [Stripe Connect: Destination Charges](https://stripe.com/docs/connect/destination-charges)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe Elements (React)](https://stripe.com/docs/stripe-js/react)

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| Dec 13, 2025 | Initial planning document created | Agent |

---

**Next Steps:**
1. Answer open questions above
2. Confirm Stripe account setup approach
3. Schedule implementation post-pilot
