from flask import Flask, request, jsonify, render_template_string
import sqlite3
import random
from datetime import date

app = Flask(__name__)
DB_NAME = "aceest_fitness.db"

PROGRAM_TEMPLATES = {
    "Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"]
}

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT
        );
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            age INTEGER,
            height REAL,
            weight REAL,
            program TEXT,
            calories INTEGER,
            target_weight REAL,
            target_adherence INTEGER,
            membership_status TEXT DEFAULT 'Active',
            membership_end TEXT
        );
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            week TEXT,
            adherence INTEGER
        );
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            date TEXT,
            workout_type TEXT,
            duration_min INTEGER,
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            date TEXT,
            weight REAL,
            waist REAL,
            bodyfat REAL
        );
    """)
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES ('admin','admin','Admin')")
    conn.commit()
    conn.close()

# ---------- HTML TEMPLATE ----------
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>ACEest Fitness & Gym</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
  :root {
    --gold: #d4af37;
    --dark: #0f0f0f;
    --card: #1a1a1a;
    --border: #2a2a2a;
    --text: #e0e0e0;
    --muted: #888;
    --green: #2ecc71;
    --red: #e74c3c;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--dark); color: var(--text); font-family: 'DM Sans', sans-serif; min-height: 100vh; }
  h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 2px; }

  /* NAV */
  nav { background: var(--card); border-bottom: 2px solid var(--gold); padding: 0 2rem; display: flex; align-items: center; justify-content: space-between; height: 60px; }
  nav h1 { color: var(--gold); font-size: 1.8rem; }
  nav span { color: var(--muted); font-size: 0.85rem; }

  /* LAYOUT */
  .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
  .grid { display: grid; grid-template-columns: 280px 1fr; gap: 1.5rem; }

  /* CARDS */
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; }
  .card h3 { color: var(--gold); margin-bottom: 1rem; font-size: 1.1rem; }

  /* FORM ELEMENTS */
  input, select, textarea {
    width: 100%; padding: 0.6rem 0.8rem; background: #111; border: 1px solid var(--border);
    color: var(--text); border-radius: 6px; font-family: 'DM Sans', sans-serif; font-size: 0.9rem;
    margin-bottom: 0.8rem; outline: none; transition: border-color 0.2s;
  }
  input:focus, select:focus { border-color: var(--gold); }
  label { font-size: 0.8rem; color: var(--muted); display: block; margin-bottom: 0.3rem; }

  /* BUTTONS */
  .btn { padding: 0.6rem 1.2rem; border: none; border-radius: 6px; cursor: pointer; font-family: 'DM Sans', sans-serif; font-weight: 600; font-size: 0.85rem; transition: all 0.2s; width: 100%; margin-bottom: 0.5rem; }
  .btn-gold { background: var(--gold); color: #000; }
  .btn-gold:hover { background: #c9a227; }
  .btn-outline { background: transparent; color: var(--gold); border: 1px solid var(--gold); }
  .btn-outline:hover { background: var(--gold); color: #000; }
  .btn-danger { background: var(--red); color: #fff; }

  /* TABS */
  .tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0; }
  .tab { padding: 0.6rem 1.2rem; cursor: pointer; color: var(--muted); border-bottom: 2px solid transparent; transition: all 0.2s; font-weight: 500; }
  .tab.active { color: var(--gold); border-bottom-color: var(--gold); }

  /* TABLE */
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  th { text-align: left; padding: 0.6rem 1rem; color: var(--gold); font-family: 'Bebas Neue'; letter-spacing: 1px; border-bottom: 1px solid var(--border); }
  td { padding: 0.6rem 1rem; border-bottom: 1px solid var(--border); }
  tr:hover td { background: #222; }

  /* BADGES */
  .badge { padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
  .badge-green { background: rgba(46,204,113,0.15); color: var(--green); }
  .badge-red { background: rgba(231,76,60,0.15); color: var(--red); }

  /* SUMMARY GRID */
  .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }
  .stat { background: #111; border: 1px solid var(--border); border-radius: 6px; padding: 1rem; }
  .stat .val { font-family: 'Bebas Neue'; font-size: 1.8rem; color: var(--gold); }
  .stat .lbl { font-size: 0.75rem; color: var(--muted); margin-top: 0.2rem; }

  /* PANEL SECTIONS */
  .section { display: none; }
  .section.active { display: block; }

  /* TOAST */
  #toast { position: fixed; bottom: 2rem; right: 2rem; background: var(--gold); color: #000; padding: 0.8rem 1.5rem; border-radius: 8px; font-weight: 600; transform: translateY(100px); transition: transform 0.3s; z-index: 9999; }
  #toast.show { transform: translateY(0); }

  /* MODAL */
  .modal-bg { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 100; align-items: center; justify-content: center; }
  .modal-bg.open { display: flex; }
  .modal { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 2rem; width: 420px; }
  .modal h3 { color: var(--gold); margin-bottom: 1.2rem; }
  .modal-close { float: right; cursor: pointer; color: var(--muted); font-size: 1.2rem; }
</style>
</head>
<body>
<nav>
  <h1>⚡ ACEest</h1>
  <span id="nav-user">Fitness & Gym Management</span>
</nav>

<div class="container">
  <!-- LOGIN -->
  <div id="login-section" style="max-width:400px;margin:4rem auto;">
    <div class="card">
      <h2 style="color:var(--gold);margin-bottom:1.5rem;text-align:center;">LOGIN</h2>
      <label>Username</label>
      <input id="login-user" type="text" placeholder="admin"/>
      <label>Password</label>
      <input id="login-pass" type="password" placeholder="admin"/>
      <button class="btn btn-gold" onclick="doLogin()">LOGIN</button>
      <p id="login-err" style="color:var(--red);font-size:0.85rem;margin-top:0.5rem;"></p>
    </div>
  </div>

  <!-- MAIN APP -->
  <div id="app-section" style="display:none;">
    <div class="grid">
      <!-- SIDEBAR -->
      <div>
        <div class="card" style="margin-bottom:1rem;">
          <h3>CLIENTS</h3>
          <label>Select Client</label>
          <select id="client-select" onchange="loadClient()">
            <option value="">-- Select --</option>
          </select>
          <button class="btn btn-gold" onclick="openAddClient()">+ Add Client</button>
          <button class="btn btn-outline" onclick="generateProgram()">⚡ Generate Program</button>
          <button class="btn btn-outline" onclick="checkMembership()">🪪 Check Membership</button>
        </div>
        <!-- Client Info -->
        <div class="card" id="client-info-card" style="display:none;">
          <h3>CLIENT INFO</h3>
          <div id="client-info-body"></div>
        </div>
      </div>

      <!-- MAIN PANEL -->
      <div>
        <div class="tabs">
          <div class="tab active" onclick="switchTab('summary')">Summary</div>
          <div class="tab" onclick="switchTab('workouts')">Workouts</div>
          <div class="tab" onclick="switchTab('metrics')">Metrics</div>
          <div class="tab" onclick="switchTab('progress')">Progress</div>
          <div class="tab" onclick="switchTab('clients')">All Clients</div>
        </div>

        <!-- SUMMARY -->
        <div class="section active" id="tab-summary">
          <div id="summary-empty" class="card" style="text-align:center;color:var(--muted);padding:3rem;">Select a client to view summary</div>
          <div id="summary-content" style="display:none;">
            <div class="stat-grid" id="stat-grid"></div>
            <div class="card">
              <h3>PROGRAM</h3>
              <p id="summary-program" style="color:var(--text);"></p>
            </div>
          </div>
        </div>

        <!-- WORKOUTS -->
        <div class="section" id="tab-workouts">
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
              <h3>WORKOUTS</h3>
              <button class="btn btn-gold" style="width:auto;" onclick="openAddWorkout()">+ Add Workout</button>
            </div>
            <table id="workout-table">
              <thead><tr><th>Date</th><th>Type</th><th>Duration</th><th>Notes</th></tr></thead>
              <tbody id="workout-tbody"></tbody>
            </table>
          </div>
        </div>

        <!-- METRICS -->
        <div class="section" id="tab-metrics">
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
              <h3>BODY METRICS</h3>
              <button class="btn btn-gold" style="width:auto;" onclick="openAddMetric()">+ Add Metric</button>
            </div>
            <table>
              <thead><tr><th>Date</th><th>Weight</th><th>Waist</th><th>Body Fat %</th></tr></thead>
              <tbody id="metrics-tbody"></tbody>
            </table>
          </div>
        </div>

        <!-- PROGRESS -->
        <div class="section" id="tab-progress">
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
              <h3>WEEKLY ADHERENCE</h3>
              <button class="btn btn-gold" style="width:auto;" onclick="openAddProgress()">+ Log Week</button>
            </div>
            <table>
              <thead><tr><th>Week</th><th>Adherence %</th><th>Rating</th></tr></thead>
              <tbody id="progress-tbody"></tbody>
            </table>
          </div>
        </div>

        <!-- ALL CLIENTS -->
        <div class="section" id="tab-clients">
          <div class="card">
            <h3>ALL CLIENTS</h3>
            <table>
              <thead><tr><th>Name</th><th>Program</th><th>Membership</th><th>End Date</th></tr></thead>
              <tbody id="all-clients-tbody"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- MODALS -->
<div class="modal-bg" id="modal-add-client">
  <div class="modal">
    <span class="modal-close" onclick="closeModal('modal-add-client')">✕</span>
    <h3>ADD CLIENT</h3>
    <label>Name</label><input id="nc-name" placeholder="Full Name"/>
    <label>Age</label><input id="nc-age" type="number" placeholder="25"/>
    <label>Height (cm)</label><input id="nc-height" type="number" placeholder="175"/>
    <label>Weight (kg)</label><input id="nc-weight" type="number" placeholder="75"/>
    <label>Calories Target</label><input id="nc-calories" type="number" placeholder="2000"/>
    <label>Target Weight (kg)</label><input id="nc-tweight" type="number" placeholder="70"/>
    <label>Membership End (YYYY-MM-DD)</label><input id="nc-mend" placeholder="2025-12-31"/>
    <button class="btn btn-gold" onclick="saveClient()">SAVE CLIENT</button>
  </div>
</div>

<div class="modal-bg" id="modal-add-workout">
  <div class="modal">
    <span class="modal-close" onclick="closeModal('modal-add-workout')">✕</span>
    <h3>ADD WORKOUT</h3>
    <label>Date</label><input id="nw-date" type="date"/>
    <label>Type</label>
    <select id="nw-type">
      <option>Strength</option><option>Hypertrophy</option><option>Cardio</option><option>Mobility</option><option>HIIT</option>
    </select>
    <label>Duration (min)</label><input id="nw-dur" type="number" placeholder="60"/>
    <label>Notes</label><input id="nw-notes" placeholder="Optional notes"/>
    <button class="btn btn-gold" onclick="saveWorkout()">SAVE WORKOUT</button>
  </div>
</div>

<div class="modal-bg" id="modal-add-metric">
  <div class="modal">
    <span class="modal-close" onclick="closeModal('modal-add-metric')">✕</span>
    <h3>ADD METRIC</h3>
    <label>Date</label><input id="nm-date" type="date"/>
    <label>Weight (kg)</label><input id="nm-weight" type="number" step="0.1" placeholder="75.0"/>
    <label>Waist (cm)</label><input id="nm-waist" type="number" step="0.1" placeholder="85.0"/>
    <label>Body Fat %</label><input id="nm-bf" type="number" step="0.1" placeholder="18.0"/>
    <button class="btn btn-gold" onclick="saveMetric()">SAVE METRIC</button>
  </div>
</div>

<div class="modal-bg" id="modal-add-progress">
  <div class="modal">
    <span class="modal-close" onclick="closeModal('modal-add-progress')">✕</span>
    <h3>LOG WEEKLY PROGRESS</h3>
    <label>Week (e.g. Week 1)</label><input id="np-week" placeholder="Week 1"/>
    <label>Adherence %</label><input id="np-adh" type="number" min="0" max="100" placeholder="80"/>
    <button class="btn btn-gold" onclick="saveProgress()">SAVE</button>
  </div>
</div>

<div id="toast"></div>

<script>
let currentClient = null;

// ---- AUTH ----
async function doLogin() {
  const u = document.getElementById('login-user').value;
  const p = document.getElementById('login-pass').value;
  const res = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username:u, password:p})});
  const data = await res.json();
  if (data.success) {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('app-section').style.display = 'block';
    document.getElementById('nav-user').textContent = `${u} (${data.role})`;
    loadClientList();
    loadAllClients();
  } else {
    document.getElementById('login-err').textContent = 'Invalid credentials';
  }
}

// ---- CLIENTS ----
async function loadClientList() {
  const res = await fetch('/api/clients');
  const data = await res.json();
  const sel = document.getElementById('client-select');
  sel.innerHTML = '<option value="">-- Select --</option>';
  data.clients.forEach(c => sel.innerHTML += `<option value="${c}">${c}</option>`);
}

async function loadClient() {
  currentClient = document.getElementById('client-select').value;
  if (!currentClient) return;
  const res = await fetch(`/api/clients/${encodeURIComponent(currentClient)}`);
  const d = await res.json();
  document.getElementById('client-info-card').style.display = 'block';
  document.getElementById('client-info-body').innerHTML = `
    <div style="font-size:0.85rem;line-height:2;color:var(--muted);">
      <div><b style="color:var(--text);">Age:</b> ${d.age || '—'}</div>
      <div><b style="color:var(--text);">Weight:</b> ${d.weight || '—'} kg</div>
      <div><b style="color:var(--text);">Height:</b> ${d.height || '—'} cm</div>
      <div><b style="color:var(--text);">Membership:</b> <span class="badge ${d.membership_status==='Active'?'badge-green':'badge-red'}">${d.membership_status||'—'}</span></div>
    </div>`;
  loadSummary(d);
  loadWorkouts();
  loadMetrics();
  loadProgress();
}

function loadSummary(d) {
  document.getElementById('summary-empty').style.display = 'none';
  document.getElementById('summary-content').style.display = 'block';
  document.getElementById('stat-grid').innerHTML = `
    <div class="stat"><div class="val">${d.calories||'—'}</div><div class="lbl">Calorie Target</div></div>
    <div class="stat"><div class="val">${d.target_weight||'—'}</div><div class="lbl">Target Weight (kg)</div></div>
    <div class="stat"><div class="val">${d.weight||'—'}</div><div class="lbl">Current Weight (kg)</div></div>
    <div class="stat"><div class="val">${d.age||'—'}</div><div class="lbl">Age</div></div>`;
  document.getElementById('summary-program').textContent = d.program || 'No program assigned. Use Generate Program.';
}

async function loadAllClients() {
  const res = await fetch('/api/clients/all');
  const data = await res.json();
  const tbody = document.getElementById('all-clients-tbody');
  tbody.innerHTML = data.clients.map(c => `<tr>
    <td>${c.name}</td><td>${c.program||'—'}</td>
    <td><span class="badge ${c.membership_status==='Active'?'badge-green':'badge-red'}">${c.membership_status||'—'}</span></td>
    <td>${c.membership_end||'—'}</td></tr>`).join('');
}

function openAddClient() { openModal('modal-add-client'); }
async function saveClient() {
  const body = {
    name: document.getElementById('nc-name').value,
    age: document.getElementById('nc-age').value,
    height: document.getElementById('nc-height').value,
    weight: document.getElementById('nc-weight').value,
    calories: document.getElementById('nc-calories').value,
    target_weight: document.getElementById('nc-tweight').value,
    membership_end: document.getElementById('nc-mend').value
  };
  await fetch('/api/clients', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  closeModal('modal-add-client');
  loadClientList(); loadAllClients();
  toast('Client saved!');
}

// ---- PROGRAM ----
async function generateProgram() {
  if (!currentClient) return toast('Select a client first');
  const res = await fetch(`/api/clients/${encodeURIComponent(currentClient)}/generate-program`, {method:'POST'});
  const d = await res.json();
  toast(`Program: ${d.program}`);
  loadClient();
}

// ---- MEMBERSHIP ----
async function checkMembership() {
  if (!currentClient) return toast('Select a client first');
  const res = await fetch(`/api/clients/${encodeURIComponent(currentClient)}/membership`);
  const d = await res.json();
  alert(`Membership: ${d.membership_status}\nEnd Date: ${d.membership_end||'N/A'}`);
}

// ---- WORKOUTS ----
async function loadWorkouts() {
  if (!currentClient) return;
  const res = await fetch(`/api/clients/${encodeURIComponent(currentClient)}/workouts`);
  const data = await res.json();
  document.getElementById('workout-tbody').innerHTML = data.workouts.map(w =>
    `<tr><td>${w.date}</td><td>${w.workout_type}</td><td>${w.duration_min} min</td><td>${w.notes||'—'}</td></tr>`).join('');
}

function openAddWorkout() {
  if (!currentClient) return toast('Select a client first');
  document.getElementById('nw-date').value = new Date().toISOString().split('T')[0];
  openModal('modal-add-workout');
}
async function saveWorkout() {
  await fetch(`/api/clients/${encodeURIComponent(currentClient)}/workouts`, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({date:document.getElementById('nw-date').value, workout_type:document.getElementById('nw-type').value, duration_min:document.getElementById('nw-dur').value, notes:document.getElementById('nw-notes').value})
  });
  closeModal('modal-add-workout'); loadWorkouts(); toast('Workout logged!');
}

// ---- METRICS ----
async function loadMetrics() {
  if (!currentClient) return;
  const res = await fetch(`/api/clients/${encodeURIComponent(currentClient)}/metrics`);
  const data = await res.json();
  document.getElementById('metrics-tbody').innerHTML = data.metrics.map(m =>
    `<tr><td>${m.date}</td><td>${m.weight} kg</td><td>${m.waist} cm</td><td>${m.bodyfat}%</td></tr>`).join('');
}

function openAddMetric() {
  if (!currentClient) return toast('Select a client first');
  document.getElementById('nm-date').value = new Date().toISOString().split('T')[0];
  openModal('modal-add-metric');
}
async function saveMetric() {
  await fetch(`/api/clients/${encodeURIComponent(currentClient)}/metrics`, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({date:document.getElementById('nm-date').value, weight:document.getElementById('nm-weight').value, waist:document.getElementById('nm-waist').value, bodyfat:document.getElementById('nm-bf').value})
  });
  closeModal('modal-add-metric'); loadMetrics(); toast('Metric saved!');
}

// ---- PROGRESS ----
async function loadProgress() {
  if (!currentClient) return;
  const res = await fetch(`/api/clients/${encodeURIComponent(currentClient)}/progress`);
  const data = await res.json();
  document.getElementById('progress-tbody').innerHTML = data.progress.map(p => {
    const rating = p.adherence >= 80 ? '<span class="badge badge-green">Great</span>' : p.adherence >= 50 ? '<span class="badge" style="background:rgba(241,196,15,0.15);color:#f1c40f;">OK</span>' : '<span class="badge badge-red">Poor</span>';
    return `<tr><td>${p.week}</td><td>${p.adherence}%</td><td>${rating}</td></tr>`;
  }).join('');
}

function openAddProgress() {
  if (!currentClient) return toast('Select a client first');
  openModal('modal-add-progress');
}
async function saveProgress() {
  await fetch(`/api/clients/${encodeURIComponent(currentClient)}/progress`, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({week:document.getElementById('np-week').value, adherence:document.getElementById('np-adh').value})
  });
  closeModal('modal-add-progress'); loadProgress(); toast('Progress logged!');
}

// ---- UTILS ----
function switchTab(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  event.target.classList.add('active');
  if (name === 'clients') loadAllClients();
}
function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3000);
}
</script>
</body>
</html>
"""

# ---------- ROUTES ----------
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    row = conn.execute("SELECT role FROM users WHERE username=? AND password=?",
                       (data['username'], data['password'])).fetchone()
    conn.close()
    if row:
        return jsonify({'success': True, 'role': row['role']})
    return jsonify({'success': False}), 401

@app.route('/api/clients', methods=['GET'])
def get_clients():
    conn = get_db()
    rows = conn.execute("SELECT name FROM clients ORDER BY name").fetchall()
    conn.close()
    return jsonify({'clients': [r['name'] for r in rows]})

@app.route('/api/clients/all', methods=['GET'])
def get_all_clients():
    conn = get_db()
    rows = conn.execute("SELECT name, program, membership_status, membership_end FROM clients ORDER BY name").fetchall()
    conn.close()
    return jsonify({'clients': [dict(r) for r in rows]})

@app.route('/api/clients', methods=['POST'])
def add_client():
    data = request.json
    conn = get_db()
    conn.execute("""INSERT OR IGNORE INTO clients
        (name, age, height, weight, calories, target_weight, membership_status, membership_end)
        VALUES (?,?,?,?,?,?,'Active',?)""",
        (data.get('name'), data.get('age'), data.get('height'), data.get('weight'),
         data.get('calories'), data.get('target_weight'), data.get('membership_end')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/clients/<name>', methods=['GET'])
def get_client(name):
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))

@app.route('/api/clients/<name>/generate-program', methods=['POST'])
def generate_program(name):
    program_type = random.choice(list(PROGRAM_TEMPLATES.keys()))
    program = random.choice(PROGRAM_TEMPLATES[program_type])
    conn = get_db()
    conn.execute("UPDATE clients SET program=? WHERE name=?", (program, name))
    conn.commit()
    conn.close()
    return jsonify({'program': program, 'type': program_type})

@app.route('/api/clients/<name>/membership', methods=['GET'])
def get_membership(name):
    conn = get_db()
    row = conn.execute("SELECT membership_status, membership_end FROM clients WHERE name=?", (name,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))

@app.route('/api/clients/<name>/workouts', methods=['GET'])
def get_workouts(name):
    conn = get_db()
    rows = conn.execute("SELECT date, workout_type, duration_min, notes FROM workouts WHERE client_name=? ORDER BY date DESC", (name,)).fetchall()
    conn.close()
    return jsonify({'workouts': [dict(r) for r in rows]})

@app.route('/api/clients/<name>/workouts', methods=['POST'])
def add_workout(name):
    data = request.json
    conn = get_db()
    conn.execute("INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?,?,?,?,?)",
                 (name, data.get('date'), data.get('workout_type'), data.get('duration_min'), data.get('notes')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/clients/<name>/metrics', methods=['GET'])
def get_metrics(name):
    conn = get_db()
    rows = conn.execute("SELECT date, weight, waist, bodyfat FROM metrics WHERE client_name=? ORDER BY date DESC", (name,)).fetchall()
    conn.close()
    return jsonify({'metrics': [dict(r) for r in rows]})

@app.route('/api/clients/<name>/metrics', methods=['POST'])
def add_metric(name):
    data = request.json
    conn = get_db()
    conn.execute("INSERT INTO metrics (client_name, date, weight, waist, bodyfat) VALUES (?,?,?,?,?)",
                 (name, data.get('date'), data.get('weight'), data.get('waist'), data.get('bodyfat')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/clients/<name>/progress', methods=['GET'])
def get_progress(name):
    conn = get_db()
    rows = conn.execute("SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,)).fetchall()
    conn.close()
    return jsonify({'progress': [dict(r) for r in rows]})

@app.route('/api/clients/<name>/progress', methods=['POST'])
def add_progress(name):
    data = request.json
    conn = get_db()
    conn.execute("INSERT INTO progress (client_name, week, adherence) VALUES (?,?,?)",
                 (name, data.get('week'), data.get('adherence')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'version': '1.0'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)