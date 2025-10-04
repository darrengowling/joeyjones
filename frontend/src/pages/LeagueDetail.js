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
  const [sport, setSport] = useState(null);
  const [uiHints, setUiHints] = useState({ assetLabel: "Club", assetPlural: "Clubs" }); // Default to football
  const [scoringOverrides, setScoringOverrides] = useState(null);
  const [editingScoring, setEditingScoring] = useState(false);
  const [savingScoring, setSavingScoring] = useState(false);

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
      
      // Load sport information based on league's sportKey
      if (response.data.sportKey) {
        try {
          const sportResponse = await axios.get(`${API}/sports/${response.data.sportKey}`);
          setSport(sportResponse.data);
          setUiHints(sportResponse.data.uiHints);
        } catch (e) {
          console.error("Error loading sport info:", e);
          // Keep default uiHints for clubs
        }
      }
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

  // Helper functions for cricket scoring configuration
  const getDefaultCricketScoring = () => ({
    type: "perPlayerMatch",
    rules: {
      run: 1,
      wicket: 25,
      catch: 10,
      stumping: 15,
      runOut: 10
    },
    milestones: {
      halfCentury: {
        enabled: true,
        threshold: 50,
        points: 10
      },
      century: {
        enabled: true,
        threshold: 100,
        points: 25
      },
      fiveWicketHaul: {
        enabled: true,
        threshold: 5,
        points: 25
      }
    }
  });

  const getCurrentScoringDisplay = () => {
    const currentScoring = league.scoringOverrides || (sport ? sport.scoringSchema : getDefaultCricketScoring());
    const rules = currentScoring.rules || {};
    const milestones = currentScoring.milestones || {};
    
    return [
      { label: "Run", value: `${rules.run || 0} pts` },
      { label: "Wicket", value: `${rules.wicket || 0} pts` },
      { label: "Catch", value: `${rules.catch || 0} pts` },
      { label: "Stumping", value: `${rules.stumping || 0} pts` },
      { label: "Run Out", value: `${rules.runOut || 0} pts` },
      { label: "Half Century", value: milestones.halfCentury?.enabled ? `+${milestones.halfCentury.points} pts` : "Disabled" },
      { label: "Century", value: milestones.century?.enabled ? `+${milestones.century.points} pts` : "Disabled" },
      { label: "Five Wicket Haul", value: milestones.fiveWicketHaul?.enabled ? `+${milestones.fiveWicketHaul.points} pts` : "Disabled" }
    ];
  };

  const updateScoringRule = (rule, value) => {
    setScoringOverrides(prev => ({
      ...prev,
      rules: {
        ...prev?.rules,
        [rule]: value
      }
    }));
  };

  const updateMilestone = (milestone, field, value) => {
    setScoringOverrides(prev => ({
      ...prev,
      milestones: {
        ...prev?.milestones,
        [milestone]: {
          ...prev?.milestones?.[milestone],
          threshold: milestone === "halfCentury" ? 50 : milestone === "century" ? 100 : 5,
          [field]: value
        }
      }
    }));
  };

  const handleSaveScoring = async () => {
    if (!isCommissioner) {
      alert("Only commissioners can modify scoring rules");
      return;
    }

    setSavingScoring(true);
    try {
      const response = await axios.put(`${API}/leagues/${leagueId}/scoring-overrides`, {
        scoringOverrides: scoringOverrides
      });

      if (response.data) {
        setLeague(prev => ({ ...prev, scoringOverrides: scoringOverrides }));
        setEditingScoring(false);
        alert("Scoring rules updated successfully!");
      }
    } catch (error) {
      console.error("Error saving scoring overrides:", error);
      alert("Failed to save scoring rules. Please try again.");
    } finally {
      setSavingScoring(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 py-8">
      <div className="container-narrow mx-auto px-4">
        <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
          <button
            onClick={() => navigate("/")}
            className="btn btn-secondary text-blue-600 hover:underline mb-4"
          >
            ← Back to Home
          </button>

          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="h1 text-3xl font-bold text-gray-900 mb-2">{league.name}</h1>
              <div className="stack-md">
                <div className="row-gap-md flex items-center">
                  <span
                    className={`chip px-3 py-1 rounded-full text-sm font-semibold ${
                      league.status === "active"
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {league.status}
                  </span>
                  <span className="subtle text-sm text-gray-600">
                    {participants.length}/{league.maxManagers} managers
                  </span>
                </div>
                <div className="subtle text-sm text-gray-600">
                  Invite Token: <code className="chip bg-gray-100 px-2 py-1 rounded font-mono">{league.inviteToken}</code>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              {league.status === "pending" && isCommissioner && (
                <div>
                  <button
                    onClick={startAuction}
                    disabled={!canStartAuction}
                    className={`btn btn-primary px-6 py-3 rounded-lg font-semibold ${
                      canStartAuction
                        ? "bg-green-600 text-white hover:bg-green-700"
                        : "bg-gray-300 text-gray-500 cursor-not-allowed"
                    }`}
                    data-testid="start-auction-button"
                  >
                    Begin Strategic Competition
                  </button>
                  {!canStartAuction && (
                    <p className="text-sm text-red-600 mt-2">
                      Need {league.minManagers - participants.length} more strategic competitors to begin
                    </p>
                  )}
                </div>
              )}
              
              {league.status === "active" && (
                <button
                  onClick={goToAuction}
                  className="btn btn-primary px-6 py-3 rounded-lg font-semibold bg-blue-600 text-white hover:bg-blue-700"
                  data-testid="go-to-auction-button"
                >
                  Enter Auction Room
                </button>
              )}
              
              {isCommissioner && (league.status === "pending" || league.status === "completed") && (
                <button
                  onClick={deleteLeague}
                  className="btn btn-danger px-6 py-3 rounded-lg font-semibold bg-red-600 text-white hover:bg-red-700"
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
                  <span className="chip font-semibold">£{league.budget.toLocaleString()}</span>
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
                  <span className="text-gray-600">{uiHints.assetLabel} Slots:</span>
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

          {/* Cricket Scoring Configuration */}
          {league && league.sportKey === "cricket" && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Advanced: Scoring (Cricket)</h3>
                {!editingScoring ? (
                  <button
                    onClick={() => {
                      setEditingScoring(true);
                      // Initialize form with current overrides or sport defaults
                      const currentOverrides = league.scoringOverrides || (sport ? sport.scoringSchema : null);
                      setScoringOverrides(currentOverrides ? JSON.parse(JSON.stringify(currentOverrides)) : getDefaultCricketScoring());
                    }}
                    className="btn-secondary px-4 py-2 text-sm"
                    data-testid="edit-scoring-button"
                  >
                    Edit Scoring Rules
                  </button>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={handleSaveScoring}
                      disabled={savingScoring}
                      className="btn-primary px-4 py-2 text-sm"
                      data-testid="save-scoring-button"
                    >
                      {savingScoring ? "Saving..." : "Save Changes"}
                    </button>
                    <button
                      onClick={() => {
                        setEditingScoring(false);
                        setScoringOverrides(null);
                      }}
                      className="btn-secondary px-4 py-2 text-sm"
                      data-testid="cancel-scoring-button"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>

              {!editingScoring ? (
                <div>
                  <p className="text-gray-600 text-sm mb-4">
                    {league.scoringOverrides ? 
                      "Using custom scoring rules for this league." : 
                      "Using default cricket scoring rules."}
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    {getCurrentScoringDisplay().map((item, index) => (
                      <div key={index} className="flex justify-between">
                        <span className="text-gray-600">{item.label}:</span>
                        <span className="font-semibold">{item.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Base Points</h4>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Run</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.run || 0}
                          onChange={(e) => updateScoringRule("run", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-run-input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Wicket</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.wicket || 0}
                          onChange={(e) => updateScoringRule("wicket", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-wicket-input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Catch</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.catch || 0}
                          onChange={(e) => updateScoringRule("catch", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-catch-input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Stumping</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.stumping || 0}
                          onChange={(e) => updateScoringRule("stumping", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-stumping-input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm text-gray-600 mb-1">Run Out</label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={scoringOverrides?.rules?.runOut || 0}
                          onChange={(e) => updateScoringRule("runOut", parseFloat(e.target.value) || 0)}
                          className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                          data-testid="scoring-runout-input"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-3">Milestone Bonuses</h4>
                    <div className="space-y-4">
                      {["halfCentury", "century", "fiveWicketHaul"].map((milestone) => {
                        const milestoneData = scoringOverrides?.milestones?.[milestone];
                        const label = milestone === "halfCentury" ? "Half Century (50+ runs)" : 
                                    milestone === "century" ? "Century (100+ runs)" : 
                                    "Five Wicket Haul (5+ wickets)";
                        
                        return (
                          <div key={milestone} className="flex items-center space-x-4">
                            <label className="flex items-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={milestoneData?.enabled || false}
                                onChange={(e) => updateMilestone(milestone, "enabled", e.target.checked)}
                                className="mr-2"
                                data-testid={`milestone-${milestone}-enabled`}
                              />
                              <span className="text-sm text-gray-700">{label}</span>
                            </label>
                            {milestoneData?.enabled && (
                              <div className="flex items-center space-x-2">
                                <span className="text-sm text-gray-600">Points:</span>
                                <input
                                  type="number"
                                  min="0"
                                  step="1"
                                  value={milestoneData?.points || 0}
                                  onChange={(e) => updateMilestone(milestone, "points", parseInt(e.target.value) || 0)}
                                  className="w-20 px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  data-testid={`milestone-${milestone}-points`}
                                />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Note:</strong> Changes will apply to future score ingests. Leave fields blank to use default cricket scoring rules.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Instructions */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">How It Works</h3>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                The commissioner starts the auction and selects {uiHints.assetPlural.toLowerCase()} to bid on
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                Each {uiHints.assetLabel.toLowerCase()} is auctioned for 60 seconds
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                If a bid is placed in the last 30 seconds, the timer extends by 30 seconds
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                The highest bidder wins the {uiHints.assetLabel.toLowerCase()} when the timer expires
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">•</span>
                Each manager can bid up to their budget across multiple {uiHints.assetPlural.toLowerCase()}
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
                    className={`btn btn-secondary px-4 py-2 rounded-lg font-semibold text-sm ${
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
                  No scores yet. {uiHints.assetPlural} need to be won in the auction first, then scores can be computed based on competition results.
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
                          {uiHints.assetLabel}
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
                Click "Go to Auction" to join the bidding and compete for {uiHints.assetPlural.toLowerCase()}.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
