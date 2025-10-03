import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CreateLeague() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [form, setForm] = useState({
    name: "",
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
      <div className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-8 app-card">
          <button
            onClick={() => navigate("/")}
            className="btn btn-secondary text-blue-600 hover:underline mb-4"
          >
            ← Back to Home
          </button>

          <h1 className="text-3xl font-bold mb-6 text-gray-900">Create New League</h1>

          <form onSubmit={handleSubmit} className="space-y-6">
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
              <label className="block text-gray-700 mb-2 font-semibold">
                Budget per Manager (£)
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
                Club Slots per Manager
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
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-semibold text-lg"
              data-testid="create-league-submit"
            >
              Create League
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
