# 🌸 FLORA PLATFORM — LLM Router

## Arquitetura do Router

```python
class LLMRouter:
    """
    Roteador inteligente de modelos de LLM.
    
    Política de seleção:
    1. Verificar plano do cliente (quais LLMs estão liberados)
    2. Verificar tipo da tarefa (chat, flora, summary, intent)
    3. Verificar complexidade (tokens, necessidade de raciocínio)
    4. Verificar custo disponível (budget do plano)
    5. Verificar latência necessária
    6. Selecionar melhor modelo
    7. Tentar → se falhar, fallback para próximo
    8. Registrar métricas
    """
    
    PROVIDERS = {
        'groq': {
            'models': [
                {'name': 'llama-3.1-8b-instant', 'speed': 'ultra', 'cost': 'free', 'context': 131072, 'quality': 'medium'},
                {'name': 'llama-3.1-70b-versatile', 'speed': 'fast', 'cost': 'free', 'context': 131072, 'quality': 'high'},
            ],
            'priority': 1,
        },
        'gemini': {
            'models': [
                {'name': 'gemini-1.5-flash', 'speed': 'fast', 'cost': 'low', 'context': 1048576, 'quality': 'high'},
                {'name': 'gemini-1.5-pro', 'speed': 'medium', 'cost': 'medium', 'context': 2097152, 'quality': 'very_high'},
            ],
            'priority': 2,
        },
        'openai': {
            'models': [
                {'name': 'gpt-4o-mini', 'speed': 'fast', 'cost': 'low', 'context': 131072, 'quality': 'high'},
                {'name': 'gpt-4o', 'speed': 'medium', 'cost': 'high', 'context': 131072, 'quality': 'very_high'},
            ],
            'priority': 3,
        },
        'anthropic': {
            'models': [
                {'name': 'claude-3-haiku', 'speed': 'fast', 'cost': 'low', 'context': 200000, 'quality': 'high'},
                {'name': 'claude-3-5-sonnet', 'speed': 'medium', 'cost': 'high', 'context': 200000, 'quality': 'very_high'},
            ],
            'priority': 4,
        },
        'ollama': {
            'models': [
                {'name': 'llama3:8b', 'speed': 'slow', 'cost': 'zero', 'context': 8192, 'quality': 'medium'},
                {'name': 'llama3:70b', 'speed': 'slow', 'cost': 'zero', 'context': 8192, 'quality': 'high'},
            ],
            'priority': 5,
        },
    }
    
    def route(self, task: 'Task', plan: 'Plan') -> 'ModelSelection':
        # 1. Filtrar por plano
        allowed = self._filter_by_plan(plan)
        
        # 2. Filtrar por tipo de tarefa
        suitable = self._filter_by_task(allowed, task)
        
        # 3. Filtrar por budget
        affordable = self._filter_by_budget(suitable, plan)
        
        # 4. Ordenar por prioridade (custo, velocidade, qualidade)
        ranked = self._rank_models(affordable, task)
        
        return ModelSelection(
            primary=ranked[0],
            fallbacks=ranked[1:3],
        )
    
    async def execute(self, selection: 'ModelSelection', messages: list) -> 'LLMResponse':
        for model in [selection.primary] + selection.fallbacks:
            try:
                response = await self._call_provider(model, messages)
                self._record_metrics(model, response, was_fallback=(model != selection.primary))
                return response
            except ProviderError as e:
                logger.warning(f"Provider {model.provider} failed: {e}")
                continue
        
        raise AllProvidersFailed("Nenhuma LLM disponível")
```

## Política por Plano

| Plano | LLMs Liberadas | Modelo Principal | Fallback Chain |
|---|---|---|---|
| Starter | Nenhuma | — | — |
| Basic | Nenhuma | — | — |
| Plus | Nenhuma | — | — |
| Pro | Groq | llama-3.1-70b | llama-3.1-8b |
| Master | Groq, Gemini, OpenAI | gpt-4o | gemini-1.5-pro → llama-3.1-70b |
| Elite | Todas exceto Enterprise | gpt-4o | claude-3-5-sonnet → gemini-1.5-pro |
| Enterprise | Todas + Ollama local | Configurável | Chain customizada |

## Seleção por Tipo de Tarefa

| Tarefa | Critério Principal | Modelo Preferido |
|---|---|---|
| Chat simples | Velocidade | Groq llama-3.1-8b |
| Chat complexo | Qualidade | gpt-4o |
| Flora AI | Custo + qualidade | gemini-1.5-flash |
| Resumo | Contexto longo | gemini-1.5-pro |
| Análise de intent | Velocidade | Groq llama-3.1-8b |
| Redação | Qualidade | claude-3-5-sonnet |
| Multimodal | Capacidade | gemini-1.5-pro |
| Modo offline | Disponibilidade | Ollama local |

## Estrutura de Custo (por 1K tokens)

| Provider | Modelo | Input | Output |
|---|---|---|---|
| Groq | llama-3.1-8b | $0.00 | $0.00 |
| Groq | llama-3.1-70b | $0.00 | $0.00 |
| Gemini | 1.5-flash | $0.00001 | $0.00004 |
| Gemini | 1.5-pro | $0.00125 | $0.005 |
| OpenAI | gpt-4o-mini | $0.00015 | $0.0006 |
| OpenAI | gpt-4o | $0.0025 | $0.01 |
| Anthropic | claude-3-haiku | $0.00025 | $0.00125 |
| Anthropic | claude-3.5-sonnet | $0.003 | $0.015 |
| DeepSeek | deepseek-chat | $0.00014 | $0.00028 |
| Ollama | qualquer | $0.00 | $0.00 |

## Rate Limiting por Plano

| Plano | Requisições/min | Tokens/dia | Custo máx/mês |
|---|---|---|---|
| Pro | 30 | 100.000 | $5 |
| Master | 60 | 500.000 | $20 |
| Elite | 120 | 2.000.000 | $50 |
| Enterprise | 300 | 10.000.000 | $200 |
