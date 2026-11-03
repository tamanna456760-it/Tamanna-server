"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { createServer } = require("../server");

async function withServer(run) {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  try {
    await run(`http://127.0.0.1:${address.port}`);
  } finally {
    await new Promise((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()));
    });
  }
}

test("website health endpoint returns minimal status", async () => {
  await withServer(async (base) => {
    const response = await fetch(`${base}/health`);
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
      status: "ok",
      service: "tamanna-static-website",
    });
  });
});

test("root serves the Tamanna website", async () => {
  await withServer(async (base) => {
    const response = await fetch(base);
    assert.equal(response.status, 200);
    assert.match(response.headers.get("content-type"), /text\/html/);
    assert.match(await response.text(), /Tamanna AI/);
  });
});

test("static server sets basic security headers", async () => {
  await withServer(async (base) => {
    const response = await fetch(base);
    assert.equal(response.headers.get("x-content-type-options"), "nosniff");
    assert.equal(response.headers.get("x-frame-options"), "DENY");
  });
});

test("unknown paths return 404", async () => {
  await withServer(async (base) => {
    const response = await fetch(`${base}/missing-file`);
    assert.equal(response.status, 404);
  });
});

test("unsupported methods return 405", async () => {
  await withServer(async (base) => {
    const response = await fetch(base, { method: "POST" });
    assert.equal(response.status, 405);
    assert.equal(response.headers.get("allow"), "GET, HEAD");
  });
});

test("path traversal is rejected", async () => {
  await withServer(async (base) => {
    const response = await fetch(`${base}/%2e%2e%2fREADME.md`);
    assert.ok([403, 404].includes(response.status));
  });
});
