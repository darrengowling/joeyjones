import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomNav from '../components/BottomNav';

// Section component moved outside Help to prevent recreation on each render
const Section = ({ id, title, children, isOpen, onToggle }) => (
  <div className="mb-4 border border-white/10 rounded-xl overflow-hidden" style={{ background: '#151C2C' }}>
    <button
      onClick={() => onToggle(id)}
      className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition-colors"
    >
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <svg
        className={`w-6 h-6 text-white/60 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    {isOpen && (
      <div className="p-6" style={{ background: 'rgba(0,0,0,0.2)' }}>
        {children}
      </div>
    )}
  </div>
);

const Help = () => {
  const navigate = useNavigate();
  const [openSection, setOpenSection] = useState('getting-started');

  // Set page title
  useEffect(() => {
    document.title = 'Help Center | Sport X';
  }, []);

  const toggleSection = (section) => {
    setOpenSection(openSection === section ? null : section);
  };

  return (
    <div className="min-h-screen" style={{ background: '#0F172A', paddingBottom: '100px' }}>
      {/* Header */}
      <header 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-md z-40 px-4 py-4"
        style={{
          background: 'rgba(15, 23, 42, 0.95)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <div className="container mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-white/60 hover:text-white transition-colors"
          >
            <span>←</span>
            <span className="text-xl font-black tracking-tighter">
              SPORT <span style={{ color: '#06B6D4' }}>X</span>
            </span>
          </button>
          <div className="text-center">
            <div className="text-xs uppercase tracking-widest text-white/40">Help Center</div>
            <h1 className="text-lg font-bold text-white">User Guide</h1>
          </div>
          <div className="w-20"></div>
        </div>
      </header>

      {/* Content */}
      <div className="container mx-auto px-4 pt-24 pb-8 max-w-4xl">
        {/* Introduction */}
        <div className="rounded-xl p-6 mb-8" style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <h2 className="text-2xl font-bold text-white mb-3">Welcome to Sport X</h2>
          <p className="text-white/80 mb-2">
            Sports Gaming with Friends. No Gambling. All Game.
          </p>
          <p className="text-white/60">
            Bid for exclusive ownership of players and teams who score your points. Experience the thrill of sports through strategic competition and community.
          </p>
        </div>

        {/* Getting Started */}
        <Section id="getting-started" title="Getting Started" isOpen={openSection === 'getting-started'} onToggle={toggleSection}>
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Account Setup & Sign In</h4>
              <p className="text-white/80 mb-3">
                Sport X uses a secure <strong>magic link authentication</strong> system. No passwords required.
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Step-by-Step Sign In:</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>Click <strong>"Sign In"</strong> on the homepage</li>
                  <li>Enter your <strong>email address</strong> and optionally your name</li>
                  <li>Click <strong>"Continue"</strong> to generate your magic link token</li>
                  <li>You'll receive a <strong>6-digit token</strong> displayed on screen</li>
                  <li>Enter this token in the next step to complete sign in</li>
                  <li>Your session will be securely maintained for easy access</li>
                </ol>
              </div>

              <div className="rounded-lg p-4" style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                <p className="text-white/80 text-sm">
                  <strong>Note:</strong> In production, the magic link token would be sent to your email. For the pilot, it's displayed on screen for convenience.
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">First Steps After Sign In</h4>
              <ul className="list-disc list-inside space-y-2 text-white/80">
                <li><strong>Create a Competition:</strong> Start your own league if you're the organizer</li>
                <li><strong>Join a Competition:</strong> Enter an invite token from a friend</li>
                <li><strong>Explore Available Teams:</strong> Browse the sports teams available for bidding</li>
              </ul>
            </div>
          </div>
        </Section>

        {/* How to Install */}
        <Section id="install-app" title="Install the App" isOpen={openSection === 'install-app'} onToggle={toggleSection}>
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Add Sport X to Your Home Screen</h4>
              <p className="text-white/80 mb-3">
                For the best experience, add Sport X to your phone's home screen. This gives you quick access and a full-screen experience without browser bars.
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">iPhone (Safari):</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>Open Sport X in <strong>Safari</strong> (not Chrome)</li>
                  <li>Tap the <strong>Share</strong> button (square with arrow pointing up)</li>
                  <li>Scroll down and tap <strong>"Add to Home Screen"</strong></li>
                  <li>Tap <strong>"Add"</strong> in the top right corner</li>
                  <li>Sport X will appear on your home screen as an app icon</li>
                </ol>
              </div>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Android (Chrome):</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>Open Sport X in <strong>Chrome</strong></li>
                  <li>Tap the <strong>three dots menu</strong> (top right corner)</li>
                  <li>Tap <strong>"Add to Home screen"</strong> or <strong>"Install app"</strong></li>
                  <li>Confirm by tapping <strong>"Add"</strong></li>
                  <li>Sport X will appear in your app drawer and home screen</li>
                </ol>
              </div>

              <div className="rounded-lg p-4" style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                <p className="text-white/80 text-sm">
                  <strong>Why install?</strong> When you open Sport X from your home screen, it launches in full-screen mode without browser navigation bars, giving you more space for bidding and a smoother experience during live auctions.
                </p>
              </div>
            </div>
          </div>
        </Section>

        {/* For Commissioners */}
        <Section id="admin-create" title="For Commissioners" isOpen={openSection === 'admin-create'} onToggle={toggleSection}>
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Creating a Competition</h4>
              <p className="text-white/80 mb-3">
                As a commissioner, you control the competition setup and manage the auction process.
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Competition Setup Steps:</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>Click <strong>"Create Your Competition"</strong> on the homepage</li>
                  <li>Enter a <strong>competition name</strong> (e.g., "Premier League 2025")</li>
                  <li>Select the <strong>sport</strong> (Cricket or Football)</li>
                  <li>Set the <strong>budget</strong> for each manager (default: £500M)</li>
                  <li>Configure <strong>manager slots</strong> (min 2, max 8 participants)</li>
                  <li>Set <strong>club slots</strong> (how many teams each manager can own)</li>
                  <li>Configure <strong>auction timer</strong> (15-120 seconds per bid)</li>
                  <li>Set <strong>anti-snipe time</strong> (0-30 seconds to prevent last-second bids)</li>
                  <li>Click <strong>"Create Competition"</strong></li>
                </ol>
              </div>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <p className="text-white/80 text-sm mb-2">
                  <strong>Key Settings Explained:</strong>
                </p>
                <ul className="text-white/70 text-sm space-y-1 list-disc list-inside">
                  <li><strong>Budget:</strong> Total virtual currency each manager gets for bidding</li>
                  <li><strong>Club Slots:</strong> Maximum teams each participant can acquire</li>
                  <li><strong>Auction Timer:</strong> Countdown for each bid - longer gives more thinking time</li>
                  <li><strong>Anti-Snipe:</strong> Extends timer if bid comes in the last few seconds</li>
                </ul>
              </div>

              <div className="rounded-lg p-4" style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                <p className="text-white/80 text-sm">
                  <strong>Important:</strong> After creating the competition, you'll receive an <strong>8-character invite token</strong>. Share this with your participants so they can join.
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Pre-Auction Setup (Optional)</h4>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Import Fixtures Before Auction</h5>
                <p className="text-white/80 mb-2">
                  You can import upcoming fixtures <em>before</em> starting the auction to help managers make strategic bidding decisions.
                </p>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>After selecting your teams, look for the <strong>"Import Fixtures (Optional)"</strong> section on the league detail page</li>
                  <li>Click <strong>"Import Fixtures"</strong> button</li>
                  <li>The system will fetch upcoming matches for your selected teams (next 7 days)</li>
                  <li>During the auction, each team will show their next fixture, helping managers bid strategically</li>
                </ol>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Running the Auction</h4>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Auction Control Steps:</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>Wait for all managers to join using the invite token</li>
                  <li>Navigate to your competition page from "My Competitions"</li>
                  <li><strong>(Optional)</strong> Import fixtures before starting if you haven't already</li>
                  <li>Click <strong>"Start Auction"</strong> when ready</li>
                  <li>The first team will be nominated for bidding automatically</li>
                  <li>Managers place bids in real-time until timer expires</li>
                  <li>After each team is won, click <strong>"Next Team"</strong> to continue</li>
                  <li>Auction concludes when all slots are filled</li>
                </ol>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Managing Fixtures & Scores</h4>
              <p className="text-white/80 mb-3">
                After the auction, commissioners manage the competition by importing fixtures and updating scores with a simple click - all automated.
              </p>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">How Fixture Import Works:</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>Navigate to Competition Dashboard → <strong>"Fixtures"</strong> tab</li>
                  <li>Click <strong>"Import Fixtures"</strong> (Football) or <strong>"Import Next Fixture"</strong> (Cricket)</li>
                  <li>The system automatically fetches upcoming matches from live sports data APIs</li>
                  <li>You'll see a confirmation message showing how many fixtures were imported/updated</li>
                  <li>Imported fixtures appear with match dates, venues, and competing teams</li>
                </ol>
              </div>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Update Scores (Automatic)</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>After a real match concludes, go to the <strong>"Fixtures"</strong> tab</li>
                  <li>Find the completed match in the fixtures list</li>
                  <li>Click the <strong>"Update Scores"</strong> button for that fixture</li>
                  <li>The system automatically fetches live match results and player stats from sports APIs</li>
                  <li>Points are calculated instantly based on the scoring rules</li>
                  <li>Standings update in real-time - participants see changes immediately</li>
                </ol>
              </div>
            </div>
          </div>
        </Section>

        {/* New Features & Updates */}
        <Section id="updates" title="Recent Updates & New Features" isOpen={openSection === 'updates'} onToggle={toggleSection}>
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Commissioner Auction Controls</h4>
              <p className="text-white/80 mb-3">
                As a commissioner, you have special controls during live auctions to manage the auction flow:
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Available Controls:</h5>
                <ul className="space-y-3 text-white/80">
                  <li>
                    <strong>Pause:</strong> Temporarily pause the auction (timer stops, no bidding allowed). Use this if you need a break or to resolve an issue.
                  </li>
                  <li>
                    <strong>Resume:</strong> Resume a paused auction (timer continues, bidding resumes).
                  </li>
                  <li>
                    <strong>Complete Lot:</strong> Manually advance to the next team/player. The current lot is awarded to the highest bidder and the next team starts immediately.
                    <div className="mt-1 text-sm rounded px-3 py-2" style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                      <strong>When to use:</strong> Only use this if the timer appears stuck or frozen. The auction normally advances automatically when the timer expires.
                    </div>
                  </li>
                  <li>
                    <strong>Delete Auction:</strong> Permanently delete the auction and all associated data. This returns the league to ready state but cannot be undone.
                  </li>
                </ul>
              </div>

              <h4 className="text-lg font-semibold text-white mb-3 mt-6">Auction Reset Feature</h4>
              <p className="text-white/80 mb-3">
                Commissioners can now reset an auction and start fresh without recreating the entire league or re-inviting participants.
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">How It Works:</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li><strong>Pause the auction:</strong> Click the Pause button in the Auction Room</li>
                  <li><strong>Reset auction:</strong> Click the Reset button (appears when paused or completed)</li>
                  <li><strong>Confirm reset:</strong> Review what will be reset and confirm the action</li>
                  <li><strong>Automatic cleanup:</strong> All bids are cleared, participant budgets reset, rosters cleared</li>
                  <li><strong>Start fresh:</strong> Return to Competition Detail Page and click "Begin Strategic Competition" to start a new auction</li>
                </ol>
              </div>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <p className="text-white/80 text-sm mb-2">
                  <strong>What Gets Reset:</strong>
                </p>
                <ul className="text-white/70 text-sm space-y-1 list-disc list-inside">
                  <li>All auction bids and history</li>
                  <li>Participant budgets (restored to full amount)</li>
                  <li>Participant rosters (clubs won are cleared)</li>
                  <li>League status (returned to pending)</li>
                </ul>
              </div>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <p className="text-white/80 text-sm mb-2">
                  <strong>What's Preserved:</strong>
                </p>
                <ul className="text-white/70 text-sm space-y-1 list-disc list-inside">
                  <li>All participants remain in the league (no re-inviting needed)</li>
                  <li>League configuration (budget, slots, timer settings)</li>
                  <li>Selected teams for the auction</li>
                  <li>Imported fixtures (if any)</li>
                </ul>
              </div>

              <div className="rounded-lg p-4" style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                <p className="text-white/80 text-sm">
                  <strong>For Participants:</strong> If you're in the auction room when the commissioner resets, you'll automatically see a message within 3 seconds with a button to return to the competition page. Just wait there for the commissioner to restart the auction.
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">API Rate Limit Display</h4>
              <p className="text-white/80 mb-3">
                We now show accurate API request limits when importing fixtures for Premier League and Champions League competitions.
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">What You'll See:</h5>
                <ul className="list-disc list-inside space-y-2 text-white/80">
                  <li><strong>Request counter:</strong> After importing fixtures, you'll see "API requests remaining this minute: X/10"</li>
                  <li><strong>Rate limit:</strong> Football-Data.org API allows 10 requests per minute on the free tier</li>
                  <li><strong>Resets automatically:</strong> The counter resets every 60 seconds</li>
                </ul>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">AFCON Competition Improvements</h4>
              <p className="text-white/80 mb-3">
                AFCON (Africa Cup of Nations) competitions now have a streamlined CSV-only workflow for fixture and score management.
              </p>
              
              <div className="rounded-lg p-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">What Changed:</h5>
                <ul className="list-disc list-inside space-y-2 text-white/80">
                  <li><strong>Simplified interface:</strong> The "Import Fixtures" button is hidden for AFCON leagues on the Competition Detail Page</li>
                  <li><strong>CSV-only workflow:</strong> AFCON uses manual CSV uploads for both fixtures and scores (as the primary data API doesn't cover this tournament)</li>
                  <li><strong>Clear instructions:</strong> All fixture/score management happens via the Competition Dashboard → Fixtures tab using CSV templates</li>
                </ul>
              </div>
            </div>
          </div>
        </Section>

        {/* For Players */}
        <Section id="user-join" title="For Players">
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Joining a Competition</h4>
              <p className="text-white/80 mb-3">
                To join a competition, you'll need an invite token from the commissioner.
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">How to Join:</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>Get the <strong>8-character invite token</strong> from your league commissioner</li>
                  <li>Click <strong>"Join the Competition"</strong> on the homepage</li>
                  <li>Enter the invite token</li>
                  <li>Click <strong>"Join"</strong> to confirm</li>
                  <li>Wait for the commissioner to start the auction</li>
                </ol>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Participating in Auctions</h4>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Bidding Strategy:</h5>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li><strong>Wait for auction to start:</strong> The commissioner will begin when all managers are ready</li>
                  <li><strong>View current team:</strong> See the team up for bidding and its base price</li>
                  <li><strong>Monitor your budget:</strong> Keep track of remaining funds for future bids</li>
                  <li><strong>Place strategic bids:</strong> Click "Place Bid" to increase the current price</li>
                  <li><strong>Watch the timer:</strong> Bids in the last seconds trigger anti-snipe extension</li>
                  <li><strong>Win teams strategically:</strong> Balance your budget across multiple teams</li>
                </ol>
              </div>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <p className="text-white/80 text-sm mb-2">
                  <strong>Pro Tips:</strong>
                </p>
                <ul className="text-white/70 text-sm space-y-1 list-disc list-inside">
                  <li>Don't spend all your budget on the first few teams</li>
                  <li>Consider team performance and upcoming fixtures</li>
                  <li>Watch other managers' budgets to gauge competition</li>
                  <li>Anti-snipe timer prevents unfair last-second wins</li>
                  <li>Stay active - auctions move fast with engaged participants</li>
                </ul>
              </div>

              <div className="rounded-lg p-4" style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                <p className="text-white/80 text-sm">
                  <strong>Remember:</strong> Each bid increases the price by a set increment. Make sure you have enough budget remaining before placing a bid.
                </p>
              </div>
            </div>
          </div>
        </Section>

        {/* Dashboards & Results */}
        <Section id="dashboards" title="Viewing Dashboards & Results">
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Competition Dashboard</h4>
              <p className="text-white/80 mb-3">
                After the auction, track your teams' performance and standings in real-time.
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Dashboard Features:</h5>
                <ul className="list-disc list-inside space-y-2 text-white/80">
                  <li><strong>Leaderboard:</strong> See all managers ranked by total points</li>
                  <li><strong>Your Teams:</strong> View all teams you won in the auction</li>
                  <li><strong>Team Details:</strong> Click any team to see their match history</li>
                  <li><strong>Live Updates:</strong> Points update automatically when matches conclude</li>
                  <li><strong>Competition Stats:</strong> Overall budget spent, teams owned, rankings</li>
                </ul>
              </div>

              <div className="rounded-lg p-4" style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                <p className="text-white/80 text-sm">
                  <strong>Access Dashboard:</strong> Click on any competition from "My Competitions" to view its live dashboard and track your performance.
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Finding Your Competitions</h4>
              
              <div className="rounded-lg p-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <ol className="list-decimal list-inside space-y-2 text-white/80">
                  <li>Click <strong>"My Competitions"</strong> in the top navigation</li>
                  <li>View all competitions you've created or joined</li>
                  <li>See current status: Pending, Auction Live, or Completed</li>
                  <li>Click any competition to view its dashboard</li>
                </ol>
              </div>
            </div>
          </div>
        </Section>

        {/* Scoring Systems */}
        <Section id="scoring" title="Scoring Systems">
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">How Points Are Calculated</h4>
              <p className="text-white/80 mb-4">
                Your teams or players earn points based on their real-world performance. The scoring system varies by sport.
              </p>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Cricket Scoring</h4>
              <p className="text-white/80 mb-3">
                In cricket competitions, points are awarded <strong>per player, per match</strong> based on individual performance:
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-3">Cricket Points Table:</h5>
                <div className="space-y-2">
                  <div className="flex justify-between items-center py-2 border-b border-white/10">
                    <span className="text-white/80 font-medium">Run scored</span>
                    <span className="text-white font-bold">1 point</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-white/10">
                    <span className="text-white/80 font-medium">Wicket taken</span>
                    <span className="text-white font-bold">20 points</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-white/10">
                    <span className="text-white/80 font-medium">Catch</span>
                    <span className="text-white font-bold">10 points</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-white/10">
                    <span className="text-white/80 font-medium">Stumping</span>
                    <span className="text-white font-bold">25 points</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-white/80 font-medium">Run out</span>
                    <span className="text-white font-bold">20 points</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg p-4" style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                <p className="text-white/80 text-sm">
                  <strong>Example:</strong> If your player scores 50 runs, takes 2 wickets, and makes 1 catch, they earn: (50 x 1) + (2 x 20) + (1 x 10) = <strong>100 points</strong>
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Football Scoring</h4>
              <p className="text-white/80 mb-3">
                In football competitions, points are awarded <strong>per team, per match</strong> based on match results and goals:
              </p>
              
              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-3">Football Points Table:</h5>
                <div className="space-y-2">
                  <div className="flex justify-between items-center py-2 border-b border-white/10">
                    <span className="text-white/80 font-medium">Match win</span>
                    <span className="text-white font-bold">3 points</span>
                  </div>
                  <div className="flex justify-between items-center py-2 border-b border-white/10">
                    <span className="text-white/80 font-medium">Match draw</span>
                    <span className="text-white font-bold">1 point</span>
                  </div>
                  <div className="flex justify-between items-center py-2">
                    <span className="text-white/80 font-medium">Goal scored</span>
                    <span className="text-white font-bold">1 point</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg p-4" style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
                <p className="text-white/80 text-sm">
                  <strong>Example:</strong> If your team wins 3-1, they earn: (1 x 3 for win) + (3 x 1 for goals) = <strong>6 points</strong>
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Total Manager Score</h4>
              <p className="text-white/80">
                Your total competition score is the <strong>sum of all points</strong> earned by your teams or players across all matches. The manager with the highest total score wins the competition.
              </p>
            </div>
          </div>
        </Section>

        {/* Navigation */}
        <Section id="navigation" title="Navigation & Finding Pages">
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-white mb-3">Navigating the Platform</h4>
              <p className="text-white/80 mb-4">
                We've made it easy to move between different areas of the platform. Here's how to find what you need:
              </p>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">My Competitions Hub</h5>
                <p className="text-white/80 mb-2">
                  Your central dashboard to access all your leagues:
                </p>
                <ul className="list-disc list-inside space-y-1 text-white/80 ml-4">
                  <li><strong>League Detail:</strong> Click to view league setup, participants, and invitation token</li>
                  <li><strong>View Dashboard:</strong> Access standings, fixtures, and scores</li>
                  <li><strong>Join Auction Now:</strong> When auction is live, this button pulses - click to enter the auction room</li>
                </ul>
              </div>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Returning to Active Auctions</h5>
                <p className="text-white/80 mb-2">
                  <strong>Don't miss your auction.</strong> If you navigate away from an auction room:
                </p>
                <ol className="list-decimal list-inside space-y-1 text-white/80 ml-4">
                  <li>Go to <strong>"My Competitions"</strong> from the top menu</li>
                  <li>Look for the competition with <strong>Auction Live</strong> status</li>
                  <li>Click the pulsing <strong>Join Auction Now</strong> button</li>
                  <li>You'll be taken directly back to the auction room</li>
                </ol>
              </div>

              <div className="rounded-lg p-4 mb-4" style={{ background: 'rgba(255,255,255,0.05)' }}>
                <h5 className="font-semibold text-white mb-2">Breadcrumb Navigation</h5>
                <p className="text-white/80 mb-2">
                  In the auction room, you'll see breadcrumbs at the top:
                </p>
                <p className="font-mono text-sm text-white/60 p-2 rounded border border-white/20 mb-2" style={{ background: 'rgba(0,0,0,0.3)' }}>
                  Home › My Competitions › League Name › Auction Room
                </p>
                <p className="text-white/80 text-sm">
                  Click any part of the path to navigate back to that page quickly.
                </p>
              </div>

              <div className="rounded-lg p-4" style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                <h5 className="font-semibold text-white mb-2">League Detail Page Alert</h5>
                <p className="text-white/80 mb-2">
                  When an auction is live and you're on the league detail page, you'll see a prominent red alert banner at the top. Click the "Join Auction Now" button to enter immediately.
                </p>
              </div>
            </div>
          </div>
        </Section>

        {/* FAQ / Troubleshooting */}
        <Section id="faq" title="FAQ & Troubleshooting">
          <div className="space-y-4">
            <div className="border-l-4 pl-4" style={{ borderColor: '#06B6D4' }}>
              <h5 className="font-semibold text-white mb-1">What happens if I lose internet connection during an auction?</h5>
              <p className="text-white/80 text-sm">
                The system has automatic reconnection built in. If you disconnect, it will attempt to reconnect you automatically. Your bids and budget are saved on the server.
              </p>
            </div>

            <div className="border-l-4 pl-4" style={{ borderColor: '#06B6D4' }}>
              <h5 className="font-semibold text-white mb-1">Can I change my bid after placing it?</h5>
              <p className="text-white/80 text-sm">
                No, bids are final once placed. This maintains fairness in the auction. Make sure you're comfortable with the price before bidding.
              </p>
            </div>

            <div className="border-l-4 pl-4" style={{ borderColor: '#06B6D4' }}>
              <h5 className="font-semibold text-white mb-1">How does anti-snipe work?</h5>
              <p className="text-white/80 text-sm">
                If a bid is placed in the last few seconds (as configured by the admin), the timer automatically extends by the anti-snipe duration. This prevents unfair last-second wins.
              </p>
            </div>

            <div className="border-l-4 pl-4" style={{ borderColor: '#06B6D4' }}>
              <h5 className="font-semibold text-white mb-1">Can I leave a competition after joining?</h5>
              <p className="text-white/80 text-sm">
                Once the auction starts, you're committed to the competition. Contact your league commissioner if you need to withdraw before the auction begins.
              </p>
            </div>

            <div className="border-l-4 pl-4" style={{ borderColor: '#06B6D4' }}>
              <h5 className="font-semibold text-white mb-1">How are points calculated?</h5>
              <p className="text-white/80 text-sm">
                Points are based on real match outcomes and performance. Your teams earn points when they win matches or achieve specific milestones. The scoring system varies by sport.
              </p>
            </div>

            <div className="border-l-4 pl-4" style={{ borderColor: '#06B6D4' }}>
              <h5 className="font-semibold text-white mb-1">Can I be in multiple competitions at once?</h5>
              <p className="text-white/80 text-sm">
                Yes. You can create or join as many competitions as you like. Each competition is independent with its own auction and standings.
              </p>
            </div>
          </div>
        </Section>

        {/* Support */}
        <div 
          className="rounded-xl p-6 mt-8 text-center"
          style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
        >
          <h3 className="text-xl font-bold text-white mb-3">Need More Help?</h3>
          <p className="text-white/80 mb-4">
            If you have questions not covered in this guide, reach out to your league commissioner or contact support.
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 rounded-xl font-semibold transition-colors"
            style={{ background: '#06B6D4', color: '#0F172A' }}
          >
            Return to Home
          </button>
        </div>
      </div>

      {/* Bottom Navigation */}
      <BottomNav onFabClick={() => navigate('/create-competition')} />
    </div>
  );
};

export default Help;
