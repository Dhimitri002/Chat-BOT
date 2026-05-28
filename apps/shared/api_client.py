# ═══════════════════════════════════════════════════════════════
# Flora Platform — Cliente HTTP Assíncrono (httpx)
# ═══════════════════════════════════════════════════════════════
# Cliente HTTP compartilhado para comunicação com o backend FastAPI.
# Gerencia autenticação, tokens, retry automático e validação de licença.
# ═══════════════════════════════════════════════════════════════

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


# ═══════════════════════════════════════════════════════════════
# Configuração
# ═══════════════════════════════════════════════════════════════

DEFAULT_BASE_URL: str = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT: float = 30.0
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_RETRY_DELAY: float = 1.0
TOKEN_FILENAME: str = ".flora_token.json"
LICENSE_FILENAME: str = ".flora_license.json"

# Diretório para armazenar tokens localmente
LOCAL_DATA_DIR: Path = Path.home() / ".flora"


# ═══════════════════════════════════════════════════════════════
# Exceções Customizadas
# ═══════════════════════════════════════════════════════════════


class APIError(Exception):
    """Erro generico da API."""

    def __init__(self, message: str, status_code: int = 0, detail: Any = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class AuthError(APIError):
    """Erro de autenticacao (401/403)."""
    pass


class LicenseError(APIError):
    """Erro de licenca (expirada, invalida ou nao encontrada)."""
    pass


class NetworkError(APIError):
    """Erro de rede (conexao, timeout)."""
    pass


class ValidationError(APIError):
    """Erro de validacao (422)."""
    pass


# ═══════════════════════════════════════════════════════════════
# Cliente HTTP — FloraAPIClient
# ═══════════════════════════════════════════════════════════════


class FloraAPIClient:
    """Cliente HTTP assincrono para a API da Flora Platform.

    Gerencia autenticacao JWT, retry automatico e armazenamento
    local de tokens. Projetado para uso em aplicativos KivyMD.

    Uso:
        client = FloraAPIClient(base_url="http://localhost:8000")
        await client.login("user@email.com", "senha123")
        data = await client.get("/api/v1/clients")

    Atributos:
        base_url: URL base da API FastAPI.
        timeout: Timeout padrao para requisicoes (segundos).
        max_retries: Numero maximo de tentativas em caso de erro de rede.
        token: Token JWT atual (se autenticado).
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        self.base_url: str = base_url.rstrip("/")
        self.timeout: float = timeout
        self.max_retries: int = max_retries
        self.retry_delay: float = retry_delay
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._user_id: Optional[int] = None
        self._license_key: Optional[str] = None

        # Garante que o diretorio local existe
        LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Carrega token salvo (se existir)
        self._load_token()

    # ── Propriedades ──────────────────────────────────────────

    @property
    def token(self) -> Optional[str]:
        """Token JWT atual."""
        return self._token

    @property
    def is_authenticated(self) -> bool:
        """True se ha um token carregado."""
        return self._token is not None

    @property
    def user_id(self) -> Optional[int]:
        """ID do usuario autenticado."""
        return self._user_id

    @property
    def license_key(self) -> Optional[str]:
        """Chave de licenca atual."""
        return self._license_key

    # ── Gerenciamento de Token ────────────────────────────────

    def _token_path(self) -> Path:
        """Retorna o caminho do arquivo de token."""
        return LOCAL_DATA_DIR / TOKEN_FILENAME

    def _license_path(self) -> Path:
        """Retorna o caminho do arquivo de licenca."""
        return LOCAL_DATA_DIR / LICENSE_FILENAME

    def _load_token(self) -> None:
        """Carrega token JWT do armazenamento local."""
        token_file = self._token_path()
        if token_file.exists():
            try:
                data = json.loads(token_file.read_text(encoding="utf-8"))
                self._token = data.get("access_token")
                self._refresh_token = data.get("refresh_token")
                self._user_id = data.get("user_id")
                logger.debug("Token carregado do armazenamento local.")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Erro ao carregar token: {e}")
                self._token = None

    def _save_token(
        self,
        access_token: str,
        refresh_token: str = "",
        user_id: Optional[int] = None,
    ) -> None:
        """Salva token JWT no armazenamento local.

        Args:
            access_token: Token de acesso JWT.
            refresh_token: Token de refresh (opcional).
            user_id: ID do usuario (opcional).
        """
        self._token = access_token
        self._refresh_token = refresh_token or self._refresh_token
        self._user_id = user_id or self._user_id

        data = {
            "access_token": self._token,
            "refresh_token": self._refresh_token,
            "user_id": self._user_id,
        }
        self._token_path().write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
        logger.debug("Token salvo no armazenamento local.")

    def _clear_token(self) -> None:
        """Remove token do armazenamento local e da memoria."""
        self._token = None
        self._refresh_token = None
        self._user_id = None
        token_file = self._token_path()
        if token_file.exists():
            token_file.unlink()
        logger.debug("Token removido.")

    def _save_license(
        self, license_key: str, plan: str = "", expires_at: str = ""
    ) -> None:
        """Salva informacoes de licenca localmente.

        Args:
            license_key: Chave de licenca.
            plan: Nome do plano.
            expires_at: Data de expiracao ISO.
        """
        self._license_key = license_key
        data = {
            "license_key": license_key,
            "plan": plan,
            "expires_at": expires_at,
        }
        self._license_path().write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )

    def _load_license(self) -> Optional[Dict[str, str]]:
        """Carrega informacoes de licenca do armazenamento local.

        Returns:
            Dicionario com dados da licenca ou None.
        """
        license_file = self._license_path()
        if license_file.exists():
            try:
                data = json.loads(license_file.read_text(encoding="utf-8"))
                self._license_key = data.get("license_key")
                return data
            except (json.JSONDecodeError, KeyError):
                return None
        return None

    # ── Headers ───────────────────────────────────────────────

    def _get_headers(
        self, extra: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Constrói headers HTTP com token de autenticacao.

        Args:
            extra: Headers adicionais.

        Returns:
            Dicionario de headers.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra:
            headers.update(extra)
        return headers

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any:
        """Retorna JSON da resposta de forma segura."""
        try:
            return response.json().get("detail")
        except Exception:
            return None

    # ── Retry Logic ───────────────────────────────────────────

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> httpx.Response:
        """Executa requisicao HTTP com retry automatico.

        Args:
            method: Metodo HTTP ('GET', 'POST', etc.).
            endpoint: Caminho do endpoint (ex: '/api/v1/clients').
            **kwargs: Argumentos adicionais para httpx.

        Returns:
            httpx.Response.

        Raises:
            NetworkError: Apos esgotar tentativas de retry.
            AuthError: Em caso de 401/403.
            APIError: Em caso de outros erros HTTP.
        """
        url = f"{self.base_url}{endpoint}"
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, **kwargs)

                # Trata erros HTTP
                if response.status_code == 401:
                    if self._refresh_token and attempt < self.max_retries:
                        refreshed = await self._try_refresh_token()
                        if refreshed:
                            kwargs["headers"] = self._get_headers()
                            continue
                    raise AuthError(
                        "Autenticacao necessaria.",
                        status_code=401,
                        detail=self._safe_json(response),
                    )

                if response.status_code == 403:
                    raise AuthError(
                        "Acesso negado.",
                        status_code=403,
                        detail=self._safe_json(response),
                    )

                if response.status_code == 404:
                    raise APIError("Recurso nao encontrado.", status_code=404)

                if response.status_code == 422:
                    raise ValidationError(
                        "Dados invalidos.",
                        status_code=422,
                        detail=self._safe_json(response),
                    )

                if response.status_code >= 500:
                    raise APIError(
                        f"Erro interno do servidor: {response.status_code}",
                        status_code=response.status_code,
                    )

                return response

            except (httpx.ConnectError, httpx.TimeoutException,
                    httpx.NetworkError) as e:
                last_exception = e
                logger.warning(
                    f"Tentativa {attempt}/{self.max_retries} falhou: {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)

            except (AuthError, ValidationError):
                raise

            except Exception as e:
                last_exception = e
                logger.error(f"Erro inesperado na requisicao: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)

        raise NetworkError(
            f"Falha de rede apos {self.max_retries} tentativas.",
            detail=str(last_exception),
        )

    async def _try_refresh_token(self) -> bool:
        """Tenta renovar o token usando o refresh token.

        Returns:
            True se o refresh foi bem-sucedido.
        """
        if not self._refresh_token:
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/refresh",
                    json={"refresh_token": self._refresh_token},
                    headers={"Content-Type": "application/json"},
                )

            if response.status_code == 200:
                data = response.json()
                self._save_token(
                    access_token=data["access_token"],
                    refresh_token=data.get(
                        "refresh_token", self._refresh_token
                    ),
                    user_id=data.get("user_id", self._user_id),
                )
                logger.info("Token renovado com sucesso.")
                return True

        except Exception as e:
            logger.warning(f"Falha ao renovar token: {e}")

        self._clear_token()
        return False

    # ── Métodos HTTP Públicos ─────────────────────────────────

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Executa requisicao GET.

        Args:
            endpoint: Caminho do endpoint.
            params: Parametros de query string.
            headers: Headers adicionais.

        Returns:
            Resposta JSON como dicionario.
        """
        response = await self._request_with_retry(
            "GET",
            endpoint,
            params=params,
            headers=self._get_headers(headers),
        )
        return response.json()

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Executa requisicao POST.

        Args:
            endpoint: Caminho do endpoint.
            data: Dados de formulario.
            json_data: Dados JSON.
            headers: Headers adicionais.

        Returns:
            Resposta JSON como dicionario.
        """
        kwargs = {"headers": self._get_headers(headers)}
        if json_data is not None:
            kwargs["json"] = json_data
        if data is not None:
            kwargs["data"] = data

        response = await self._request_with_retry("POST", endpoint, **kwargs)
        return response.json()

    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Executa requisicao PUT.

        Args:
            endpoint: Caminho do endpoint.
            json_data: Dados JSON.
            headers: Headers adicionais.

        Returns:
            Resposta JSON como dicionario.
        """
        kwargs = {"headers": self._get_headers(headers)}
        if json_data is not None:
            kwargs["json"] = json_data

        response = await self._request_with_retry("PUT", endpoint, **kwargs)
        return response.json()

    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Executa requisicao DELETE.

        Args:
            endpoint: Caminho do endpoint.
            headers: Headers adicionais.

        Returns:
            Resposta JSON como dicionario.
        """
        response = await self._request_with_retry(
            "DELETE",
            endpoint,
            headers=self._get_headers(headers),
        )
        return response.json()

    # ── Autenticação ──────────────────────────────────────────

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Realiza login e salva o token JWT.

        Args:
            email: Email do usuario.
            password: Senha do usuario.

        Returns:
            Dados da resposta (token, user_id, etc.).

        Raises:
            AuthError: Credenciais invalidas.
            NetworkError: Erro de conexao.
        """
        response = await self.post(
            "/api/v1/auth/login",
            json_data={"email": email, "password": password},
        )

        access_token = response.get("access_token")
        refresh_token = response.get("refresh_token", "")
        user_id = response.get("user_id")

        if access_token:
            self._save_token(access_token, refresh_token, user_id)
            logger.info(f"Login realizado com sucesso (user_id={user_id}).")

        return response

    async def logout(self) -> None:
        """Realiza logout e remove tokens."""
        try:
            await self.post("/api/v1/auth/logout")
        except Exception:
            pass
        self._clear_token()
        logger.info("Logout realizado.")

    async def register(
        self,
        name: str,
        email: str,
        password: str,
        phone: str = "",
    ) -> Dict[str, Any]:
        """Registra um novo usuario.

        Args:
            name: Nome completo.
            email: Email.
            password: Senha.
            phone: Telefone (opcional).

        Returns:
            Dados do usuario criado.
        """
        return await self.post(
            "/api/v1/auth/register",
            json_data={
                "name": name,
                "email": email,
                "password": password,
                "phone": phone,
            },
        )

    async def get_profile(self) -> Dict[str, Any]:
        """Retorna o perfil do usuario autenticado.

        Returns:
            Dados do perfil.
        """
        return await self.get("/api/v1/auth/me")

    # ── Validação de Licença ──────────────────────────────────

    async def validate_license(self, license_key: str) -> Dict[str, Any]:
        """Valida uma chave de licenca na API.

        Args:
            license_key: Chave de licenca a validar.

        Returns:
            Dados da licenca (plan, expiracao, etc.).

        Raises:
            LicenseError: Licenca invalida ou expirada.
        """
        try:
            response = await self.post(
                "/api/v1/licenses/validate",
                json_data={"license_key": license_key},
            )

            # Salva licenca localmente
            self._save_license(
                license_key=license_key,
                plan=response.get("plan", ""),
                expires_at=response.get("expires_at", ""),
            )

            logger.info(
                f"Licenca validada: {response.get('plan', 'desconhecido')}"
            )
            return response

        except APIError as e:
            if e.status_code == 404:
                raise LicenseError("Licenca nao encontrada.", status_code=404)
            if e.status_code == 410:
                raise LicenseError("Licenca expirada.", status_code=410)
            raise LicenseError(
                f"Erro ao validar licenca: {e.message}",
                status_code=e.status_code,
            )

    async def check_license_status(self) -> Dict[str, Any]:
        """Verifica o status da licenca atual.

        Returns:
            Status da licenca.
        """
        if not self._license_key:
            local = self._load_license()
            if not local:
                raise LicenseError("Nenhuma licenca configurada.")
            self._license_key = local.get("license_key")

        return await self.validate_license(self._license_key)

    # ── Endpoints de Negócio ──────────────────────────────────

    async def get_clients(
        self,
        page: int = 1,
        per_page: int = 20,
        search: str = "",
    ) -> Dict[str, Any]:
        """Lista clientes paginados.

        Args:
            page: Numero da pagina.
            per_page: Itens por pagina.
            search: Termo de busca.

        Returns:
            Lista paginada de clientes.
        """
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        return await self.get("/api/v1/clients", params=params)

    async def get_client(self, client_id: int) -> Dict[str, Any]:
        """Retorna detalhes de um cliente.

        Args:
            client_id: ID do cliente.

        Returns:
            Dados do cliente.
        """
        return await self.get(f"/api/v1/clients/{client_id}")

    async def create_client(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um novo cliente.

        Args:
            data: Dados do cliente.

        Returns:
            Cliente criado.
        """
        return await self.post("/api/v1/clients", json_data=data)

    async def update_client(
        self, client_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza um cliente existente.

        Args:
            client_id: ID do cliente.
            data: Dados atualizados.

        Returns:
            Cliente atualizado.
        """
        return await self.put(f"/api/v1/clients/{client_id}", json_data=data)

    async def delete_client(self, client_id: int) -> Dict[str, Any]:
        """Remove um cliente.

        Args:
            client_id: ID do cliente.

        Returns:
            Confirmacao de remocao.
        """
        return await self.delete(f"/api/v1/clients/{client_id}")

    async def get_conversations(
        self,
        client_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """Lista conversas.

        Args:
            client_id: Filtrar por cliente (opcional).
            page: Numero da pagina.
            per_page: Itens por pagina.

        Returns:
            Lista paginada de conversas.
        """
        params = {"page": page, "per_page": per_page}
        if client_id:
            params["client_id"] = client_id
        return await self.get("/api/v1/conversations", params=params)

    async def get_messages(
        self,
        conversation_id: int,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        """Lista mensagens de uma conversa.

        Args:
            conversation_id: ID da conversa.
            page: Numero da pagina.
            per_page: Itens por pagina.

        Returns:
            Lista paginada de mensagens.
        """
        params = {"page": page, "per_page": per_page}
        return await self.get(
            f"/api/v1/conversations/{conversation_id}/messages",
            params=params,
        )

    async def send_message(
        self,
        conversation_id: int,
        content: str,
        role: str = "user",
    ) -> Dict[str, Any]:
        """Envia uma mensagem em uma conversa.

        Args:
            conversation_id: ID da conversa.
            content: Conteudo da mensagem.
            role: Papel do remetente ('user' ou 'assistant').

        Returns:
            Mensagem criada.
        """
        return await self.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json_data={"content": content, "role": role},
        )

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Retorna estatisticas do dashboard.

        Returns:
            Metricas do dashboard.
        """
        return await self.get("/api/v1/dashboard/stats")

    async def get_plans(self) -> List[Dict[str, Any]]:
        """Lista todos os planos disponiveis.

        Returns:
            Lista de planos.
        """
        return await self.get("/api/v1/plans")
