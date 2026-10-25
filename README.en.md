# wise-Vibe-Skills

**A skill set for coding agents — 3 skills, 1 CLI.**
Repository review (run by level) · report/PRD generation (run by mode) · developer utilities (`wvs` CLI), shipped as standard `SKILL.md` folders.
Installs into Claude Code, Claude Desktop, Codex, Cursor, Gemini CLI, Windsurf, Devin, OpenCode, Antigravity, GitHub Copilot CLI, Command Code, Grok Build, OMP and VS Code.

[한국어 README](README.md)

| Skill | What it does | Example (Claude Code) |
|---|---|---|
| **`wvs-review`** | Repository review by **level** — L1 structure · L2 +commercial (licenses, security, ISO 5230) · L3 +junior/implementation guides · L4 +line-by-line code review; bulk analysis of a GitHub star list | `/wvs-review ./proj --level 2` |
| **`wvs-report`** | Reports and PRDs by **mode** — `repos` (clone + Summary-Repos) · `deep` (in-depth analysis of attached images, files (md) and sites) · `prd` (PRD + UI design deck from reports, requirement docs, images and links) → docx/pdf · `sess-bak` (incremental per-project md backup of session history) | `/wvs-report deep` (attach an image) |
| **`wvs-tools`** | A **single CLI** `wvs` — pdf · archive · clean · bookmarks · deploy ios/android · dist · doctor | `wvs pdf REPORT.md` |

Generated documents are written in Korean by default (with English where useful), matching the house report templates; prompts can be given in any language.

---

## Contents
1. [Quick start](#1-quick-start)
2. [Installation](#2-installation)
3. [Usage — wvs-review](#3-usage--wvs-review)
4. [Usage — wvs-report](#4-usage--wvs-report)
5. [Usage — wvs-tools (`wvs` CLI)](#5-usage--wvs-tools-wvs-cli)
6. [Built-in alternatives and when they replace these skills](#6-built-in-alternatives-and-when-they-replace-these-skills)
7. [Migrating from v0.1 commands](#7-migrating-from-v01-commands)
8. [Troubleshooting / FAQ](#8-troubleshooting--faq)
9. [Repository layout, development, release](#9-repository-layout-development-release)
10. [References, sources, license](#10-references-sources-license)

---

## 1. Quick start

```bash
# 1) Install for every detected agent and link the wvs CLI for your terminal  (private repo: use the gh api command in 2.1)
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --bin-dir ~/.local/bin

# 2) Restart running agents (start a new session)

# 3) Use (Claude Code)
/wvs-review ./my-repo                     # structure + commercial review (default L2)
/wvs-report deep                          # attached images / files (md) / sites → in-depth report docx/pdf
wvs pdf docs/REPORT.md                    # terminal: Markdown with Mermaid → PDF
```

In other agents (Codex, Cursor, Gemini CLI, …) name the skill in your request, e.g. "**use the wvs-review skill to review ./my-repo at level 2**".
Agents pick skills from their `description`; every skill also reads its arguments from the request text when the host does not substitute `$ARGUMENTS`.

---

## 2. Installation

### 2.1 Methods
| Method | Command | When |
|---|---|---|
| **Install script** (recommended) | `curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh \| bash` | macOS · Linux · Windows (Git Bash/WSL). No Node needed |
| **npx** | `npx github:WisemanLim/wise-Vibe-Skills install` (after an npm release: `npx wise-vibe-skills@latest install`) | Node 18+, including native Windows shells |
| **Claude Code plugin** | `/plugin marketplace add WisemanLim/wise-Vibe-Skills` → `/plugin install wise-vibe-skills@wise-vibe-skills` | Claude Code only; skills are namespaced as `/wise-vibe-skills:wvs-review` |
| **skills.sh** | `npx skills add WisemanLim/wise-Vibe-Skills` | skills CLI users |
| **Claude Desktop (chat)** | `npx wise-vibe-skills zip` or `install.sh --desktop-zip`, then upload `<skill>.zip` in Settings › Capabilities › Skills | Desktop chat; code execution must be enabled |
| **Manual** | `git clone`, then copy `skills/<name>/` into the agent's skills folder | Offline / restricted networks |

**If the repository is private**, `raw.githubusercontent.com` answers an unauthenticated `curl` with 404 (`gh auth login` does not apply to curl). Fetch the installer through the GitHub CLI instead — it then downloads the skills through `gh api` as well:

```bash
gh auth login        # an account with access to the repository
gh api -H "Accept: application/vnd.github.raw" repos/WisemanLim/wise-Vibe-Skills/contents/install.sh | bash -s -- --bin-dir ~/.local/bin
# or
gh repo clone WisemanLim/wise-Vibe-Skills && cd wise-Vibe-Skills && ./install.sh --bin-dir ~/.local/bin
```

npx works for a private repository only when git can authenticate (`gh auth setup-git`, then `npx github:WisemanLim/wise-Vibe-Skills install`). To let everyone install with the one-line `curl … | bash`, make the repository public.

### 2.2 Installer options (same for npx)
| Option | Default | Description |
|---|---|---|
| `--client <ids>` | `detected` | Comma list, `all`, or `detected` (detected agents; falls back to Claude Code + the shared folder) |
| `--scope user\|project` | `user` | `project` installs into `./.claude/skills` and `./.agents/skills` of the current folder (share with a team repo) |
| `--dir <path>` | — | Install into any skills folder |
| `--skills <list>` | all | Subset of `wvs-review,wvs-report,wvs-tools` |
| `--bin-dir <dir>` | — | Symlink the `wvs` CLI (e.g. `~/.local/bin`) |
| `--desktop-zip [dir]` | `~/Downloads/wise-vibe-skills-desktop` | Build Claude Desktop upload zips (automatic when Claude Desktop is selected) |
| `--ref <tag>` | `main` | Branch or tag to install (e.g. `v0.3.1`) |
| `--link` · `--source <path>` | — | Symlink/copy from a local checkout (development) |
| `--force` | — | Also overwrite same-named folders this installer did not create |
| `--dry-run` · `--list` · `--uninstall` · `-y` | — | Plan only · list/detection · remove · no prompts |

```bash
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --list
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --client claude-code,codex,cursor -y
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --scope project --skills wvs-review
npx wise-vibe-skills doctor          # detected agents, installed skills, required tools
```

### 2.3 Install locations per agent
Personal skill roots follow the client registry of the REA installer (`morluto/rea`, `SupportedClients.ts`). Shared roots are installed once.

| `--client` | Agent | user scope | project scope |
|---|---|---|---|
| `claude-code` | Claude Code | `${CLAUDE_CONFIG_DIR:-~/.claude}/skills` | `./.claude/skills` |
| `claude-desktop` | Claude Desktop | zip upload + `~/.claude/skills` (Code tab) | — |
| `antigravity` | Antigravity | `~/.gemini/config/skills` | `./.agents/skills` |
| `gemini-cli` | Gemini CLI | `${GEMINI_CLI_HOME:-~}/.agents/skills` | `./.agents/skills` |
| `codex` `cursor` `windsurf` `devin` `opencode` `copilot-cli` `commandcode` `grok-build` `omp` `vscode` | Codex · Cursor · Windsurf · Devin · OpenCode · GitHub Copilot CLI · Command Code · Grok Build · OMP · VS Code | `~/.agents/skills` (shared) | `./.agents/skills` |

For an agent that is not listed, use `--dir <that agent's skills folder>`.

### 2.4 Update / uninstall
```bash
# Update = run the installer again (replaces the previous install). Pin a version with --ref v0.3.1
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- -y
# Uninstall (including the wvs link)
curl -fsSL https://raw.githubusercontent.com/WisemanLim/wise-Vibe-Skills/main/install.sh | bash -s -- --uninstall --bin-dir ~/.local/bin -y
```
- The installer writes a `.wise-vibe-skills` marker into every skill folder it creates and **only replaces or removes folders with that marker**; your own same-named folders are left alone (override with `--force`).
- v0.1 skills (the previous 11) are cleaned up automatically when they carry the marker. Old slash-command files in `~/.claude/commands/` only trigger a warning; they are never deleted.

### 2.5 Requirements
| Feature | Tools | Check |
|---|---|---|
| wvs-review | none besides the agent; `--pdf` uses the wvs-tools pdf toolchain | — |
| wvs-report | `python3` (builds create `<assets>/.venv` with python-docx · python-pptx · matplotlib · pymupdf), `git`, `gh` (`gh auth login` recommended — anonymous API is limited to 60 requests/hour), LibreOffice (`soffice`) | `npx wise-vibe-skills doctor` |
| wvs-tools pdf | md: `pandoc` · `xelatex` (BasicTeX/TeX Live) · `mmdc` (`npm i -g @mermaid-js/mermaid-cli`) · Noto Sans CJK KR / docx·pptx: LibreOffice | `wvs doctor` |
| wvs-tools others | archive: GNU tar (`gtar`) · bookmarks: python3 · deploy ios: Xcode · deploy android: JDK + fastlane · dist: git · gh · Docker | `wvs doctor` |

---

## 3. Usage — wvs-review

One skill for repository and source review; choose **depth by level**. Levels are cumulative and results go to the target's `.review/`.

| Level | Parts | Output (`<target>/.review/`) |
|---|---|---|
| `--level 1` | structure — purpose, layout, stack, architecture, tests, security, docs, maturity (8 steps) | `REVIEW.md` |
| `--level 2` **(default)** | + commercial — license audit (AGPL, BUSL, GPL propagation), security, community, commercial architecture, legal / ISO 5230 (OpenChain), 5-tier risk rating | + `REVIEW-InDepth.md` |
| `--level 3` | + guide — bilingual (Korean/English) junior and implementation guides | + `GUIDE4Junior.md` · `GUIDE4ImpMethod.md` |
| `--level 4` | + code — line/block review tuned to reader level R0 (non-programmer) … R4 (architect) | + `CODE-REVIEW-Lv<n>/` (INDEX · directory abstracts · per-file reviews) |

| Option | Description |
|---|---|
| `--only structure,commercial,guide,code` | Run only these parts (not cumulative) |
| `--reader 0-4` | Reader level for the code part (default 2 = handover quality for a ~3-year developer) |
| `-O` / `--overall` | Multi-target aggregate under the first target's `.review/<name>/` with a cross-project comparison |
| `--pdf` | Convert produced Markdown to PDF |
| `--name` · `--out-dir` | Output name · folder |
| `--include` · `--exclude` · `--max-files` · `--max-lines-per-file` · `--entry-only` | Scope of the code part |
| `--stars <md> [--previous <md>] [--depth mass\|deep\|hybrid]` | Bulk analysis of a star list — category/rank buckets, incremental runs |

```text
/wvs-review                                   current folder, L2
/wvs-review ./proj --level 1 --pdf            structure report + PDF
/wvs-review ./proj --only commercial          license/commercial review only
/wvs-review ./proj --level 3                  + junior and implementation guides
/wvs-review ./src --only code --reader 0      line-by-line walkthrough for non-programmers
/wvs-review ./a ./b -O                        compare two projects
/wvs-review --stars stars.md --previous stars-old.md --depth hybrid
```

---

## 4. Usage — wvs-report

Builds docx (house template: US Letter, Apple SD Gothic Neo / Noto CJK, cover, automatic table of contents, table/figure styles) and PDF from attached images, links or reports.

### 4.1 Modes
| Mode | Input | Output | Main steps |
|---|---|---|---|
| `repos` | Infographic listing tools (image/link) | `<root>/<Project>/NN-Category/Tool/` (shallow clones) + `Summary-Repos.docx/.pdf` | transcribe → map to GitHub (follows moved repos) → measure (stars, SPDX, releases, registries) → clone + trees → per-repo research → comparison, selection guide, infographic check |
| `deep` | Attached images (category / package / concept diagrams) · attached files (md etc.) · attached site URLs — one or more, mixed (works without an image) | `OUT/<title>.docx/.pdf` + `<title>_assets/` (OUT rule in 4.4) | preserve inputs (`prd_intake.py` → `inputs/` + input table) → transcribe → **pre-research web check** + research spec → research (parallel or sequential: definition, source repo, install, usage, internals, performance, use cases, extensions) → repo and arXiv verification → **run a reference implementation (`sample/`)** → (optional hands-on experiment) → diagram verdicts — with a **quality gate** at each step (4.5) |
| `prd` | **Multiple inputs** (4.3) — analysis report docx/pdf (+ `_assets/`) · requirements / direction doc (md) · attached images · reference site / GitHub links · the prompt | `OUT/<Brand>_<Phrase>_PRD.docx/.pdf` + `<Brand>_UI_Design.pptx/.pdf` (OUT rule in 4.4) | intake, classification and requirement-item (RQ) extraction → every detailed item → an independently deployable unit (micro-agent) → FRs (`FR-<unit>-NN`, basis = RQ) → similar systems → GitHub stars/repos cross-check → UI/UX wireframes → packaging, release, Agent Manager → traceability gates |
| `sess-bak` | `~/.claude/projects` (Claude Code session jsonl · subagents · memory) | `~/.claude/session-history/<name>.md` (one per project) + `INDEX.md` | Merge only new sessions/messages (unchanged files are not rewritten, no separate backup copies) → keep sessions/memory whose source was deleted → abort on any loss → `--install-hook` runs it at every session end (`references/sess-bak.md`) |

### 4.2 `{ }` and `[ ]` in prompts
`{ }` marks values **extracted automatically** from the attachment (title, project name, document name, categories); `[ ]` marks detailed requirements **derived automatically** from it, which shape the classification, analysis axes, chapters, FRs and screens. Values you give explicitly take precedence.

```text
/wvs-report repos --root ~/wise-Analysis-Repos
  Using the attached image, clone the {sub-projects of each category} into the {Python-Tools-for-AI-Projects} project and write
  Summary-Repos.docx with directory structure, usage and scope of application, then convert to PDF
  (only some categories: --categories "Model & Data Security, Data Visualization")

/wvs-report deep --root ~/wise-Analysis-Repos
  The attachment is about {OCR+PDF Extractors} … [compare Native PDF · OCR Engines · Document Parsers · VLM+Specialists] …
  include [definition, source repo, install/config, usage and internals, use cases, extensions] (+ --experiment for a measured chapter)

/wvs-report prd "9AI-Concepts-That-Put-You-Ahead-of-99%-in-2026" --github-user WisemanLim
  Derive requirements from the {analysis report} → PRD named after {'The map behind production AI Systems'} (+ UI design deck; --ui-pptx false to skip)

/wvs-report prd docs/requirements.md ui-mock-1.png ui-mock-2.png https://www.bizinfo.go.kr https://github.com/langgenius/dify
  PRD covering every requirement item of the {requirements/direction doc} + UI mock-ups + reference sites and repos (works without an analysis report)

/wvs-report prd "9AI-Concepts-That-Put-You-Ahead-of-99%-in-2026" direction.md --links refs.txt
  analysis report + direction doc + a list of reference links (one URL per line) together
```

### 4.3 `prd` inputs — mix several kinds
| Input | Example | Used for |
|---|---|---|
| Analysis report `.docx`/`.pdf` (+ `<name>_assets/`) | output of `deep` mode | reuse research notes, verified repositories and the source diagram; consider every derived stack |
| Requirements / direction doc `.md`·`.txt`·`.rst` (`.docx`/`.pdf` with `--req`) | `requirements.md`, `direction.md`, a PRD draft | requirement items **RQ-NNN** extracted automatically (functional, UI, non-functional, constraint, goal, non-goal) → every functional, UI, non-functional and constraint RQ is **traced to FRs / NFRs / chapters** (build fails if any is missing) |
| Attached images `.png`·`.jpg`·`.webp`·`.svg`, image URLs | infographic, architecture diagram, UI mock-up, competitor screenshot | diagram → canonical source of units and information architecture / mock-up → screens and layout / quoted in 1.2 with credit |
| Reference site URLs | similar or competing products, public services, docs | feature lists, menu structure, UI patterns, pricing/licensing (chapters 4 and 15). No copying of text or images; URL and access date are cited |
| GitHub repository URLs | `https://github.com/owner/repo` | measured (stars, SPDX, activity) + README → reference OSS and integration mode (chapter 16) |
| Prompt | numbered items 1–6 · * · ** | RQs and the 1.1 user-requirement table |

- Pass files, folders and URLs together as positional arguments, or use `--req` · `--report` · `--image` · `--url` · `--links <urls.txt>`. Images and links attached to the conversation are inputs too.
- The first step runs `scripts/prd_intake.py`: it classifies and preserves inputs (`<Brand>_assets/inputs/IN-NN.*`) and writes `research/inputs.json`, `_INPUTS.md` (per-input transcription/summary slots) and `req_items.tsv` (RQ candidates). The agent then reads each input, fills the summaries and reviews the RQs (merge, split, fix types).
- Precedence on conflicts: prompt > requirements doc > analysis report / diagram > images (mock-ups) > reference sites. Conflicts and decisions are recorded in PRD 3.4.
- Added to the PRD: 2.1 input inventory, chapter 3 input analysis (per-input summary · RQ list · unit catalogue · conflicts and decisions), 21.4 RQ → FR / NFR / chapter traceability. New build gates: **0 unmapped RQs · 0 unsummarized inputs**.

### 4.4 Shared rules
- **Output folder (OUT)** — `deep` writes into `<root>/Miscellaneous-Data` and `prd` into `<root>/Need-to-be-organized-into-PRD` **when that folder exists**; **otherwise directly into `<root>`** (the default folder is never created). Override with `--out-dir <dir>`. The canonical rule is `wvs-report/scripts/out_dir.py`; the document and its `_assets/` folder always sit in the same OUT.
  - e.g. with `~/wise-Analysis-Repos/Miscellaneous-Data/` present → `~/wise-Analysis-Repos/Miscellaneous-Data/OCR+PDF Extractors.docx`; without it → `~/wise-Analysis-Repos/OCR+PDF Extractors.docx`
  - `prd` follows the same layout — inside `Need-to-be-organized-into-PRD/` if it exists, otherwise directly in `<root>`. `repos` is unchanged (`<root>/<Project>/`).
  - The build never stops on a missing figure file or research block (marked `[unverified]` + a `WARN:` list) — the docx/pdf is always written to OUT.
  - When `prd` gets an analysis report by name only, it looks in `<root>/Miscellaneous-Data/<name>` first, then `<root>/<name>`.
- Sources, licenses and referenced images are always cited (figure captions, stars + SPDX for repositories, source and figure appendices).
- **Previous documents used only as a format template are never cited** — checked after the build with `check_report.py --forbid`.
- Unverified facts are marked `[미확인]` (unverified); repositories and papers that cannot be verified are left out (`gh_probe.py`, `verify_sources.py`).
- Before finishing, the output is checked (blank pages, required IDs, forbidden strings) and rendered pages are inspected. Pipeline: the `deep` result is the input to `prd`.
- **`*_assets/` is pruned after completion** — once every gate passes, `prune_assets.py` keeps only the minimal set needed for rework (4.6). Pass `--keep-assets` to keep everything.

### 4.5 Host-independent quality gates (`deep`)
The same input produced very different depth depending on the agent (e.g. two infographics: 453 lines of research, 26 pages, 26 tables versus 1,836–2,025 lines, 64–69 pages, 89–114 tables). The causes were (1) the research-spec template being summarised and compressed, (2) every research unit being written in one pass without subagents, (3) web research being skipped (a real product was marked `[미확인]`), and (4) length rules that were advice nobody checked.
From v0.3.3 quality is decided by **script gates**, not by how diligent the model is. A run on Claude Code, Claude Desktop, Codex, Cursor, Gemini CLI, Windsurf, Devin, OpenCode, Antigravity, Copilot CLI, Command Code, Grok Build, OMP or VS Code is finished only when it passes the same floors.

| Step | Gate | Checks |
|---|---|---|
| Start | Host capability line | `subagents Y/N · web search Y/N · shell Y/N → parallel\|sequential mode`. Without subagents, research units are written one at a time with a gate after each |
| Research spec | `check_research.py --stage spec` | `_SPEC.md` has the 7 required sections and 50+ lines (no summarising), transcription items, **3+ primary-source URLs in the pre-research web check**, 4+ diagram-specific verdict candidates, the unit table (keys `PREFIX_NAME`) |
| Each unit | `check_research.py --unit rN_x.md` | item blocks 70+ lines with every required subheading, 3+ lines per subheading, code and 12+ lines under usage/implementation, a measured repository table, a verdict table with 3+ rows; other blocks 35+ lines and 3+ subheadings; 3+ references per block (URLs for non-arXiv sources) |
| Wrap-up | `check_research.py --stage final` | no failed repository or paper checks, 3+ figures, `sample/` reference code plus its run output (skip only with `--no-sample`) |
| After build | `check_report.py --min-pages 40 --min-tables 50` | page and table floors, blank pages, forbidden strings |

- The thresholds were set by running the gate on a good report (PASS) and a shallow one (139–165 FAIL lines). Each FAIL line names the file, block and subheading and says what to add.
- A FAIL that cannot be fixed because no evidence exists is reported with the reason, never padded with invented content. Full protocol: `skills/wvs-report/references/host-compat.md`.
- Host tips: enable subagents and web search where the host has them. On Cursor, Windsurf and similar, prefer a stronger reasoning model and long-context mode. Without a web tool, fall back to `curl` and `gh api`.

### 4.6 Pruning the assets folder after completion (`prune_assets.py`)
While a report is built, `*_assets/` collects a venv (hundreds of MB), cloned repositories, downloaded videos, generated figures and caches. From v0.3.4 all three modes **prune the assets folder as the last step**, after the final docx/pptx/pdf exists and every gate has passed, keeping only the code and environment information needed for a later version or rework.

| | What |
|---|---|
| Kept | code (`build_*.py`, `report_config.py`, `p_*.py`, `figs.py`, `sample/`, `exp/`, PRD/UI template copies), research sources `research/`, `measured.json`, measured-result JSON, original inputs (`inputs/`, `source_infographic.*`, videos excluded), `.wvs_kit` — text files up to 2 MB each |
| Deleted | `.venv`, `__pycache__` and other caches, `.omc`, `node_modules`, cloned repositories (folders containing `.git`), generated figures (`fig_*.png`, wireframes), videos, logs, intermediate docx/pptx/pdf, large files |
| Created | `requirements.txt` (venv package versions frozen before deletion), `ASSETS.md` (date, final outputs, deleted items, rebuild steps) |

```bash
KIT=<skills>/wvs-report/scripts
python3 $KIT/prune_assets.py "<OUT>/<title>_assets" --dry-run     # list what would be deleted
python3 $KIT/prune_assets.py "<OUT>/<title>_assets"               # prune (for prd: <Brand>_assets and <Brand>_UI_assets)

# rework / new version — same as the steps in ASSETS.md
bash $KIT/setup_env.sh "<OUT>/<title>_assets"                      # recreates .venv and installs requirements.txt
(cd "<OUT>/<title>_assets" && .venv/bin/python figs.py && WVS_KIT=$KIT .venv/bin/python build_report.py --pdf)
```
- Safeguards: refuses a folder not named `*_assets` or one without a final docx/pptx beside it (override with `--force`), refuses git repositories, never follows symlinks. Running it again on a pruned folder changes nothing (`ASSETS.md` is kept).
- In `repos` mode the per-category clones (`<Project>/NN-category/tool/`) are deliverables and are not touched — only `_assets/` is pruned. `prd` never touches the base `deep` report's `_assets/`.
- `--drop-inputs` also deletes the original inputs. The pruning result (space freed) is one line of the final report.

---

## 5. Usage — wvs-tools (`wvs` CLI)

Use `/wvs-tools <task>` inside an agent or `wvs <task>` in a terminal (after `--bin-dir`, or run `<skills>/wvs-tools/scripts/wvs` directly).

| Task | Description | Example |
|---|---|---|
| `pdf` | `.md` (Mermaid → PNG, pandoc + xelatex, CJK fonts) / `.docx`·`.pptx` (LibreOffice) → PDF with the same name | `wvs pdf REPORT.md -C` · `wvs pdf "A+B.docx"` |
| `archive` | tar.gz with default excludes, `--split 2048m`, `--remove`, `--dry-run` | `wvs archive -o out.tar.gz ./src ./docs` |
| `clean` | Remove `.DS_Store`, `__pycache__`, `Thumbs.db` …, custom patterns `-D/-F/-E` | `wvs clean . --dry-run` |
| `bookmarks` | De-duplicate Chrome bookmarks (per folder/global, URL normalization, `.bak` with `--in-place`) | `wvs bookmarks -i Bookmarks --dry-run` |
| `deploy ios` | Xcode archive → TestFlight upload, build number +1 | `wvs deploy ios ./app` |
| `deploy android` | Gradle → Google Play (fastlane), versionCode +1 | `wvs deploy android ./app` |
| `dist` | Service bootstrap (repo sync, Docker, compose, Makefile) — TUI, `--cli`, `--no-run`, old version via `--classic` | `wvs dist -I "<url1> <url2>" --cli` |
| `doctor` · `list` · `help <task>` | Tool check · task ↔ script map · original script help | `wvs help archive` |

For deletions, uploads and overwrites the skill shows a `--dry-run` first and asks before running. Credentials (`.deploy-*.env`, `*.p8`, service-account JSON) are excluded by `.gitignore`.

---

## 6. Built-in alternatives and when they replace these skills

If your agent or service already ships a similar built-in feature, you can use it instead. The table shows **what is replaceable and what only this skill set provides**.
(As of 2026-10. Built-ins change between versions — check each agent's `/help`.)

| This skill set | Built-in alternative | Replaceable? | How to choose |
|---|---|---|---|
| `wvs-tools pdf` (md → PDF) | Claude: Anthropic **`pdf` skill** (create, merge, split, extract, forms; built into Claude.ai/Desktop, for Claude Code via `/plugin marketplace add anthropics/skills`) · Gemini CLI · Codex · Copilot CLI: no dedicated command (the agent runs pandoc etc.) | **Partly** | General PDF work is covered by the `pdf` skill. Use `wvs pdf` for **Mermaid rendering + CJK fonts + xelatex publication quality + toolchain check and guided install** |
| `wvs-tools pdf` (docx/pptx → PDF) | Anthropic **`docx` / `pptx` skills** (create/edit) · LibreOffice `soffice --convert-to pdf` | **Yes** | Same result for plain conversion; `wvs pdf` also handles special-character file names and an isolated profile |
| `wvs-review` L1 structure | Claude Code `/init` (CLAUDE.md) · Codex `/init` (AGENTS.md) · Gemini CLI `/init` (GEMINI.md) | **Partly** | `/init` writes an agent **context file**. Use L1 for a human-readable 8-step **report** (multi-project comparison, PDF) |
| `wvs-review` L2 commercial | Claude Code `/security-review` · Gemini CLI security extension (`/security:analyze`) · Copilot app `/security-review` | **Partly (security only)** | Built-ins focus on **vulnerabilities**. **License audit, GPL/AGPL propagation, ISO 5230 and a commercial risk rating** exist only in L2 |
| `wvs-review` L3 guide | `/init`-style context files | **Partly** | Use L3 for human **bilingual onboarding and implementation guides** |
| `wvs-review` L4 code | Claude Code `/review` and `code-review` skill · Codex `/review` · Copilot CLI `/review` · Cursor `/review` (Bugbot, 3.7+) · Gemini CLI code-review extension · GitHub PR review | **Partly** | Built-ins find **defects in a diff**. L4 writes an **educational/handover walkthrough of the whole code base at reader level R0–R4**. For PR gates prefer the built-ins |
| `wvs-review --stars` | none | **No** | Bulk, incremental analysis of hundreds to thousands of starred repos |
| `wvs-report repos` / `deep` | Claude **Research** · Gemini **Deep Research** and similar web research reports | **Partly (research step)** | A research summary alone is replaceable. **Cloning, directory trees, GitHub/registry/arXiv verification, diagram verdicts and the house docx/pdf template** are only in wvs-report |
| `wvs-report prd` | PRD template skills/plugins · Anthropic `docx`/`pptx` skills (document format) | **Partly** | A generic PRD draft is replaceable. **Diagram → micro-agent decomposition, 100 % requirement-doc RQ↔FR and FR↔screen traceability gates, merging several inputs (docs, mock-ups, reference links), stars/repos cross-check and the UI design deck** are only in wvs-report prd |
| `wvs-tools archive` · `clean` | `tar` · `find … -delete` | **Yes** | Use `wvs` for excludes, splitting and dry-run in one command |
| `wvs-tools bookmarks` | Browser extensions, manual cleanup | **Yes** | Use `wvs` to keep folder structure with backup and dry-run |
| `wvs-tools deploy` | fastlane (`pilot`, `supply`) · Xcode Cloud · Gradle Play Publisher | **Yes** | Keep your CI/CD if you have one; `wvs deploy` is a one-line local upload |
| `wvs-tools dist` | `gh repo clone` + `docker compose` by hand | **Yes** | Use `wvs dist` for interactive multi-repo sync, compose selection and Makefile generation |

---

## 7. Migrating from v0.1 commands

| Old command | New call |
|---|---|
| `/analysis-source <p>` | `/wvs-review <p> --level 1` |
| `/in-depth-review <p>` | `/wvs-review <p> --only commercial` (with the structure report: `--level 2`) |
| `/create-guide4junior <p>` | `/wvs-review <p> --only guide` |
| `/code-review-by-levels <p> --level N` | `/wvs-review <p> --only code --reader N` |
| `/totally-analysis-based-on-star --input f.md` | `/wvs-review --stars f.md` |
| `/convert-to-pdf -I X.md` | `/wvs-tools pdf X.md` · `wvs pdf X.md` |
| the 8 `ref-sh` scripts | `wvs archive · clean · bookmarks · pdf · deploy ios/android · dist [--classic]` |
| `/oss-clone-analysis` · `/attachment-deep-analysis` · `/requirement-based-prd` | `/wvs-report repos` · `/wvs-report deep` · `/wvs-report prd` |
| `wise-report-kit` | `wvs-report/scripts/` (internal toolkit) |

Old option names (`--review-result`, `--pdf true|false`, `-O`) are still accepted.

---

## 8. Troubleshooting / FAQ

| Symptom | Fix |
|---|---|
| Skills do not show up | Restart the agent in a **new session**; check locations with `npx wise-vibe-skills doctor`; use `--dir` for unlisted agents |
| `curl … install.sh` returns 404 | The repository is private (or not published). curl does not use gh credentials → use `gh api … install.sh \| bash` from 2.1, or `gh repo clone` and `./install.sh` |
| Old commands such as `/analysis-source` appear twice | Delete `~/.claude/commands/<old-name>.md` yourself (the installer only warns) |
| A `deep` report is shallow (few pages/tables, one-line subheadings) | Run `python3 <skills>/wvs-report/scripts/check_research.py --assets "<title>_assets" --stage final` to find the thin blocks, expand only those research units, then rebuild (4.5) |
| `wvs-report/scripts 를 찾을 수 없습니다` (toolkit not found) | `export WVS_KIT=<skills>/wvs-report/scripts` |
| GitHub measurements are slow or fail | `gh auth login` (5,000 requests/hour when authenticated vs. 60 anonymous) |
| docx → PDF fails | Install LibreOffice: macOS `brew install --cask libreoffice` · Debian `sudo apt-get install -y libreoffice-writer libreoffice-impress` |
| Broken Korean glyphs in PDF | Install Noto Sans CJK KR or set `WVS_FONT="<font name>"` |
| Rebuilding a pruned `*_assets` folder | Follow the rebuild steps in `ASSETS.md` — `setup_env.sh <assets>` (installs requirements.txt) → `figs.py` → the build script with `--pdf` (4.6) |
| `prune_assets.py` refuses (`no final docx/pptx`) | The report is not built yet or its name differs from the assets folder → build first, or pass `--force` if intended |
| `wvs` on Windows | Use Git Bash/WSL: `bash <skills>/wvs-tools/scripts/wvs …` |

---

## 9. Repository layout, development, release

```
install.sh                       curl | bash installer (bash 3.2 compatible, truncation guard)
bin/wise-vibe-skills.mjs         npx installer (install · uninstall · list · doctor · zip), no dependencies
.claude-plugin/                  Claude Code plugin and marketplace manifests
skills/
├── wvs-review/   SKILL.md · references/{structure,commercial,guide,code,bulk-stars}.md
├── wvs-report/   SKILL.md · references/{repos,deep,deep-research-spec,host-compat,prd,kit,…}.md · scripts/ (docx engine, verification, cloning, wireframes, pptx, research-depth gate, checks, assets pruning) · templates/{repos,deep,prd}/
└── wvs-tools/    SKILL.md · references/{pdf,scripts,dist}.md · scripts/wvs · scripts/lib/*.sh
tests/                           run.sh · validate_skills.py · smoke_kit.py · smoke_deep.py · smoke_research.py · smoke_prd.py · smoke_ui.py
```

- **Design**: each `SKILL.md` is a short router (level, mode, task); detailed procedures in `references/` are read only when that part runs, keeping context small.
- **Tests**: `bash tests/run.sh` — metadata, syntax, shellcheck, bash/npx destination parity, install / v0.1 cleanup / uninstall, bin link, zip, `wvs` dispatch, a report-toolkit smoke build (docx/pptx/pdf), the research-depth gate (shallow research fails, thorough research passes) a PRD multi-input smoke test (input classification, RQ tracing, gates passing/failing) and assets pruning (keep/delete, requirements.txt, ASSETS.md, re-run, refusal). Reuse a venv with `WVS_TEST_PY=<venv python>`.
- **Kept out of the repo**: `.gitignore` excludes OS files (.DS_Store, Thumbs.db), personal environments (.vscode, .idea, *.code-workspace, .env, .venv), agent sessions and conversation logs (.claude/, .codex/, .gemini/, .cursor/, .omc/, *.jsonl, sessions/), review/report outputs (.review/) and signing material (*.p8, *.keystore, service-account JSON). `.gitattributes` pins LF line endings for shell scripts.
- **Release**: bump `VERSION`, `package.json`, `.claude-plugin/*.json` and `VERSION` inside `wvs` together → `bash tests/run.sh` → commit → `git tag vX.Y.Z && git push --tags` → (optional) `npm publish`.

---

## 10. References, sources, license
- Installer design: [REA — Get started](https://rea.tools/get-started/), [morluto/rea](https://github.com/morluto/rea) (`install.sh`, `docs/installation.md`, `src/application/SupportedClients.ts`)
- Original skills: [WisemanLim/expired-wise-skills](https://github.com/WisemanLim/expired-wise-skills) `commands/`
- Built-in comparison: [Claude Code slash commands](https://code.claude.com/docs/en/commands) · [anthropics/skills](https://github.com/anthropics/skills) · [Codex CLI slash commands](https://developers.openai.com/codex/cli/slash-commands) · [Gemini CLI commands](https://geminicli.com/docs/reference/commands) · [Gemini CLI code review & security extensions codelab](https://codelabs.developers.google.com/gemini-cli-code-analysis) · [GitHub Copilot CLI command reference](https://docs.github.com/en/copilot/reference/cli-command-reference) · [Cursor Bugbot](https://docs.cursor.com/bugbot)
- License: not chosen yet. Add a `LICENSE` file before publishing publicly.
