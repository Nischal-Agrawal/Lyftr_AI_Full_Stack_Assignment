import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Set test environment variables before importing app
temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temp_db_path = temp_db.name
temp_db.close()

os.environ["DATABASE_URL"] = f"sqlite:///{temp_db_path}"
os.environ["LLM_API_KEYS"] = "test-key-alpha,test-key-beta"
os.environ["LLM_MODEL"] = "gemini/gemini-2.0-flash"
os.environ["ENABLE_FAILURE_SIMULATION"] = "true"
os.environ["LITELLM_CACHE_TYPE"] = "local"

from app.main import app
from app.config import settings
from app.database import init_db
import litellm
from litellm.caching import Cache


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()
    yield
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass


@pytest.fixture(autouse=True)
def reset_cache_per_test():
    litellm.cache = Cache(type="local")
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
