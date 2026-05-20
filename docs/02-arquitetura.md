# 🌸 FLORA PLATFORM — Arquitetura Completa

## Diagrama de Componentes

```
[WhatsApp User] ←→ [WPPConnect Connector] ←→ [Backend FastAPI] ←→ [PostgreSQL + Redis]
                                                              ↕
                                              [App Admin (KivyMD)]  [App Cliente (KivyMD)]
                                                              ↕
                                                   [LLM Router → Groq/Gemini/OpenAI/Claude/Ollama]
```

## Comunicação

```
App Admin ──HTTPS──▶ Backend API ◀──HTTPS── App Cliente
                         │
                    ┌────┴────┐
                    │         │
               PostgreSQL   Redis
                    │
              ┌─────┴──────┐
              │            │
         WPPConnect    LLM Router
         (sessões)    (Groq, Gemini,
                      OpenAI, etc.)
```

## Princípios Arquiteturais

1. **Cliente burro, servidor inteligente** — toda lógica crítica no backend
2. **Zero trust** — toda requisição autenticada e autorizada
3. **Segregação por plano** — feature flags controladas server-side
4. **Idempotência** — operações repetidas não causam efeitos colaterais
5. **Circuit breaker** — se uma LLM cai, fallback automático
6. **Event-driven** — eventos desacoplam módulos
7. **Stateless API** — escala horizontal sem sessão grudada

## Stack Técnica

### Frontend (Apps Desktop)
| Tecnologia | Uso |
|---|---|
| Python | Linguagem base |
| Kivy | Framework UI cross-platform |
| KivyMD | Material Design components |
| kv language | Declaração de UI |
| Pillow | Processamento de imagens |
| qrcode | Geração de QR Code |
| matplotlib | Gráficos |
| rich | Terminal bonito (dev) |
| watchdog | File system events |
| python-dotenv | Variáveis de ambiente |
| requests | HTTP client |
| aiohttp | HTTP async |
| websockets | Comunicação real-time |
| pyinstaller | Build executável |
| orjson | JSON rápido |
| msgpack | Serialização compacta |
| tenacity | Retry com backoff |
| jinja2 | Templates |

### Backend
| Tecnologia | Uso |
|---|---|
| FastAPI | Framework web async |
| Uvicorn | ASGI server |
| Pydantic | Validação de dados |
| SQLAlchemy | ORM |
| Alembic | Migrações de banco |
| SQLite → PostgreSQL | Banco de dados |
| Redis | Cache + sessões + pub/sub |
| APScheduler | Tarefas agendadas |
| Loguru | Logging |
| httpx | HTTP client async |
| Celery/RQ | Task queue |
| PyJWT | Tokens JWT |
| cryptography | Criptografia AES/RSA |
| passlib + argon2-cffi | Hash de senhas |
| jsonschema | Validação de schemas |
| pandas | Análise de dados |
| openpyxl | Exportar Excel |

### LLMs Suportadas
| Provider | Modelos | Uso |
|---|---|---|
| Groq | llama-3.1-8b, llama-3.1-70b | Rápido, barato |
| Gemini | 1.5-flash, 1.5-pro | Multimodal, raciocínio |
| OpenAI | gpt-4o-mini, gpt-4o | Tarefas gerais |
| Anthropic | claude-3-haiku, claude-3.5-sonnet | Contexto longo |
| DeepSeek | deepseek-chat | Raciocínio, baixo custo |
| Cohere | command-r | Tarefas específicas |
| Ollama | llama3:8b, llama3:70b | Local/offline |
| Together AI | Vários | Alternativa |
| HuggingFace | Vários | Alternativa |
| AWS Bedrock | Vários | Corporativo |

### Opcional (IA Avançada)
| Biblioteca | Uso |
|---|---|
| faiss | Busca vetorial |
| chromadb | Banco vetorial |
| sentence-transformers | Embeddings |
| transformers | Modelos HuggingFace |
| spaCy | NLP |
| scikit-learn | ML básico |
| numpy | Computação |
