"""Pruebas de integración: recorren la API completa (HTTP -> servicio -> repositorio)."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

DOC = {
    "title": "Guía de matrícula",
    "content": "Para matricularse el estudiante debe pagar la matrícula y entregar el carné "
               "en la oficina de admisiones antes del primer día de clases.",
    "tags": ["admisiones"],
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

    updated = client.put(f"/documents/{doc_id}", json={**DOC, "title": "Guía actualizada"})
    assert updated.status_code == 200 and updated.json()["title"] == "Guía actualizada"

    assert client.delete(f"/documents/{doc_id}").status_code == 204
    assert client.get(f"/documents/{doc_id}").status_code == 404


def test_error_handling(client):
    """422 por validación, 409 por título duplicado y 404 con formato uniforme."""
    invalid = client.post("/documents", json={"title": "ab", "content": "corto"})
    assert invalid.status_code == 422
    assert invalid.json()["error"] == "validation_error"

    assert client.post("/documents", json=DOC).status_code == 201
    assert client.post("/documents", json=DOC).status_code == 409

    missing = client.get("/documents/999")
    assert missing.status_code == 404
    assert set(missing.json()) >= {"status", "error", "message", "path"}


@pytest.mark.parametrize("technique", ["zero_shot", "few_shot", "chain_of_thought"])
def test_rag_ask_with_each_technique(client, technique):
    """El RAG recupera la fuente correcta con cada técnica; sin contexto no llama al LLM."""
    client.post("/documents", json=DOC)

    response = client.post("/ai/ask", json={"question": "¿Dónde entrego el carné?", "technique": technique})
    body = response.json()
    assert response.status_code == 200
    assert body["technique"] == technique
    assert body["sources"][0]["title"] == DOC["title"]
    assert body["answer"].startswith("[FAKE-LLM]")

    unrelated = client.post("/ai/ask", json={"question": "¿Cuál es la capital de Francia?"}).json()
    assert unrelated["sources"] == []
