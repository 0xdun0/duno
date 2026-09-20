# Política de Segurança, Sandbox & Uso Responsável — DUNO

O **DUNO** é uma plataforma deliberadamente vulnerável criada para fins de **pesquisa, treinamento técnico e capacitação em cibersegurança**.

---

## 1. Confinamento & Sandbox de Desafios

Todos os laboratórios e máquinas são executados em ambiente estritamente isolado:

1. **Sem Acesso Privilegiado:** Nenhum container de desafio roda com `privileged: true` ou capabilities elevadas (`CAP_SYS_ADMIN`, `CAP_NET_ADMIN`).
2. **Rede Interna sem Egress:** A rede de desafios `duno-challenges-net` não possui rota de saída para a internet pública (`internal: true`), impedindo que máquinas vulneráveis sejam pivotadas para ataques externos.
3. **Limites Rígidos de Hardware:**
   * Memória RAM: Capped em 512MB por container.
   * CPU: Limitado a 0.5 vCPU (`500_000_000 nano_cpus`).
   * Processos máximos: `pids_limit = 100`.
4. **TTL & Autodestruição:** Instâncias de máquinas expiram e são purgadas do Docker daemon após 45 minutos de inatividade.

---

## 2. Blindagem do Pipeline de Submissão de Arquivos (ZIP / TAR)

O mecanismo de ingestão de arquivos compactados aplica as seguintes verificações:

| Vetor de Ataque | Mitigação Implementada |
|---|---|
| **Magic Bytes Spoofing** | Inspeção dos primeiros 512 bytes exigindo cabeçalho real (`PK\x03\x04` ou `\x1f\x8b`), bloqueando executáveis ELF/PE disfarçados. |
| **ZipSlip / Path Traversal** | Rejeição de `\x00`, caminhos com `..`, barras invertidas e contenção estrita via `pathlib.Path.relative_to`. |
| **Dispositivos Reservados** | Bloqueio de nós do Windows/DOS (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`). |
| **Symlinks e Hardlinks** | Rejeição de atributos POSIX de links simbólicos em ZIP e flags `issym() / islnk()` em TAR para evitar leitura de arquivos do host (`/etc/shadow`). |
| **Device Nodes & FIFOs** | Proibição de arquivos de bloco, caractere, pipes e sockets (`isdev`, `ischr`, `isblk`, `isfifo`). |
| **ZipBomb / Decompression Bomb** | Extração em streaming com contagem real de bytes: teto de 500 arquivos, 60MB por arquivo e 100MB no total descompactado. |
| **Teto de Upload HTTP** | Limite rígido de 50MB no recebimento de payloads no Flask. |

---

## 3. Uso Responsável & Ética

O uso da plataforma deve obedecer aos seguintes princípios:
* **Ambiente Local e Isolado:** Nunca exponha a porta 2300 ou as portas dos desafios diretamente na internet pública sem autenticação e firewall perimetral.
* **Consentimento:** Testes e ataques devem ocorrer única e exclusivamente dentro dos containers fornecidos pelo DUNO.
