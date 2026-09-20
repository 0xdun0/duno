# Guia de Empacotamento & Submissão de Máquinas da Comunidade

O DUNO permite que qualquer pesquisador de segurança ou desenvolvedor submeta novas máquinas de laboratório para a comunidade. As submissões passam por uma esteira rigorosa de compilação, validação de segurança e publicação através do **Command Center**.

---

## 1. Estrutura Obrigatória do Pacote

O pacote submetido deve ser um arquivo compactado `.zip` ou `.tar.gz` (máximo de 50MB) contendo:

```text
minha-maquina.zip
├── manifest.yml          # Especificação de metadados, runtime e flags (obrigatório)
├── Dockerfile            # Configuração de build do container (ou docker-compose.yml)
├── README.md             # Documentação técnica e writeup da solução
└── app/                  # Código-fonte da aplicação vulnerável
```

---

## 2. Ciclo de Vida da Submissão (7 Estados)

Toda máquina submetida navega pelos seguintes estados controlados por máquina de estados formal:

1. **`draft`:** O autor cria o rascunho inicial no portal de submissões.
2. **`submitted`:** O pacote zip é enviado e passa pela checagem de integridade e magic bytes.
3. **`scanning`:** O worker executa a varredura estática de segurança e análise AST em busca de segredos vazados.
4. **`in_review`:** A submissão fica disponível na fila de moderação dos administradores no Command Center.
5. **`approved`:** Aprovada tecnicamente pela equipe de curadoria.
6. **`published`:** A máquina entra no catálogo público de desafios e passa a ser orquestrada pelo Challenge Runner.
7. **`rejected`:** A submissão é rejeitada com justificativa registrada no log de auditoria.

---

## 3. Checklist de Segurança para Aprovação

Para ser aceita na plataforma, sua máquina não pode conter:
* [x] Flags de execução privilegiada (`privileged: true` ou `CAP_SYS_ADMIN`).
* [x] Montagens de socket do Docker hospedeiro (`/var/run/docker.sock`).
* [x] Uso de rede host (`network_mode: host`).
* [x] Links simbólicos ou atalhos apontando para fora do pacote (proteção anti-ZipSlip).
* [x] Chaves de API privadas (AWS, GitHub, tokens de produção) em texto puro.
* [x] Comportamentos maliciosos reais contra a infraestrutura do host ou internet pública.

---

## 4. Como Submeter

1. Acesse o **Command Center** na aba **Minhas Contribuições** (`/command-center`).
2. Clique em **Nova Submissão de Máquina**.
3. Preencha o formulário e faça o upload do pacote `.zip` ou `.tar.gz`.
4. Acompanhe a esteira de validação em tempo real.
