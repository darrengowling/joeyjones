import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CreateLeague() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [sports, setSports] = useState([]);
  const [form, setForm] = useState({
    name: "",
    sportKey: "football", // Default to football
    budget: 500000000, // £500m default budget
    minManagers: 2,
    maxManagers: 12,
    clubSlots: 3,
  });

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) {
      alert("Please sign in first");
      return;
    }

    try {
      const response = await axios.post(`${API}/leagues`, {
        ...form,
        commissionerId: user.id,
      });
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
                Strategic Budget per Manager (£)
              </label>
              <input
                type="number"
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.budget}
                onChange={(e) => setForm({ ...form, budget: Number(e.target.value) })}
                min="100"
                required
                data-testid="league-budget-input"
              />
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
