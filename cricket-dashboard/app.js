const DATASETS = [
  { role: "Batting", apiRole: "batsmen", format: "ODI" },
  { role: "Batting", apiRole: "batsmen", format: "T20" },
  { role: "Batting", apiRole: "batsmen", format: "Test" },
  { role: "Bowling", apiRole: "bowler", format: "ODI" },
  { role: "Bowling", apiRole: "bowler", format: "T20" },
  { role: "Bowling", apiRole: "bowler", format: "Test" },
  { role: "Fielding", apiRole: "fielder", format: "ODI" },
  { role: "Fielding", apiRole: "fielder", format: "T20" },
  { role: "Fielding", apiRole: "fielder", format: "Test" }
];

const ROLE_CONFIG = {
  Batting: {
    primary: "runs",
    metrics: ["runs", "average", "strike_rate", "hundreds", "fifties", "sixes"],
    kpis: ["runs", "average", "strike_rate", "hundreds"],
    profile: ["matches_played", "innings_played", "highest_score", "fifties", "ducks"]
  },
  Bowling: {
    primary: "wickets",
    metrics: ["wickets", "average", "economy", "strike_rate", "five_wicket_hauls", "ten_wicket_hauls"],
    kpis: ["wickets", "average", "economy", "five_wicket_hauls"],
    profile: ["matches_played", "innings_played", "best_innings", "best_match", "runs_conceded"]
  },
  Fielding: {
    primary: "dismissals",
    metrics: ["dismissals", "catches", "stumpings", "catch_wickets", "matches_played"],
    kpis: ["dismissals", "catches", "stumpings", "catch_wickets"],
    profile: ["matches_played", "innings_played", "years_active"]
  }
};

const LABELS = {
  runs: "Runs",
  average: "Average",
  strike_rate: "Strike rate",
  hundreds: "100s",
  fifties: "50s",
  sixes: "Sixes",
  wickets: "Wickets",
  economy: "Economy",
  five_wicket_hauls: "5 wicket hauls",
  ten_wicket_hauls: "10 wicket hauls",
  dismissals: "Dismissals",
  catches: "Catches",
  stumpings: "Stumpings",
  catch_wickets: "Keeper catches",
  matches_played: "Matches",
  innings_played: "Innings",
  highest_score: "Highest score",
  ducks: "Ducks",
  best_innings: "Best innings",
  best_match: "Best match",
  runs_conceded: "Runs conceded",
  years_active: "Years active"
};

const RANKINGS_LABELS = {
  batsmen: "batting",
  bowler: "bowling",
  fielder: "fielding"
};

const RANKINGS_COLUMNS = {
  batsmen: [
    ["full_name", "Player"], ["country", "Country"], ["formats_played", "Formats"],
    ["total_matches", "Matches"], ["total_runs", "Runs"], ["total_centuries", "100s"],
    ["total_fifties", "50s"], ["total_average", "Average"]
  ],
  bowler: [
    ["full_name", "Player"], ["country", "Country"], ["formats_played", "Formats"],
    ["total_matches", "Matches"], ["total_wickets", "Wickets"],
    ["average_bowling_average", "Average"], ["average_bowling_economy", "Economy"]
  ],
  fielder: [
    ["full_name", "Player"], ["country", "Country"], ["formats_played", "Formats"],
    ["total_catches", "Catches"], ["total_wicket_keeper_catches", "Keeper catches"],
    ["total_stumpings", "Stumpings"]
  ]
};

const COUNTRY_COLUMNS = {
  batsmen: [
    ["country", "Country"], ["number_of_players", "Players"], ["total_runs", "Runs"],
    ["average_batting_average", "Avg"], ["average_strike_rate", "Strike rate"],
    ["total_hundreds", "100s"], ["total_fifties", "50s"], ["total_ducks", "Ducks"]
  ],
  bowler: [
    ["country", "Country"], ["number_of_players", "Players"], ["total_wickets", "Wickets"],
    ["runs_conceded", "Runs conceded"], ["average_bowling_average", "Avg"],
    ["average_economy", "Economy"], ["total_five_wicket_hauls", "5W hauls"]
  ],
  fielder: [
    ["country", "Country"], ["number_of_players", "Players"], ["total_dismissals", "Dismissals"],
    ["total_catches", "Catches"], ["total_stumpings", "Stumpings"]
  ]
};

const state = {
  rows: [],
  role: "Batting",
  format: "Test",
  activeTab: "overview",
  selectedPlayer: "",
  comparePlayer: "",
  suggestionNames: [],
  analytics: {
    subtab: "rankings",
    rankingsRole: "batsmen",
    rankingsData: [],
    rankingsError: "",
    countryRole: "batsmen",
    countryFormat: "Test",
    countryFilter: "",
    countryList: [],
    countryData: [],
    countryError: ""
  }
};

const el = {
  playerCount: document.querySelector("#playerCount"),
  playerSearch: document.querySelector("#playerSearch"),
  suggestions: document.querySelector("#suggestions"),
  appTabs: document.querySelector("#appTabs"),
  overviewView: document.querySelector("#overviewView"),
  compareView: document.querySelector("#compareView"),
  openCompare: document.querySelector("#openCompare"),
  selectedPlayerName: document.querySelector("#selectedPlayerName"),
  selectedPlayerMeta: document.querySelector("#selectedPlayerMeta"),
  comparePlayerSearch: document.querySelector("#comparePlayerSearch"),
  compareSuggestions: document.querySelector("#compareSuggestions"),
  compareMeta: document.querySelector("#compareMeta"),
  primaryCompareCard: document.querySelector("#primaryCompareCard"),
  secondaryCompareCard: document.querySelector("#secondaryCompareCard"),
  kpiGrid: document.querySelector("#kpiGrid"),
  barTitle: document.querySelector("#barTitle"),
  barChart: document.querySelector("#barChart"),
  compareTitle: document.querySelector("#compareTitle"),
  compareChart: document.querySelector("#compareChart"),
  compareFormatTitle: document.querySelector("#compareFormatTitle"),
  compareFormatChart: document.querySelector("#compareFormatChart"),
  leaderTitle: document.querySelector("#leaderTitle"),
  metricSelect: document.querySelector("#metricSelect"),
  leaderHead: document.querySelector("#leaderHead"),
  leaderBody: document.querySelector("#leaderBody"),
  profileCard: document.querySelector("#profileCard"),
  // Advanced Analytics
  analyticsView: document.querySelector("#analyticsView"),
  analyticsSubTabs: document.querySelector("#analyticsSubTabs"),
  rankingsSubview: document.querySelector("#rankingsSubview"),
  countrySubview: document.querySelector("#countrySubview"),
  rankingsRoleTabs: document.querySelector("#rankingsRoleTabs"),
  rankingsTitle: document.querySelector("#rankingsTitle"),
  rankingsHead: document.querySelector("#rankingsHead"),
  rankingsBody: document.querySelector("#rankingsBody"),
  countryRoleTabs: document.querySelector("#countryRoleTabs"),
  countryFormatTabs: document.querySelector("#countryFormatTabs"),
  countryFilter: document.querySelector("#countryFilter"),
  countryStatsTitle: document.querySelector("#countryStatsTitle"),
  countryStatsContainer: document.querySelector("#countryStatsContainer")
};

init();

async function init() {
  state.rows = (await Promise.all(DATASETS.map(loadDataset))).flat();
  state.selectedPlayer = pickDefaultPlayer();
  state.comparePlayer = pickComparePlayer();

  bindEvents();
  render();

  await loadCountryList();
  await loadRankings();
  await loadCountryStats();
}

async function loadDataset(dataset) {
  const response = await fetch(`/api/players?role=${dataset.apiRole}&format=${dataset.format}`);
  if (!response.ok) {
    throw new Error(`Unable to load ${dataset.apiRole}/${dataset.format}`);
  }
  const rows = await response.json();
  return rows.map((row) => ({ ...row, role: dataset.role, format: dataset.format }));
}

function bindEvents() {
  el.appTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    state.activeTab = button.dataset.tab;
    setActive("#appTabs", button);
    render();
  });

  el.openCompare.addEventListener("click", () => {
    state.activeTab = "compare";
    document.querySelectorAll("#appTabs button").forEach((button) => {
      button.classList.toggle("active", button.dataset.tab === "compare");
    });
    render();
  });

  document.querySelector("#formatTabs").addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    state.format = button.dataset.format;
    setActive("#formatTabs", button);
    render();
    // Reload rankings when format changes
    if (state.activeTab === "analytics" && state.analytics.subtab === "rankings") {
      loadRankings();
    }
  });

  document.querySelector("#roleTabs").addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    state.role = button.dataset.role;
    setActive("#roleTabs", button);
    state.selectedPlayer = pickDefaultPlayer();
    state.comparePlayer = pickComparePlayer();
    // Sync analytics role with main role
    const roleMap = { "Batting": "batsmen", "Bowling": "bowler", "Fielding": "fielder" };
    state.analytics.rankingsRole = roleMap[button.dataset.role];
    state.analytics.countryRole = roleMap[button.dataset.role];
    // Update the country role tabs to reflect the change
    document.querySelectorAll("#countryRoleTabs button").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.role === state.analytics.countryRole);
    });
    render();
    // Reload rankings when role changes
    if (state.activeTab === "analytics" && state.analytics.subtab === "rankings") {
      loadRankings();
    }
  });

  el.playerSearch.addEventListener("input", () => {
    const query = el.playerSearch.value.trim().toLowerCase();
    renderSuggestions(query);
  });

  el.playerSearch.addEventListener("focus", () => {
    el.playerSearch.select();
    renderSuggestions(el.playerSearch.value.trim().toLowerCase());
  });

  el.playerSearch.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && state.suggestionNames[0]) {
      event.preventDefault();
      selectPlayer(state.suggestionNames[0]);
    }
    if (event.key === "Escape") {
      hideSuggestions();
    }
  });

  el.playerSearch.addEventListener("blur", () => {
    window.setTimeout(hideSuggestions, 200);
  });

  el.suggestions.addEventListener("mousedown", (event) => {
    event.preventDefault();
    const button = event.target.closest("button");
    if (!button) return;
    selectPlayer(button.dataset.player);
  });

  el.comparePlayerSearch.addEventListener("input", () => {
    const query = el.comparePlayerSearch.value.trim().toLowerCase();
    renderCompareSuggestions(query);
  });

  el.comparePlayerSearch.addEventListener("focus", () => {
    el.comparePlayerSearch.select();
    renderCompareSuggestions(el.comparePlayerSearch.value.trim().toLowerCase());
  });

  el.comparePlayerSearch.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && state.suggestionNames[0]) {
      event.preventDefault();
      selectComparePlayer(state.suggestionNames[0]);
    }
    if (event.key === "Escape") {
      hideCompareSuggestions();
    }
  });

  el.comparePlayerSearch.addEventListener("blur", () => {
    window.setTimeout(hideCompareSuggestions, 200);
  });

  el.compareSuggestions.addEventListener("mousedown", (event) => {
    event.preventDefault();
    const button = event.target.closest("button");
    if (!button) return;
    selectComparePlayer(button.dataset.player);
  });

  el.metricSelect.addEventListener("change", () => renderLeaderboard());

  // Advanced Analytics
  el.analyticsSubTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    state.analytics.subtab = button.dataset.subtab;
    setActive("#analyticsSubTabs", button);
    renderAnalyticsSubtabs();
  });

  // Rankings role tabs removed - now controlled by main SKILL buttons

  el.countryRoleTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    state.analytics.countryRole = button.dataset.role;
    setActive("#countryRoleTabs", button);
    loadCountryStats();
  });

  el.countryFormatTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    state.analytics.countryFormat = button.dataset.format;
    setActive("#countryFormatTabs", button);
    loadCountryStats();
  });

  el.countryFilter.addEventListener("change", () => {
    state.analytics.countryFilter = el.countryFilter.value;
    loadCountryStats();
  });
}

function setActive(parentSelector, activeButton) {
  document.querySelectorAll(`${parentSelector} button`).forEach((button) => {
    button.classList.toggle("active", button === activeButton);
  });
}

function render() {
  const names = playerNames();
  if (!names.includes(state.selectedPlayer)) {
    state.selectedPlayer = pickDefaultPlayer();
  }
  if (!names.includes(state.comparePlayer) || state.comparePlayer === state.selectedPlayer) {
    state.comparePlayer = pickComparePlayer();
  }

  renderViews();
  el.playerCount.textContent = new Set(state.rows.map((row) => row.full_name)).size.toLocaleString();
  renderMetricPicker();
  renderPlayerHeader();
  renderKpis();
  renderBarChart();
  renderCompareChart();
  renderCompareHeader();
  renderVersusCards();
  renderCompareFormatChart();
  renderLeaderboard();
  renderProfile();
}

function renderViews() {
  el.overviewView.classList.toggle("active-view", state.activeTab === "overview");
  el.compareView.classList.toggle("active-view", state.activeTab === "compare");
  el.analyticsView.classList.toggle("active-view", state.activeTab === "analytics");
  document.querySelectorAll("#appTabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === state.activeTab);
  });
  
  // Hide search in Advanced Analytics tab
  const topSearch = document.querySelector(".top-search");
  if (topSearch) {
    topSearch.style.display = state.activeTab === "analytics" ? "none" : "flex";
  }
}

function renderMetricPicker() {
  const metrics = availableMetrics();
  const current = el.metricSelect.value || ROLE_CONFIG[state.role].primary;
  el.metricSelect.innerHTML = metrics
    .map((metric) => `<option value="${metric}"${metric === current ? " selected" : ""}>${label(metric)}</option>`)
    .join("");
}

function renderPlayerHeader() {
  const rows = playerRows(state.selectedPlayer);
  const countries = [...new Set(rows.map((row) => row.country).filter(Boolean))];
  const formats = [...new Set(rows.map((row) => row.format))].sort(formatSort);
  el.selectedPlayerName.textContent = state.selectedPlayer || "No player found";
  el.selectedPlayerMeta.textContent = `${countries.join(", ") || "Unknown country"} | ${formats.join(", ") || "No format data"} | ${state.role}`;
}

function renderKpis() {
  const kpis = ROLE_CONFIG[state.role].kpis.filter((metric) => metricAvailable(metric));
  el.kpiGrid.innerHTML = kpis.map((metric) => {
    const value = aggregate(playerRows(state.selectedPlayer), metric);
    return `
      <article class="kpi">
        <small>${label(metric)}</small>
        <strong>${formatValue(value, metric)}</strong>
        <span>${state.format}</span>
      </article>
    `;
  }).join("");
}

function renderBarChart() {
  const primary = ROLE_CONFIG[state.role].primary;
  const rows = playerRows(state.selectedPlayer, true);
  const values = ["Test", "ODI", "T20"].map((format) => ({
    format,
    value: aggregate(rows.filter((row) => row.format === format), primary)
  }));
  const max = Math.max(...values.map((item) => Number(item.value) || 0), 1);

  el.barTitle.textContent = `${label(primary)} by format`;
  el.barChart.innerHTML = values.map((item) => `
    <div class="bar-row">
      <span class="bar-label">${item.format}</span>
      <div class="track"><div class="fill" style="width: ${Math.max((Number(item.value) || 0) / max * 100, 2)}%"></div></div>
      <span class="bar-value">${formatValue(item.value, primary)}</span>
    </div>
  `).join("");
}

function renderCompareChart() {
  const metrics = availableMetrics().slice(0, 5);
  const firstRows = playerRows(state.selectedPlayer);
  const secondRows = playerRows(state.comparePlayer);

  el.compareTitle.textContent = `${state.selectedPlayer} vs ${state.comparePlayer}`;
  el.compareChart.innerHTML = metrics.map((metric) => {
    const first = aggregate(firstRows, metric);
    const second = aggregate(secondRows, metric);
    const max = Math.max(Number(first) || 0, Number(second) || 0, 1);
    const firstPct = Math.max((Number(first) || 0) / max * 100, 5);
    const secondPct = Math.max((Number(second) || 0) / max * 100, 5);
    const firstWins = (Number(first) || 0) > (Number(second) || 0);

    return `
      <div class="vertical-compare-item">
        <div class="vertical-compare-label">${label(metric)}</div>
        <div class="vertical-bars-container">
          <div class="vertical-bar-column">
            <div class="vertical-bar-value ${firstWins ? 'winning' : ''}">${formatValue(first, metric)}</div>
            <div class="vertical-bar-wrapper">
              <div class="vertical-bar primary-vertical-bar" style="height: ${firstPct}%">
                <div class="bar-shimmer"></div>
              </div>
            </div>
            <div class="vertical-bar-player">Player 1</div>
          </div>
          <div class="vertical-bar-column">
            <div class="vertical-bar-value ${!firstWins ? 'winning' : ''}">${formatValue(second, metric)}</div>
            <div class="vertical-bar-wrapper">
              <div class="vertical-bar secondary-vertical-bar" style="height: ${secondPct}%">
                <div class="bar-shimmer"></div>
              </div>
            </div>
            <div class="vertical-bar-player">Player 2</div>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function renderCompareHeader() {
  const firstRows = playerRows(state.selectedPlayer);
  const secondRows = playerRows(state.comparePlayer);
  const firstCountry = firstRows[0]?.country || "Unknown";
  const secondCountry = secondRows[0]?.country || "Unknown";
  el.compareTitle.textContent = `${state.selectedPlayer} vs ${state.comparePlayer}`;
  el.compareMeta.textContent = `${firstCountry} against ${secondCountry} | ${state.format} | ${state.role}`;
}

function renderVersusCards() {
  el.primaryCompareCard.innerHTML = renderVersusCard(state.selectedPlayer);
  el.secondaryCompareCard.innerHTML = renderVersusCard(state.comparePlayer);
}

function renderVersusCard(playerName) {
  const rows = playerRows(playerName);
  const country = rows[0]?.country || "Unknown country";
  const metrics = availableMetrics().slice(0, 4);
  return `
    <h3>${escapeHtml(playerName)}</h3>
    <p class="versus-meta">${escapeHtml(country)} | ${state.format}</p>
    <div class="versus-stats">
      ${metrics.map((metric) => `
        <div class="versus-stat">
          <small>${label(metric)}</small>
          <strong>${formatValue(aggregate(rows, metric), metric)}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function renderCompareFormatChart() {
  const primary = ROLE_CONFIG[state.role].primary;
  const firstRows = playerRows(state.selectedPlayer, true);
  const secondRows = playerRows(state.comparePlayer, true);
  const values = ["Test", "ODI", "T20"].map((format) => {
    const first = aggregate(firstRows.filter((row) => row.format === format), primary);
    const second = aggregate(secondRows.filter((row) => row.format === format), primary);
    return { format, first, second };
  });
  const max = Math.max(...values.flatMap((item) => [Number(item.first) || 0, Number(item.second) || 0]), 1);
  el.compareFormatTitle.textContent = `${label(primary)} by format`;
  el.compareFormatChart.innerHTML = values.map((item) => {
    const firstPct = Math.max((Number(item.first) || 0) / max * 100, 5);
    const secondPct = Math.max((Number(item.second) || 0) / max * 100, 5);
    const firstWins = (Number(item.first) || 0) > (Number(item.second) || 0);

    return `
      <div class="vertical-compare-item">
        <div class="vertical-compare-label">${item.format}</div>
        <div class="vertical-bars-container">
          <div class="vertical-bar-column">
            <div class="vertical-bar-value ${firstWins ? 'winning' : ''}">${formatValue(item.first, primary)}</div>
            <div class="vertical-bar-wrapper">
              <div class="vertical-bar primary-vertical-bar" style="height: ${firstPct}%">
                <div class="bar-shimmer"></div>
              </div>
            </div>
            <div class="vertical-bar-player">Player 1</div>
          </div>
          <div class="vertical-bar-column">
            <div class="vertical-bar-value ${!firstWins ? 'winning' : ''}">${formatValue(item.second, primary)}</div>
            <div class="vertical-bar-wrapper">
              <div class="vertical-bar secondary-vertical-bar" style="height: ${secondPct}%">
                <div class="bar-shimmer"></div>
              </div>
            </div>
            <div class="vertical-bar-player">Player 2</div>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function renderLeaderboard() {
  const metric = el.metricSelect.value || ROLE_CONFIG[state.role].primary;
  const grouped = new Map();
  relevantRows().forEach((row) => {
    if (!grouped.has(row.full_name)) grouped.set(row.full_name, []);
    grouped.get(row.full_name).push(row);
  });

  const leaders = [...grouped.entries()]
    .map(([name, rows]) => ({ name, rows, value: aggregate(rows, metric), country: rows[0]?.country || "" }))
    .filter((item) => item.value !== null && item.value !== undefined && item.value !== "")
    .sort((a, b) => sortMetric(metric, a.value, b.value))
    .slice(0, 12);

  el.leaderTitle.textContent = `Top ${label(metric).toLowerCase()}`;
  el.leaderHead.innerHTML = `<tr><th>Rank</th><th>Player</th><th>Country</th><th>${label(metric)}</th></tr>`;
  el.leaderBody.innerHTML = leaders.map((item, index) => `
    <tr>
      <td>${index + 1}</td>
      <td>${escapeHtml(item.name)}</td>
      <td>${escapeHtml(item.country)}</td>
      <td>${formatValue(item.value, metric)}</td>
    </tr>
  `).join("");
}

function renderProfile() {
  const rows = playerRows(state.selectedPlayer);
  const bestFormat = bestFormatForPlayer(rows);
  const profileMetrics = ROLE_CONFIG[state.role].profile.filter((metric) => metricAvailable(metric));
  el.profileCard.innerHTML = `
    <div class="profile-top">
      <strong>${escapeHtml(bestFormat.format || "No data")}</strong>
      <span>Best format by ${label(ROLE_CONFIG[state.role].primary).toLowerCase()}</span>
    </div>
    ${profileMetrics.map((metric) => `
      <div class="profile-row">
        <span>${label(metric)}</span>
        <span>${formatValue(aggregate(rows, metric), metric)}</span>
      </div>
    `).join("")}
  `;
}

function renderSuggestions(query) {
  const ranked = rankedPlayers().map((player) => player.name);
  const matches = ranked
    .filter((name) => !query || name.toLowerCase().includes(query))
    .slice(0, 8);
  state.suggestionNames = matches;
  if (!matches.length) {
    el.suggestions.innerHTML = `<div class="suggestion"><span>No player found</span></div>`;
    el.suggestions.hidden = false;
    return;
  }
  el.suggestions.innerHTML = matches.map((name) => {
    const rows = playerRows(name);
    const country = rows[0]?.country || "Unknown";
    const primary = ROLE_CONFIG[state.role].primary;
    return `
      <button type="button" class="suggestion" data-player="${escapeHtml(name)}">
        <span>
          <strong>${escapeHtml(name)}</strong>
          <small>${escapeHtml(country)} | ${state.role}</small>
        </span>
        <small>${formatValue(aggregate(rows, primary), primary)} ${label(primary)}</small>
      </button>
    `;
  }).join("");
  el.suggestions.hidden = false;
}

function hideSuggestions() {
  el.suggestions.hidden = true;
}

function hideCompareSuggestions() {
  el.compareSuggestions.hidden = true;
}

function selectPlayer(name) {
  state.selectedPlayer = name;
  if (state.comparePlayer === state.selectedPlayer) {
    state.comparePlayer = pickComparePlayer();
  }
  el.playerSearch.value = name;
  hideSuggestions();
  render();
}

function selectComparePlayer(name) {
  state.comparePlayer = name;
  el.comparePlayerSearch.value = name;
  hideCompareSuggestions();
  render();
}

function renderCompareSuggestions(query) {
  const ranked = rankedPlayers().map((player) => player.name);
  const matches = ranked
    .filter((name) => name !== state.selectedPlayer && (!query || name.toLowerCase().includes(query)))
    .slice(0, 8);
  state.suggestionNames = matches;
  if (!matches.length) {
    el.compareSuggestions.innerHTML = `<div class="suggestion"><span>No player found</span></div>`;
    el.compareSuggestions.hidden = false;
    return;
  }
  el.compareSuggestions.innerHTML = matches.map((name) => {
    const rows = playerRows(name);
    const country = rows[0]?.country || "Unknown";
    const primary = ROLE_CONFIG[state.role].primary;
    return `
      <button type="button" class="suggestion" data-player="${escapeHtml(name)}">
        <span>
          <strong>${escapeHtml(name)}</strong>
          <small>${escapeHtml(country)} | ${state.role}</small>
        </span>
        <small>${formatValue(aggregate(rows, primary), primary)} ${label(primary)}</small>
      </button>
    `;
  }).join("");
  el.compareSuggestions.hidden = false;
}

function relevantRows(includeAllFormats = false) {
  return state.rows.filter((row) => {
    const formatOk = includeAllFormats || row.format === state.format;
    return row.role === state.role && formatOk;
  });
}

function playerRows(name, includeAllFormats = false) {
  return relevantRows(includeAllFormats).filter((row) => row.full_name === name);
}

function playerNames() {
  return [...new Set(relevantRows().map((row) => row.full_name))]
    .filter(Boolean)
    .sort((a, b) => a.localeCompare(b));
}

function pickDefaultPlayer() {
  return rankedPlayers()[0]?.name || "";
}

function pickComparePlayer() {
  return rankedPlayers().find((player) => player.name !== state.selectedPlayer)?.name || state.selectedPlayer;
}

function rankedPlayers() {
  const primary = ROLE_CONFIG[state.role].primary;
  const grouped = new Map();
  relevantRows().forEach((row) => {
    if (!grouped.has(row.full_name)) grouped.set(row.full_name, []);
    grouped.get(row.full_name).push(row);
  });
  return [...grouped.entries()]
    .map(([name, rows]) => ({ name, value: aggregate(rows, primary) }))
    .sort((a, b) => (Number(b.value) || 0) - (Number(a.value) || 0));
}

function availableMetrics() {
  return ROLE_CONFIG[state.role].metrics.filter((metric) => metricAvailable(metric));
}

function metricAvailable(metric) {
  return relevantRows(true).some((row) => row[metric] !== undefined && row[metric] !== null && row[metric] !== "");
}

function aggregate(rows, metric) {
  const values = rows.map((row) => row[metric]).filter((value) => value !== undefined && value !== null && value !== "");
  if (!values.length) return null;

  if (["average", "strike_rate", "economy"].includes(metric)) {
    const numeric = values.filter((value) => typeof value === "number");
    return numeric.length ? numeric.reduce((sum, value) => sum + value, 0) / numeric.length : values[0];
  }

  if (["highest_score"].includes(metric)) {
    return Math.max(...values.map(Number).filter(Number.isFinite));
  }

  if (["best_innings", "best_match"].includes(metric)) {
    return values[0];
  }

  const numeric = values.filter((value) => typeof value === "number");
  return numeric.length ? numeric.reduce((sum, value) => sum + value, 0) : values[0];
}

function bestFormatForPlayer(rows) {
  const primary = ROLE_CONFIG[state.role].primary;
  return ["Test", "ODI", "T20"]
    .map((format) => ({ format, value: aggregate(rows.filter((row) => row.format === format), primary) }))
    .sort((a, b) => (Number(b.value) || 0) - (Number(a.value) || 0))[0] || {};
}

function sortMetric(metric, a, b) {
  if (["average", "economy", "strike_rate"].includes(metric) && state.role === "Bowling") {
    return (Number(a) || Infinity) - (Number(b) || Infinity);
  }
  return (Number(b) || 0) - (Number(a) || 0);
}

function formatValue(value, metric) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value !== "number") return value;
  if (["average", "strike_rate", "economy"].includes(metric)) return value.toFixed(2);
  return Math.round(value).toLocaleString();
}

function label(metric) {
  return LABELS[metric] || metric.replaceAll("_", " ");
}

function formatSort(a, b) {
  return ["Test", "ODI", "T20"].indexOf(a) - ["Test", "ODI", "T20"].indexOf(b);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;"
  })[char]);
}

// ============================================================================
// ADVANCED ANALYTICS — live queries against the materialized views
// ============================================================================

function renderAnalyticsSubtabs() {
  el.rankingsSubview.classList.toggle("active-subview", state.analytics.subtab === "rankings");
  el.countrySubview.classList.toggle("active-subview", state.analytics.subtab === "country");
}

async function loadCountryList() {
  const response = await fetch("/api/countries");
  const countries = response.ok ? await response.json() : [];
  state.analytics.countryList = countries;
  el.countryFilter.innerHTML = `<option value="">All countries</option>` +
    countries.map((country) => `<option value="${escapeHtml(country)}">${escapeHtml(country)}</option>`).join("");
}

async function loadRankings() {
  const role = state.analytics.rankingsRole;
  const format = state.format;
  
  // Always use players endpoint for specific formats (Test, ODI, T20)
  const endpoint = `/api/players?role=${role}&format=${format}`;
  
  const response = await fetch(endpoint);
  const payload = await response.json().catch(() => null);
  state.analytics.rankingsError = response.ok ? "" : (payload?.error || `Request failed (${response.status})`);
  state.analytics.rankingsData = response.ok && Array.isArray(payload) ? payload : [];
  renderRankingsTable();
}

function renderRankingsTable() {
  const role = state.analytics.rankingsRole;
  const format = state.format;
  
  // Use simplified columns for format data
  // Note: Column names must match what the SERVER returns (server aliases "Runs" AS runs)
  const formatColumns = {
    batsmen: [
      ["full_name", "Player"], ["country", "Country"],
      ["matches_played", "Matches"], ["runs", "Runs"], ["hundreds", "100s"],
      ["fifties", "50s"], ["average", "Average"], ["strike_rate", "Strike Rate"]
    ],
    bowler: [
      ["full_name", "Player"], ["country", "Country"],
      ["matches_played", "Matches"], ["wickets", "Wickets"],
      ["average", "Average"], ["economy", "Economy"], ["strike_rate", "Strike Rate"]
    ],
    fielder: [
      ["full_name", "Player"], ["country", "Country"],
      ["matches_played", "Matches"], ["dismissals", "Dismissals"],
      ["catches", "Catches"], ["stumpings", "Stumpings"], ["catch_wickets", "Keeper Catches"]
    ]
  };
  
  const columns = formatColumns[role];
  let rows = [...state.analytics.rankingsData];

  // Sort the data based on role - ALWAYS sort by primary metric first
  // Note: Use column names as returned by the server
  const sortConfig = {
    batsmen: ["runs", "hundreds", "fifties", "matches_played"],
    bowler: ["wickets", "five_wicket_hauls", "matches_played"],
    fielder: ["catches", "catch_wickets", "stumpings", "matches_played"]
  };
  
  const sortKeys = sortConfig[role];
  rows.sort((a, b) => {
    for (const key of sortKeys) {
      const aVal = Number(a[key]) || 0;
      const bVal = Number(b[key]) || 0;
      const diff = bVal - aVal;
      if (diff !== 0) return diff;
    }
    return 0;
  });

  el.rankingsTitle.textContent = `${format} ${RANKINGS_LABELS[role]} leaders`;
  el.rankingsHead.innerHTML = `<tr>${columns.map(([, heading]) => `<th>${heading}</th>`).join("")}</tr>`;

  if (state.analytics.rankingsError) {
    el.rankingsBody.innerHTML = `<tr><td colspan="${columns.length}">Query failed: ${escapeHtml(state.analytics.rankingsError)}</td></tr>`;
    return;
  }
  if (!rows.length) {
    el.rankingsBody.innerHTML = `<tr><td colspan="${columns.length}">No data yet — run the DAG to populate this view.</td></tr>`;
    return;
  }

  el.rankingsBody.innerHTML = rows.slice(0, 25).map((row) => `
    <tr>
      ${columns.map(([key]) => `<td>${escapeHtml(formatCell(row[key]))}</td>`).join("")}
    </tr>
  `).join("");
}

async function loadCountryStats() {
  const { countryRole, countryFormat, countryFilter } = state.analytics;
  const params = new URLSearchParams({ role: countryRole, format: countryFormat });
  if (countryFilter) params.set("country", countryFilter);
  const response = await fetch(`/api/country-stats?${params.toString()}`);
  const payload = await response.json().catch(() => null);
  state.analytics.countryError = response.ok ? "" : (payload?.error || `Request failed (${response.status})`);
  state.analytics.countryData = response.ok && Array.isArray(payload) ? payload : [];
  renderCountryStatsTable();
}

function renderCountryStatsTable() {
  const role = state.analytics.countryRole;
  const columns = COUNTRY_COLUMNS[role];
  const primaryMetric = columns[2][0];
  const rows = [...state.analytics.countryData].sort((a, b) => (Number(b[primaryMetric]) || 0) - (Number(a[primaryMetric]) || 0));

  el.countryStatsTitle.textContent = `Country-wise ${RANKINGS_LABELS[role]} statistics (${state.analytics.countryFormat})`;

  if (state.analytics.countryError) {
    el.countryStatsContainer.innerHTML = `<div class="panel span-12"><p style="padding: 2rem; text-align: center;">Query failed: ${escapeHtml(state.analytics.countryError)}</p></div>`;
    return;
  }
  if (!rows.length) {
    el.countryStatsContainer.innerHTML = `<div class="panel span-12"><p style="padding: 2rem; text-align: center;">No data yet — run the DAG to populate this view.</p></div>`;
    return;
  }

  // Render each country as a separate block
  el.countryStatsContainer.innerHTML = rows.map((row) => {
    const country = row.country || "Unknown";
    const flag = getCountryFlag(country);
    const statsHtml = columns.slice(1).map(([key, heading]) => `
      <div class="country-stat-item">
        <small>${heading}</small>
        <strong>${escapeHtml(formatCell(row[key]))}</strong>
      </div>
    `).join("");
    
    return `
      <article class="panel country-block">
        <div class="country-block-header">
          <h4>${flag} ${escapeHtml(country)}</h4>
        </div>
        <div class="country-stats-grid">
          ${statsHtml}
        </div>
      </article>
    `;
  }).join("");
}

function getCountryFlag(country) {
  const flags = {
    "India": "🇮🇳",
    "Australia": "🇦🇺",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Pakistan": "🇵🇰",
    "South Africa": "🇿🇦",
    "New Zealand": "🇳🇿",
    "West Indies": "🏴‍☠️",
    "Sri Lanka": "🇱🇰",
    "Bangladesh": "🇧🇩",
    "Zimbabwe": "🇿🇼",
    "Afghanistan": "🇦🇫",
    "Afganisthan": "🇦🇫",
    "Ireland": "🇮🇪",
    "Netherlands": "🇳🇱",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "United Arab Emirates": "🇦🇪",
    "Kenya": "🇰🇪",
    "Canada": "🇨🇦",
    "Bermuda": "🇧🇲",
    "Papua New Guinea": "🇵🇬",
    "Namibia": "🇳🇦",
    "Nepal": "🇳🇵",
    "HongKonng": "🇭🇰"
  };
  return flags[country] || "🏏";
}

function formatCell(value) {
  if (value === null || value === undefined || value === "") return "-";
  if (Array.isArray(value)) return value.join(" / ");
  if (typeof value === "number") return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
  return value;
}
