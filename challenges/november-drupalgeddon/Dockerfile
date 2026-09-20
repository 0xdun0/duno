# Use official Drupal 7.57 (vulnerable to CVE-2018-7600 Drupalgeddon2)
FROM drupal:7.57-apache

# ── Flags ──────────────────────────────────────────────────────────────────
# FLAG1: RCE proof — www-data can cat /flag1.txt
# FLAG2: Deeper command execution — /flag2.txt
# FLAG3: Hidden file discovery — /root/secret/admin_notes.txt
#         /root is chmod 711: others can traverse to known paths but cannot ls
ARG FLAG1=dr7_rce_unauth
ARG FLAG2=full_c0mp_4ch13v3d
ARG FLAG3=r00t_4dm1n_n0t3s

RUN echo "${FLAG1}" > /flag1.txt && chmod 644 /flag1.txt && \
    echo "${FLAG2}" > /flag2.txt && chmod 644 /flag2.txt && \
    printf 'cat /flag1.txt\ncat /flag2.txt\ncat /root/secret/admin_notes.txt\n' > /var/www/.bash_history && \
    chown www-data:www-data /var/www/.bash_history && \
    mkdir -p /root/secret && \
    echo "${FLAG3}" > /root/secret/admin_notes.txt && \
    chmod 644 /root/secret/admin_notes.txt && \
    # 711: root can rwx, others can only traverse (x) — ls fails, cat to known path works
    chmod 711 /root && \
    chmod 711 /root/secret

# ── Drupal filesystem prep ─────────────────────────────────────────────────
RUN mkdir -p /var/www/html/sites/default/files && \
    chmod 777 /var/www/html/sites/default/files && \
    chmod 777 /var/www/html/sites/default

# ── Auto-install entrypoint ────────────────────────────────────────────────
COPY install_via_http.sh /install_via_http.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80

# Health check: wait up to 120 s for Drupal to finish installing
HEALTHCHECK --interval=15s --timeout=10s --start-period=120s --retries=5 \
  CMD curl -sf http://localhost/ | grep -q "EverSec\|user\|log in\|Log in" || exit 1

CMD ["/entrypoint.sh"]
