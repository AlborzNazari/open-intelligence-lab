"""
tests/test_api_endpoints.py — v0.6.1

HTTP-level tests for all FastAPI routes via Starlette TestClient.
No live server, no ports, no race conditions.
Covers: root, health, /intelligence/entities, /intelligence/analyze/{id},
        /intelligence/graph/summary, /intelligence/graph/edges,
        /intelligence/entities/ids

v0.6.1 fix: version assertions now read from app.version instead of
hardcoded strings — bumping main.py never breaks this suite again.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# Single source of truth — pulled from FastAPI constructor in main.py.
# Never hardcode a version string in a test.
EXPECTED_VERSION = app.version


class TestRootAndHealth:
    def test_root_returns_200(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_root_has_status_ok(self):
        r = client.get("/")
        assert r.json()["status"] == "ok"

    def test_root_has_version(self):
        r = client.get("/")
        assert "version" in r.json()

    def test_root_version_matches_app(self):
        r = client.get("/")
        assert r.json()["version"] == EXPECTED_VERSION

    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_status_ok(self):
        r = client.get("/health")
        assert r.json()["status"] == "ok"

    def test_health_version_matches_app(self):
        # v0.6.1: was hardcoded "0.6.0" — now reads from app.version
        r = client.get("/health")
        assert r.json()["version"] == EXPECTED_VERSION

    def test_docs_accessible(self):
        r = client.get("/docs")
        assert r.status_code == 200

    def test_openapi_json_accessible(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200


class TestEntitiesEndpoint:
    def test_returns_200(self):
        r = client.get("/intelligence/entities")
        assert r.status_code == 200

    def test_response_has_required_shape(self):
        r = client.get("/intelligence/entities")
        data = r.json()
        for key in ("total", "offset", "limit", "entities"):
            assert key in data

    def test_entities_is_list(self):
        r = client.get("/intelligence/entities")
        assert isinstance(r.json()["entities"], list)

    def test_query_param_apt28(self):
        r = client.get("/intelligence/entities?query=APT28")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1

    def test_entity_type_filter_threat_actor(self):
        r = client.get("/intelligence/entities?entity_type=threat_actor")
        assert r.status_code == 200
        for e in r.json()["entities"]:
            assert e["type"] == "threat_actor"

    def test_min_risk_filter(self):
        r = client.get("/intelligence/entities?min_risk=0.9")
        assert r.status_code == 200
        for e in r.json()["entities"]:
            assert e["risk_score"] >= 0.9

    def test_limit_param(self):
        r = client.get("/intelligence/entities?limit=3")
        assert r.status_code == 200
        assert len(r.json()["entities"]) <= 3

    def test_no_match_returns_empty_list(self):
        r = client.get("/intelligence/entities?query=ZZZNONEXISTENTZZZ")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_invalid_entity_type_returns_422(self):
        r = client.get("/intelligence/entities?entity_type=invalid_type")
        assert r.status_code == 422

    def test_limit_above_max_returns_422(self):
        r = client.get("/intelligence/entities?limit=999")
        assert r.status_code == 422


class TestAnalyzeEndpoint:
    def test_known_entity_returns_200(self):
        r = client.get("/intelligence/analyze/TA-001")
        assert r.status_code == 200

    def test_response_has_entity_id(self):
        r = client.get("/intelligence/analyze/TA-001")
        assert r.json()["entity_id"] == "TA-001"

    def test_response_has_risk_score(self):
        r = client.get("/intelligence/analyze/TA-001")
        data = r.json()
        assert "risk_score" in data
        assert 0.0 <= data["risk_score"] <= 1.0

    def test_response_has_explanation(self):
        r = client.get("/intelligence/analyze/TA-001")
        assert "explanation" in r.json()
        assert isinstance(r.json()["explanation"], list)

    def test_malware_entity(self):
        r = client.get("/intelligence/analyze/MA-001")
        assert r.status_code == 200
        assert r.json()["type"] == "malware"

    def test_vulnerability_entity(self):
        r = client.get("/intelligence/analyze/VUL-001")
        assert r.status_code == 200

    def test_sector_entity(self):
        r = client.get("/intelligence/analyze/SECTOR-001")
        assert r.status_code == 200

    def test_unknown_entity_returns_404(self):
        r = client.get("/intelligence/analyze/NONEXISTENT-9999")
        assert r.status_code == 404

    def test_404_detail_mentions_entity_id(self):
        r = client.get("/intelligence/analyze/FAKE-000")
        assert "FAKE-000" in r.json()["detail"]


class TestGraphSummaryEndpoint:
    def test_returns_200(self):
        r = client.get("/intelligence/graph/summary")
        assert r.status_code == 200

    def test_has_all_required_keys(self):
        r = client.get("/intelligence/graph/summary")
        data = r.json()
        for key in ("node_count", "edge_count", "avg_risk_score", "max_risk_score", "min_risk_score"):
            assert key in data

    def test_node_count_is_positive_int(self):
        r = client.get("/intelligence/graph/summary")
        assert isinstance(r.json()["node_count"], int)
        assert r.json()["node_count"] > 0

    def test_edge_count_is_positive_int(self):
        r = client.get("/intelligence/graph/summary")
        assert r.json()["edge_count"] > 0


class TestGraphEdgesEndpoint:
    def test_returns_200(self):
        r = client.get("/intelligence/graph/edges")
        assert r.status_code == 200

    def test_has_edge_count_and_edges(self):
        r = client.get("/intelligence/graph/edges")
        data = r.json()
        assert "edge_count" in data
        assert "edges" in data

    def test_edge_count_matches_list_length(self):
        r = client.get("/intelligence/graph/edges")
        data = r.json()
        assert data["edge_count"] == len(data["edges"])

    def test_each_edge_has_required_fields(self):
        r = client.get("/intelligence/graph/edges")
        for edge in r.json()["edges"]:
            for field in ("source", "target", "relation_type", "confidence"):
                assert field in edge


class TestEntityIdsEndpoint:
    def test_returns_200(self):
        r = client.get("/intelligence/entities/ids")
        assert r.status_code == 200

    def test_has_count_and_ids(self):
        r = client.get("/intelligence/entities/ids")
        data = r.json()
        assert "count" in data
        assert "entity_ids" in data

    def test_count_matches_list_length(self):
        r = client.get("/intelligence/entities/ids")
        data = r.json()
        assert data["count"] == len(data["entity_ids"])

    def test_ta001_in_ids(self):
        r = client.get("/intelligence/entities/ids")
        assert "TA-001" in r.json()["entity_ids"]

    def test_all_ids_are_strings(self):
        r = client.get("/intelligence/entities/ids")
        for eid in r.json()["entity_ids"]:
            assert isinstance(eid, str)
