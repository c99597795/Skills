#!/usr/bin/env python3
"""Audit pipeline contracts and generated textbook learning artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile


REQUIRED_FILES = (
    "work/00_intake/source_manifest.yaml",
    "work/00_intake/requirements.md",
    "work/01_strategy/course_blueprint.md",
    "work/01_strategy/glossary.csv",
    "work/01_strategy/source_ledger.csv",
    "work/01_strategy/visual_spec.md",
    "work/02_plan/deck_plan.json",
    "work/02_plan/exercise_coverage.csv",
    "work/02_plan/asset_manifest.csv",
    "work/03_content/slide_copy.md",
    "work/03_content/speaker_notes.md",
    "work/03_content/exercises.json",
    "work/06_qa/visual_review.md",
    "work/06_qa/defect_ledger.csv",
    "work/06_qa/final_signoff.md",
)

CSV_SCHEMAS = {
    "work/01_strategy/glossary.csv": {
        "term_en",
        "term_zh_tw",
        "plain_language",
        "first_source_ref",
        "notes",
    },
    "work/01_strategy/source_ledger.csv": {
        "source_id",
        "source_file",
        "pdf_page",
        "textbook_page",
        "topic",
        "claim_or_asset",
        "usage",
        "notes",
    },
    "work/02_plan/exercise_coverage.csv": {
        "number",
        "category",
        "source_ref",
        "original_complete",
        "translation_complete",
        "knowledge_complete",
        "answer_complete",
        "steps_complete",
        "verification",
        "status",
        "notes",
    },
    "work/02_plan/asset_manifest.csv": {
        "asset_id",
        "type",
        "purpose",
        "source_or_prompt",
        "owner",
        "file_path",
        "editable",
        "source_ref",
        "status",
        "notes",
    },
    "work/06_qa/defect_ledger.csv": {
        "id",
        "severity",
        "artifact",
        "page",
        "category",
        "description",
        "expected",
        "owner",
        "status",
        "verification",
    },
}

JSON_FILES = (
    "work/02_plan/deck_plan.json",
    "work/03_content/exercises.json",
)

ALLOWED_OUTPUT_EXTENSIONS = {".pptx", ".pdf", ".docx"}
FINAL_EXERCISE_STATUSES = {"complete", "not_in_source", "out_of_scope_approved"}


class Audit:
    def __init__(self, root: Path, final: bool):
        self.root = root
        self.final = final
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.metrics: dict[str, object] = {}

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def check_required_files(self) -> None:
        for relative in REQUIRED_FILES:
            if not (self.root / relative).is_file():
                self.error(f"Missing required contract: {relative}")

    def check_locks(self) -> None:
        checks = {
            "work/00_intake/requirements.md": "SCOPE_LOCKED",
            "work/01_strategy/course_blueprint.md": "PLAN_LOCKED",
        }
        for relative, marker in checks.items():
            path = self.root / relative
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if marker not in text:
                message = f"Missing lock marker {marker} in {relative}"
                self.error(message) if self.final else self.warn(message)

    def read_csv(self, relative: str) -> list[dict[str, str]]:
        path = self.root / relative
        if not path.is_file():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing = CSV_SCHEMAS[relative] - fields
            if missing:
                self.error(f"{relative} missing columns: {sorted(missing)}")
            return list(reader)

    def check_csv_contracts(self) -> None:
        rows_by_file = {relative: self.read_csv(relative) for relative in CSV_SCHEMAS}

        coverage = rows_by_file["work/02_plan/exercise_coverage.csv"]
        self.metrics["exercise_rows"] = len(coverage)
        if self.final and not coverage:
            self.warn("Exercise coverage has no rows; confirm the requested scope contains no exercises.")
        for index, row in enumerate(coverage, start=2):
            status = (row.get("status") or "").strip()
            if self.final and status not in FINAL_EXERCISE_STATUSES:
                self.error(
                    f"Exercise coverage row {index} has non-final status: {status!r}"
                )
            if status == "complete":
                for field in (
                    "original_complete",
                    "translation_complete",
                    "knowledge_complete",
                    "answer_complete",
                    "steps_complete",
                ):
                    if (row.get(field) or "").strip().lower() not in {"yes", "true", "1"}:
                        self.error(
                            f"Exercise {row.get('number', index)} is complete but {field} is not true"
                        )

        defects = rows_by_file["work/06_qa/defect_ledger.csv"]
        open_critical = [
            row
            for row in defects
            if (row.get("severity") or "").strip().upper() in {"P0", "P1"}
            and (row.get("status") or "").strip().lower()
            not in {"closed", "accepted_limitation"}
        ]
        self.metrics["open_p0_p1_defects"] = len(open_critical)
        if self.final and open_critical:
            ids = [row.get("id") or "<missing-id>" for row in open_critical]
            self.error(f"Open P0/P1 defects remain: {ids}")

    def check_json_contracts(self) -> None:
        for relative in JSON_FILES:
            path = self.root / relative
            if not path.is_file():
                continue
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                self.error(f"Invalid JSON in {relative}: {exc}")

    def inspect_pptx(self, path: Path) -> None:
        try:
            with ZipFile(path) as archive:
                corrupt = archive.testzip()
                if corrupt:
                    self.error(f"Corrupt PPTX member in {path.name}: {corrupt}")
                    return
                names = archive.namelist()
        except BadZipFile:
            self.error(f"Invalid PPTX ZIP container: {path.name}")
            return

        slides = [
            name
            for name in names
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        ]
        notes = [
            name
            for name in names
            if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        ]
        self.metrics[f"{path.name}:slides"] = len(slides)
        self.metrics[f"{path.name}:notes"] = len(notes)
        if not slides:
            self.error(f"PPTX has no slides: {path.name}")
        if len(notes) != len(slides):
            self.error(
                f"PPTX slide/notes mismatch in {path.name}: {len(slides)} slides, {len(notes)} notes"
            )

    def inspect_docx(self, path: Path) -> None:
        try:
            with ZipFile(path) as archive:
                corrupt = archive.testzip()
                names = set(archive.namelist())
        except BadZipFile:
            self.error(f"Invalid DOCX ZIP container: {path.name}")
            return
        if corrupt:
            self.error(f"Corrupt DOCX member in {path.name}: {corrupt}")
        if "word/document.xml" not in names:
            self.error(f"DOCX missing word/document.xml: {path.name}")

    def inspect_pdf(self, path: Path) -> None:
        try:
            from pypdf import PdfReader  # type: ignore
        except ImportError:
            self.warn(f"pypdf unavailable; skipped PDF page count for {path.name}")
            return
        try:
            pages = len(PdfReader(str(path)).pages)
        except Exception as exc:  # pypdf exposes several parser exception types
            self.error(f"Unreadable PDF {path.name}: {exc}")
            return
        self.metrics[f"{path.name}:pages"] = pages
        if pages == 0:
            self.error(f"PDF has no pages: {path.name}")

    def check_outputs(self) -> None:
        output_dir = self.root / "outputs"
        if not output_dir.is_dir():
            self.error("Missing outputs directory")
            return
        files = [path for path in output_dir.iterdir() if path.is_file()]
        self.metrics["output_files"] = [path.name for path in files]
        if self.final and not files:
            self.error("No final deliverables found in outputs")

        for path in files:
            if path.suffix.lower() not in ALLOWED_OUTPUT_EXTENSIONS:
                self.error(f"Unexpected file in outputs: {path.name}")
                continue
            if path.stat().st_size == 0:
                self.error(f"Empty output file: {path.name}")
                continue
            if path.suffix.lower() == ".pptx":
                self.inspect_pptx(path)
            elif path.suffix.lower() == ".docx":
                self.inspect_docx(path)
            elif path.suffix.lower() == ".pdf":
                self.inspect_pdf(path)

    def check_signoff(self) -> None:
        path = self.root / "work/06_qa/final_signoff.md"
        if not path.is_file() or not self.final:
            return
        text = path.read_text(encoding="utf-8")
        if not re.search(r"(?im)^\s*PASS\s*$", text):
            self.error("final_signoff.md does not contain a standalone PASS line")

    def run(self) -> dict[str, object]:
        self.check_required_files()
        self.check_locks()
        self.check_csv_contracts()
        self.check_json_contracts()
        self.check_outputs()
        self.check_signoff()
        return {
            "status": "PASS" if not self.errors else "FAIL",
            "final_mode": self.final,
            "project_root": str(self.root),
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--final",
        action="store_true",
        help="Enforce lock markers, completed coverage, sign-off, outputs, and closed P0/P1 defects.",
    )
    parser.add_argument(
        "--no-write-results",
        action="store_true",
        help="Do not update work/06_qa/automated_results.json.",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    result = Audit(root, args.final).run()
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    print(rendered)

    if not args.no_write_results:
        result_path = root / "work/06_qa/automated_results.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(rendered + "\n", encoding="utf-8", newline="\n")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
