# 🌸 FLORA PLATFORM — Telas do App Administrador

## Mapa de Telas (15 telas)

```
APP ADMINISTRADOR — MAPA DE TELAS
═══════════════════════════════════

1.  Splash Screen
2.  Login
3.  Dashboard Principal
4.  Lista de Bots
5.  Editor de Bot (Wizard em 8 etapas)
6.  Gerenciador de Licenças
7.  Gerenciador de Clientes
8.  Gerenciador de Planos
9.  Analytics
10. Logs & Auditoria
11. Backup & Restore
12. Templates
13. Suporte
14. Configurações
15. Teste de Bot (Sandbox)
```

## Detalhamento de Cada Tela

### 1. Splash Screen
- Logo Flora animada (fade in + scale)
- Barra de progresso vermelha
- Verifica sessão salva → pula pro dashboard se logado
- Dark premium com vermelho
- Duração: 2-3 segundos

### 2. Login
- Campo email (com ícone)
- Campo senha (com toggle mostrar/ocultar)
- Botão "Entrar" (vermelho, full width)
- Link "Esqueci minha senha"
- Se 2FA habilitado: tela extra com campo TOTP
- Fundo glassmorphism
- Validação em tempo real

### 3. Dashboard Principal
```
┌─────────────────────────────────────────────────────────────┐
│ 🌸 FLORA ADMIN          🔍 Buscar    🔔 3    👤 Admin  ⚙️  │
├────────┬────────────────────────────────────────────────────┤
│        │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │
│ 📊     │  │Bots  │ │Client│ │Receit│ │Alert │             │
│ Dashb. │  │  12  │ │  8   │ │R$12k │ │  3   │             │
│        │  └──────┘ └──────┘ └──────┘ └──────┘             │
│ 🤖     │                                                    │
│ Bots   │  ┌──────────────────────────────────────────────┐ │
│        │  │  📈 Mensagens (últimos 30 dias)              │ │
│ 👥     │  │  ▁▂▃▅▇█▇▅▃▂▁▂▃▅▇█▇▅▃▂▁▂▃▅▇█▇▅▃            │ │
│ Client.│  │  1.247 hoje | 34.891 este mês               │ │
│        │  └──────────────────────────────────────────────┘ │
│ 🎫     │                                                    │
│ Ticket │  ┌────────────────────┐ ┌────────────────────┐    │
│        │  │ 💰 Receita Mensal  │ │ 🤖 Custo LLM      │    │
│ 📋     │  │ R$ 12.450,00      │ │ R$ 1.230,00       │    │
│ Licenç.│  │ ▲ 23% vs mês ant. │ │ ▼ 5% vs mês ant.  │    │
│        │  └────────────────────┘ └────────────────────┘    │
│ 📈     │                                                    │
│ Analyt.│  ┌──────────────────────────────────────────────┐ │
│        │  │ ⚡ Eventos Recentes                          │ │
│ 📝     │  │ • Bot "Pizzaria" conectou — 2 min atrás     │ │
│ Logs   │  │ • Licença FLORA-ABCD expira em 3 dias       │ │
│        │  │ • Cliente João fez upgrade para Pro          │ │
│ 💾     │  │ • LLM Groq indisponível (fallback Gemini)   │ │
│ Backup │  │ • Backup automático concluído — 1h atrás     │ │
│        │  └──────────────────────────────────────────────┘ │
│ 🎨     │                                                    │
│ Templ. │                                    [+ Novo Bot]   │
│        │                                                    │
│ ⚙️     │                                                    │
│ Config │                                                    │
└────────┴────────────────────────────────────────────────────┘
```

### 4. Lista de Bots
- Cards com: avatar, nome, status (conectado/desconectado), cliente, plano
- Filtros: todos, ativos, inativos, desconectados
- Busca por nome ou cliente
- Botão flutuante "+ Novo Bot"
- Swipe para ações rápidas (ativar, desativar, editar)

### 5. Editor de Bot (Wizard)

**5a. Perfil**
- Nome do bot
- Upload de avatar
- Número do WhatsApp
- Nome do cliente
- Email do cliente

**5b. Personalidade**
- System prompt (textarea grande)
- Personalidade: friendly, professional, casual, formal
- Tom: warm, neutral, enthusiastic, serious
- Idioma: pt-BR, en-US, es, etc.
- Emoji level: none, moderate, high

**5c. Intenções**
- Lista de intents com patterns e responses
- Botão "+ Nova Intent"
- Drag para reordenar
- Testar intent inline

**5d. Comandos**
- Lista de comandos personalizados
- Trigger, tipo, ação, condições
- Botão "+ Novo Comando"
- Sandbox para testar

**5e. Automações**
- Gatilho → Ação
- Condições (horário, plano, etc.)
- Visual estilo flowchart simples

**5f. Horários**
- Grid de dias da semana
- Horário de início/fim por dia
- Mensagem de fora de expediente
- Timezone

**5g. LLM**
- Provider (dropdown)
- Modelo (dropdown baseado no provider)
- Temperature (slider 0-1)
- Max tokens (number input)
- Fallback chain (drag to order)

**5h. Revisão**
- Resumo de todas as configurações
- Botão "Testar" (abre sandbox)
- Botão "Salvar e Ativar"

### 6. Gerenciador de Licenças
- Tabela: chave, cliente, plano, status, expiração
- Filtros: ativa, suspensa, revogada, expirada
- Botão "Gerar Licença"
- Ações: revogar, renovar, suspender, exportar
- Busca por chave ou cliente

### 7. Gerenciador de Clientes
- Tabela: nome, email, plano, status, bots
- Perfil do cliente com detalhes completos
- Histórico de ações
- Botão "Novo Cliente"

### 8. Gerenciador de Planos
- Cards por plano com features listadas
- Editor de plano (preço, limites, features)
- Toggle ativo/inativo
- Drag para reordenar exibição

### 9. Analytics
- Dashboard com gráficos matplotlib
- Mensagens por dia/semana/mês
- Custo de LLM por bot
- Receita por plano
- Top bots por uso
- Horários de pico
- Exportar relatório (Excel/PDF)

### 10. Logs & Auditoria
- Timeline de eventos
- Filtros: tipo, data, usuário, severidade
- Detalhes de cada evento (old_value → new_value)
- Exportar logs
- Busca full-text

### 11. Backup & Restore
- Lista de backups com data, tamanho, tipo
- Botão "Criar Backup Manual"
- Restaurar de backup (com confirmação)
- Agendar backups automáticos (diário/semanal)
- Download de backup

### 12. Templates
- Galeria de templates por categoria
- Preview do template (prompt, intents, commands)
- Botão "Novo Template"
- Aplicar template em bot existente
- Templates pré-definidos: restaurante, clínica, loja, advocacia, etc.

### 13. Suporte
- Lista de tickets (abertos, em progresso, resolvidos)
- Chat do ticket
- Atribuir ticket
- Responder
- Filtros por status e prioridade

### 14. Configurações
- Chaves de API das LLMs (com teste de conexão)
- Configurações de e-mail (SMTP)
- Webhooks globais
- Segurança (2FA, sessões ativas)
- Tema do app
- Notificações
- Idioma

### 15. Teste de Bot (Sandbox)
- Interface de chat simulado
- Enviar mensagem e ver resposta
- Painel debug: intent usada, LLM chamada, tokens, latência
- Modo debug toggle
- Histórico do teste
