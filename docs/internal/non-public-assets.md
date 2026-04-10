# Non-Public / Internal Assets

This file lists development-only materials that should stay outside the public-facing project surface.

## Removed from the current public tree

- `browser_data/`
- repository-local `runs/`
- `.venv/`
- `.skill-control/`
- `skills/`
- root-level helper `scripts/`
- historical planning and prompt-pack directories
- machine-local cache, bytecode, and system junk

## Keep outside the public contract in future development

- donor workspaces used only for development
- internal prompt engineering notes
- internal skill authoring notes
- browser profiles and cookies
- local virtual environments
- machine-local runtime artifacts
- ad-hoc planning documents

## Rule

If a file or directory is not required to:

1. run the official execution pipeline,
2. explain the official public contract, or
3. validate the official run structure,

it should stay outside the public project surface.
