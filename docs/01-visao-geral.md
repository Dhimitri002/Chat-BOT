# 🌸 FLORA PLATFORM — Visão Geral do Produto

## O Que É

A **Flora Platform** é uma fábrica de chatbots para WhatsApp baseada em assinatura. Você cria, configura e gerencia bots profissionais. Seus clientes compram licenças, conectam o WhatsApp por QR Code e têm um bot funcionando — de simples (regras) a inteligente (LLMs). A **Flora AI** é a assistente embutida que guia o cliente dentro do app.

## Proposta de Valor

| Para você (admin) | Para o cliente |
|---|---|
| Receita recorrente previsível | Bot profissional sem programar |
| Controle total de todos os bots | Conexão WhatsApp em 30 segundos |
| Escalar sem aumentar custo operacional | Suporte da Flora AI 24/7 |
| Margem alta (custo LLM vs preço plano) | Recursos crescem com o plano |
| White-label e revenda | Interface bonita e simples |

## Modelo de Negócio

```
Receita = Σ (clientes_ativos × preço_plano) - custo_LLM - infra

Margem saudável porque:
- Planos sem LLM = custo quase zero
- Planos com LLM = markup de 3-10x sobre custo real
- Enterprise = preço premium com custo marginal baixo
- Revenda = você lucra, revendedor lucra
```

## Diferenciais Competitivos

1. **Dois apps nativos** (Kivy/KivyMD) — não é web app disfarçado
2. **Flora AI integrada** — assistente que reduz churn e suporte
3. **LLM Router inteligente** — custo otimizado por plano
4. **Licença com assinatura digital** — anti-pirataria realasass
5. **White-label nativo** — revendedores têm marca própria
6. **Modo offline** — Ollama local para clientes enterprise
7. **QR Code pairing** — zero configuração técnica pro cliente

## Arquitetura de Alto Nível

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLORA PLATFORM                              │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  APP ADMIN   │    │  APP CLIENTE │    │   BACKEND API    │   │
│  │  (KivyMD)    │    │  (KivyMD)    │    │   (FastAPI)      │   │
│  │              │    │              │    │                  │   │
│  │ • Cria bots  │    │ • Valida     │    │ • Valida licença │   │
│  │ • Gera       │    │   licença    │    │ • Autentica      │   │
│  │   licenças   │    │ • QR Code    │    │ • Roteia LLM     │   │
│  │ • Gerencia   │    │ • Conversa   │    │ • Gerencia bots  │   │
│  │   clientes   │    │ • Flora AI   │    │ • Logs/Auditoria │   │
│  │ • Métricas   │    │ • Relatórios │    │ • Billing        │   │
│  │ • Backup     │    │ • Planos     │    │ • Notificações   │   │
│  └──────┬───────┘    └──────┬───────