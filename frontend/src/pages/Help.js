import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

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

  const Section = ({ id, title, children, icon }) => (
    <div className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => toggleSection(id)}
        className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        <svg
          className={`w-6 h-6 text-gray-600 transition-transform ${openSection === id ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {openSection === id && (
        <div className="p-6 bg-white">
          {children}
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-blue-600 hover:text-blue-700 font-semibold"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Home
          </button>
          <div>
            <div className="text-xs uppercase tracking-wide text-gray-500 mb-1 text-center">Help Center</div>
            <h1 className="text-2xl font-bold text-gray-900">User Guide</h1>
          </div>
          <div className="w-24"></div> {/* Spacer for centering */}
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Introduction */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <h2 className="text-2xl font-bold text-blue-900 mb-3">Welcome to Friends of PIFA!</h2>
          <p className="text-blue-800 mb-2">
            Sports Gaming with Friends. No Gambling. All Strategy.
          </p>
          <p className="text-blue-700">
            Bid for exclusive ownership of players and teams who score your points. Experience the thrill of sports through strategic competition and community.
          </p>
        </div>

        {/* Quick Links */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Quick Navigation</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <button onClick={() => toggleSection('getting-started')} className="text-left px-4 py-2 bg-blue-50 hover:bg-blue-100 rounded-lg text-blue-700 font-medium transition-colors">
              🚀 Getting Started
            </button>
            <button onClick={() => toggleSection('admin-create')} className="text-left px-4 py-2 bg-purple-50 hover:bg-purple-100 rounded-lg text-purple-700 font-medium transition-colors">
              👑 For Commissioners
            </button>
            <button onClick={() => toggleSection('user-join')} className="text-left px-4 py-2 bg-green-50 hover:bg-green-100 rounded-lg text-green-700 font-medium transition-colors">
              👥 For Players
            </button>
            <button onClick={() => toggleSection('dashboards')} className="text-left px-4 py-2 bg-orange-50 hover:bg-orange-100 rounded-lg text-orange-700 font-medium transition-colors">
              📊 Viewing Results
            </button>
          </div>
        </div>

        {/* Getting Started */}
        <Section id="getting-started" title="Getting Started" icon="🚀">
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3">Account Setup & Sign In</h4>
              <p className="text-gray-700 mb-3">
                Friends of PIFA uses a secure <strong>magic link authentication</strong> system. No passwords required!
              </p>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h5 className="font-semibold text-gray-900 mb-2">Step-by-Step Sign In:</h5>
                <ol className="list-decimal list-inside space-y-2 text-gray-700">
                  <li>Click <strong>"Sign In"</strong> on the homepage</li>
                  <li>Enter your <strong>email address</strong> and optionally your name</li>
                  <li>Click <strong>"Continue"</strong> to generate your magic link token</li>
                  <li>You'll receive a <strong>6-digit token</strong> displayed on screen</li>
                  <li>Enter this token in the next step to complete sign in</li>
                  <li>Your session will be securely maintained for easy access</li>
                </ol>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-800 text-sm">
                  <strong>💡 Tip:</strong> In production, the magic link token would be sent to your email. For the pilot, it's displayed on screen for convenience.
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3">First Steps After Sign In</h4>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                <li><strong>Create a Competition:</strong> Start your own league if you're the organizer</li>
                <li><strong>Join a Competition:</strong> Enter an invite token from a friend</li>
                <li><strong>Explore Available Teams:</strong> Browse the sports teams available for bidding</li>
              </ul>
            </div>
          </div>
        </Section>

        {/* For League Admins */}
        <Section id="admin-create" title="For League Admins" icon="👑">
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3">Creating a Competition</h4>
              <p className="text-gray-700 mb-3">
                As a league admin, you control the competition setup and manage the auction process.
              </p>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h5 className="font-semibold text-gray-900 mb-2">Competition Setup Steps:</h5>
                <ol className="list-decimal list-inside space-y-2 text-gray-700">
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

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
                <p className="text-purple-800 text-sm mb-2">
                  <strong>💡 Key Settings Explained:</strong>
                </p>
                <ul className="text-purple-700 text-sm space-y-1 list-disc list-inside">
                  <li><strong>Budget:</strong> Total virtual currency each manager gets for bidding</li>
                  <li><strong>Club Slots:</strong> Maximum teams each participant can acquire</li>
                  <li><strong>Auction Timer:</strong> Countdown for each bid - longer gives more thinking time</li>
                  <li><strong>Anti-Snipe:</strong> Extends timer if bid comes in the last few seconds</li>
                </ul>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800 text-sm">
                  <strong>⚠️ Important:</strong> After creating the competition, you'll receive an <strong>8-character invite token</strong>. Share this with your participants so they can join!
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3">Running the Auction</h4>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h5 className="font-semibold text-gray-900 mb-2">Auction Control Steps:</h5>
                <ol className="list-decimal list-inside space-y-2 text-gray-700">
                  <li>Wait for all managers to join using the invite token</li>
                  <li>Navigate to your competition page from "My Competitions"</li>
                  <li>Click <strong>"Start Auction"</strong> when ready</li>
                  <li>The first team will be nominated for bidding automatically</li>
                  <li>Managers place bids in real-time until timer expires</li>
                  <li>After each team is won, click <strong>"Next Team"</strong> to continue</li>
                  <li>Auction concludes when all slots are filled</li>
                </ol>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-purple-800 text-sm">
                  <strong>💡 Admin Controls:</strong> As the commissioner, you have full control to start, pause, and manage the auction flow. You can see all bids in real-time and ensure fair play.
                </p>
              </div>
            </div>
          </div>
        </Section>

        {/* For Players */}
        <Section id="user-join" title="For Players" icon="👥">
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3">Joining a Competition</h4>
              <p className="text-gray-700 mb-3">
                To join a competition, you'll need an invite token from the league admin.
              </p>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h5 className="font-semibold text-gray-900 mb-2">How to Join:</h5>
                <ol className="list-decimal list-inside space-y-2 text-gray-700">
                  <li>Get the <strong>8-character invite token</strong> from your league commissioner</li>
                  <li>Click <strong>"Join the Competition"</strong> on the homepage</li>
                  <li>Enter the invite token</li>
                  <li>Click <strong>"Join"</strong> to confirm</li>
                  <li>Wait for the commissioner to start the auction</li>
                </ol>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 text-sm">
                  <strong>✅ Success:</strong> Once joined, you'll see the competition in your "My Competitions" list and receive your starting budget for bidding!
                </p>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3">Participating in Auctions</h4>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h5 className="font-semibold text-gray-900 mb-2">Bidding Strategy:</h5>
                <ol className="list-decimal list-inside space-y-2 text-gray-700">
                  <li><strong>Wait for auction to start:</strong> The commissioner will begin when all managers are ready</li>
                  <li><strong>View current team:</strong> See the team up for bidding and its base price</li>
                  <li><strong>Monitor your budget:</strong> Keep track of remaining funds for future bids</li>
                  <li><strong>Place strategic bids:</strong> Click "Place Bid" to increase the current price</li>
                  <li><strong>Watch the timer:</strong> Bids in the last seconds trigger anti-snipe extension</li>
                  <li><strong>Win teams strategically:</strong> Balance your budget across multiple teams</li>
                </ol>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-blue-800 text-sm mb-2">
                  <strong>💡 Pro Tips:</strong>
                </p>
                <ul className="text-blue-700 text-sm space-y-1 list-disc list-inside">
                  <li>Don't spend all your budget on the first few teams</li>
                  <li>Consider team performance and upcoming fixtures</li>
                  <li>Watch other managers' budgets to gauge competition</li>
                  <li>Anti-snipe timer prevents unfair last-second wins</li>
                  <li>Stay active - auctions move fast with engaged participants!</li>
                </ul>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800 text-sm">
                  <strong>⚠️ Remember:</strong> Each bid increases the price by a set increment. Make sure you have enough budget remaining before placing a bid!
                </p>
              </div>
            </div>
          </div>
        </Section>

        {/* Dashboards & Results */}
        <Section id="dashboards" title="Viewing Dashboards & Results" icon="📊">
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3">Competition Dashboard</h4>
              <p className="text-gray-700 mb-3">
                After the auction, track your teams' performance and standings in real-time.
              </p>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h5 className="font-semibold text-gray-900 mb-2">Dashboard Features:</h5>
                <ul className="list-disc list-inside space-y-2 text-gray-700">
                  <li><strong>Leaderboard:</strong> See all managers ranked by total points</li>
                  <li><strong>Your Teams:</strong> View all teams you won in the auction</li>
                  <li><strong>Team Details:</strong> Click any team to see their match history</li>
                  <li><strong>Live Updates:</strong> Points update automatically when matches conclude</li>
                  <li><strong>Competition Stats:</strong> Overall budget spent, teams owned, rankings</li>
                </ul>
              </div>

              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <p className="text-orange-800 text-sm">
                  <strong>📈 Access Dashboard:</strong> Click on any competition from "My Competitions" to view its live dashboard and track your performance!
                </p>
              </div>
            </div>


            <div>
              <h4 className="text-lg font-semibold text-gray-900 mb-3">Finding Your Competitions</h4>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <ol className="list-decimal list-inside space-y-2 text-gray-700">
                  <li>Click <strong>"My Competitions"</strong> in the top navigation</li>
                  <li>View all competitions you've created or joined</li>
                  <li>See current status: Pending, Auction Live, or Completed</li>
                  <li>Click any competition to view its dashboard</li>
                </ol>
              </div>
            </div>
          </div>
        </Section>

        {/* FAQ / Troubleshooting */}
        <Section id="faq" title="FAQ & Troubleshooting" icon="❓">
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h5 className="font-semibold text-gray-900 mb-1">What happens if I lose internet connection during an auction?</h5>
              <p className="text-gray-700 text-sm">
                The system has automatic reconnection built in. If you disconnect, it will attempt to reconnect you automatically. Your bids and budget are saved on the server.
              </p>
            </div>

            <div className="border-l-4 border-blue-500 pl-4">
              <h5 className="font-semibold text-gray-900 mb-1">Can I change my bid after placing it?</h5>
              <p className="text-gray-700 text-sm">
                No, bids are final once placed. This maintains fairness in the auction. Make sure you're comfortable with the price before bidding!
              </p>
            </div>

            <div className="border-l-4 border-blue-500 pl-4">
              <h5 className="font-semibold text-gray-900 mb-1">How does anti-snipe work?</h5>
              <p className="text-gray-700 text-sm">
                If a bid is placed in the last few seconds (as configured by the admin), the timer automatically extends by the anti-snipe duration. This prevents unfair last-second wins.
              </p>
            </div>

            <div className="border-l-4 border-blue-500 pl-4">
              <h5 className="font-semibold text-gray-900 mb-1">Can I leave a competition after joining?</h5>
              <p className="text-gray-700 text-sm">
                Once the auction starts, you're committed to the competition. Contact your league commissioner if you need to withdraw before the auction begins.
              </p>
            </div>

            <div className="border-l-4 border-blue-500 pl-4">
              <h5 className="font-semibold text-gray-900 mb-1">How are points calculated?</h5>
              <p className="text-gray-700 text-sm">
                Points are based on real match outcomes and performance. Your teams earn points when they win matches or achieve specific milestones. The scoring system varies by sport.
              </p>
            </div>

            <div className="border-l-4 border-blue-500 pl-4">
              <h5 className="font-semibold text-gray-900 mb-1">Can I be in multiple competitions at once?</h5>
              <p className="text-gray-700 text-sm">
                Yes! You can create or join as many competitions as you like. Each competition is independent with its own auction and standings.
              </p>
            </div>
          </div>
        </Section>

        {/* Support */}
        <div className="bg-gray-100 rounded-lg p-6 mt-8 text-center">
          <h3 className="text-xl font-bold text-gray-900 mb-3">Need More Help?</h3>
          <p className="text-gray-700 mb-4">
            If you have questions not covered in this guide, reach out to your league commissioner or contact support.
          </p>
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold transition-colors"
          >
            Return to Home
          </button>
        </div>
      </div>
    </div>
  );
};

export default Help;
