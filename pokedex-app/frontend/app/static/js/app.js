/* ============================================================
   POKÉDEX — frontend app
   ============================================================ */

'use strict';

// ---------------------------------------------------------------------------
// Type colour map (mirrors CSS custom properties)
// ---------------------------------------------------------------------------
const TYPE_COLORS = {
  normal:   '#9199a1',
  fire:     '#ff9c54',
  water:    '#4d90d5',
  electric: '#f3d23b',
  grass:    '#63bb5b',
  ice:      '#74cec0',
  fighting: '#ce416b',
  poison:   '#ab6ac8',
  ground:   '#d97845',
  flying:   '#89aae3',
  psychic:  '#f97176',
  bug:      '#91c12f',
  rock:     '#c5b78c',
  ghost:    '#5269ac',
  dragon:   '#0b6dc3',
  dark:     '#5a5465',
  steel:    '#5a8ea2',
  fairy:    '#ec8fe6',
};

// Stat bar colours (GameFreak palette-inspired)
const STAT_COLORS = {
  hp:               '#ff5959',
  attack:           '#f5ac78',
  defense:          '#fae078',
  'special-attack': '#9db7f5',
  'special-defense':'#a7db8d',
  speed:            '#fa92b2',
};

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
const state = {
  page:         0,
  limit:        24,
  selectedType: null,
  searchQuery:  '',
  total:        0,
  loading:      false,
};

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------
const grid          = document.getElementById('pokemon-grid');
const searchInput   = document.getElementById('search-input');
const typeFilters   = document.getElementById('type-filters');
const prevBtn       = document.getElementById('prev-btn');
const nextBtn       = document.getElementById('next-btn');
const pageInfo      = document.getElementById('page-info');
const pagination    = document.getElementById('pagination');
const modalOverlay  = document.getElementById('modal-overlay');
const modalContent  = document.getElementById('modal-content');
const modalClose    = document.getElementById('modal-close');
const toast         = document.getElementById('toast');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function padId(n) {
  return '#' + String(n).padStart(4, '0');
}

function typeColor(type) {
  return TYPE_COLORS[type] ?? '#8b949e';
}

function badgeHtml(type, size = '') {
  return `<span class="badge${size}" style="background:${typeColor(type)}">${type}</span>`;
}

function showToast(msg, kind = 'info') {
  toast.textContent = msg;
  toast.className = `toast ${kind} show`;
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove('show'), 3500);
}

// ---------------------------------------------------------------------------
// Fetch wrappers
// ---------------------------------------------------------------------------

async function apiFetch(url) {
  const resp = await fetch(url);
  if (resp.status === 401) {
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

// ---------------------------------------------------------------------------
// Type filter buttons
// ---------------------------------------------------------------------------

async function loadTypes() {
  try {
    const types = await apiFetch('/api/types');

    // "All" button
    const allBtn = createTypeBtn('All', '#4a5568', '');
    allBtn.classList.add('active');
    typeFilters.appendChild(allBtn);

    types.forEach(type => {
      typeFilters.appendChild(createTypeBtn(type, typeColor(type), type));
    });
  } catch {
    // non-critical — filters just won't appear
  }
}

function createTypeBtn(label, color, typeValue) {
  const btn = document.createElement('button');
  btn.className = 'type-btn';
  btn.textContent = label;
  btn.style.background = color;
  btn.dataset.type = typeValue;
  btn.addEventListener('click', () => handleTypeFilter(btn, typeValue));
  return btn;
}

function handleTypeFilter(btn, type) {
  document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  state.selectedType = type || null;
  state.page = 0;
  state.searchQuery = '';
  searchInput.value = '';
  loadPokemon();
}

// ---------------------------------------------------------------------------
// Load & render pokemon list
// ---------------------------------------------------------------------------

async function loadPokemon() {
  if (state.loading) return;
  state.loading = true;
  renderLoading();

  try {
    let url;
    if (state.searchQuery) {
      url = `/api/search?q=${encodeURIComponent(state.searchQuery)}`;
    } else {
      const offset = state.page * state.limit;
      url = `/api/pokemon?offset=${offset}&limit=${state.limit}`;
      if (state.selectedType) url += `&type=${state.selectedType}`;
    }

    const data = await apiFetch(url);
    state.total = data.total;
    renderGrid(data.results);
    renderPagination();
  } catch (err) {
    if (err.message !== 'Unauthorized') {
      renderEmpty('Failed to load Pokémon. Please try again.');
      showToast('Failed to load Pokémon', 'error');
    }
  } finally {
    state.loading = false;
  }
}

function renderLoading() {
  grid.innerHTML = '<div class="loading-wrap"><div class="spinner"></div></div>';
}

function renderEmpty(msg = 'No Pokémon found.') {
  grid.innerHTML = `
    <div class="empty-state">
      <h2>No results</h2>
      <p>${msg}</p>
    </div>`;
}

function renderGrid(list) {
  if (!list.length) { renderEmpty(); return; }

  grid.innerHTML = list.map(p => {
    const primaryType = p.types[0] ?? 'normal';
    const color = typeColor(primaryType);
    const img = p.sprites.official_artwork ?? p.sprites.front_default ?? '';
    const fallback = p.sprites.front_default ?? '';

    return `
      <article class="pokemon-card" style="--card-color:${color}"
               onclick="openModal('${p.name}')" role="button" tabindex="0"
               aria-label="${p.name} ${padId(p.id)}">
        <div class="card-id">${padId(p.id)}</div>
        <div class="card-img-wrap">
          <img class="card-img"
               src="${img}"
               alt="${p.name}"
               loading="lazy"
               onerror="this.onerror=null;this.src='${fallback}'" />
        </div>
        <div class="card-name">${p.name}</div>
        <div class="type-badges">${p.types.map(t => badgeHtml(t)).join('')}</div>
      </article>`;
  }).join('');

  // Keyboard accessibility for cards
  grid.querySelectorAll('.pokemon-card').forEach(card => {
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') card.click();
    });
  });
}

function renderPagination() {
  pagination.style.display = 'flex';

  if (state.searchQuery) {
    prevBtn.style.visibility = 'hidden';
    nextBtn.style.visibility = 'hidden';
    pageInfo.textContent = `${state.total} result${state.total !== 1 ? 's' : ''}`;
    return;
  }

  prevBtn.style.visibility = '';
  nextBtn.style.visibility = '';
  const totalPages = Math.max(1, Math.ceil(state.total / state.limit));
  pageInfo.textContent = `Page ${state.page + 1} of ${totalPages} · ${state.total.toLocaleString()} Pokémon`;
  prevBtn.disabled = state.page === 0;
  nextBtn.disabled = state.page + 1 >= totalPages;
}

// ---------------------------------------------------------------------------
// Pagination controls
// ---------------------------------------------------------------------------

prevBtn.addEventListener('click', () => {
  if (state.page > 0) { state.page--; loadPokemon(); scrollToTop(); }
});
nextBtn.addEventListener('click', () => {
  state.page++;
  loadPokemon();
  scrollToTop();
});

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ---------------------------------------------------------------------------
// Search (debounced)
// ---------------------------------------------------------------------------

let searchTimer;
searchInput.addEventListener('input', e => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    const q = e.target.value.trim();
    state.searchQuery = q;
    state.page = 0;
    if (q) {
      // Deselect type filter
      document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
      state.selectedType = null;
    } else {
      // Restore "All" button active state
      const allBtn = typeFilters.querySelector('[data-type=""]');
      if (allBtn) allBtn.classList.add('active');
    }
    loadPokemon();
  }, 380);
});

// Keyboard shortcut: press "/" to focus search
document.addEventListener('keydown', e => {
  if (e.key === '/' && document.activeElement !== searchInput) {
    e.preventDefault();
    searchInput.focus();
  }
});

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

async function openModal(nameOrId) {
  modalOverlay.classList.add('active');
  modalContent.innerHTML = '<div class="loading-wrap"><div class="spinner"></div></div>';

  try {
    const p = await apiFetch(`/api/pokemon/${nameOrId}`);
    renderModal(p);
  } catch {
    modalContent.innerHTML = '<div class="empty-state"><h2>Not found</h2></div>';
  }
}

function renderModal(p) {
  const primaryType = p.types[0] ?? 'normal';
  const secondType  = p.types[1] ?? null;
  const heroGradient = secondType
    ? `linear-gradient(135deg, ${typeColor(primaryType)}30, ${typeColor(secondType)}30)`
    : `linear-gradient(135deg, ${typeColor(primaryType)}30, transparent)`;

  const img = p.sprites.official_artwork ?? p.sprites.front_default ?? '';
  const fallback = p.sprites.front_default ?? '';

  const statsTotal = p.stats.reduce((acc, s) => acc + s.base_stat, 0);

  const statsHtml = p.stats.map(s => {
    const pct = Math.min(100, Math.round((s.base_stat / 255) * 100));
    const color = STAT_COLORS[s.name] ?? '#68d391';
    return `
      <div class="stat-row">
        <span class="stat-name">${s.name.replace(/-/g, ' ')}</span>
        <span class="stat-value">${s.base_stat}</span>
        <div class="stat-track">
          <div class="stat-fill" style="width:0%;background:${color}"
               data-width="${pct}"></div>
        </div>
      </div>`;
  }).join('');

  const abilitiesHtml = p.abilities.map(a => `
    <span class="ability-tag ${a.is_hidden ? 'hidden' : ''}">${a.name}${a.is_hidden ? ' (hidden)' : ''}</span>
  `).join('');

  const shinyHtml = p.sprites.front_shiny ? `
    <div class="shiny-wrap">
      <p class="section-label">Shiny Form</p>
      <img src="${p.sprites.front_shiny}" alt="${p.name} shiny" loading="lazy" />
    </div>` : '';

  modalContent.innerHTML = `
    <div class="modal-hero" style="background:${heroGradient}">
      <img class="modal-hero-img"
           src="${img}" alt="${p.name}"
           onerror="this.onerror=null;this.src='${fallback}'" />
      <div>
        <div class="modal-hero-id">${padId(p.id)}</div>
        <h2 class="modal-hero-name">${p.name}</h2>
        <div class="modal-hero-types">${p.types.map(t => badgeHtml(t, ' modal-badge')).join('')}</div>
        <div class="modal-meta">
          <span class="modal-meta-label">Height</span>
          <span class="modal-meta-label">Weight</span>
          <span class="modal-meta-value">${(p.height / 10).toFixed(1)} m</span>
          <span class="modal-meta-value">${(p.weight / 10).toFixed(1)} kg</span>
          <span class="modal-meta-label">Exp.</span>
          <span class="modal-meta-label">Moves</span>
          <span class="modal-meta-value">${p.base_experience ?? '—'}</span>
          <span class="modal-meta-value">${p.moves_count}</span>
        </div>
      </div>
    </div>

    <p class="section-label">Abilities</p>
    <div class="abilities-wrap">${abilitiesHtml}</div>

    <p class="section-label">Base Stats</p>
    ${statsHtml}
    <p class="stat-total">Total: <strong>${statsTotal}</strong></p>

    ${shinyHtml}
  `;

  // Animate stat bars after DOM paint
  requestAnimationFrame(() => {
    modalContent.querySelectorAll('.stat-fill').forEach(el => {
      el.style.width = el.dataset.width + '%';
    });
  });
}

// Close modal handlers
modalOverlay.addEventListener('click', e => {
  if (e.target === modalOverlay) closeModal();
});
modalClose.addEventListener('click', closeModal);
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

function closeModal() {
  modalOverlay.classList.remove('active');
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
loadTypes();
loadPokemon();
