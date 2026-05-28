"""
Flora Platform — Security Tests
================================
Testes para hashing de senhas, JWT, criptografia e licencas.
"""

import os
import pytest
import pytest_asyncio
from datetime import timedelta
from unittest.mock import MagicMock

from backend.config import Settings
from backend.core.security import (
    SecurityManager,
    TokenBlacklist,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    revoke_token,
    verify_password,
    get_password_hash,
    validate_password_strength,
    generate_api_key,
    sanitize_input,
    is_token_blacklisted,
    get_token_blacklist,
    TokenExpiredError,
    TokenInvalidError,
    TokenBlacklistedError,
)


# ─── Configuracao de teste ──────────────────────────────────
@pytest.fixture
def security_manager() -> SecurityManager:
    """Cria uma instancia limpa do SecurityManager para testes."""
    return SecurityManager()


@pytest.fixture
def blacklist() -> TokenBlacklist:
    """Cria uma blacklist limpa para testes."""
    bl = TokenBlacklist()
    bl.clear()
    return bl


# ─── Hash de Senhas ────────────────────────────────────────
class TestPasswordHashing:
    """Testes de hash e verificacao de senhas."""

    def test_password_hashing(self, security_manager: SecurityManager):
        """Senha e hash sao gerados corretamente."""
        password = "SecurePassword123!"
        hashed = security_manager.hash_password(password)
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_correct_password(self, security_manager: SecurityManager):
        """Senha correta e verificada com sucesso."""
        password = "SecurePassword123!"
        hashed = security_manager.hash_password(password)
        assert security_manager.verify_password(password, hashed) is True

    def test_verify_wrong_password(self, security_manager: SecurityManager):
        """Senha incorreta e rejeitada."""
        password = "SecurePassword123!"
        hashed = security_manager.hash_password(password)
        assert security_manager.verify_password("WrongPassword!", hashed) is False

    def test_hash_consistency(self, security_manager: SecurityManager):
        """Hashes da mesma senha sao diferentes (salt), mas ambos validam."""
        password = "SamePassword456!"
        hash1 = security_manager.hash_password(password)
        hash2 = security_manager.hash_password(password)
        assert hash1 != hash2  # Different salts
        assert security_manager.verify_password(password, hash1) is True
        assert security_manager.verify_password(password, hash2) is True

    def test_weak_password_rejected(self, security_manager: SecurityManager):
        """Senha muito curta e rejeitada pelo hash."""
        with pytest.raises(ValueError):
            security_manager.hash_password("123")

    def test_empty_password_rejected(self, security_manager: SecurityManager):
        """Senha vazia e rejeitada."""
        with pytest.raises(ValueError):
            security_manager.hash_password("")


# ─── JWT Tokens ────────────────────────────────────────────
class TestJWT:
    """Testes de criacao e validacao de tokens JWT."""

    def test_jwt_token_creation(self, security_manager: SecurityManager):
        """Token JWT e criado com sucesso."""
        token = security_manager.create_access_token("user-123", role="user")
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2  # JWT has 3 parts separated by dots

    def test_jwt_token_validation(self, security_manager: SecurityManager):
        """Token valido e decodificado corretamente."""
        token = security_manager.create_access_token("user-123", role="user")
        payload = security_manager.decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_jwt_token_tampering(self, security_manager: SecurityManager):
        """Token adulterado e rejeitado."""
        token = security_manager.create_access_token("user-123", role="user")
        parts = token.split(".")
        parts[1] = parts[1][::-1]  # Reverse the payload
        tampered = ".".join(parts)
        with pytest.raises((TokenExpiredError, TokenInvalidError)):
            security_manager.decode_token(tampered)

    def test_refresh_token_creation(self, security_manager: SecurityManager):
        """Refresh token e criado com tipo correto."""
        token = security_manager.create_refresh_token("user-123")
        payload = security_manager.decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["sub"] == "user-123"

    def test_expired_token(self, security_manager: SecurityManager):
        """Token expirado e rejeitado."""
        token = security_manager.create_access_token(
            "user-123", role="user", expire_delta=timedelta(seconds=-1)
        )
        with pytest.raises(TokenExpiredError):
            security_manager.decode_token(token)

    def test_create_token_pair(self, security_manager: SecurityManager):
        """Par de tokens (access + refresh) e criado corretamente."""
        pair = security_manager.create_token_pair("user-123", role="admin")
        assert "access_token" in pair
        assert "refresh_token" in pair

    def test_token_with_extra_claims(self, security_manager: SecurityManager):
        """Token com claims extras os inclui no payload."""
        token = security_manager.create_access_token(
            "user-123", role="user", extra_claims={"tenant_id": "tenant-456"}
        )
        payload = security_manager.decode_token(token)
        assert payload["tenant_id"] == "tenant-456"


# ─── Token Blacklist ────────────────────────────────────────
class TestTokenBlacklist:
    """Testes de blacklist de tokens."""

    def test_add_and_check(self, blacklist: TokenBlacklist):
        """Token adicionado a blacklist e detectado."""
        from datetime import datetime, timezone, timedelta
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        blacklist.add("jti-123", exp)
        assert blacklist.is_blacklisted("jti-123") is True

    def test_not_blacklisted(self, blacklist: TokenBlacklist):
        """Token nao adicionado nao e detectado."""
        assert blacklist.is_blacklisted("jti-999") is False

    def test_revoke_token_flow(self, security_manager: SecurityManager):
        """Fluxo completo: criar, revogar, verificar blacklist."""
        token = security_manager.create_access_token("user-123", role="user")
        payload = security_manager.decode_token(token)
        jti = payload.get("jti")
        assert jti is not None

        security_manager.revoke_token(token)
        assert is_token_blacklisted(jti) is True

    def test_validate_token_strength_strong(self, security_manager: SecurityManager):
        """Senha forte passa na validacao."""
        is_valid, errors = security_manager.validate_password_strength("Str0ng!Pass")
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_token_strength_weak(self, security_manager: SecurityManager):
        """Senha fraca falha na validacao."""
        is_valid, errors = security_manager.validate_password_strength("weak")
        assert is_valid is False
        assert len(errors) > 0


# ─── Convenience Functions ──────────────────────────────────
class TestModuleLevelFunctions:
    """Testes das funcoes de conveniencia de nivel de modulo."""

    def test_module_create_access_token(self):
        """create_access_token funciona como funcao de modulo."""
        token = create_access_token("user-123", role="admin")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_module_create_refresh_token(self):
        """create_refresh_token funciona como funcao de modulo."""
        token = create_refresh_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_module_verify_password(self):
        """verify_password funciona como funcao de modulo."""
        hashed = get_password_hash("Test123!")
        assert verify_password("Test123!", hashed) is True
        assert verify_password("Wrong!", hashed) is False

    def test_module_get_password_hash(self):
        """get_password_hash funciona como funcao de modulo."""
        hashed = get_password_hash("Test123!")
        assert isinstance(hashed, str)
        assert len(hashed) > 0


# ─── Criptografia ───────────────────────────────────────────
class TestEncryption:
    """Testes de criptografia AES-256."""

    def test_encrypt_decrypt_roundtrip(self):
        """Dados criptografados e descriptografados corretamente."""
        from backend.security.crypto import encrypt_field, decrypt_field

        original = "sensitive-data-for-testing-123"
        key = os.environ["ENCRYPTION_MASTER_KEY"]
        encrypted = encrypt_field(original, key)
        decrypted = decrypt_field(encrypted, key)
        assert decrypted == original

    def test_encrypt_produces_different_output(self):
        """Dados criptografados diferem do original."""
        from backend.security.crypto import encrypt_field

        original = "data-to-encrypt"
        key = os.environ["ENCRYPTION_MASTER_KEY"]
        encrypted = encrypt_field(original, key)
        assert encrypted != original.encode()

    def test_encrypt_with_different_keys(self):
        """Dados criptografados com chaves diferentes produzem resultados diferentes."""
        from backend.security.crypto import encrypt_field

        original = "test-data"
        key1 = "first-key-that-is-32-bytes-long!"
        key2 = "second-key-that-is-32-bytes-long"
        enc1 = encrypt_field(original, key1)
        enc2 = encrypt_field(original, key2)
        assert enc1 != enc2


# ─── Licencas ──────────────────────────────────────────────
class TestLicenseKeys:
    """Testes de geracao e validacao de chaves de licenca."""

    def test_license_key_generation(self):
        """Chave de licenca e gerada com formato correto."""
        from backend.security.crypto import generate_license_key

        key = generate_license_key()
        assert isinstance(key, str)
        assert len(key) > 0
        assert "FLORA" in key.upper() or "-" in key

    def test_license_key_uniqueness(self):
        """Chaves geradas sao unicas."""
        from backend.security.crypto import generate_license_key

        key1 = generate_license_key()
        key2 = generate_license_key()
        assert key1 != key2

    def test_license_key_length(self):
        """Chave de licenca tem comprimento minimo."""
        from backend.security.crypto import generate_license_key

        key = generate_license_key()
        assert len(key) >= 16


# ─── Settings e Configuracao ──────────────────────────────
class TestSettings:
    """Testes de configuracao da aplicacao."""

    def test_settings_load(self):
        """Configuracao carrega corretamente com variaveis de ambiente."""
        settings = Settings()
        assert settings.SECRET_KEY is not None
        assert settings.JWT_ALGORITHM == "HS256"

    def test_default_values(self):
        """Valores padrao estao corretos."""
        settings = Settings()
        assert settings.APP_NAME == "Flora Platform"
        assert settings.JWT_ALGORITHM == "HS256"


# ─── API Key Generation ────────────────────────────────────
class TestApiKey:
    """Testes de geracao de API keys."""

    def test_generate_api_key(self, security_manager: SecurityManager):
        """API key e gerada com sucesso."""
        key = security_manager.generate_api_key()
        assert isinstance(key, str)
        assert len(key) >= 32

    def test_api_key_uniqueness(self, security_manager: SecurityManager):
        """API keys geradas sao unicas."""
        key1 = security_manager.generate_api_key()
        key2 = security_manager.generate_api_key()
        assert key1 != key2


# ─── Input Sanitization ────────────────────────────────────
class TestSanitization:
    """Testes de sanitizacao de input."""

    def test_sanitize_html(self, security_manager: SecurityManager):
        """HTML malicioso e sanitizado."""
        malicious = '<script>alert("xss")</script>Hello'
        sanitized = security_manager.sanitize_html(malicious)
        assert "<script>" not in sanitized

    def test_sanitize_sql_injection(self, security_manager: SecurityManager):
        """Tentativa de SQL injection e sanitizada."""
        malicious = "SELECT * FROM users; DROP TABLE users"
        sanitized = security_manager.sanitize_sql_input(malicious)
        assert "SELECT" not in sanitized.upper() or sanitized == ""

    def test_sanitize_empty(self, security_manager: SecurityManager):
        """Input vazio e retornado como esta."""
        assert security_manager.sanitize_html("") == ""

    def test_sanitize_none(self, security_manager: SecurityManager):
        """Input None e retornado como esta."""
        assert security_manager.sanitize_html(None) is None
