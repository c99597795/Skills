# Workflow

## Contents

1. Operating model
2. Phase 0 — Intake
3. Phase 1 — Source and scope lock
4. Phase 2 — Pedagogical and visual lock
5. Phase 3 — Parallel content and production preparation
6. Phase 4 — Assembly and first QA
7. Phase 5 — Lead review and repair loop
8. Phase 6 — Final delivery

## Operating model

The lead is accountable for the whole result. The writer and production agent are bounded specialists. All durable state lives in the shared contract files, not in agent memory.

```text
Source -> Lead scope/design -> Writer content
                           -> Production scaffold
Writer + Production + Lead assets -> Production assembly
Production renders/audits -> Lead review
Lead content defects -> Writer -> Production rebuild
Lead mechanical defects -> Production rebuild
Production regression -> Lead sign-off -> outputs/
```

Work in the source chapter's project directory. Keep source files unchanged. Use `work/` for intermediate artifacts and `outputs/` for final files.

## Phase 0 — Intake

Owner: lead.

Inputs:

- User request and supplied source files.
- Required language, formats, teaching duration, and learner level.

Actions:

1. Confirm whether the request includes a deck, study guide, both, or a subset.
2. Identify source files and check that they open.
3. Record requested naming, versioning, and output constraints.
4. Initialize the pipeline workspace.

Exit:

- `requirements.md` reflects the user request without inferred scope expansion.

## Phase 1 — Source and scope lock

Owner: lead. Production may extract and inventory.

Actions:

1. Identify textbook title, edition, chapter, and page mappings.
2. Record source authority and any supporting official sources.
3. Inventory every exercise category and exact number found in the source.
4. Map each topic, figure, table, and exercise to source pages.
5. Record missing, unreadable, duplicated, or contradictory material.
6. Define what is out of scope.

Exit:

- `source_manifest.yaml`, `source_ledger.csv`, and `exercise_coverage.csv` agree.
- `SCOPE_LOCKED` appears in `requirements.md`.

## Phase 2 — Pedagogical and visual lock

Owner: lead.

Actions:

1. Define prerequisites and observable objectives.
2. Build a dependency-first concept map.
3. Choose a motivating scenario and instructional narrative.
4. Select complete worked examples and verification methods.
5. Plan misconception checks, question/reveal pairs, recap, and takeaways.
6. Define slide purposes, visual types, sources, and notes requirements.
7. Define typography, color semantics, geometry, density, and asset rules.
8. Generate only the raster images that add pedagogical value.

Exit:

- `course_blueprint.md`, `deck_plan.json`, `glossary.csv`, `visual_spec.md`, and `asset_manifest.csv` are complete.
- `PLAN_LOCKED` appears in `course_blueprint.md`.

## Phase 3 — Parallel content and production preparation

Owners: writer and production.

Writer output:

- Slide copy and speaker notes.
- Complete exercise records.
- Explicit uncertainty markers tied to source references.

Production output:

- Page-provenanced extraction.
- Build, export, render, and audit scripts.
- Calculation and algorithm verification.
- Normal and fallback export smoke tests.

Synchronization rule:

- Neither agent may change the locked plan. Proposed changes go to the lead and are recorded before implementation.

Exit:

- Every in-scope exercise row is content-complete.
- Representative deck and document pages build, reopen, and render.

## Phase 4 — Assembly and first QA

Owner: production.

Actions:

1. Assemble final native artifacts from contract files.
2. Export PDFs.
3. Verify ZIP integrity for PPTX and DOCX.
4. Verify slide count, notes count, PDF page counts, and exercise coverage.
5. Render all pages and inspect montage plus original-size high-density pages.
6. Compare native and PDF outputs.
7. Fix mechanical defects and rerun the complete build.

Exit:

- Automated audit passes without P0/P1 mechanical defects.
- `visual_review.md` names the pages inspected and issues found.

## Phase 5 — Lead review and repair loop

Owner: lead.

Review the actual native artifacts and rendered pages across four lanes:

1. Pedagogy: order, scaffolding, cognitive load, examples, checks, answer reveals.
2. Content: exact questions, translation, calculations, proofs, terminology, sources.
3. Visuals: hierarchy, density, arrows, tables, page numbers, titles, images.
4. Delivery: editability, native/PDF consistency, clean outputs, openability.

Every defect requires severity, artifact, page, category, description, owner, status, and verification.

Repair loop:

1. Writer fixes semantic content first when both content and layout are affected.
2. Production rebuilds and fixes the resulting mechanical layout.
3. Production reruns full regression and original-size checks for affected pages.
4. Lead closes defects only after inspecting evidence.

After three failed attempts for the same defect, the lead changes the strategy or specification.

## Phase 6 — Final delivery

Owner: lead.

Actions:

1. Run the final audit.
2. Confirm all required deliverables and only final deliverables are in `outputs/`.
3. Write `final_signoff.md` with artifact names, counts, known limitations, and PASS.
4. Deliver clickable file links and a concise QA summary.

Exit:

- No open P0/P1 defects.
- All required gates in `qa-gates.md` pass.
