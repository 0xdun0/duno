package com.eversec;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;

/**
 * EverSec Audit Logger v2.0
 *
 * Internal microservice that handles audit logging for the Log Analysis Platform.
 * Listens on localhost:8080 and accepts log entries from the main Flask application.
 *
 * VULNERABILITY: CVE-2021-44228 (Log4Shell)
 * Apache Log4j2 versions 2.0-beta9 through 2.14.1 are affected.
 * User-controlled strings passed to logger.info() trigger JNDI lookups when they
 * contain ${jndi:...} expressions, enabling remote code execution.
 *
 * Affected log calls:
 *   logger.info("Request from: {}", xff)    <- X-Forwarded-For header
 *   logger.info("Client agent: {}", ua)     <- User-Agent header
 *   logger.info("Search query: {}", query)  <- Search input
 */
public class AuditLogger {

    private static final Logger logger = LogManager.getLogger(AuditLogger.class);
    private static final List<String> recentLogs = new CopyOnWriteArrayList<>();
    private static final int MAX_PREVIEW_ENTRIES = 10;

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 8080), 0);
        server.createContext("/log", new LogHandler());
        server.createContext("/log-preview", new PreviewHandler());
        server.setExecutor(Executors.newCachedThreadPool());
        server.start();
        System.out.println("[AuditLogger] Listening on 127.0.0.1:8080");
        System.out.println("[AuditLogger] Apache Log4j 2.14.1 initialized");

        // Keep alive
        Thread.currentThread().join();
    }

    static class LogHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(405, 0);
                exchange.getResponseBody().close();
                return;
            }

            String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            String xff   = extractJsonValue(body, "xff");
            String ua    = extractJsonValue(body, "ua");
            String query = extractJsonValue(body, "query");
            String ts    = new SimpleDateFormat("HH:mm:ss.SSS").format(new Date());

            // VULNERABLE: Log4j 2.14.1 evaluates ${jndi:...} lookups in log messages.
            // Any user-controlled string reaching these calls can trigger CVE-2021-44228.
            if (xff != null && !xff.isEmpty()) {
                logger.info("Request from: {}", xff);
                storePreview(ts + " [INFO] Request from: " + xff);
            }
            if (ua != null && !ua.isEmpty()) {
                logger.info("Client agent: {}", ua);
                storePreview(ts + " [INFO] Client agent: " + ua);
            }
            if (query != null && !query.isEmpty()) {
                logger.info("Search query: {}", query);
                storePreview(ts + " [INFO] Search query: " + query);
            }

            byte[] response = "{\"status\":\"logged\"}".getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, response.length);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.getResponseBody().write(response);
            exchange.getResponseBody().close();
        }
    }

    static class PreviewHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            List<String> entries = new ArrayList<>(recentLogs);
            int from = Math.max(0, entries.size() - MAX_PREVIEW_ENTRIES);
            List<String> last = entries.subList(from, entries.size());

            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < last.size(); i++) {
                if (i > 0) sb.append(",");
                // Escape for JSON
                String escaped = last.get(i)
                    .replace("\\", "\\\\")
                    .replace("\"", "\\\"")
                    .replace("\n", "\\n")
                    .replace("\r", "\\r");
                sb.append("\"").append(escaped).append("\"");
            }
            sb.append("]");

            byte[] response = sb.toString().getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, response.length);
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.getResponseBody().write(response);
            exchange.getResponseBody().close();
        }
    }

    private static void storePreview(String entry) {
        recentLogs.add(entry);
        if (recentLogs.size() > 50) {
            recentLogs.remove(0);
        }
    }

    private static String extractJsonValue(String json, String key) {
        if (json == null || key == null) return null;
        String search = "\"" + key + "\":\"";
        int start = json.indexOf(search);
        if (start < 0) return null;
        start += search.length();
        int end = json.indexOf("\"", start);
        if (end < 0) return null;
        return json.substring(start, end);
    }
}
