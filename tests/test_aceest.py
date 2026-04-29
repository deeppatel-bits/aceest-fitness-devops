"""
Pytest test suite for ACEest Fitness & Gym Flask Application
"""
import pytest
import json
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from aceest_fitness import app, init_db, DB_NAME

TEST_DB = "test_aceest.db"

# ---------- FIXTURES ----------

@pytest.fixture
def client():
    """Create a test Flask client with a fresh test database."""
    app.config['TESTING'] = True
    
    # Use a separate test database
    import aceest_fitness as af
    af.DB_NAME = TEST_DB
    
    init_db()
    
    with app.test_client() as client:
        yield client
    
    # Cleanup test DB after tests
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


# ---------- HEALTH CHECK ----------

class TestHealth:
    def test_health_endpoint_returns_200(self, client):
        res = client.get('/health')
        assert res.status_code == 200

    def test_health_endpoint_returns_healthy_status(self, client):
        res = client.get('/health')
        data = json.loads(res.data)
        assert data['status'] == 'healthy'

    def test_health_endpoint_returns_version(self, client):
        res = client.get('/health')
        data = json.loads(res.data)
        assert 'version' in data


# ---------- HOME ROUTE ----------

class TestHome:
    def test_home_returns_200(self, client):
        res = client.get('/')
        assert res.status_code == 200

    def test_home_returns_html(self, client):
        res = client.get('/')
        assert b'ACEest' in res.data


# ---------- AUTH ----------

class TestLogin:
    def test_valid_login(self, client):
        res = client.post('/api/login',
            data=json.dumps({'username': 'admin', 'password': 'admin'}),
            content_type='application/json')
        data = json.loads(res.data)
        assert res.status_code == 200
        assert data['success'] is True

    def test_valid_login_returns_role(self, client):
        res = client.post('/api/login',
            data=json.dumps({'username': 'admin', 'password': 'admin'}),
            content_type='application/json')
        data = json.loads(res.data)
        assert 'role' in data
        assert data['role'] == 'Admin'

    def test_invalid_login_wrong_password(self, client):
        res = client.post('/api/login',
            data=json.dumps({'username': 'admin', 'password': 'wrongpass'}),
            content_type='application/json')
        assert res.status_code == 401

    def test_invalid_login_wrong_user(self, client):
        res = client.post('/api/login',
            data=json.dumps({'username': 'nobody', 'password': 'admin'}),
            content_type='application/json')
        data = json.loads(res.data)
        assert data['success'] is False

    def test_invalid_login_empty_credentials(self, client):
        res = client.post('/api/login',
            data=json.dumps({'username': '', 'password': ''}),
            content_type='application/json')
        assert res.status_code == 401


# ---------- CLIENTS ----------

class TestClients:
    def _add_client(self, client, name="Test User"):
        return client.post('/api/clients',
            data=json.dumps({'name': name, 'age': 25, 'height': 175,
                             'weight': 75, 'calories': 2000,
                             'target_weight': 70, 'membership_end': '2025-12-31'}),
            content_type='application/json')

    def test_get_clients_empty(self, client):
        res = client.get('/api/clients')
        data = json.loads(res.data)
        assert res.status_code == 200
        assert 'clients' in data
        assert isinstance(data['clients'], list)

    def test_add_client_success(self, client):
        res = self._add_client(client)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['success'] is True

    def test_add_client_appears_in_list(self, client):
        self._add_client(client, "John Doe")
        res = client.get('/api/clients')
        data = json.loads(res.data)
        assert "John Doe" in data['clients']

    def test_add_duplicate_client_ignored(self, client):
        self._add_client(client, "Duplicate")
        res = self._add_client(client, "Duplicate")
        assert res.status_code == 200  # INSERT OR IGNORE — no crash

    def test_get_single_client(self, client):
        self._add_client(client, "Jane Smith")
        res = client.get('/api/clients/Jane Smith')
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['name'] == 'Jane Smith'

    def test_get_single_client_fields(self, client):
        self._add_client(client, "Field Test")
        res = client.get('/api/clients/Field Test')
        data = json.loads(res.data)
        assert 'age' in data
        assert 'weight' in data
        assert 'membership_status' in data

    def test_get_nonexistent_client_returns_404(self, client):
        res = client.get('/api/clients/Ghost User')
        assert res.status_code == 404

    def test_get_all_clients(self, client):
        self._add_client(client, "Client A")
        self._add_client(client, "Client B")
        res = client.get('/api/clients/all')
        data = json.loads(res.data)
        assert len(data['clients']) >= 2

    def test_new_client_membership_active(self, client):
        self._add_client(client, "Active Member")
        res = client.get('/api/clients/Active Member')
        data = json.loads(res.data)
        assert data['membership_status'] == 'Active'


# ---------- PROGRAM GENERATOR ----------

class TestProgramGenerator:
    def _add_client(self, client, name="Prog Client"):
        client.post('/api/clients',
            data=json.dumps({'name': name}),
            content_type='application/json')

    def test_generate_program_success(self, client):
        self._add_client(client)
        res = client.post('/api/clients/Prog Client/generate-program')
        assert res.status_code == 200

    def test_generate_program_returns_program(self, client):
        self._add_client(client)
        res = client.post('/api/clients/Prog Client/generate-program')
        data = json.loads(res.data)
        assert 'program' in data
        assert len(data['program']) > 0

    def test_generate_program_returns_type(self, client):
        self._add_client(client)
        res = client.post('/api/clients/Prog Client/generate-program')
        data = json.loads(res.data)
        assert data['type'] in ['Fat Loss', 'Muscle Gain', 'Beginner']

    def test_generate_program_updates_client(self, client):
        self._add_client(client, "Program Update")
        client.post('/api/clients/Program Update/generate-program')
        res = client.get('/api/clients/Program Update')
        data = json.loads(res.data)
        assert data['program'] is not None


# ---------- MEMBERSHIP ----------

class TestMembership:
    def _add_client(self, client, name="Member"):
        client.post('/api/clients',
            data=json.dumps({'name': name, 'membership_end': '2025-12-31'}),
            content_type='application/json')

    def test_get_membership_status(self, client):
        self._add_client(client)
        res = client.get('/api/clients/Member/membership')
        assert res.status_code == 200

    def test_get_membership_fields(self, client):
        self._add_client(client)
        res = client.get('/api/clients/Member/membership')
        data = json.loads(res.data)
        assert 'membership_status' in data
        assert 'membership_end' in data

    def test_membership_nonexistent_client(self, client):
        res = client.get('/api/clients/Ghost/membership')
        assert res.status_code == 404


# ---------- WORKOUTS ----------

class TestWorkouts:
    def setup_client(self, client, name="Workout Client"):
        client.post('/api/clients',
            data=json.dumps({'name': name}),
            content_type='application/json')

    def _add_workout(self, client, name="Workout Client"):
        return client.post(f'/api/clients/{name}/workouts',
            data=json.dumps({'date': '2025-01-15', 'workout_type': 'Strength',
                             'duration_min': 60, 'notes': 'Felt strong'}),
            content_type='application/json')

    def test_get_workouts_empty(self, client):
        self.setup_client(client)
        res = client.get('/api/clients/Workout Client/workouts')
        data = json.loads(res.data)
        assert data['workouts'] == []

    def test_add_workout_success(self, client):
        self.setup_client(client)
        res = self._add_workout(client)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['success'] is True

    def test_workout_appears_in_list(self, client):
        self.setup_client(client)
        self._add_workout(client)
        res = client.get('/api/clients/Workout Client/workouts')
        data = json.loads(res.data)
        assert len(data['workouts']) == 1
        assert data['workouts'][0]['workout_type'] == 'Strength'

    def test_workout_fields_present(self, client):
        self.setup_client(client)
        self._add_workout(client)
        res = client.get('/api/clients/Workout Client/workouts')
        w = json.loads(res.data)['workouts'][0]
        assert 'date' in w
        assert 'workout_type' in w
        assert 'duration_min' in w
        assert 'notes' in w

    def test_multiple_workouts(self, client):
        self.setup_client(client)
        self._add_workout(client)
        self._add_workout(client)
        res = client.get('/api/clients/Workout Client/workouts')
        data = json.loads(res.data)
        assert len(data['workouts']) == 2


# ---------- METRICS ----------

class TestMetrics:
    def setup_client(self, client, name="Metrics Client"):
        client.post('/api/clients',
            data=json.dumps({'name': name}),
            content_type='application/json')

    def _add_metric(self, client, name="Metrics Client"):
        return client.post(f'/api/clients/{name}/metrics',
            data=json.dumps({'date': '2025-01-15', 'weight': 75.5,
                             'waist': 85.0, 'bodyfat': 18.5}),
            content_type='application/json')

    def test_get_metrics_empty(self, client):
        self.setup_client(client)
        res = client.get('/api/clients/Metrics Client/metrics')
        data = json.loads(res.data)
        assert data['metrics'] == []

    def test_add_metric_success(self, client):
        self.setup_client(client)
        res = self._add_metric(client)
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['success'] is True

    def test_metric_appears_in_list(self, client):
        self.setup_client(client)
        self._add_metric(client)
        res = client.get('/api/clients/Metrics Client/metrics')
        data = json.loads(res.data)
        assert len(data['metrics']) == 1

    def test_metric_values_correct(self, client):
        self.setup_client(client)
        self._add_metric(client)
        m = json.loads(client.get('/api/clients/Metrics Client/metrics').data)['metrics'][0]
        assert float(m['weight']) == 75.5
        assert float(m['waist']) == 85.0
        assert float(m['bodyfat']) == 18.5


# ---------- PROGRESS ----------

class TestProgress:
    def setup_client(self, client, name="Progress Client"):
        client.post('/api/clients',
            data=json.dumps({'name': name}),
            content_type='application/json')

    def _add_progress(self, client, name="Progress Client", week="Week 1", adherence=80):
        return client.post(f'/api/clients/{name}/progress',
            data=json.dumps({'week': week, 'adherence': adherence}),
            content_type='application/json')

    def test_get_progress_empty(self, client):
        self.setup_client(client)
        res = client.get('/api/clients/Progress Client/progress')
        data = json.loads(res.data)
        assert data['progress'] == []

    def test_add_progress_success(self, client):
        self.setup_client(client)
        res = self._add_progress(client)
        assert res.status_code == 200

    def test_progress_appears_in_list(self, client):
        self.setup_client(client)
        self._add_progress(client)
        res = client.get('/api/clients/Progress Client/progress')
        data = json.loads(res.data)
        assert len(data['progress']) == 1
        assert data['progress'][0]['week'] == 'Week 1'
        assert data['progress'][0]['adherence'] == 80

    def test_multiple_weeks_progress(self, client):
        self.setup_client(client)
        self._add_progress(client, week="Week 1", adherence=70)
        self._add_progress(client, week="Week 2", adherence=85)
        res = client.get('/api/clients/Progress Client/progress')
        data = json.loads(res.data)
        assert len(data['progress']) == 2