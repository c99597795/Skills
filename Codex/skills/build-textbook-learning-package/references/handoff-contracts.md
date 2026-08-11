# Handoff Contracts

## Contents

1. Directory layout
2. Lock markers
3. Core file schemas
4. Defect routing

## Directory layout

```text
work/
  00_intake/
    source_manifest.yaml
    requirements.md
  01_strategy/
    course_blueprint.md
    glossary.csv
    source_ledger.csv
    visual_spec.md
  02_plan/
    deck_plan.json
    exercise_coverage.csv
    asset_manifest.csv
  03_content/
    slide_copy.md
    speaker_notes.md
    exercises.json
  04_assets/
    generated/
    extracted/
  05_build/
  06_qa/
    automated_results.json
    visual_review.md
    defect_ledger.csv
    final_signoff.md
outputs/
```

## Lock markers

- `SCOPE_LOCKED` belongs in `work/00_intake/requirements.md`.
- `PLAN_LOCKED` belongs in `work/01_strategy/course_blueprint.md`.
- Agents must not begin full writing or assembly before both markers exist.
- A lead-approved scope or plan change must update the affected contracts before work resumes.

## Core file schemas

### source_manifest.yaml

Required fields:

```yaml
source_title: ""
edition: ""
chapter: ""
source_files: []
pdf_page_range: ""
textbook_page_range: ""
authority: "user-supplied"
language: ""
notes: ""
```

### glossary.csv

```text
term_en,term_zh_tw,plain_language,first_source_ref,notes
```

### source_ledger.csv

```text
source_id,source_file,pdf_page,textbook_page,topic,claim_or_asset,usage,notes
```

### deck_plan.json

Use this root shape:

```json
{
  "metadata": {},
  "sections": [],
  "slides": [
    {
      "slide_id": "",
      "title": "",
      "purpose": "",
      "core_concept": "",
      "learner_visible_takeaway": "",
      "visual_type": "",
      "source_refs": [],
      "speaker_notes_requirements": {}
    }
  ]
}
```

### exercise_coverage.csv

```text
number,category,source_ref,original_complete,translation_complete,knowledge_complete,answer_complete,steps_complete,verification,status,notes
```

Allowed final `status` values: `complete`, `not_in_source`, `out_of_scope_approved`.

### asset_manifest.csv

```text
asset_id,type,purpose,source_or_prompt,owner,file_path,editable,source_ref,status,notes
```

### exercises.json

Each exercise record must contain:

```json
{
  "number": "",
  "category": "",
  "source_ref": "",
  "original": "",
  "translation_zh_tw": "",
  "reference_knowledge": [],
  "answer": "",
  "steps": [],
  "misconceptions": [],
  "verification": "",
  "notes": ""
}
```

### defect_ledger.csv

```text
id,severity,artifact,page,category,description,expected,owner,status,verification
```

Severities:

- `P0`: corrupt, missing deliverable, materially wrong answer, or unusable output.
- `P1`: missing required content, clipping, wrong arrow semantics, incomplete original question, or major drift.
- `P2`: localized clarity, density, styling, or non-blocking consistency issue.

Statuses: `open`, `fixed_pending_review`, `closed`, `accepted_limitation`.

## Defect routing

Writer-owned categories:

- `content`
- `translation`
- `solution`
- `terminology`
- `speaker_notes`

Production-owned categories:

- `extraction`
- `layout`
- `pagination`
- `numbering`
- `render`
- `export`
- `build`
- `packaging`

Lead-owned categories:

- `scope`
- `pedagogy`
- `answer_strategy`
- `visual_story`
