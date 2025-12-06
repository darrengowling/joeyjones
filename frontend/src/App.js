import { useState, useEffect, lazy, Suspense } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import axios from "axios";
import toast, { Toaster } from "react-hot-toast";
import { formatCurrency } from "./utils/currency";
import { setUser as setSentryUser, clearUser as clearSentryUser, captureException, addBreadcrumb } from "./utils/sentry";
import { clearSocketUser } from "./utils/socket";

// Lazy load route components for better performance (Production Hardening Day 11)
const CreateLeague = lazy(() => import("./pages/CreateLeague"));
const ClubsList = lazy(() => import("./pages/ClubsList"));
const LeagueDetail = lazy(() => import("./pages/LeagueDetail"));
const AuctionRoom = lazy(() => import("./pages/AuctionRoom"));
const MyCompetitions = lazy(() => import("./pages/MyCompetitions"));
const CompetitionDashboard = lazy(() => import("./pages/CompetitionDashboard"));
const Help = lazy(() => import("./pages/Help"));

// Loading component for lazy-loaded routes
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios to include JWT token in all requests
axios.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem("accessToken");
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    // Maintain backward compatibility with X-User-ID header for existing functionality
    const user = localStorage.getItem("user");
    if (user) {
      const userData = JSON.parse(user);
      config.headers["X-User-ID"] = userData.id;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle token refresh on 401
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Capture API errors in Sentry
    if (error.response) {
      // Server responded with error status
      captureException(error, {
        url: originalRequest?.url,
        method: originalRequest?.method,
        status: error.response.status,
        data: error.response.data,
      });
    } else if (error.request) {
      // Request was made but no response
      captureException(error, {
        url: originalRequest?.url,
        method: originalRequest?.method,
        message: "No response from server",
      });
    }

    // If 401 and we haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refreshToken");
        if (refreshToken) {
          const response = await axios.post(`${API}/auth/refresh`, {
            refreshToken: refreshToken,
          });

          const { accessToken } = response.data;
          localStorage.setItem("accessToken", accessToken);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return axios(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear auth and redirect to login
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("user");
        clearSentryUser();
        window.location.href = "/";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

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
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authStep, setAuthStep] = useState("email"); // "email" or "token"
  const [magicToken, setMagicToken] = useState(""); // Token returned from magic link endpoint
  const [tokenInput, setTokenInput] = useState(""); // User's token input
  const [creatingLeague, setCreatingLeague] = useState(false);
  const [joiningLeague, setJoiningLeague] = useState(false);
  const [leagues, setLeagues] = useState([]);
  const [sports, setSports] = useState([]);
  const [leagueForm, setLeagueForm] = useState({
    name: "",
    sportKey: "football", // Default to football
    competitionCode: "PL", // Default to Premier League
    budget: 500000000, // £500m default budget
    minManagers: 2,
    maxManagers: 8,
    clubSlots: 3,
    timerSeconds: 30, // Prompt D: Default 30s timer
    antiSnipeSeconds: 10, // Prompt D: Default 10s anti-snipe
  });
  const [budgetDisplay, setBudgetDisplay] = useState("500"); // Display in millions
  const [inviteToken, setInviteToken] = useState("");
  const [userCompetitions, setUserCompetitions] = useState([]);
  const [showCompetitionsCTA, setShowCompetitionsCTA] = useState(false);

  useEffect(() => {
    loadSports();
    
    // Load user from localStorage
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
      } catch (e) {
        console.error("Error parsing user data:", e);
      }
    }
  }, []);

  // Load leagues and user competitions when user changes
  useEffect(() => {
    if (user) {
      loadLeagues();
      loadUserCompetitions(user.id);
    } else {
      setLeagues([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const loadUserCompetitions = async (userId) => {
    try {
      const response = await axios.get(`${API}/me/competitions`, {
        params: { userId }
      });
      setUserCompetitions(response.data);
      
      // Show CTA if user has leagues and no active auction
      const hasLeagues = response.data.length > 0;
      const hasActiveAuction = response.data.some(comp => comp.status === "auction_live");
      setShowCompetitionsCTA(hasLeagues && !hasActiveAuction);
    } catch (e) {
      console.error("Error loading user competitions:", e);
    }
  };

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
      // If user is logged in, show only their leagues
      if (user) {
        const response = await axios.get(`${API}/me/competitions`, {
          params: { userId: user.id }
        });
        
        // Get full details for each league
        const leaguesWithDetails = await Promise.all(
          response.data.map(async (comp) => {
            try {
              const leagueResponse = await axios.get(`${API}/leagues/${comp.leagueId}`);
              const participantsResponse = await axios.get(`${API}/leagues/${comp.leagueId}/participants`);
              return {
                ...leagueResponse.data,
                participantCount: participantsResponse.data.count || 0
              };
            } catch (err) {
              console.error(`Error loading league ${comp.leagueId}:`, err);
              return null;
            }
          })
        );
        
        // Filter out any failed requests
        setLeagues(leaguesWithDetails.filter(league => league !== null));
      } else {
        // If not logged in, show no leagues (they need to log in first)
        setLeagues([]);
      }
    } catch (e) {
      console.error("Error loading leagues:", e);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError("");

    // Step 1: Request magic link
    if (authStep === "email") {
      if (!userForm.email || !userForm.email.includes("@")) {
        setAuthError("Please enter a valid email address");
        setAuthLoading(false);
        return;
      }

      try {
        // Request magic link
        const response = await axios.post(`${API}/auth/magic-link`, {
          email: userForm.email.trim().toLowerCase(),
        });

        // Store the token (in pilot mode, it's returned directly)
        setMagicToken(response.data.token);
        setAuthStep("token");
        setAuthError("");
        toast.success("Magic link generated! Enter the token below.");
      } catch (error) {
        console.error("Magic link generation error:", error);
        const errorMessage = error.response?.data?.detail || error.message || "Unable to send magic link. Check your email address and internet connection, then try again.";
        setAuthError(errorMessage);
      } finally {
        setAuthLoading(false);
      }
      return;
    }

    // Step 2: Verify magic link token
    if (authStep === "token") {
      if (!tokenInput.trim()) {
        setAuthError("Please enter the magic link token");
        setAuthLoading(false);
        return;
      }

      try {
        // Verify magic link and get JWT tokens
        const response = await axios.post(`${API}/auth/verify-magic-link`, {
          email: userForm.email.trim().toLowerCase(),
          token: tokenInput.trim(),
        });

        const { accessToken, refreshToken, user } = response.data;

        // Store tokens and user data
        localStorage.setItem("accessToken", accessToken);
        localStorage.setItem("refreshToken", refreshToken);
        localStorage.setItem("user", JSON.stringify(user));

        setUser(user);
        setSentryUser(user); // Track user in Sentry
        addBreadcrumb("User signed in", { email: user.email }, "auth");
        setShowUserDialog(false);
        setUserForm({ name: "", email: "" });
        setTokenInput("");
        setAuthStep("email");
        setAuthError("");
        toast.success("Successfully signed in!");
      } catch (error) {
        console.error("Token verification error:", error);
        const errorMessage = error.response?.data?.detail || error.message || "Invalid or expired magic link token. Request a new link and try again within 15 minutes.";
        setAuthError(errorMessage);
      } finally {
        setAuthLoading(false);
      }
    }
  };

  const handleCreateCompetition = () => {
    if (!user) {
      setAuthError(""); // Clear any previous auth errors
      setShowUserDialog(true);
    } else {
      setShowCreateLeagueDialog(true);
    }
  };

  const handleCloseUserDialog = () => {
    setShowUserDialog(false);
    setUserForm({ name: "", email: "" });
    setAuthError("");
    setAuthLoading(false);
    setAuthStep("email");
    setTokenInput("");
    setMagicToken("");
  };

  const handleCreateLeague = async (e) => {
    e.preventDefault();
    if (!user) {
      toast.error("Please sign in first");
      return;
    }

    // Prompt D: Validate timer configuration
    if (leagueForm.antiSnipeSeconds >= leagueForm.timerSeconds) {
      toast.error("Anti-snipe seconds must be less than the bidding timer seconds");
      return;
    }

    if (leagueForm.timerSeconds < 15 || leagueForm.timerSeconds > 120) {
      toast.error("Bidding timer must be between 15 and 120 seconds");
      return;
    }

    if (leagueForm.antiSnipeSeconds < 0 || leagueForm.antiSnipeSeconds > 30) {
      toast.error("Anti-snipe must be between 0 and 30 seconds");
      return;
    }

    setCreatingLeague(true);
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
      
      toast.success(`Competition created! Invite token: ${response.data.inviteToken}`);
      setShowCreateLeagueDialog(false);
      loadLeagues();
      navigate(`/league/${response.data.id}`);
    } catch (e) {
      console.error("Error creating league:", e);
      const errorMessage = e.response?.data?.detail || e.message || "Unable to create competition. Check your internet connection and try again.";
      toast.error(errorMessage);
    } finally {
      setCreatingLeague(false);
    }
  };

  const handleJoinLeague = async (e) => {
    e.preventDefault();
    if (!user) {
      toast.error("Please sign in first");
      return;
    }

    setJoiningLeague(true);
    try {
      // Trim whitespace and normalize token (handle copy-paste issues)
      const normalizedToken = inviteToken.trim();
      
      if (!normalizedToken) {
        toast.error("Please enter an invite token");
        setJoiningLeague(false);
        return;
      }

      // Find league by invite token using dedicated endpoint (fixes issue with 100+ leagues)
      const tokenSearchResponse = await axios.get(`${API}/leagues/by-token/${normalizedToken}`);
      
      if (!tokenSearchResponse.data.found) {
        toast.error(`Invalid invite token "${normalizedToken}". Please check with your commissioner.`);
        setJoiningLeague(false);
        return;
      }

      const league = tokenSearchResponse.data.league;

      await axios.post(`${API}/leagues/${league.id}/join`, {
        userId: user.id,
        inviteToken: normalizedToken, // Send trimmed token to backend
      });

      toast.success(`Successfully joined "${league.name}"! Ready to start bidding.`);
      setShowJoinLeagueDialog(false);
      setInviteToken("");
      loadLeagues();
      navigate(`/league/${league.id}`);
    } catch (e) {
      console.error("Error joining league:", e);
      // Show the backend error message which includes helpful details
      const errorMsg = e.response?.data?.detail || "Unable to join league. Check your invite code (8 characters) or ask the commissioner to resend it.";
      toast.error(errorMsg);
    } finally {
      setJoiningLeague(false);
    }
  };

  const handleDeleteLeague = async (league, e) => {
    e.stopPropagation(); // Prevent navigation to league detail
    
    if (!user) {
      toast.error("Please sign in first");
      return;
    }

    if (league.commissionerId !== user.id) {
      toast.error("Only the commissioner can delete this league");
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to delete "${league.name}"? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await axios.delete(`${API}/leagues/${league.id}?user_id=${user.id}`);
      toast.success("League deleted successfully");
      loadLeagues();
    } catch (e) {
      console.error("Error deleting league:", e);
      toast.error(e.response?.data?.detail || "Error deleting league");
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
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 pointer-events-auto">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Enter Your Details</h2>
              <button
                onClick={handleCloseUserDialog}
                className="btn btn-secondary text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            {authError && (
              <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
                {authError}
              </div>
            )}
            <form onSubmit={handleAuth}>
              {authStep === "email" ? (
                <>
                  {/* Step 1: Email Input */}
                  <div className="mb-6">
                    <label className="block text-gray-700 mb-2 font-medium">Email Address</label>
                    <input
                      type="email"
                      inputMode="email"
                      placeholder="your.email@example.com"
                      className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 text-[16px]"
                      value={userForm.email}
                      onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                      data-testid="user-email-input"
                      disabled={authLoading}
                      required
                      maxLength="100"
                    />
                    <p className="text-sm text-gray-500 mt-2">
                      We&apos;ll send you a magic link to sign in securely
                    </p>
                  </div>
                  <button
                    type="submit"
                    className="btn btn-primary w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                    data-testid="request-magic-link-button"
                    disabled={authLoading}
                  >
                    {authLoading ? "Generating Magic Link..." : "Send Magic Link"}
                  </button>
                </>
              ) : (
                <>
                  {/* Step 2: Token Input */}
                  <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-800 font-medium mb-2">Magic link generated!</p>
                    <p className="text-xs text-green-700">
                      In pilot mode, your token is: <code className="bg-white px-2 py-1 rounded font-mono">{magicToken}</code>
                    </p>
                    <p className="text-xs text-green-600 mt-2">
                      (In production, this would be sent to your email)
                    </p>
                  </div>
                  <div className="mb-6">
                    <label className="block text-gray-700 mb-2 font-medium">Enter Magic Link Token</label>
                    <input
                      type="text"
                      placeholder="Paste your token here"
                      className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 font-mono text-sm"
                      value={tokenInput}
                      onChange={(e) => setTokenInput(e.target.value)}
                      data-testid="magic-token-input"
                      disabled={authLoading}
                      required
                    />
                    <p className="text-sm text-gray-500 mt-2">
                      Token expires in 15 minutes
                    </p>
                  </div>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setAuthStep("email");
                        setTokenInput("");
                        setMagicToken("");
                        setAuthError("");
                      }}
                      className="btn btn-outline flex-1 border border-gray-300 text-gray-700 py-3 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                      disabled={authLoading}
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primary flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                      data-testid="verify-magic-link-button"
                      disabled={authLoading}
                    >
                      {authLoading ? "Verifying..." : "Verify & Sign In"}
                    </button>
                  </div>
                </>
              )}
            </form>
          </div>
        </div>
      )}

      {/* Create League Dialog */}
      {showCreateLeagueDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 pointer-events-auto">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 max-h-[90dvh] overflow-y-auto app-card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Create Your Competition</h2>
              <button
                onClick={() => setShowCreateLeagueDialog(false)}
                className="btn btn-secondary text-gray-500 hover:text-gray-700 min-w-[44px] min-h-[44px]"
                aria-label="Close dialog"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateLeague}>
              <div className="mb-6">
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

              <div className="mb-6">
                <label className="block text-gray-700 mb-2 font-semibold">Sport</label>
                <select
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-[16px]"
                  value={leagueForm.sportKey}
                  onChange={(e) => setLeagueForm({ ...leagueForm, sportKey: e.target.value })}
                  data-testid="create-sport-select"
                >
                  <option value="football">⚽ Football</option>
                  {sports.find(s => s.key === 'cricket') && (
                    <option value="cricket">🏏 Cricket</option>
                  )}
                </select>
                <p className="text-sm text-gray-500 mt-2">
                  Choose the sport for your competition
                </p>
              </div>

              {/* Competition Selector (Football Only) */}
              {leagueForm.sportKey === "football" && (
                <div className="mb-6">
                  <label className="block text-gray-700 mb-2 font-semibold">Competition</label>
                  <select
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={leagueForm.competitionCode || "PL"}
                    onChange={(e) => setLeagueForm({ ...leagueForm, competitionCode: e.target.value })}
                    data-testid="create-competition-select"
                  >
                    <option value="PL">🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League</option>
                    <option value="CL">🏆 Champions League</option>
                    <option value="AFCON">🌍 AFCON</option>
                  </select>
                  <p className="text-sm text-gray-500 mt-2">
                    Select which competition to run
                  </p>
                </div>
              )}

              <div className="mb-6">
                <label className="block text-gray-700 mb-2 font-semibold">
                  Budget per Manager
                </label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      const currentMillions = leagueForm.budget / 1000000;
                      const newMillions = Math.max(10, currentMillions - 10);
                      setLeagueForm({ ...leagueForm, budget: newMillions * 1000000 });
                      setBudgetDisplay(newMillions.toString());
                    }}
                    className="px-4 py-3 bg-gray-200 hover:bg-gray-300 rounded-lg font-bold text-xl"
                  >
                    −
                  </button>
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-center font-semibold text-lg"
                      value={budgetDisplay}
                      onChange={(e) => {
                        const value = e.target.value.replace(/[^0-9]/g, '');
                        setBudgetDisplay(value);
                        if (value) {
                          setLeagueForm({ ...leagueForm, budget: Number(value) * 1000000 });
                        }
                      }}
                      required
                      data-testid="league-budget-input"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 font-semibold">m</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      const currentMillions = leagueForm.budget / 1000000;
                      const newMillions = currentMillions + 10;
                      setLeagueForm({ ...leagueForm, budget: newMillions * 1000000 });
                      setBudgetDisplay(newMillions.toString());
                    }}
                    className="px-4 py-3 bg-gray-200 hover:bg-gray-300 rounded-lg font-bold text-xl"
                  >
                    +
                  </button>
                </div>
                <p className="text-sm text-gray-500 mt-2">
                  Current: {formatCurrency(leagueForm.budget)} (adjust in £10m increments)
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-gray-700 mb-2 font-semibold">Min Managers</label>
                  <input
                    type="number"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-[16px]"
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
                    inputMode="numeric"
                    pattern="[0-9]*"
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-[16px]"
                    value={leagueForm.maxManagers}
                    onChange={(e) => setLeagueForm({ ...leagueForm, maxManagers: Number(e.target.value) })}
                    min="2"
                    max="8"
                    required
                    data-testid="league-max-managers-input"
                  />
                </div>
              </div>

              <div className="mb-6">
                <label className="block text-gray-700 mb-2 font-semibold">
                  {sports.find(s => s.key === leagueForm.sportKey)?.uiHints.assetPlural || "Assets"} per Manager (1-10)
                </label>
                <input
                  type="number"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-[16px]"
                  value={leagueForm.clubSlots}
                  onChange={(e) => setLeagueForm({ ...leagueForm, clubSlots: Number(e.target.value) })}
                  min="1"
                  max="10"
                  required
                  data-testid="league-club-slots-input"
                />
              </div>

              {/* Prompt D: Timer Configuration */}
              <div className="grid md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-gray-700 mb-2 font-semibold">Bidding Timer (seconds)</label>
                  <input
                    type="number"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-[16px]"
                    value={leagueForm.timerSeconds}
                    onChange={(e) => setLeagueForm({ ...leagueForm, timerSeconds: Number(e.target.value) })}
                    min="15"
                    max="120"
                    required
                    data-testid="league-timer-seconds-input"
                  />
                  <p className="text-sm text-gray-500 mt-2">15-120 seconds</p>
                </div>
                <div>
                  <label className="block text-gray-700 mb-2 font-semibold">Anti-Snipe (seconds)</label>
                  <input
                    type="number"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-[16px]"
                    value={leagueForm.antiSnipeSeconds}
                    onChange={(e) => setLeagueForm({ ...leagueForm, antiSnipeSeconds: Number(e.target.value) })}
                    min="0"
                    max="30"
                    required
                    data-testid="league-anti-snipe-input"
                  />
                  <p className="text-sm text-gray-500 mt-2">0-30 seconds, must be less than timer</p>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="create-league-submit"
                disabled={creatingLeague}
              >
                {creatingLeague ? "Creating Competition..." : "Create Competition"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Join League Dialog */}
      {showJoinLeagueDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 pointer-events-auto">
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
                className="btn btn-primary w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                data-testid="join-league-submit"
                disabled={joiningLeague}
              >
                {joiningLeague ? "Joining Competition..." : "Join the Competition"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-md app-header">
        <div className="container-narrow mx-auto px-4 py-4 flex justify-between items-center">
          <span data-testid="nav-brand" className="h2 text-lg md:text-2xl">Sport X</span>
          {user ? (
            <div className="flex items-center gap-2 md:gap-4">
              {/* Desktop view - show all items */}
              <div className="hidden md:flex items-center gap-4">
                {/* Prompt 6: Feature flag - hide My Competitions nav if flag off */}
                {process.env.REACT_APP_FEATURE_MY_COMPETITIONS === 'true' && (
                  <button
                    onClick={() => navigate("/app/my-competitions")}
                    className="btn btn-secondary text-sm text-blue-600 hover:underline font-semibold"
                    data-testid="nav-my-competitions"
                  >
                    My Competitions
                  </button>
                )}
                <button
                  onClick={() => navigate("/help")}
                  className="btn btn-secondary text-sm text-gray-600 hover:text-gray-800 hover:underline"
                  data-testid="nav-help"
                >
                  Help
                </button>
                <span className="text-gray-700 text-sm">
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
                    localStorage.removeItem("accessToken");
                    localStorage.removeItem("refreshToken");
                    setUser(null);
                    clearSentryUser(); // Clear Sentry user context
                    clearSocketUser(); // Clear Socket.IO user context
                    addBreadcrumb("User signed out", {}, "auth");
                    toast.success("Signed out successfully");
                  }}
                  className="btn btn-secondary text-sm text-red-600 hover:underline"
                  data-testid="logout-button"
                >
                  Logout
                </button>
              </div>
              
              {/* Mobile view - show condensed */}
              <div className="flex md:hidden items-center gap-2">
                <span className="text-gray-700 text-xs truncate max-w-[120px]">
                  <strong>{user.name}</strong>
                </span>
                {process.env.REACT_APP_FEATURE_MY_COMPETITIONS === 'true' && (
                  <button
                    onClick={() => navigate("/app/my-competitions")}
                    className="btn btn-secondary text-xs px-2 py-1 text-blue-600 hover:underline"
                    data-testid="nav-my-competitions"
                  >
                    My Comps
                  </button>
                )}
                <button
                  onClick={() => navigate("/help")}
                  className="btn btn-secondary text-xs px-2 py-1 text-gray-600 hover:underline"
                  data-testid="nav-help"
                >
                  Help
                </button>
                <button
                  onClick={() => {
                    localStorage.removeItem("user");
                    localStorage.removeItem("accessToken");
                    localStorage.removeItem("refreshToken");
                    setUser(null);
                    clearSentryUser(); // Clear Sentry user context
                    clearSocketUser(); // Clear Socket.IO user context
                    addBreadcrumb("User signed out", {}, "auth");
                    toast.success("Signed out successfully");
                  }}
                  className="btn btn-danger text-xs px-2 py-1 text-red-600 hover:underline"
                  data-testid="logout-button"
                >
                  Logout
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate("/help")}
                className="btn btn-secondary text-sm text-gray-600 hover:text-gray-800 hover:underline"
                data-testid="nav-help-logged-out"
              >
                Help
              </button>
              <button
                onClick={() => setShowUserDialog(true)}
                className="btn btn-primary bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm md:text-base"
                data-testid="login-button"
              >
                Sign In
              </button>
            </div>
          )}
        </div>
      </div>

      {/* CTA Banner - Show if user has leagues but no active auction - Prompt 6: Feature flag protected */}
      {user && showCompetitionsCTA && process.env.REACT_APP_FEATURE_MY_COMPETITIONS === 'true' && (
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 shadow-md">
          <div className="container-narrow mx-auto px-4 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <span className="text-2xl">🏆</span>
              <span className="font-semibold">Jump back in: Check your competitions!</span>
            </div>
            <button
              onClick={() => navigate("/app/my-competitions")}
              className="bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              View My Competitions
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="container-narrow mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="h1 text-3xl font-bold mb-6 text-gray-900">Welcome to Sport X</h2>
          <p className="h2 text-lg font-semibold text-blue-900 mb-2">Sports Gaming with Friends. No Gambling. All Strategy.</p>
          <p className="subtle text-gray-600 mb-8">
            Bid for exclusive ownership of players and teams who score your points. Experience the thrill of sports through strategic competition and community.
          </p>

          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <button
              onClick={handleCreateCompetition}
              className="btn btn-primary bg-blue-600 text-white px-6 py-4 rounded-lg hover:bg-blue-700 text-lg font-semibold"
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
              className="btn btn-secondary bg-gray-100 text-gray-900 px-6 py-4 rounded-lg hover:bg-gray-200 text-lg font-semibold border border-gray-300"
              data-testid="join-league-button"
            >
              Join the Competition
            </button>
            <button
              onClick={() => navigate("/clubs")}
              className="btn btn-outline bg-transparent text-blue-600 px-6 py-4 rounded-lg hover:bg-blue-600 hover:text-white text-lg font-semibold border-2 border-blue-600"
              data-testid="view-clubs-button"
            >
              Explore Available Teams
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
                        
                        {/* Delete button for commissioners */}
                        {isCommissioner && (
                          <div className="mt-3">
                            <button
                              onClick={(e) => handleDeleteLeague(league, e)}
                              className="w-full px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition text-sm font-medium"
                              data-testid={`delete-league-${league.id}`}
                            >
                              🗑️ Delete League
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  
                  {/* Add League Card */}
                  <div
                    className="flex-shrink-0 w-72 border-2 border-dashed border-gray-300 rounded-lg p-4 hover:border-blue-400 hover:bg-blue-50 transition-all duration-200 cursor-pointer flex flex-col items-center justify-center text-center"
                    onClick={handleCreateCompetition}
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
      <Toaster 
        position="top-right"
        containerStyle={{
          top: '16px',
          right: '16px',
          bottom: 'calc(64px + env(safe-area-inset-bottom))',
        }}
        toastOptions={{
          duration: 3000,
          style: {
            background: '#363636',
            color: '#fff',
            fontSize: 'var(--t-sm)',
            maxWidth: '90vw',
            wordBreak: 'break-word',
            overflowWrap: 'anywhere',
            minHeight: '44px',
            padding: '12px 16px',
          },
          success: {
            iconTheme: {
              primary: '#10B981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#EF4444',
              secondary: '#fff',
            },
          },
        }}
      />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/create-league" element={<CreateLeague />} />
          <Route path="/clubs" element={<ClubsList />} />
          <Route path="/league/:leagueId" element={<LeagueDetail />} />
          <Route path="/auction/:auctionId" element={<AuctionRoom />} />
          <Route path="/app/my-competitions" element={<MyCompetitions />} />
          <Route path="/app/competitions/:leagueId" element={<CompetitionDashboard />} />
          <Route path="/competitions/:leagueId" element={<CompetitionDashboard />} />
          <Route path="/help" element={<Help />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}