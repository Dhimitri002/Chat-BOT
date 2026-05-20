# 🌸 FLORA PLATFORM — Banco de Dados

## Entidades Principais (Diagrama ER)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   users      │────▶│  licenses   │────▶│   plans     │
│             │     │             │     │             │
│ id (UUID)   │     │ id (UUID)   │     │ id (UUID)   │
│ email       │     │ user_id(FK) │     │ name        │
│ password    │     │ plan_id(FK) │     │ slug        │
│ role        │     │ key_hash    │     │ price       │
│ is_active   │     │ signature   │     │ features    │
│ created_at  │     │ status      │     │ limits      │
└─────────────┘     │ expires_at  │     │ llm_access  │
                    └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │    bots      │
                    │             │
                    │ id (UUID)   │
                    │ license_id  │
                    │ name        │
                    │ prompt      │
                    │ personality │
                    │ language    │
                    │ config      │
                    │ is_active   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────┴──┐  ┌─────┴─────┐  ┌──┴──────────┐
     │ whatsapp_ │  │  commands │  │  bot_       │
     │ sessions  │  │           │  │  memories   │
     └───────────┘  └───────────┘  └─────────────┘
```

## Tabelas Completas

```sql
-- =============================================
-- USUÁRIOS
-- =============================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255),
    phone           VARCHAR(50),
    role            VARCHAR(20) DEFAULT 'client' CHECK (role IN ('superadmin', 'admin', 'reseller', 'client')),
    is_active       BOOLEAN DEFAULT TRUE,
    is_2fa_enabled  BOOLEAN DEFAULT FALSE,
    totp_secret     VARCHAR(255),
    avatar_url      TEXT,
    last_login_at   TIMESTAMPTZ,
    login_attempts  INT DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- =============================================
-- PLANOS
-- =============================================
CREATE TABLE plans (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(100) NOT NULL,
    slug                VARCHAR(50) UNIQUE NOT NULL,
    description         TEXT,
    price_monthly       DECIMAL(10,2) NOT NULL,
    price_yearly        DECIMAL(10,2),
    currency            VARCHAR(3) DEFAULT 'BRL',
    max_bots            INT DEFAULT 1,
    max_messages_month  INT DEFAULT 1000,
    max_commands        INT DEFAULT 50,
    max_file_size_mb    INT DEFAULT 5,
    max_memory_items    INT DEFAULT 100,
    has_llm             BOOLEAN DEFAULT FALSE,
    llm_provider        VARCHAR(50),
    llm_model           VARCHAR(100),
    llm_max_tokens      INT DEFAULT 2048,
    has_media           BOOLEAN DEFAULT FALSE,
    has_pdf             BOOLEAN DEFAULT FALSE,
    has_image           BOOLEAN DEFAULT FALSE,
    has_audio           BOOLEAN DEFAULT FALSE,
    has_transcription   BOOLEAN DEFAULT FALSE,
    has_flora           BOOLEAN DEFAULT FALSE,
    flora_model         VARCHAR(100),
    has_custom_commands BOOLEAN DEFAULT FALSE,
    has_automations     BOOLEAN DEFAULT FALSE,
    has_webhooks        BOOLEAN DEFAULT FALSE,
    has_analytics       BOOLEAN DEFAULT FALSE,
    has_priority_support BOOLEAN DEFAULT FALSE,
    has_whitelabel      BOOLEAN DEFAULT FALSE,
    has_api_access      BOOLEAN DEFAULT FALSE,
    has_multi_device    BOOLEAN DEFAULT FALSE,
    is_active           BOOLEAN DEFAULT TRUE,
    is_public           BOOLEAN DEFAULT TRUE,
    display_order       INT DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- ASSINATURAS
-- =============================================
CREATE TABLE subscriptions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id),
    plan_id             UUID NOT NULL REFERENCES plans(id),
    status              VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'cancelled', 'expired', 'trial')),
    billing_cycle       VARCHAR(10) DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'yearly')),
    trial_ends_at       TIMESTAMPTZ,
    current_period_start TIMESTAMPTZ,
    current_period_end  TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    payment_method      VARCHAR(50),
    payment_provider    VARCHAR(50),
    external_subscription_id VARCHAR(255),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- =============================================
-- LICENÇAS
-- =============================================
CREATE TABLE licenses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id),
    license_key     VARCHAR(64) UNIQUE NOT NULL,
    key_hash        VARCHAR(128) NOT NULL,
    signature       VARCHAR(512) NOT NULL,
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'revoked', 'expired')),
    device_fingerprint VARCHAR(255),
    activated_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ NOT NULL,
    last_validated_at TIMESTAMPTZ,
    max_validations INT DEFAULT 100,
    validation_count INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_licenses_key ON licenses(license_key);
CREATE INDEX idx_licenses_subscription ON licenses(subscription_id);
CREATE INDEX idx_licenses_status ON licenses(status);

-- =============================================
-- BOTS
-- =============================================
CREATE TABLE bots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id      UUID NOT NULL REFERENCES licenses(id),
    name            VARCHAR(100) NOT NULL,
    avatar_url      TEXT,
    prompt          TEXT NOT NULL,
    personality     VARCHAR(50) DEFAULT 'friendly',
    tone            VARCHAR(50) DEFAULT 'warm',
    language        VARCHAR(10) DEFAULT 'pt-BR',
    welcome_message TEXT,
    farewell_message TEXT,
    away_message    TEXT,
    business_hours  JSONB,
    timezone        VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    preferred_llm   VARCHAR(50),
    temperature     FLOAT DEFAULT 0.7,
    max_tokens      INT DEFAULT 1024,
    is_active       BOOLEAN DEFAULT TRUE,
    is_connected    BOOLEAN DEFAULT FALSE,
    config          JSONB DEFAULT '{}',
    version         INT DEFAULT 1,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bots_license ON bots(license_id);

-- =============================================
-- SESSÕES WHATSAPP
-- =============================================
CREATE TABLE whatsapp_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID NOT NULL REFERENCES bots(id),
    session_name    VARCHAR(100) NOT NULL,
    phone_number    VARCHAR(20),
    qr_code         TEXT,
    status          VARCHAR(20) DEFAULT 'disconnected' CHECK (status IN ('disconnected', 'connecting', 'connected', 'qr_ready', 'error')),
    connected_at    TIMESTAMPTZ,
    disconnected_at TIMESTAMPTZ,
    last_activity   TIMESTAMPTZ,
    device_info     JSONB,
    error_log       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_wa_sessions_bot ON whatsapp_sessions(bot_id);
CREATE INDEX idx_wa_sessions_status ON whatsapp_sessions(status);

-- =============================================
-- INTENTS
-- =============================================
CREATE TABLE intents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID NOT NULL REFERENCES bots(id),
    tag             VARCHAR(100) NOT NULL,
    patterns        TEXT[] NOT NULL,
    responses       TEXT[] NOT NULL,
    priority        INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    requires_llm   BOOLEAN DEFAULT FALSE,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_intents_bot ON intents(bot_id);

-- =============================================
-- COMANDOS PERSONALIZADOS
-- =============================================
CREATE TABLE commands (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID NOT NULL REFERENCES bots(id),
    trigger         VARCHAR(255) NOT NULL,
    trigger_type    VARCHAR(20) DEFAULT 'keyword' CHECK (trigger_type IN ('keyword', 'regex', 'intent', 'schedule', 'webhook')),
    action          VARCHAR(50) NOT NULL,
    payload         JSONB NOT NULL,
    conditions      JSONB DEFAULT '{}',
    priority        INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    is_approved     BOOLEAN DEFAULT FALSE,
    version         INT DEFAULT 1,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_commands_bot ON commands(bot_id);

-- =============================================
-- MEMÓRIA DO BOT
-- =============================================
CREATE TABLE bot_memories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID NOT NULL REFERENCES bots(id),
    contact_id      VARCHAR(100) NOT NULL,
    contact_name    VARCHAR(255),
    context         JSONB DEFAULT '{}',
    summary         TEXT,
    message_count   INT DEFAULT 0,
    first_contact   TIMESTAMPTZ DEFAULT NOW(),
    last_contact    TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memories_bot_contact ON bot_memories(bot_id, contact_id);

-- =============================================
-- MENSAGENS (LOG)
-- =============================================
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID NOT NULL REFERENCES bots(id),
    contact_id      VARCHAR(100) NOT NULL,
    direction       VARCHAR(10) CHECK (direction IN ('inbound', 'outbound')),
    content         TEXT,
    message_type    VARCHAR(20) DEFAULT 'text',
    media_url       TEXT,
    llm_provider    VARCHAR(50),
    llm_model       VARCHAR(100),
    llm_tokens_in   INT,
    llm_tokens_out  INT,
    llm_cost        DECIMAL(10,6),
    llm_latency_ms  INT,
    status          VARCHAR(20) DEFAULT 'sent',
    error           TEXT,
    sent_at         TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_bot ON messages(bot_id);
CREATE INDEX idx_messages_contact ON messages(contact_id);
CREATE INDEX idx_messages_sent_at ON messages(sent_at);

-- =============================================
-- USO DE LLM
-- =============================================
CREATE TABLE llm_usage (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID NOT NULL REFERENCES bots(id),
    provider        VARCHAR(50) NOT NULL,
    model           VARCHAR(100) NOT NULL,
    tokens_in       INT NOT NULL,
    tokens_out      INT NOT NULL,
    cost            DECIMAL(10,6) NOT NULL,
    latency_ms      INT,
    was_fallback    BOOLEAN DEFAULT FALSE,
    fallback_from   VARCHAR(50),
    task_type       VARCHAR(50),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_llm_usage_bot ON llm_usage(bot_id);
CREATE INDEX idx_llm_usage_created ON llm_usage(created_at);

-- =============================================
-- LOGS DE AUDITORIA
-- =============================================
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    action          VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(50),
    entity_id       UUID,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);

-- =============================================
-- EVENTOS DO SISTEMA
-- =============================================
CREATE TABLE system_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      VARCHAR(100) NOT NULL,
    severity        VARCHAR(20) DEFAULT 'info',
    entity_type     VARCHAR(50),
    entity_id       UUID,
    payload         JSONB,
    is_resolved     BOOLEAN DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- BACKUPS
-- =============================================
CREATE TABLE backups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID REFERENCES bots(id),
    backup_type     VARCHAR(20) DEFAULT 'full',
    file_path       TEXT NOT NULL,
    file_size       BIGINT,
    checksum        VARCHAR(128),
    is_encrypted    BOOLEAN DEFAULT TRUE,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- WEBHOOKS
-- =============================================
CREATE TABLE webhooks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id          UUID NOT NULL REFERENCES bots(id),
    url             TEXT NOT NULL,
    secret          VARCHAR(255),
    events          TEXT[] NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    last_triggered  TIMESTAMPTZ,
    last_status     INT,
    failure_count   INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- TICKETS DE SUPORTE
-- =============================================
CREATE TABLE support_tickets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    bot_id          UUID REFERENCES bots(id),
    subject         VARCHAR(255) NOT NULL,
    description     TEXT,
    status          VARCHAR(20) DEFAULT 'open',
    priority        VARCHAR(10) DEFAULT 'normal',
    assigned_to     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- =============================================
-- TEMPLATES DE BOT
-- =============================================
CREATE TABLE bot_templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(50) UNIQUE NOT NULL,
    description     TEXT,
    category        VARCHAR(50),
    prompt          TEXT NOT NULL,
    personality     VARCHAR(50),
    tone            VARCHAR(50),
    intents         JSONB NOT NULL,
    commands        JSONB DEFAULT '[]',
    config          JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT TRUE,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- REVENDEDORES
-- =============================================
CREATE TABLE resellers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    company_name    VARCHAR(255),
    commission_rate DECIMAL(5,2) DEFAULT 20.00,
    custom_domain   VARCHAR(255),
    whitelabel_config JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```
