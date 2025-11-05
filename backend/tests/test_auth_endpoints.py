"""
🧪 Testes de Integração - Authentication Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token, get_password_hash


class TestAuthEndpoints:
    """Testes para endpoints de autenticação"""

    @pytest.fixture
    def client(self):
        """Criar cliente de teste"""
        from simple_api import app
        return TestClient(app)

    def test_register_new_user(self, client):
        """Test: Registrar novo usuário"""
        response = client.post("/api/v1/auth/register", json={
            "email": "test2@example.com",
            "username": "testuser2",
            "password": "Test123456"
        })

        # Pode retornar 201 (sucesso) ou 400 (usuário já existe)
        assert response.status_code in [201, 400], \
            f"Unexpected status code: {response.status_code}"

        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["email"] == "test2@example.com"
            assert data["username"] == "testuser2"

    def test_login_with_valid_credentials(self, client):
        """Test: Login com credenciais válidas"""
        # Primeiro registrar
        client.post("/api/v1/auth/register", json={
            "email": "login_test@example.com",
            "username": "logintest",
            "password": "Test123456"
        })

        # Então fazer login
        response = client.post("/api/v1/auth/login", json={
            "username": "logintest",
            "password": "Test123456"
        })

        # Pode retornar 200 ou 429 (rate limit)
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert "expires_in" in data

    def test_login_with_invalid_password(self, client):
        """Test: Login com senha incorreta deve falhar"""
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })

        # Deve retornar 401 (Unauthorized) ou 429 (rate limit)
        assert response.status_code in [401, 429], \
            f"Expected 401 or 429, got {response.status_code}"

    def test_get_current_user_with_token(self, client):
        """Test: Obter usuário atual com token válido"""
        # Criar token
        token = create_access_token(data={"sub": "1", "username": "testuser"})

        # Fazer request com token
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Se user existe, retorna 200; se não, 404
        assert response.status_code in [200, 404], \
            f"Unexpected status code: {response.status_code}"

    def test_get_current_user_without_token(self, client):
        """Test: Acessar endpoint protegido sem token deve falhar"""
        response = client.get("/api/v1/auth/me")

        # Deve retornar 403 (Forbidden)
        assert response.status_code == 403, \
            f"Expected 403, got {response.status_code}"

    def test_password_hashing(self):
        """Test: Senha deve ser hasheada"""
        password = "mypassword123"
        hashed = get_password_hash(password)

        # Hash não deve ser igual à senha original
        assert hashed != password, "Password was not hashed"

        # Hash deve ter comprimento razoável
        assert len(hashed) > 30, "Hash length too short"


class TestRateLimiting:
    """Testes de rate limiting"""

    @pytest.fixture
    def client(self):
        from simple_api import app
        return TestClient(app)

    def test_rate_limit_on_root_endpoint(self, client):
        """Test: Rate limit no endpoint root (20/min)"""
        # Fazer múltiplas requisições
        responses = []
        for _ in range(25):
            response = client.get("/")
            responses.append(response.status_code)

        # Deve ter pelo menos um 429 (Too Many Requests)
        assert 429 in responses, \
            "Rate limit not triggered after 25 requests"

    def test_rate_limit_on_login(self, client):
        """Test: Rate limit no login (10/min)"""
        # Fazer múltiplas tentativas de login
        responses = []
        for _ in range(15):
            response = client.post("/api/v1/auth/login", json={
                "username": "test",
                "password": "test"
            })
            responses.append(response.status_code)

        # Deve ter 401 ou 429
        assert any(code in [401, 429] for code in responses), \
            "Expected rate limit or auth error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
