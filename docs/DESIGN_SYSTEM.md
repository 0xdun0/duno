# Identidade Visual & Design System — DUNO

O **DUNO Design System** adota uma linguagem visual moderna, sóbria e focada em engenharia, inspirada na estética do **Walkie** e do **Obsidian**. A premissa central é o minimalismo de alto impacto, contraste cirúrgico e ausência total de bibliotecas pesadas de terceiros (Tailwind, Bootstrap).

---

## 1. Princípios de Design

1. **Evolua a Plataforma, Não Redesenhe:** Qualquer nova tela deve parecer que sempre fez parte do ecossistema do DUNO.
2. **Cores Harmoniosas & Sem Ruído:** Base neutra escura/clara com destaques em laranja elétrico (`var(--orange)`), verde menta para sucessos e azul ciano para dados de telemetria.
3. **Padrão Oficial de Ícones:** **Nerd Fonts** (`<i class="nf nf-..."></i>`). É estritamente proibido o uso de emojis crus ou imagens geradas por IA no lugar de ícones de sistema.
4. **Tipografia Técnica:** Fontes de alta legibilidade (Inter / Outfit) para leitura e monoespaçadas (JetBrains Mono / Fira Code) para dados e comandos.

---

## 2. Tokens de Cor & Variáveis CSS

As variáveis globais são declaradas em `static/css/duno.css` e suportam troca dinâmica de tema via `[data-theme="dark"]`:

### Tema Escuro (Padrão — Dark Mode Obsidian)
```css
[data-theme="dark"] {
  --bg: #0d1117;              /* Fundo principal da viewport */
  --bg-card: #161b22;         /* Superfície de cards e modais */
  --bg-subtle: #21262d;       /* Badges, inputs e áreas secundárias */
  --ink: #f0f6fc;             /* Texto primário de alto contraste */
  --ink-2: #8b949e;           /* Subtítulos, metadados e kickers */
  --ink-3: #6e7681;           /* Bordas sutis e texto desabilitado */
  --line: #30363d;            /* Linhas divisórias estruturais */
  --line-highlight: #ff5a1f;  /* Borda de foco ativa */
  --orange: #ff5a1f;          /* Laranja elétrico oficial DUNO */
  --orange-glow: rgba(255, 90, 31, 0.25);
}
```

### Tema Claro (Walkie Soft Paper)
```css
:root {
  --bg: #F7F4EE;              /* Papel quente suave */
  --bg-card: #FFFFFF;         /* Superfície branca pura */
  --bg-subtle: #EFECE4;       /* Cinza aquecido */
  --ink: #111110;             /* Preto nanquim */
  --ink-2: #6E6D68;           /* Cinza editorial */
  --ink-3: #9E9D96;           /* Linhas e separadores */
  --line: #E2DFD7;            /* Borda sutil */
  --orange: #FF4F00;          /* Laranja queimado */
  --orange-glow: rgba(255, 79, 0, 0.20);
}
```

---

## 3. Tipografia

* **Fonte Principal (Sans-Serif):** `'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
* **Fonte Técnica (Monospace):** `'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, monospace`

---

## 4. Componentes Canônicos

### Botões (`.btn`)
* `.btn.btn-primary`: Fundo `var(--orange)`, texto branco, raio de 6px, transição de elevação de 2px no hover.
* `.btn.btn-secondary`: Fundo `var(--bg-subtle)`, borda `1px solid var(--line)`, texto `var(--ink)`.
* `.btn.btn-ghost`: Transparente, borda sutil, foco em ícone.

### Pílulas & Badges (`.pill-badge`)
Usados para exibir tags, status e categorias técnicas:
* `.pill-badge-orange`: Destaques, módulos ativos e novidades.
* `.pill-badge-blue`: Redes, DNS e protocolos.
* `.pill-badge-green`: Status publicado, acertos e conformidade.
* `.pill-badge-red`: Alertas críticos, exploits e falhas.
