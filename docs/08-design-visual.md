# 🌸 FLORA PLATFORM — Design Visual

## Paleta de Cores — Dark Premium (Padrão)

```
Fundo principal:     #0A0A0F (quase preto)
Fundo cards:         #12121A (cinza muito escuro)
Fundo elevação:      #1A1A25 (cinza escuro)
Bordas:              #2A2A3A (cinza médio)

Texto primário:      #FFFFFF (branco)
Texto secundário:    #A0A0B8 (cinza claro)
Texto terciário:     #6A6A80 (cinza apagado)

Destaque principal:  #E63946 (vermelho Flora)
Destaque hover:      #FF4D5A (vermelho claro)
Destaque suave:      #3D1A1A (vermelho escuro)

Sucesso:             #2ECC71 (verde)
Aviso:               #F39C12 (amarelo/laranja)
Erro:                #E74C3C (vermelho)
Info:                #3498DB (azul)

Glassmorphism:
  background:        rgba(18, 18, 26, 0.7)
  backdrop-filter:   blur(20px)
  border:            1px solid rgba(255, 255, 255, 0.08)
```

## Gradientes

```
Principal:           linear-gradient(135deg, #E63946, #FF6B6B)
Cards:               linear-gradient(145deg, #12121A, #1A1A25)
Flora:               linear-gradient(135deg, #E63946, #C0392B)
Sucesso:             linear-gradient(135deg, #2ECC71, #27AE60)
```

## Tipografia

```
Fonte títulos:       Inter / Montserrat (Bold 700)
Fonte corpo:         Inter / Roboto (Regular 400, Medium 500)
Fonte mono:          JetBrains Mono (Regular)

Tamanhos:
  H1:                28sp
  H2:                22sp
  H3:                18sp
  Body:              14sp
  Caption:           12sp
  Small:             10sp
```

## Espaçamento (8dp grid)

```
Padding cards:       16dp
Gap entre cards:     12dp
Padding tela:        16dp
Margin seções:       24dp
Border radius cards: 16dp
Border radius botões: 12dp
Border radius modais: 24dp
Altura botões:       48dp
Altura inputs:       52dp
```

## Sombras

```
Cards:               0 4px 24px rgba(0, 0, 0, 0.4)
Botões:              0 2px 12px rgba(230, 57, 70, 0.3)
Float:               0 8px 32px rgba(0, 0, 0, 0.5)
Modais:              0 16px 64px rgba(0, 0, 0, 0.6)
```

## Componentes de UI

### Botões

```
Primary:
  - Fundo: gradiente vermelho
  - Texto: branco, bold
  - Radius: 12dp
  - Altura: 48dp
  - Sombra: 0 2px 12px rgba(230, 57, 70, 0.3)
  - Hover: scale(1.02), brilho aumentado
  - Pressed: scale(0.98)

Secondary:
  - Borda: 1px vermelho
  - Texto: vermelho
  - Fundo: transparente
  - Radius: 12dp

Ghost:
  - Sem borda
  - Texto: vermelho
  - Fundo: transparente

Danger:
  - Fundo: #C0392B
  - Texto: branco

Icon Button:
  - Circular, 48dp
  - Fundo: #1A1A25
  - Ícone: vermelho
```

### Cards

```
Default:
  - Fundo: #12121A
  - Borda: 1px solid #2A2A3A
  - Radius: 16dp
  - Padding: 16dp

Glass:
  - Fundo: rgba(18, 18, 26, 0.7)
  - Backdrop blur: 20dp
  - Borda: 1px solid rgba(255, 255, 255, 0.08)
  - Radius: 16dp

Highlight:
  - Borda: 1px solid rgba(230, 57, 70, 0.3)
  - Glow: 0 0 20px rgba(230, 57, 70, 0.1)

Stat Card:
  - Número grande (28sp, bold)
  - Label pequeno (12sp, secundário)
  - Ícone no canto
```

### Inputs

```
Default:
  - Fundo: #1A1A25
  - Borda: 1px solid #2A2A3A
  - Radius: 12dp
  - Altura: 52dp
  - Padding: 16dp
  - Focus: borda vermelho, glow suave
  - Placeholder: #6A6A80

Search:
  - Ícone lupa à esquerda
  - Fundo elevado
  - Radius: 24dp (pill shape)

Textarea:
  - Auto-resize
  - Min height: 100dp
  - Max height: 300dp
```

### Loading States

```
Spinner:
  - Anel vermelho giratório
  - Tamanho: 32dp

Skeleton:
  - Blocos pulsantes cinza (#1A1A25 → #2A2A3A)
  - Radius: 8dp
  - Animação: pulse 1.5s infinite

Dots:
  - 3 pontos vermelhos pulsantes
  - Animação: bounce

Progress:
  - Barra vermelha com porcentagem
  - Fundo: #1A1A25
  - Radius: 4dp
  - Altura: 8dp
```

### States Vazios

```
Empty:
  - Ilustração central (SVG)
  - Título: "Nada aqui ainda"
  - Subtítulo: mensagem amigável
  - Botão de ação principal

Error:
  - Ícone de erro (vermelho)
  - Mensagem clara
  - Botão "Tentar novamente"

Success:
  - Check animado (verde)
  - Mensagem de sucesso

Offline:
  - Ícone wifi off
  - "Você está offline"
  - Botão "Reconectar"
```

### Navegação

```
Bottom Bar (5 itens):
  - Fundo: glassmorphism
  - Altura: 64dp
  - Ícones: 24dp
  - Label: 10sp
  - Ativo: vermelho
  - Inativo: #6A6A80
  - Indicador: dot vermelho sob o ativo

Sidebar:
  - Largura: 240dp (expandido) / 64dp (colapsado)
  - Fundo: #0A0A0F
  - Ícones + labels
  - Ativo: fundo vermelho suave, texto vermelho

Tabs:
  - Indicador vermelho sob o ativo (2dp height)
  - Texto ativo: branco
  - Texto inativo: #6A6A80
  - Animação: slide indicator
```

## Temas Disponíveis

```
1. 🌑 Dark Premium (padrão)
    Fundo escuro, vermelho como destaque

2. ☀️ Light Elegance
    Fundo claro (#F5F5FA), vermelho como destaque
    Texto: #1A1A25
    Cards: #FFFFFF

3. 🌸 Flora Mode
    Tons de rosa/vermelho, acolhedor
    Fundo: #1A0A0F
    Destaque: #E63946

4. 💼 Corporativo
    Azul escuro + branco, profissional
    Fundo: #0A1628
    Destaque: #2563EB

5. 🌙 Neon
    Fundo muito escuro + neon accents
    Fundo: #050505
    Destaque: #FF0040
    Glow forte

6. 🎌 Anime
    Estilo japonês, cores vibrantes
    Fundo: #0F0A1A
    Destaque: #FF6B9D
    Secundário: #C084FC

7. ⬜ Minimalista
    Quase sem cor, só essencial
    Fundo: #0A0A0A
    Destaque: #FFFFFF
    Bordas: #1A1A1A
```

## Animações e Microinterações

```
Transições de tela:
  - Duration: 300ms
  - Easing: ease-in-out
  - Tipo: fade + slide up

Botões:
  - Press: scale(0.98), 100ms
  - Hover: scale(1.02), 150ms
  - Loading: spinner substitui texto

Cards:
  - Hover: elevação +4dp, 200ms
  - Press: scale(0.99), 100ms

Listas:
  - Entrada: stagger animation (50ms entre itens)
  - Saída: fade out 200ms

Pull to refresh:
  - Spinner vermelho
  - Threshold: 80dp

Toast/Notificação:
  - Entrada: slide down 300ms
  - Saída: fade out 200ms
  - Auto-dismiss: 4s

QR Code:
  - Scan line animation (loop)
  - Pulse quando aguardando
  - Check animado quando conectado
```

## Ícones

```
Estilo: Outlined (padrão), Filled (ativo)
Tamanho: 24dp (padrão), 20dp (pequeno), 32dp (grande)
Cor: herda do contexto

Biblioteca: Material Design Icons (MDI)
via kivymd.icon_definitions.md_icons
```

## Responsividade (Desktop)

```
Mobile (até 480dp):
  - Bottom navigation
  - Cards full width
  - Sidebar oculta (drawer)

Tablet (481dp - 1024dp):
  - Sidebar colapsável
  - Grid 2 colunas para cards

Desktop (1024dp+):
  - Sidebar fixa expandida
  - Grid 3-4 colunas
  - Modais centralizados (max 600dp)
```
