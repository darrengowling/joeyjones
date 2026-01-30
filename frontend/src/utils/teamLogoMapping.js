// Team name to logo file mapping
// Logos stored in /public/assets/clubs/football/

export const footballLogoMapping = {
  // Premier League
  "Chelsea FC": "chelsea_fc.png",
  "Nottingham Forest FC": "nottingham_forest.png",
  "Wolverhampton Wanderers FC": "wolverhampton_wanderers.png",
  "Arsenal FC": "arsenal_fc.png",
  "Liverpool FC": "liverpool_fc.png",
  "Manchester City FC": "manchester_city.png",
  "Manchester United FC": "manchester_united.png",
  "Tottenham Hotspur FC": "tottenham_hotspur.png",
  "Newcastle United FC": "newcastle_united.png",
  "Brentford FC": "brentford_fc.png",
  "Brighton & Hove Albion FC": "brighton_&_hove_albion.png",
  "Crystal Palace FC": "crystal_palace.png",
  "Everton FC": "everton_fc.png",
  "West Ham United FC": "west_ham_united.png",
  "Aston Villa FC": "aston_villa.png",
  "Fulham FC": "fulham_fc.png",
  "Burnley FC": "burnley_fc.png",
  "Leeds United FC": "leeds_united.png",
  "Sunderland AFC": "sunderland_afc.png",
  "AFC Bournemouth": "afc_bournemouth.png",
  
  // Champions League / European
  "AFC Ajax": "ajax_amsterdam.png",
  "Atalanta BC": "atalanta_bc.png",
  "Athletic Club": "athletic_bilbao.png",
  "Borussia Dortmund": "borussia_dortmund.png",
  "FC Barcelona": "fc_barcelona.png",
  "FC Bayern München": "bayern_munich.png",
  "Sport Lisboa e Benfica": "sl_benfica.png",
  "Eintracht Frankfurt": "eintracht_frankfurt.png",
  "FC Internazionale Milano": "inter_milan.png",
  "Juventus FC": "juventus_fc.png",
  "Bayer 04 Leverkusen": "bayer_04_leverkusen.png",
  "Olympique de Marseille": "olympique_marseille.png",
  "AS Monaco FC": "as_monaco.png",
  "SSC Napoli": "ssc_napoli.png",
  "Paris Saint-Germain FC": "paris_saint-germain.png",
  "PSV": "psv_eindhoven.png",
  "Real Madrid CF": "real_madrid.png",
  "Sporting Clube de Portugal": "sporting_cp.png",
  "Villarreal CF": "villarreal_cf.png",
  "AC Milan": "ac_milan.png",
  "SS Lazio": "ss_lazio.png",
  "AS Roma": "as_roma.png",
  "Sevilla FC": "sevilla_fc.png",
  "Real Sociedad": "real_sociedad.png",
  "FC Porto": "fc_porto.png",
  "RB Leipzig": "rb_leipzig.png",
  "VfB Stuttgart": "vfb_stuttgart.png",
  "Feyenoord Rotterdam": "feyenoord_rotterdam.png",
  "LOSC Lille": "losc_lille.png",
  "Olympique Lyon": "olympique_lyon.png",
  "OGC Nice": "ogc_nice.png",
  "SC Braga": "sc_braga.png",
  
  // Champions League 2025/26 - Added Jan 30
  "Club Atlético de Madrid": "atletico_madrid.png",
  "Atlético Madrid": "atletico_madrid.png",
  "FK Bodø/Glimt": "bodo_glimt.png",
  "Bodø/Glimt": "bodo_glimt.png",
  "Club Brugge KV": "club_brugge.png",
  "Club Brugge": "club_brugge.png",
};

// IPL Cricket team logos
export const cricketLogoMapping = {
  "Chennai Super Kings": "chennai_super_kings.png",
  "Mumbai Indians": "mumbai_indians.png",
  "Royal Challengers Bengaluru": "royal_challengers_bangalore.png",
  "Royal Challengers Bangalore": "royal_challengers_bangalore.png",
  "Kolkata Knight Riders": "kolkata_knight_riders.png",
  "Delhi Capitals": "delhi_capitals.png",
  "Rajasthan Royals": "rajasthan_royals.png",
  "Sunrisers Hyderabad": "sunrisers_hyderabad.png",
  "Punjab Kings": "punjab_kings.png",
  "Lucknow Super Giants": "lucknow_super_giants.png",
  "Gujarat Titans": "gujarat_titans.png",
};

// Helper function to get logo path
export const getTeamLogoPath = (teamName, sport = 'football') => {
  const mapping = sport === 'cricket' ? cricketLogoMapping : footballLogoMapping;
  const logoFile = mapping[teamName];
  
  if (logoFile) {
    return `/assets/clubs/${sport}/${logoFile}`;
  }
  return null;
};
