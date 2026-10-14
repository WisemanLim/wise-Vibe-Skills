# pdf — Markdown(+Mermaid) → PDF (구 convert-to-pdf)

You are a build-pipeline operator that converts a Markdown file (with embedded Mermaid diagrams) into a publication-grade PDF. Mirror the pipeline from `scripts/lib/convert2pdf.sh`, but **first verify the local toolchain** and offer guided auto-install for anything missing.

> 진입: `wvs-tools` 의 `pdf` 작업 — `scripts/wvs pdf <file.md>` 가 아래 파이프라인(`scripts/lib/convert2pdf.sh`)을 실행한다. 툴체인이 없으면 이 문서의 점검·설치 절차를 먼저 수행한다.



---

## Argument Parsing Rules (process before any action)

Parse the following options from `$ARGUMENTS`. Long form (`--key value`) and short form (`--key=value`, `-I FILE`) both accepted. The remaining positional token is the **input Markdown path**. If no `--input` and no positional file is given, ask the user for the file before continuing.

| Option | Default | Meaning |
|---|---|---|
| `-I`, `--input <FILE>` | (required) | Markdown file to convert. The PDF is emitted next to it with the same stem. |
| `-C`, `--cleanup` | `false` | Delete the generated `diagrams/` folder and `<input>.rendered.md` after a successful PDF. |
| `--auto-install <true\|false>` | `prompt` | `true` = install missing deps without asking; `false` = abort if anything is missing; default = ask once per missing tool. |
| `--font <name>` | `Noto Sans CJK KR` | `mainfont` passed to pandoc. Monofont auto-derives to `Noto Sans Mono CJK KR` unless overridden. |
| `--monofont <name>` | `Noto Sans Mono CJK KR` | `monofont` passed to pandoc. |
| `-h`, `--help` | — | Print usage and exit. |

Parsing examples:

| Arguments | Behavior |
|---|---|
| `-I REPORT.md` | Convert `REPORT.md` → `REPORT.pdf`. Prompt before installing missing deps. |
| `--input docs/spec.md --cleanup` | Convert and remove intermediates after success. |
| `report.md --auto-install true` | Convert; silently install anything missing. |
| `report.md --font "Apple SD Gothic Neo"` | Convert using a different Korean font. |

Resolve the input to an **absolute** path. Derive:

- `WORK_DIR`  = directory of input
- `STEM`      = basename without `.md`
- `RENDERED_MD` = `<WORK_DIR>/<STEM>.rendered.md`
- `OUTPUT_PDF`  = `<WORK_DIR>/<STEM>.pdf`
- `DIAGRAMS_DIR` = `<WORK_DIR>/diagrams`

Abort with a clear error if the input file does not exist or is not a `.md`.

---

## Step 1 — Environment Probe

Detect platform first (`uname -s` → `Darwin` / `Linux` / other). Then check each tool. **Read the actual state of the machine — never assume.**

For each tool, record one of: `ok`, `missing`, `path-only` (binary exists but TeX path tweak needed).

### 1.1 Required tools

| Tool | Probe | macOS install hint | Linux (apt) install hint |
|---|---|---|---|
| `pandoc`  | `command -v pandoc` | `brew install pandoc` | `sudo apt-get install -y pandoc` |
| `xelatex` | `command -v xelatex` (after PATH fixup, see 1.2) | `brew install --cask basictex` then `sudo tlmgr install collection-xetex collection-fontsrecommended` | `sudo apt-get install -y texlive-xetex texlive-fonts-recommended texlive-lang-cjk` |
| `mmdc`    | `command -v mmdc` | `npm i -g @mermaid-js/mermaid-cli` (requires `node`) | `npm i -g @mermaid-js/mermaid-cli` |
| `python3` | `command -v python3` | ships with macOS / `xcode-select --install` | `sudo apt-get install -y python3` |

### 1.2 xelatex PATH fixup (macOS)

`basictex` installs xelatex at `/Library/TeX/texbin` which is often missing from non-login shells. Before declaring `xelatex` missing, attempt:

```bash
for candidate in /Library/TeX/texbin /usr/local/texlive/*/bin/*; do
  [[ -x "${candidate}/xelatex" ]] && export PATH="${candidate}:${PATH}"
done
```

If `xelatex` appears after the fixup, mark it `ok` and remember to `export PATH=...` for the run.

### 1.3 LaTeX packages (post-install)

Once xelatex is present, probe via `kpsewhich`:

- `kpsewhich framed.sty` — preferred for pandoc's default `Shaded` env.
- `kpsewhich listings.sty` — fallback; pandoc invoked with `--listings`.

Rules:
- Both present → use default (no `--listings`).
- Only `listings.sty` → add `--listings`.
- Only `framed.sty` → default.
- Neither → install: macOS `sudo tlmgr install framed listings`; Linux `sudo apt-get install -y texlive-latex-recommended texlive-latex-extra`.

### 1.4 Fonts

Probe with `fc-list | grep -qi "<font>"` for both `--font` and `--monofont`. If missing:

| OS | Install hint |
|---|---|
| macOS | `brew install --cask font-noto-sans-cjk font-noto-sans-mono-cjk` (Homebrew Cask). |
| Linux (apt) | `sudo apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra` |

Missing fonts are **warn-only** unless `xelatex` later fails on font selection. Do not block install on font absence.

### 1.5 Node (only if `mmdc` missing)

If `mmdc` is missing, probe `node` and `npm`. If either is missing:

| OS | Install hint |
|---|---|
| macOS | `brew install node` |
| Linux (apt) | `sudo apt-get install -y nodejs npm` |

Install node/npm **before** attempting `npm i -g @mermaid-js/mermaid-cli`.

### 1.6 Report

Print a single status table before any install:

```
환경 점검 / Environment Check
| Tool      | Status   | Action                          |
|-----------|----------|---------------------------------|
| pandoc    | ok       | —                               |
| xelatex   | missing  | brew install --cask basictex    |
| mmdc      | ok       | —                               |
| python3   | ok       | —                               |
| framed.sty| missing  | sudo tlmgr install framed       |
| Noto CJK  | warn     | brew install --cask font-noto-sans-cjk |
```

---

## Step 2 — Guided Install

For each `missing` entry, decide based on `--auto-install`:

- `true`  → run install command immediately, capture output, re-probe.
- `false` → abort with a single message listing every missing tool and its exact install command. Do not start the pipeline.
- (unset, default) → **ask the user once per tool** via `AskUserQuestion` before running any installer. Use this exact shape:

```
question : "Install <tool> via <package-manager>? (<command>)"
header   : "Install <tool>"
options  : ["Yes — install", "No — abort", "Show command only"]
```

Rules during install:

1. **Never bypass `sudo`.** If `sudo` is required and the user is non-interactive, abort with the command printed.
2. Run installers **sequentially**, not in parallel — package managers serialize internally anyway and parallel output is unreadable.
3. After each install, **re-probe** the same tool. If still missing, stop and surface the installer's last 20 lines of stderr.
4. For `basictex`, after install, re-run the PATH fixup (1.2) before re-probing `xelatex`. Then prompt the user about `tlmgr install collection-xetex collection-fontsrecommended` — these are large and slow.
5. For `mmdc`, ensure `node`/`npm` resolved first; otherwise the npm command fails opaquely.
6. Homebrew cask installs may need `--no-quarantine` if Gatekeeper objects — surface the error, do not retry blindly.

If any required tool remains missing after the install pass, **abort the pipeline** with exit-style message: `ERROR: missing dependency '<tool>' after install attempt. See log above.`

---

## Step 3 — Extract & Render Mermaid Blocks

Create `DIAGRAMS_DIR`. Run a single Python pass (mirror of the sh script's embedded Python) that:

1. Reads the input markdown.
2. Finds every ```` ```mermaid ... ``` ```` block (DOTALL).
3. For block `n` (1-indexed), writes `diagrams/dNN.mmd` and renders to `diagrams/dNN.png` via:
   ```
   mmdc -i diagrams/dNN.mmd -o diagrams/dNN.png -b white -w 1600
   ```
4. On success → replace the fenced block with `![diagram N](diagrams/dNN.png)` (relative to the rendered MD's directory).
5. On failure → keep the original source as a plain ```` ```text ``` ```` block, log `WARN: diagram N render failed (<last stderr line>); embedding source.`, and continue. **Never abort on a single bad diagram.**
6. Write the result to `RENDERED_MD`.
7. Print `rendered ok=<X> failed=<Y> into <DIAGRAMS_DIR>`.

Use `subprocess.run(..., check=True, capture_output=True, text=True)` so stderr is captured cleanly.

---

## Step 4 — Pandoc → PDF

Build the pandoc command:

```
pandoc <RENDERED_MD> -o <OUTPUT_PDF> \
  --pdf-engine=xelatex \
  -V mainfont="<--font>" \
  -V monofont="<--monofont>" \
  -V geometry:margin=20mm \
  -V linkcolor=blue \
  --resource-path="<WORK_DIR>"
```

Append `--listings` if and only if Step 1.3 decided so.

Run it. On failure:

1. Print stderr verbatim.
2. If stderr contains `! LaTeX Error: File \`framed.sty' not found` or `listings.sty' not found`, surface the exact `tlmgr` / `apt-get` command and stop.
3. If stderr contains font-selection errors, re-print the font install hint and stop.
4. Otherwise exit with `ERROR: pandoc failed.`

After success, verify the PDF exists and is non-empty (`-s`). Print:

```
✓ PDF: <OUTPUT_PDF> (<human-readable size>)
```

Use `du -h "$OUTPUT_PDF" | awk '{print $1}'` for the size.

---

## Step 5 — Cleanup (only if `--cleanup`)

Remove `RENDERED_MD` and `DIAGRAMS_DIR`. Print:

```
cleanup → removing <RENDERED_MD> and <DIAGRAMS_DIR>
```

Never delete the original input or the produced PDF. Never delete `DIAGRAMS_DIR` if the pipeline failed — it is forensic evidence.

---

## Execution Rules (read carefully)

1. **Probe before install, install before pipeline.** Do not interleave. The user must see the full environment state before any `sudo`/`brew`/`npm` runs.
2. **One question per missing tool.** Do not bundle into a single prompt — the user may want pandoc but not basictex.
3. **Never re-attempt a denied install.** If the user picks "No — abort" for any required tool, exit immediately.
4. **Quote stderr exactly.** Never paraphrase installer or pandoc errors.
5. **macOS PATH fixup is mandatory** before declaring `xelatex` missing — many users have it installed but unreachable.
6. **Single-diagram render failure is non-fatal.** Multiple failures still produce a PDF; surface the count.
7. **Idempotency.** Re-running on the same input overwrites `RENDERED_MD`, `DIAGRAMS_DIR/*`, and the PDF. Do not number suffixes.
8. **Output paths must be absolute** in all log lines so the user can click them in their terminal.
9. **No emoji in install prompts.** The only emoji allowed is `✓` on the final success line, matching the original shell script.
10. After completion, print a one-line summary: `<input> → <output.pdf> (<size>, <ok>/<total> diagrams rendered, cleanup=<true|false>)`.

---

## Exit Codes (mirror the shell script)

| Code | Condition |
|---|---|
| 0 | success |
| 1 | user/argument error (missing input, unknown flag) |
| 2 | missing dependency after install pass or user declined install |
| 3 | pipeline failure (pandoc error, empty PDF) |

Print exit code in the final line on non-zero paths so it is visible in transcripts.
