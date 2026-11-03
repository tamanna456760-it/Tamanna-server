import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const html = await readFile(resolve(here, "Index.html"), "utf8");
const robots = await readFile(resolve(here, "robots.txt"), "utf8");
const sitemap = await readFile(resolve(here, "sitemap.xml"), "utf8");

test("homepage has a unique SEO title and description", () => {
  assert.match(html, /<title>Tamanna AI \| Secure AI Assistant &amp; Automation Platform<\/title>/);
  assert.match(html, /<meta name="description" content="[^"]{80,}"\s*\/>/);
});

test("homepage declares canonical and social metadata", () => {
  assert.match(html, /<link rel="canonical" href="https:\/\/www\.bd-king-r7\.com\/"\s*\/>/);
  assert.match(html, /property="og:title"/);
  assert.match(html, /name="twitter:card"/);
  assert.match(html, /type="application\/ld\+json"/);
});

test("robots allows public crawling and points to sitemap", () => {
  assert.match(robots, /User-agent: \*/);
  assert.match(robots, /Allow: \/\s/);
  assert.match(robots, /Sitemap: https:\/\/www\.bd-king-r7\.com\/sitemap\.xml/);
});

test("sitemap is valid XML-shaped and includes canonical homepage", () => {
  assert.match(sitemap, /^<\?xml version="1\.0" encoding="UTF-8"\?>/);
  assert.match(sitemap, /<urlset xmlns="https:\/\/www\.sitemaps\.org\/schemas\/sitemap\/0\.9">/);
  assert.match(sitemap, /<loc>https:\/\/www\.bd-king-r7\.com\/<\/loc>/);
  assert.match(sitemap, /<\/urlset>\s*$/);
});
