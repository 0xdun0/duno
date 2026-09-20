# DUNO Kids: Currículo Completo, Trilhas Pedagógicas & Terminal CRT

O **DUNO Kids** é o subsistema educacional gamificado da plataforma, desenhado para introduzir conceitos avançados de computação, sistemas operacionais, redes e cibersegurança para iniciantes e jovens entusiastas através de analogias do mundo real e desafios práticos.

---

## 1. Visão Geral da Skill Tree (Mapa de Missões)

O aluno inicia sua jornada no centro do mapa (**A Ilha Inicial**). Para avançar, ele deve completar as 3 fases de cada missão:
1. **Fase Teórica:** Slides conceituais com analogias ricas e orientações do mascote **Tux**.
2. **Fase Prática (Laboratório):** Simulador de Terminal Linux CRT retrô, sequenciamento lógico de blocos ou ferramenta de inspeção visual.
3. **Fase Checkpoint (Desafio):** Quiz de fixação com feedback imediato, pontuação de vidas e recompensa em XP.

---

## 2. As 5 Trilhas de Formação

### Trilha 1: Sistemas Operacionais (OS)
**Objetivo:** Compreender que o computador é uma máquina obediente a comandos diretos e que o Terminal Linux é a ferramenta central de qualquer especialista em segurança.

* **Módulo 1.1: O Cérebro do Computador (O que é um OS?)**
  * *Analogia:* O Sistema Operacional é como o diretor da escola: organiza as turmas (processos), distribui os livros (arquivos) e define quem entra em cada sala.
  * *Prática:* Identificar as responsabilidades do Kernel vs Programas de usuário.
  * *Ponte CTF:* Entender que todo alvo possui uma estrutura de pastas e processos específica.
* **Módulo 1.2: A Caverna do Terminal (Introdução ao Shell)**
  * *Analogia:* O terminal não morde: é apenas uma linha direta de conversa com o computador sem o peso de botões gráficos.
  * *Prática no CRT:* Digitar comandos básicos `help`, `clear` e `echo`.
  * *Ponte CTF:* Acesso SSH e sessões reversas operam inteiramente via terminal.
* **Módulo 1.3: Navegando no Escuro (Comandos de Sistema)**
  * *Comandos ensinados:* `pwd` (onde estou?), `ls` (o que tem aqui?), `cd` (mudar de pasta), `mkdir` (criar diretório).
  * *Prática no CRT:* Explorar pastas ocultas para encontrar a chave de acesso.
  * *Ponte CTF:* Ao obter acesso inicial em qualquer máquina, `ls -la` é a primeira ação do pentester.
* **Módulo 1.4: As Chaves do Reino (Permissões de Arquivo)**
  * *Analogia:* As três chaves do cofre: Ler (`r`), Escrever (`w`) e Executar (`x`). O usuário `root` carrega o chaveiro mestre.
  * *Prática:* Executar `chmod +x run.sh` para autorizar a execução de um script defensivo.
  * *Ponte CTF:* Permissões incorretas de arquivos (SUID) são uma das maiores fontes de Privilege Escalation.

---

### Trilha 2: Redes de Computadores (Networks)
**Objetivo:** Desmistificar como os computadores conversam entre si e como as informações navegam pelo planeta.

* **Módulo 2.1: A Teia Mundial (O que é a Internet?)**
  * *Analogia:* A internet é como o sistema dos Correios: cartas (pacotes) são envelopadas com endereço de origem e destino (IP).
  * *Prática no CRT:* `ping 1.1.1.1` para testar o tempo de resposta e latência.
  * *Ponte CTF:* Todo alvo em um CTF possui um endereço IP acessível na VPN.
* **Módulo 2.2: A Lista Telefônica (DNS)**
  * *Analogia:* Ninguém decora o IP do servidor; nós usamos nomes como `google.com`. O DNS traduz nomes em números.
  * *Prática:* `host duno.lab` e análise de registros A e CNAME.
  * *Ponte CTF:* Enumeração de subdomínios via DNS Brute Force para descobrir painéis administrativos.
* **Módulo 2.3: As Portas do Castelo (Portas & Serviços)**
  * *Analogia:* Uma casa possui porta da frente (Porta 80 - Web), garagem (Porta 22 - SSH) e portão dos fundos (Porta 21 - FTP).
  * *Prática:* Identificar qual porta está escutando na máquina de teste.
  * *Ponte CTF:* O scanner `nmap` varre portas abertas para mapear a superfície de ataque.
* **Módulo 2.4: O Guardião da Muralha (Firewall & Pacotes)**
  * *Analogia:* O porteiro do condomínio que checa crachás: bloqueia pacotes não autorizados e protege a rede local.
  * *Prática:* Compreender a diferença entre tráfego de entrada (Inbound) e saída (Outbound).

---

### Trilha 3: Aplicações Web (Web Apps)
**Objetivo:** Ensinar como websites funcionam por baixo do capô e como inspecionar elementos invisíveis.

* **Módulo 3.1: O Esqueleto da Web (HTML & Tags)**
  * *Analogia:* O HTML são as paredes e vigas de uma casa: tags como `<h1>`, `<p>`, `<a>` e `<input>`.
  * *Prática:* Inspecionar código-fonte da página para encontrar comentários esquecidos pelo desenvolvedor.
  * *Ponte CTF:* Desenvolvedores frequentemente deixam credenciais ou dicas em comentários HTML `<!-- secret -->`.
* **Módulo 3.2: O Inspetor de Elementos (DevTools)**
  * *Analogia:* O raio-X do navegador: permite alterar textos e cores localmente sem afetar o servidor real.
  * *Prática:* Mudar o atributo de um botão desabilitado (`disabled`) para poder clicar.
  * *Ponte CTF:* Bypass de validações frágeis feitas apenas no lado do cliente (Client-Side).
* **Módulo 3.3: O Garçom da Web (Requisições HTTP GET & POST)**
  * *Analogia:* O cliente pede o cardápio (GET) e entrega o pedido na cozinha (POST). O garçom traz o prato (Código 200 OK).
  * *Prática:* Analisar os cabeçalhos de resposta HTTP e códigos de status (200, 301, 404, 500).
  * *Ponte CTF:* Ferramentas de proxy como Burp Suite interceptam e alteram requisições HTTP.
* **Módulo 3.4: Biscoitos Mágicos (Cookies & Sessão)**
  * *Analogia:* O carimbo que você ganha na entrada do parque de diversões: prova que você já pagou o ingresso.
  * *Prática:* Observar como o navegador guarda o identificador de login.
  * *Ponte CTF:* Roubo e fixação de sessão via XSS e Cookie Tampering.

---

### Trilha 4: Criptografia & Segredos (Cryptography)
**Objetivo:** Entender a matemática do sigilo: como transformar dados legíveis em texto cifrado e proteger credenciais.

* **Módulo 4.1: A Roda Secreta (Cifra de César & Substituição)**
  * *Analogia:* Deslocar cada letra 3 posições para frente: `A` vira `D`, `B` vira `E`.
  * *Prática:* Decodificar uma mensagem secreta usando o disco de rotação.
  * *Ponte CTF:* Identificação de padrões ROT13 e cifras clássicas em desafios de criptografia.
* **Módulo 4.2: O Moedor de Carne Digital (Funções Hash)**
  * *Analogia:* Depois que você moeu a carne, não dá para transformar de volta em bife: hashes são vias de mão única.
  * *Prática:* Comparar o hash MD5 e SHA256 de duas palavras e notar o Efeito Avalanche.
  * *Ponte CTF:* Quebra de hashes de senhas via dicionário no John the Ripper / Hashcat.
* **Módulo 4.3: Duas Chaves para um Cadeado (Criptografia Asimétrica)**
  * *Analogia:* Chave Pública (o cadeado aberto que qualquer um pode trancar) e Chave Privada (a chave física que só você tem no bolso).
  * *Prática:* Compreender como funciona o HTTPS e certificados digitais SSL/TLS.
* **Módulo 4.4: O Cofre dos Hackers (Senhas Fortes & 2FA)**
  * *Analogia:* Uma fechadura com segredo de letras e um código enviado no chaveiro do celular.
  * *Prática:* Testar a força de entropia de diferentes senhas.

---

### Trilha 5: Defesa Digital & Segurança Pessoal (Defense)
**Objetivo:** Formar cidadãos digitais conscientes, capazes de identificar golpes, proteger sua privacidade e navegar com segurança.

* **Módulo 5.1: O Peixe no Anzol (Reconhecendo Phishing)**
  * *Analogia:* A isca irresistível: mensagens urgentes pedindo cliques para não perder uma conta ou ganhar um prêmio falso.
  * *Prática:* Inspecionar o endereço do remetente e links encurtados suspeitos.
* **Módulo 5.2: Os Zumbis da Rede (Malware & Vírus)**
  * *Analogia:* Programas invasores que fingem ser joguinhos para roubar dados em segundo plano.
  * *Prática:* Compreender a importância de manter sistemas atualizados e antivírus ativo.
* **Módulo 5.3: O Rastro Digital (Privacidade & Pegada na Web)**
  * *Analogia:* Pegadas na areia: tudo o que você posta, curte ou busca fica registrado para sempre.
  * *Prática:* Auditoria básica de dados compartilhados em perfis públicos.
* **Módulo 5.4: O Hacker Ético (White Hat & Responsabilidade)**
  * *Analogia:* O chaveiro experiente que é contratado para testar se as fechaduras do banco são seguras e relata as falhas.
  * *Prática:* O código de conduta do hacker ético: respeito, legalidade e autorização explícita.
