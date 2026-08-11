---
name: build-textbook-learning-package
description: Orchestrate multi-agent conversion of university textbooks or PDF chapters into beginner-friendly Traditional Chinese PPTX/PDF teaching decks and DOCX/PDF exercise study guides. Use when Codex must lock source scope, design a dependency-first course, generate pedagogical images, write complete bilingual exercise solutions, build editable artifacts, render-verify every page, and coordinate Sol/Luna custom agents through a defect-routing review loop.
---

# Build Textbook Learning Package

Create a source-grounded teaching package through explicit contracts, deterministic validation, and an independent final review. Treat the final artifacts as the product; scripts and chat summaries are only supporting evidence.

## Load the workflow

Read these files before acting:

1. [references/workflow.md](references/workflow.md) for phase order, owners, and stopping rules.
2. [references/handoff-contracts.md](references/handoff-contracts.md) before creating or delegating work.
3. [references/qa-gates.md](references/qa-gates.md) before building, reviewing, or declaring completion.

Use the PDF, Presentations, Documents, and ImageGen skills when those artifact types are in scope. Follow their render-and-verify requirements in addition to this Skill.

## Use the agent team

Use the installed custom agents when available:

- `textbook_lead`: Sol `xhigh`; own source scope, pedagogy, visual direction, image generation, routing, and final review.
- `textbook_writer`: Luna `max`; own slide copy, speaker notes, exact original questions, translations, solutions, and terminology.
- `textbook_production`: Luna `xhigh`; own extraction, normalization, build scripts, assembly, export, rendering, audits, and mechanical fixes.

If the current agent is not acting as `textbook_lead`, delegate overall orchestration to `textbook_lead` and wait for its result. The lead must delegate bounded content and production work after the plan is locked. If custom agents are unavailable, preserve the same role separation in sequential passes and perform a fresh-context review before final delivery.

Do not delegate responsibility for final acceptance. The lead must inspect the rendered artifacts itself.

## Establish the workspace

Run:

```text
python scripts/init_pipeline_workspace.py <project-root>
```

Keep intermediate files under `work/` and final deliverables under `outputs/`. Use the paths and schemas in the handoff contract. Never use chat-only handoffs for source scope, exercise coverage, content, or defects.

## Execute the pipeline

### 1. Lock source and scope

- Identify the edition, chapter, PDF page range, textbook page range, and source authority.
- Inventory every Practice Exercise, Exercise, Programming Problem, and Programming Project present in the supplied source.
- Record missing pages and contradictions. Do not invent absent original questions.
- Define required formats, language, learner level, teaching time, and expected coverage.
- Write `SCOPE_LOCKED` only when every required item is traceable to a source page.

### 2. Lock pedagogy and visuals

- Define learner assumptions, prerequisites, observable objectives, concept dependencies, misconceptions, knowledge checks, and takeaways.
- Re-sequence for learning rather than mirroring the textbook section order.
- Select complete worked examples with inputs, intermediate states, answer, and independent verification method.
- Define the deck plan, glossary, source ledger, asset manifest, and visual specification.
- Have the lead generate any pedagogical raster images. Use editable native shapes for precise diagrams, algorithms, graphs, tables, timelines, and state traces.
- Write `PLAN_LOCKED` before high-volume writing or assembly starts.

### 3. Produce content and build scaffolding

Run content and production preparation in parallel when safe.

The writer must:

- Preserve complete original questions without summarizing long prompts.
- Provide Traditional Chinese translations, prerequisite knowledge, answers, full reasoning, and misconceptions.
- Show intermediate states for numerical and algorithmic work.
- Write speaker notes with teaching intent, talk track, prompt, misconception watch, transition, and sources.
- Apply the locked glossary and flag uncertainty instead of silently guessing.

The production agent must:

- Extract text and figures with page provenance.
- Create reproducible deck, handout, export, render, and audit scripts.
- Build independent checkers for calculations or algorithms named in the plan.
- Smoke-test both the normal export path and a non-Office fallback before full production.

### 4. Assemble and validate

- Build editable PPTX and DOCX artifacts from the locked contracts.
- Export PDFs from the final native artifacts when the normal path is available.
- Render every slide and page to images.
- Run `scripts/audit_pipeline.py <project-root>` during production.
- Inspect page geometry, fonts, titles, page numbers, arrows, tables, code blocks, question/answer separation, and blank pages.
- Compare PPTX with slide PDF and DOCX with handout PDF.

### 5. Review and route defects

The lead must review actual rendered outputs and write defects to `work/06_qa/defect_ledger.csv`.

Route defects as follows:

- `content`, `translation`, `solution`, `terminology`, `speaker_notes` -> `textbook_writer`.
- `extraction`, `layout`, `pagination`, `numbering`, `render`, `export`, `build`, `packaging` -> `textbook_production`.
- Ambiguous pedagogy, answer strategy, scope, or visual storytelling -> `textbook_lead` decides first, then delegates implementation.

After each fix, rebuild from source and run the full regression audit. Do not validate only the changed page.

### 6. Complete the final gate

Run:

```text
python scripts/audit_pipeline.py <project-root> --final
```

Require all QA gates to pass. Keep only final deliverables in `outputs/`. Do not declare completion while P0 or P1 defects remain, original questions are abbreviated, notes or sources are missing, or rendered pages have not been inspected.

## Stop and escalate

- Stop when a source page or user decision is required to determine scope or the correct answer.
- After three failed fixes for the same defect, change the implementation strategy instead of continuing small adjustments.
- If an export engine is unavailable or quota-limited, use the pre-tested fallback and disclose the format provenance in the QA ledger.
- Never call a learning solution official unless the supplied or cited source explicitly establishes that status.
