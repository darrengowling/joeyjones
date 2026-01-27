import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { formatCurrency } from "../utils/currency";
import BottomNav from "../components/BottomNav";

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
    sportKey: "football",
    competitionCode: "",
    budget: 500000000,
    minManagers: 2,
    maxManagers: 12,
    clubSlots: 3,
  });
  const [budgetDisplay, setBudgetDisplay] = useState("500");

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
    if (FEATURE_ASSET_SELECTION) {
      const fetchAssets = async () => {
        try {
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

    if (FEATURE_ASSET_SELECTION && teamMode === "select" && selectedAssets.length === 0) {
      alert("Please select at least one team for the auction, or choose 'Include all teams'");
      return;
    }

    try {
      const leagueData = {
        ...form,
        commissionerId: user.id,
      };
      
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
    <div className="min-h-screen" style={{ background: '#0B101B', paddingBottom: '100px' }}>
      {/* Header */}
      <header 
        className="fixed top-0 left-0 right-0 z-40 px-4 py-4 flex items-center justify-between"
        style={{
          background: 'rgba(11, 16, 27, 0.95)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-white/60 hover:text-white transition-colors"
        >
          <span>←</span>
          <span className="text-xl font-black tracking-tighter">
            SPORT <span style={{ color: '#06B6D4' }}>X</span>
          </span>
        </button>
      </header>

      {/* Main Content */}
      <div className="pt-20 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="text-xs uppercase tracking-widest text-white/40 mb-1">Create Competition</div>
          <h1 className="text-2xl font-bold text-white mb-2">🏆 Create Your Competition</h1>
          <p className="text-white/60 text-sm mb-6">Build your peer-to-peer strategic arena where skill and tactics determine victory</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* League Name */}
            <div 
              className="rounded-xl p-4"
              style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
            >
              <label className="block text-white/60 mb-2 text-sm font-semibold">League Name</label>
              <input
                type="text"
                className="w-full px-4 py-3 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Enter league name..."
                required
                data-testid="league-name-input"
              />
            </div>

            {/* Sport Selection */}
            <div 
              className="rounded-xl p-4"
              style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
            >
              <label className="block text-white/60 mb-2 text-sm font-semibold">Sport</label>
              <select
                className="w-full px-4 py-3 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                value={form.sportKey}
                onChange={(e) => setForm({ ...form, sportKey: e.target.value })}
                data-testid="create-sport-select"
              >
                <option value="football">⚽ Football</option>
                {sports.find(s => s.key === 'cricket') && (
                  <option value="cricket">🏏 Cricket</option>
                )}
              </select>
              <p className="text-xs text-white/40 mt-2">Choose the sport for your competition</p>
            </div>

            {/* Budget */}
            <div 
              className="rounded-xl p-4"
              style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
            >
              <label className="block text-white/60 mb-2 text-sm font-semibold">Strategic Budget per Manager</label>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const currentMillions = form.budget / 1000000;
                    const newMillions = Math.max(10, currentMillions - 10);
                    setForm({ ...form, budget: newMillions * 1000000 });
                    setBudgetDisplay(newMillions.toString());
                  }}
                  className="w-12 h-12 rounded-xl font-bold text-xl text-white transition-colors"
                  style={{ background: 'rgba(255, 255, 255, 0.1)' }}
                >
                  −
                </button>
                <div className="flex-1 relative">
                  <input
                    type="text"
                    className="w-full px-4 py-3 rounded-xl text-white text-center font-semibold text-lg focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                    style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
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
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-white/60 font-semibold">m</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    const currentMillions = form.budget / 1000000;
                    const newMillions = currentMillions + 10;
                    setForm({ ...form, budget: newMillions * 1000000 });
                    setBudgetDisplay(newMillions.toString());
                  }}
                  className="w-12 h-12 rounded-xl font-bold text-xl text-white transition-colors"
                  style={{ background: 'rgba(255, 255, 255, 0.1)' }}
                >
                  +
                </button>
              </div>
              <p className="text-xs text-white/40 mt-2">Current: {formatCurrency(form.budget)} (adjust in £10m increments)</p>
            </div>

            {/* Manager Settings */}
            <div 
              className="rounded-xl p-4"
              style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
            >
              <label className="block text-white/60 mb-3 text-sm font-semibold">Manager Settings</label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-white/40 mb-1 text-xs">Min Managers</label>
                  <input
                    type="number"
                    className="w-full px-4 py-3 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                    style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                    value={form.minManagers}
                    onChange={(e) => setForm({ ...form, minManagers: Number(e.target.value) })}
                    min="2"
                    required
                    data-testid="league-min-managers-input"
                  />
                </div>
                <div>
                  <label className="block text-white/40 mb-1 text-xs">Max Managers</label>
                  <input
                    type="number"
                    className="w-full px-4 py-3 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                    style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                    value={form.maxManagers}
                    onChange={(e) => setForm({ ...form, maxManagers: Number(e.target.value) })}
                    min="2"
                    required
                    data-testid="league-max-managers-input"
                  />
                </div>
              </div>
            </div>

            {/* Assets per Manager */}
            <div 
              className="rounded-xl p-4"
              style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
            >
              <label className="block text-white/60 mb-2 text-sm font-semibold">
                {sports.find(s => s.key === form.sportKey)?.uiHints.assetPlural || "Assets"} per Manager
              </label>
              <input
                type="number"
                className="w-full px-4 py-3 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                value={form.clubSlots}
                onChange={(e) => setForm({ ...form, clubSlots: Number(e.target.value) })}
                min="1"
                required
                data-testid="league-club-slots-input"
              />
            </div>

            {/* Team Selection (Feature Flag) */}
            {FEATURE_ASSET_SELECTION && (
              <div 
                className="rounded-xl p-4"
                style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
              >
                <label className="block text-white/60 mb-3 text-sm font-semibold">Team Selection</label>
                
                {/* Radio Group */}
                <div className="space-y-2 mb-4">
                  <label className="flex items-center space-x-3 cursor-pointer p-2 rounded-lg hover:bg-white/5">
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
                      style={{ accentColor: '#00F0FF' }}
                      data-testid="rules-team-mode-include-all"
                    />
                    <span className="text-white">Include all teams</span>
                  </label>
                  
                  <label className="flex items-center space-x-3 cursor-pointer p-2 rounded-lg hover:bg-white/5">
                    <input
                      type="radio"
                      name="teamMode"
                      value="select"
                      checked={teamMode === "select"}
                      onChange={(e) => setTeamMode(e.target.value)}
                      className="w-4 h-4"
                      style={{ accentColor: '#00F0FF' }}
                      data-testid="rules-team-mode-select"
                    />
                    <span className="text-white">Select teams for auction</span>
                  </label>
                </div>

                {/* Team Checklist (only visible when "select" mode) */}
                {teamMode === "select" && (
                  <div 
                    className="rounded-xl p-4"
                    style={{ background: 'rgba(0, 0, 0, 0.3)', border: '1px solid rgba(255, 255, 255, 0.05)' }}
                  >
                    {/* Competition Filter for Football */}
                    {form.sportKey === "football" && (
                      <div className="mb-4">
                        <label className="block text-white/40 mb-2 text-xs font-semibold">Filter by Competition</label>
                        <select
                          className="w-full px-4 py-3 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                          style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                          onChange={async (e) => {
                            const filter = e.target.value;
                            try {
                              let response;
                              if (filter === "all") {
                                response = await axios.get(`${API}/clubs?sportKey=football`);
                                setForm({ ...form, competitionCode: "" });
                              } else {
                                response = await axios.get(`${API}/clubs?sportKey=football&competition=${filter}`);
                                setForm({ ...form, competitionCode: filter });
                              }
                              setAvailableAssets(response.data);
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
                          <option value="AFCON">AFCON Only (24)</option>
                        </select>
                      </div>
                    )}

                    {/* Competition Filter for Cricket */}
                    {form.sportKey === "cricket" && (
                      <div className="mb-4">
                        <label className="block text-white/40 mb-2 text-xs font-semibold">Competition Type</label>
                        <select
                          className="w-full px-4 py-3 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                          style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                          onChange={async (e) => {
                            const filter = e.target.value;
                            try {
                              if (filter === "IPL") {
                                const response = await axios.get(`${API}/assets?sportKey=cricket&pageSize=300`);
                                const allPlayers = response.data.assets || [];
                                
                                const franchises = {};
                                allPlayers.forEach(p => {
                                  const franchise = p.meta?.franchise;
                                  if (franchise) {
                                    if (!franchises[franchise]) franchises[franchise] = [];
                                    if (franchises[franchise].length < 11) {
                                      franchises[franchise].push(p);
                                    }
                                  }
                                });
                                
                                const iplPlayers = Object.values(franchises).flat();
                                setAvailableAssets(iplPlayers);
                                setSelectedAssets(iplPlayers.map(p => p.id));
                                setForm({ ...form, competitionCode: "IPL" });
                              } else if (filter === "CUSTOM") {
                                const response = await axios.get(`${API}/assets?sportKey=cricket&pageSize=300`);
                                setAvailableAssets(response.data.assets || []);
                                setSelectedAssets([]);
                                setForm({ ...form, competitionCode: "CUSTOM" });
                              }
                            } catch (error) {
                              console.error("Error filtering players:", error);
                            }
                          }}
                          data-testid="cricket-competition-select"
                        >
                          <option value="">-- Select Competition Type --</option>
                          <option value="IPL">🏏 IPL (Full Squads - 110 players)</option>
                          <option value="CUSTOM">🎯 Custom Selection</option>
                        </select>
                        <p className="text-xs text-white/40 mt-2">
                          IPL: Auto-selects 11 players from each franchise. Custom: Build your own.
                        </p>
                      </div>
                    )}
                    
                    {/* Search and Actions */}
                    <div className="mb-3 flex gap-2">
                      <input
                        type="text"
                        placeholder="Search teams..."
                        className="flex-1 px-4 py-2 rounded-xl text-white placeholder-white/40 text-sm focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                        style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
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
                        className="px-3 py-2 rounded-xl text-sm font-semibold"
                        style={{ background: '#00F0FF', color: '#0B101B' }}
                      >
                        Select All
                      </button>
                      <button
                        type="button"
                        onClick={() => setSelectedAssets([])}
                        className="px-3 py-2 rounded-xl text-sm font-semibold"
                        style={{ background: 'rgba(255, 255, 255, 0.1)', color: 'white' }}
                      >
                        Clear
                      </button>
                    </div>
                    
                    {/* Team List */}
                    <div className="max-h-64 overflow-y-auto space-y-1" data-testid="rules-team-checklist">
                      {availableAssets
                        .filter(asset => 
                          asset.name.toLowerCase().includes(assetSearchTerm.toLowerCase())
                        )
                        .map(asset => (
                          <label 
                            key={asset.id} 
                            className="flex items-center space-x-3 cursor-pointer p-2 rounded-lg hover:bg-white/5"
                          >
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
                              style={{ accentColor: '#00F0FF' }}
                            />
                            <div className="flex-1">
                              <span className="font-medium text-white">{asset.name}</span>
                              {form.sportKey === "cricket" && asset.meta?.nationality && (
                                <span 
                                  className="ml-2 text-xs px-2 py-0.5 rounded"
                                  style={{ background: 'rgba(0, 240, 255, 0.2)', color: '#00F0FF' }}
                                >
                                  {asset.meta.nationality}
                                </span>
                              )}
                              {form.sportKey === "cricket" && asset.meta?.role && (
                                <span className="ml-1 text-xs text-white/40">
                                  ({asset.meta.role})
                                </span>
                              )}
                            </div>
                          </label>
                        ))}
                    </div>
                    
                    <div className="mt-3 text-sm text-white/60">
                      Selected: <span style={{ color: '#00F0FF' }}>{selectedAssets.length}</span> / {availableAssets.length} teams
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full py-4 rounded-xl font-bold text-lg transition-all hover:scale-[1.02]"
              style={{ background: 'linear-gradient(135deg, #06B6D4, #0891B2)', color: 'white' }}
              data-testid="create-league-submit"
            >
              Create Competition
            </button>
          </form>
        </div>
      </div>

      {/* Bottom Navigation */}
      <BottomNav onFabClick={() => navigate('/create-competition')} />
    </div>
  );
}
