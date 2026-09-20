"""modules/kids/kids_db.py — Banco de Dados e Inicialização de Dados da DUNO Kids.
Implementação completa dos 5 Pilares (Trilhas) e 21 Lições conforme docs/leia.md.
"""
import sqlite3
from datetime import date

KIDS_DDL = """
CREATE TABLE IF NOT EXISTS kids_user_stats (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    coins INTEGER DEFAULT 50,
    lives INTEGER DEFAULT 5,
    max_lives INTEGER DEFAULT 5,
    streak_days INTEGER DEFAULT 1,
    last_active_date TEXT,
    league TEXT DEFAULT 'Bronze',
    chests_opened INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS kids_modules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT NOT NULL,
    description TEXT NOT NULL,
    order_idx INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS kids_lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL,
    icon TEXT NOT NULL,
    order_idx INTEGER NOT NULL,
    xp_reward INTEGER DEFAULT 100,
    coins_reward INTEGER DEFAULT 20,
    FOREIGN KEY(module_id) REFERENCES kids_modules(id)
);

CREATE TABLE IF NOT EXISTS kids_quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL,
    order_idx INTEGER NOT NULL,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL CHECK(correct_option IN ('A','B','C','D')),
    explanation TEXT NOT NULL,
    xp INTEGER DEFAULT 25,
    FOREIGN KEY(lesson_id) REFERENCES kids_lessons(id)
);

CREATE TABLE IF NOT EXISTS kids_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lesson_id INTEGER NOT NULL,
    status TEXT DEFAULT 'available' CHECK(status IN ('locked','available','completed')),
    stars INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    completed_at TIMESTAMP,
    UNIQUE(user_id, lesson_id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(lesson_id) REFERENCES kids_lessons(id)
);

CREATE TABLE IF NOT EXISTS kids_quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    reward_xp INTEGER DEFAULT 50,
    reward_coins INTEGER DEFAULT 15,
    reward_chest TEXT,
    target_count INTEGER DEFAULT 1,
    current_count INTEGER DEFAULT 0,
    claimed INTEGER DEFAULT 0,
    quest_date TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
"""

# ════════════════════════════════════════════════════════════════════════════════
# 5 PILARES (TRILHAS) DO CURRÍCULO DUNO KIDS (docs/leia.md)
# ════════════════════════════════════════════════════════════════════════════════
INITIAL_MODULES = [
    ("networks", "Rede de computadores", "nf-md-web", "A teia mundial, DNS, HTTP/HTTPS e pacotes de dados", 1),
    ("os", "Sistemas Operacionais", "nf-md-laptop", "Comandos mágicos, terminal Linux e permissões de arquivos", 2),
    ("programming", "Programação", "nf-md-code_braces", "Lógica de programação, variáveis, condicionais e Python", 3),
    ("security", "Security", "nf-md-shield_check", "Tríade CIA, senhas fortes, phishing e firewalls", 4),
    ("english", "Inglês para Cyber", "nf-md-translate", "Vocabulário técnico, comandos em inglês e man pages", 5)
]

# ════════════════════════════════════════════════════════════════════════════════
# LIÇÕES DAS TRILHAS (docs/leia.md)
# ════════════════════════════════════════════════════════════════════════════════
INITIAL_LESSONS = [
    # ── TRILHA 1: REDES & INTERNET ──
    (1, "networks", "o-que-e-a-internet", "O que é a Internet?", "A teia gigante que conecta o planeta", "nf-md-web", 1, 100, 20),
    (2, "networks", "o-que-e-um-ip", "O que é um Endereço IP?", "O CEP e RG de cada máquina conectada", "nf-md-map_marker", 2, 100, 20),
    (3, "networks", "o-gps-da-web-dns", "O GPS da Web: DNS", "Como o navegador acha sites sem saber números", "nf-md-compass", 3, 120, 25),
    (4, "networks", "o-carteiro-http-https", "O Carteiro (HTTP/HTTPS)", "Cartas abertas vs cofres blindados criptografados", "nf-md-lock_check", 4, 150, 30),
    (5, "networks", "net-radar-comandos", "O Radar de Rede", "Comandos essenciais: ping, ip e ifconfig", "nf-md-radar", 5, 200, 40),

    # ── TRILHA 2: SISTEMAS OPERACIONAIS (OS) ──
    (6, "os", "os-cerebro-computador", "O Cérebro do Computador", "O que é um Sistema Operacional e seus papéis", "nf-md-laptop", 1, 100, 20),
    (7, "os", "os-caverna-terminal", "A Caverna do Terminal", "Introdução ao Linux e comandos diretos no shell", "nf-oct-terminal", 2, 100, 20),
    (8, "os", "os-navegando-no-escuro", "Navegando no Escuro", "Comandos essenciais: pwd, ls, cd e mkdir", "nf-md-folder_search", 3, 120, 25),
    (9, "os", "os-chaves-do-reino", "As Chaves do Reino", "Permissões de arquivos (r, w, x) e o comando chmod", "nf-md-key", 4, 150, 30),

    # ── TRILHA 3: PROGRAMAÇÃO ──
    (10, "programming", "prog-receita-de-bolo", "A Receita de Bolo", "Lógica de programação e passos ordenados", "nf-md-chef_hat", 1, 100, 20),
    (11, "programming", "prog-caixas-e-etiquetas", "Caixas e Etiquetas", "Variáveis, tipos de dados e strings na memória", "nf-md-package_variant_closed", 2, 100, 20),
    (12, "programming", "prog-o-semaforo", "O Semáforo (If/Else)", "Condicionais e decisões baseadas em verdadeiro/falso", "nf-md-call_split", 3, 120, 25),
    (13, "programming", "prog-magia-do-python", "A Magia do Python", "Seu primeiro script e comandos reais de automação", "nf-md-language_python", 4, 150, 30),

    # ── TRILHA 4: SECURITY (CYBERSECURITY) ──
    (14, "security", "sec-triangulo-magico", "O Triângulo Mágico (Tríade CIA)", "Confidencialidade, Integridade e Disponibilidade", "nf-md-shield_check", 1, 100, 20),
    (15, "security", "sec-chave-da-porta", "A Chave da Porta", "Senhas fortes, proteção contra força bruta e 2FA", "nf-md-form_textbox_password", 2, 100, 20),
    (16, "security", "sec-pescador-de-dados", "O Pescador de Dados (Phishing)", "Identificando mensagens falsas e engenharia social", "nf-md-fish", 3, 120, 25),
    (17, "security", "sec-guardas-do-castelo", "Os Guardas do Castelo", "Firewall perimetral e antivírus no disco", "nf-md-wall", 4, 150, 30),

    # ── TRILHA 5: INGLÊS PARA CYBERSECURITY ──
    (18, "english", "eng-alfabeto-do-hacker", "O Alfabeto do Hacker", "A origem em inglês de ls, cd, cat e grep", "nf-md-alphabetical", 1, 100, 20),
    (19, "english", "eng-palavras-que-assustam", "Palavras que Assustam", "Desmistificando Bug, Exploit, Payload e Hash", "nf-md-book_open_page_variant", 2, 100, 20),
    (20, "english", "eng-lendo-as-instrucoes", "Lendo as Instruções", "Dominando man pages e a flag --help no terminal", "nf-md-file_document_outline", 3, 120, 25),
    (21, "english", "eng-falando-com-o-mundo", "Falando com o Mundo", "Relatórios técnicos, PoCs e disclosure responsável", "nf-md-forum", 4, 150, 30)
]

# ════════════════════════════════════════════════════════════════════════════════
# QUIZZES EDUCATIVOS
# ════════════════════════════════════════════════════════════════════════════════
INITIAL_QUIZZES = [
    # ── LIÇÃO 1: O que é a Internet? ──
    (1, 1, "O que é a Internet no mundo real?", 
     "Uma nuvem de fumaça mágica no céu", 
     "Uma rede mundial de computadores interligados por cabos e sinais", 
     "Um aplicativo que só existe dentro do celular", 
     "Uma caixa de metal fechada", 
     "B", "A Internet é exatamente uma teia mundial de milhões de computadores conectados compartilhando informações!", 25),
    (1, 2, "Como os dados viajam de um país para outro?",
     "Por garrafas flutuando no oceano",
     "Por pombos-correio digitais",
     "Por cabos submarinos gigantes no fundo dos oceanos e satélites",
     "Eles se teletransportam pelo ar",
     "C", "Mais de 95% do tráfego internacional de internet viaja por cabos de fibra óptica debaixo do mar!", 25),
    (1, 3, "Qual é o principal trabalho de um Servidor na internet?",
     "Guardar arquivos e entregar páginas quando você pede",
     "Jogar videogame sozinho à noite",
     "Desligar a energia da sua casa",
     "Tirar fotos dos cabos",
     "A", "Servidores são computadores poderosos que ficam ligados 24 horas servindo sites, vídeos e jogos para clientes.", 25),

    # ── LIÇÃO 2: O que é um Endereço IP? ──
    (2, 1, "Para que serve um endereço IP?",
     "Para saber a senha do Wi-Fi do vizinho",
     "Para identificar com exclusividade cada dispositivo na rede",
     "Para medir a velocidade do cooler",
     "Para pintar a tela de verde",
     "B", "Assim como cada casa tem um endereço postal, cada computador na rede possui um IP para receber dados.", 25),
    (2, 2, "Qual dos formatos abaixo parece um endereço IPv4 real?",
     "192.168.1.10",
     "usuario@gmail.com",
     "batata-frita-1234",
     "www.google.com.br",
     "A", "O IPv4 é formado por 4 grupos de números separados por pontos, variando de 0 a 255!", 25),

    # ── LIÇÃO 3: O GPS da Web: DNS ──
    (3, 1, "Qual é a função do servidor DNS?",
     "Limpar vírus do teclado",
     "Traduzir nomes de sites (como duno.com) no número de IP real",
     "Comprar domínios na internet",
     "Aumentar o volume dos vídeos",
     "B", "O DNS é a 'lista telefônica da internet'. Você digita o nome e ele descobre o IP para conectar!", 25),

    # ── LIÇÃO 4: O Carteiro (HTTP/HTTPS) ──
    (4, 1, "O que a letra 'S' em HTTPS significa?",
     "Speed (Rápido)",
     "Secure (Seguro — com criptografia SSL/TLS)",
     "Simple (Simples)",
     "System (Sistema)",
     "B", "O HTTPS protege os dados trafegados entre seu navegador e o servidor com um cofre criptográfico impenetrável!", 25),

    # ── LIÇÃO 5: Radar de Rede ──
    (5, 1, "Para que serve o comando ping?",
     "Para tocar música",
     "Para enviar pacotes ICMP e testar se um servidor está acessível",
     "Para apagar o disco",
     "Para desligar a tela",
     "B", "O ping mede a conectividade e o tempo de resposta da máquina de destino!", 25),

    # ── LIÇÃO 6: O Cérebro do Computador (OS) ──
    (6, 1, "Qual é o papel principal de um Sistema Operacional (OS)?",
     "Apenas ligar as luzes do teclado",
     "Organizar arquivos, controlar a memória e permitir que programas rodem",
     "Tirar fotos automáticas da tela",
     "Desconectar a internet quando você joga",
     "B", "O Sistema Operacional é como o diretor da escola: organiza recursos, programas e dispositivos para tudo funcionar em harmonia!", 25),

    # ── LIÇÃO 7: A Caverna do Terminal ──
    (7, 1, "Por que profissionais de segurança preferem usar o terminal?",
     "Porque não gostam de cores",
     "Porque é muito mais rápido, poderoso e permite automação com scripts",
     "Porque o mouse é proibido por lei",
     "Porque gasta menos bateria do monitor",
     "B", "O terminal permite dar instruções diretas ao computador e automatizar tarefas complexas em milissegundos!", 25),

    # ── LIÇÃO 8: Navegando no Escuro ──
    (8, 1, "Qual comando lista todos os arquivos e pastas do diretório onde você está?",
     "cd", "ls", "pwd", "mkdir",
     "B", "O comando 'ls' (List) mostra todos os arquivos e pastas visíveis no diretório atual.", 25),

    # ── LIÇÃO 9: As Chaves do Reino (Permissões) ──
    (9, 1, "O que significam as letras de permissão 'r', 'w' e 'x' no Linux?",
     "Restart, Wait e Exit",
     "Read (Ler), Write (Escrever) e Execute (Executar)",
     "Red, White e Xenon",
     "Root, Web e X-ray",
     "B", "'r' permite ler o arquivo, 'w' permite editar/salvar e 'x' permite rodar o arquivo como um programa!", 25),

    # ── LIÇÃO 10: A Receita de Bolo (Lógica) ──
    (10, 1, "O que é um Algoritmo?",
     "O nome do primeiro programador",
     "Uma sequência finita e lógica de passos para resolver um problema",
     "Um vírus de computador",
     "Um teclado especial",
     "B", "Assim como uma receita de bolo, o algoritmo dita passo a passo o que deve ser feito para alcançar o resultado.", 25),

    # ── LIÇÃO 11: Caixas e Etiquetas (Variáveis) ──
    (11, 1, "O que é uma Variável em programação?",
     "Uma caixa com nome na memória do computador para armazenar dados",
     "Um botão que quebra o teclado",
     "Um cabo desconectado",
     "Uma foto da internet",
     "A", "Variáveis guardam números, palavras ou estados para serem lidos e modificados durante o programa.", 25),

    # ── LIÇÃO 12: O Semáforo (If/Else) ──
    (12, 1, "Como funciona a estrutura de decisão If / Else?",
     "Executa todos os comandos de uma vez só",
     "Se (If) a condição for verdadeira faz uma coisa, senão (Else) faz outra",
     "Desliga o computador",
     "Apaga o código-fonte",
     "B", "O computador avalia a expressão lógica e desvia o fluxo do programa com base no resultado verdadeiro ou falso.", 25),

    # ── LIÇÃO 13: A Magia do Python ──
    (13, 1, "Qual comando em Python imprime uma mensagem na tela?",
     "echo << print", "print('Olá, DUNO!')", "write.screen()", "display.now()",
     "B", "A função print() em Python escreve o texto fornecido diretamente no terminal.", 25),

    # ── LIÇÃO 14: O Triângulo Mágico (Tríade CIA) ──
    (14, 1, "Quais são os 3 pilares da Tríade CIA em segurança da informação?",
     "Carros, Internet e Aviões",
     "Confidencialidade, Integridade e Disponibilidade",
     "Código, Imagem e Áudio",
     "Cookies, IPs e Antivírus",
     "B", "A Tríade CIA é a base de toda a segurança moderna: proteger o segredo, impedir alterações indevidas e manter no ar!", 25),

    # ── LIÇÃO 15: A Chave da Porta (Senhas & 2FA) ──
    (15, 1, "O que é um ataque de Força Bruta (Brute Force)?",
     "Bater com o teclado na mesa",
     "Testar milhares ou milhões de senhas automaticamente até adivinhar a correta",
     "Cortar os cabos de internet com alicate",
     "Mandar vírus pelo correio",
     "B", "Programas automatizados testam dicionários inteiros de senhas comuns contra formulários desprotegidos.", 25),

    # ── LIÇÃO 16: O Pescador de Dados (Phishing) ──
    (16, 1, "O que caracteriza um golpe de Phishing?",
     "Pescar peixes com redes digitais",
     "Uma mensagem falsa que imita uma entidade confiável para enganar a vítima e roubar credenciais",
     "Um jogo de pescaria online",
     "Um erro de conexão no roteador",
     "B", "Engenharia social pura: golpistas criam sites e e-mails idênticos a bancos para coletar senhas desavisadas!", 25),

    # ── LIÇÃO 17: Os Guardas do Castelo (Firewall) ──
    (17, 1, "Qual é a principal responsabilidade de um Firewall?",
     "Apagar o fogo do computador",
     "Monitorar e filtrar o tráfego de rede, bloqueando conexões e portas não autorizadas",
     "Limpar a poeira do gabinete",
     "Deixar os downloads mais coloridos",
     "B", "O Firewall atua como o segurança da portaria: decide exatamente quem pode entrar e sair da sua rede!", 25),

    # ── LIÇÃO 18: O Alfabeto do Hacker (Inglês) ──
    (18, 1, "De qual palavra em inglês vem o comando 'cat'?",
     "Cat (Gato)", "Concatenate (Juntar/Exibir sequencialmente)", "Catch (Pegar)", "Catalog (Catálogo)",
     "B", "O comando cat concatena e exibe o conteúdo de um arquivo diretamente na tela do terminal!", 25),

    # ── LIÇÃO 19: Palavras que Assustam ──
    (19, 1, "O que significa 'Payload' em um teste de invasão?",
     "O dinheiro que o hacker ganha",
     "A carga útil ou código executado no alvo após o exploit obter sucesso",
     "O peso do computador",
     "O botão de salvar",
     "B", "O exploit abre a brecha; o payload é o que é entregue lá dentro (como uma shell reversa)!", 25),

    # ── LIÇÃO 20: Lendo as Instruções (Man Pages) ──
    (20, 1, "Qual comando abre o manual oficial de um comando no Linux?",
     "helpme", "man <comando>", "read-book", "ask-google",
     "B", "'man ls' ou 'man chmod' abre a página de manual (Man Page) completa e documentada do comando!", 25),

    # ── LIÇÃO 21: Falando com o Mundo ──
    (21, 1, "O que é uma 'Proof of Concept' (PoC)?",
     "Uma prova de conceito demonstrando tecnicamente que uma vulnerabilidade é real",
     "Um certificado de compra de computador",
     "Uma foto da placa-mãe",
     "Uma mensagem de despedida",
     "A", "Uma PoC reproduz a falha de forma clara e controlada para que a equipe de defesa consiga corrigi-la.", 25)
]


def init_kids_db(db):
    """Executa o DDL das tabelas Kids e popula o conteúdo das 5 Trilhas e 21 Lições."""
    db.executescript(KIDS_DDL)

    # Remove módulos e lições legadas (ex: coding, cyber)
    db.execute("DELETE FROM kids_modules WHERE id NOT IN ('networks', 'os', 'programming', 'security', 'english')")
    db.execute("DELETE FROM kids_lessons WHERE module_id NOT IN ('networks', 'os', 'programming', 'security', 'english')")

    # Inserção/Atualização dos 5 Módulos
    for m in INITIAL_MODULES:
        db.execute(
            """INSERT INTO kids_modules (id, name, icon, description, order_idx) 
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET name=excluded.name, icon=excluded.icon, description=excluded.description, order_idx=excluded.order_idx""",
            m
        )

    # Inserção/Atualização das Lições
    for l in INITIAL_LESSONS:
        db.execute(
            """INSERT INTO kids_lessons (id, module_id, slug, title, subtitle, icon, order_idx, xp_reward, coins_reward) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET module_id=excluded.module_id, slug=excluded.slug, title=excluded.title, subtitle=excluded.subtitle, icon=excluded.icon, order_idx=excluded.order_idx, xp_reward=excluded.xp_reward, coins_reward=excluded.coins_reward""",
            l
        )

    # Inserção dos Quizzes se ainda não estiverem populados
    cur = db.execute("SELECT COUNT(*) FROM kids_quizzes")
    if cur.fetchone()[0] < len(INITIAL_QUIZZES):
        db.execute("DELETE FROM kids_quizzes")
        for q in INITIAL_QUIZZES:
            db.execute(
                """INSERT INTO kids_quizzes 
                   (lesson_id, order_idx, question, option_a, option_b, option_c, option_d, correct_option, explanation, xp) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                q
            )
    db.commit()


def get_or_create_kids_stats(db, user_id):
    """Obtém os atributos gamificados do usuário no Kids ou inicializa com valores padrão."""
    row = db.execute("SELECT * FROM kids_user_stats WHERE user_id = ?", (user_id,)).fetchone()
    today_str = date.today().isoformat()
    if not row:
        db.execute(
            """INSERT INTO kids_user_stats 
               (user_id, xp, level, coins, lives, max_lives, streak_days, last_active_date, league, chests_opened)
               VALUES (?, 0, 1, 50, 5, 5, 1, ?, 'Bronze', 0)""",
            (user_id, today_str)
        )
        db.commit()
        row = db.execute("SELECT * FROM kids_user_stats WHERE user_id = ?", (user_id,)).fetchone()
    
    # Atualiza streak se for um novo dia consecutivo
    last_date = row["last_active_date"]
    if last_date != today_str:
        try:
            diff = (date.today() - date.fromisoformat(last_date)).days
            if diff == 1:
                new_streak = row["streak_days"] + 1
            elif diff > 1:
                new_streak = 1
            else:
                new_streak = row["streak_days"]
        except Exception:
            new_streak = 1
        
        # Recupera vidas completas no novo dia
        db.execute(
            "UPDATE kids_user_stats SET last_active_date = ?, streak_days = ?, lives = max_lives WHERE user_id = ?",
            (today_str, new_streak, user_id)
        )
        db.commit()
        row = db.execute("SELECT * FROM kids_user_stats WHERE user_id = ?", (user_id,)).fetchone()

    # Garante que as missões diárias de hoje existam
    _ensure_daily_quests(db, user_id, today_str)
    return row


def _ensure_daily_quests(db, user_id, today_str):
    """Gera o conjunto diário de 3 missões para o usuário."""
    cur = db.execute("SELECT COUNT(*) FROM kids_quests WHERE user_id = ? AND quest_date = ?", (user_id, today_str))
    if cur.fetchone()[0] == 0:
        daily_templates = [
            ("Conclua 1 Lição na Trilha", 60, 20, 1, "bronze"),
            ("Acerte 3 Perguntas de Quiz", 50, 15, 3, None),
            ("Estude Comandos no Terminal", 75, 25, 1, "silver")
        ]
        for title, xp, coins, target, chest in daily_templates:
            db.execute(
                """INSERT INTO kids_quests 
                   (user_id, title, reward_xp, reward_coins, reward_chest, target_count, current_count, claimed, quest_date)
                   VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?)""",
                (user_id, title, xp, coins, chest, target, today_str)
            )
        db.commit()
