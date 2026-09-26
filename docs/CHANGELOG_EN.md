# What's New — Timeline & Changelog — DUNO

Follow the main architectural updates, new subsystems, and technical improvements implemented in **DUNO**.

---

## September 26, 2026

### [i18n & Global Localization] Native Multi-Language Support (PT-BR, EN, ES)
* **Flask-Babel Architecture:** Complete internationalization pipeline with automatic locale detection and persistence via `duno_lang` cookie.
* **Full Interface Translation:** 100% coverage across Jinja2 templates (Base, Home, Authentication, Profile, OWASP Labs, CTF Challenges, Academy Hub, Walkthroughs, Machine Submissions, and Admin).
* **Decoupled YAML Hubs:** Localized YAML data files for Official Documentation (`docs_*.yaml`), Academy Hub (`academy_*.yaml`), and Challenges Catalog (`challenges_*.yaml`).
* **Complete Translation of DUNO Kids:** Full multi-language support across all 5 curriculum tracks, 21 lessons, daily quests, leaderboard, and pedagogical Tux mascot prompts.
* **Catalog Automation:** Intelligent batch translation script with `fuzzy` tag sanitization and instant binary `.mo` catalog compilation.

### [CTF Challenges Engine] Phonetic Directory Standardization & Flag Hashes
* **Phonetic Naming:** Standardized offensive machine directories (`challenges/alpha`, `bravo`, `charlie`... `zero`).
* **Unified Flags:** Consistent standard formatting under `DUNO{<hash>}` with centralized validation via `flag_service.py`.
* **Walkthroughs & Solutions:** Step-by-step offensive security solutions documented and cataloged for all environment machines.

### [UI/UX & Platform Stability]
* **Academy Hub Fix:** Resolved HTTP 500 exception caused by improper JavaScript literal escaping in Jinja2 templates.
* **Centralized Countdown Component:** Reusable countdown timer component for lab telemetry (`countdown_central.html`).
* **Refined Brand Identity:** Updated vector assets (`duno-logo.svg`, `duno-mark.svg`, `favicon.svg`).
* **Software Quality Assurance:** Comprehensive automated pytest test suite for Kids and Machine Submissions subsystems.

---

## September 19, 2026

### [Machine Submissions] Community Machine Submission and Audit Pipeline
* **Ingestion Pipeline:** Compressed package uploads (`.zip` and `.tar.gz`) up to 50MB with mandatory `manifest.yml` validation.
* **Security and Anti-ZipSlip:** Magic byte validation (`PK\x03\x04`, `\x1f\x8b`, `ustar`), strict rejection of symbolic links, and real byte counting against ZipBombs.
* **Command Center:** Unified operational dashboard for machine moderation, telemetry, and audit trail inspection (`machine_audit_logs`).
* **Static Vulnerability Scanner:** Automated linters for detecting privileged ports, `/var/run/docker.sock` socket mounts, and plaintext private key leaks.

---

## September 18, 2026

### [DUNO Kids] 5 Gamified Learning Tracks & Retro Linux CRT Terminal
* **Complete Curriculum:** 20 pedagogical missions distributed across 5 core pillars (Operating Systems, Networks, Web Applications, Cryptography, and Digital Defense).
* **Retro Linux CRT Terminal:** Integrated in-browser terminal simulator running real commands (`pwd`, `ls`, `cd`, `cat`, `chmod`, `ping`, `echo`).
* **Dynamic Tux Mascot:** Interactive pixel-art companion with color shifting, feedback expressions, pedagogical tips, and Nerd Fonts badges.
* **Quizzes & Checkpoints:** Validation system featuring player lives, audio feedback, and experience point (XP) rewards.

---

## September 17, 2026

### [Challenges Engine] Catalog of 25 CTF Offensive Machines
* **Autonomous Orchestration:** Dynamic container spin-up and teardown on demand via Challenge Runner.
* **Tripartite Segregation:** Total isolation of `duno-challenges-net` network with disabled egress (`internal: true`).
* **Controlled Lifetime:** Automatic 45-minute TTL per instance to conserve CPU and memory resources.
* **Flag Submission:** Point system with dynamic flags and per-user solve tracking.

---

## September 16, 2026

### [Security Hardening] Operations Runbook & Kill Switches
* **Emergency Shutdown:** Global feature flag `CHALLENGES_ENABLED=false` in `.env` for immediate deactivation without redeployment.
* **Compliance Audit:** Formal security assessment with 8/8 isolation checklist requirements in strict compliance.

---

## September 15, 2026

### [OWASP Core] 20 Native Vulnerability Modules
* **4-Level Graduation:** Real-time switching between `Low`, `Medium`, `High`, and `Impossible`.
* **Source Code Viewer:** Interactive modal with syntax highlighting showcasing the real implementation of each level.
* **Walkie Design System:** Refined interface without heavy frontend frameworks, native Dark Mode support, and Outfit typography.
