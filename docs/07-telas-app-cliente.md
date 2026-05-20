# 🌸 FLORA PLATFORM — Telas do App do Cliente

## Mapa de Telas (13 telas)

```
APP DO CLIENTE — MAPA DE TELAS
════════════════════════════════

1.  Splash Screen
2.  Boas-vindas / Onboarding
3.  Validação de Licença
4.  Dashboard do Bot
5.  Conexão WhatsApp
6.  Chat com o Bot (Teste)
7.  Flora AI (Chat)
8.  Meu Plano
9.  Relatórios Simples
10. Configurações do Bot
11. Suporte
12. Conta
13. Avisos e Notificações
```

## Detalhamento de Cada Tela

### 1. Splash Screen
- Logo Flora animada
- Loading spinner vermelho
- Verifica licença salva → pula pro dashboard se válida

### 2. Boas-vindas / Onboarding
- 3 slides com ilustrações:
  - Slide 1: "Bem-vindo à Flora! 🌸" + descrição
  - Slide 2: "Conecte seu WhatsApp em segundos" + ilustração QR
  - Slide 3: "A Flora está aqui para ajudar!" + avatar da Flora
- Botão "Começar"
- Indicadores de página (dots)

### 3. Validação de Licença
```
┌─────────────────────────────────────────────────┐
│                                                   │
│              🌸                                   │
│         FLORA PLATFORM                            │
│                                                   │
│  ┌───────────────────────────────────────────┐   │
│  │  Digite sua licença                        │   │
│  │                                            │   │
│  │  ┌──────────────────────────────────────┐ │   │
│  │  │ FLORA-XXXX-XXXX-XXXX-XXXX            │ │   │
│  │  └──────────────────────────────────────┘ │   │
│  │                                            │   │
│  │  [     VALIDAR LICENÇA     ]              │   │
│  │                                            │   │
│  │  ── ou escaneie o QR Code ──              │   │
│  │                                            │   │
│  │  Não tem licença? Fale conosco →          │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
└─────────────────────────────────────────────────┘
```

- Campo para digitar a chave (auto-formatar: FLORA-XXXX-XXXX-XXXX-XXXX)
- Validação em tempo real do formato
- Botão "Validar" com loading animado
- Sucesso → dashboard | Erro → mensagem clara
- Opção de escanear QR Code da licença

### 4. Dashboard do Bot
```
┌─────────────────────────────────────────────────────────────┐
│ 🌸 Meu Bot              💬 Flora    🔔 2    👤 João       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  🤖 Assistente Pizzaria          ● Conectado          │  │
│  │  Plano Pro 💎                    Expira em 23 dias    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Mensagens │ │Contatos  │ │Hoje      │ │Esta Sem. │       │
│  │  1.247   │ │  89     │ │  156     │ │  1.089   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  📊 Mensagens por dia                                 │  │
│  │  ▁▂▃▅▇█▇▅▃▂▁▂▃▅▇█▇▅▃▂▁▂▃▅▇█▇▅▃                     │  │
│  │  Seg Ter Qua Qui Sex Sáb Dom                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ⚡ Ações Rápidas                                     │  │
│  │  [💬 Testar Bot]  [📱 Reconectar]  [🌸 Falar c/ Flora]│  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  🌸 Dica da Flora                                     │  │
│  │  "Que tal adicionar um comando de cardápio?           │  │
│  │   Toque aqui para eu te ajudar! 🌟"                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  📋 Seu Plano Pro                                     │  │
│  │  ✅ LLM (Groq)     ✅ Flora AI     ✅ PDF            │  │
│  │  ✅ Memória        ✅ 5.000 msg/mês                   │  │
│  │  🔒 Webhooks       🔒 White-label                    │  │
│  │  [Ver todos os recursos →]                            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  🏠 Home    🤖 Bot    🌸 Flora    📊 Dados    ⚙️ Config   │
└─────────────────────────────────────────────────────────────┘
```

### 5. Conexão WhatsApp
- QR Code centralizado (grande, com borda vermelha)
- Instruções passo a passo:
  1. Abra o WhatsApp no celular
   2. Toque em "Aparelhos conectados"
   3. Toque em "Conectar um aparelho"
   4. Escaneie este QR Code
- Status: aguardando / conectado / expirado
- Botão "Gerar novo QR" se expirar
- Animação de scan

### 6. Chat com o Bot (Teste)
- Interface de chat estilo WhatsApp
- Balões de mensagem (enviada/recebida)
- Input de texto + botão enviar
- Indicador de digitação
- Últimas conversas com contatos

### 7. Flora AI (Chat)
- Interface de chat dedicada com avatar da Flora
- Flora responde sobre o sistema
- Sugestões rápidas (chips):
  - "Como conecto o WhatsApp?"
  - "Quais recursos meu plano tem?"
  - "Como crio um comando?"
  - "Meu bot está desconectado"
  - "Quero fazer upgrade"
- Histórico de conversas com Flora
- Streaming de resposta (letra por letra)

### 8. Meu Plano
- Nome do plano com badge colorido
- Features disponíveis (✅ verde)
- Features bloqueadas (🔒 cinza)
- Barra de uso atual vs limites:
  - Mensagens: 1.247 / 5.000 (49%)
  - Comandos: 12 / 50 (24%)
  - Memória: 45 / 100 (45%)
- Botão "Fazer Upgrade" (abre chat com Flora)
- Comparação com outros planos

### 9. Relatórios Simples
- Gráfico de mensagens por dia (barras)
- Top 5 contatos mais ativos
- Horários de pico (heatmap)
- Mensagens enviadas vs recebidas
- Exportar (se plano permitir)

### 10. Configurações do Bot
- Nome do bot (editável se plano permitir)
- Mensagem de boas-vindas
- Horário de funcionamento
- Mensagem de ausência
- Toggle: responder grupos (se plano permitir)
- Toggle: salvar mídia
- (campos limitados pelo plano — bloqueados com 🔒)

### 11. Suporte
- Chat com Flora (atalho)
- FAQ expansível
- Botão "Abrir Ticket"
- Lista de tickets com status
- Detalhe do ticket com chat

### 12. Conta
- Dados pessoais (nome, email)
- Licença (chave, validade, copiar chave)
- Dispositivos conectados
- Botão "Sair" (confirmação)
- Botão "Excluir conta" (vermelho, confirmação dupla)

### 13. Avisos e Notificações
- Lista de notificações com ícones:
  - 🔴 Expiração de licença (< 7 dias)
  - 🟡 Bot desconectado
  - 🔵 Atualização disponível
  - 🌸 Dica da Flora
  - 💰 Cobrança realizada
- Marcar como lida
- Limpar todas
