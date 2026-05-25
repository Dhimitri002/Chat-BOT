# 🌸 Flora Platform — Guia de Instalação

## Pré-requisitos

| Software | Versão | Obrigatório |
|---|---|---|
| Python | 3.11+ | ✅ |
| pip | 23+ | ✅ |
| Git | 2.40+ | ✅ |
| PostgreSQL | 15+ | Produção |
| Redis | 7+ | Produção |
| Node.js | 20+ | Opcional (WhatsApp) |

## Instalação Rápida

```bash
# 1. Clone
git clone https://github.com/TiltzOff/flora-platform.git
cd flora-platform

# 2. Ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Dependências
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configuração
cp .env.example .env
# Edite .env com suas configurações

# 5. Inicialização
python run.py setup

# 6. Execução
python run.py backend   # Terminal 1
python run.py admin     # Terminal 2
python run.py client    # Terminal 3
```

## Instalação com Docker

```bash
# Tudo incluso (backend + PostgreSQL + Redis)
docker compose up -d

# Verificar
docker compose ps
docker compose logs -f backend
```

## Verificação

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Documentação da API
# Abra: http://localhost:8000/docs

# Testes
python run.py test
```

## Troubleshooting

| Problema | Solução |
|---|---|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `psycopg2` build error | Use SQLite em dev ou instale `postgresql-dev` |
| Porta 8000 em use | Mude `PORT` no .env |
| Redis connection error | Inicie o Redis ou use cache em memória |
| Kivy não instala | Veja [Kivy install guide](https://kivy.org/doc/stable/gettingstarted/installing.html) |
