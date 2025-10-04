import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import axios from "axios";
import CreateLeague from "./pages/CreateLeague";
import ClubsList from "./pages/ClubsList";
import LeagueDetail from "./pages/LeagueDetail";
import AuctionRoom from "./pages/AuctionRoom";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  // Set test mode attribute on HTML element to disable animations
  useEffect(() => {
    const isTestMode = 
      process.env.REACT_APP_TEST_MODE === 'true' ||
      process.env.NODE_ENV === 'test' ||
      window.location.search.includes('test-mode=true') ||
      localStorage.getItem('test-mode') === 'true';
    
    if (isTestMode) {
      document.documentElement.setAttribute('data-test-mode', 'true');
    } else {
      document.documentElement.removeAttribute('data-test-mode');
    }
  }, []);
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [showCreateLeagueDialog, setShowCreateLeagueDialog] = useState(false);
  const [showJoinLeagueDialog, setShowJoinLeagueDialog] = useState(false);
  const [userForm, setUserForm] = useState({ name: "", email: "" });
  const [leagues, setLeagues] = useState([]);
  const [sports, setSports] = useState([]);
  const [leagueForm, setLeagueForm] = useState({
    name: "",
    sportKey: "football", // Default to football
    budget: 500000000, // £500m default budget
    minManagers: 2,
    maxManagers: 8,
    clubSlots: 3,
  });
  const [inviteToken, setInviteToken] = useState("");

  useEffect(() => {
    loadLeagues();
    loadSports();
  }, []);

  const loadSports = async () => {
    try {
      const response = await axios.get(`${API}/sports`);
      setSports(response.data);
    } catch (e) {
      console.error("Error loading sports:", e);
    }
  };

  const loadLeagues = async () => {
    try {
      const response = await axios.get(`${API}/leagues`);
      const leaguesWithParticipants = await Promise.all(
        response.data.map(async (league) => {
          const participantsResponse = await axios.get(`${API}/leagues/${league.id}/participants`);
          return { ...league, participantCount: participantsResponse.data.length };
        })
      );
      setLeagues(leaguesWithParticipants);
    } catch (e) {
      console.error("Error loading leagues:", e);
    }
  };

  const handleUserSubmit = async (e) => {
    e.preventDefault();
    if (!userForm.name || !userForm.email) {
      alert("Please enter both name and email");
      return;
    }

    try {
      const response = await axios.post(`${API}/users`, userForm);
      setUser(response.data);
      localStorage.setItem("user", JSON.stringify(response.data));
      setShowUserDialog(false);
    } catch (e) {
      console.error("Error creating user:", e);
      alert("Error creating user");
    }
  };

  const handleCreateLeague = async (e) => {
    e.preventDefault();
    if (!user) {
      alert("Please sign in first");
      return;
    }

    try {
      const response = await axios.post(`${API}/leagues`, {
        ...leagueForm,
        commissionerId: user.id,
      });
      
      // Auto-join as commissioner
      await axios.post(`${API}/leagues/${response.data.id}/join`, {
        userId: user.id,
        inviteToken: response.data.inviteToken,
      });
      
      alert(`Strategic competition created! Share this invite token with your competitors: ${response.data.inviteToken}`);
      setShowCreateLeagueDialog(false);
      loadLeagues();
      navigate(`/league/${response.data.id}`);
    } catch (e) {
      console.error("Error creating league:", e);
      alert("Error creating league");
    }
  };

  const handleJoinLeague = async (e) => {
    e.preventDefault();
    if (!user) {
      alert("Please sign in first");
      return;
    }

    try {
      // Trim whitespace and normalize token (handle copy-paste issues)
      const normalizedToken = inviteToken.trim().toLowerCase();
      
      if (!normalizedToken) {
        alert("Please enter an invite token");
        return;
      }

      // Find league by invite token (case-insensitive)
      const leaguesResponse = await axios.get(`${API}/leagues`);
      const league = leaguesResponse.data.find((l) => 
        l.inviteToken.trim().toLowerCase() === normalizedToken
      );
      
      if (!league) {
        alert(`Invalid invite token "${inviteToken.trim()}". Please check with your league commissioner for the correct token.`);
        return;
      }

      await axios.post(`${API}/leagues/${league.id}/join`, {
        userId: user.id,
        inviteToken: inviteToken.trim(), // Send trimmed token to backend
      });

      alert(`Successfully joined the strategic competition "${league.name}"! Ready to start bidding.`);
      setShowJoinLeagueDialog(false);
      setInviteToken("");
      loadLeagues();
      navigate(`/league/${league.id}`);
    } catch (e) {
      console.error("Error joining league:", e);
      // Show the backend error message which includes helpful details
      alert(e.response?.data?.detail || "Error joining league");
    }
  };

  const handleDeleteLeague = async (league, e) => {
    e.stopPropagation(); // Prevent navigation to league detail
    
    if (!user) {
      alert("Please sign in first");
      return;
    }

    if (league.commissionerId !== user.id) {
      alert("Only the commissioner can delete this league");
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to delete "${league.name}"? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await axios.delete(`${API}/leagues/${league.id}?user_id=${user.id}`);
      alert("League deleted successfully");
      loadLeagues();
    } catch (e) {
      console.error("Error deleting league:", e);
      alert(e.response?.data?.detail || "Error deleting league");
    }
  };

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900">
      {/* User Dialog */}
      {showUserDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">Enter Your Details</h2>
            <form onSubmit={handleUserSubmit}>
              <div className="mb-4">
                <label className="block text-gray-700 mb-2">Name</label>
                <input
                  type="text"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={userForm.name}
                  onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
                  data-testid="user-name-input"
                />
              </div>
              <div className="mb-4">
                <label className="block text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={userForm.email}
                  onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                  data-testid="user-email-input"
                />
              </div>
              <button
                type="submit"
                className="btn btn-primary w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                data-testid="user-submit-button"
              >
                Continue
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Create League Dialog */}
      {showCreateLeagueDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto app-card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Create Your Competition</h2>
              <button
                onClick={() => setShowCreateLeagueDialog(false)}
                className="btn btn-secondary text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateLeague}>
              <div className="mb-4">
                <label className="block text-gray-700 mb-2 font-semibold">League Name</label>
                <input
                  type="text"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={leagueForm.name}
                  onChange={(e) => setLeagueForm({ ...leagueForm, name: e.target.value })}
                  required
                  data-testid="league-name-input"
                />
              </div>

              <div className="mb-4">
                <label className="block text-gray-700 mb-2 font-semibold">Sport</label>
                <select
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={leagueForm.sportKey}
                  onChange={(e) => setLeagueForm({ ...leagueForm, sportKey: e.target.value })}
                  data-testid="create-sport-select"
                >
                  <option value="football">Football</option>
                  {sports.find(s => s.key === 'cricket') && (
                    <option value="cricket">Cricket</option>
                  )}
                </select>
                <p className="text-sm text-gray-500 mt-1">
                  Choose the sport for your competition
                </p>
              </div>

              <div className="mb-4">
                <label className="block text-gray-700 mb-2 font-semibold">
                  Budget per Manager (£)
                </label>
                <input
                  type="number"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={leagueForm.budget}
                  onChange={(e) => setLeagueForm({ ...leagueForm, budget: Number(e.target.value) })}
                  min="100"
                  required
                  data-testid="league-budget-input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-gray-700 mb-2 font-semibold">Min Managers</label>
                  <input
                    type="number"
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={leagueForm.minManagers}
                    onChange={(e) => setLeagueForm({ ...leagueForm, minManagers: Number(e.target.value) })}
                    min="2"
                    max="8"
                    required
                    data-testid="league-min-managers-input"
                  />
                </div>

                <div>
                  <label className="block text-gray-700 mb-2 font-semibold">Max Managers</label>
                  <input
                    type="number"
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={leagueForm.maxManagers}
                    onChange={(e) => setLeagueForm({ ...leagueForm, maxManagers: Number(e.target.value) })}
                    min="2"
                    max="8"
                    required
                    data-testid="league-max-managers-input"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-gray-700 mb-2 font-semibold">
                  {sports.find(s => s.key === leagueForm.sportKey)?.uiHints.assetPlural || "Assets"} per Manager (1-10)
                </label>
                <input
                  type="number"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={leagueForm.clubSlots}
                  onChange={(e) => setLeagueForm({ ...leagueForm, clubSlots: Number(e.target.value) })}
                  min="1"
                  max="10"
                  required
                  data-testid="league-club-slots-input"
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold text-lg"
                data-testid="create-league-submit"
              >
                Create Competition
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Join League Dialog */}
      {showJoinLeagueDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Join the Competition</h2>
              <button
                onClick={() => setShowJoinLeagueDialog(false)}
                className="btn btn-secondary text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleJoinLeague}>
              <div className="mb-4">
                <label className="block text-gray-700 mb-2 font-semibold">Invite Token</label>
                <input
                  type="text"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter 8-character invite token"
                  value={inviteToken}
                  onChange={(e) => setInviteToken(e.target.value)}
                  maxLength={8}
                  required
                  data-testid="invite-token-input"
                />
                <p className="text-sm text-gray-500 mt-2">
                  Get the invite token from your competition commissioner to join the strategic arena
                </p>
              </div>

              <button
                type="submit"
                className="btn btn-primary w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold"
                data-testid="join-league-submit"
              >
                Join the Competition
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-md app-header">
        <div className="container-narrow mx-auto px-4 py-4 flex justify-between items-center">
          <span data-testid="nav-brand" className="h2">Friends of PIFA</span>
          {user ? (
            <div className="flex items-center gap-4">
              <span className="text-gray-700">
                <strong>{user.name}</strong> ({user.email})
              </span>
              <button
                onClick={() => setShowUserDialog(true)}
                className="btn btn-secondary text-sm text-blue-600 hover:underline"
              >
                Change
              </button>
              <button
                onClick={() => {
                  localStorage.removeItem("user");
                  setUser(null);
                }}
                className="btn btn-secondary text-sm text-red-600 hover:underline"
                data-testid="logout-button"
              >
                Logout
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowUserDialog(true)}
              className="btn btn-primary bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              data-testid="login-button"
            >
              Sign In
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="container-narrow mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="h1 text-3xl font-bold mb-6 text-gray-900">Welcome to Friends of PIFA</h2>
          <p className="h2 text-lg font-semibold text-blue-900 mb-2">Sports Gaming with Friends. No Gambling. All Strategy.</p>
          <p className="subtle text-gray-600 mb-8">
            Bid for exclusive ownership of players and teams who score your points. Experience the thrill of sports through strategic competition and community.
          </p>

          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <button
              onClick={() => {
                if (!user) {
                  setShowUserDialog(true);
                } else {
                  setShowCreateLeagueDialog(true);
                }
              }}
              className="btn btn-primary bg-green-600 text-white px-6 py-4 rounded-lg hover:bg-green-700 text-lg font-semibold"
              data-testid="create-league-button"
            >
              Create Your Competition
            </button>
            <button
              onClick={() => {
                if (!user) {
                  setShowUserDialog(true);
                } else {
                  setShowJoinLeagueDialog(true);
                }
              }}
              className="btn btn-primary bg-blue-600 text-white px-6 py-4 rounded-lg hover:bg-blue-700 text-lg font-semibold"
              data-testid="join-league-button"
            >
              Join the Competition
            </button>
            <button
              onClick={() => navigate("/clubs")}
              className="btn btn-primary bg-purple-600 text-white px-6 py-4 rounded-lg hover:bg-purple-700 text-lg font-semibold"
              data-testid="view-clubs-button"
            >
              Explore Available Assets
            </button>
          </div>

          {/* Active Leagues - Compact Horizontal Layout */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="h2 text-2xl font-bold text-gray-900">Active Leagues</h3>
              {leagues.length > 0 && (
                <p className="text-sm text-gray-500">{leagues.length} competitions</p>
              )}
            </div>
            {leagues.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg">
                <p className="text-gray-500 text-lg">🏆 No competitions yet</p>
                <p className="text-gray-400 text-sm mt-2">Create your strategic arena to get started!</p>
              </div>
            ) : (
              <div className="overflow-x-auto pb-4">
                <div className="flex space-x-4 min-w-max">
                  {leagues.map((league) => {
                    const isCommissioner = user && league.commissionerId === user.id;
                    const sportIcon = league.sportKey === 'football' ? '⚽' : league.sportKey === 'cricket' ? '🏏' : '🏆';
                    const sportName = league.sportKey === 'football' ? 'Football' : league.sportKey === 'cricket' ? 'Cricket' : league.sportKey;
                    
                    return (
                      <div
                        key={league.id}
                        className="flex-shrink-0 w-72 border rounded-lg p-4 hover:shadow-md transition-all duration-200 cursor-pointer app-card bg-white hover:bg-gray-50"
                        onClick={() => navigate(`/league/${league.id}`)}
                        data-testid={`league-card-${league.id}`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">{sportIcon}</span>
                            <span className="chip bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-medium">
                              {sportName}
                            </span>
                          </div>
                          {isCommissioner && (
                            <span className="chip bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs font-medium">
                              Commissioner
                            </span>
                          )}
                        </div>
                        
                        <h4 className="text-lg font-semibold text-gray-900 mb-2 truncate" title={league.name}>
                          {league.name}
                        </h4>
                        
                        <div className="space-y-2 text-sm text-gray-600">
                          <div className="flex justify-between">
                            <span>Budget:</span>
                            <span className="font-medium">£{(league.budget / 1000000).toFixed(0)}M</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Managers:</span>
                            <span className={`font-medium ${league.participantCount >= league.minManagers ? 'text-green-600' : ''}`}>
                              {league.participantCount || 0}/{league.maxManagers}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Slots:</span>
                            <span className="font-medium">{league.clubSlots}</span>
                          </div>
                        </div>
                        
                        {league.participantCount >= league.minManagers && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <span className="text-xs text-green-600 font-medium">✓ Ready for Competition</span>
                          </div>
                        )}
                        
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <p className="text-xs text-gray-500">
                            Token: <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">{league.inviteToken}</code>
                          </p>
                        </div>
                      </div>
                    );
                  })}
                  
                  {/* Add League Card */}
                  <div
                    className="flex-shrink-0 w-72 border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 cursor-pointer flex flex-col items-center justify-center text-center"
                    onClick={() => {
                      if (!user) {
                        setShowUserDialog(true);
                      } else {
                        setShowCreateLeagueDialog(true);
                      }
                    }}
                  >
                    <div className="text-4xl mb-3 text-gray-400">+</div>
                    <h4 className="text-lg font-semibold text-gray-700 mb-2">Create New Competition</h4>
                    <p className="text-sm text-gray-500">Start your own strategic arena</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/create-league" element={<CreateLeague />} />
        <Route path="/clubs" element={<ClubsList />} />
        <Route path="/league/:leagueId" element={<LeagueDetail />} />
        <Route path="/auction/:auctionId" element={<AuctionRoom />} />
      </Routes>
    </BrowserRouter>
  );
}