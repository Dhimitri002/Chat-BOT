# 🚀 Guia de Instalacao

> **Versao:** 1.0.0 | **Data:** 2026-05-26

Guia completo para instalar a Flora Platform do zero.

---

## 1. Pre-requisitos

### Obrigatorios

| Software | Versao Minima | Verificar |
|----------|---------------|-----------|
| Python | 3.11+ | `python --version` |
| pip | 23+ | `pip --version` |
| Git | 2.40+ | `git --version` |

### Opcional (Producao)

| Software | Versao | Uso |
|----------|--------|-----|
| PostgreSQL | 15+ | Banco de dados em producao |
| Redis | 7+ | Cache e rate limiting |
| Docker | 24+ | Deploy em conteineres |
| Node.js | 20+ | WhatsApp WPPConnect connector |

---

## 2. Instalacao Passo a Passo

### 2.1 Clonar o Repositorio

```bash
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform
```

### 2.2 Ambiente Virtual

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar (Linux/Mac)
source .venv/bin/activate

# Ativar (Windows)
.venv\Scripts\activate
```

> **Dica:** Sempre use ambiente virtual para evitar conflitos de dependencias.

### 2.3 Instalar Dependencias

```bash
# Atualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

**Dependencias principais instaladas:**
- `fastapi` — Framework web
- `uvicorn` — Servidor ASGI
- `sqlalchemy` — ORM
- `pydantic` — Validacao
- `python-jose` — JWT
- `passlib` — Hash de senhas
- `cryptography` — Criptografia
- `loguru` — Logging
- `httpx` — HTTP client
- `kivy` + `kivymd` — Apps desktop
- `pytest` — Testes

### 2.4 Configurar Ambiente

```bash
# Copiar template
cp .env.example .env

# Editar configuracoes
# (veja proxima secao)
```

### 2.5 Setup Inicial

```bash
# Criar tabelas do banco
python run.py setup

# Verificar instalacao
python run.py test
```

---

## 3. Configuracao do `.env`

Edite o arquivo `.env` com suas configuracoes:

### Minimo para Desenvolvimento

```env
# App
APP_NAME=Flora Platform
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# Seguranca (GERE CHAVES FORTES!)
SECRET_KEY=sua-chave-secreta-aqui-min-32-caracteres!!
FLORA_MASTER_KEY=sua-chave-mestra-aqui-min-32-cararacteres!!
LICENSE_SIGNING_KEY=sua-chave-licenca-aqui-min-32-caracteres!!

# Banco (SQLite para dev)
DATABASE_URL=sqlite+aiosqlite:///./flora.db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin padrao
ADMIN_EMAIL=admin@flora.com
ADMIN_PASSWORD=Admin@123456
ADMIN_NAME=Administrador

# WhatsApp
WHATSAPP_SESSION_DIR=./sessions
WHATSAPP_CONNECTOR_URL=http://localhost:3333

# Logging
LOG_LEVEL=INFO
```

### Gerar Chaves Seguras

```bash
# Python one-liner para gerar chaves
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 4. Banco de Dados

### 4.1 Desenvolvimento (SQLite)

SQLite e usado por padrao. Nenhuma configuracao extra necessaria.

```env
DATABASE_URL=sqlite+aiosqlite:///./flora.db
```

O arquivo `flora.db` sera criado automaticamente na raiz do projeto.

### 4.2 Producao (PostgreSQL)

```bash
# Instalar driver async do PostgreSQL
pip install asyncpg

# Configurar
DATABASE_URL=postgresql+asyncpg://usuario:senha@localhost:5432/flora_platform
```

**Criar banco:**
```sql
CREATE DATABASE flora_platform;
CREATE USER flora WITH ENCRYPTED PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE flora_platform TO flora;
```

### 4.3 Migrations (Alembic)

```bash
# Inicializar alembic (primeira vez)
alembic init alembic

# Gerar migration
alembic revision --autogenerate -m "descricao da mudanca"

# Aplicar migrations
alembic upgrade head

# Voltar uma migration
alembic downgrade -1
```

---

## 5. Redis

### 5.1 Instalacao

**Linux:**
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**Mac:**
```bash
brew install redis
brew services start redis
```

**Windows:**
```bash
# Usando Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 5.2 Verificar

```bash
redis-cli ping
# Deve retornar: PONG
```

### 5.3 Sem Redis (Desenvolvimento)

Se nao quiser instalar Redis, o backend funciona sem ele (rate limit e cache ficam desabilitados).

```env
REDIS_URL=redis://localhost:6379/0
# O backend tenta conectar, se falhar continua sem cache
```

---

## 6. WhatsApp Connector (Opcional em Dev)

Para testar a integracao WhatsApp, voce precisa do WPPConnect:

```bash
# Clonar WPPConnect
git clone https://github.com/wppconnect-team/wppconnect-server.git
cd wppconnect-server

# Instalar
npm install

# Configurar
cp .env.example .env

# Executar
npm run start
```

O connector rodara em `http://localhost:3333`.

---

## 7. Verificacao

### 7.1 Testar Backend

```bash
# Iniciar backend
python run.py backend

# Em outro terminal, testar
curl http://localhost:8000/api/v1/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 7.2 Testar Autenticacao

```bash
# Registrar
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Senha@123","name":"Test"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Senha@123"}'
```

### 7.3 Testar App Cliente

```bash
cd app_cliente
python main.py
```

### 7.4 Testar App Admin

```bash
cd app_admin
python main.py
```

---

## 8. Instalacao com Docker

### 8.1 Docker Compose (Recomendado)

```bash
# Tudo incluido
docker compose up -d

# Ver logs
docker compose logs -f

# Parar
docker compose down
```

### 8.2 Dockerfile (Backend)

```bash
# Build
docker build -t flora-backend .

# Run
docker run -d \
  --name flora-backend \
  -p 8000:8000 \
  --env-file .env \
  flora-backend
```

---

## 9. Problemas Comuns

### `ModuleNotFoundError`
```bash
# Verificar se o venv esta ativado
which python  # Deve mostrar .venv/bin/python

# Reinstalar dependencias
pip install -r requirements.txt
```

### `SECRET_KEY` muito curta
```
ValueError: SECRET_KEY must be at least 32 characters
```
```bash
# Gerar chave forte
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Banco de dados travado (SQLite)
```bash
# Deletar e recriar
rm flora.db
python run.py setup
```

### Redis nao conecta
```bash
# Verificar se esta rodando
redis-cli ping

# Ou desabilitar no .env (backend continua sem cache)
```

### Porta 8000 ja em uso
```bash
# Linux/Mac: encontrar processo
lsof -i :8000
kill -9 <PID>

# Ou usar outra porta
python run.py backend --port 8001
```

### Kivy nao abre (Linux)
```bash
# Instalar dependencias do Kivy
sudo apt install python3-dev libsdl2-dev libsdl2-image-dev \
  libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev libswscale-dev \
  libavformat-dev libavcodec-dev zlib1g-dev libgstreamer1.0-dev \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good
```

---

## 10. Proximos Passos

1. [Configuracao](configuracao.md) — Detalhes das variaveis de ambiente
2. [Execucao](execucao.md) — Como executar cada componente
3. [Desenvolvimento](desenvolvimento.md) — Guia do desenvolvedor
4. [API Reference](../API/) — Documentacao da API
