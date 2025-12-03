# 🎯 NEW AGENT ONBOARDING CHECKLIST

**CRITICAL: Complete this checklist BEFORE making ANY changes or suggestions**

---

## Phase 1: System Understanding (MANDATORY)

### 1. Read and Summarize the Handoff Summary

After reading the handoff summary, answer in your own words:
- What is the core purpose of this application?
- What was the last working item?
- What are the pending issues/tasks?
- What are the upcoming tasks?
- What are the known problem areas to avoid?
- What mistakes did previous agents make that you must not repeat?

### 2. Map the Actual User Flows

**Examine the UI code** (not documentation, not assumptions) to understand:

**Commissioner Journey:**
- Create competition → ? → ? → ? → ?
- Where do they land after creating a competition?
- What actions are available on each page?
- When can they import fixtures?
- When can they start an auction?
- What happens after the auction completes?

**Participant Journey:**
- Join competition → ? → ? → ? → ?
- How do they join?
- When do they enter the auction?
- What do they see after the auction?

**Critical Questions to Answer:**
- Can commissioners import fixtures BEFORE auctions? (Show me the code path)
- What triggers the auction to start?
- Where do users go after an auction completes?
- What is the difference between league status "pending" vs "active" vs "completed"?

### 3. Identify the Navigation Structure

Check the routing and UI to map out:
- What pages/components exist?
- What determines which features/buttons are visible?
- What are the key state transitions? (e.g., pending → active)

### 4. Understand the Data Flow

Trace through:
- How are fixtures stored and linked to leagues?
- When are scores updated?
- How does real-time communication work (Socket.IO)?
- What are the critical database collections and their relationships?

---

## Phase 2: Confirm Understanding (ASK HUMAN)

### 5. Before Implementing Anything, Use ask_human to:

- **Present your understanding** of the user flow with a step-by-step walkthrough
- **Confirm which workflow** applies to the current task
- **Ask about any ambiguities** or gaps in your understanding
- **Show your proposed approach** and get explicit approval
- **Clarify edge cases** you're unsure about

**Example questions to ask:**
- "I understand the flow is: Create → Start Auction → Import Fixtures. Is this correct?"
- "Can users access the Competition Dashboard before the auction? I need to verify."
- "For this change, I plan to modify [X]. Could this affect [Y]? Should I proceed?"

---

## Phase 3: Safety Checks

### 6. Before Touching Any Code:

Answer these questions:
- What pages/components does this change affect?
- Could this break existing functionality? How?
- What testing approach will you use?
- What's your rollback plan if something breaks?
- Are you touching any critical paths? (auction logic, socket connections, authentication, scoring)

---

## ❌ FORBIDDEN ACTIONS

### Do NOT:
- ❌ Make assumptions about user workflows based on documentation alone
- ❌ Implement features without tracing through the actual UI code
- ❌ Skip asking clarifying questions when uncertain
- ❌ Proceed without explicit user approval on your approach
- ❌ Touch auction logic, socket connections, scoring, or authentication without deep understanding
- ❌ Make changes within 24 hours of deployment without user approval
- ❌ Assume previous documentation is accurate - verify in the actual code

### ALWAYS:
- ✅ Read the actual code to understand workflows
- ✅ Use ask_human when you have ANY uncertainty
- ✅ Test your changes before declaring them complete
- ✅ Propose your plan and get approval BEFORE implementing
- ✅ Consider "what could break?" for every change

---

## ✅ SUCCESS CRITERIA

**You've completed onboarding when you can:**

1. Explain the end-to-end commissioner and participant journey without looking at code
2. Identify which page a user lands on after each major action
3. Answer: "Can commissioners import fixtures before auctions?" with code evidence
4. Confirm your understanding has been validated by the user via ask_human

---

## 🚨 DEPLOYMENT AWARENESS

**Before making ANY changes, check:**
- Is deployment imminent? (within 24-48 hours)
- Is there active user testing happening?
- Is this a critical production environment?

**If YES to any:** Exercise EXTREME caution. Only make changes with explicit user approval and prefer doing nothing over breaking something.

---

## 📝 Onboarding Checklist

Use this as a literal checklist in your first response:

```
## Onboarding Status

- [ ] Read and summarized handoff summary
- [ ] Mapped commissioner journey with code references
- [ ] Mapped participant journey with code references  
- [ ] Verified fixture import workflow in actual UI
- [ ] Identified all pages and navigation paths
- [ ] Asked clarifying questions via ask_human
- [ ] Received user confirmation of understanding
- [ ] Ready to proceed with approved tasks only

**Notes from onboarding:**
[Your findings and questions here]
```

---

## 🎯 How to Use This Document

**For Commissioners (Users):**
1. Copy this entire document content
2. Paste it in your first message to any new forked agent
3. Require the agent to complete the checklist before proceeding
4. Review their understanding before approving any work

**For Agents:**
1. Complete every item in this checklist
2. Document your findings
3. Ask clarifying questions
4. Wait for user approval
5. Only then proceed with implementation

---

**Remember: Taking 30 minutes to understand the system properly saves hours of debugging broken features later.**
