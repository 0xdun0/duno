/*
 * EverSec Backup Tool v1.0
 *
 * VULNERABILITY: Path traversal - no input validation
 * Allows reading arbitrary files as root when SUID bit is set
 *
 * Exploitation: /usr/local/bin/backup_tool /root/flag4.txt
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("EverSec Backup Tool v1.0\n");
        printf("Usage: %s <filepath>\n", argv[0]);
        printf("\nBackup critical system files securely.\n");
        return 1;
    }

    char *filepath = argv[1];

    // VULNERABILITY: No path sanitization or validation!
    // Should check for:
    // - Path traversal sequences (../)
    // - Absolute paths outside allowed directories
    // - Restricted file access

    printf("[ ] Reading file: %s\n", filepath);

    FILE *file = fopen(filepath, "r");
    if (!file) {
        perror("[!] Error opening file");
        return 1;
    }

    printf("[+] File opened successfully:\n\n");
    printf("------- BEGIN FILE CONTENTS -------\n");

    // Read and print file contents
    char buffer[1024];
    while (fgets(buffer, sizeof(buffer), file)) {
        printf("%s", buffer);
    }

    printf("-------- END FILE CONTENTS --------\n");

    fclose(file);
    return 0;
}
