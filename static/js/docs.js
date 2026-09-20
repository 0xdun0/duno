/**
 * static/js/docs.js — Interatividade da Central de Documentação DUNO
 * Busca instantânea, atalhos de teclado e cópia de blocos de código.
 */

document.addEventListener('DOMContentLoaded', () => {
  // ── 1. BUSCA INSTANTÂNEA NO HERO ──────────────────────────────────────────
  const searchInput = document.getElementById('docs-search-input');
  const searchDropdown = document.getElementById('docs-search-dropdown');
  const searchForm = document.getElementById('docs-search-form');
  const searchPills = document.querySelectorAll('.js-docs-pill');

  let debounceTimer = null;

  async function performSearch(query) {
    if (!query || query.trim().length < 2) {
      if (searchDropdown) {
        searchDropdown.classList.remove('active');
        searchDropdown.innerHTML = '';
      }
      return;
    }

    try {
      const res = await fetch(`/api/docs/search?q=${encodeURIComponent(query.trim())}`);
      const data = await res.json();

      if (!searchDropdown) return;

      if (data.length === 0) {
        searchDropdown.innerHTML = `
          <div style="padding: 18px; text-align: center; color: var(--ink-2); font-size: 0.88rem;">
            Nenhum artigo encontrado para "<strong>${escapeHtml(query)}</strong>".
          </div>
        `;
        searchDropdown.classList.add('active');
        return;
      }

      let html = '';
      data.forEach(item => {
        html += `
          <a href="/docs/${item.slug}" class="docs-search-result-item">
            <div class="docs-search-result-icon">
              <i class="nf ${item.icon || 'nf-md-file_document_outline'}"></i>
            </div>
            <div style="flex: 1; min-width: 0;">
              <div class="docs-search-result-category">${escapeHtml(item.category_title)}</div>
              <div class="docs-search-result-title">${escapeHtml(item.title)}</div>
              <div class="docs-search-result-desc">${escapeHtml(item.snippet || item.desc)}</div>
            </div>
          </a>
        `;
      });

      searchDropdown.innerHTML = html;
      searchDropdown.classList.add('active');
    } catch (e) {
      console.error('Erro na busca de docs:', e);
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        performSearch(e.target.value);
      }, 180);
    });

    // Fecha ao clicar fora
    document.addEventListener('click', (e) => {
      if (searchDropdown && !searchDropdown.contains(e.target) && e.target !== searchInput) {
        searchDropdown.classList.remove('active');
      }
    });

    // Tecla ESC fecha busca
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && searchDropdown) {
        searchDropdown.classList.remove('active');
      }
    });
  }

  // Atalho de foco com '/' ou 'Ctrl+K'
  document.addEventListener('keydown', (e) => {
    if ((e.key === '/' || (e.ctrlKey && e.key.toLowerCase() === 'k')) && searchInput && document.activeElement !== searchInput) {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  });

  // Pills de sugestão preenchem a busca e navegam
  searchPills.forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.preventDefault();
      const q = pill.getAttribute('data-query');
      if (searchInput) {
        searchInput.value = pill.textContent.trim();
        performSearch(q);
      }
    });
  });

  if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const firstResult = searchDropdown ? searchDropdown.querySelector('.docs-search-result-item') : null;
      if (firstResult) {
        window.location.href = firstResult.href;
      } else if (searchInput && searchInput.value.trim()) {
        performSearch(searchInput.value.trim());
      }
    });

    // ── ROBÔ ASSISTENTE: ABRE E FECHA O OLHO AO POSICIONAR O MOUSE OU DIGITAR ──
    const robotEl = document.getElementById('docs-search-robot');
    if (robotEl && searchForm) {
      let blinkTimer = null;
      const triggerEyeBlink = () => {
        robotEl.classList.remove('robot-blinking');
        void robotEl.offsetWidth;
        robotEl.classList.add('robot-blinking');
        clearTimeout(blinkTimer);
        blinkTimer = setTimeout(() => {
          robotEl.classList.remove('robot-blinking');
        }, 700);
      };

      searchForm.addEventListener('mouseenter', triggerEyeBlink);
      robotEl.addEventListener('mouseenter', triggerEyeBlink);
      if (searchInput) {
        searchInput.addEventListener('input', triggerEyeBlink);
      }
    }
  }

  // ── 2. CÓPIA DE BLOCOS DE CÓDIGO NO LEITOR ───────────────────────────────
  const codeBlocks = document.querySelectorAll('.docs-prose pre');
  codeBlocks.forEach(pre => {
    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.className = 'docs-code-copy-btn';
    copyBtn.innerHTML = '<i class="nf nf-md-content_copy"></i> Copiar';
    copyBtn.setAttribute('title', 'Copiar código');

    copyBtn.style.position = 'absolute';
    copyBtn.style.top = '8px';
    copyBtn.style.right = '8px';
    copyBtn.style.padding = '4px 10px';
    copyBtn.style.fontSize = '0.74rem';
    copyBtn.style.fontFamily = 'var(--font-mono)';
    copyBtn.style.background = 'rgba(255, 255, 255, 0.08)';
    copyBtn.style.border = '1px solid rgba(255, 255, 255, 0.15)';
    copyBtn.style.borderRadius = '4px';
    copyBtn.style.color = '#e6edf3';
    copyBtn.style.cursor = 'pointer';
    copyBtn.style.transition = 'all 0.15s ease';

    pre.style.position = 'relative';
    pre.appendChild(copyBtn);

    copyBtn.addEventListener('click', async () => {
      const codeEl = pre.querySelector('code');
      const text = codeEl ? codeEl.innerText : pre.innerText;
      try {
        await navigator.clipboard.writeText(text);
        copyBtn.innerHTML = '<i class="nf nf-fa-check" style="color: #10b981;"></i> Copiado!';
        setTimeout(() => {
          copyBtn.innerHTML = '<i class="nf nf-md-content_copy"></i> Copiar';
        }, 2000);
      } catch (err) {
        console.error('Falha ao copiar:', err);
      }
    });
  });
});
