# RoboRSI Installation Guide

This guide is the native host installation path. If you want Docker-based workflows, use:

- [Docker Installation](./DOCKERINSTALLATION.md)

## 1. Prerequisites

Start from a clean clone:

```bash
git clone --recursive https://github.com/nssmd/RoboRSI.git
cd RoboRSI
```

## 2. Install RoboRSI

Install the package in editable mode:

```bash
pip install -e ".[dev,web]"
```

After installation, the `roborsi` command should be available:

```bash
roborsi --help
```

Expected result:

- commands such as `manager`, `web`, `eval`, `onboard`, and `status` are listed

## 3. Initialize RoboRSI

Run:

```bash
roborsi onboard
```

This should create `~/.roborsi/config.json`, `~/.roborsi/workspace/`, and the initial workspace scaffold. You can verify it with:

```bash
find ~/.roborsi -maxdepth 4 -type f | sort
```

You should see at least:

```text
~/.roborsi/config.json
~/.roborsi/workspace/AGENTS.md
~/.roborsi/workspace/SOUL.md
~/.roborsi/workspace/TOOLS.md
~/.roborsi/workspace/USER.md
~/.roborsi/workspace/memory/MEMORY.md
```

## 4. Verify Status Output

Run:

```bash
roborsi status
```

Check that:

- `Config` is shown as `✓`
- `Workspace` is shown as `✓`
- the current `Model` looks correct
- provider status matches the actual state of your machine

## 5. Configure the Model Provider

Before launching a Manager or evaluation, make sure the model provider is
configured.

First run:

```bash
roborsi status
```

This tells you which providers are already available on the current machine.

Two common cases:

### 5.1 OAuth provider

If you are using an OAuth-based provider, log in directly.

The current codebase supports:

```bash
roborsi provider login openai-codex
roborsi provider login github-copilot
```

### 5.2 API key provider

If you are using an API-key-based provider, edit:

```bash
~/.roborsi/config.json
```

Fill in the provider key and default model there.

Common API key providers include:

- `openai`
- `anthropic`
- `openrouter`
- `deepseek`
- `gemini`
- `zhipu`
- `dashscope`
- `moonshot`
- `minimax`
- `siliconflow`
- `volcengine`
- `azureOpenai`
- `custom`
- `vllm`

Then run:

```bash
roborsi status
```

Check that:

- the current `Model` is correct
- the provider you want to use is no longer `not set`

## 6. Launch the Manager

Start the top-level orchestration session:

```bash
roborsi manager
```

Use `--backend codex`, `--backend claude`, or `--backend copilot` when you need
to select an installed coding-agent backend explicitly.

## 7. Launch the Web Dashboard

`roborsi web` serves the self-evolution dashboard (requires the `web` extra,
`pip install -e ".[web]"`):

```bash
roborsi web --host 127.0.0.1 --evo-port 8787
```

Open **http://127.0.0.1:8787**.

## 8. Configure a Real LIBERO Runtime

Install the simulator dependencies:

```bash
pip install -e ".[libero]"
```

Clone the benchmark and persist its location:

```bash
git clone --depth 1 https://github.com/Zxy-MLlab/LIBERO-PRO.git
roborsi libero configure \
  --root ./LIBERO-PRO \
  --bddldir ./LIBERO-PRO-assets/bddl_files \
  --initdir ./LIBERO-PRO-assets/init_files
```

RoboRSI writes `~/.roborsi/libero.json` and a non-interactive upstream LIBERO
`config.yaml`. The backend activates this checkout before importing
`libero.libero`, so no manual `.pth` or `PYTHONPATH` edit is needed.

Verify import, task enumeration, and one real reset:

```bash
roborsi libero doctor \
  --backend libero \
  --task libero_object/0 \
  --reset
```

Use `--initdir /path/to/regenerated/init_files` during `configure` only when a
campaign has a separate fixed init-state panel.

## 9. Run Frozen LIBERO Evaluation

One task:

```bash
roborsi eval libero_pick_place \
  --backend libero \
  --sim-task libero_object/0 \
  --seeds 5
```

Resumable short-suite task-level pass@5:

```bash
roborsi eval-suite \
  --backend libero-pro \
  --pass-at 5 \
  --workers 4 \
  --out ~/.roborsi/evals/libero-pro-pass5
```

The suite directory contains an immutable `campaign.json`, append-only
`episodes.jsonl`, and `summary.json`. Reusing `--out` resumes only when the task
panel, seed range, models, tool budget, and retry policy match exactly.
