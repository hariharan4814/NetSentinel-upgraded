// Build a deliberately narrow public artifact. Never copy the repository root.
import { cp, mkdir, readFile, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const stage = path.join(frontend, ".public-build");
const release = path.resolve(frontend, "..", "public-release");
// Refuse a populated staging tree: it must never accumulate non-allowlisted routes.
if (existsSync(stage)) throw new Error(`Public staging already exists: ${stage}. Review and remove that generated directory before rebuilding.`);
await mkdir(stage, { recursive: true });
const files = ["src/app/page.tsx", "src/app/layout.tsx", "src/app/public.css", "src/components/public/connection-app.tsx", "src/components/public/public-tools.tsx", "src/components/public/icon.tsx", "src/lib/connection-check.ts", "src/lib/troubleshooting.ts", "src/lib/public-measurements.ts", "src/lib/public-report.ts", "public/connection-check.json", "public/companion-release.json", "public/THIRD_PARTY_NOTICES.txt", "tsconfig.json", "package.json", "package-lock.json"];
for (const file of files) {
  await mkdir(path.dirname(path.join(stage, file)), { recursive: true });
  await cp(path.join(frontend, file), path.join(stage, file));
}
await writeFile(path.join(stage, "next.config.ts"), 'import type { NextConfig } from "next";\nconst config: NextConfig = { output: "export", poweredByHeader: false, turbopack: { root: ' + JSON.stringify(frontend) + ' } };\nexport default config;\n');
const result = spawnSync(process.execPath, [path.join(frontend, "node_modules/next/dist/bin/next"), "build", stage], { cwd: frontend, stdio: "inherit" });
if (result.status !== 0) process.exit(result.status ?? 1);
const out = path.join(stage, "out");
for (const forbidden of ["api", "local", "local.html", "lab", "lab.html", "artifacts", "resources", ".env", "backend", "sensor"]) {
  if (existsSync(path.join(out, forbidden))) throw new Error(`Unsafe public output: ${forbidden}`);
}
await mkdir(release, { recursive: true });
const site = path.join(release, "dist");
if (existsSync(site)) throw new Error(`Release output already exists: ${site}. Review and remove only that generated directory before rebuilding.`);
await cp(out, site, { recursive: true });
await writeFile(path.join(site, "_headers"), "/*\n  X-Content-Type-Options: nosniff\n  X-Frame-Options: DENY\n  Referrer-Policy: no-referrer\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n/connection-check.json\n  Cache-Control: no-store\n");
await mkdir(path.join(release, ".openai"), { recursive: true });
const manifestPath = path.join(release, ".openai/hosting.json");
const manifest = existsSync(manifestPath) ? JSON.parse(await readFile(manifestPath, "utf8")) : {};
await writeFile(manifestPath, JSON.stringify({ ...manifest, static: { directory: "dist" } }, null, 2) + "\n");
await writeFile(path.join(release, ".gitignore"), ".sites-runtime/\n*.zip\n");
await writeFile(path.join(release, "README.md"), "# NetSentinel public release\n\nGenerated from an explicit allowlist in frontend/scripts/build-public.mjs. Contains public static assets only. The private local monitor, APIs, sensor, ML, configuration and data are intentionally absent.\n");
console.log(JSON.stringify({ release, site, publicOnly: true }));
