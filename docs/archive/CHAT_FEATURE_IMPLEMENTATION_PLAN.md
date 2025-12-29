# Chat Feature Implementation Plan for FOPIFA
**Purpose**: Safe, community-focused communication tool  
**Status**: RESEARCH & PLANNING PHASE  
**Target**: Post-pilot implementation  
**Date**: January 2025

---

## Executive Summary

### Vision Alignment
A chat feature directly supports FOPIFA's core mission: **creating safe, online spaces for friends to compete away from gambling ads, strengthening communities through shared passion for sport.**

### Key Principles
1. **Safety First**: Robust moderation tools to maintain community standards
2. **Community Focused**: League-based chat rooms, not public forums
3. **Non-intrusive**: Enhance but don't distract from core auction/competition experience
4. **Simple & Scalable**: Start minimal, expand based on user feedback

### Recommended Approach
**Leverage existing Socket.IO infrastructure** + add moderation layer + simple UI components

**Estimated Effort**: 2-3 weeks development + 1 week testing/moderation setup

---

## Part 1: Why Chat Matters for FOPIFA

### User Benefits
1. **Pre-Auction Banter**: Trash talk, strategy discussion, team building
2. **Live Auction Commentary**: Real-time reactions during bidding
3. **Post-Match Analysis**: Celebrate wins, commiserate losses, discuss performances
4. **Community Building**: Friendships strengthened through ongoing interaction
5. **Reduces External Tools**: No need for WhatsApp/Discord groups

### Community Safety Benefits
- **Closed Leagues**: Only league members can chat (no strangers)
- **Commissioner Control**: League creator has moderation powers
- **Report Tools**: Users can flag inappropriate content
- **No Gambling Links**: Auto-filter betting site URLs
- **Age-Appropriate**: Can implement family-friendly filters

### Competitive Advantage
- Most fantasy sports platforms lack integrated, safe chat
- Differentiator for "friends & family" market vs commercial platforms
- Aligns with anti-gambling, community-first positioning

---

## Part 2: Technical Architecture

### Option A: Socket.IO + Custom Backend (RECOMMENDED)

**Why Recommended:**
- ✅ Already using Socket.IO for real-time auction features
- ✅ Full control over data and privacy
- ✅ No third-party costs or dependencies
- ✅ Can integrate seamlessly with existing rooms architecture
- ✅ MongoDB storage for chat history

**Architecture:**
```
Frontend (React)
    ↓
Socket.IO Client (existing)
    ↓
Backend (FastAPI + Socket.IO)
    ↓
MongoDB (chat_messages collection)
```

**Components:**
1. **Backend Socket Events**:
   - `send_message` - User sends a message
   - `message_received` - Broadcast to league room
   - `typing_indicator` - Show who's typing
   - `message_deleted` - Commissioner/user deletes message

2. **Database Schema**:
```json
{
  "id": "uuid",
  "leagueId": "uuid",
  "userId": "uuid",
  "userName": "string",
  "message": "string",
  "timestamp": "ISO datetime",
  "edited": false,
  "deleted": false,
  "flagged": false,
  "flaggedBy": [],
  "moderatorNotes": ""
}
```

3. **API Endpoints**:
   - `GET /api/leagues/{league_id}/chat/history` - Load last 50 messages
   - `POST /api/leagues/{league_id}/chat/flag` - Report message
   - `DELETE /api/leagues/{league_id}/chat/{message_id}` - Delete (commissioner only)
   - `GET /api/leagues/{league_id}/chat/moderation` - Moderation dashboard

**Pros:**
- Minimal new infrastructure
- Full privacy control
- No external costs
- Leverages existing real-time capabilities

**Cons:**
- Need to build moderation tools from scratch
- Requires storage management (message retention policies)
- More development effort

---

### Option B: Third-Party Chat SDK (CometChat, Stream, SendBird)

**Why Consider:**
- ✅ Pre-built UI components
- ✅ Built-in moderation dashboards
- ✅ Spam/profanity filters included
- ✅ Rich features (typing indicators, read receipts, reactions)

**Architecture:**
```
Frontend (React)
    ↓
CometChat SDK
    ↓
CometChat Cloud Service
```

**Pros:**
- Faster implementation (1 week vs 3 weeks)
- Professional moderation tools out-of-box
- Scales automatically
- Rich feature set (emojis, file sharing, etc.)

**Cons:**
- ❌ Monthly cost (~$49-99/month for 100-500 users)
- ❌ Data stored externally (privacy concerns)
- ❌ Less control over features/customization
- ❌ Vendor lock-in

**Verdict**: Not recommended for FOPIFA's "safe space" mission - external data storage conflicts with privacy-first approach

---

### Option C: Firebase Firestore Chat

**Why Consider:**
- ✅ Real-time sync
- ✅ Offline support
- ✅ Free tier (reasonable limits)

**Pros:**
- Simple integration
- Serverless (no backend code needed)
- Auto-scaling

**Cons:**
- ❌ Requires Firebase account setup
- ❌ New technology stack to manage
- ❌ Less flexible than custom Socket.IO
- ❌ Cost uncertainty at scale

**Verdict**: Could work but adds complexity. Socket.IO option is better since infrastructure already exists.

---

## Part 3: Feature Specification

### Phase 1: MVP Chat (Pilot Testing)

**Core Features:**
1. **League Chat Room**
   - One chat room per league
   - Only league members can access
   - Automatically created when league is created

2. **Basic Messaging**
   - Text messages only (no images/files initially)
   - 500 character limit per message
   - Timestamps (relative: "2 minutes ago")

3. **Message History**
   - Load last 50 messages on page load
   - "Load more" button for older messages
   - Persist in MongoDB

4. **User Identification**
   - Display user name with each message
   - "You" label for own messages
   - Commissioner badge (⭐) next to commissioner's name

5. **Basic Moderation**
   - Commissioners can delete any message
   - Users can delete their own messages (within 5 minutes)
   - Basic profanity filter (block common offensive words)

**UI Placement:**
- **Option 1**: Collapsible chat panel on Competition Dashboard (right sidebar)
- **Option 2**: Separate "Chat" tab alongside Summary, League Table, Fixtures, Breakdown
- **Option 3**: Floating chat button (bottom-right) that opens overlay

**Recommended**: Option 1 (collapsible panel) - always accessible but not intrusive

**Not Included in MVP:**
- ❌ Emojis/reactions
- ❌ File/image sharing
- ❌ Direct messages
- ❌ Thread/replies
- ❌ @mentions
- ❌ Read receipts

---

### Phase 2: Enhanced Features (Post-Pilot)

**Based on user feedback, consider adding:**

1. **Emoji Reactions** 👍 ❤️ 😂 🎉
   - React to messages without typing
   - Show reaction count

2. **@Mentions**
   - @username to notify specific user
   - Highlight mentioned user

3. **Message Editing**
   - Edit sent messages (mark as "edited")
   - 5-minute window to edit

4. **Rich Notifications**
   - Browser push notifications for new messages
   - Mute/unmute chat per league

5. **Auto-Moderation**
   - AI-powered toxicity detection
   - Auto-flag suspicious messages for review

6. **Message Search**
   - Search chat history by keyword
   - Filter by user

7. **Pinned Messages**
   - Commissioner can pin important announcements
   - Show at top of chat

---

### Phase 3: Advanced Features (Future)

1. **Auction Live Commentary Mode**
   - Chat overlay during auctions
   - Quick reactions to bids

2. **Match Day Chat Rooms**
   - Temporary chat for specific matches
   - Auto-archive after match ends

3. **User Status Indicators**
   - Online/offline status
   - "Typing..." indicator

4. **Chat Themes**
   - League-specific chat colors/backgrounds
   - Team badge integration

5. **Analytics Dashboard**
   - Message volume over time
   - Most active users
   - Sentiment analysis

---

## Part 4: Safety & Moderation Strategy

### Built-In Safety Features

**1. League-Based Privacy**
- Chat only visible to league members
- No public/global chat rooms
- Invite-only leagues = invite-only chat

**2. Commissioner Powers**
- Delete any message
- Mute/unmute users (prevent sending messages)
- Ban users from league (removes chat access)
- View flagged messages dashboard

**3. User-Level Controls**
- Report message (flags for commissioner review)
- Delete own messages (5-minute window)
- Mute notifications per league

**4. Automated Moderation**

**Profanity Filter** (Tier 1 - Basic):
```python
BLOCKED_WORDS = [
    # Common profanity
    "offensive_word1", "offensive_word2", ...
]

def filter_message(message):
    for word in BLOCKED_WORDS:
        if word.lower() in message.lower():
            return "Message blocked: inappropriate language"
    return message
```

**Anti-Gambling Filter** (Critical for FOPIFA):
```python
GAMBLING_DOMAINS = [
    "bet365", "betfair", "paddypower", 
    "williamhill", "draftkings", "fanduel"
]

def filter_gambling_links(message):
    for domain in GAMBLING_DOMAINS:
        if domain in message.lower():
            return "Message blocked: gambling links not allowed"
    return message
```

**Spam Detection**:
- Limit: 5 messages per minute per user
- Block repeated identical messages
- Prevent flooding during auctions

**5. Reporting Workflow**
```
User clicks "Report" on message
    ↓
Message flagged in database
    ↓
Commissioner receives notification (in-app + email)
    ↓
Commissioner reviews in Moderation Dashboard
    ↓
Commissioner takes action:
    - Delete message
    - Warn user
    - Mute user (1 hour, 24 hours, permanent)
    - Ban from league
```

---

### Moderation Dashboard (Commissioner View)

**Location**: Competition Dashboard → "Moderation" tab (commissioner only)

**Features**:
1. **Flagged Messages List**
   - Message text
   - Sender name
   - Who flagged it
   - Timestamp
   - Actions: Delete, Dismiss flag, Mute user

2. **User Activity Log**
   - Messages sent per user
   - Flags received
   - Previous warnings/mutes

3. **Chat Statistics**
   - Total messages
   - Most active users
   - Messages per day graph

4. **Quick Actions**
   - Mute user (with duration dropdown)
   - Ban user from league
   - Clear all chat history

---

### Community Guidelines (Display in Chat)

**Suggest including:**
```
FOPIFA Community Guidelines:
1. Keep it friendly - this is a space for mates
2. No gambling links or promotions
3. Respect all league members
4. No spam or repeated messages
5. Commissioners can remove inappropriate content
6. Report issues - don't respond to trolls
```

**Display**: Small "Guidelines" link at bottom of chat panel

---

## Part 5: UI/UX Design Mockup

### Chat Panel Layout (Collapsible Sidebar)

```
┌─────────────────────────────────────────────┐
│ Competition Dashboard                       │
├─────────────────────────┬───────────────────┤
│                         │ 💬 League Chat   ↓│
│                         ├───────────────────┤
│  Main Content           │ John: Great bid!  │
│  (Summary/Table/etc)    │ 2 min ago         │
│                         │                   │
│                         │ You: Thanks! 🎉   │
│                         │ Just now          │
│                         │                   │
│                         │ ⭐ Sarah: Next    │
│                         │    player up!     │
│                         │ Just now          │
│                         ├───────────────────┤
│                         │ [Type message...] │
│                         │         [Send] 📤  │
└─────────────────────────┴───────────────────┘
```

**Key Elements:**
1. **Header**: "💬 League Chat" with minimize button (↓)
2. **Message List**: Scrollable, newest at bottom
3. **Message Bubble**:
   - User name (bold)
   - Message text
   - Relative timestamp ("2 min ago")
   - Actions (⋮) on hover: Delete, Report
4. **Input Box**: Text area with Send button
5. **Status**: "X users online" at top

**Collapsed State**:
```
│ 💬 Chat (3 new) ↑│
```

**Mobile View**:
- Floating button (bottom-right): 💬
- Tapping opens full-screen chat overlay
- Swipe down to close

---

### Message Display Variants

**Own Message** (right-aligned):
```
┌────────────────────────────────┐
│                    You:        │
│                    Great win!  │
│                    Just now  ✓ │
└────────────────────────────────┘
```

**Other User Message** (left-aligned):
```
┌────────────────────────────────┐
│ John:                          │
│ Thanks mate! Close one 😅      │
│ 2 min ago                      │
└────────────────────────────────┘
```

**Commissioner Message** (highlighted):
```
┌────────────────────────────────┐
│ ⭐ Sarah (Commissioner):       │
│ Auction starts in 5 minutes!   │
│ 5 min ago                      │
└────────────────────────────────┘
```

**System Message** (centered):
```
┌────────────────────────────────┐
│     ━━━ Tom joined the chat    │
│     1 hour ago                 │
└────────────────────────────────┘
```

---

## Part 6: Implementation Roadmap

### Pre-Implementation Checklist
- [ ] Pilot complete with 150 users
- [ ] User feedback on need for chat
- [ ] Moderation policy finalized
- [ ] Commissioner guidelines document created
- [ ] Community guidelines drafted

---

### Phase 1: MVP Implementation (2-3 weeks)

**Week 1: Backend Infrastructure**

**Day 1-2: Database & Models**
- [ ] Create `chat_messages` collection schema
- [ ] Add indexes (leagueId, timestamp)
- [ ] Create chat message Pydantic model
- [ ] Add message retention policy (90 days default)

**Day 3-4: Socket.IO Events**
- [ ] Add `send_message` event handler
- [ ] Add `message_received` broadcast
- [ ] Implement room-based chat (league rooms)
- [ ] Add message persistence to MongoDB

**Day 5: Moderation Backend**
- [ ] Implement profanity filter
- [ ] Add gambling link filter
- [ ] Create rate limiting (5 msgs/minute)
- [ ] Add flag/report endpoint
- [ ] Add delete message endpoint (with auth check)

**Week 2: Frontend UI**

**Day 1-2: Chat Component**
- [ ] Create `<ChatPanel>` component
- [ ] Message list with virtualization (React Window)
- [ ] Message input with character count
- [ ] Auto-scroll to bottom on new message

**Day 3: Socket.IO Integration**
- [ ] Connect to league chat room on dashboard mount
- [ ] Listen for `message_received` events
- [ ] Emit `send_message` on form submit
- [ ] Handle reconnection logic

**Day 4: UI Polish**
- [ ] Add timestamps (relative time)
- [ ] Style own vs other messages differently
- [ ] Add commissioner badge
- [ ] Implement collapsible panel

**Day 5: User Actions**
- [ ] Add delete button (own messages only)
- [ ] Add report button (all messages)
- [ ] Confirmation dialogs for actions

**Week 3: Testing & Moderation Dashboard**

**Day 1-2: Moderation Dashboard**
- [ ] Create Commissioner-only "Moderation" tab
- [ ] Display flagged messages list
- [ ] Add delete/mute user actions
- [ ] Show user activity stats

**Day 3-4: Testing**
- [ ] Unit tests for filters (profanity, gambling)
- [ ] Integration tests for Socket.IO events
- [ ] E2E tests for chat flow (Playwright)
- [ ] Load testing (100 users, 10 messages/sec)

**Day 5: Documentation & Launch Prep**
- [ ] Update user documentation
- [ ] Create commissioner moderation guide
- [ ] Add community guidelines to chat UI
- [ ] Prepare release notes

---

### Phase 2: Enhanced Features (Post-MVP Feedback)

**Timing**: 4-6 weeks after MVP launch

**Based on user feedback, prioritize:**
1. Emoji reactions (high demand, low effort)
2. Push notifications (high value, medium effort)
3. @Mentions (medium demand, medium effort)
4. Message editing (low demand, low effort)

---

### Phase 3: Advanced Features (6+ months)

**Conditional on:**
- User adoption > 70%
- Positive feedback on chat usefulness
- Minimal moderation issues

**Consider:**
- AI-powered moderation
- Voice messages
- Match-day specific chat rooms
- Integration with auction overlay

---

## Part 7: Development Estimates

### Effort Breakdown (MVP)

| Task | Effort | Developer |
|------|--------|-----------|
| Backend (Socket.IO + DB) | 5 days | Full-stack |
| Frontend UI Components | 5 days | Frontend |
| Moderation Tools | 3 days | Full-stack |
| Testing & QA | 2 days | QA/Developer |
| **Total** | **15 days** | **~3 weeks** |

### Technology Stack (No New Dependencies)

**Backend:**
- ✅ Socket.IO (already installed)
- ✅ FastAPI (already installed)
- ✅ MongoDB (already installed)
- ✅ Pydantic (already installed)

**Frontend:**
- ✅ React (already installed)
- ✅ Socket.IO Client (already installed)
- 🆕 React Window (for virtualized message list) - lightweight
- 🆕 React Timeago (for relative timestamps) - optional, can use date-fns

**New Infrastructure**: NONE

---

## Part 8: Risks & Mitigation

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Toxic behavior/abuse** | Medium | High | Strong moderation tools, clear guidelines, commissioner powers |
| **Chat distracts from core features** | Low | Medium | Collapsible UI, test with pilot users first |
| **Performance issues with many users** | Low | Medium | Message virtualization, pagination, load testing |
| **Spam/flooding** | Medium | Low | Rate limiting (5 msgs/min), automated detection |
| **Gambling links shared** | Low | High | Auto-filter gambling domains, user reports |
| **Storage costs grow** | Low | Low | 90-day message retention, compression |
| **Moderation overhead for commissioners** | Medium | Medium | Simple tools, auto-moderation, clear guidelines |

---

### Critical Success Factors

**Must Have:**
- ✅ Zero tolerance for gambling content (auto-filter)
- ✅ Commissioner delete powers (immediate action)
- ✅ User report functionality (community self-regulation)
- ✅ Profanity filter (basic protection)
- ✅ Rate limiting (prevent spam)

**Should Have:**
- Simple, intuitive UI (low learning curve)
- Fast, responsive (no lag)
- Mobile-friendly (50%+ users on mobile)

**Nice to Have:**
- Emojis/reactions
- Message editing
- Push notifications

---

## Part 9: Pilot Testing Plan

### Beta Test Group
- Select 2-3 pilot leagues (20-30 users total)
- Mix of demographics (age, tech-savviness)
- Include at least 1 commissioner per league

### Testing Phase (2 weeks)

**Week 1: Soft Launch**
- Enable chat for beta leagues only
- Monitor usage patterns
- Collect qualitative feedback (surveys)

**Week 2: Stress Test**
- Encourage heavy usage (auction days)
- Test moderation tools with real scenarios
- Monitor performance metrics

### Success Metrics
1. **Adoption**: >50% of league members send at least 1 message
2. **Engagement**: Average 10+ messages per league per day
3. **Safety**: <5% of messages flagged/deleted
4. **Performance**: <200ms message delivery latency
5. **Satisfaction**: >4/5 stars in user surveys

### Go/No-Go Criteria
- ✅ No critical bugs
- ✅ Positive user feedback (>70% approval)
- ✅ Moderation tools effective (commissioners feel in control)
- ✅ No performance degradation to core features
- ❌ If toxic behavior unmanageable → pause rollout, strengthen moderation

---

## Part 10: Cost Analysis

### Development Costs
- **Engineering**: 3 weeks × 1 developer = ~£6,000 - £12,000 (contractor rates)
- **Testing**: 1 week QA = ~£1,500 - £3,000
- **Design** (optional): 2 days UI/UX = ~£1,000 - £2,000

**Total One-Time**: ~£8,500 - £17,000

### Operational Costs

**Infrastructure** (monthly):
- Socket.IO/MongoDB: £0 (already running)
- Storage (chat messages): ~£1-5/month (estimated 100MB/month for 150 users)
- Bandwidth: Negligible increase

**Total Monthly**: ~£1-5 (basically free)

**Moderation** (time cost):
- Commissioner time: ~1-2 hours/month per league (volunteer)
- Platform support: ~2-4 hours/month (handle escalations)

**Total Ongoing**: Minimal

---

## Part 11: Alternatives Considered

### Don't Build Chat - Use External Tools

**Option**: Recommend users create WhatsApp/Discord groups

**Pros:**
- Zero development cost
- Users already familiar with these tools
- Rich features out-of-box

**Cons:**
- ❌ Breaks "all-in-one" experience
- ❌ No control over content/safety
- ❌ Gambling ads likely to appear (Discord, social media)
- ❌ Requires users to share phone numbers (WhatsApp)
- ❌ Misses opportunity for differentiation

**Verdict**: Contradicts FOPIFA's mission of creating safe, ad-free spaces

---

### Build Read-Only "Announcements" First

**Option**: Start with commissioner-only announcements (no replies)

**Pros:**
- Simpler to build (1 week vs 3 weeks)
- Lower moderation risk
- Still adds value

**Cons:**
- Not true "community" feature
- Doesn't enable friend interaction
- Less engaging

**Verdict**: Could be a stepping stone, but doesn't fulfill community vision

---

## Part 12: Recommendations

### Short-Term (Pre-Pilot)
1. ✅ **Gather user feedback during pilot**
   - Survey question: "Would in-app chat enhance your experience?"
   - Observe if users are organizing external chats
   - Ask commissioners if they'd use chat for announcements

2. ✅ **Finalize moderation policy**
   - Draft community guidelines
   - Define commissioner responsibilities
   - Create moderation playbook

### Medium-Term (Post-Pilot, Pre-Chat Launch)
3. ✅ **Implement MVP chat** (Option A: Socket.IO custom)
   - Leverage existing infrastructure
   - Start simple (text only)
   - Focus on safety features first

4. ✅ **Beta test with 2-3 leagues** (2 weeks)
   - Monitor closely
   - Iterate based on feedback
   - Ensure moderation tools are effective

### Long-Term (6+ months)
5. ✅ **Expand features based on usage**
   - If adoption >70%, add emoji reactions, mentions
   - If moderation issues arise, enhance auto-filters
   - Consider AI moderation if needed

6. ✅ **Integrate with other features**
   - Auction live commentary
   - Match-day chat rooms
   - Social sharing

---

## Part 13: Key Decision Points

### Decision #1: When to Implement?
**Recommendation**: Post-pilot (after 150-user test complete)

**Reasoning**:
- Pilot will reveal if users want chat
- Need stable platform before adding social features
- Can assess moderation needs from pilot behavior

**Timeline**: 3-6 months from now

---

### Decision #2: Which Architecture?
**Recommendation**: Option A (Socket.IO + Custom Backend)

**Reasoning**:
- Leverages existing infrastructure (no new costs)
- Full control over data (privacy-first)
- Aligns with FOPIFA's independent, user-centric values
- Flexible for future customization

**Alternative**: If dev resources tight, consider CometChat for faster launch

---

### Decision #3: How Much Moderation?
**Recommendation**: Start Conservative, Expand Carefully

**Tier 1 (MVP)**: Basic filters + commissioner powers
**Tier 2 (Post-launch)**: If issues arise, add AI moderation
**Tier 3 (Scale)**: Dedicated moderation team (only if app grows to 10,000+ users)

**For 150-500 users**: Commissioner-led moderation is sufficient

---

### Decision #4: Mobile-First or Desktop-First?
**Recommendation**: Mobile-first design (but desktop functional)

**Reasoning**:
- 50%+ users likely on mobile during matches
- Chat most valuable during live events (auctions, match days)
- Simple text chat works well on mobile
- Desktop can use same UI (responsive)

---

## Part 14: Success Criteria

### Launch Success (3 months post-launch)
- [ ] 60%+ of leagues have active chat
- [ ] 40%+ of users send at least 1 message/week
- [ ] <3% of messages flagged/deleted (indicates healthy community)
- [ ] 4+ stars user satisfaction on chat feature
- [ ] No gambling content getting through filters

### Long-Term Success (12 months)
- [ ] 75%+ of leagues use chat regularly
- [ ] Average 20+ messages per league per day
- [ ] Chat feature mentioned in user testimonials
- [ ] Zero major moderation incidents
- [ ] Feature contributes to 10%+ increase in user retention

---

## Conclusion

### Summary

**Chat aligns perfectly with FOPIFA's mission** of creating safe, ad-free community spaces. The feature can be built efficiently using existing Socket.IO infrastructure with minimal cost.

**Recommended Path Forward:**
1. **Now**: Include chat as topic in pilot user feedback
2. **Post-Pilot** (3-6 months): Implement MVP if feedback positive
3. **Beta Test**: 2-3 leagues, 2 weeks
4. **Gradual Rollout**: All leagues if beta successful
5. **Iterate**: Enhance based on usage patterns

**Key to Success:**
- Start simple (text only)
- Empower commissioners (moderation tools)
- Auto-filter gambling content (critical)
- Monitor closely during beta
- Expand features based on real usage

**Risk Level**: LOW (if done post-pilot with strong moderation)

**Value**: HIGH (differentiates FOPIFA, builds community, increases engagement)

---

## Next Steps

### Immediate Actions (Now)
1. Review this plan with stakeholders
2. Incorporate chat question into pilot user surveys
3. Draft community guidelines document
4. Create commissioner moderation guide

### Pre-Implementation (Post-Pilot)
1. Analyze pilot user feedback on chat need
2. Finalize moderation policy
3. Secure development resources (3 weeks)
4. Design UI mockups for approval

### Implementation (When Ready)
1. Follow 3-week development roadmap (Part 6)
2. Beta test with 2-3 leagues
3. Iterate based on feedback
4. Gradual rollout to all leagues

---

**Document Version**: 1.0  
**Status**: READY FOR REVIEW  
**Next Review**: Post-Pilot (3-6 months)

---

**Questions for Consideration:**
1. Should commissioners be able to permanently ban users, or just mute?
2. Should there be a "slow mode" during busy times (e.g., limit to 1 message/minute during auctions)?
3. Should chat history be exportable (for archiving league memories)?
4. Should there be a global "FOPIFA Announcements" read-only channel for platform updates?

**Ready to implement when the time is right!** 🚀
