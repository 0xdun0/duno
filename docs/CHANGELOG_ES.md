# Novedades — Línea de Tiempo y Registro de Cambios — DUNO

Siga las principales actualizaciones de arquitectura, nuevos subsistemas y mejoras técnicas implementadas en **DUNO**.

---

## 26 de Septiembre de 2026

### [i18n y Localización Global] Soporte Multilingüe Nativo (PT-BR, EN, ES)
* **Arquitectura Flask-Babel:** Pipeline completo de internacionalización con detección automática de idioma y persistencia a través de la cookie `duno_lang`.
* **Traducción Integral de la Interfaz:** Cobertura del 100% en las plantillas Jinja2 (Base, Inicio, Autenticación, Perfil, Laboratorios OWASP, Desafíos CTF, Academy Hub, Walkthroughs, Machine Submissions y Admin).
* **Hubs Desacoplados en YAML:** Localización en archivos YAML independientes para la Documentación Oficial (`docs_*.yaml`), Academy Hub (`academy_*.yaml`) y Catálogo de Desafíos (`challenges_*.yaml`).
* **Traducción Completa de DUNO Kids:** Soporte multilingüe en los 5 módulos curriculares, 21 lecciones, misiones diarias, tabla de clasificación y avisos pedagógicos del Tux.
* **Automatización de Catálogos:** Script de traducción por lotes inteligente con eliminación de etiquetas `fuzzy` y compilación binaria instantánea de catálogos `.mo`.

### [Motor de Desafíos CTF] Estandarización Fonética y Hashes de Flags
* **Nomenclatura Fonética:** Estandarización de directorios de máquinas ofensivas (`challenges/alpha`, `bravo`, `charlie`... `zero`).
* **Unificación de Flags:** Formateo uniforme bajo el estándar `DUNO{<hash>}` con validación centralizada mediante `flag_service.py`.
* **Walkthroughs y Soluciones:** Soluciones documentadas paso a paso para todas las máquinas del entorno.

### [UI/UX y Estabilidad de Plataforma]
* **Corrección en Academy Hub:** Resolución de excepción HTTP 500 originada por escapes incorrectos de literales JavaScript en plantillas Jinja2.
* **Componente de Cuenta Regresiva:** Nuevo componente de temporizador centralizado para telemetría de laboratorios (`countdown_central.html`).
* **Identidad Visual Refinada:** Nuevos recursos vectoriales de la marca (`duno-logo.svg`, `duno-mark.svg`, `favicon.svg`).
* **Garantía de Calidad:** Batería completa de pruebas automatizadas con pytest para los subsistemas Kids y Machine Submissions.

---

## 19 de Septiembre de 2026

### [Machine Submissions] Pipeline de Envío y Auditoría de Máquinas Comunitarias
* **Pipeline de Ingesta:** Carga de paquetes comprimidos (`.zip` y `.tar.gz`) de hasta 50MB con validación obligatoria de `manifest.yml`.
* **Seguridad y Anti-ZipSlip:** Validación de magic bytes (`PK\x03\x04`, `\x1f\x8b`, `ustar`), rechazo estricto de enlaces simbólicos y conteo real de bytes contra ZipBombs.
* **Centro de Mando:** Panel operativo unificado para moderación de máquinas, telemetría e inspección de auditoría (`machine_audit_logs`).
* **Escáner Estático de Vulnerabilidades:** Linters automáticos para detectar puertos privilegiados, montajes de `/var/run/docker.sock` y claves privadas en texto claro.

---

## 18 de Septiembre de 2026

### [DUNO Kids] 5 Senderos Gamificados y Terminal Linux CRT Retro
* **Currículo Completo:** 20 misiones pedagógicas distribuidas en 5 pilares (Sistemas Operativos, Redes, Aplicaciones Web, Criptografía y Defensa Digital).
* **Terminal Linux CRT Retro:** Simulador de terminal integrado en el navegador con comandos reales (`pwd`, `ls`, `cd`, `cat`, `chmod`, `ping`, `echo`).
* **Mascota Tux Dinámica:** Guía interactiva en pixel-art con rotación de colores, expresiones de feedback, consejos pedagógicos e insignias Nerd Fonts.
* **Quizzes y Checkpoints:** Sistema de validación con vidas, retroalimentación sonora y recompensas en puntos de experiencia (XP).

---

## 17 de Septiembre de 2026

### [Motor de Desafíos] Catálogo de 25 Máquinas Ofensivas CTF
* **Orquestación Autónoma:** Inicio y detención de contenedores dinámicos a pedido a través de Challenge Runner.
* **Segregación Tripartita:** Aislamiento total de la red `duno-challenges-net` con salida desactivada (`internal: true`).
* **Tiempo de Vida Controlado:** TTL automático de 45 minutos por instancia para preservar recursos de CPU y RAM.
* **Envío de Flags:** Sistema de puntaje con flags dinámicas y registro de soluciones por usuario.

---

## 16 de Septiembre de 2026

### [Fortalecimiento de Seguridad] Manual de Operaciones e Interruptores de Emergencia
* **Desactivación de Emergencia:** Variable global `CHALLENGES_ENABLED=false` en `.env` para apagado inmediato sin reinicio de contenedores.
* **Auditoría de Cumplimiento:** Evaluación formal de seguridad con 8/8 requisitos de la lista de verificación en estricto cumplimiento.

---

## 15 de Septiembre de 2026

### [Núcleo OWASP] 20 Módulos Nativos de Vulnerabilidad
* **Graduación en 4 Niveles:** Cambio en tiempo real entre `Low`, `Medium`, `High` e `Impossible`.
* **Visor de Código Fuente:** Modal interactivo con resaltado de sintaxis que muestra la implementación real de cada nivel.
* **Sistema de Diseño Walkie:** Interfaz refinada sin frameworks pesados, soporte nativo de Modo Oscuro y tipografía Outfit.
