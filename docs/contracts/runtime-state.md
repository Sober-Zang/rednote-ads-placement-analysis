# Runtime Contract

## Runtime Boundary

Runtime state is not part of the repository. By default, this project no longer creates a separate sibling `RUNTIME_DIR`. Short-lived runtime files should stay inside the current run under `OUTPUT_DIR`.

## Sole Login-State Exception

To improve login-state reuse on the current device, one path is allowed to live inside the repository root:

- `xhs_user_data_dir/`

This is the only runtime directory allowed to be written back into the project. All other runtime caches, temporary state, and derived outputs must remain outside the repository or inside the current external run directory.
Do not keep or recreate a second login-state directory under `browser_data/` or any other legacy location.

## Official Runtime Layout

```text
OUTPUT_DIR/
  run_<timestamp>_<task-slug>/
    ...
    prompt/
    logs/
    manifests/
```

Long-lived login reuse lives only in `xhs_user_data_dir/`. Temporary execution files should follow the current run instead of creating a separate sibling runtime root.

## What Belongs Here

- Saved browser login state inside `xhs_user_data_dir/`
- Short-lived runtime bookkeeping inside the current external run

## What Must Not Belong Here

- Product source
- Prompt assets
- Official reports
- Human-maintained documentation

## Public Rule

Do not commit real runtime state into the repository. Public snapshots must be clean of:

- browser profiles
- cookies
- session state
- local caches
