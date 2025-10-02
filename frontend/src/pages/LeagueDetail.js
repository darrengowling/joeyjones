import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LeagueDetail() {
  const { leagueId } = useParams();
  const navigate = useNavigate();
  const [league, setLeague] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    loadLeague();
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

            {isCommissioner && league.status === "pending" && (
              <button
                onClick={startAuction}
                className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 font-semibold"
                data-testid="start-auction-button"
              >
                Start Auction
              </button>
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

          {isCommissioner && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-900 font-semibold">
                🎯 You are the commissioner of this league
              </p>
              <p className="text-blue-700 text-sm mt-1">
                You can start the auction when ready
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
