# 🌸 FLORA PLATFORM — Guia de Instalação

> Guia completo de instalação para Windows, Linux e macOS.

---

## 📋 Pré-requisitos

| Requisito | Versão Mínima | Obrigatório |
|---|---|---|
| **Python** | 3.11+ | ✅ Sim |
| **pip** | 23.0+ | ✅ Sim |
| **Git** | 2.40+ | ✅ Sim |
| **Redis** | 7.0+ | ⚠️ Recomendado |
| **PostgreSQL** | 16+ | ⚠️ Produção |
| **Docker** | 24+ | ⚠️ Opcional |
| **Docker Compose** | 2.20+ | ⚠️ Opcional |

---

## 🚀 Instalação Rápida (Desenvolvimento)

### 1. Clone o Repositório

```bash
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform
```

### 2. Crie um Ambiente Virtual

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Instale as Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure as Variáveis de Ambiente

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env

# Windows (CMD)
copy .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Mínimo necessário para desenvolvimento
SECRET_KEY=sua-chave-secreta-aqui-min-32-chars
JWT_SECRET=seu-jwt-secret-aqui-min-32-chars!!
DATABASE_URL=sqlite+aiosqlite:///./flora.db
ENVIRONMENT=development
DEBUG=true
```

### 5. Execute o Backend

```bash
python run.py
```

A API estará disponível em:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🪟 Instalação no Windows (Detalhada)

### Passo 1: Instalar Python 3.11+

1. Acesse [python.org/downloads](https://www.python.org/downloads/)
2. Baixe o instalador do Python 3.11+
3. **IMPORTANTE**: Marque "Add Python to PATH"
4. Clique em "Install Now"

Verifique a instalação:
```cmd
python --version
pip --version
```

### Passo 2: Instalar Git

1. Acesse [git-scm.com](https://git-scm.com/)
2. Baixe e instale o Git para Windows
3. Use as opções padrão do instalador

Verifique:
```cmd
git --version
```

### Passo 3: Clonar e Configurar

```cmd
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### Passo 4: Executar

```cmd
python run.py
```

### (Opcional) Instalar Redis no Windows

Opção 1 — **WSL2** (recomendado):
```bash
# No terminal WSL2 (Ubuntu)
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

Opção 2 — **Memurai** (Redis para Windows):
1. Baixe em [memurai.com](https://www.memurai.com/)
2. Instale e inicie o serviço

---

## 🐧 Instalação no Linux (Detalhada)

### Ubuntu / Debian

```bash
# 1. Atualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python 3.11+
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# 3. Instalar Git
sudo apt install git -y

# 4. (Opcional) Instalar Redis
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 5. (Opcional) Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib -y
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 6. Clonar e configurar
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 7. Executar
python run.py
```

### Fedora / RHEL

```bash
# 1. Instalar Python 3.11+
sudo dnf install python3.11 python3.11-devel -y

# 2. Instalar Git
sudo dnf install git -y

# 3. (Opcional) Instalar Redis
sudo dnf install redis -y
sudo systemctl enable redis
sudo systemctl start redis

# 4. Clonar e configurar
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 5. Executar
python run.py
```

### Arch Linux

```bash
# 1. Instalar Python e Git
sudo pacman -S python python-pip git

# 2. (Opcional) Instalar Redis
sudo pacman -S redis
sudo systemctl enable redis
sudo systemctl start redis

# 3. Clonar e configurar
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 4. Executar
python run.py
```

---

## 🍎 Instalação no macOS (Detalhada)

### Usando Homebrew (Recomendado)

```bash
# 1. Instalar Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar Python 3.11+
brew install python@3.11

# 3. Instalar Git
brew install git

# 4. (Opcional) Instalar Redis
brew install redis
brew services start redis

# 5. (Opcional) Instalar PostgreSQL
brew install postgresql@16
brew services start postgresql@16

# 6. Clonar e configurar
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 7. Executar
python run.py
```

---

## 🐳 Instalação com Docker

### Pré-requisitos

- Docker 24+
- Docker Compose 2.20+

### Passo a Passo

```bash
# 1. Clonar
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform

# 2. Configurar ambiente
cp .env.example .env
# Edite o .env para produção (veja seção de Deploy)

# 3. Build e subir containers
docker compose up -d --build

# 4. Verificar logs
docker compose logs -f backend

# 5. Verificar status
docker compose ps
```

### Comandos Docker Úteis

```bash
# Parar tudo
docker compose down

# Parar e remover volumes (CUIDADO: apaga dados)
docker compose down -v

# Ver logs em tempo real
docker compose logs -f backend

# Executar comando no container
docker compose exec backend bash

# Rebuild após mudanças
docker compose up -d --build backend

# Ver health check
docker compose ps
```

### Serviços no Docker Compose

| Serviço | Porta | Descrição |
|---|---|---|
| `backend` | 8000 | FastAPI REST API |
| `postgres` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 |
| `prometheus` | 9090 | Métricas |
| `grafana` | 3000 | Dashboards |

---

## ⚙️ Configuração do Banco de Dados

### SQLite (Desenvolvimento — Padrão)

```env
DATABASE_URL=sqlite+aiosqlite:///./flora.db
```

Não precisa de configuração adicional. O arquivo `flora.db` é criado automaticamente.

### PostgreSQL (Produção)

```env
DATABASE_URL=postgresql+asyncpg://flora:SENHA@localhost:5432/flora_platform
```

Criar banco e usuário:

```sql
CREATE USER flora WITH PASSWORD 'SENHA';
CREATE DATABASE flora_platform OWNER flora;
GRANT ALL PRIVILEGES ON DATABASE flora_platform TO flora;
```

---

## 🔑 Configuração de Chaves

### Gerar SECRET_KEY

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Linux / macOS
openssl rand -hex 32
```

### Gerar JWT_SECRET

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### Gerar ENCRYPTION_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Gerar LICENSE_SIGNING_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🧪 Verificação da Instalação

Após iniciar o backend, verifique:

```bash
# 1. Health check
curl http://localhost:8000/api/v1/health

# Esperado: {"status":"healthy","version":"1.0.0"}

# 2. Documentação Swagger
# Abra no navegador: http://localhost:8000/docs

# 3. Registrar usuário de teste
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@flora.com","password":"Teste@123456","name":"Teste"}'

# 4. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@flora.com","password":"Teste@123456"}'
```

---

## 🧪 Executando Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=backend --cov-report=html

# Testes específicos
pytest backend/tests/test_security_phase1.py -v

# Com output detalhado
pytest -v -s
```

---

## 🔧 Troubleshooting

### Erro: `ModuleNotFoundError`
```bash
# Certifique-se de que o venv está ativo
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Reinstale dependências
pip install -r requirements.txt
```

### Erro: `Connection refused` no banco
```bash
# Verifique se o DATABASE_URL está correto no .env
# Para SQLite, verifique permissões de escrita
# Para PostgreSQL, verifique se o serviço está rodando
```

### Erro: Porta 8000 já em uso
```bash
# Linux/macOS
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Erro: Redis não conecta
```bash
# Verifique se o Redis está rodando
redis-cli ping
# Esperado: PONG

# Se não estiver, inicie:
redis-server  # Linux/macOS
# ou inicie o serviço Redis no Windows
```

---

## 📚 Próximos Passos

- [Configuração da API](11-api-endpoints.md) — Endpoints disponíveis
- [Flora AI](09-flora-ai.md) — Configurar a assistente
- [Segurança](10-seguranca.md) — Configurações de segurança
- [Deploy](deploy.md) — Deploy em produção

---

<div align="center">

🌸 [Índice](INDICE.md) | [Anterior: Planos](14-planos.md) | [Próximo: Deploy](deploy.md)

</div>
