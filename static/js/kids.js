/**
 * static/js/kids.js — Motor Interativo da DUNO Kids
 * Gerenciamento de Mascote Guia (Tux), Missões em 3 Fases (Teoria + Lab + Checkpoint)
 * e Gamificação da Plataforma.
 */
(function() {
  'use strict';

  // ══════════════════════════════════════════════════════════════════════════════
  // 1. TUX MASCOT COMPANION & SPEECH BUBBLE (DASHBOARD & HUD)
  // ══════════════════════════════════════════════════════════════════════════════
  const heroSpeechBubble = document.getElementById('tux-speech-bubble');
  const heroBubbleText = document.getElementById('tux-bubble-text');
  const heroMascotImg = document.getElementById('tux-mascot-img');

  const companionWidget = document.getElementById('tux-companion-widget');
  const companionBtn = document.getElementById('tux-companion-btn');
  const companionBubble = document.getElementById('tux-companion-bubble');
  const companionClose = document.getElementById('tux-companion-close');
  const companionMsg = document.getElementById('tux-companion-msg');
  const companionSprite = document.getElementById('tux-companion-sprite');

  // 8 Dicas com ícones Nerd Fonts, cores e orientações de cibersegurança e Linux
  const COMPANION_TIPS = [
    {
      icon: 'nf-fa-shield',
      color: '#f43f5e',
      glow: 'rgba(244, 63, 94, 0.45)',
      name: 'SECURITY GUARD',
      tip: 'Fique atento! Nunca compartilhe suas senhas com ninguém, nem mesmo em jogos!'
    },
    {
      icon: 'nf-fa-coffee',
      color: '#06b6d4',
      glow: 'rgba(6, 182, 212, 0.45)',
      name: 'CYAN PAUSE',
      tip: 'Descanse a mente entre uma lição e outra. Aprender com calma fixa muito melhor!'
    },
    {
      icon: 'nf-md-terminal_box',
      color: '#d946ef',
      glow: 'rgba(217, 70, 239, 0.45)',
      name: 'TERMINAL PRO',
      tip: 'Errou um comando? Sem estresse! No terminal, errar é o primeiro passo para dominar a máquina.'
    },
    {
      icon: 'nf-md-bug',
      color: '#84cc16',
      glow: 'rgba(132, 204, 22, 0.45)',
      name: 'BUG HUNTER',
      tip: 'Cuidado com links e anexos suspeitos! Eles podem esconder malwares querendo invadir seu PC.'
    },
    {
      icon: 'nf-md-rocket_launch',
      color: '#10b981',
      glow: 'rgba(16, 185, 129, 0.45)',
      name: 'STAR PILOT',
      tip: 'Brilhante! Você está subindo de nível e dominando os segredos do Linux e das Redes!'
    },
    {
      icon: 'nf-fa-bolt',
      color: '#ec4899',
      glow: 'rgba(236, 72, 153, 0.45)',
      name: 'FAST BYTE',
      tip: 'Chocado com a velocidade do terminal? Um único script de automação faz o trabalho de 100 cliques!'
    },
    {
      icon: 'nf-fa-globe',
      color: '#3b82f6',
      glow: 'rgba(59, 130, 246, 0.45)',
      name: 'NET ROAR',
      tip: 'A internet inteira conversa por protocolos como HTTP e TCP/IP. É uma orquestra global sincronizada!'
    },
    {
      icon: 'nf-fa-lock',
      color: '#ef4444',
      glow: 'rgba(239, 68, 68, 0.45)',
      name: 'LOCK MASTER',
      tip: 'Proteja seu navio digital! Ative o Firewall perimetral e use autenticação em 2 fatores (2FA).'
    }
  ];

  let companionIdx = 0;

  function updateCompanionNeon(idx) {
    const item = COMPANION_TIPS[idx % COMPANION_TIPS.length];
    if (companionWidget) {
      companionWidget.style.setProperty('--companion-color', item.color);
      companionWidget.style.setProperty('--companion-glow', item.glow);
    }
    if (companionSprite) {
      companionSprite.style.transform = 'scale(0.85)';
      setTimeout(() => {
        if (companionSprite.tagName === 'IMG') {
          // fallback
        } else {
          companionSprite.className = `nf ${item.icon} tux-companion-icon`;
          companionSprite.style.color = item.color;
        }
        companionSprite.style.transform = 'scale(1)';
      }, 120);
    }
    const speakerEl = companionBubble ? companionBubble.querySelector('.tux-companion-speaker') : null;
    if (speakerEl) {
      speakerEl.textContent = item.name + ':';
      speakerEl.style.color = item.color;
    }
    if (companionMsg) {
      companionMsg.textContent = item.tip;
    }
  }

  // Falas do Mascote Amarelo no Hero do Dashboard
  const YELLOW_CAT_HERO_TIPS = [
    "Estou devorando este livro! Vamos aprender tecnologia juntos?",
    "No terminal, você fala direto com o cérebro da máquina. Sem limites!",
    "Você sabia? O Kernel Linux comanda foguetes da NASA e os maiores servidores do mundo!",
    "Senhas fortes misturam letras, números e símbolos especiais. Nunca use 123456!",
    "O DNS é a agenda de contatos da web: traduz nomes em números de IP!"
  ];

  let yellowTipIdx = 0;
  if (heroBubbleText) {
    setInterval(() => {
      yellowTipIdx = (yellowTipIdx + 1) % YELLOW_CAT_HERO_TIPS.length;
      heroBubbleText.style.opacity = '0';
      setTimeout(() => {
        heroBubbleText.textContent = YELLOW_CAT_HERO_TIPS[yellowTipIdx];
        heroBubbleText.style.opacity = '1';
      }, 250);
    }, 9000);
  }

  // Interação com o Mascote Companheiro Flutuante (cada clique avança de dica e muda cor/ícone)
  if (companionBtn && companionBubble) {
    updateCompanionNeon(companionIdx);

    companionBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      companionIdx = (companionIdx + 1) % COMPANION_TIPS.length;
      updateCompanionNeon(companionIdx);
      companionBubble.style.display = 'block';
    });

    if (companionClose) {
      companionClose.addEventListener('click', (e) => {
        e.stopPropagation();
        companionBubble.style.display = 'none';
      });
    }

    // Fecha ao clicar fora
    document.addEventListener('click', (e) => {
      if (companionWidget && !companionWidget.contains(e.target)) {
        companionBubble.style.display = 'none';
      }
    });
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 2. SKILL TREE NODE POPOVERS (DASHBOARD)
  // ══════════════════════════════════════════════════════════════════════════════
  const treeNodes = document.querySelectorAll('.js-tree-node');
  if (treeNodes.length > 0) {
    treeNodes.forEach(node => {
      const btn = node.querySelector('.kids-node-btn');
      const popover = node.querySelector('.js-node-popover');
      
      if (btn && popover) {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const isCurrentlyOpen = popover.style.display === 'block';

          // Fecha todos os outros popovers abertos
          document.querySelectorAll('.js-node-popover').forEach(p => {
            p.style.display = 'none';
          });

          // Alterna o popover atual
          popover.style.display = isCurrentlyOpen ? 'none' : 'block';
        });

        popover.addEventListener('click', (e) => {
          e.stopPropagation();
        });
      }
    });

    // Fecha ao clicar fora
    document.addEventListener('click', () => {
      document.querySelectorAll('.js-node-popover').forEach(p => {
        p.style.display = 'none';
      });
    });
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 3. REINVENTED INTERACTIVE MISSION RUNNER (QUIZ.HTML OVERHAUL)
  // ══════════════════════════════════════════════════════════════════════════════
  const missionContainer = document.querySelector('.kids-mission-container');
  if (missionContainer) {
    const lessonId = parseInt(missionContainer.getAttribute('data-lesson-id'), 10);

    // Seções de fases
    const phaseSections = {
      theory: document.getElementById('phase-theory'),
      lab: document.getElementById('phase-lab'),
      quiz: document.getElementById('phase-quiz')
    };

    // Botões de navegação no stepper
    const stepButtons = {
      theory: document.getElementById('step-btn-theory'),
      lab: document.getElementById('step-btn-lab'),
      quiz: document.getElementById('step-btn-quiz')
    };

    function activatePhase(phaseKey) {
      Object.keys(phaseSections).forEach(key => {
        if (phaseSections[key]) {
          phaseSections[key].style.display = (key === phaseKey) ? 'block' : 'none';
        }
        if (stepButtons[key]) {
          if (key === phaseKey) {
            stepButtons[key].classList.add('active');
          } else {
            stepButtons[key].classList.remove('active');
          }
        }
      });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Clique manual no stepper de fases
    Object.keys(stepButtons).forEach(key => {
      if (stepButtons[key]) {
        stepButtons[key].addEventListener('click', () => {
          activatePhase(key);
        });
      }
    });

    // ── FASE 1: TEORIA & SLIDES INTERATIVOS ──
    const slides = Array.from(document.querySelectorAll('.js-theory-slide'));
    const btnPrevSlide = document.getElementById('btn-prev-slide');
    const btnNextSlide = document.getElementById('btn-next-slide');
    const btnStartLab = document.getElementById('btn-start-lab');
    const theoryMascotSpeech = document.getElementById('theory-mascot-speech');
    let currentSlideIdx = 0;

    function renderSlide(idx) {
      slides.forEach((sl, i) => {
        sl.style.display = (i === idx) ? 'block' : 'none';
      });

      if (btnPrevSlide) btnPrevSlide.style.display = (idx > 0) ? 'inline-flex' : 'none';
      const isLast = (idx === slides.length - 1);
      if (btnNextSlide) btnNextSlide.style.display = isLast ? 'none' : 'inline-flex';
      if (btnStartLab) btnStartLab.style.display = isLast ? 'inline-flex' : 'none';
    }

    if (slides.length > 0) {
      renderSlide(currentSlideIdx);

      if (btnNextSlide) {
        btnNextSlide.addEventListener('click', () => {
          if (currentSlideIdx < slides.length - 1) {
            currentSlideIdx++;
            renderSlide(currentSlideIdx);
          }
        });
      }

      if (btnPrevSlide) {
        btnPrevSlide.addEventListener('click', () => {
          if (currentSlideIdx > 0) {
            currentSlideIdx--;
            renderSlide(currentSlideIdx);
          }
        });
      }

      if (btnStartLab) {
        btnStartLab.addEventListener('click', () => {
          if (stepButtons.theory) stepButtons.theory.classList.add('completed');
          activatePhase('lab');
        });
      }
    }

    // ── FASE 2: MINI-LABORATÓRIO PRÁTICO ──
    const terminalForm = document.getElementById('lab-terminal-form');
    const terminalInput = document.getElementById('lab-terminal-input');
    const terminalOutput = document.getElementById('lab-terminal-output');
    const labSuccessFooter = document.getElementById('lab-success-footer');
    const btnGoToQuiz = document.getElementById('btn-go-to-quiz');
    const labMascotImg = document.getElementById('lab-mascot-img');

    // Execução no Terminal
    async function runTerminalCommand(rawCmd) {
      const cmd = rawCmd.trim();
      if (!cmd || !terminalOutput) return;

      // Adiciona linha de comando digitada
      const cmdLine = document.createElement('div');
      cmdLine.className = 'term-line';
      cmdLine.innerHTML = `<span class="prompt-user">aluno@duno-kids</span>:<span class="prompt-dir">~</span>$ <strong>${escapeHtml(cmd)}</strong>`;
      terminalOutput.appendChild(cmdLine);

      if (terminalInput) terminalInput.value = '';

      try {
        const res = await fetch('/kids/api/lab/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lesson_id: lessonId, type: 'terminal', command: cmd })
        });
        const data = await res.json();

        if (data.clear) {
          terminalOutput.innerHTML = '';
          return;
        }

        if (data.output) {
          const outLine = document.createElement('div');
          outLine.className = 'term-line ' + (data.completed ? 'term-success' : '');
          outLine.textContent = data.output;
          terminalOutput.appendChild(outLine);
        }

        if (data.tux_reaction) {
          const tuxLine = document.createElement('div');
          tuxLine.className = 'term-line term-system';
          tuxLine.textContent = `[Tux Guia]: ${data.tux_reaction}`;
          terminalOutput.appendChild(tuxLine);
        }

        terminalOutput.scrollTop = terminalOutput.scrollHeight;

        if (data.completed) {
          if (labMascotImg) {
            labMascotImg.className = 'nf nf-md-trophy tux-lab-icon';
            labMascotImg.style.color = '#10b981';
          }
          if (labSuccessFooter) labSuccessFooter.style.display = 'flex';
          if (stepButtons.lab) stepButtons.lab.classList.add('completed');
        }

      } catch (e) {
        console.error('Erro executando comando do lab:', e);
      }
    }

    if (terminalForm) {
      terminalForm.addEventListener('submit', (e) => {
        e.preventDefault();
        if (terminalInput) runTerminalCommand(terminalInput.value);
      });
    }

    // Botões de comandos rápidos
    document.querySelectorAll('.js-quick-cmd').forEach(btn => {
      btn.addEventListener('click', function() {
        const cmd = this.getAttribute('data-cmd');
        if (cmd) runTerminalCommand(cmd);
      });
    });

    // Lab de Sequência
    const seqTargetArea = document.getElementById('seq-target-area');
    const btnResetSeq = document.getElementById('btn-reset-seq');
    const btnCheckSeq = document.getElementById('btn-check-seq');
    let chosenSequence = [];

    document.querySelectorAll('.js-seq-opt').forEach(btn => {
      btn.addEventListener('click', function() {
        const val = this.getAttribute('data-value');
        if (!val || this.classList.contains('slotted')) return;

        this.classList.add('slotted');
        chosenSequence.push(val);

        if (seqTargetArea) {
          const emptyHint = seqTargetArea.querySelector('.seq-empty-hint');
          if (emptyHint) emptyHint.style.display = 'none';

          const slotPill = document.createElement('div');
          slotPill.className = 'kids-seq-btn slotted-target';
          slotPill.innerHTML = `<strong>#${chosenSequence.length}</strong> ${escapeHtml(val)}`;
          seqTargetArea.appendChild(slotPill);
        }
      });
    });

    if (btnResetSeq) {
      btnResetSeq.addEventListener('click', () => {
        chosenSequence = [];
        document.querySelectorAll('.js-seq-opt').forEach(b => b.classList.remove('slotted'));
        if (seqTargetArea) {
          seqTargetArea.innerHTML = '<div class="seq-empty-hint">Clique nos blocos abaixo na ordem desejada...</div>';
        }
      });
    }

    if (btnCheckSeq) {
      btnCheckSeq.addEventListener('click', async () => {
        if (chosenSequence.length === 0) return;
        try {
          const res = await fetch('/kids/api/lab/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lesson_id: lessonId, type: 'sequence', sequence: chosenSequence })
          });
          const data = await res.json();
          if (data.completed) {
            if (labSuccessFooter) labSuccessFooter.style.display = 'flex';
            if (stepButtons.lab) stepButtons.lab.classList.add('completed');
            if (labMascotImg) {
              labMascotImg.className = 'nf nf-md-trophy tux-lab-icon';
              labMascotImg.style.color = '#10b981';
            }
          } else {
            alert(data.tux_reaction || 'Sequência incorreta. Tente novamente!');
          }
        } catch (e) {
          console.error(e);
        }
      });
    }

    // Lab de Inspetor
    document.querySelectorAll('.js-inspector-btn').forEach(btn => {
      btn.addEventListener('click', async function() {
        const answer = this.getAttribute('data-answer');
        try {
          const res = await fetch('/kids/api/lab/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lesson_id: lessonId, type: 'inspector', answer: answer })
          });
          const data = await res.json();
          if (data.completed) {
            this.classList.add('selected-correct');
            if (labSuccessFooter) labSuccessFooter.style.display = 'flex';
            if (stepButtons.lab) stepButtons.lab.classList.add('completed');
            if (labMascotImg) {
              labMascotImg.className = 'nf nf-md-trophy tux-lab-icon';
              labMascotImg.style.color = '#10b981';
            }
          } else {
            this.classList.add('selected-wrong');
            alert(data.tux_reaction || 'Ops, esse item parece legítimo. Procure pelo suspeito!');
          }
        } catch (e) {
          console.error(e);
        }
      });
    });

    if (btnGoToQuiz) {
      btnGoToQuiz.addEventListener('click', () => {
        activatePhase('quiz');
      });
    }

    // ── FASE 3: DESAFIO CHECKPOINT (QUIZ REFINADO) ──
    const questionBoxes = Array.from(document.querySelectorAll('.js-quiz-question-box'));
    const livesCounter = document.getElementById('quiz-lives-count');
    const drawer = document.getElementById('quiz-drawer');
    const nextBtn = document.getElementById('quiz-next-btn');
    const quizMascotImg = document.getElementById('quiz-mascot-img');
    const tuxCheckpointSpeech = document.getElementById('tux-checkpoint-speech');
    const btnAskTuxHint = document.getElementById('btn-ask-tux-hint');
    const totalQuestions = questionBoxes.length;

    let currentIndex = 0;
    let correctCount = 0;
    let answered = false;

    function showQuestion(index) {
      answered = false;
      questionBoxes.forEach((box, i) => {
        box.style.display = (i === index) ? 'block' : 'none';
      });
      if (drawer) drawer.style.display = 'none';
      if (quizMascotImg) {
        quizMascotImg.className = 'nf nf-md-help_network tux-mentor-icon';
        quizMascotImg.style.color = 'var(--orange)';
      }
      if (tuxCheckpointSpeech) tuxCheckpointSpeech.textContent = 'Leia com atenção e escolha a melhor resposta!';
    }

    if (questionBoxes.length > 0) {
      showQuestion(currentIndex);
    }

    // Dica do Tux sob demanda
    if (btnAskTuxHint) {
      btnAskTuxHint.addEventListener('click', () => {
        if (quizMascotImg) {
          quizMascotImg.className = 'nf nf-md-lightbulb_on_outline tux-mentor-icon';
          quizMascotImg.style.color = '#f59e0b';
        }
        if (tuxCheckpointSpeech) {
          tuxCheckpointSpeech.textContent = '💡 Dica do Tux: Lembre-se do que vimos nos slides e no laboratório prático!';
        }
      });
    }

    // Seleção de alternativas
    document.querySelectorAll('.js-option-btn').forEach(btn => {
      btn.addEventListener('click', async function() {
        if (answered) return;
        answered = true;

        const quizId = this.getAttribute('data-quiz-id');
        const selectedOption = this.getAttribute('data-option');
        const parentBox = this.closest('.js-quiz-question-box');
        const optionButtons = parentBox.querySelectorAll('.js-option-btn');

        optionButtons.forEach(b => {
          b.disabled = true;
          b.classList.remove('selected');
        });
        this.classList.add('selected');

        try {
          const res = await fetch('/kids/api/quiz/answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quiz_id: quizId, answer: selectedOption })
          });
          const data = await res.json();

          if (data.correct) {
            this.classList.remove('selected');
            this.classList.add('correct');
            correctCount++;
            if (quizMascotImg) {
              quizMascotImg.className = 'nf nf-md-trophy tux-mentor-icon';
              quizMascotImg.style.color = '#10b981';
            }
            if (tuxCheckpointSpeech) tuxCheckpointSpeech.textContent = data.tux_reaction || 'Sensacional! Você acertou!';
            showDrawerFeedback(true, 'Resposta Correta!', data.explanation);
          } else {
            this.classList.remove('selected');
            this.classList.add('incorrect');
            optionButtons.forEach(b => {
              if (b.getAttribute('data-option') === data.correct_option) {
                b.classList.add('correct');
              }
            });
            if (quizMascotImg) {
              quizMascotImg.className = 'nf nf-fa-times_circle tux-mentor-icon';
              quizMascotImg.style.color = '#ef4444';
            }
            if (tuxCheckpointSpeech) tuxCheckpointSpeech.textContent = data.tux_reaction || 'Ops! Veja a explicação abaixo para fixar.';
            showDrawerFeedback(false, 'Incorreto', data.explanation);
          }

          if (livesCounter && data.lives_remaining !== undefined) {
            livesCounter.textContent = data.lives_remaining;
          }

          if (data.game_over) {
            setTimeout(() => {
              alert('Suas vidas acabaram para esta sessão. Pratique novamente na trilha!');
              window.location.href = '/kids/dashboard';
            }, 2000);
          }

        } catch (err) {
          console.error(err);
          answered = false;
          optionButtons.forEach(b => b.disabled = false);
        }
      });
    });

    function showDrawerFeedback(isSuccess, title, explanation) {
      if (!drawer) return;
      const iconEl = document.getElementById('feedback-status-icon');
      const titleEl = drawer.querySelector('.js-feedback-title');
      const explEl = drawer.querySelector('.js-feedback-expl');

      if (iconEl) {
        iconEl.innerHTML = isSuccess ? '<i class="nf nf-md-check" style="color: #10b981;"></i>' : '<i class="nf nf-md-close" style="color: #ef4444;"></i>';
      }
      if (titleEl) {
        titleEl.textContent = title;
        titleEl.style.color = isSuccess ? '#10b981' : '#ef4444';
      }
      if (explEl) explEl.textContent = explanation;

      drawer.style.display = 'flex';
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', async function() {
        currentIndex++;
        if (currentIndex < totalQuestions) {
          showQuestion(currentIndex);
        } else {
          // Conclui a Lição completa
          if (stepButtons.quiz) stepButtons.quiz.classList.add('completed');
          try {
            const res = await fetch('/kids/api/lesson/complete', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                lesson_id: lessonId,
                correct_count: correctCount,
                total_count: totalQuestions
              })
            });
            const finishData = await res.json();
            showCompletionModal(finishData);
          } catch (err) {
            window.location.href = '/kids/dashboard';
          }
        }
      });
    }

    function showCompletionModal(data) {
      const modal = document.getElementById('quiz-finish-modal');
      if (modal) {
        const starContainer = modal.querySelector('.js-modal-stars');
        if (starContainer) {
          starContainer.innerHTML = '';
          for (let i = 0; i < 3; i++) {
            const isFilled = i < data.stars;
            starContainer.innerHTML += `<i class="nf ${isFilled ? 'nf-md-star' : 'nf-md-star_outline'}" style="color: #f59e0b; font-size: 2.2rem; margin: 0 4px;"></i>`;
          }
        }
        modal.style.display = 'flex';
      } else {
        window.location.href = '/kids/dashboard';
      }
    }
  }

  // ══════════════════════════════════════════════════════════════════════════════
  // 4. DAILY QUESTS CLAIM ENGINE
  // ══════════════════════════════════════════════════════════════════════════════
  document.querySelectorAll('.js-claim-quest-btn').forEach(btn => {
    btn.addEventListener('click', async function() {
      const questId = this.getAttribute('data-quest-id');
      if (!questId) return;

      this.disabled = true;
      const originalText = this.innerHTML;
      this.textContent = 'Resgatando...';

      try {
        const res = await fetch('/kids/api/quest/claim', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ quest_id: parseInt(questId, 10) })
        });
        const data = await res.json();

        if (data.success) {
          this.textContent = 'Resgatado ✓';
          this.className = 'btn btn-outline btn-sm';
          this.style.opacity = '0.6';
          this.style.cursor = 'default';
        } else {
          this.innerHTML = originalText;
          this.disabled = false;
        }
      } catch (e) {
        this.innerHTML = originalText;
        this.disabled = false;
      }
    });
  });

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag));
  }

})();
