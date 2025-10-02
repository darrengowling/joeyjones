import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LeagueDetail() {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  const [league, setLeague] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [standings, setStandings] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingScores, setLoadingScores] = useState(false);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    loadLeague();
    loadParticipants();
    loadStandings();
  }, [leagueId]);

  const loadLeague = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}`);
      setLeague(response.data);
    } catch (e) {
      console.error("Error loading league:", e);
      alert("League not found");
      navigate("/");
    } finally {
      setLoading(false);
    }
  };

  const loadParticipants = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/participants`);
      setParticipants(response.data);
    } catch (e) {
      console.error("Error loading participants:", e);
    }
  };

  const loadStandings = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/standings`);
      setStandings(response.data);
    } catch (e) {
      console.error("Error loading standings:", e);
    }
  };

  const recomputeScores = async () => {
    setLoadingScores(true);
    try {
      await axios.post(`${API}/leagues/${leagueId}/score/recompute`);
      await loadStandings();
      alert("Scores recomputed successfully!");
    } catch (e) {
      console.error("Error recomputing scores:", e);
      alert(e.response?.data?.detail || "Error recomputing scores");
    } finally {
      setLoadingScores(false);
    }
  };

  const startAuction = async () => {
    if (!user) {
      alert("Please sign in first");
      return;
    }

    if (league.commissionerId !== user.id) {
      alert("Only the league commissioner can start the auction");
      return;
    }

    try {
      const response = await axios.post(`${API}/leagues/${leagueId}/auction/start`);
      alert("Auction started!");
      navigate(`/auction/${response.data.auctionId}`);
    } catch (e) {
      console.error("Error starting auction:", e);
      alert("Error starting auction");
    }
  };

  const goToAuction = async () => {
    try {
      const response = await axios.get(`${API}/leagues/${leagueId}/auction`);
      navigate(`/auction/${response.data.auctionId}`);
    } catch (e) {
      console.error("Error getting auction:", e);
      alert("No auction found for this league");
    }
  };

  const deleteLeague = async () => {
    if (!user) {
      alert("Please sign in first");
      return;
    }

    if (league.commissionerId !== user.id) {
      alert("Only the league commissioner can delete this league");
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to delete "${league.name}"? This will remove all participants, auction data, and bids. This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await axios.delete(`${API}/leagues/${leagueId}?user_id=${user.id}`);
      alert("League deleted successfully");
      navigate("/");
    } catch (e) {
      console.error("Error deleting league:", e);
      alert(e.response?.data?.detail || "Error deleting league");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading...</div>
      </div>
    );
  }

  if (!league) {
    return null;
  }

  const isCommissioner = user && league.commissionerId === user.id;
  const canStartAuction = participants.length >= league.minManagers;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
          <button
            onClick={() => navigate("/")}
            className="text-blue-600 hover:underline mb-4"
          >
            ← Back to Home
          </button>

          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{league.name}</h1>
              <div className="flex gap-2 items-center">
                <span
                  className={`px-3 py-1 rounded-full text-sm font-semibold ${
                    league.status === "active"
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {league.status}
                </span>
                <span className="text-sm text-gray-600">
                  {participants.length}/{league.maxManagers} managers
                </span>
              </div>
              <div className="mt-2 text-sm text-gray-600">
                Invite Token: <code className="bg-gray-100 px-2 py-1 rounded font-mono">{league.inviteToken}</code>
              </div>
            </div>

            <div className="flex gap-3">
              {league.status === "pending" && isCommissioner && (
                <div>
                  <button
                    onClick={startAuction}
                    disabled={!canStartAuction}
                    className={`px-6 py-3 rounded-lg font-semibold ${
                      canStartAuction
                        ? "bg-green-600 text-white hover:bg-green-700"
                        : "bg-gray-300 text-gray-500 cursor-not-allowed"
                    }`}
                    data-testid="start-auction-button"
                  >
                    Start Auction
                  </button>
                  {!canStartAuction && (
                    <p className="text-sm text-red-600 mt-2">
                      Need {league.minManagers - participants.length} more manager(s) to start
                    </p>
                  )}
                </div>
              )}
              
              {league.status === "active" && (
                <button
                  onClick={goToAuction}
                  className="px-6 py-3 rounded-lg font-semibold bg-blue-600 text-white hover:bg-blue-700"
                  data-testid="go-to-auction-button"
                >
                  Go to Auction
                </button>
              )}
              
              {isCommissioner && league.status === "pending" && (
                <button
                  onClick={deleteLeague}
                  className="px-6 py-3 rounded-lg font-semibold bg-red-600 text-white hover:bg-red-700"
                  data-testid="delete-league-button"
                >
                  Delete League
                </button>
              )}
            </div>
          </div>

          {/* Participants */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">League Participants</h3>
            {participants.length === 0 ? (
              <p className="text-gray-600">No participants yet. Share the invite token to get started!</p>
            ) : (
              <div className="space-y-2">
                {participants.map((p) => (
                  <div
                    key={p.id}
                    className="flex justify-between items-center bg-white p-3 rounded"
                  >
                    <div>
                      <span className="font-semibold text-gray-900">{p.userName}</span>
                      {p.userId === league.commissionerId && (
                        <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                          Commissioner
                        </span>
                      )}
                    </div>
                    <span className="text-sm text-gray-600">{p.userEmail}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* League Details */}
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            <div className="bg-gray-50 p-6 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">League Settings</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Budget per Manager:</span>
                  <span className="font-semibold">${league.budget}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Min Managers:</span>
                  <span className="font-semibold">{league.minManagers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Managers:</span>
                  <span className="font-semibold">{league.maxManagers}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Club Slots:</span>
                  <span className="font-semibold">{league.clubSlots}</span>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 p-6 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Auction Info</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Bid Timer:</span>
                  <span className="font-semibold">60 seconds</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Anti-Snipe:</span>
                  <span className="font-semibold">30 seconds</span>
                </div>
                <div className="text-sm text-gray-500 mt-4">
                  * Timer extends by 30 seconds if bid placed in last 30 seconds
                </div>
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">How It Works</h3>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                The commissioner starts the auction and selects clubs to bid on
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                Each club is auctioned for 60 seconds
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                If a bid is placed in the last 30 seconds, the timer extends by 30 seconds
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                The highest bidder wins the club when the timer expires
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                Each manager can bid up to their budget across multiple clubs
              </li>
            </ul>
          </div>

          {/* Standings */}
          {league.status === "active" && (
            <div className="bg-white border border-gray-200 rounded-lg p-6 mt-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">League Standings</h3>
                {isCommissioner && (
                  <button
                    onClick={recomputeScores}
                    disabled={loadingScores}
                    className={`px-4 py-2 rounded-lg font-semibold text-sm ${
                      loadingScores
                        ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                        : "bg-blue-600 text-white hover:bg-blue-700"
                    }`}
                    data-testid="recompute-scores-button"
                  >
                    {loadingScores ? "Computing..." : "🔄 Recompute Scores"}
                  </button>
                )}
              </div>

              {standings.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No scores yet. Clubs need to be won in the auction first, then scores can be computed based on Champions League results.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Rank
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Club
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          W
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          D
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          L
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          GF
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          GA
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          GD
                        </th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider font-bold">
                          Points
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {standings.map((club, index) => {
                        const goalDiff = club.goalsScored - club.goalsConceded;
                        return (
                          <tr key={club.id} className={index < 3 ? "bg-green-50" : ""}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {index + 1}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                              {club.clubName}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.wins}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.draws}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.losses}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.goalsScored}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-600">
                              {club.goalsConceded}
                            </td>
                            <td className={`px-6 py-4 whitespace-nowrap text-sm text-center font-semibold ${
                              goalDiff > 0 ? "text-green-600" : goalDiff < 0 ? "text-red-600" : "text-gray-600"
                            }`}>
                              {goalDiff > 0 ? "+" : ""}{goalDiff}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-center font-bold text-blue-600">
                              {club.totalPoints}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  <div className="mt-4 text-xs text-gray-500 space-y-1">
                    <p>📊 <strong>Scoring:</strong> Win = 3 pts | Draw = 1 pt | Goal Scored = 1 pt</p>
                    <p>🏆 <strong>Legend:</strong> W=Wins | D=Draws | L=Losses | GF=Goals For | GA=Goals Against | GD=Goal Difference</p>
                    <p className="text-green-600">Green rows = Top 3 positions</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {isCommissioner && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-900 font-semibold">
                🎯 You are the commissioner of this league
              </p>
              <p className="text-blue-700 text-sm mt-1">
                {league.status === "pending" 
                  ? "You can start the auction when ready"
                  : league.status === "active"
                  ? "Auction is currently running. Click 'Go to Auction' to participate."
                  : "You can recompute scores to update standings based on latest Champions League results"}
              </p>
            </div>
          )}
          
          {!isCommissioner && league.status === "active" && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-900 font-semibold">
                🎮 Auction is Live!
              </p>
              <p className="text-green-700 text-sm mt-1">
                Click "Go to Auction" to join the bidding and compete for clubs.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
