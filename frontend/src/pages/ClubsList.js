import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ClubsList() {
  const navigate = useNavigate();
  const [clubs, setClubs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("all");

  useEffect(() => {
    loadClubs();
  }, []);

  const loadClubs = async () => {
    try {
      const response = await axios.get(`${API}/clubs`);
      if (response.data.length === 0) {
        // Seed clubs if empty
        await axios.post(`${API}/clubs/seed`);
        const newResponse = await axios.get(`${API}/clubs`);
        setClubs(newResponse.data);
      } else {
        setClubs(response.data);
      }
    } catch (e) {
      console.error("Error loading clubs:", e);
    } finally {
      setLoading(false);
    }
  };

  const countries = [...new Set(clubs.map((club) => club.country))].sort();

  const filteredClubs = clubs.filter((club) => {
    const matchesSearch = club.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCountry = selectedCountry === "all" || club.country === selectedCountry;
    return matchesSearch && matchesCountry;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-2xl">Loading clubs...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 py-8">
      <div className="container-narrow mx-auto px-4">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <button
            onClick={() => navigate("/")}
            className="btn btn-secondary text-blue-600 hover:underline mb-4"
          >
            ← Back to Home
          </button>

          <h1 className="h1 text-3xl font-bold mb-6 text-gray-900">
            🏆 UCL Teams 2025/26 - Available for Ownership
          </h1>
          <p className="subtle text-gray-600 mb-6">Explore the teams you can bid for exclusive ownership. Each team you own scores points for your strategic success.</p>

          {/* Filters */}
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-gray-700 mb-2 font-semibold">Search</label>
              <input
                type="text"
                placeholder="Search teams available for ownership..."
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                data-testid="club-search-input"
              />
            </div>

            <div>
              <label className="block text-gray-700 mb-2 font-semibold">Country</label>
              <select
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={selectedCountry}
                onChange={(e) => setSelectedCountry(e.target.value)}
                data-testid="club-country-filter"
              >
                <option value="all">All Countries</option>
                {countries.map((country) => (
                  <option key={country} value={country}>
                    {country}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Clubs Grid */}
          <div className="text-gray-600 mb-4">
            Showing {filteredClubs.length} of {clubs.length} clubs
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredClubs.map((club) => (
              <div
                key={club.id}
                className="border rounded-lg p-6 hover:shadow-lg transition-shadow bg-white"
                data-testid={`club-card-${club.id}`}
              >
                <h3 className="text-xl font-bold text-gray-900 mb-2">{club.name}</h3>
                <div className="flex items-center gap-2 text-gray-600">
                  <span className="text-2xl">{getCountryFlag(club.country)}</span>
                  <span>{club.country}</span>
                </div>
                <div className="mt-2 text-sm text-gray-500">
                  UEFA ID: {club.uefaId}
                </div>
              </div>
            ))}
          </div>

          {filteredClubs.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              No clubs found matching your criteria
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getCountryFlag(country) {
  const flags = {
    Spain: "🇪🇸",
    England: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    Germany: "🇩🇪",
    Italy: "🇮🇹",
    France: "🇫🇷",
    Portugal: "🇵🇹",
    Netherlands: "🇳🇱",
    Belgium: "🇧🇪",
    Scotland: "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    Austria: "🇦🇹",
    "Czech Republic": "🇨🇿",
    Croatia: "🇭🇷",
    Switzerland: "🇨🇭",
    Serbia: "🇷🇸",
    Ukraine: "🇺🇦",
    Denmark: "🇩🇰",
    Poland: "🇵🇱",
  };
  return flags[country] || "🏴";
}
