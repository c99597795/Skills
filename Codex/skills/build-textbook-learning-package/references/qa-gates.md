# QA Gates

## Contents

1. Source and content
2. Pedagogy
3. Presentation
4. Study guide
5. Cross-format consistency
6. Final packaging
7. Known recurring failures

## Source and content

- Confirm edition, chapter, PDF pages, and textbook pages.
- Trace every technical claim, figure, table, and original question to a source reference.
- Preserve complete original questions; do not use faithful abbreviations.
- Record source inconsistencies instead of silently correcting them.
- Give every in-scope exercise a translation, answer, reasoning, and reference knowledge.
- Independently recompute numerical and algorithmic examples.
- Label instructor-created examples and non-official solutions.

## Pedagogy

- State prerequisites and observable objectives.
- Teach in dependency order rather than source order.
- Include a motivating scenario, concept map, misconceptions, checks, recaps, and takeaways.
- Keep question pages free of premature answer reveals.
- Make worked examples complete from inputs through intermediate states to verification.
- Explain analogy boundaries.

## Presentation

- Keep technical diagrams editable when precision matters.
- Verify connector and arrow direction after actual PowerPoint rendering.
- Check title wrapping, page number width, footer placement, CJK fonts, and table density.
- Ensure no text or shapes exceed slide bounds.
- Require one notes slide and source block per slide.
- Inspect all rendered slides, then recheck high-density and modified slides at original size.

## Study guide

- Restart ordered steps for every exercise.
- Preserve a/b/c subitem numbering across blank lines and paragraphs.
- Prevent table rows and headings from splitting badly across pages.
- Check code blocks, equations, Unicode subscripts, and long original questions.
- Remove accidental blank pages, isolated source notes, and sparse orphan pages.
- Confirm DOCX structure and accessibility when tools support it.

## Cross-format consistency

- Export the slide PDF from the final PPTX whenever possible.
- Export the handout PDF from the final DOCX whenever possible.
- Record and validate any fallback PDF path.
- Match native and PDF page counts when layout engines should be identical.
- Compare rendered native and PDF pages or document any expected difference.
- Confirm no missing, black, duplicated, or reordered pages.

## Final packaging

- Verify PPTX and DOCX ZIP integrity.
- Verify PDF readability and page counts.
- Confirm required file names and minimum non-zero sizes.
- Keep only final deliverables in `outputs/`.
- Close all P0 and P1 defects.
- Require the lead to write PASS in `final_signoff.md`.

## Known recurring failures

These failures were observed across multiple real chapter builds and must be checked explicitly:

- Arrowheads reversed after PowerPoint export.
- Zero-width or zero-height lines rejected by the presentation engine.
- Page numbers with two digits clipped by narrow boxes.
- Titles or labels shifted or clipped only in Office/PDF rendering.
- Question slides displaying the answer too early.
- Word ordered lists continuing across exercises.
- Lettered subitems restarting after blank paragraphs.
- Tables splitting across pages and headings becoming orphaned.
- Per-exercise page breaks producing blank or sparse pages.
- Long original questions being abbreviated late in production.
- Unicode subscripts rendering as missing-glyph boxes.
- Office export stalling or failing because of environment or usage limits.
- Temporary inspection files leaking into `outputs/`.
