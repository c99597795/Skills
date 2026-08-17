# Codex Textbook Learning Package

This bundle installs one reusable Codex Skill and three custom agents for converting textbook chapters into beginner-friendly Traditional Chinese teaching materials.

## Included

- `skills/build-textbook-learning-package/` — orchestration workflow, handoff contracts, QA gates, and deterministic helper scripts.
- `agents/textbook_lead.toml` — GPT-5.6 Sol at `xhigh` for planning, pedagogical design, image generation, and final review.
- `agents/textbook_writer.toml` — GPT-5.6 Luna at `max` for slide copy, speaker notes, translations, and worked solutions.
- `agents/textbook_production.toml` — GPT-5.6 Luna at `xhigh` for extraction, assembly, exports, rendering, and mechanical QA.
- `config.example.toml` — optional multi-agent concurrency settings.

## Install

From PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Codex\install.ps1
```

The installer copies the Skill into `%CODEX_HOME%\skills` and the agent profiles into `%CODEX_HOME%\agents`. When `CODEX_HOME` is unset, it uses the current user's `.codex` directory. It refuses to replace an existing installation unless `-Force` is supplied.

The execution-policy override applies only to this installer process; it does not change the machine's persistent PowerShell policy.

Manual installation:

```text
Codex/skills/build-textbook-learning-package -> ~/.codex/skills/build-textbook-learning-package
Codex/agents/*.toml                         -> ~/.codex/agents/
```

If needed, merge `config.example.toml` into your personal or project Codex config instead of replacing the existing config.

## Use

Invoke the Skill explicitly:

```text
Use $build-textbook-learning-package to turn this textbook chapter into a beginner-friendly Traditional Chinese PPTX/PDF and a bilingual exercise study guide.
```

The lead agent freezes the source scope, pedagogy, and visual system before delegating text work to `textbook_writer` and production work to `textbook_production`. It reviews rendered artifacts and routes defects back to the appropriate agent until the final gates pass.

## Validate a run

Initialize the standard handoff workspace:

```powershell
python .\Codex\skills\build-textbook-learning-package\scripts\init_pipeline_workspace.py <project-folder>
```

Audit the contracts and generated artifacts:

```powershell
python .\Codex\skills\build-textbook-learning-package\scripts\audit_pipeline.py <project-folder>
python .\Codex\skills\build-textbook-learning-package\scripts\audit_pipeline.py <project-folder> --final
```

The final audit checks unresolved critical defects, unexpected output files, PPTX slide/notes counts, ZIP integrity, and PDF readability when `pypdf` is available.
