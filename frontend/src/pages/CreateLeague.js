import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { formatCurrency, parseCurrencyInput } from "../utils/currency";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const FEATURE_ASSET_SELECTION = process.env.REACT_APP_FEATURE_ASSET_SELECTION === 'true';

export default function CreateLeague() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [sports, setSports] = useState([]);
  const [availableAssets, setAvailableAssets] = useState([]);
  const [teamMode, setTeamMode] = useState("all"); // "all" or "select"
  const [selectedAssets, setSelectedAssets] = useState([]);
  const [assetSearchTerm, setAssetSearchTerm] = useState("");
  const [form, setForm] = useState({
    name: "",
    sportKey: "football", // Default to football
    budget: 500000000, // £500m default budget
    minManagers: 2,
    maxManagers: 12,
    clubSlots: 3,
  });
  const [budgetDisplay, setBudgetDisplay] = useState("500"); // Display in millions

  // Set page title
  useEffect(() => {
    document.title = "Create Competition | Sport X";
  }, []);

  useEffect(() => {
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    } else {
      alert("Please sign in first");
      navigate("/");
    }
  }, [navigate]);

  useEffect(() => {
    // Fetch available sports
    const fetchSports = async () => {
      try {
        const response = await axios.get(`${API}/sports`);
        setSports(response.data);
      } catch (error) {
        console.error("Error fetching sports:", error);
      }
    };
    
    fetchSports();
  }, []);

  useEffect(() => {
    // Fetch available assets when sport changes (if feature enabled)
    if (FEATURE_ASSET_SELECTION) {
      const fetchAssets = async () => {
        try {
          // Use unified /clubs endpoint for all sports
          const response = await axios.get(`${API}/clubs?sportKey=${form.sportKey}`);
          setAvailableAssets(response.data);
        } catch (error) {
          console.error("Error fetching assets:", error);
        }
      };
      
      fetchAssets();
    }
  }, [form.sportKey]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      alert("Please sign in first");
      return;
    }

    // Validation: If team mode is "select" and no teams selected
    if (FEATURE_ASSET_SELECTION && teamMode === "select" && selectedAssets.length === 0) {
      alert("Please select at least one team for the auction, or choose 'Include all teams'");
      return;
    }

    try {
      const leagueData = {
        ...form,
        commissionerId: user.id,
      };
      
      // Only include assetsSelected if feature enabled and teams are selected
      if (FEATURE_ASSET_SELECTION && teamMode === "select" && selectedAssets.length > 0) {
        leagueData.assetsSelected = selectedAssets;
      }
      
      const response = await axios.post(`${API}/leagues`, leagueData);
      alert("League created successfully!");
      navigate(`/league/${response.data.id}`);
    } catch (e) {
      console.error("Error creating league:", e);
      alert("Error creating league");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 py-8">
      <div className="container-narrow mx-auto px-4">
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8 app-card">
          <button
            onClick={() => navigate("/")}
            className="btn btn-secondary text-blue-600 hover:underline mb-4"
          >
            ← Back to Home
          </button>

          <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Create Competition</div>
          <h1 className="h1 text-3xl font-bold mb-6 text-gray-900">🏆 Create Your Competition</h1>
          <p className="subtle text-gray-600 mb-6">Build your peer-to-peer strategic arena where skill and tactics determine victory</p>

          <form onSubmit={handleSubmit} className="stack-lg space-y-6">
            <div>
              <label className="block text-gray-700 mb-2 font-semibold">League Name</label>
              <input
                type="text"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                data-testid="league-name-input"
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2 font-semibold">Sport</label>
              <select
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.sportKey}
                onChange={(e) => setForm({ ...form, sportKey: e.target.value })}
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

            <div>
              <label className="block text-gray-700 mb-2 font-semibold">
                Strategic Budget per Manager
              </label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const currentMillions = form.budget / 1000000;
                    const newMillions = Math.max(10, currentMillions - 10);
                    setForm({ ...form, budget: newMillions * 1000000 });
                    setBudgetDisplay(newMillions.toString());
                  }}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg font-bold text-xl"
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
                        setForm({ ...form, budget: Number(value) * 1000000 });
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
                    const currentMillions = form.budget / 1000000;
                    const newMillions = currentMillions + 10;
                    setForm({ ...form, budget: newMillions * 1000000 });
                    setBudgetDisplay(newMillions.toString());
                  }}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg font-bold text-xl"
                >
                  +
                </button>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Current: {formatCurrency(form.budget)} (adjust in £10m increments)
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-700 mb-2 font-semibold">Min Managers</label>
                <input
                  type="number"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={form.minManagers}
                  onChange={(e) => setForm({ ...form, minManagers: Number(e.target.value) })}
                  min="2"
                  required
                  data-testid="league-min-managers-input"
                />
              </div>

              <div>
                <label className="block text-gray-700 mb-2 font-semibold">Max Managers</label>
                <input
                  type="number"
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={form.maxManagers}
                  onChange={(e) => setForm({ ...form, maxManagers: Number(e.target.value) })}
                  min="2"
                  required
                  data-testid="league-max-managers-input"
                />
              </div>
            </div>

            <div>
              <label className="block text-gray-700 mb-2 font-semibold">
                {sports.find(s => s.key === form.sportKey)?.uiHints.assetPlural || "Assets"} per Manager
              </label>
              <input
                type="number"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.clubSlots}
                onChange={(e) => setForm({ ...form, clubSlots: Number(e.target.value) })}
                min="1"
                required
                data-testid="league-club-slots-input"
              />
            </div>

            {/* Team Selection (Feature Flag) */}
            {FEATURE_ASSET_SELECTION && (
              <div className="border-t pt-4">
                <label className="block text-gray-700 mb-3 font-semibold">Team Selection</label>
                
                {/* Radio Group */}
                <div className="space-y-2 mb-4">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="radio"
                      name="teamMode"
                      value="all"
                      checked={teamMode === "all"}
                      onChange={(e) => {
                        setTeamMode(e.target.value);
                        setSelectedAssets([]);
                      }}
                      className="w-4 h-4"
                      data-testid="rules-team-mode-include-all"
                    />
                    <span>Include all teams</span>
                  </label>
                  
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="radio"
                      name="teamMode"
                      value="select"
                      checked={teamMode === "select"}
                      onChange={(e) => setTeamMode(e.target.value)}
                      className="w-4 h-4"
                      data-testid="rules-team-mode-select"
                    />
                    <span>Select teams for auction</span>
                  </label>
                </div>

                {/* Team Checklist (only visible when "select" mode) */}
                {teamMode === "select" && (
                  <div className="border rounded-lg p-4 bg-gray-50">
                    {/* Competition Filter for Football */}
                    {form.sportKey === "football" && (
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Competition</label>
                        <select
                          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                          onChange={async (e) => {
                            const filter = e.target.value;
                            try {
                              let response;
                              if (filter === "all") {
                                response = await axios.get(`${API}/clubs?sportKey=football`);
                              } else {
                                response = await axios.get(`${API}/clubs?sportKey=football&competition=${filter}`);
                              }
                              setAvailableAssets(response.data);
                              // Auto-select all teams in filtered view
                              if (filter !== "all") {
                                setSelectedAssets(response.data.map(t => t.id));
                              }
                            } catch (error) {
                              console.error("Error filtering clubs:", error);
                            }
                          }}
                        >
                          <option value="all">All Teams ({availableAssets.length})</option>
                          <option value="EPL">Premier League Only (20)</option>
                          <option value="UCL">Champions League Only (36)</option>
                        </select>
                      </div>
                    )}

                    {/* Competition Filter for Cricket */}
                    {form.sportKey === "cricket" && (
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Series</label>
                        <select
                          className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                          onChange={async (e) => {
                            const filter = e.target.value;
                            try {
                              let response;
                              if (filter === "all") {
                                response = await axios.get(`${API}/clubs?sportKey=cricket`);
                              } else {
                                response = await axios.get(`${API}/clubs?sportKey=cricket&competition=${filter}`);
                              }
                              setAvailableAssets(response.data);
                              // Auto-select all players in filtered view
                              if (filter !== "all") {
                                setSelectedAssets(response.data.map(p => p.id));
                              }
                            } catch (error) {
                              console.error("Error filtering players:", error);
                            }
                          }}
                        >
                          <option value="all">All Players (53)</option>
                          <option value="ASHES">🏴󠁧󠁢󠁥󠁮󠁧󠁿🇦🇺 The Ashes 2025/26 (30)</option>
                          <option value="NZ_ENG">🇳🇿🏴 NZ vs England ODI (23)</option>
                        </select>
                      </div>
                    )}
                    
                    <div className="mb-3 flex gap-2">
                      <input
                        type="text"
                        placeholder="Search teams..."
                        className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={assetSearchTerm}
                        onChange={(e) => setAssetSearchTerm(e.target.value)}
                      />
                      <button
                        type="button"
                        onClick={() => {
                          const filtered = availableAssets.filter(asset => 
                            asset.name.toLowerCase().includes(assetSearchTerm.toLowerCase())
                          );
                          setSelectedAssets(filtered.map(a => a.id));
                        }}
                        className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold"
                      >
                        Select All
                      </button>
                      <button
                        type="button"
                        onClick={() => setSelectedAssets([])}
                        className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-semibold"
                      >
                        Clear
                      </button>
                    </div>
                    
                    <div className="max-h-64 overflow-y-auto space-y-2" data-testid="rules-team-checklist">
                      {availableAssets
                        .filter(asset => 
                          asset.name.toLowerCase().includes(assetSearchTerm.toLowerCase())
                        )
                        .map(asset => (
                          <label key={asset.id} className="flex items-center space-x-2 cursor-pointer hover:bg-gray-100 p-2 rounded">
                            <input
                              type="checkbox"
                              checked={selectedAssets.includes(asset.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedAssets([...selectedAssets, asset.id]);
                                } else {
                                  setSelectedAssets(selectedAssets.filter(id => id !== asset.id));
                                }
                              }}
                              className="w-4 h-4"
                            />
                            <div className="flex-1">
                              <span className="font-medium">{asset.name}</span>
                              {/* Display nationality for cricket players */}
                              {form.sportKey === "cricket" && asset.meta?.nationality && (
                                <span className="ml-2 text-xs text-gray-600 bg-gray-200 px-2 py-0.5 rounded">
                                  {asset.meta.nationality}
                                </span>
                              )}
                              {/* Display role for cricket players */}
                              {form.sportKey === "cricket" && asset.meta?.role && (
                                <span className="ml-1 text-xs text-gray-500">
                                  ({asset.meta.role})
                                </span>
                              )}
                            </div>
                          </label>
                        ))}
                    </div>
                    
                    <div className="mt-3 text-sm text-gray-600">
                      Selected: {selectedAssets.length} / {availableAssets.length} teams
                    </div>
                  </div>
                )}
              </div>
            )}

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
    </div>
  );
}
