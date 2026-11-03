"use strict";

const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const WEB_ROOT = path.resolve(__dirname, "Wabsite");
const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
  ".webp": "image/webp",
};

function sendJson(res, status, payload) {
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(payload));
}

function createServer() {
  return http.createServer((req, res) => {
    res.setHeader("X-Content-Type-Options", "nosniff");
    res.setHeader("X-Frame-Options", "DENY");
    res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
    res.setHeader("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
    res.setHeader("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'");

    if (req.method !== "GET" && req.method !== "HEAD") {
      res.setHeader("Allow", "GET, HEAD");
      return sendJson(res, 405, { error: "method not allowed" });
    }

    let pathname;
    try {
      pathname = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
    } catch {
      return sendJson(res, 400, { error: "invalid URL path" });
    }

    if (pathname === "/health") {
      return sendJson(res, 200, { status: "ok", service: "tamanna-static-website" });
    }

    const requested = pathname === "/" ? "Index.html" : pathname.replace(/^\/+/, "");
    const filePath = path.resolve(WEB_ROOT, requested);
    if (!filePath.startsWith(WEB_ROOT + path.sep) && filePath !== path.join(WEB_ROOT, "Index.html")) {
      return sendJson(res, 403, { error: "forbidden path" });
    }

    fs.stat(filePath, (error, stat) => {
      if (error || !stat.isFile()) {
        return sendJson(res, 404, { error: "not found" });
      }
      const contentType = MIME_TYPES[path.extname(filePath).toLowerCase()] || "application/octet-stream";
      res.writeHead(200, {
        "Content-Type": contentType,
        "Content-Length": stat.size,
        "Cache-Control": "no-cache",
      });
      if (req.method === "HEAD") return res.end();
      const stream = fs.createReadStream(filePath);
      stream.on("error", () => {
        if (!res.headersSent) sendJson(res, 500, { error: "file read failed" });
        else res.destroy();
      });
      stream.pipe(res);
    });
  });
}

if (require.main === module) {
  const port = Number.parseInt(process.env.WEB_PORT || "3000", 10);
  const host = process.env.WEB_HOST || "127.0.0.1";
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error("WEB_PORT must be between 1 and 65535");
  }
  createServer().listen(port, host, () => {
    process.stdout.write(`Tamanna website listening on http://${host}:${port}\n`);
  });
}

module.exports = { createServer };
