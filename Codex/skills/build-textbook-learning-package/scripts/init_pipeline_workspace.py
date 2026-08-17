#!/usr/bin/env python3
"""Initialize the shared contract workspace for a textbook learning package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DIRECTORIES = (
    "work/00_intake",
    "work/01_strategy",
    "work/02_plan",
    "work/03_content",
    "work/04_assets/generated",
    "work/04_assets/extracted",
    "work/05_build",
    "work/06_qa",
    "outputs",
)


FILES = {
    "work/00_intake/source_manifest.yaml": """source_title: ""
edition: ""
chapter: ""
source_files: []
pdf_page_range: ""
textbook_page_range: ""
authority: "user-supplied"
language: ""
notes: ""
""",
    "work/00_intake/requirements.md": """# Requirements

## Requested deliverables

## Learner and language

## Scope

## Constraints

<!-- Add SCOPE_LOCKED only after every required item is source-traceable. -->
""",
    "work/01_strategy/course_blueprint.md": """# Course Blueprint

## Learner profile

## Prerequisites

## Observable objectives

## Concept dependencies

## Teaching narrative

## Worked examples

## Misconceptions and checks

<!-- Add PLAN_LOCKED only after the lead freezes pedagogy and visuals. -->
""",
    "work/01_strategy/glossary.csv": (
        "term_en,term_zh_tw,plain_language,first_source_ref,notes\n"
    ),
    "work/01_strategy/source_ledger.csv": (
        "source_id,source_file,pdf_page,textbook_page,topic,claim_or_asset,usage,notes\n"
    ),
    "work/01_strategy/visual_spec.md": """# Visual Specification

## Canvas and typography

## Color semantics

## Editable technical visuals

## Raster image policy

## Density and geometry limits

## Question and answer reveal rules
""",
    "work/02_plan/deck_plan.json": json.dumps(
        {"metadata": {}, "sections": [], "slides": []}, ensure_ascii=False, indent=2
    )
    + "\n",
    "work/02_plan/exercise_coverage.csv": (
        "number,category,source_ref,original_complete,translation_complete,"
        "knowledge_complete,answer_complete,steps_complete,verification,status,notes\n"
    ),
    "work/02_plan/asset_manifest.csv": (
        "asset_id,type,purpose,source_or_prompt,owner,file_path,editable,source_ref,status,notes\n"
    ),
    "work/03_content/slide_copy.md": "# Slide Copy\n",
    "work/03_content/speaker_notes.md": "# Speaker Notes\n",
    "work/03_content/exercises.json": "[]\n",
    "work/06_qa/automated_results.json": "{}\n",
    "work/06_qa/visual_review.md": """# Visual Review

## Rendered artifacts

## Pages inspected

## Findings
""",
    "work/06_qa/defect_ledger.csv": (
        "id,severity,artifact,page,category,description,expected,owner,status,verification\n"
    ),
    "work/06_qa/final_signoff.md": """# Final Sign-off

## Artifacts

## Counts

## Known limitations

## Result

PENDING
""",
}


def write_file(path: Path, content: str, force: bool) -> str:
    if path.exists() and not force:
        return "skipped"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return "written"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing contract template files. Source files are never touched.",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    for relative in DIRECTORIES:
        (root / relative).mkdir(parents=True, exist_ok=True)

    results = {
        relative: write_file(root / relative, content, args.force)
        for relative, content in FILES.items()
    }
    summary = {
        "project_root": str(root),
        "written": sum(value == "written" for value in results.values()),
        "skipped": sum(value == "skipped" for value in results.values()),
        "files": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
