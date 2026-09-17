import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const root = resolve(__dirname, "..");
const html = readFileSync(resolve(root, "index.html"), "utf8");
const css = readFileSync(resolve(root, "src/styles.css"), "utf8");
const js = readFileSync(resolve(root, "src/app.js"), "utf8");
const blob = html + css + js;

describe("Validation Center automated a11y qualification", () => {
  it("has lang, landmarks, h1, labels, focus, reduced motion, a11y options", () => {
    expect(html).toMatch(/<html[^>]+lang=/);
    expect(html).toContain("<main");
    expect(html).toMatch(/<h1[\s>]/);
    expect(html).toContain("<label");
    expect(blob).toMatch(/:focus/);
    expect(blob).toContain("prefers-reduced-motion");
    expect(html).toContain("Accessibility Options");
    expect(blob.includes("min-height: 44px") || blob.includes("--target-min")).toBe(true);
    expect(html).toContain("status-text");
    expect(html).toContain("skip-link");
  });

  it("does not claim WCAG from automation alone", () => {
    expect(html.toLowerCase()).not.toContain("wcag 2.2 aa conformant");
  });
});
