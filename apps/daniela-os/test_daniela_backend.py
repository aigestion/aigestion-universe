import os

import pytest
from daniela_brain_system import MEMORY_FILE, TASKS_FILE, app, cargar_json, guardar_json


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup():
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
    if os.path.exists(TASKS_FILE):
        os.remove(TASKS_FILE)
    yield
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
    if os.path.exists(TASKS_FILE):
        os.remove(TASKS_FILE)


# --- PRUEBAS UNITARIAS ---
def test_cargar_y_guardar_json():
    test_data = ["Tarea 1", "Tarea 2"]
    test_file = "test_temp.json"
    guardar_json(test_file, test_data)
    loaded = cargar_json(test_file, [])
    assert loaded == test_data
    if os.path.exists(test_file):
        os.remove(test_file)


def test_home_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"DANIELA OS" in response.data


def test_gestionar_tareas_endpoint(client):
    response = client.get("/tareas")
    assert response.status_code == 200
    assert response.get_json() == []

    response = client.post("/tareas", json={"tarea": "Revisar perímetro"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert "Revisar perímetro" in data["tareas"]


def test_borrar_tarea_endpoint(client):
    client.post("/tareas", json={"tarea": "Tarea a eliminar"})
    response = client.post("/tareas/borrar", json={"index": 0})
    assert response.status_code == 200
    assert response.get_json()["tareas"] == []

    response_err = client.post("/tareas/borrar", json={"index": 99})
    assert response_err.status_code == 400


def test_cambiar_personalidad_endpoint(client):
    response = client.post("/personalidad", json={"modo": "tactica"})
    assert response.status_code == 200
    assert response.get_json()["modo"] == "tactica"

    response_err = client.post("/personalidad", json={"modo": "modo_inexistente"})
    assert response_err.status_code == 400


def test_limpiar_memoria_endpoint(client):
    response = client.post("/limpiar_memoria")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_chat_endpoint_validacion(client):
    response = client.post("/chat", json={"prompt": ""})
    assert response.status_code == 400

    response_valid = client.post("/chat", json={"prompt": "Hola Daniela"})
    assert response_valid.status_code == 200
    assert "respuesta" in response_valid.get_json()
