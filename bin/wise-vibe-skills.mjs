#!/usr/bin/env node
// wise-Vibe-Skills CLI — npx installer (macOS · Linux · Windows, no dependencies).
//   npx wise-vibe-skills@latest install [--client ids|all|detected] [--scope user|project] [--dir path] [--skills list] [--dry-run] [--force] [-y]
//   npx wise-vibe-skills uninstall | list | doctor | zip [dir]
//   npx github:WisemanLim/wise-Vibe-Skills install      (before an npm release)
// Same client registry as install.sh (skill roots follow REA's SupportedClients.ts, github.com/morluto/rea).
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import readline from "node:readline";
import zlib from "node:zlib";

const PKG_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SKILLS_DIR = path.join(PKG_ROOT, "skills");
const MARKER = ".wise-vibe-skills";
const VERSION = JSON.parse(fs.readFileSync(path.join(PKG_ROOT, "package.json"), "utf8")).version;
const HOME = os.homedir();
const ENV = process.env;
const CFG = ENV.XDG_CONFIG_HOME || path.join(HOME, ".config");
const APPDATA = ENV.APPDATA || "";
// v0.1 skill names, superseded by wvs-* — removed on install when they carry our marker
const LEGACY_SKILLS = ["analysis-source", "in-depth-review", "create-guide4junior", "code-review-by-levels", "totally-analysis-based-on-star",
  "convert-to-pdf", "ref-sh", "oss-clone-analysis", "attachment-deep-analysis", "requirement-based-prd", "wise-report-kit"];

const claudeHome = () => ENV.CLAUDE_CONFIG_DIR || path.join(HOME, ".claude");
const shared = () => path.join(HOME, ".agents", "skills");
const CLIENTS = [
  { id: "claude-code", name: "Claude Code", cmds: ["claude"], dirs: () => [claudeHome()], root: () => path.join(claudeHome(), "skills"), proj: ".claude/skills" },
  { id: "claude-desktop", name: "Claude Desktop", cmds: [], dirs: () => ["/Applications/Claude.app", path.join(HOME, "Library/Application Support/Claude"), path.join(CFG, "Claude"), APPDATA && path.join(APPDATA, "Claude")],
    root: () => path.join(claudeHome(), "skills"), proj: null, zip: true },
  { id: "codex", name: "Codex", cmds: ["codex"], dirs: () => [ENV.CODEX_HOME || path.join(HOME, ".codex")], root: shared, proj: ".agents/skills" },
  { id: "cursor", name: "Cursor", cmds: ["cursor", "cursor-agent"], dirs: () => [path.join(HOME, ".cursor")], root: shared, proj: ".agents/skills" },
  { id: "gemini-cli", name: "Gemini CLI", cmds: ["gemini"], dirs: () => [path.join(ENV.GEMINI_CLI_HOME || HOME, ".gemini")],
    root: () => path.join(ENV.GEMINI_CLI_HOME || HOME, ".agents", "skills"), proj: ".agents/skills" },
  { id: "windsurf", name: "Windsurf", cmds: ["windsurf"], dirs: () => [path.join(HOME, ".codeium", "windsurf")], root: shared, proj: ".agents/skills" },
  { id: "devin", name: "Devin", cmds: ["devin"], dirs: () => [path.join(CFG, "devin")], root: shared, proj: ".agents/skills" },
  { id: "opencode", name: "OpenCode", cmds: ["opencode"], dirs: () => [path.join(CFG, "opencode")], root: shared, proj: ".agents/skills" },
  { id: "antigravity", name: "Antigravity", cmds: ["antigravity"], dirs: () => ["/Applications/Antigravity.app", path.join(HOME, ".gemini", "antigravity")],
    root: () => path.join(HOME, ".gemini", "config", "skills"), proj: ".agents/skills" },
  { id: "copilot-cli", name: "GitHub Copilot CLI", cmds: ["copilot"], dirs: () => [path.join(HOME, ".copilot")], root: shared, proj: ".agents/skills" },
  { id: "commandcode", name: "Command Code", cmds: ["commandcode", "command-code"], dirs: () => [path.join(HOME, ".commandcode")], root: shared, proj: ".agents/skills" },
  { id: "grok-build", name: "Grok Build", cmds: ["grok"], dirs: () => [ENV.GROK_HOME || path.join(HOME, ".grok")], root: shared, proj: ".agents/skills" },
  { id: "omp", name: "OMP", cmds: ["omp"], dirs: () => [path.join(HOME, ".omp")], root: shared, proj: ".agents/skills" },
  { id: "vscode", name: "VS Code", cmds: ["code"], dirs: () => [path.join(HOME, ".vscode")], root: shared, proj: ".agents/skills" },
];

// ------------------------------------------------------------------ helpers
const exists = (p) => { try { fs.accessSync(p); return true; } catch { return false; } };
function hasCmd(cmd) {
  const exts = process.platform === "win32" ? (ENV.PATHEXT || ".EXE;.CMD;.BAT").split(";") : [""];
  return (ENV.PATH || "").split(path.delimiter).some((d) => d && exts.some((e) => exists(path.join(d, cmd + e))));
}
const detected = (c) => c.cmds.some(hasCmd) || c.dirs().filter(Boolean).some(exists);
const allSkills = () => fs.readdirSync(SKILLS_DIR).filter((s) => exists(path.join(SKILLS_DIR, s, "SKILL.md"))).sort();

function parseArgs(argv) {
  const o = { cmd: "install", client: "detected", scope: "user", dir: "", skills: "all", dryRun: false, force: false, yes: false, zipDir: "", binDir: "" };
  const a = [...argv];
  if (a[0] && !a[0].startsWith("-")) o.cmd = a.shift();
  while (a.length) {
    let k = a.shift(), v;
    if (k.includes("=")) [k, v] = [k.slice(0, k.indexOf("=")), k.slice(k.indexOf("=") + 1)];
    const need = () => { const x = v ?? a.shift(); if (x === undefined) die(`${k} needs a value`); return x; };
    switch (k) {
      case "--client": o.client = need(); break;
      case "--scope": o.scope = need(); break;
      case "--dir": o.dir = need(); break;
      case "--skills": o.skills = need(); break;
      case "--bin-dir": o.binDir = need(); break;
      case "--desktop-zip": o.zipDir = v ?? (a[0] && !a[0].startsWith("-") ? a.shift() : path.join(HOME, "Downloads", "wise-vibe-skills-desktop")); break;
      case "--dry-run": o.dryRun = true; break;
      case "--force": o.force = true; break;
      case "-y": case "--yes": o.yes = true; break;
      case "-h": case "--help": o.cmd = "help"; break;
      case "-v": case "--version": o.cmd = "version"; break;
      default:
        if (o.cmd === "zip" && !k.startsWith("-")) o.zipDir = k; else die(`unknown option: ${k} (see --help)`);
    }
  }
  if (!["user", "project"].includes(o.scope)) die("--scope must be user or project");
  return o;
}
function die(msg) { console.error(`wise-vibe-skills: ${msg}`); process.exit(1); }

function selectedSkills(o) {
  if (o.skills === "all") return allSkills();
  const out = o.skills.split(",").map((s) => s.trim()).filter(Boolean);
  out.forEach((s) => exists(path.join(SKILLS_DIR, s, "SKILL.md")) || die(`unknown skill: ${s} (try list)`));
  return out;
}
function selectedClients(o) {
  if (o.client === "all") return CLIENTS;
  if (o.client === "detected") {
    const d = CLIENTS.filter(detected);
    return d.length ? d : CLIENTS.filter((c) => ["claude-code", "codex"].includes(c.id));
  }
  return o.client.split(",").map((id) => CLIENTS.find((c) => c.id === id.trim()) || die(`unknown client: ${id} (try list)`));
}
function rootOf(c, o) {
  if (o.scope === "project") return c.proj ? path.resolve(c.proj) : null;
  return c.root();
}
function destinations(o) {
  if (o.dir) return [path.resolve(o.dir)];
  return [...new Set(selectedClients(o).map((c) => rootOf(c, o)).filter(Boolean))];
}
async function confirm(o, q) {
  if (o.yes || !process.stdin.isTTY) return true;
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const a = await new Promise((r) => rl.question(`${q} [Y/n] `, r)); rl.close();
  return !/^n/i.test(a.trim());
}
function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    if ([".DS_Store", "__pycache__", ".venv"].includes(e.name)) continue;
    const s = path.join(src, e.name), d = path.join(dst, e.name);
    if (e.isDirectory()) copyDir(s, d);
    else { fs.copyFileSync(s, d); fs.chmodSync(d, fs.statSync(s).mode); }
  }
}

// ------------------------------------------------------------------ zip (Claude Desktop upload; deflate, no deps)
const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
const crc32 = (b) => { let c = 0xffffffff; for (const x of b) c = CRC[(c ^ x) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
function walk(dir, base = dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    if ([".DS_Store", "__pycache__", ".venv", MARKER].includes(e.name)) return [];
    const p = path.join(dir, e.name);
    return e.isDirectory() ? walk(p, base) : [p];
  });
}
function writeZip(srcDir, prefix, out) {
  const locals = [], centrals = []; let off = 0;
  for (const f of walk(srcDir)) {
    const name = Buffer.from(path.posix.join(prefix, path.relative(srcDir, f).split(path.sep).join("/")));
    const data = fs.readFileSync(f), comp = zlib.deflateRawSync(data), crc = crc32(data);
    const lh = Buffer.alloc(30); lh.writeUInt32LE(0x04034b50, 0); lh.writeUInt16LE(20, 4); lh.writeUInt16LE(0x0800, 6); lh.writeUInt16LE(8, 8);
    lh.writeUInt32LE(0, 10); lh.writeUInt32LE(crc, 14); lh.writeUInt32LE(comp.length, 18); lh.writeUInt32LE(data.length, 22); lh.writeUInt16LE(name.length, 26);
    const ch = Buffer.alloc(46); ch.writeUInt32LE(0x02014b50, 0); ch.writeUInt16LE(20, 4); ch.writeUInt16LE(20, 6); ch.writeUInt16LE(0x0800, 8); ch.writeUInt16LE(8, 10);
    ch.writeUInt32LE(0, 12); ch.writeUInt32LE(crc, 16); ch.writeUInt32LE(comp.length, 20); ch.writeUInt32LE(data.length, 24); ch.writeUInt16LE(name.length, 28); ch.writeUInt32LE(off, 42);
    locals.push(lh, name, comp); centrals.push(ch, name); off += 30 + name.length + comp.length;
  }
  const cd = Buffer.concat(centrals), end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0); end.writeUInt16LE(centrals.length / 2, 8); end.writeUInt16LE(centrals.length / 2, 10); end.writeUInt32LE(cd.length, 12); end.writeUInt32LE(off, 16);
  fs.writeFileSync(out, Buffer.concat([...locals, cd, end]));
}
function buildZips(o, dir) {
  if (o.dryRun) return console.log(`  would write Claude Desktop zips → ${dir}`);
  fs.mkdirSync(dir, { recursive: true });
  for (const s of selectedSkills(o)) writeZip(path.join(SKILLS_DIR, s), s, path.join(dir, `${s}.zip`));
  console.log(`  ✓ Claude Desktop zips → ${dir} (Settings › Capabilities › Skills › Upload; enable Code execution)`);
}

// ------------------------------------------------------------------ commands
function list(o) {
  console.log(`wise-Vibe-Skills ${VERSION} — ${SKILLS_DIR}\n\nSkills:`);
  allSkills().forEach((s) => console.log(`  - ${s}`));
  console.log(`\nClients (scope=${o.scope}):`);
  for (const c of CLIENTS) console.log(`  ${c.id.padEnd(15)} ${c.name.padEnd(20)} ${(detected(c) ? "detected" : "-").padEnd(9)} ${rootOf(c, o) || "(zip upload)"}`);
}
async function install(o) {
  const roots = destinations(o), skills = selectedSkills(o), clients = selectedClients(o);
  console.log(`wise-Vibe-Skills ${VERSION} · install · scope=${o.scope} · clients: ${clients.map((c) => c.id).join(" ")}`);
  console.log(`skills: ${skills.join(" ")}\ndestinations:\n${roots.map((r) => "  " + r).join("\n")}`);
  if (!o.dryRun && !(await confirm(o, "Install now?"))) die("cancelled");
  for (const root of roots) {
    for (const s of skills) {
      const dst = path.join(root, s);
      if (exists(dst) && !exists(path.join(dst, MARKER)) && !o.force) { console.warn(`warn: skip ${dst} (exists, not installed by wise-Vibe-Skills; use --force)`); continue; }
      if (o.dryRun) { console.log(`  would copy ${s} → ${dst}`); continue; }
      fs.rmSync(dst, { recursive: true, force: true });
      copyDir(path.join(SKILLS_DIR, s), dst);
      fs.writeFileSync(path.join(dst, MARKER), `name=${s}\nversion=${VERSION}\nsource=npm:wise-vibe-skills\ninstalled=${new Date().toISOString()}\n`);
      console.log(`  ✓ ${s} → ${dst}`);
    }
    for (const s of LEGACY_SKILLS) {            // remove v0.1 folders we created (marker present); never touch others
      const d = path.join(root, s);
      if (!exists(path.join(d, MARKER))) continue;
      if (o.dryRun) console.log(`  would remove legacy ${d} (superseded by wvs-*)`);
      else { fs.rmSync(d, { recursive: true, force: true }); console.log(`  ✗ legacy ${s} removed (superseded by wvs-*)`); }
    }
    if (root.endsWith(path.join(".claude", "skills"))) {
      const cmdDir = path.join(path.dirname(root), "commands");
      const found = LEGACY_SKILLS.filter((s) => exists(path.join(cmdDir, `${s}.md`)));
      if (found.length) console.warn(`warn: legacy slash commands in ${cmdDir}: ${found.join(" ")} — superseded by /wvs-review · /wvs-report · /wvs-tools (keep or remove them yourself)`);
    }
  }
  if (o.binDir && roots.length) linkBin(o, roots[0]);
  const zipDir = o.zipDir || (clients.some((c) => c.zip) ? path.join(HOME, "Downloads", "wise-vibe-skills-desktop") : "");
  if (zipDir) buildZips(o, zipDir);
  if (!o.dryRun) console.log("\nDone. Restart running agents (new session). wvs-report needs python3 · gh (auth) · LibreOffice; wvs-tools pdf needs pandoc · xelatex · mmdc.");
}
function linkBin(o, root) {
  const src = path.join(root, "wvs-tools", "scripts", "wvs"), dst = path.join(path.resolve(o.binDir), "wvs");
  if (process.platform === "win32") return console.warn(`warn: --bin-dir is for macOS/Linux; on Windows run: bash "${src}"`);
  if (o.dryRun) return console.log(`  would link ${dst} → ${src}`);
  if (!exists(src)) return console.warn(`warn: --bin-dir: wvs-tools not installed in ${root} — skip`);
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  let isLink = false; try { isLink = fs.lstatSync(dst).isSymbolicLink(); } catch { /* absent */ }
  if (exists(dst) && !isLink) return console.warn(`warn: ${dst} exists and is not a symlink — skip`);
  if (isLink) fs.unlinkSync(dst);
  fs.symlinkSync(src, dst); console.log(`  ✓ wvs → ${dst}`);
  if (!(ENV.PATH || "").split(path.delimiter).includes(path.dirname(dst))) console.warn(`warn: ${path.dirname(dst)} is not on PATH — add it to your shell profile`);
}
async function uninstall(o) {
  const roots = destinations(o);
  if (!o.dryRun && !(await confirm(o, `Remove wise-Vibe-Skills from ${roots.join(", ")}?`))) die("cancelled");
  for (const root of roots) {
    if (!exists(root)) continue;
    let n = 0;
    for (const s of fs.readdirSync(root)) {
      const d = path.join(root, s);
      if (!exists(path.join(d, MARKER))) continue;
      if (o.dryRun) console.log(`  would remove ${d}`); else { fs.rmSync(d, { recursive: true, force: true }); console.log(`  ✗ removed ${d}`); }
      n++;
    }
    if (!n) console.log(`  (nothing installed in ${root})`);
  }
  if (o.binDir) {
    const dst = path.join(path.resolve(o.binDir), "wvs");
    try { if (fs.lstatSync(dst).isSymbolicLink() && fs.readlinkSync(dst).endsWith(path.join("wvs-tools", "scripts", "wvs"))) {
      if (o.dryRun) console.log(`  would remove ${dst}`); else { fs.unlinkSync(dst); console.log(`  ✗ removed ${dst}`); } } } catch { /* absent */ }
  }
}
function doctor() {
  const probe = (cmd, args) => { try { return execFileSync(cmd, args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).split("\n")[0].trim(); } catch { return null; } };
  const soffice = hasCmd("soffice") || exists("/Applications/LibreOffice.app/Contents/MacOS/soffice");
  const rows = [
    ["python3", probe(process.platform === "win32" ? "python" : "python3", ["--version"]), "보고서 빌드(docx·그림)"],
    ["uv", probe("uv", ["--version"]), "선택 — venv 가속"],
    ["git", probe("git", ["--version"]), "저장소 클론"],
    ["gh", probe("gh", ["--version"]), "GitHub 실측 — `gh auth login` 권장"],
    ["gh auth", probe("gh", ["auth", "status"]) !== null ? "ok" : null, "미인증이면 익명 API(시간당 60회)"],
    ["soffice", soffice ? "ok" : null, "docx/pptx → PDF (LibreOffice)"],
    ["pandoc", probe("pandoc", ["--version"]), "convert-to-pdf · 기존 docx 읽기"],
  ];
  console.log(`wise-Vibe-Skills ${VERSION} doctor (${process.platform}/${process.arch})`);
  for (const [k, v, why] of rows) console.log(`  ${(v ? "ok " : "-- ").padEnd(4)}${k.padEnd(9)} ${(v || "missing").slice(0, 40).padEnd(42)} ${why}`);
  console.log("\nInstalled:");
  for (const c of CLIENTS) {
    const r = c.root(); const n = exists(r) ? fs.readdirSync(r).filter((s) => exists(path.join(r, s, MARKER))).length : 0;
    console.log(`  ${c.id.padEnd(15)} ${detected(c) ? "detected" : "-       "} ${String(n).padStart(2)} skills  ${r}`);
  }
}
const HELP = `wise-vibe-skills ${VERSION}
Usage: npx wise-vibe-skills [install|uninstall|list|doctor|zip] [options]
  --client <ids|all|detected>  claude-code claude-desktop codex cursor gemini-cli windsurf devin opencode antigravity copilot-cli commandcode grok-build omp vscode
  --scope user|project  --dir <path>  --skills wvs-review,wvs-report,wvs-tools  --desktop-zip [dir]  --bin-dir <dir>  --dry-run  --force  -y
  zip [dir]   build per-skill zips for Claude Desktop (Settings › Capabilities › Skills)`;

const o = parseArgs(process.argv.slice(2));
switch (o.cmd) {
  case "install": await install(o); break;
  case "uninstall": await uninstall(o); break;
  case "list": list(o); break;
  case "doctor": doctor(); break;
  case "zip": buildZips(o, o.zipDir || path.join(HOME, "Downloads", "wise-vibe-skills-desktop")); break;
  case "version": console.log(VERSION); break;
  case "help": console.log(HELP); break;
  default: die(`unknown command: ${o.cmd}\n${HELP}`);
}
