import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import BottomNav from "../components/BottomNav";
import TeamCrest from "../components/TeamCrest";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ClubsList() {
  const navigate = useNavigate();
  const [assets, setAssets] = useState({ football: [], cricket: [] });
  const [totalCounts, setTotalCounts] = useState({ football: 0, cricket: 0 });
  const [sports, setSports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSport, setSelectedSport] = useState("football");
  const [selectedFranchise, setSelectedFranchise] = useState("all");
  const [selectedRole, setSelectedRole] = useState("all");

  // Set page title
  useEffect(() => {
    document.title = "Browse Teams | Sport X";
  }, []);

  useEffect(() => {
    loadSportsAndAssets();
  }, []);

  const loadSportsAndAssets = async () => {
    try {
      // Load available sports
      const sportsResponse = await axios.get(`${API}/sports`);
      setSports(sportsResponse.data);
      
      // Load assets for each sport
      const assetPromises = sportsResponse.data.map(async (sport) => {
        try {
          if (sport.key === 'football') {
            // Load clubs for football
            let response = await axios.get(`${API}/clubs`);
            if (response.data.length === 0) {
              // Seed clubs if empty
              await axios.post(`${API}/clubs/seed`);
              response = await axios.get(`${API}/clubs`);
            }
            return { sport: sport.key, assets: response.data, total: response.data.length };
          } else {
            // Load assets for other sports
            const response = await axios.get(`${API}/assets?sportKey=${sport.key}&pageSize=250`);
            const total = response.data.pagination?.total || response.data.assets?.length || 0;
            return { sport: sport.key, assets: response.data.assets || [], total };
          }
        } catch (e) {
          console.error(`Error loading ${sport.key} assets:`, e);
          return { sport: sport.key, assets: [], total: 0 };
        }
      });
      
      const assetsData = await Promise.all(assetPromises);
      const assetsBySport = {};
      const totalsBySport = {};
      assetsData.forEach(({ sport, assets, total }) => {
        assetsBySport[sport] = assets;
        totalsBySport[sport] = total;
      });
      
      setAssets(assetsBySport);
      setTotalCounts(totalsBySport);
    } catch (e) {
      console.error("Error loading sports and assets:", e);
      toast.error("Error loading sports data");
    } finally {
      setLoading(false);
    }
  };

  const currentSport = sports.find(s => s.key === selectedSport);
  const currentAssets = assets[selectedSport] || [];
  
  // Get unique franchises and roles for cricket filters
  const franchises = selectedSport === 'cricket' 
    ? [...new Set(currentAssets.map(a => a.meta?.franchise).filter(Boolean))].sort()
    : [];
  const roles = selectedSport === 'cricket'
    ? [...new Set(currentAssets.map(a => a.meta?.role).filter(Boolean))].sort()
    : [];
  
  // Dynamic filtering based on sport
  const filteredAssets = currentAssets.filter((asset) => {
    const matchesSearch = asset.name.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (selectedSport === 'football') {
      // For football, we can still filter by country if needed
      return matchesSearch;
    } else if (selectedSport === 'cricket') {
      // Filter by franchise dropdown
      const matchesFranchise = selectedFranchise === 'all' || asset.meta?.franchise === selectedFranchise;
      // Filter by role dropdown
      const matchesRole = selectedRole === 'all' || asset.meta?.role === selectedRole;
      // Filter by search (name)
      return matchesSearch && matchesFranchise && matchesRole;
    }
    
    return matchesSearch;
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0B101B' }}>
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#00F0FF] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white/60">Loading sports assets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: '#0B101B', paddingBottom: '100px' }}>
      {/* Header */}
      <header 
        className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-md z-40 px-4 py-4 flex items-center justify-between"
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
      <div className="pt-20 px-4" data-testid="clubs-list-page">
        <div className="max-w-4xl mx-auto">
          <div className="text-xs uppercase tracking-widest text-white/40 mb-1">Research Hub</div>
          <h1 className="text-2xl font-bold text-white mb-2">
            {currentSport ? `${currentSport.name} ${currentSport.uiHints.assetPlural}` : 'Sports Assets'}
          </h1>
          <p className="text-white/60 text-sm mb-6">
            Explore the {currentSport?.uiHints.assetPlural.toLowerCase() || 'assets'} you can bid for exclusive ownership.
          </p>

          {/* Sport Selection & Search */}
          <div 
            className="rounded-xl p-4 mb-6"
            style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
          >
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-white/60 mb-2 text-sm font-semibold">Sport</label>
                <select
                  className="w-full px-4 py-3 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-[#06B6D4] appearance-none cursor-pointer"
                  style={{ 
                    background: '#0B101B', 
                    border: '1px solid #06B6D4',
                    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2306B6D4'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'right 12px center',
                    backgroundSize: '20px'
                  }}
                  value={selectedSport}
                  onChange={(e) => {
                    setSelectedSport(e.target.value);
                    setSelectedFranchise("all");
                    setSelectedRole("all");
                    setSearchTerm("");
                  }}
                  data-testid="sport-filter-select"
                >
                  {sports.map((sport) => (
                    <option key={sport.key} value={sport.key} style={{ background: '#0B101B', color: '#fff' }}>
                      {sport.name} ({sport.uiHints.assetPlural})
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-white/60 mb-2 text-sm font-semibold">Search</label>
                <input
                  type="text"
                  placeholder={`Search ${currentSport?.uiHints.assetPlural.toLowerCase() || 'assets'}...`}
                  className="w-full px-4 py-3 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                  style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  data-testid="asset-search-input"
                />
              </div>
            </div>

            {/* Cricket Filters */}
            {selectedSport === 'cricket' && (
              <div className="grid md:grid-cols-2 gap-4 mt-4 pt-4" style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <div>
                  <label className="block text-white/60 mb-2 text-sm font-semibold">IPL Team</label>
                  <select
                    className="w-full px-4 py-3 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                    style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                    value={selectedFranchise}
                    onChange={(e) => setSelectedFranchise(e.target.value)}
                    data-testid="franchise-filter-select"
                  >
                    <option value="all">All Teams ({franchises.length})</option>
                    {franchises.map((franchise) => (
                      <option key={franchise} value={franchise}>
                        {franchise} ({currentAssets.filter(a => a.meta?.franchise === franchise).length})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-white/60 mb-2 text-sm font-semibold">Role</label>
                  <select
                    className="w-full px-4 py-3 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-[#00F0FF]"
                    style={{ background: '#0B101B', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                    value={selectedRole}
                    onChange={(e) => setSelectedRole(e.target.value)}
                    data-testid="role-filter-select"
                  >
                    <option value="all">All Roles</option>
                    {roles.map((role) => (
                      <option key={role} value={role}>
                        {role} ({currentAssets.filter(a => a.meta?.role === role).length})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Results Count */}
          <div className="text-white/40 text-sm mb-4">
            {totalCounts[selectedSport] > currentAssets.length ? (
              <>Showing first {filteredAssets.length} of {totalCounts[selectedSport]} {currentSport?.uiHints.assetPlural.toLowerCase() || 'assets'}</>
            ) : (
              <>Showing {filteredAssets.length} of {currentAssets.length} {currentSport?.uiHints.assetPlural.toLowerCase() || 'assets'}</>
            )}
          </div>

          {/* Assets Grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredAssets.map((asset) => (
              <div
                key={asset.id}
                className="rounded-xl p-4 transition-all hover:scale-[1.02]"
                style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
                data-testid={`asset-card-${asset.id}`}
              >
                <div className="flex items-start gap-3">
                  <TeamCrest 
                    clubId={asset.id}
                    apiFootballId={asset.apiFootballId}
                    name={asset.name}
                    sportKey={selectedSport}
                    variant="thumbnail"
                  />
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-white mb-1 truncate">{asset.name}</h3>
                    
                    {selectedSport === 'football' && (
                      <div>
                        {asset.country && (
                          <div className="flex items-center gap-2 text-white/60 mb-1">
                            {getCountryFlag(asset.country) && (
                              <span className="text-base">{getCountryFlag(asset.country)}</span>
                            )}
                            <span className="text-sm">{asset.country}</span>
                          </div>
                        )}
                        {asset.uefaId && (
                          <div className="text-xs text-white/40">
                            UEFA ID: {asset.uefaId}
                          </div>
                        )}
                      </div>
                    )}
                    
                    {selectedSport === 'cricket' && asset.meta && (
                      <div>
                        <div className="flex flex-wrap gap-2 mb-2">
                          {asset.meta.nationality && (
                            <span 
                              className="text-xs px-2 py-1 rounded-full"
                              style={{ background: 'rgba(0, 240, 255, 0.2)', color: '#00F0FF' }}
                            >
                              {asset.meta.nationality}
                            </span>
                          )}
                          {asset.meta.role && (
                            <span 
                              className="text-xs px-2 py-1 rounded-full"
                              style={{ background: 'rgba(255, 255, 255, 0.1)', color: 'rgba(255, 255, 255, 0.6)' }}
                            >
                              {asset.meta.role}
                            </span>
                          )}
                        </div>
                        {asset.meta.franchise && (
                          <p className="text-sm" style={{ color: '#A78BFA' }}>{asset.meta.franchise}</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {filteredAssets.length === 0 && currentAssets.length > 0 && (
            <div 
              className="rounded-xl p-12 text-center"
              style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
            >
              <div className="text-6xl mb-4">
                {selectedSport === 'football' ? '⚽' : '🏏'}
              </div>
              <p className="text-white font-semibold mb-2">
                No {currentSport?.uiHints.assetPlural.toLowerCase() || 'assets'} found
              </p>
              <p className="text-sm text-white/40">
                Try adjusting your search criteria
              </p>
            </div>
          )}
          
          {currentAssets.length === 0 && !loading && (
            <div 
              className="rounded-xl p-12 text-center"
              style={{ background: '#151C2C', border: '1px solid rgba(255, 255, 255, 0.1)' }}
            >
              <div className="text-6xl mb-4">
                {selectedSport === 'football' ? '⚽' : '🏏'}
              </div>
              <p className="text-white font-semibold mb-2">
                No {currentSport?.uiHints.assetPlural || 'Assets'} available
              </p>
              <p className="text-sm text-white/40">
                Try selecting a different sport above
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Navigation */}
      <BottomNav onFabClick={() => navigate('/create-competition')} />
    </div>
  );
}

function getCountryFlag(country) {
  const flags = {
    // Football countries
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
    // Cricket countries
    Australia: "🇦🇺",
    India: "🇮🇳",
    Pakistan: "🇵🇰",
    "South Africa": "🇿🇦",
    "New Zealand": "🇳🇿",
    "Sri Lanka": "🇱🇰",
    Bangladesh: "🇧🇩",
    "West Indies": "🏴‍☠️",
    Afghanistan: "🇦🇫",
    Ireland: "🇮🇪",
  };
  return flags[country] || null;
}
