"""Pruebas de integración: recorren la API completa (HTTP -> servicio -> repositorio)."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

DOC = {
    "title": "Enrollment guide",
    "content": "To enroll, the student must pay the tuition fee and hand in the student ID card "
               "at the admissions office before the first day of classes.",
    "tags": ["admissions"],
}


@pytest.fixture()
def client():
    """Cliente con app nueva (estado limpio) y LLM simulado en cada prueba."""
    return TestClient(create_app(Settings(llm_provider="fake")))


def test_crud_lifecycle(client):
    """Crear -> leer -> listar -> actualizar -> eliminar -> 404."""
    created = client.post("/documents", json=DOC)
    assert created.status_code == 201
    doc_id = created.json()["id"]

    assert client.get(f"/documents/{doc_id}").json()["title"] == DOC["title"]
    assert len(client.get("/documents").json()) == 1

    updated = client.put(f"/documents/{doc_id}", json={**DOC, "title": "Enrollment guide 2026"})
    assert updated.status_code == 200 and updated.json()["title"] == "Enrollment guide 2026"

    assert client.delete(f"/documents/{doc_id}").status_code == 204
    assert client.get(f"/documents/{doc_id}").status_code == 404


def test_error_handling(client):
    """422 por validación, 409 por título duplicado y 404 con formato uniforme."""
    invalid = client.post("/documents", json={"title": "ab", "content": "short"})
    assert invalid.status_code == 422
    body = invalid.json()
    assert body["error"] == "validation_error"
    assert {d["field"] for d in body["details"]} == {"title", "content"}

    assert client.post("/documents", json=DOC).status_code == 201
    assert client.post("/documents", json=DOC).status_code == 409

    missing = client.get("/documents/999")
    assert missing.status_code == 404
    assert missing.json() == {"status": 404, "error": "not_found",
                              "message": "Document 999 not found", "path": "/documents/999"}


@pytest.mark.parametrize("technique", ["zero_shot", "few_shot", "chain_of_thought"])
def test_rag_ask_with_each_technique(client, technique):
    """El RAG recupera la fuente correcta con cada técnica; sin contexto no llama al LLM."""
    client.post("/documents", json=DOC)

    response = client.post("/ai/ask", json={"question": "Where do I hand in my student ID card?",
                                            "technique": technique})
    body = response.json()
    assert response.status_code == 200
    assert body["technique"] == technique
    assert body["sources"][0]["title"] == DOC["title"]
    assert body["answer"].startswith("[FAKE-LLM]")

    unrelated = client.post("/ai/ask", json={"question": "What is the capital of France?"}).json()
    assert unrelated["sources"] == []
