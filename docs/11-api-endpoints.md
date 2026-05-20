# 🌸 FLORA PLATFORM — API Endpoints

## Mapa Completo de Endpoints

### AUTH
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/auth/register` | Registrar novo usuário | Não |
| POST | `/auth/login` | Login (retorna access + refresh) | Não |
| POST | `/auth/refresh` | Renovar access token | Refresh token |
| POST | `/auth/logout` | Invalidar tokens | Sim |
| POST | `/auth/2fa/enable` | Habilitar 2FA | Sim |
| POST | `/auth/2fa/verify` | Verificar código 2FA | Sim |
| POST | `/auth/password-reset` | Solicitar reset de senha | Não |
| POST | `/auth/password-reset/confirm` | Confirmar reset | Token |

### USERS
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| GET | `/users/me` | Perfil do usuário logado | Sim |
| PUT | `/users/me` | Atualizar perfil | Sim |
| GET | `/users` | Listar usuários (admin) | Admin |
| GET | `/users/:id` | Detalhes do usuário | Admin |
| PUT | `/users/:id` | Atualizar usuário | Admin |
| DELETE | `/users/:id` | Deletar usuário | Superadmin |

### LICENSES
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/licenses` | Criar licença | Admin |
| POST | `/licenses/validate` | Validar licença (cliente) | Não* |
| GET | `/licenses` | Listar licenças | Admin |
| GET | `/licenses/:id` | Detalhes da licença | Admin |
| PUT | `/licenses/:id/revoke` | Revogar licença | Admin |
| PUT | `/licenses/:id/renew` | Renovar licença | Admin |
| GET | `/licenses/:id/usage` | Uso da licença | Admin |

### PLANS
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| GET | `/plans` | Listar planos públicos | Não |
| GET | `/plans/:id` | Detalhes do plano | Não |
| POST | `/plans` | Criar plano | Superadmin |
| PUT | `/plans/:id` | Atualizar plano | Superadmin |
| DELETE | `/plans/:id` | Deletar plano | Superadmin |

### SUBSCRIPTIONS
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/subscriptions` | Criar assinatura | Admin |
| GET | `/subscriptions` | Listar assinaturas | Admin |
| GET | `/subscriptions/:id` | Detalhes | Admin |
| PUT | `/subscriptions/:id` | Atualizar | Admin |
| POST | `/subscriptions/:id/cancel` | Cancelar | Admin |
| POST | `/subscriptions/:id/upgrade` | Upgrade | Admin |

### BOTS
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/bots` | Criar bot | Admin |
| GET | `/bots` | Listar bots | Admin |
| GET | `/bots/:id` | Detalhes do bot | Admin/Cliente* |
| PUT | `/bots/:id` | Atualizar bot | Admin |
| DELETE | `/bots/:id` | Deletar bot | Admin |
| POST | `/bots/:id/activate` | Ativar bot | Admin |
| POST | `/bots/:id/deactivate` | Desativar bot | Admin |
| POST | `/bots/:id/duplicate` | Duplicar bot | Admin |
| GET | `/bots/:id/config` | Config completa | Admin |
| PUT | `/bots/:id/config` | Atualizar config | Admin |
| POST | `/bots/:id/test` | Testar bot (sandbox) | Admin |

### WHATSAPP
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/whatsapp/connect` | Iniciar conexão | Cliente |
| POST | `/whatsapp/disconnect` | Desconectar | Cliente |
| GET | `/whatsapp/status` | Status da sessão | Cliente |
| GET | `/whatsapp/qr` | Obter QR Code | Cliente |
| POST | `/whatsapp/send` | Enviar mensagem | Admin |

### INTENTS
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/bots/:id/intents` | Criar intent | Admin |
| GET | `/bots/:id/intents` | Listar intents | Admin |
| PUT | `/intents/:id` | Atualizar intent | Admin |
| DELETE | `/intents/:id` | Deletar intent | Admin |
| POST | `/intents/:id/test` | Testar intent | Admin |

### COMMANDS
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/bots/:id/commands` | Criar comando | Admin |
| GET | `/bots/:id/commands` | Listar comandos | Admin |
| PUT | `/commands/:id` | Atualizar comando | Admin |
| DELETE | `/commands/:id` | Deletar comando | Admin |
| POST | `/commands/:id/test` | Testar comando | Admin |
| POST | `/commands/:id/approve` | Aprovar comando | Admin |

### CHAT
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/chat` | Processar mensagem (webhook) | API Key |
| POST | `/chat/flora` | Chat com Flora AI | Cliente |
| GET | `/chat/history/:contact` | Histórico | Admin/Cliente |
| GET | `/chat/conversations` | Lista conversas | Admin/Cliente |

### ANALYTICS
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| GET | `/analytics/dashboard` | Dashboard geral | Admin |
| GET | `/analytics/bot/:id` | Analytics por bot | Admin |
| GET | `/analytics/llm-usage` | Uso de LLM | Admin |
| GET | `/analytics/revenue` | Receita | Admin |
| GET | `/analytics/client/:id` | Por cliente | Admin |
| GET | `/analytics/export` | Exportar relatório | Admin |

### BILLING
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/billing/checkout` | Criar sessão de pagamento | Cliente |
| GET | `/billing/invoices` | Listar faturas | Admin |
| POST | `/billing/webhook/stripe` | Webhook Stripe | Não* |
| POST | `/billing/webhook/mercadopago` | Webhook MP | Não* |

### SUPPORT
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/support/tickets` | Criar ticket | Cliente |
| GET | `/support/tickets` | Listar tickets | Admin/Cliente |
| GET | `/support/tickets/:id` | Detalhes | Admin/Cliente |
| POST | `/support/tickets/:id/reply` | Responder | Admin/Cliente |
| PUT | `/support/tickets/:id/status` | Atualizar status | Admin |

### BACKUP
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/bots/:id/backup` | Criar backup | Admin |
| POST | `/bots/:id/restore` | Restaurar | Admin |
| GET | `/bots/:id/backups` | Listar backups | Admin |
| GET | `/backups/:id/download` | Download | Admin |

### TEMPLATES
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| GET | `/templates` | Listar templates | Admin |
| GET | `/templates/:id` | Detalhes | Admin |
| POST | `/templates` | Criar template | Admin |
| PUT | `/templates/:id` | Atualizar | Admin |
| POST | `/templates/:id/apply` | Aplicar em bot | Admin |

### WEBHOOKS
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| POST | `/bots/:id/webhooks` | Criar webhook | Admin |
| GET | `/bots/:id/webhooks` | Listar | Admin |
| PUT | `/webhooks/:id` | Atualizar | Admin |
| DELETE | `/webhooks/:id` | Deletar | Admin |
| POST | `/webhooks/:id/test` | Testar | Admin |

### SYSTEM
| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| GET | `/health` | Health check | Não |
| GET | `/system/status` | Status do sistema | Superadmin |
| GET | `/system/logs` | Logs do sistema | Superadmin |
| POST | `/system/maintenance` | Modo manutenção | Superadmin |
| GET | `/system/metrics` | Métricas (Prometheus) | Superadmin |

## Exemplos de Request/Response

### POST /auth/login
```json
// Request
{
  "email": "admin@flora.app",
  "password": "SenhaForte123!"
}

// Response 200
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@flora.app",
    "full_name": "Admin Flora",
    "role": "superadmin",
    "is_2fa_enabled": true
  }
}

// Response 401
{
  "error": "invalid_credentials",
  "message": "Email ou senha incorretos"
}
```

### POST /licenses/validate
```json
// Request
{
  "license_key": "FLORA-A3F2-B8C1-D4E5-9G7H",
  "device_fingerprint": "sha256:abc123..."
}

// Response 200
{
  "valid": true,
  "plan": {
    "id": "...",
    "name": "Pro",
    "slug": "pro",
    "features": {
      "has_llm": true,
      "llm_provider": "groq",
      "has_flora": true,
      "max_messages_month": 5000
    }
  },
  "expires_at": "2026-06-19T00:00:00Z",
  "days_remaining": 23
}

// Response 400
{
  "valid": false,
  "reason": "expired",
  "message": "Sua licença expirou em 2026-04-19. Renove para continuar usando."
}
```

### POST /chat/flora
```json
// Request
{
  "message": "Como conecto o WhatsApp?",
  "session_id": "flora-session-abc123"
}

// Response 200 (streaming SSE)
{
  "reply": "Para conectar seu WhatsApp, siga estes passos:\n\n1. Toque em 'Conectar WhatsApp' na tela principal\n2. Abra o WhatsApp no seu celular\n3. Vá em Aparelhos conectados\n4. Escaneie o QR Code\n\nPronto! Seu bot estará online. 🌸",
  "session_id": "flora-session-abc123",
  "tokens_used": 150
}
```

### POST /bots
```json
// Request
{
  "license_id": "550e8400-...",
  "name": "Assistente Pizzaria",
  "prompt": "Você é o assistente da Pizzaria Bella...",
  "personality": "friendly",
  "tone": "warm",
  "language": "pt-BR",
  "welcome_message": "Olá! 🍕 Bem-vindo!",
  "business_hours": {
    "mon": {"start": "18:00", "end": "23:00"}
  },
  "llm": {
    "provider": "groq",
    "model": "llama-3.1-70b-versatile",
    "temperature": 0.7
  }
}

// Response 201
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Assistente Pizzaria",
  "status": "created",
  "created_at": "2026-05-19T12:00:00Z"
}
```
