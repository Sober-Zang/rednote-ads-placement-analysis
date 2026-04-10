# Execution-Only Contract

## Positioning

This repository is an execution-only pipeline repository. Treat the workspace as read-only product source by default.

## Hard Rules

| Rule | Requirement |
| --- | --- |
| Source mutability | Do not modify workspace source or docs as a side effect of a normal run. |
| Official entry | Always execute through `pipeline.py`. |
| Output location | Real run artifacts may only be written to `OUTPUT_DIR/**`. |
| Runtime location | No separate sibling runtime directory is created by default. Short-lived runtime files belong in the current run under `OUTPUT_DIR/**`. |
| Temp location | Temporary files may only be written to the current official run or to `/tmp/**`. |
| Historical reuse | Re-run the user task from scratch by default. Reuse an earlier run only if the user explicitly allows it. |
| Source edits | If a task truly requires source changes, stop and report instead of modifying code during execution. |

## Sole Write-Back Exception

There is only one allowed write-back path inside the repository:

- `xhs_user_data_dir/`

This exception exists only to maximize Xiaohongshu login-state reuse on the current device. No other runtime state, output, cache, or temporary file may be written back into the repository.

## Default External Roots

When `OUTPUT_DIR` is not explicitly provided, the pipeline must use the visible sibling directory next to the repository:

- `../rednote-ads-placement-analysis-output`

Do not fall back to hidden directories under the home directory, and do not create a separate sibling runtime directory unless the user explicitly overrides it.

## Official Sequence

1. `python pipeline.py check-env`
2. `python pipeline.py login-only` (only when the user explicitly asks to log in)
3. `python pipeline.py prepare-run --input-text "<raw task input>"`
4. `python pipeline.py crawl --run-dir <official-run-dir>`
5. `python pipeline.py finalize-broadcast --run-dir <official-run-dir>`
6. `python pipeline.py validate-contract --run-dir <official-run-dir>`

## Forbidden Behavior

- Do not invent new input or output filenames.
- Do not run ad-hoc scripts against the repo when the official entry can do the job.
- Do not write `runs/`, `browser_data/`, or other runtime state into the repository.
- Do not create ad-hoc `task_input.md` files inside the repository.
- If a temporary task file is truly needed, write it inside the current official run instead of inventing a repo-level filename.
- Do not silently continue if a run would require source edits.
