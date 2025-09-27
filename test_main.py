from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "projeto" in data
    assert data["projeto"] == "Steam Requirements API com IA"

def test_listar_dados():
    response = client.get("/dados?skip=0&limit=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) <= 5

def test_buscar_por_id_existente():
    response = client.get("/dados/10")  
    assert response.status_code == 200
    data = response.json()
    assert "item" in data or "erro" in data

def test_instrucoes_para_id():
    response = client.get("/como-encontrar-id")
    assert response.status_code == 200
    data = response.json()
    assert "mensagem" in data

def test_verificar_especs_ia_jogo_inexistente():
    payload = {
        "steam_appid": 999999999,
        "sistema_operacional": "Windows 10",
        "processador": "Intel Core i5",
        "memoria_ram_gb": 8,
        "placa_de_video": "NVIDIA GTX 1050"
    }
    response = client.post("/verificar-especs-ia", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "erro" in data
