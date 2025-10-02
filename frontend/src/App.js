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
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [showCreateLeagueDialog, setShowCreateLeagueDialog] = useState(false);
  const [showJoinLeagueDialog, setShowJoinLeagueDialog] = useState(false);
  const [userForm, setUserForm] = useState({ name: "", email: "" });
  const [leagues, setLeagues] = useState([]);
  const [leagueForm, setLeagueForm] = useState({
    name: "",
    budget: 1000,
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
      // Find league by invite token
      const leaguesResponse = await axios.get(`${API}/leagues`);
      const league = leaguesResponse.data.find((l) => l.inviteToken === inviteToken);
      
      if (!league) {
        alert("Invalid invite token");
        return;
      }

      await axios.post(`${API}/leagues/${league.id}/join`, {
        userId: user.id,
        inviteToken: inviteToken,
      });

      alert("Joined league successfully!");
      setShowJoinLeagueDialog(false);
      setInviteToken("");
      loadLeagues();
      navigate(`/league/${league.id}`);
    } catch (e) {
      console.error("Error joining league:", e);
      alert(e.response?.data?.detail || "Error joining league");
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
                className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
                data-testid="user-submit-button"
              >
                Continue
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-blue-900">UEFA Club Auction</h1>
          {user ? (
            <div className="flex items-center gap-4">
              <span className="text-gray-700">
                <strong>{user.name}</strong> ({user.email})
              </span>
              <button
                onClick={() => setShowUserDialog(true)}
                className="text-sm text-blue-600 hover:underline"
              >
                Change
              </button>
              <button
                onClick={() => {
                  localStorage.removeItem("user");
                  setUser(null);
                }}
                className="text-sm text-red-600 hover:underline"
                data-testid="logout-button"
              >
                Logout
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowUserDialog(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              data-testid="login-button"
            >
              Sign In
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-3xl font-bold mb-6 text-gray-900">Welcome to UEFA Club Auction</h2>
          <p className="text-gray-600 mb-8">
            Bid on UEFA Champions League clubs and build your dream team!
          </p>

          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <button
              onClick={() => navigate("/create-league")}
              className="bg-green-600 text-white px-6 py-4 rounded-lg hover:bg-green-700 text-lg font-semibold"
              data-testid="create-league-button"
            >
              Create New League
            </button>
            <button
              onClick={() => navigate("/clubs")}
              className="bg-purple-600 text-white px-6 py-4 rounded-lg hover:bg-purple-700 text-lg font-semibold"
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
                {leagues.map((league) => (
                  <div
                    key={league.id}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => navigate(`/league/${league.id}`)}
                    data-testid={`league-card-${league.id}`}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="text-xl font-semibold text-gray-900">{league.name}</h4>
                        <p className="text-gray-600">
                          Budget: ${league.budget} | Slots: {league.clubSlots} | Status: {league.status}
                        </p>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          league.status === "active"
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {league.status}
                      </span>
                    </div>
                  </div>
                ))}
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