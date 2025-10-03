import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import axios from "axios";
import CreateLeague from "./pages/CreateLeague";
import ClubsList from "./pages/ClubsList";
import LeagueDetail from "./pages/LeagueDetail";
import AuctionRoom from "./pages/AuctionRoom";
import { ThemeProvider } from "./hooks/useTheme";
import { ThemeToggle } from "./components/ThemeToggle";
// import { brandTokens } from "./brand/brand.ts";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [showCreateLeagueDialog, setShowCreateLeagueDialog] = useState(false);
  const [showJoinLeagueDialog, setShowJoinLeagueDialog] = useState(false);
  const [userForm, setUserForm] = useState({ name: "", email: "" });
  const [leagues, setLeagues] = useState([]);
  const [leagueForm, setLeagueForm] = useState({
    name: "",
    budget: 500000000, // £500m default budget
    minManagers: 2,
    maxManagers: 8,
    clubSlots: 3,
  });
  const [inviteToken, setInviteToken] = useState("");

  useEffect(() => {
    loadLeagues();
  }, []);

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
      
      alert(`League created! Invite Token: ${response.data.inviteToken}`);
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

      alert(`Successfully joined "${league.name}"!`);
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
    <div className="min-h-screen bg-background">
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
                className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
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
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Create New League</h2>
              <button
                onClick={() => setShowCreateLeagueDialog(false)}
                className="text-gray-500 hover:text-gray-700"
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
                  Club Slots per Manager (1-10)
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
                className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold text-lg"
                data-testid="create-league-submit"
              >
                Create League
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
              <h2 className="text-2xl font-bold text-gray-900">Join League</h2>
              <button
                onClick={() => setShowJoinLeagueDialog(false)}
                className="text-gray-500 hover:text-gray-700"
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
                  Get the invite token from your league commissioner
                </p>
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold"
                data-testid="join-league-submit"
              >
                Join League
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-card border-b border-border shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-foreground">Friends of PIFA</h1>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <div className="flex items-center gap-4">
            {user ? (
              <>
                <span className="text-muted-foreground">
                  <strong>{user.name}</strong> ({user.email})
                </span>
                <button
                  onClick={() => setShowUserDialog(true)}
                  className="text-sm text-primary hover:underline"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowUserDialog(true)}
                className="bg-primary text-primary-foreground px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="bg-card border border-border rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold mb-6 text-foreground">Welcome to Friends of PIFA</h2>
          <p className="text-muted-foreground mb-8">
            Bid for exclusive ownership of UCL teams and compete with friends!
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
              className="bg-secondary text-secondary-foreground px-6 py-4 rounded-lg hover:bg-secondary/90 text-lg font-semibold transition-colors"
              data-testid="create-league-button"
            >
              Create New League
            </button>
            <button
              onClick={() => {
                if (!user) {
                  setShowUserDialog(true);
                } else {
                  setShowJoinLeagueDialog(true);
                }
              }}
              className="bg-primary text-primary-foreground px-6 py-4 rounded-lg hover:bg-primary/90 text-lg font-semibold transition-colors"
              data-testid="join-league-button"
            >
              Join League
            </button>
            <button
              onClick={() => navigate("/clubs")}
              className="bg-accent text-accent-foreground px-6 py-4 rounded-lg hover:bg-accent/90 text-lg font-semibold transition-colors"
              data-testid="view-clubs-button"
            >
              View All Clubs
            </button>
          </div>

          {/* Active Leagues */}
          <div>
            <h3 className="text-2xl font-bold mb-4 text-gray-900">Active Leagues</h3>
            {leagues.length === 0 ? (
              <p className="text-gray-500">No leagues yet. Create one to get started!</p>
            ) : (
              <div className="grid gap-4">
                {leagues.map((league) => {
                  const isCommissioner = user && league.commissionerId === user.id;
                  return (
                    <div
                      key={league.id}
                      className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => navigate(`/league/${league.id}`)}
                      data-testid={`league-card-${league.id}`}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="text-xl font-semibold text-gray-900 mb-2">{league.name}</h4>
                          <p className="text-gray-600 text-sm mb-1">
                            Budget: £{league.budget.toLocaleString()} | Slots: {league.clubSlots}
                          </p>
                          <p className="text-gray-600 text-sm">
                            Managers: {league.participantCount || 0}/{league.maxManagers} 
                            {league.participantCount >= league.minManagers && (
                              <span className="text-green-600 ml-2">✓ Ready to start</span>
                            )}
                          </p>
                          <p className="text-xs text-gray-500 mt-2">
                            Invite Token: <code className="bg-gray-100 px-2 py-1 rounded">{league.inviteToken}</code>
                          </p>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <span
                            className={`px-3 py-1 rounded-full text-sm font-semibold ${
                              league.status === "active"
                                ? "bg-green-100 text-green-800"
                                : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {league.status}
                          </span>
                          {isCommissioner && (
                            <button
                              onClick={(e) => handleDeleteLeague(league, e)}
                              className="text-red-600 hover:text-red-800 text-sm font-semibold"
                              data-testid={`delete-league-${league.id}`}
                            >
                              🗑️ Delete
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/create-league" element={<CreateLeague />} />
          <Route path="/clubs" element={<ClubsList />} />
          <Route path="/league/:leagueId" element={<LeagueDetail />} />
          <Route path="/auction/:auctionId" element={<AuctionRoom />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}