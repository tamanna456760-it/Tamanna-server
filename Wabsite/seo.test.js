const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const html = readFileSync(path.join(__dirname, "Index.html"), "utf8");
const robots = readFileSync(path.join(__dirname, "robots.txt"), "utf8");
const sitemap = readFileSync(path.join(__dirname, "sitemap.xml"), "utf8");

test("homepage has a descriptive title and meta description", () => {
  assert.match(html, /<title>Tamanna AI \| Secure AI Assistant &amp; Automation Platform<\/title>/);
  assert.match(html, /<meta name="description" content="[^"]{80,}"\s*\/>/);
});

test("homepage declares canonical, social metadata, and structured data", () => {
  assert.match(html, /<link rel="canonical" href="https:\/\/www\.bd-king-r7\.com\/"\s*\/>/);
  assert.match(html, /property="og:title"/);
  assert.match(html, /name="twitter:card"/);
  assert.match(html, /type="application\/ld\+json"/);
});

test("robots permits crawling and advertises the sitemap", () => {
  assert.match(robots, /User-agent: \*/);
  assert.match(robots, /Allow: \/\s/);
  assert.match(robots, /Sitemap: https:\/\/www\.bd-king-r7\.com\/sitemap\.xml/);
});

test("sitemap includes the canonical homepage", () => {
  assert.match(sitemap, /^<\?xml version="1\.0" encoding="UTF-8"\?>/);
  assert.match(sitemap, /<urlset xmlns="https:\/\/www\.sitemaps\.org\/schemas\/sitemap\/0\.9">/);
  assert.match(sitemap, /<loc>https:\/\/www\.bd-king-r7\.com\/<\/loc>/);
  assert.match(sitemap, /<\/urlset>\s*$/);
});
