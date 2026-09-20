"""modules/kids/kids_content.py — Conteúdo Pedagógico Interativo e Laboratórios da DUNO Kids.
Fornece Teoria Interativa com o Mascote Tux, Mini-Laboratórios (Terminal, Sequência, Inspetor)
e Dicas Didáticas para todas as 21 lições do currículo.
"""

LESSON_INTERACTIVE_DATA = {
    # ══════════════════════════════════════════════════════════════════════════════
    # TRILHA 1: REDE DE COMPUTADORES (Lições 1 a 5)
    # ══════════════════════════════════════════════════════════════════════════════
    1: {
        "lesson_id": 1,
        "title": "O que é a Internet?",
        "theory_slides": [
            {
                "title": "A Teia Invisível que Conecta o Mundo",
                "mascot_pose": "estudando",
                "tux_speech": "Ei! Você já se perguntou como uma mensagem sua chega ao Japão em menos de um segundo? A Internet não é mágica, é uma rede física gigante!",
                "analogy": "Imagine uma ferrovia global: em vez de trens transportando pessoas, cabos submarinos e antenas transportam bilhões de letrinhas e números!",
                "badge": "CONCEITO FUNDAMENTAL",
                "points": [
                    "A Internet é uma rede de computadores conversando entre si.",
                    "Mais de 95% dos dados viajam por cabos de fibra óptica no fundo dos oceanos.",
                    "Servidores são supercomputadores que guardam sites e respondem aos seus pedidos."
                ],
                "code_preview": "Seu Computador ──[Cabo/Wi-Fi]──> Roteador ──[Fibra Submarina]──> Servidor da Web"
            },
            {
                "title": "Clientes e Servidores: Uma Conversa Real",
                "mascot_pose": "guiando",
                "tux_speech": "Quando você abre o navegador e acessa o DUNO, você é o Cliente (fazendo um pedido) e o computador central é o Servidor (entregando a página).",
                "analogy": "É exatamente como uma lanchonete: você pede o cardápio (Requisição) e o garçom traz o lanche prontinho (Resposta)!",
                "badge": "CLIENTE VS SERVIDOR",
                "points": [
                    "Cliente: o dispositivo que pede informações (seu notebook, tablet ou celular).",
                    "Servidor: a máquina poderosa que atende milhares de pessoas ao mesmo tempo.",
                    "Sem servidores, os sites não teriam onde morar!"
                ],
                "code_preview": "Requisição: GET /kids HTTP/1.1\nResposta: 200 OK (Aqui está a sua lição!)"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Testando a Conexão Global",
            "instruction": "Vamos testar se a Internet está viva no seu computador! Digite o comando ping duno.kids e pressione Enter para enviar pacotes de teste.",
            "target_command": "ping duno.kids",
            "commands": {
                "ping duno.kids": {
                    "output": "PING duno.kids (192.168.1.10): 56 data bytes\n64 bytes from 192.168.1.10: icmp_seq=0 ttl=64 time=12.4 ms\n64 bytes from 192.168.1.10: icmp_seq=1 ttl=64 time=11.8 ms\n64 bytes from 192.168.1.10: icmp_seq=2 ttl=64 time=12.1 ms\n\n--- duno.kids ping statistics ---\n3 packets transmitted, 3 packets received, 0.0% packet loss\nround-trip min/avg/max = 11.8/12.1/12.4 ms",
                    "tux_reaction": "Demais! Os 3 pacotes foram e voltaram em apenas 12 milissegundos. A sua conexão com a rede mundial está voando!",
                    "completed": True
                },
                "help": {
                    "output": "Comandos aceitos neste lab: ping duno.kids, status, clear",
                    "tux_reaction": "Experimente rodar: ping duno.kids",
                    "completed": False
                },
                "status": {
                    "output": "Interface de Rede: eth0 [CONECTADA]\nIP Local: 192.168.0.42\nGateway: 192.168.0.1",
                    "tux_reaction": "Tudo conectado! Agora rode: ping duno.kids",
                    "completed": False
                }
            },
            "quick_buttons": ["ping duno.kids", "status", "help"]
        },
        "hint": "Lembre-se: a internet é uma rede física de computadores interligados por cabos e sinais de rádio."
    },

    2: {
        "lesson_id": 2,
        "title": "O que é um Endereço IP?",
        "theory_slides": [
            {
                "title": "O CEP e o RG de Cada Dispositivo",
                "mascot_pose": "estudando",
                "tux_speech": "Como o carteiro sabe em qual casa entregar uma encomenda? Pelo CEP e número da casa! Na internet, esse endereço se chama IP (Internet Protocol).",
                "analogy": "Sem endereço, nenhuma carta chega ao destino. Sem IP, nenhum computador sabe para onde mandar os vídeos ou fotos que você clica!",
                "badge": "ENDEREÇAMENTO IP",
                "points": [
                    "Todo celular, impressora e servidor conectado tem seu próprio endereço IP.",
                    "O formato mais comum é o IPv4, composto por quatro números de 0 a 255.",
                    "Exemplo de IP da sua rede doméstica: 192.168.1.1"
                ],
                "code_preview": "IPv4: 192.168.1.10  <-- Quatro blocos numéricos separados por ponto!"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Descobrindo seu IP Local",
            "instruction": "Descubra qual é a identidade da sua máquina na rede! Digite o comando ip addr e aperte Enter.",
            "target_command": "ip addr",
            "commands": {
                "ip addr": {
                    "output": "1: lo: <LOOPBACK,UP> mtu 65536\n    inet 127.0.0.1/8 scope host lo\n2: eth0: <BROADCAST,MULTICAST,UP> mtu 1500\n    inet 192.168.1.42/24 brd 192.168.1.255 scope global eth0",
                    "tux_reaction": "Achou! O endereço IPv4 da sua placa eth0 é 192.168.1.42. Cada máquina da sua casa tem um final diferente!",
                    "completed": True
                },
                "ifconfig": {
                    "output": "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>\n        inet 192.168.1.42  netmask 255.255.255.0",
                    "tux_reaction": "Boa! ifconfig é o comando clássico. O seu IP é 192.168.1.42!",
                    "completed": True
                },
                "help": {
                    "output": "Comandos aceitos: ip addr, ifconfig, clear",
                    "tux_reaction": "Digite: ip addr",
                    "completed": False
                }
            },
            "quick_buttons": ["ip addr", "ifconfig", "help"]
        },
        "hint": "Um endereço IPv4 é formado por 4 números separados por pontos, como 192.168.1.10."
    },

    3: {
        "lesson_id": 3,
        "title": "O GPS da Web: DNS",
        "theory_slides": [
            {
                "title": "A Lista Telefônica da Internet",
                "mascot_pose": "guiando",
                "tux_speech": "Você decorou o número de telefone de todos os seus amigos? Quase ninguém decora! Nós guardamos os nomes na agenda. O DNS faz exatamente isso com sites!",
                "analogy": "Quando você digita 'duno.com', o DNS procura na agenda e descobre: 'Opa, o IP desse site é 142.250.190.46'!",
                "badge": "SISTEMA DE NOMES DE DOMÍNIO",
                "points": [
                    "DNS significa Domain Name System.",
                    "Computadores conversam com números (IPs), mas humanos preferem nomes legíveis.",
                    "Sem o DNS, você precisaria digitar 142.250.190.46 toda vez que quisesse pesquisar algo!"
                ],
                "code_preview": "Você digita: duno.com\nDNS responde: 'Conecte em 192.168.1.100!'"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Consultando o DNS",
            "instruction": "Vamos pedir ao DNS para traduzir o nome de um site em IP! Digite nslookup duno.com e veja a mágica acontecer.",
            "target_command": "nslookup duno.com",
            "commands": {
                "nslookup duno.com": {
                    "output": "Server:         8.8.8.8 (Google DNS)\nAddress:        8.8.8.8#53\n\nNon-authoritative answer:\nName:   duno.com\nAddress: 104.21.55.120\nAddress: 172.67.182.202",
                    "tux_reaction": "Perfeito! O servidor DNS 8.8.8.8 consultou a tabela mundial e encontrou os IPs de duno.com em milissegundos!",
                    "completed": True
                },
                "dig duno.com": {
                    "output": ";; ANSWER SECTION:\nduno.com.   300 IN  A   104.21.55.120",
                    "tux_reaction": "Show de bola! O comando dig é a ferramenta favorita dos hackers éticos para checar DNS!",
                    "completed": True
                }
            },
            "quick_buttons": ["nslookup duno.com", "dig duno.com"]
        },
        "hint": "O DNS é o tradutor que transforma nomes como duno.com no número de IP real do servidor."
    },

    4: {
        "lesson_id": 4,
        "title": "O Carteiro (HTTP/HTTPS)",
        "theory_slides": [
            {
                "title": "Cartas Abertas vs Cofres Blindados",
                "mascot_pose": "estudando",
                "tux_speech": "Quando você envia uma senha pela web, como ter certeza de que ninguém no caminho está espiando? É aí que entra a letra 'S' de HTTPS!",
                "analogy": "HTTP comum é como mandar um cartão-postal: qualquer carteiro ou curioso pode ler no caminho. HTTPS é colocar a carta em um cofre com cadeado criptográfico!",
                "badge": "SEGURANÇA SSL/TLS",
                "points": [
                    "HTTP: protocolo padrão de transferência de hipertexto (não criptografado).",
                    "HTTPS: HTTP com camada Secure (criptografia com chaves secretas).",
                    "Procure sempre pelo símbolo de cadeado na barra de endereços do navegador!"
                ],
                "code_preview": "HTTP  (Inseguro): senha='123'  <-- Qualquer um vê no Wi-Fi!\nHTTPS (Protegido): 9f8a6b2c...  <-- Criptografado e indecifrável!"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Inspecionando o Cadeado HTTPS",
            "instruction": "Use o utilitário curl com a flag -I para ver os cabeçalhos de segurança do site. Digite curl -I https://duno.com",
            "target_command": "curl -I https://duno.com",
            "commands": {
                "curl -I https://duno.com": {
                    "output": "HTTP/2 200\nserver: cloudflare\nstrict-transport-security: max-age=31536000; includeSubDomains\ncontent-type: text/html; charset=UTF-8\nx-content-type-options: nosniff",
                    "tux_reaction": "Excelente! Veja a linha 'strict-transport-security': o servidor exige conexão 100% criptografada!",
                    "completed": True
                }
            },
            "quick_buttons": ["curl -I https://duno.com"]
        },
        "hint": "A letra 'S' no final de HTTPS significa 'Secure' e garante que a comunicação é protegida por criptografia."
    },

    5: {
        "lesson_id": 5,
        "title": "O Radar de Rede",
        "theory_slides": [
            {
                "title": "Comandos de Diagnóstico de Redes",
                "mascot_pose": "guiando",
                "tux_speech": "Especialistas em computação não adivinham se a internet caiu: eles usam ferramentas de linha de comando como ping e traceroute para mapear o caminho!",
                "analogy": "É como o sonar de um submarino: você emite um bipe sonoro e cronometra quanto tempo o eco demora para voltar da montanha!",
                "badge": "FERRAMENTAS DE RADAR",
                "points": [
                    "ping: envia ecos ICMP para saber se um computador remoto está acordado.",
                    "traceroute / tracert: mostra cada roteador pelo qual seu pacote passou até o destino.",
                    "Latência: o tempo em milissegundos (ms) que a viagem de ida e volta levou."
                ],
                "code_preview": "traceroute duno.com\n1  192.168.1.1 (Seu Roteador)\n2  10.20.0.1  (Provedor)\n3  104.21.55.1 (Servidor Final)"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Rastreando o Sonar",
            "instruction": "Descubra o tempo de resposta do servidor central digitando ping -c 3 8.8.8.8",
            "target_command": "ping -c 3 8.8.8.8",
            "commands": {
                "ping -c 3 8.8.8.8": {
                    "output": "PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.\n64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=8.21 ms\n64 bytes from 8.8.8.8: icmp_seq=2 ttl=118 time=7.94 ms\n64 bytes from 8.8.8.8: icmp_seq=3 ttl=118 time=8.10 ms\n\n--- 8.8.8.8 ping statistics ---\n3 packets transmitted, 3 received, 0% packet loss, time 2002ms",
                    "tux_reaction": "Radar operacional! 0% de perda de pacotes e tempo de apenas 8ms. Sua rota está ultra veloz!",
                    "completed": True
                }
            },
            "quick_buttons": ["ping -c 3 8.8.8.8"]
        },
        "hint": "O comando ping utiliza pacotes de eco ICMP para medir a resposta e disponibilidade de uma máquina."
    },

    # ══════════════════════════════════════════════════════════════════════════════
    # TRILHA 2: SISTEMAS OPERACIONAIS (Lições 6 a 9)
    # ══════════════════════════════════════════════════════════════════════════════
    6: {
        "lesson_id": 6,
        "title": "O Cérebro do Computador",
        "theory_slides": [
            {
                "title": "O Que Faz um Sistema Operacional?",
                "mascot_pose": "estudando",
                "tux_speech": "Um computador sem Sistema Operacional é só uma caixa com peças de silício e plástico. O SO é a alma que faz tudo conversar!",
                "analogy": "O Sistema Operacional é como o maestro de uma grande orquestra: ele diz quando a bateria entra, quando o violino toca e não deixa ninguém atropelar o outro!",
                "badge": "SISTEMA OPERACIONAL",
                "points": [
                    "Gerencia memória RAM, processador (CPU) e disco rígido.",
                    "Permite que seus jogos, navegadores e ferramentas rodem ao mesmo tempo.",
                    "Exemplos famosos: Linux (meu favorito!), Windows, macOS e Android."
                ],
                "code_preview": "[Seus Aplicativos / Jogos]\n         ↓\n[Sistema Operacional (Kernel Linux)]\n         ↓\n[Hardware (CPU, Memória, Placa de Vídeo)]"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Inspecionando o Sistema",
            "instruction": "Vamos ver as informações do sistema operacional rodando! Digite uname -a e aperte Enter.",
            "target_command": "uname -a",
            "commands": {
                "uname -a": {
                    "output": "Linux duno-penguin-station 6.6.14-kids #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux",
                    "tux_reaction": "Maravilha! Você está usando o Kernel Linux versão 6.6. É o mesmo cérebro que comanda foguetes espaciais e os maiores servidores do mundo!",
                    "completed": True
                }
            },
            "quick_buttons": ["uname -a"]
        },
        "hint": "O SO organiza os recursos da máquina (memória, processador, arquivos) para que os programas possam funcionar."
    },

    7: {
        "lesson_id": 7,
        "title": "A Caverna do Terminal",
        "theory_slides": [
            {
                "title": "O Poder das Palavras de Comando",
                "mascot_pose": "guiando",
                "tux_speech": "Antes de existirem botões e mouses, todo mundo conversava com computadores pelo Terminal. E adivinhe só? Os profissionais de segurança ainda preferem assim!",
                "analogy": "Usar o mouse é como apontar com o dedo no restaurante. Usar o terminal é falar o dialeto nativo do computador: muito mais rápido e sem limites!",
                "badge": "O SHELL DO LINUX",
                "points": [
                    "O terminal executa comandos diretamente com o processador.",
                    "Com uma única linha, você pode fazer tarefas que levariam horas no clique do mouse.",
                    "Você digita um comando, aperta Enter e a máquina obedece na hora."
                ],
                "code_preview": "aluno@duno:~$ echo 'Olá, Terminal!'\nOlá, Terminal!"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Seu Primeiro Eco no Shell",
            "instruction": "Digite echo 'Olá Tux' no terminal para fazer o computador repetir a sua mensagem!",
            "target_command": "echo 'Olá Tux'",
            "commands": {
                "echo 'Olá Tux'": {
                    "output": "Olá Tux",
                    "tux_reaction": "Olá! Que alegria te ver no terminal! O comando 'echo' imprime na tela qualquer texto que você passar.",
                    "completed": True
                },
                "echo Ola Tux": {
                    "output": "Ola Tux",
                    "tux_reaction": "Muito bom! Você deu vida ao terminal!",
                    "completed": True
                }
            },
            "quick_buttons": ["echo 'Olá Tux'"]
        },
        "hint": "Profissionais usam o terminal porque ele é muito mais rápido, direto e permite criar scripts de automação."
    },

    8: {
        "lesson_id": 8,
        "title": "Navegando no Escuro",
        "theory_slides": [
            {
                "title": "Comandos Básicos de Exploração",
                "mascot_pose": "estudando",
                "tux_speech": "No terminal não existem pastinhas coloridas para clicar. Nós usamos três comandos sagrados: pwd, ls e cd!",
                "analogy": "pwd é sua bússola ('onde estou?'). ls é acender a lanterna ('o que tem aqui?'). cd é andar para outra sala!",
                "badge": "BÚSSOLA DO SHELL",
                "points": [
                    "pwd: Print Working Directory (mostra em qual pasta você está).",
                    "ls: List (lista os arquivos e pastas deste local).",
                    "cd: Change Directory (muda para outra pasta).",
                    "mkdir: Make Directory (cria uma pasta nova)."
                ],
                "code_preview": "$ pwd\n/home/aluno\n$ ls\nDocumentos  Downloads  missoes_secretas"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Encontrando o Arquivo Secreto",
            "instruction": "Use o comando ls para inspecionar os arquivos da pasta atual e depois use cat segredo.txt para ler o que está dentro!",
            "target_command": "cat segredo.txt",
            "commands": {
                "ls": {
                    "output": "anotações.md  foto_tux.png  segredo.txt  regras.cfg",
                    "tux_reaction": "Olha ali! O arquivo 'segredo.txt' apareceu! Agora digite cat segredo.txt para ler o conteúdo dele!",
                    "completed": False
                },
                "pwd": {
                    "output": "/home/aluno/laboratorio",
                    "tux_reaction": "Você está em /home/aluno/laboratorio. Use ls para ver os arquivos!",
                    "completed": False
                },
                "cat segredo.txt": {
                    "output": "🔐 [MENSAGEM SECRETA DO TUX]:\n'Você acaba de dominar os comandos mais importantes do Linux! O caminho do hacker ético começa aqui.'",
                    "tux_reaction": "UAU! Você decodificou o segredo com perfeição! Agora você sabe listar e ler arquivos como um verdadeiro profissional.",
                    "completed": True
                }
            },
            "quick_buttons": ["ls", "cat segredo.txt", "pwd"]
        },
        "hint": "O comando 'ls' (List) mostra todos os arquivos e pastas da pasta em que você se encontra."
    },

    9: {
        "lesson_id": 9,
        "title": "As Chaves do Reino",
        "theory_slides": [
            {
                "title": "Permissões de Arquivos: r, w, x",
                "mascot_pose": "guiando",
                "tux_speech": "No Linux, nem todo mundo pode mexer em tudo. Cada arquivo tem um cadeado com três regras claras: Ler, Escrever e Executar!",
                "analogy": "Ler (r) é folhear um livro na biblioteca. Escrever (w) é poder rabiscar nele. Executar (x) é apertar o botão de ligar o robô!",
                "badge": "SISTEMA DE PERMISSÕES",
                "points": [
                    "r = Read (Ler o conteúdo do arquivo).",
                    "w = Write (Alterar, editar ou deletar o arquivo).",
                    "x = Execute (Rodar o arquivo como programa ou script).",
                    "chmod é o comando usado para trocar essas permissões!"
                ],
                "code_preview": "-rwxr-xr-- 1 tux kids 1024 script.sh\n rwx = Dono pode Ler, Escrever e Rodar!"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Concedendo Permissão de Execução",
            "instruction": "O script de segurança precisa de permissão para rodar. Digite chmod +x script.sh e depois rode com ./script.sh",
            "target_command": "./script.sh",
            "commands": {
                "chmod +x script.sh": {
                    "output": "Permissão 'execute' (+x) concedida para script.sh com sucesso!",
                    "tux_reaction": "Boa! Agora que tem permissão 'x', digite ./script.sh para rodar o programa!",
                    "completed": False
                },
                "./script.sh": {
                    "output": "🚀 [INICIANDO SISTEMA DE DEFESA DUNO KIDS]...\nStatus: 100% SEGURO! Parabéns pelo domínio do chmod.",
                    "tux_reaction": "Sensacional! O script rodou porque você adicionou a permissão correta!",
                    "completed": True
                },
                "ls -l": {
                    "output": "-rwxr-xr-x 1 aluno aluno 42 script.sh",
                    "tux_reaction": "Repare nos 'x' verdes! O arquivo agora é executável. Digite ./script.sh!",
                    "completed": False
                }
            },
            "quick_buttons": ["chmod +x script.sh", "./script.sh", "ls -l"]
        },
        "hint": "As letras representam: r = Read (Ler), w = Write (Escrever/Gravar) e x = Execute (Executar)."
    },

    # ══════════════════════════════════════════════════════════════════════════════
    # TRILHA 3: PROGRAMAÇÃO (Lições 10 a 13)
    # ══════════════════════════════════════════════════════════════════════════════
    10: {
        "lesson_id": 10,
        "title": "A Receita de Bolo",
        "theory_slides": [
            {
                "title": "O Que é Lógica de Programação?",
                "mascot_pose": "estudando",
                "tux_speech": "Programar não é decorar códigos mágicos: é ensinar o computador a resolver um problema passo a passo, na ordem certa!",
                "analogy": "É como seguir uma receita de bolo: se você colocar a massa no forno antes de quebrar os ovos, vai dar tudo errado! A sequência exata importa.",
                "badge": "ALGORITMOS & PASSOS",
                "points": [
                    "Um algoritmo é uma sequência lógica de instruções claras.",
                    "Computadores fazem exatamente o que você manda, nem mais, nem menos.",
                    "Dividir problemas grandes em pedacinhos pequenos é o segredo de quem programa."
                ],
                "code_preview": "Passo 1: Abrir a porta\nPasso 2: Entrar na sala\nPasso 3: Acender a luz\n(Na ordem certa, tudo funciona!)"
            }
        ],
        "lab": {
            "type": "sequence",
            "title": "Mini-Lab do Tux: Montando a Receita do Robô",
            "instruction": "Clique nos passos abaixo na ordem correta para ensinar o robô a atravessar a rua com segurança!",
            "target_sequence": ["Olhar para os dois lados", "Verificar se o sinal está verde para pedestres", "Atravessar na faixa com atenção"],
            "options": [
                "Atravessar na faixa com atenção",
                "Olhar para os dois lados",
                "Verificar se o sinal está verde para pedestres"
            ],
            "tux_reaction": "Perfeito! Você construiu um algoritmo seguro: primeiro checar os dois lados, validar o sinal e só então atravessar!"
        },
        "hint": "Um algoritmo é uma sequência ordenada de instruções para realizar uma tarefa ou resolver um problema."
    },

    11: {
        "lesson_id": 11,
        "title": "Caixas e Etiquetas",
        "theory_slides": [
            {
                "title": "Guardando Coisas na Memória (Variáveis)",
                "mascot_pose": "guiando",
                "tux_speech": "Onde o jogo salva quantas moedas ou vidas você tem? Em caixas etiquetadas na memória chamadas Variáveis!",
                "analogy": "Imagine várias caixas de sapato. Em uma caixa você escreve 'vidas' com canetinha e coloca o número 5 dentro. Quando toma dano, você tira 1!",
                "badge": "VARIÁVEIS & TIPOS",
                "points": [
                    "Variável: um espaço na memória do computador com um nome e um valor.",
                    "Números inteiros (int): vidas = 5, moedas = 120.",
                    "Textos (strings): nome = 'Tux'."
                ],
                "code_preview": "vidas = 5\nnome_jogador = 'CyberKid'\nxp = 250"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Criando Sua Primeira Variável",
            "instruction": "No terminal interativo Python, crie uma variável com seu apelido: digite jogador = 'Heroi' e aperte Enter!",
            "target_command": "jogador = 'Heroi'",
            "commands": {
                "jogador = 'Heroi'": {
                    "output": ">>> Variável 'jogador' alocada na memória com valor 'Heroi'!",
                    "tux_reaction": "Boa! Agora digite print(jogador) para ver o valor guardado na caixa!",
                    "completed": False
                },
                "print(jogador)": {
                    "output": "Heroi",
                    "tux_reaction": "Incrível! A memória do computador guardou e devolveu o seu valor perfeitamente!",
                    "completed": True
                }
            },
            "quick_buttons": ["jogador = 'Heroi'", "print(jogador)"]
        },
        "hint": "Variáveis são como caixas com etiqueta que guardam valores (números, palavras) na memória do computador."
    },

    12: {
        "lesson_id": 12,
        "title": "O Semáforo (If/Else)",
        "theory_slides": [
            {
                "title": "Tomando Decisões no Código",
                "mascot_pose": "estudando",
                "tux_speech": "E se o sinal estiver vermelho? Você para! E se estiver verde? Você anda! Programas usam o comando 'if' (SE) para decidir o que fazer.",
                "analogy": "É uma encruzilhada com placa: SE o jogador tiver mais de 100 moedas, LIBERE a espada mágica. SENÃO, diga 'junte mais moedas'!",
                "badge": "CONDICIONAIS",
                "points": [
                    "if (se): executa o bloco se a condição for verdadeira.",
                    "else (senão): executa o bloco alternativo caso seja falsa.",
                    "Permite criar jogos inteligentes e sistemas de segurança que bloqueiam invasores."
                ],
                "code_preview": "if senha == 'secreta':\n    print('Acesso Liberado!')\nelse:\n    print('Alarme ativado!')"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: O Guardião da Porta",
            "instruction": "Teste o algoritmo de verificação de idade para o jogo! Digite checar_idade(12) e veja a resposta do sistema.",
            "target_command": "checar_idade(12)",
            "commands": {
                "checar_idade(12)": {
                    "output": ">>> Idade: 12\n>>> Condição: if idade >= 10: [VERDADEIRO]\n>>> Resultado: 'Acesso Liberado! Bem-vindo à arena DUNO Kids.'",
                    "tux_reaction": "Excelente! O if comparou se 12 é maior ou igual a 10 e tomou o caminho correto!",
                    "completed": True
                }
            },
            "quick_buttons": ["checar_idade(12)"]
        },
        "hint": "A estrutura if/else permite ao programa escolher entre dois caminhos baseado em uma condição verdadeira ou falsa."
    },

    13: {
        "lesson_id": 13,
        "title": "A Magia do Python",
        "theory_slides": [
            {
                "title": "A Linguagem Favorita dos Especialistas",
                "mascot_pose": "guiando",
                "tux_speech": "Python é tão limpo e gostoso de ler que parece inglês do dia a dia. Hackers éticos, cientistas e criadores de IA usam Python o tempo todo!",
                "analogy": "Enquanto outras linguagens exigem dezenas de linhas cheias de símbolos para imprimir uma frase, em Python você só escreve: print('Olá, mundo!')!",
                "badge": "PYTHON EM AÇÃO",
                "points": [
                    "Sintaxe limpa e fácil de aprender.",
                    "Mundialmente usada em segurança da informação, robótica e inteligência artificial.",
                    "Com 3 linhas de código, você cria um script que automatiza o seu dia!"
                ],
                "code_preview": "for i in range(3):\n    print('Tux aprendeu mais um poder!')"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Rodando um Script Python",
            "instruction": "Rode o script que gera um relatório de segurança em Python! Digite python3 missao.py e aperte Enter.",
            "target_command": "python3 missao.py",
            "commands": {
                "python3 missao.py": {
                    "output": "=== DUNO SECURITY SCANNER v1.0 ===\n[✓] Firewall: Ativo\n[✓] Senhas: Fortes\n[✓] Antivírus: Atualizado\nStatus: SEU SISTEMA ESTÁ BLINDADO!",
                    "tux_reaction": "Demais! O Python leu o arquivo, executou as verificações e imprimiu o relatório em segundos!",
                    "completed": True
                }
            },
            "quick_buttons": ["python3 missao.py"]
        },
        "hint": "Python é conhecida mundialmente por sua sintaxe simples e legível, ideal tanto para iniciantes quanto para especialistas."
    },

    # ══════════════════════════════════════════════════════════════════════════════
    # TRILHA 4: SECURITY (Lições 14 a 17)
    # ══════════════════════════════════════════════════════════════════════════════
    14: {
        "lesson_id": 14,
        "title": "O Triângulo Mágico (Tríade CIA)",
        "theory_slides": [
            {
                "title": "Os Três Pilares da Segurança",
                "mascot_pose": "estudando",
                "tux_speech": "Na segurança cibernética, tudo gira em torno de 3 palavras mágicas que formam a sigla CIA: Confidencialidade, Integridade e Disponibilidade!",
                "analogy": "Confidencialidade = só quem tem a chave entra. Integridade = ninguém alterou o texto no caminho. Disponibilidade = o site nunca cai quando você precisa!",
                "badge": "TRÍADE C.I.A.",
                "points": [
                    "Confidencialidade: manter segredos protegidos de olhos curiosos.",
                    "Integridade: garantir que os dados não foram adulterados ou corrompidos.",
                    "Disponibilidade: garantir que os sistemas estejam no ar 24/7 para quem tem direito."
                ],
                "code_preview": "Tríade CIA:\n  [C]onfidencialidade  ──> Criptografia\n  [I]ntegridade        ──> Hash e Assinatura\n  [A]vailability       ──> Servidores redundantes"
            }
        ],
        "lab": {
            "type": "inspector",
            "title": "Mini-Lab do Tux: Classificador da Tríade",
            "instruction": "Um invasor alterou a nota de uma prova no sistema escolar. Qual pilar da segurança foi violado?",
            "target_answer": "Integridade",
            "options": ["Confidencialidade", "Integridade", "Disponibilidade"],
            "tux_reaction": "Exatamente! Quando alguém altera um arquivo sem autorização, a INTEGRIDADE do dado foi destruída!"
        },
        "hint": "A Tríade CIA é composta por Confidencialidade (segredo), Integridade (exatidão sem alterações) e Disponibilidade (estar no ar)."
    },

    15: {
        "lesson_id": 15,
        "title": "A Chave da Porta",
        "theory_slides": [
            {
                "title": "Senhas Fortes vs Ataques de Força Bruta",
                "mascot_pose": "guiando",
                "tux_speech": "Você sabia que a senha '123456' pode ser adivinhada por um computador em menos de 1 segundo? Para se proteger, precisamos de senhas longas e 2FA!",
                "analogy": "Uma senha fraca é como colocar um cadeado de papel na porta. Uma senha forte é uma fechadura biométrica com chave mista e alarme!",
                "badge": "HIGIENE DE SENHAS & 2FA",
                "points": [
                    "Nunca use datas de aniversário, nomes de animais ou sequências óbvias.",
                    "Combine letras maiúsculas, minúsculas, números e símbolos especiais ($#@!).",
                    "Autenticação em 2 Fatores (2FA) pede um código no celular além da senha."
                ],
                "code_preview": "Fraca:  senha123       (Quebrada em 0.01s!)\nForte:  Tux#Voador!2026 (Levaria 500 anos para quebrar!)"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Testador de Força de Senha",
            "instruction": "Teste uma senha no nosso analisador cibernético! Digite check_password 'Tux#Voador!2026' e veja a pontuação.",
            "target_command": "check_password 'Tux#Voador!2026'",
            "commands": {
                "check_password 'Tux#Voador!2026'": {
                    "output": "Analisando: 'Tux#Voador!2026'\n[✓] Tamanho: 16 caracteres (Excelente)\n[✓] Maiúsculas e Minúsculas: Sim\n[✓] Símbolos especiais: Sim (!, #)\n[✓] Números: Sim\nFORÇA: 100/100 (BLINDADA CONTRA FORÇA BRUTA)",
                    "tux_reaction": "Nota 100! Essa senha levaria séculos para ser adivinhada por um supercomputador!",
                    "completed": True
                },
                "check_password '123456'": {
                    "output": "Analisando: '123456'\n[X] Muito curta!\n[X] Só números!\nFORÇA: 5/100 (PERIGO CRÍTICO)",
                    "tux_reaction": "Essa quebra em milissegundos! Teste: check_password 'Tux#Voador!2026'",
                    "completed": False
                }
            },
            "quick_buttons": ["check_password 'Tux#Voador!2026'", "check_password '123456'"]
        },
        "hint": "Uma senha segura mistura letras maiúsculas, minúsculas, números e caracteres especiais, além de ter bom comprimento."
    },

    16: {
        "lesson_id": 16,
        "title": "O Pescador de Dados (Phishing)",
        "theory_slides": [
            {
                "title": "Como Funciona a Isca Digital",
                "mascot_pose": "estudando",
                "tux_speech": "Phishing vem da palavra 'fishing' (pescaria). Em vez de peixes, criminosos jogam e-mails e links falsos esperando que você morda o anzol!",
                "analogy": "É como alguém bater na sua porta vestido de carteiro com um bigode falso de plástico dizendo: 'Me dê a chave da sua casa para eu guardar'!",
                "badge": "DETECTOR DE PHISHING",
                "points": [
                    "Sempre crie um senso falso de urgência ('Sua conta será apagada em 10 minutos!').",
                    "Olhe bem para o endereço do link: b4nco-falso.xyz não é o site oficial!",
                    "Erros de português e promessas de prêmios fáceis são sinais claros de golpe."
                ],
                "code_preview": "Oficial:  https://duno.com/login\nPhishing: http://duno-login-premio-gratis.tk (GOLPE!)"
            }
        ],
        "lab": {
            "type": "inspector",
            "title": "Mini-Lab do Tux: Detective de E-mails",
            "instruction": "Você recebeu uma mensagem misteriosa. Qual destes remetentes é claramente uma tentativa de Phishing?",
            "target_answer": "suporte@banco-urgente-premiado.xyz",
            "options": [
                "contato@duno.com",
                "suporte@banco-urgente-premiado.xyz",
                "notificacoes@google.com"
            ],
            "tux_reaction": "Na mosca! O domínio 'banco-urgente-premiado.xyz' é um golpe clássico com urgência e domínio suspeito!"
        },
        "hint": "Phishing é uma técnica de engenharia social que tenta enganar pessoas para roubar senhas e dados confidenciais."
    },

    17: {
        "lesson_id": 17,
        "title": "Os Guardas do Castelo",
        "theory_slides": [
            {
                "title": "Firewall: O Porteiro da Sua Rede",
                "mascot_pose": "guiando",
                "tux_speech": "O Firewall fica na portaria da sua rede conferindo o crachá de cada pacote de dados que tenta entrar ou sair!",
                "analogy": "Ele é o segurança da festa com uma prancheta de regras: 'Pacote do jogo DUNO? Pode entrar! Conexão estranha vinda de um computador desconhecido? Barrado!'",
                "badge": "FIREWALL & ANTIVÍRUS",
                "points": [
                    "Filtra conexões com base em regras de portas e endereços IP.",
                    "Bloqueia acessos não autorizados vindo de fora da sua rede.",
                    "Trabalha em conjunto com o antivírus para manter seu computador seguro."
                ],
                "code_preview": "Regra 1: Permitir porta 443 (HTTPS Web)\nRegra 2: Bloquear porta 23 (Telnet inseguro)\nRegra 3: Bloquear IPs da lista negra"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Ativando a Parede de Fogo (UFW)",
            "instruction": "Ative o firewall do sistema para barrar invasores! Digite ufw enable e aperte Enter.",
            "target_command": "ufw enable",
            "commands": {
                "ufw enable": {
                    "output": "Firewall is active and enabled on system startup\nDefault policy: deny (incoming), allow (outgoing)",
                    "tux_reaction": "Escudo erguido! Agora todas as tentativas de conexão suspeitas serão bloqueadas automaticamente!",
                    "completed": True
                },
                "ufw status": {
                    "output": "Status: active\nLogging: on (low)\nDefault: deny (incoming), allow (outgoing)",
                    "tux_reaction": "O firewall está ativo e vigilante!",
                    "completed": True
                }
            },
            "quick_buttons": ["ufw enable", "ufw status"]
        },
        "hint": "O Firewall inspeciona e filtra todo o tráfego de rede, bloqueando conexões perigosas ou não autorizadas."
    },

    # ══════════════════════════════════════════════════════════════════════════════
    # TRILHA 5: INGLÊS PARA CYBER (Lições 18 a 21)
    # ══════════════════════════════════════════════════════════════════════════════
    18: {
        "lesson_id": 18,
        "title": "O Alfabeto do Hacker",
        "theory_slides": [
            {
                "title": "De Onde Vêm os Comandos?",
                "mascot_pose": "estudando",
                "tux_speech": "Você sabia que os comandos do Linux são apenas abreviações de palavras normais em inglês? Quando você aprende o significado, nunca mais esquece!",
                "analogy": "É como um código secreto: 'ls' vem de 'List' (listar). 'cd' vem de 'Change Directory' (mudar de pasta). 'cat' vem de 'Concatenate' (juntar/ler)!",
                "badge": "VOCABULÁRIO NATIVO",
                "points": [
                    "ls = List (Listar)",
                    "cd = Change Directory (Mudar Diretório)",
                    "rm = Remove (Remover / Apagar)",
                    "cp = Copy (Copiar)"
                ],
                "code_preview": "ls  ==> List\ncd  ==> Change Directory\nrm  ==> Remove\npwd ==> Print Working Directory"
            }
        ],
        "lab": {
            "type": "sequence",
            "title": "Mini-Lab do Tux: Pareando Comandos com Inglês",
            "instruction": "Ordene os significados corretos dos comandos na ordem: ls, cd, rm",
            "target_sequence": ["List (Listar)", "Change Directory (Mudar de Pasta)", "Remove (Apagar)"],
            "options": [
                "Remove (Apagar)",
                "List (Listar)",
                "Change Directory (Mudar de Pasta)"
            ],
            "tux_reaction": "Sensacional! Sabendo inglês técnico, o terminal deixa de ser misterioso e vira uma conversa natural!"
        },
        "hint": "Comandos Linux são abreviações de termos em inglês: 'ls' vem de 'List' e 'cd' de 'Change Directory'."
    },

    19: {
        "lesson_id": 19,
        "title": "Palavras que Assustam",
        "theory_slides": [
            {
                "title": "Bug, Exploit, Payload e Patch",
                "mascot_pose": "guiando",
                "tux_speech": "Filmes adoram falar palavras difíceis como 'payload' e 'exploit'. Mas elas são muito simples quando entendemos o conceito!",
                "analogy": "Bug = uma rachadura na fechadura da porta. Exploit = o grampo que entra na rachadura. Patch = o conserto que tapa a rachadura!",
                "badge": "JARGÃO CYBER DESMISTIFICADO",
                "points": [
                    "Bug: um erro ou falha no código de um programa.",
                    "Vulnerabilidade: um bug que permite que alguém faça algo indevido.",
                    "Patch: uma atualização que conserta e fecha a brecha."
                ],
                "code_preview": "1. O pesquisador acha o [Bug]\n2. A empresa cria o [Patch]\n3. O sistema atualizado fica [Seguro]!"
            }
        ],
        "lab": {
            "type": "inspector",
            "title": "Mini-Lab do Tux: O Médico dos Programas",
            "instruction": "Quando uma empresa de jogos descobre uma falha e lança uma correção para todos baixarem, como se chama essa correção?",
            "target_answer": "Patch (Atualização de correção)",
            "options": [
                "Payload (Carga)",
                "Patch (Atualização de correção)",
                "Bug (Inseto/Falha)"
            ],
            "tux_reaction": "Exatamente! Um 'Patch' é o remendo/conserto digital que fecha a falha de segurança!"
        },
        "hint": "Patch é o termo em inglês para remendo ou atualização de software que corrige bugs e vulnerabilidades."
    },

    20: {
        "lesson_id": 20,
        "title": "Lendo as Instruções",
        "theory_slides": [
            {
                "title": "O Superpoder do 'man' e '--help'",
                "mascot_pose": "estudando",
                "tux_speech": "Nenhum hacker precisa decorar centenas de opções de comandos: o próprio terminal traz manuais completos embutidos!",
                "analogy": "É como ter o manual de instruções com índice e fotos dentro da caixa de cada brinquedo. Se você esquecer, é só abrir!",
                "badge": "DOCUMENTAÇÃO NO SHELL",
                "points": [
                    "comando --help: mostra um resumo rápido de como usar o comando.",
                    "man comando: abre o Manual completo e detalhado.",
                    "Saber ler a documentação é o superpoder número 1 de quem programa."
                ],
                "code_preview": "$ grep --help\nUsage: grep [OPTION]... PATTERNS [FILE]...\nSearch for PATTERNS in each FILE."
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Abrindo a Ajuda de um Comando",
            "instruction": "Peça ajuda ao comando curl digitando curl --help no terminal!",
            "target_command": "curl --help",
            "commands": {
                "curl --help": {
                    "output": "Usage: curl [options...] <url>\n -d, --data <data>          HTTP POST data\n -H, --header <header/@file> Pass custom header(s) to server\n -I, --head                 Show document info only\n -o, --output <file>        Write to file instead of stdout",
                    "tux_reaction": "Viu só? O manual te deu todas as opções mastigadas. Você nunca precisa adivinhar no escuro!",
                    "completed": True
                }
            },
            "quick_buttons": ["curl --help"]
        },
        "hint": "Adicionar a flag '--help' ao final de um comando exibe instruções rápidas de uso e opções disponíveis."
    },

    21: {
        "lesson_id": 21,
        "title": "Falando com o Mundo",
        "theory_slides": [
            {
                "title": "Relatórios Técnicos e Ética Hacker",
                "mascot_pose": "animado",
                "tux_speech": "Você chegou ao topo da jornada! Hackers éticos (White Hats) usam o inglês para escrever relatórios e avisar empresas sobre falhas antes que criminosos as encontrem!",
                "analogy": "É como um bombeiro perito: ele inspeciona o prédio, encontra onde o extintor está vencido e entrega um relatório claro para o síndico proteger todos!",
                "badge": "DISCLOSURE RESPONSÁVEL",
                "points": [
                    "PoC (Proof of Concept): demonstração prática e controlada da falha.",
                    "Responsible Disclosure: avisar a empresa dona do sistema com antecedência.",
                    "A comunidade global de segurança fala inglês para compartilhar defesas."
                ],
                "code_preview": "SECURITY REPORT #404:\n- Target: Web Portal\n- Finding: Weak password policy\n- Recommendation: Enable 2FA"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux: Assinando o Relatório Final",
            "instruction": "Assine seu primeiro relatório ético digitando submit_report --ethical e celebre sua formatura!",
            "target_command": "submit_report --ethical",
            "commands": {
                "submit_report --ethical": {
                    "output": "================================================\n🏆 DUNO KIDS CYBER CADET GRADUATION\nRelatório Ético Registrado com Sucesso!\nVocê concluiu todas as lições com o Tux!\n================================================",
                    "tux_reaction": "PARABÉNS! Você é oficialmente um Guardião Digital da DUNO Kids! O Tux tem muito orgulho de você!",
                    "completed": True
                }
            },
            "quick_buttons": ["submit_report --ethical"]
        },
        "hint": "Divulgação responsável (Responsible Disclosure) é relatar vulnerabilidades de forma privada e ética para que sejam corrigidas."
    }
}


def get_lesson_interactive_data(lesson_id: int):
    """Retorna os dados interativos ricos (Teoria, Lab, Dicas) para uma lição."""
    return LESSON_INTERACTIVE_DATA.get(lesson_id, {
        "lesson_id": lesson_id,
        "title": "Lição Interativa",
        "theory_slides": [
            {
                "title": "Explorando o Conhecimento",
                "mascot_pose": "estudando",
                "tux_speech": "Vamos aprender juntos! Preste atenção nos conceitos abaixo e prepare-se para o desafio.",
                "analogy": "Cada novo comando é uma ferramenta que você guarda na sua mochila cibernética!",
                "badge": "CONCEITO CHAVE",
                "points": ["Compreenda o objetivo", "Pratique no terminal", "Fixe o aprendizado"],
                "code_preview": "# Aprendendo com o Tux"
            }
        ],
        "lab": {
            "type": "terminal",
            "title": "Mini-Lab do Tux",
            "instruction": "Digite status e aperte Enter para verificar o laboratório.",
            "target_command": "status",
            "commands": {
                "status": {
                    "output": "Laboratório operacional!",
                    "tux_reaction": "Tudo pronto! Vamos em frente!",
                    "completed": True
                }
            },
            "quick_buttons": ["status"]
        },
        "hint": "Leia com atenção as instruções e siga a trilha com o Tux."
    })
