const API_BASE = "http://127.0.0.1:5000/api";

const state = {
  area: null,
  bhk: null,
  location: null,
  floor: 5,
  age: 0,
  amenities: {
    parking: 1,
    gym: 0,
    pool: 0,
    clubhouse: 0,
    security_24: 1,
    power_backup: 1,
  }
};

const $ = id => document.getElementById(id);

// ── Theme Switcher ────────────────────────────────────
function initThemeSwitcher() {
  const colorButtons = document.querySelectorAll(".color-btn");
  
  // Load saved theme from localStorage
  const savedTheme = localStorage.getItem("app-theme") || "orange";
  setTheme(savedTheme);
  
  colorButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const theme = btn.dataset.theme;
      setTheme(theme);
      localStorage.setItem("app-theme", theme);
    });
  });
}

function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  
  // Update active button
  document.querySelectorAll(".color-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.theme === theme);
  });
}

// ── Format price in Indian notation ────────────────────
function formatINR(amount) {
  if (amount >= 10000000)  return `₹${(amount / 10000000).toFixed(2)} Cr`;
  if (amount >= 100000)    return `₹${(amount / 100000).toFixed(2)} L`;
  return `₹${amount.toLocaleString("en-IN")}`;
}

// ── Pill selector factory ───────────────────────────────
function initPills(groupId, key, callback) {
  const group = document.getElementById(groupId);
  if (!group) return;
  group.querySelectorAll(".pill").forEach(pill => {
    pill.addEventListener("click", () => {
      group.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      state[key] = pill.dataset.value;
      if (callback) callback(pill.dataset.value);
    });
  });
}

// ── Load & render locations ────────────────────────────
async function loadLocations() {
  try {
    const res  = await fetch(`${API_BASE}/locations`);
    const data = await res.json();
    renderLocations(data.locations);
  } catch {
    // fallback: render a placeholder message
    const grid = $("location-grid");
    if (grid) grid.innerHTML = `<p style="color:var(--muted);font-size:13px">⚠️ Could not load locations — make sure the server is running.</p>`;
  }
}

function renderLocations(locations) {
  const grid = $("location-grid");
  if (!grid) return;
  grid.innerHTML = "";

  const tierClass = { luxury: "tier-luxury", premium: "tier-premium", mid: "tier-mid", affordable: "tier-affordable" };
  const tierLabel = { luxury: "Luxury", premium: "Premium", mid: "Mid", affordable: "Budget" };

  locations.forEach(loc => {
    const card = document.createElement("div");
    card.className = "location-card";
    card.dataset.id = loc.id;
    card.innerHTML = `
      <span class="loc-tier ${tierClass[loc.tier] || ''}">${tierLabel[loc.tier] || ''}</span>
      <div class="loc-name">${loc.name}</div>
      <div class="loc-zone">${loc.zone}</div>
    `;
    card.addEventListener("click", () => {
      grid.querySelectorAll(".location-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      state.location = loc.id;
    });
    grid.appendChild(card);
  });
}

// ── Amenity toggles ────────────────────────────────────
function initAmenities() {
  document.querySelectorAll(".amenity-toggle").forEach(toggle => {
    const key = toggle.dataset.key;
    // Set initial visual state
    if (state.amenities[key]) toggle.classList.add("active");

    toggle.addEventListener("click", () => {
      state.amenities[key] = state.amenities[key] ? 0 : 1;
      toggle.classList.toggle("active", !!state.amenities[key]);
    });
  });
}

// ── Custom area input ───────────────────────────────────
function initCustomArea() {
  const input = $("custom-area");
  if (!input) return;
  input.addEventListener("input", () => {
    const val = parseInt(input.value);
    if (val > 0) {
      // deselect pills
      document.querySelectorAll("#area-pills .pill").forEach(p => p.classList.remove("active"));
      state.area = val;
    }
  });
}

// ── Floor & Age dropdowns ───────────────────────────────
function initSelects() {
  const floorSel = $("floor-select");
  const ageSel   = $("age-select");
  if (floorSel) floorSel.addEventListener("change", () => { state.floor = parseInt(floorSel.value); });
  if (ageSel)   ageSel.addEventListener("change",   () => { state.age   = parseInt(ageSel.value);   });
}

// ── Validate before predict ─────────────────────────────
function validate() {
  if (!state.area)     return "Please select or enter an area.";
  if (!state.bhk)      return "Please select a BHK type.";
  if (!state.location) return "Please select a location.";
  return null;
}

// ── Main predict call ───────────────────────────────────
async function predict() {
  const errEl = $("error-msg");
  errEl.classList.remove("visible");

  const validationError = validate();
  if (validationError) {
    errEl.textContent = validationError;
    errEl.classList.add("visible");
    return;
  }

  const btn = $("estimate-btn");
  btn.classList.add("loading");
  btn.disabled = true;

  const payload = {
    area:         state.area,
    location:     state.location,
    bhk:          state.bhk,
    floor:        state.floor,
    age:          state.age,
    parking:      state.amenities.parking,
    gym:          state.amenities.gym,
    pool:         state.amenities.pool,
    clubhouse:    state.amenities.clubhouse,
    security_24:  state.amenities.security_24,
    power_backup: state.amenities.power_backup,
  };

  try {
    const res  = await fetch(`${API_BASE}/predict`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Prediction failed");
    renderResult(data);

  } catch (err) {
    errEl.textContent = `Error: ${err.message}`;
    errEl.classList.add("visible");
  } finally {
    btn.classList.remove("loading");
    btn.disabled = false;
  }
}

// ── Render result panel ─────────────────────────────────
function renderResult(data) {
  const panel = $("result-panel");

  // Price
  $("result-price").textContent = formatINR(data.predicted_price);
  $("result-range").textContent =
    `Range: ${formatINR(data.range_low)} – ${formatINR(data.range_high)}`;

  // Price per sq ft
  $("stat-psqft").textContent = `₹${data.price_per_sqft.toLocaleString("en-IN")}`;
  $("stat-area").textContent  = `${state.area} sq ft`;
  $("stat-bhk").textContent   = state.bhk.toUpperCase();
  $("stat-tier").textContent  = data.tier;

  // Tier badge styling
  const badge = $("tier-badge");
  badge.textContent = data.tier;
  const tierStyles = {
    "Luxury":     { bg: "rgba(251,191,36,0.15)", color: "#fbbf24" },
    "Premium":    { bg: "rgba(249,115,22,0.15)", color: "#f97316" },
    "Mid-Range":  { bg: "rgba(99,102,241,0.15)", color: "#818cf8" },
    "Affordable": { bg: "rgba(34,197,94,0.15)",  color: "#22c55e" },
  };
  const ts = tierStyles[data.tier] || tierStyles["Mid-Range"];
  badge.style.background = ts.bg;
  badge.style.color      = ts.color;

  // Location meta
  const meta = data.location_meta || {};
  $("loc-name-result").textContent    = meta.name        || state.location;
  $("loc-desc-result").textContent    = meta.description || "";

  const metaTags = $("loc-meta-tags");
  metaTags.innerHTML = "";
  if (meta.connectivity) {
    metaTags.innerHTML += `<span class="loc-meta-tag tag-conn">🚇 Connectivity: ${meta.connectivity}</span>`;
  }
  if (meta.appreciation) {
    metaTags.innerHTML += `<span class="loc-meta-tag tag-appr">📈 Appreciation: ${meta.appreciation}</span>`;
  }

  // Amenity chips (from location metadata)
  const chipsEl = $("amenity-chips");
  chipsEl.innerHTML = "";
  (meta.amenities || []).forEach(am => {
    const chip = document.createElement("span");
    chip.className = "amenity-chip";
    chip.textContent = am;
    chipsEl.appendChild(chip);
  });

  // Show panel and scroll
  panel.classList.add("visible");
  panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// ── Init ────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initThemeSwitcher();
  initPills("area-pills", "area");
  initPills("bhk-pills", "bhk");
  initCustomArea();
  initAmenities();
  initSelects();
  loadLocations();

  $("estimate-btn").addEventListener("click", predict);
});
