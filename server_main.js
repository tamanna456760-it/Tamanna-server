"use strict";

// Compatibility entry point. The canonical static website server is server.js.
const { createServer } = require("./server");

if (require.main === module) {
  const port = Number.parseInt(process.env.POWERHUB_PORT || "8080", 10);
  const host = process.env.POWERHUB_HOST || "127.0.0.1";
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error("POWERHUB_PORT must be between 1 and 65535");
  }
  createServer().listen(port, host, () => {
    process.stdout.write(`Tamanna compatibility website server listening on http://${host}:${port}\n`);
  });
}

module.exports = { createServer };
