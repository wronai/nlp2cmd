# E2E Tests for NLP2CMD Service Mode

This directory contains end-to-end tests for the NLP2CMD service mode implementation.

## 📋 Test Coverage

### ✅ Core Functionality Tests
- **Service Startup** - Verify service starts correctly
- **Health Check** - Test `/health` endpoint
- **Service Info** - Test root `/` endpoint with configuration
- **Basic Query Processing** - Test natural language to command conversion
- **Polish Language Support** - Test Polish queries (znajdź, uruchom, pokaż)
- **Query with Explanation** - Test explanation functionality
- **Configuration Management** - Test config get/update endpoints
- **Error Handling** - Test invalid requests and error responses
- **Concurrent Requests** - Test multiple simultaneous requests

### 🔧 Technical Tests
- **Service Lifecycle** - Start/stop/restart scenarios
- **Configuration Persistence** - .env file management
- **API Validation** - Pydantic model validation
- **Performance** - Response time and concurrency
- **Integration** - Full workflow testing

## 🚀 Running Tests

### Quick Start (Simple Runner)

```bash
# Run all E2E tests with default settings
python3 run_e2e_tests.py

# Run with custom host/port
python3 run_e2e_tests.py --host 127.0.0.1 --port 8002

# Verbose output
python3 run_e2e_tests.py --verbose
```

### With pytest

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run only service tests
pytest tests/e2e/ -m service

# Run with coverage
pytest tests/e2e/ --cov=nlp2cmd.service --cov-report=html

# Run specific test file
pytest tests/e2e/test_service_e2e.py -v
```

## 📁 File Structure

```
tests/e2e/
├── conftest.py              # Pytest configuration and fixtures
├── test_service_e2e.py      # Main E2E test suite
└── README.md               # This file

run_e2e_tests.py             # Simple test runner (no pytest needed)
pytest.ini                  # Pytest configuration
```

## 🧪 Test Categories

### Service Tests (`@pytest.mark.service`)
Tests specifically for the HTTP API service mode:
- Service lifecycle management
- API endpoint functionality
- Configuration management
- Error handling

### Integration Tests (`@pytest.mark.integration`)
Tests that verify integration between components:
- Full workflow testing
- Multi-step scenarios
- Real-world usage patterns

### E2E Tests (`@pytest.mark.e2e`)
Complete end-to-end scenarios:
- Service startup to query processing
- Polish language workflows
- Configuration persistence

## 📊 Test Results Example

```
🎯 Starting E2E Tests for NLP2CMD Service Mode
==================================================
🧪 Running test: Health Check
✅ Health Check: PASSED

🧪 Running test: Service Info
✅ Service Info: PASSED

🧪 Running test: Basic Query
✅ Basic Query: PASSED

🧪 Running test: Polish Queries
✅ Polish Queries: PASSED

🧪 Running test: Query with Explanation
✅ Query with Explanation: PASSED

🧪 Running test: Config Management
✅ Config Management: PASSED

🧪 Running test: Error Handling
✅ Error Handling: PASSED

🧪 Running test: Concurrent Requests
✅ Concurrent Requests: PASSED

==================================================
📊 Test Results: 8/8 passed
🎉 All tests passed!
```

## 🔍 Test Details

### Health Check Test
- **Endpoint**: `GET /health`
- **Expected**: `{"status": "healthy", "service": "nlp2cmd"}`
- **Purpose**: Verify service is running and responsive

### Service Info Test
- **Endpoint**: `GET /`
- **Expected**: Service info with configuration
- **Purpose**: Verify service metadata and config exposure

### Basic Query Test
- **Endpoint**: `POST /query`
- **Payload**: `{"query": "list files", "dsl": "shell"}`
- **Expected**: Successful command generation
- **Purpose**: Verify core NLP functionality

### Polish Queries Test
- **Queries**: Polish language inputs
- **Examples**: "znajdź pliki większe niż 100MB"
- **Purpose**: Verify Polish language support

### Configuration Management Test
- **Endpoints**: `GET /config`, `POST /config`
- **Purpose**: Verify runtime configuration updates

### Error Handling Test
- **Scenarios**: Invalid JSON, missing fields, bad data
- **Purpose**: Verify graceful error handling

### Concurrent Requests Test
- **Method**: 5 simultaneous requests
- **Purpose**: Verify concurrency handling

## 🛠️ Test Implementation

### Service Manager Class
```python
class NLP2CMDServiceManager:
    """Manages NLP2CMD service lifecycle for testing."""
    
    def start_service(self) -> subprocess.Popen
    def stop_service(self)
    def wait_for_ready(self, timeout: int = 30) -> bool
    def cleanup(self)
```

### Test Fixtures
```python
@pytest.fixture(scope="function")
def service_manager():
    """Fixture for managing service lifecycle."""
    
@pytest.fixture(scope="function") 
def running_service(service_manager):
    """Fixture that provides a running service."""
```

## 🔧 Configuration

### Test Environment
- **Host**: 127.0.0.1 (localhost)
- **Port**: 8001 (default, configurable)
- **Timeout**: 30 seconds startup
- **Environment**: Test .env file created automatically

### Pytest Configuration
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
markers =
    e2e: End-to-end tests
    service: Service mode tests
    integration: Integration tests
```

## 📝 Adding New Tests

### 1. Simple Test (using runner)
```python
def test_new_feature(self) -> bool:
    """Test new feature."""
    response = requests.get(f"{self.base_url}/new-endpoint")
    return response.status_code == 200
```

### 2. Pytest Test
```python
@pytest.mark.service
def test_new_feature(running_service):
    """Test new feature with pytest."""
    response = requests.get(f"{running_service.base_url}/new-endpoint")
    assert response.status_code == 200
```

### 3. Integration Test
```python
@pytest.mark.integration
def test_complete_workflow(running_service):
    """Test complete workflow."""
    # Step 1: Configure
    # Step 2: Process queries  
    # Step 3: Verify results
```

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check dependencies
pip install fastapi uvicorn

# Check port availability
netstat -tlnp | grep :8001

# Enable debug mode
python3 run_e2e_tests.py --verbose
```

### Tests Fail
```bash
# Check service logs
python3 run_e2e_tests.py --verbose

# Run individual test
pytest tests/e2e/test_service_e2e.py::TestServiceE2E::test_health_check -v

# Check dependencies
pip install -r requirements.txt
```

### Port Conflicts
```bash
# Use different port
python3 run_e2e_tests.py --port 8002

# Or set environment variable
export NLP2CMD_TEST_PORT=8002
python3 run_e2e_tests.py
```

## 📈 Performance

### Test Duration
- **Service Startup**: ~2-5 seconds
- **All Tests**: ~15-20 seconds
- **Individual Tests**: ~0.5-2 seconds each

### Resource Usage
- **Memory**: ~50-100MB during tests
- **CPU**: Minimal during test execution
- **Network**: Localhost requests only

## 🎯 Best Practices

1. **Isolation**: Each test gets a clean service instance
2. **Cleanup**: Automatic service shutdown after tests
3. **Timeouts**: Reasonable timeouts for all operations
4. **Error Messages**: Clear failure descriptions
5. **Idempotency**: Tests can be run multiple times
6. **Parallel Safe**: Tests don't interfere with each other

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run E2E tests
        run: python3 run_e2e_tests.py
```

### Docker Testing
```bash
# Build and test in Docker
docker build -t nlp2cmd-test .
docker run --rm nlp2cmd-test python3 run_e2e_tests.py
```

## 📚 Related Documentation

- **[Service Mode Guide](../docs/SERVICE_MODE.md)** - Service mode documentation
- **[API Reference](../docs/api/README.md)** - API endpoint documentation
- **[Installation Guide](../INSTALLATION.md)** - Setup instructions
- **[Contributing Guide](../CONTRIBUTING.md)** - Development guidelines
