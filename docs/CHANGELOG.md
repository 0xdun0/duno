# What's New — Linha do Tempo & Changelog — DUNO

Acompanhe as principais atualizações de arquitetura, novos subsistemas e melhorias técnicas implementadas no **DUNO**.

---

## 19 de Setembro de 2026

### [Machine Submissions] Pipeline de Submissão e Auditoria de Máquinas
* **Esteira de Ingestão:** Upload de pacotes compactados (`.zip` e `.tar.gz`) de até 50MB com validação obrigatória de `manifest.yml`.
* **Segurança e Anti-ZipSlip:** Validação de magic bytes (`PK\x03\x04`, `\x1f\x8b`, `ustar`), rejeição estrita de links simbólicos e contagem real de bytes contra ZipBombs.
* **Command Center:** Painel de controle operacional unificado para moderação de máquinas, telemetria e visualização de trilha de auditoria (`machine_audit_logs`).
* **Scanner Estático de Vulnerabilidades:** Linters automáticos para detecção de portas privilegiadas, montagem de `/var/run/docker.sock` e vazamento de chaves privadas em texto puro.

---

## 18 de Setembro de 2026

### [DUNO Kids] 5 Trilhas Gamificadas & Terminal Linux CRT
* **Currículo Completo:** 20 missões didáticas distribuídas em 5 pilares fundamentais (Sistemas Operacionais, Redes, Aplicações Web, Criptografia e Defesa Digital).
* **Terminal Linux CRT Retrô:** Simulador de terminal integrado no navegador com comandos reais (`pwd`, `ls`, `cd`, `cat`, `chmod`, `ping`, `echo`).
* **Mascote Tux Dinâmico:** Guia interativo em pixel-art com rotação de cores, expressões de feedback, dicas pedagógicas e badges Nerd Fonts.
* **Quizzes & Checkpoints:** Sistema de validação com vidas, feedback sonoro e recompensas em pontos de experiência (XP).

---

## 17 de Setembro de 2026

### [Challenges Engine] Catálogo de 25 Máquinas Ofensivas CTF
* **Orquestração Autônoma:** Início e término de containers dinâmicos sob demanda via Challenge Runner.
* **Segregação Tripartite:** Isolamento total da rede `duno-challenges-net` com desativação de egress (`internal: true`).
* **Tempo de Vida Controlado:** TTL automático de 45 minutos por instância para preservação de recursos de CPU e RAM.
* **Submissão de Flags:** Sistema de pontuação com flags dinâmicas e registro de soluções por usuário.

---

## 16 de Setembro de 2026

### [Security Hardening] Runbook de Operações & Kill Switches
* **Desativação Emergencial:** Feature flag global `CHALLENGES_ENABLED=false` no arquivo `.env` para desativação imediata sem redeploy.
* **Auditoria de Conformidade:** Avaliação formal de segurança com 8/8 requisitos do checklist de isolamento em conformidade estrita.

---

## 15 de Setembro de 2026

### [OWASP Core] 20 Módulos Nativos de Vulnerabilidade
* **Graduação em 4 Níveis:** Alternância em tempo real entre `Low`, `Medium`, `High` e `Impossible`.
* **Visualizador de Código-Fonte:** Modal interativo com syntax highlighting exibindo a implementação real de cada nível.
* **Design System Walkie:** Interface refinada sem frameworks pesados, suporte nativo a Dark Mode e tipografia Outfit.
