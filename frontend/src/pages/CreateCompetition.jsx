import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import BottomNav from "../components/BottomNav";
import { formatCurrency } from "../utils/currency";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * CreateCompetition - Stitch-styled create competition page
 */
export default function CreateCompetition() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [sports, setSports] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [form, setForm] = useState({
    name: "",
    sportKey: "football",
    competitionCode: "PL",
    budget: 500000000,
    minManagers: 2,
    maxManagers: 8,
    clubSlots: 3,
  });
  
  const [budgetDisplay, setBudgetDisplay] = useState("500");

  useEffect(() => {
    document.title = "Create Competition | Sport X";
    
    const savedUser = localStorage.getItem("user");
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    } else {
      toast.error("Please sign in first");
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      toast.error("Please sign in first");
      return;
    }

    if (!form.name.trim()) {
      toast.error("Please enter a competition name");
      return;
    }

    setLoading(true);
    try {
      const leagueData = {
        ...form,
        commissionerId: user.id,
      };
      
      const response = await axios.post(`${API}/leagues`, leagueData);
      const newLeague = response.data;
      
      // Auto-join the commissioner as first participant
      try {
        await axios.post(`${API}/leagues/${newLeague.id}/join`, {
          inviteToken: newLeague.inviteToken,
          userId: user.id,
          userName: user.name,
          userEmail: user.email,
        });
      } catch (joinError) {
        // If already joined or other error, continue anyway
        console.log("Commissioner auto-join:", joinError.response?.data?.message || "Already joined");
      }
      
      toast.success("Competition created!");
      navigate(`/league/${newLeague.id}`);
    } catch (e) {
      console.error("Error creating league:", e);
      toast.error("Error creating competition");
    } finally {
      setLoading(false);
    }
  };

  const adjustBudget = (delta) => {
    const currentMillions = form.budget / 1000000;
    const newMillions = Math.max(10, Math.min(1000, currentMillions + delta));
    setForm({ ...form, budget: newMillions * 1000000 });
    setBudgetDisplay(newMillions.toString());
  };

  const adjustSlots = (delta) => {
    const newValue = Math.max(1, Math.min(20, form.clubSlots + delta));
    setForm({ ...form, clubSlots: newValue });
  };

  // Get sport-specific labels
  const currentSport = sports.find(s => s.key === form.sportKey);
  const assetLabel = currentSport?.uiHints?.assetPlural || "Teams";

  return (
    <div 
      className="min-h-screen font-sans"
      style={{ background: '#070B13' }}
    >
      {/* Gradient overlay */}
      <div 
        className="fixed inset-0 pointer-events-none"
        style={{ 
          background: 'radial-gradient(circle at 50% -20%, rgba(6, 182, 212, 0.08), transparent 50%)',
        }}
      />

      {/* Header */}
      <header 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-md z-40 px-6 pt-6 pb-4 flex items-center justify-between"
        style={{ background: '#070B13' }}
      >
        <button 
          onClick={() => navigate('/')}
          className="w-10 h-10 flex items-center justify-center rounded-full active:scale-95 transition-transform"
          style={{ 
            background: '#0F1624',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          <span className="material-symbols-outlined text-white text-2xl">chevron_left</span>
        </button>
        <h1 className="text-lg font-extrabold tracking-tight text-white uppercase">
          Create Competition
        </h1>
        <div className="w-10"></div>
      </header>

      {/* Main Content */}
      <main className="pt-24 px-6 pb-48">
        {/* Progress Indicator */}
        <div className="flex items-center justify-center space-x-2 mb-10">
          <div className="h-1.5 w-12 rounded-full" style={{ background: '#06B6D4' }}></div>
          <div className="h-1.5 w-12 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}></div>
          <div className="h-1.5 w-12 rounded-full" style={{ background: 'rgba(255,255,255,0.1)' }}></div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Competition Name & Sport Card */}
          <div 
            className="p-6 space-y-6 rounded-2xl"
            style={{ 
              background: '#0F1624',
              border: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            {/* Competition Name */}
            <div className="space-y-2">
              <label 
                className="block text-[11px] font-extrabold uppercase tracking-widest"
                style={{ color: '#06B6D4' }}
              >
                Competition Name
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="ENTER NAME"
                className="w-full rounded-xl px-4 py-4 text-base font-bold text-white placeholder:text-slate-700 focus:outline-none transition-all"
                style={{ 
                  background: '#000000',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
                data-testid="competition-name-input"
              />
            </div>

            {/* Sport Selection */}
            <div className="space-y-2">
              <label 
                className="block text-[11px] font-extrabold uppercase tracking-widest"
                style={{ color: '#06B6D4' }}
              >
                Select Sport
              </label>
              <div className="relative">
                <select
                  value={form.sportKey}
                  onChange={(e) => setForm({ ...form, sportKey: e.target.value })}
                  className="w-full rounded-xl px-4 py-4 appearance-none text-base font-bold text-white focus:outline-none transition-all"
                  style={{ 
                    background: '#000000',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                  }}
                  data-testid="competition-sport-select"
                >
                  <option value="football">PREMIER LEAGUE FOOTBALL</option>
                  {sports.find(s => s.key === 'cricket') && (
                    <option value="cricket">IPL CRICKET</option>
                  )}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                  <span className="material-symbols-outlined" style={{ color: '#06B6D4' }}>expand_more</span>
                </div>
              </div>
            </div>
          </div>

          {/* Managers Grid - Min and Max */}
          <div className="grid grid-cols-2 gap-4">
            {/* Min Managers */}
            <div 
              className="p-5 space-y-3 rounded-2xl"
              style={{ 
                background: '#0F1624',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <label 
                className="block text-[11px] font-extrabold uppercase tracking-widest"
                style={{ color: '#06B6D4' }}
              >
                Min Managers
              </label>
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => setForm({ ...form, minManagers: Math.max(2, form.minManagers - 1) })}
                  className="w-8 h-8 rounded-lg flex items-center justify-center active:bg-white/10 transition-colors"
                  style={{ 
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.05)',
                  }}
                >
                  <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>remove</span>
                </button>
                <span className="text-xl font-black text-white">{form.minManagers}</span>
                <button
                  type="button"
                  onClick={() => setForm({ ...form, minManagers: Math.min(form.maxManagers, form.minManagers + 1) })}
                  className="w-8 h-8 rounded-lg flex items-center justify-center active:bg-white/10 transition-colors"
                  style={{ 
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.05)',
                  }}
                >
                  <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>add</span>
                </button>
              </div>
            </div>

            {/* Max Managers */}
            <div 
              className="p-5 space-y-3 rounded-2xl"
              style={{ 
                background: '#0F1624',
                border: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <label 
                className="block text-[11px] font-extrabold uppercase tracking-widest"
                style={{ color: '#06B6D4' }}
              >
                Max Managers
              </label>
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => {
                    const newMax = Math.max(2, form.maxManagers - 1);
                    setForm({ 
                      ...form, 
                      maxManagers: newMax,
                      minManagers: Math.min(form.minManagers, newMax)
                    });
                  }}
                  className="w-8 h-8 rounded-lg flex items-center justify-center active:bg-white/10 transition-colors"
                  style={{ 
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.05)',
                  }}
                >
                  <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>remove</span>
                </button>
                <span className="text-xl font-black text-white">{form.maxManagers}</span>
                <button
                  type="button"
                  onClick={() => setForm({ ...form, maxManagers: Math.min(20, form.maxManagers + 1) })}
                  className="w-8 h-8 rounded-lg flex items-center justify-center active:bg-white/10 transition-colors"
                  style={{ 
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.05)',
                  }}
                >
                  <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>add</span>
                </button>
              </div>
            </div>
          </div>

          {/* Budget */}
          <div 
            className="p-5 space-y-3 rounded-2xl"
            style={{ 
              background: '#0F1624',
              border: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <label 
              className="block text-[11px] font-extrabold uppercase tracking-widest"
              style={{ color: '#06B6D4' }}
            >
              Budget
            </label>
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={() => adjustBudget(-10)}
                className="w-10 h-10 rounded-lg flex items-center justify-center active:bg-white/10 transition-colors"
                style={{ 
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.05)',
                }}
              >
                <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>remove</span>
              </button>
              <div className="flex items-center">
                <span className="font-black text-xl mr-1" style={{ color: '#06B6D4' }}>£</span>
                <span className="text-2xl font-black text-white">{budgetDisplay}M</span>
              </div>
              <button
                type="button"
                onClick={() => adjustBudget(10)}
                className="w-10 h-10 rounded-lg flex items-center justify-center active:bg-white/10 transition-colors"
                style={{ 
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.05)',
                }}
              >
                <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>add</span>
              </button>
            </div>
            <p className="text-[10px] text-slate-500 text-center">Adjust in £10m increments</p>
          </div>

          {/* Teams per Manager */}
          <div 
            className="p-5 rounded-2xl"
            style={{ 
              background: '#0F1624',
              border: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <div className="flex items-center justify-between">
              <div>
                <label 
                  className="block text-[11px] font-extrabold uppercase tracking-widest mb-1"
                  style={{ color: '#06B6D4' }}
                >
                  {assetLabel} per Manager
                </label>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tight">
                  Roster size for each player
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => adjustSlots(-1)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center active:bg-white/10 transition-colors"
                  style={{ 
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.05)',
                  }}
                >
                  <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>remove</span>
                </button>
                <span className="text-xl font-black text-white w-8 text-center">{form.clubSlots}</span>
                <button
                  type="button"
                  onClick={() => adjustSlots(1)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center active:bg-white/10 transition-colors"
                  style={{ 
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.05)',
                  }}
                >
                  <span className="material-symbols-outlined text-xl" style={{ color: '#06B6D4' }}>add</span>
                </button>
              </div>
            </div>
          </div>

          {/* Private League Toggle */}
          <div 
            className="p-4 flex items-center justify-between rounded-2xl"
            style={{ 
              background: '#0F1624',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderLeft: '4px solid #06B6D4',
            }}
          >
            <div className="flex items-center space-x-3">
              <span className="material-symbols-outlined text-slate-400">lock</span>
              <div>
                <p className="text-sm font-bold text-white">Private Competition</p>
                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tight">Invite code required</p>
              </div>
            </div>
            <div className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" checked readOnly className="sr-only peer" />
              <div 
                className="w-11 h-6 rounded-full peer peer-checked:after:translate-x-5 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"
                style={{ background: '#06B6D4' }}
              ></div>
            </div>
          </div>

          {/* Security Badge */}
          <div className="flex items-center justify-center space-x-2 text-slate-600 text-[10px] font-bold uppercase tracking-[0.2em] pt-4">
            <span className="material-symbols-outlined text-sm">security</span>
            <span>Premium Social Gaming</span>
          </div>
        </form>
      </main>

      {/* Fixed CTA Button */}
      <div className="fixed bottom-28 left-1/2 -translate-x-1/2 w-full max-w-md px-6 z-40">
        <button
          onClick={handleSubmit}
          disabled={loading || !form.name.trim()}
          className="w-full h-16 rounded-2xl flex items-center justify-center space-x-2 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ 
            background: '#06B6D4',
            color: '#000000',
            fontWeight: 800,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            boxShadow: '0 4px 14px 0 rgba(6, 182, 212, 0.3)',
          }}
          data-testid="create-competition-submit"
        >
          <span className="text-base">{loading ? 'CREATING...' : 'CREATE COMPETITION'}</span>
          {!loading && <span className="material-symbols-outlined">arrow_forward</span>}
        </button>
      </div>

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  );
}
