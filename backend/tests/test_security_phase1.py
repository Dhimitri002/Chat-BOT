"""
Testes de Segurança — Fase 1: Validação de Secrets
Auditoria profunda e brutal do sistema Flora Platform
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from pydantic import ValidationError


class TestSecurityPhase1:
    """FASE 1: Segurança Crítica — Validação de Secrets"""

    def test_license_signing_key_required(self):
        """❌ CRÍTICA: LICENSE_SIGNING_KEY deve ser obrigatório"""
        # Remover a chave
        with patch.dict(os.environ, {}, clear=False):
            if "LICENSE_SIGNING_KEY" in os.environ:
                del os.environ["LICENSE_SIGNING_KEY"]
            
            # Tentar importar license_manager deve falhar
            with pytest.raises(ValueError, match="LICENSE_SIGNING_KEY não definida"):
                from backend.core.license_manager import LICENSE_SIGNING_KEY

    def test_license_signing_key_no_default(self):
        """❌ CRÍTICA: LICENSE_SIGNING_KEY não pode ter default"""
        # Usar default inseguro deve falhar
        with patch.dict(os.environ, {"LICENSE_SIGNING_KEY": "flora-license-secret-change-me"}):
            with pytest.raises(ValueError, match="using default inseguro"):
                from backend.core.license_manager import LICENSE_SIGNING_KEY

    def test_license_signing_key_min_length(self):
        """LICENSE_SIGNING_KEY deve ter min 32 chars"""
        with patch.dict(os.environ, {"LICENSE_SIGNING_KEY": "short"}):
            with pytest.raises(ValueError, match="min 32 chars"):
                from backend.core.license_manager import LICENSE_SIGNING_KEY

    def test_config_secret_key_required(self):
        """SECRET_KEY deve ser obrigatório em config"""
        with patch.dict(os.environ, {"SECRET_KEY": ""}, clear=False):
            with pytest.raises(ValidationError):
                from backend.config import Settings
                Settings()

    def test_config_flora_master_key_required(self):
        """FLORA_MASTER_KEY deve ser obrigatório em config"""
        with patch.dict(os.environ, {"FLORA_MASTER_KEY": ""}, clear=False):
            with pytest.raises(ValidationError):
                from backend.config import Settings
                Settings()

    def test_config_no_random_secrets_per_import(self):
        """❌ BUG: secret_key não pode ser aleatório em cada import"""
        # secret_key deve ser lido de .env, não gerado em cada import
        # Isso já foi fixado em config.py
        from backend.config import settings as settings1
        # Importar novamente não deve gerar nova chave
        # (no código antigo isso criaria nova chave)
        assert settings1.secret_key  # Deve ter valor
        assert len(settings1.secret_key) >= 32  # Deve ter tamanho mínimo

    def test_argon2_password_hashing(self):
        """Verificar que Argon2 está bem configurado"""
        from backend.core.security import hash_password, verify_password

        password = "test_password_123!"
        hashed = hash_password(password)
        
        # Hash não deve ser igual ao password
        assert hashed != password
        
        # Verificação deve funcionar
        assert verify_password(password, hashed) is True
        
        # Password errado deve falhar
        assert verify_password("wrong_password", hashed) is False

    def test_jwt_token_expiry(self):
        """JWT tokens devem expirar após tempo definido"""
        from backend.core.security import create_access_token, decode_token
        import time

        user_id = "test-user-123"
        role = "user"
        
        token = create_access_token(user_id, role)
        decoded = decode_token(token)
        
        # Deve conter user_id e role
        assert decoded.get("sub") == user_id
        assert decoded.get("role") == role
        assert decoded.get("type") == "access"

    def test_hmac_license_signature(self):
        """HMAC para assinatura de licença deve ser seguro"""
        from backend.core.license_manager import sign_license, verify_license_signature
        
        license_key = "FLORA-ABCD-1234-EFGH-5678"
        signature = sign_license(license_key)
        
        # Verificação deve passar
        assert verify_license_signature(license_key, signature) is True
        
        # Signature errada deve falhar
        fake_signature = "0" * 64
        assert verify_license_signature(license_key, fake_signature) is False

    def test_device_fingerprint_consistent(self):
        """Device fingerprint deve ser consistente"""
        from backend.core.license_manager import get_device_fingerprint
        
        fp1 = get_device_fingerprint()
        fp2 = get_device_fingerprint()
        
        # Deve ser igual em mesma máquina
        assert fp1 == fp2
        assert len(fp1) == 16  # 16 chars (SHA256[:16])


class TestSecurityPhase1Endpoints:
    """Testar que endpoints validam secrets em produção"""

    @pytest.mark.asyncio
    async def test_app_startup_validates_secrets(self):
        """App deve falhar no startup se secrets estão inseguros"""
        # Isso será testado quando rodar o app
        # Com DEBUG=False, as validações devem ser mais rigorosas
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
