# Sport X Design Specification

**Version:** 1.0  
**Created:** January 2026  
**Purpose:** Single source of truth for UI redesign implementation  
**Status:** REFERENCE ONLY - No code changes until migration complete

---

## Table of Contents
1. [Design Overview](#design-overview)
2. [Color Palette](#color-palette)
3. [Typography](#typography)
4. [Spacing & Layout](#spacing--layout)
5. [Components](#components)
6. [Page Specifications](#page-specifications)
7. [Effects & Animations](#effects--animations)
8. [Icons](#icons)
9. [Implementation Notes](#implementation-notes)

---

## Design Overview

### Design Philosophy
- **Mobile-first**: All screens designed for ~390px width (iPhone 14 Pro equivalent)
- **Dark theme**: Deep navy backgrounds with cyan accents
- **Glassmorphism**: Frosted glass card effects throughout
- **Stadium atmosphere**: Subtle ambient glows suggesting sports arena lighting
- **Accessibility**: High contrast text, clear hierarchy

### Key Characteristics
| Aspect | Description |
|--------|-------------|
| Primary aesthetic | Dark, premium, sports-tech |
| Card style | Glassmorphism with subtle borders |
| Button style | Pill-shaped (fully rounded) |
| Navigation | Bottom nav bar (5 items) |
| Corners | Large radius (16-24px) |
| Depth | Layered cards with shadows and glows |

---

## Color Palette

### Primary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Background Dark** | `#0A1628` | rgb(10, 22, 40) | Main app background |
| **Background Card** | `#0D1E30` | rgb(13, 30, 48) | Card backgrounds |
| **Cyan Primary** | `#00D4FF` | rgb(0, 212, 255) | Primary accent, CTAs, highlights |
| **Cyan Glow** | `#00D4FF40` | rgba(0, 212, 255, 0.25) | Glow effects, active states |

### Secondary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| **Orange Timer** | `#FF6B35` | rgb(255, 107, 53) | Countdown timers, urgency |
| **Red Danger** | `#DC3545` | rgb(220, 53, 69) | Pass button, negative actions |
| **Green Online** | `#00FF88` | rgb(0, 255, 136) | Online indicators, success |
| **Gold Trophy** | `#FFD700` | rgb(255, 215, 0) | Winner badges, 1st place |
| **Silver Trophy** | `#C0C0C0` | rgb(192, 192, 192) | 2nd place |
| **Bronze Trophy** | `#CD7F32` | rgb(205, 127, 50) | 3rd place |

### Text Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Text Primary** | `#FFFFFF` | Headings, important text |
| **Text Secondary** | `#8899AA` | Subtext, labels, muted content |
| **Text Cyan** | `#00D4FF` | Accent text, links, highlights |

### Border Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Border Default** | `#1A3A5C` | Card borders, dividers |
| **Border Glow** | `#00D4FF30` | Glowing borders on active elements |
| **Border Input** | `#2A4A6C` | Form input borders |

### Gradient Definitions

```css
/* Hero card gradient overlay */
.hero-gradient {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, transparent 50%);
}

/* Bottom nav gradient */
.nav-gradient {
  background: linear-gradient(180deg, transparent 0%, #0A1628 100%);
}
```

---

## Typography

### Font Family

**Primary Font:** Space Grotesk  
**Fallback:** system-ui, -apple-system, sans-serif

```css
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
  --font-primary: 'Space Grotesk', system-ui, -apple-system, sans-serif;
}
```

### Type Scale

| Element | Size | Weight | Line Height | Letter Spacing | Usage |
|---------|------|--------|-------------|----------------|-------|
| **H1 - Hero** | 32px | 700 | 1.2 | -0.02em | Page titles, hero text |
| **H2 - Section** | 24px | 600 | 1.3 | -0.01em | Section headers |
| **H3 - Card Title** | 20px | 600 | 1.3 | 0 | Card titles |
| **Body Large** | 18px | 500 | 1.4 | 0 | Important body text |
| **Body** | 16px | 400 | 1.5 | 0 | Default body text |
| **Body Small** | 14px | 400 | 1.4 | 0 | Secondary text |
| **Caption** | 12px | 500 | 1.3 | 0.05em | Labels, captions (often uppercase) |
| **Overline** | 10px | 600 | 1.2 | 0.15em | Category labels (uppercase) |

### Special Typography

| Style | Properties | Usage |
|-------|------------|-------|
| **Stat Number** | 48px, 700 weight | Large statistics (142, 28, etc.) |
| **Timer** | 48px, 700 weight, tabular nums | Countdown clock (00:24) |
| **Currency** | 36px, 700 weight | Bid amounts (£15m) |
| **Badge** | 10px, 600 weight, uppercase | "LEGENDARY", "WINNER '24" |

---

## Spacing & Layout

### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | 4px | Tight gaps, icon padding |
| `--space-sm` | 8px | Between related elements |
| `--space-md` | 16px | Standard padding, gaps |
| `--space-lg` | 24px | Section spacing |
| `--space-xl` | 32px | Large section gaps |
| `--space-2xl` | 48px | Page sections |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 8px | Small elements, tags |
| `--radius-md` | 12px | Buttons, inputs |
| `--radius-lg` | 16px | Cards |
| `--radius-xl` | 24px | Large cards, modals |
| `--radius-full` | 9999px | Pill buttons, avatars |

### Layout Grid

- **Container max-width:** 430px (mobile-first)
- **Side padding:** 16px
- **Content width:** 398px (430 - 32)
- **Card gap:** 16px
- **Bottom nav height:** 80px
- **Safe area bottom:** 34px (for notch devices)

---

## Components

### 1. Glass Card

The primary container component used throughout the app.

```
┌─────────────────────────────────────┐
│  [Content]                          │
│                                     │
└─────────────────────────────────────┘
```

**Properties:**
| Property | Value |
|----------|-------|
| Background | `rgba(13, 30, 48, 0.8)` |
| Border | `1px solid rgba(26, 58, 92, 0.5)` |
| Border Radius | 16px |
| Backdrop Filter | `blur(12px)` |
| Padding | 20px |
| Box Shadow | `0 4px 24px rgba(0, 0, 0, 0.3)` |

**Variants:**
- **Default:** Standard glass effect
- **Highlighted:** Cyan border glow (`box-shadow: 0 0 20px rgba(0, 212, 255, 0.2)`)
- **Interactive:** Hover state with slight lift

---

### 2. Primary Button (CTA)

Pill-shaped cyan button for primary actions.

```
┌───────────────────────────────┐
│    Send Magic Link  ⚡        │
└───────────────────────────────┘
```

**Properties:**
| Property | Value |
|----------|-------|
| Background | `#00D4FF` |
| Text Color | `#0A1628` (dark) |
| Font | 16px, 600 weight |
| Padding | 16px 32px |
| Border Radius | 9999px (pill) |
| Text Transform | uppercase |
| Letter Spacing | 0.05em |

**States:**
- **Hover:** `background: #00BFEA`, slight scale(1.02)
- **Active:** `background: #00A8D4`, scale(0.98)
- **Disabled:** `opacity: 0.5`, no pointer events

---

### 3. Secondary Button

Outline style for secondary actions.

```
┌───────────────────────────────┐
│      JOIN COMPETITION         │
└───────────────────────────────┘
```

**Properties:**
| Property | Value |
|----------|-------|
| Background | `transparent` |
| Border | `2px solid #1A3A5C` |
| Text Color | `#FFFFFF` |
| Font | 16px, 600 weight |
| Padding | 14px 32px |
| Border Radius | 9999px |
| Text Transform | uppercase |

**States:**
- **Hover:** `border-color: #00D4FF`, `color: #00D4FF`

---

### 4. Bid Increment Buttons

Three-button row for auction bidding.

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│  +£1m    │  │  +£5m    │  │  +£10m   │
└──────────┘  └──────────┘  └──────────┘
  (outline)     (outline)     (filled)
```

**Properties:**
| Property | Default | Active (rightmost) |
|----------|---------|-------------------|
| Background | `transparent` | `#00D4FF` |
| Border | `2px solid #1A3A5C` | `none` |
| Text Color | `#FFFFFF` | `#0A1628` |
| Padding | 16px 24px | 16px 24px |
| Border Radius | 12px | 12px |
| Font | 18px, 700 weight | 18px, 700 weight |

---

### 5. Pass Button

Full-width danger button for passing on a lot.

```
┌─────────────────────────────────────┐
│    🚫  PASS THIS ROUND              │
└─────────────────────────────────────┘
```

**Properties:**
| Property | Value |
|----------|-------|
| Background | `rgba(220, 53, 69, 0.2)` |
| Border | `2px solid #DC3545` |
| Text Color | `#DC3545` |
| Font | 16px, 600 weight |
| Padding | 16px |
| Border Radius | 12px |
| Text Transform | uppercase |

---

### 6. Bottom Navigation

Fixed bottom nav with 5 items + floating center action.

```
┌─────────────────────────────────────┐
│  🏠    📊    [+]    👥    ⚙️       │
│ HOME  STATS       SOCIAL PROFILE   │
└─────────────────────────────────────┘
```

**Container Properties:**
| Property | Value |
|----------|-------|
| Background | `rgba(10, 22, 40, 0.95)` |
| Backdrop Filter | `blur(20px)` |
| Height | 80px |
| Border Top | `1px solid rgba(26, 58, 92, 0.5)` |
| Padding Bottom | 34px (safe area) |

**Nav Item Properties:**
| State | Icon Color | Label Color |
|-------|------------|-------------|
| Default | `#8899AA` | `#8899AA` |
| Active | `#00D4FF` | `#00D4FF` |

**Center Action Button:**
| Property | Value |
|----------|-------|
| Size | 56px × 56px |
| Background | `#00D4FF` |
| Icon | Plus (+), black |
| Border Radius | 50% |
| Box Shadow | `0 4px 20px rgba(0, 212, 255, 0.4)` |
| Position | Floating above nav (-28px) |
| Border | `4px solid #0A1628` |

---

### 7. Input Field

Text input with dark styling.

```
┌─────────────────────────────────────┐
│  your.email@example.com             │
└─────────────────────────────────────┘
```

**Properties:**
| Property | Value |
|----------|-------|
| Background | `rgba(10, 22, 40, 0.8)` |
| Border | `1px solid #2A4A6C` |
| Text Color | `#FFFFFF` |
| Placeholder Color | `#8899AA` |
| Padding | 16px 20px |
| Border Radius | 12px |
| Font | 16px, 400 weight |

**States:**
- **Focus:** `border-color: #00D4FF`, `box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.2)`

---

### 8. Avatar

User profile image with optional ring.

**Sizes:**
| Size | Dimensions | Border |
|------|------------|--------|
| Small | 32px | 2px |
| Medium | 48px | 2px |
| Large | 80px | 3px |
| XL (Profile) | 120px | 4px cyan glow |

**Properties:**
| Property | Value |
|----------|-------|
| Border Radius | 50% |
| Border | `2px solid #00D4FF` |
| Object Fit | cover |

---

### 9. Manager Badge (Active Managers Row)

Shows participating managers in auction.

```
┌──────────────────┐
│ [JD] Josh.D      │
└──────────────────┘
```

**Properties:**
| Property | Value |
|----------|-------|
| Background | `rgba(13, 30, 48, 0.8)` |
| Border | `1px solid #1A3A5C` |
| Border Radius | 9999px |
| Padding | 8px 16px |
| Avatar Size | 24px |
| Gap | 8px |

**States:**
- **Current User:** Border color `#00D4FF`
- **Leading Bidder:** Green dot indicator

---

### 10. Team Card (Auction Queue)

Small team thumbnail in horizontal scroll.

```
┌─────────┐
│  [logo] │
│ Chelsea │
└─────────┘
```

**Properties:**
| Property | Value |
|----------|-------|
| Width | 72px |
| Background | `rgba(255, 255, 255, 0.1)` |
| Border | `1px solid #1A3A5C` |
| Border Radius | 12px |
| Padding | 8px |
| Text | 12px, center-aligned |

**States:**
- **Active (on block):** Border `#00D4FF`, background glow

---

### 11. Trophy Shelf

Horizontal scrollable row of trophy icons.

```
🏆 🏆 🏆 🏆 🏆
(gold) (silver) (cyan) (bronze) (grey)
```

**Container:**
| Property | Value |
|----------|-------|
| Background | Glass card |
| Padding | 16px |
| Gap | 24px |
| Overflow | scroll-x, hidden scrollbar |

**Trophy Icon:**
| Property | Value |
|----------|-------|
| Size | 32px |
| Colors | Gold (#FFD700), Cyan (#00D4FF), Silver, Bronze, Grey |

---

### 12. Stat Card

Two-column stat display.

```
┌─────────────────┐  ┌─────────────────┐
│ 📈              │  │ 👥              │
│ TOTAL WINS      │  │ CLUBS OWNED     │
│ 142             │  │ 28              │
└─────────────────┘  └─────────────────┘
```

**Properties:**
| Property | Value |
|----------|-------|
| Background | Glass card |
| Border Radius | 16px |
| Padding | 20px |
| Icon | 24px, cyan |
| Label | 12px, uppercase, secondary color |
| Value | 36px, 700 weight, white |

---

### 13. Chat Bubble

Message bubbles for Banter Feed.

**Other User:**
```
┌──────────────────────────────┐
│ You really think he's worth  │
│ that much? 😏                │
└──────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Background | `rgba(13, 30, 48, 0.9)` |
| Border | `1px solid #1A3A5C` |
| Border Radius | 16px 16px 16px 4px |
| Padding | 12px 16px |
| Max Width | 80% |

**Current User:**
```
                ┌──────────────────────────────┐
                │ I have the budget, why not?  │
                │ 🚀                           │
                └──────────────────────────────┘
```

| Property | Value |
|----------|-------|
| Background | `#00D4FF` |
| Text Color | `#0A1628` |
| Border Radius | 16px 16px 4px 16px |
| Padding | 12px 16px |
| Max Width | 80% |
| Align | Right |

---

### 14. Quick Reply Pills

Horizontal scrollable quick responses.

```
[ Too expensive! 💸 ] [ My club now! 🏆 ] [ In your dreams! ]
```

**Properties:**
| Property | Value |
|----------|-------|
| Background | `rgba(13, 30, 48, 0.8)` |
| Border | `1px solid #1A3A5C` |
| Border Radius | 9999px |
| Padding | 8px 16px |
| Font | 14px |
| White Space | nowrap |

---

### 15. Countdown Timer

Large prominent timer display.

```
    ┌────────┐   ┌────────┐
    │   00   │ : │   24   │
    └────────┘   └────────┘
```

**Properties:**
| Property | Value |
|----------|-------|
| Background | `rgba(255, 107, 53, 0.2)` |
| Border | `2px solid #FF6B35` |
| Border Radius | 12px |
| Padding | 12px 20px |
| Font | 48px, 700 weight, tabular-nums |
| Color | `#FF6B35` |

**Behavior:**
- Normal (>10s): Orange color
- Urgent (<10s): Pulse animation
- Anti-snipe: Flash cyan briefly when extended

---

## Page Specifications

### Page 1: Sign In

**Header:**
- Back arrow (left)
- Logo "SPORT X" (center)
- No right element

**Content:**
- Glass card containing:
  - H1: "Enter Your Details"
  - Subtitle: "Welcome back. Join the action in seconds."
  - Label: "Email Address"
  - Input field
  - Primary button: "Send Magic Link ⚡"
  - Security note with lock icon

**Footer:**
- "Need help? Contact Support" link

**Background:**
- Subtle radial glow in bottom-right (cyan, 20% opacity)

---

### Page 2: Home

**Header:**
- Logo icon (cyan lightning bolt in circle)
- "Sport X" text
- Search icon
- User avatar

**Hero Card:**
- Overline: "● LIVE AUCTION PLATFORM"
- H1: "Sports Gaming" / "with Friends" (cyan)
- Tagline: "No Gambling. All Game."
- Primary button: "CREATE COMPETITION"
- Secondary button: "JOIN COMPETITION"
- Diagonal gradient overlay

**Active Leagues Section:**
- Section header: "Active Leagues" + "VIEW ALL" link
- Empty state card:
  - Trophy icon (muted)
  - "No competitions yet"
  - Subtitle text
  - "Get Started" button

**Bottom Navigation:**
- HOME (active), STATS, [+], SOCIAL, PROFILE

---

### Page 3: Live Auction Room

**Header Bar:**
- "USER ROSTER 2/4" (left)
- "● LIVE AUCTION ROOM 04" (center)
- "BUDGET LEFT £235m" (right)

**Team Queue:**
- Horizontal scroll of team cards
- Active team highlighted

**Current Lot:**
- Large countdown timer (orange)
- Team logo watermark (faded background)
- Team name (H1)
- Next match info
- "CURRENT HIGHEST BID" label
- Bid amount (large cyan)
- Leading bidder indicator

**Active Managers:**
- "8 Online" count
- Horizontal scroll of manager badges

**Bid Controls:**
- Three increment buttons (+£1m, +£5m, +£10m)
- Pass button (full width, red)

**Bottom Navigation:**
- AUCTION (active), STATS, [+], WALLET, SETTINGS

---

### Page 4: Live Auction Banter

**Header:**
- Back arrow
- "Live Auction Banter" title
- "LEAGUE DIVISION A" subtitle
- Info icon (right)

**Current Lot Summary:**
- "PLAYER ON BLOCK" label
- Player name
- "CLOCK" label
- Countdown timer
- Current bid display
- Top bidder name

**Banter Feed:**
- Scrollable chat messages
- Bid event notifications (cyan bar)
- User messages (right-aligned, cyan)
- Other messages (left-aligned, dark)

**Quick Replies:**
- Horizontal scroll of pill buttons

**Message Input:**
- Input field with placeholder
- Send button (cyan circle with arrow)

---

### Page 5: Manager Profile (Hall of Fame)

**Header:**
- Settings icon (left)
- "HALL OF FAME" title
- Share icon (right)

**Profile Section:**
- Large avatar with cyan glow ring
- "LEGENDARY" badge
- Manager name (H1)
- Title: "ALL-TIME WIN LEADER"

**Trophy Shelf:**
- Glass card with horizontal scroll
- Trophy icons in various colors
- "12 LEAGUE TITLES SECURED" caption

**Career Stats:**
- Two-column stat cards
- "TOTAL WINS: 142"
- "CLUBS OWNED: 28"

**Record Stat:**
- Full-width card
- "RECORD BID PLACED: £142.5M"
- Decorative chart icon

**Trophy Room:**
- "TROPHY ROOM" header + "SEASON 24/25" filter
- Team cards showing wins:
  - Chelsea FC - "WINNER '24"
  - AC Milan - "FINALIST"

**View Past Campaigns:**
- Text link/button

**Bottom Navigation:**
- Different icons for profile context

---

## Effects & Animations

### Glassmorphism

```css
.glass {
  background: rgba(13, 30, 48, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(26, 58, 92, 0.5);
}
```

### Cyan Glow

```css
.glow-cyan {
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3),
              0 0 40px rgba(0, 212, 255, 0.1);
}
```

### Stadium Light Effect

```css
.stadium-light {
  position: relative;
}

.stadium-light::before {
  content: '';
  position: absolute;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.15) 0%, transparent 70%);
  pointer-events: none;
}
```

### Timer Pulse (Urgent)

```css
@keyframes timer-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
}

.timer-urgent {
  animation: timer-pulse 1s ease-in-out infinite;
}
```

### Button Press

```css
.btn:active {
  transform: scale(0.98);
  transition: transform 0.1s ease;
}
```

### Card Hover

```css
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  transition: all 0.2s ease;
}
```

### Bid Flash

```css
@keyframes bid-flash {
  0% { background-color: rgba(0, 212, 255, 0.3); }
  100% { background-color: transparent; }
}

.new-bid {
  animation: bid-flash 0.5s ease-out;
}
```

---

## Icons

### Icon Library
**Recommended:** Material Symbols (Outlined)

```html
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" rel="stylesheet">
```

### Icon Mapping

| Usage | Icon Name | Code |
|-------|-----------|------|
| Home | home | `<span class="material-symbols-outlined">home</span>` |
| Stats | bar_chart | `bar_chart` |
| Social | group | `group` |
| Profile | settings | `settings` |
| Wallet | account_balance_wallet | `account_balance_wallet` |
| Search | search | `search` |
| Back | chevron_left | `chevron_left` |
| Share | share | `share` |
| Info | info | `info` |
| Lock | lock | `lock` |
| Trophy | emoji_events | `emoji_events` |
| Add | add | `add` |
| Send | send | `send` |
| Auction/Bid | flash_on | `flash_on` |
| Block/Pass | block | `block` |
| Trending | trending_up | `trending_up` |
| People | people | `people` |

### Icon Sizing

| Context | Size |
|---------|------|
| Navigation | 24px |
| Inline | 20px |
| Decorative | 32px |
| Large feature | 48px |

---

## Feature Status

### What Maps to Existing Backend

| Screen | Feature | Backend Status |
|--------|---------|----------------|
| Sign In | Magic link authentication | ✅ Exists |
| Home | Create competition | ✅ Exists |
| Home | Join competition | ✅ Exists |
| Home | View active leagues | ✅ Exists |
| Auction Room | Real-time bidding | ✅ Exists |
| Auction Room | Timer with anti-snipe | ✅ Exists |
| Auction Room | Budget tracking | ✅ Exists |
| Auction Room | Team queue | ✅ Exists |

### Placeholder Features (No Backend Yet)

These features appear in mockups but require future backend development:

| Screen | Feature | Notes |
|--------|---------|-------|
| Auction Banter | Live chat during auction | Requires WebSocket chat system |
| Auction Banter | Quick reply pills | Requires chat backend |
| Auction Banter | Bid event notifications in chat | Requires event integration |
| Profile | Hall of Fame title | Requires stats aggregation |
| Profile | Career stats (Total Wins, Clubs Owned) | Requires historical data |
| Profile | Record Bid Placed | Requires bid history query |
| Profile | Trophy Room | Requires competition history |
| Profile | Trophy shelf with league titles | Requires achievement system |
| Profile | "LEGENDARY" badge system | Requires ranking/tier system |
| Stats Page | (Not yet designed) | Placeholder |
| Social Page | (Not yet designed) | Placeholder |

### Design-Only Deliverables

This specification covers **visual design and component structure only**. 

When building:
- Placeholder screens should be static/non-functional
- Use mock data for demonstration
- No backend integration until tested and approved
- Build in a **separate project** to avoid affecting existing codebase

---

## Mockup Reference

Original mockups stored at:
- Sign In: `https://customer-assets.emergentagent.com/job_sportsbid-ux/artifacts/jwd9l8h1_sign%20in%20page.png`
- Home: `https://customer-assets.emergentagent.com/job_sportsbid-ux/artifacts/5aokhsqg_home%20page.png`
- Auction Room: `https://customer-assets.emergentagent.com/job_sportsbid-ux/artifacts/9q2oxkny_auction%20screen%20final.png`
- Chat/Banter: `https://customer-assets.emergentagent.com/job_sportsbid-ux/artifacts/tr44vgrx_chat%20screen.png`
- Profile: `https://customer-assets.emergentagent.com/job_sportsbid-ux/artifacts/zyaackpr_manager%20profile%20screen.png`

---

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Status:** Reference specification - implementation pending Railway migration
