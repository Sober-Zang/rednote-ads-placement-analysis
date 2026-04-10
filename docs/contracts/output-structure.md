# Output Contract

## Official Run Root

Every real run must live under:

- `OUTPUT_DIR/run_<timestamp>_<task-slug>/`

Default `OUTPUT_DIR`:

- `../rednote-ads-placement-analysis-output`

No other run root is considered official.
If that sibling directory already exists, it must be reused as-is. Only when it does not exist may the pipeline create it in the same sibling location. It must never be created as a hidden directory or at a higher parent level.

## Required Structure

```text
OUTPUT_DIR/
  run_<timestamp>_<task-slug>/
    aggregate/
    creators/
    inputs/
      invalid_links.md
      raw_user_input.md
    logs/
      final_broadcast.md
    manual-artifacts/
    manifests/
      link_manifest.json
      run_manifest.json
    notes/
    prompt/
      prompt_mode.json
      used_prompt.md
```

## Required Filenames

These files must exist in every official run:

- `inputs/raw_user_input.md`
- `inputs/invalid_links.md`
- `manifests/link_manifest.json`
- `manifests/run_manifest.json`
- `prompt/used_prompt.md`
- `prompt/prompt_mode.json`

## Forbidden Filenames

The following are not valid contract filenames and must not be produced as official artifacts:

- `raw_user_input.txt`
- `used_prompt.txt`
- `link_manifest.txt`
- `run_manifest.txt`

## Path Rules

- Manifest paths must be run-relative.
- Do not keep absolute workstation paths inside final run manifests.
- External URLs may stay as URLs.

## Report Rules

- `final_broadcast.md` is the official broadcast artifact.
- Standard tasks must make the assistant reply exactly match `final_broadcast.md`.
- If reports are not generated yet, `final_broadcast.md` must state that the run is still waiting for reports.
- When reports are generated, `final_broadcast.md` must show a Chinese status label and a Chinese login-state label based on the real run facts.
- The core conclusion in `final_broadcast.md` must be a 100-300 character Chinese synthesis distilled from the aggregate report's key sections, rather than a flat list or a direct copy of any single subsection.
- If a run writes spreadsheet or other manual artifacts, they must live under the same official run directory, for example `manual-artifacts/spreadsheet/...`.
- Manual artifacts must not float at the top level of `OUTPUT_DIR/`.
