import os
from pathlib import Path

os.environ["SCANPRO_DATA_ROOT"] = "/tmp/scanpro-test"
os.environ["SCANPRO_DATABASE_URL"] = "sqlite:////tmp/scanpro-test/scanpro-test.db"

from fastapi.testclient import TestClient
from scanpro.main import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "1.0.0-dev",
        "schema_version": 1,
    }
