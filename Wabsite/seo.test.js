const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");

const html = readFileSync(path.join(__dirname, "Index.html"), "utf8");
const robots = readFileSync(path.join(__dirname, "robots.txt"), "utf8");
const sitemap = readFileSync(path.join(__dirname, "sitemap.xml"), "utf8");
const canonical = "https://www.bd-king-r7.com/";

test("homepage has a descriptive title, summary, and indexable directives", () => {
  assert.match(html, /<title>Tamanna AI \| Secure AI Assistant &amp; Automation Platform<\/title>/);
  assert.match(html, /<meta name="description" content="[^"]{80,}"\s*\/>/);
  assert.match(html, /<meta name="robots" content="index, follow/);
  assert.doesNotMatch(html, /name="robots" content="[^"]*noindex/i);
});

test("homepage uses one canonical host and social metadata", () => {
  assert.ok(html.includes(`<link rel="canonical" href="${canonical}" />`));
  assert.match(html, /property="og:url" content="https:\/\/www\.bd-king-r7\.com\//);
  assert.match(html, /property="og:title"/);
  assert.match(html, /name="twitter:card"/);
});

test("SoftwareApplication structured data is valid JSON and describes the canonical site", () => {
  const match = html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
  assert.ok(match, "JSON-LD block must exist");
  const data = JSON.parse(match[1]);
  assert.equal(data["@context"], "https://schema.org");
  assert.equal(data["@type"], "SoftwareApplication");
  assert.equal(data.name, "Tamanna AI");
  assert.equal(data.url, canonical);
});

test("robots permits public crawling and advertises the sitemap", () => {
  assert.match(robots, /User-agent: \*/);
  assert.match(robots, /Allow: \/\s/);
  assert.match(robots, /Sitemap: https:\/\/www\.bd-king-r7\.com\/sitemap\.xml/);
});

test("sitemap is validly namespaced and lists only canonical URLs", () => {
  assert.match(sitemap, /^<\?xml version="1\.0" encoding="UTF-8"\?>/);
  assert.match(sitemap, /<urlset xmlns="http:\/\/www\.sitemaps\.org\/schemas\/sitemap\/0\.9">/);
  assert.match(sitemap, /<loc>https:\/\/www\.bd-king-r7\.com\/<\/loc>/);
  assert.doesNotMatch(sitemap, /<loc>https?:\/\/(?!www\.bd-king-r7\.com)/);
  assert.match(sitemap, /<\/urlset>\s*$/);
});
