# Jupyter Environment

A HUD environment for evaluating spreadsheet manipulation tasks.

## 1. Deploy to Platform

To deploy this environment to [hud.ai](https://hud.ai):

1. Push this repo to GitHub
2. Go to [hud.ai](https://hud.ai) → **New** → **Environment**
3. Connect your GitHub repo
4. Push changes to trigger builds

Once deployed, your environment is accessible by its slug (e.g., `my-org/hud-jupyter`). You can then run evaluations against datasets/tasks on the platform.

## 2. Define Tools and Scenarios

Tools are functions agents can call. Scenarios define the evaluation lifecycle.

### Available Tools

This environment provides a **Jupyter kernel tool** for executing Python code (implemented by `tools/jupyter.py`). Successful code is automatically recorded to `/app/shared_data/1_solution.py`.

### Available Scenarios

| Scenario      | Description                                                                                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `spreadsheet` | The SpreadSheetBench task loop: provide an instruction + input `.xlsx`, let the agent write Python code to solve it, then evaluate on 3 instances |

## 3. Create Tasks from Scenarios

Tasks are scenario instances with specific arguments.

### In Code

```python
tasks = [
    env("spreadsheet",
        id="13-1",
        instruction="How can I combine data...",
        spreadsheet_path="/app/data/all_data_912/spreadsheet/13-1/1_13-1_input.xlsx",
        instruction_type="Sheet-Level Manipulation",
        answer_position="A3:D32",
        output_path="/app/data/all_data_912/spreadsheet/13-1/1_13-1_output.xlsx"
    ),
]
```

### From JSON

```json
[
  {
    "env": { "name": "my-org/hud-jupyter" },
    "scenario": "jupyter:spreadsheet",
    "args": {
      "id": "13-1",
      "instruction": "How can I combine data...",
      "spreadsheet_path": "/app/data/all_data_912/spreadsheet/13-1/1_13-1_input.xlsx",
      "instruction_type": "Sheet-Level Manipulation",
      "answer_position": "A3:D32",
      "output_path": "/app/data/all_data_912/spreadsheet/13-1/1_13-1_output.xlsx"
    }
  }
]
```

### On Platform

After deploying, create tasks from your scenarios on [hud.ai](https://hud.ai). Access them by slug:

```python
from hud.datasets import load_tasks
tasks = load_tasks("FRDY/SpreadSheetBench-v5")
```

### Task Arguments

- `spreadsheet_path` — path to the **input** workbook
- `output_path` — where agent should save the **modified** workbook
- `answer_position` — cell range used for scoring (compared against ground truth)

## 4. Run Evaluations

### On Platform

Run evaluations at scale directly on [hud.ai](https://hud.ai) with parallel execution and automatic tracing.

### CLI

```bash
# Evaluate a published dataset of tasks (runs on platform)
hud eval FRDY/SpreadSheetBench-v5 --remote

# Evaluate a local JSON task file (runs on platform)
hud eval ./remote_tasks.json --remote
```

### Python

```python
import hud
from hud.agents import OpenAIChatAgent  # See all models: https://hud.ai/models

async with hud.eval(tasks) as ctx:
    agent = OpenAIChatAgent.create(model="gpt-4o")  # Uses inference.hud.ai
    await agent.run(ctx)

# Results are automatically traced to hud.ai
```

### With Variants (A/B Testing)

```python
from env import env

tasks = [
    env("spreadsheet",
        id="13-1",
        instruction="How can I combine data...",
        spreadsheet_path="/app/data/all_data_912/spreadsheet/13-1/1_13-1_input.xlsx",
        instruction_type="Sheet-Level Manipulation",
        answer_position="A3:D32",
        output_path="/app/data/all_data_912/spreadsheet/13-1/1_13-1_output.xlsx"
    ),
]
variants = {"model": ["gpt-4o-mini", "gpt-4o"]}

async with hud.eval(tasks, variants=variants, group=2) as ctx:
    agent = OpenAIChatAgent.create(model=ctx.variants["model"])
    await agent.run(ctx)
```

## Configuration

### API Keys

| Variable            | When Required    | Description                                                                                                                                |
| ------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `HUD_API_KEY`       | Platform         | Your HUD API key for running evaluations on [hud.ai](https://hud.ai) and accessing models via [inference.hud.ai](https://inference.hud.ai) |
| `ANTHROPIC_API_KEY` | Local (if using) | Your Anthropic API key for Claude models                                                                                                   |
| `OPENAI_API_KEY`    | Local (if using) | Your OpenAI API key for GPT models                                                                                                         |

Get your HUD API key at [hud.ai/settings](https://hud.ai/settings).

> **Note:** When running locally (not on the platform), you only need the API key for your LLM provider (e.g., `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`). `HUD_API_KEY` is only required when running evaluations on the HUD platform or using the HUD inference gateway.

### Environment Details

- **Data path**: Dataset is pre-loaded at `/app/data/` (downloaded during Docker build)
- **Recorded solution**: Successful code is appended to `/app/shared_data/1_solution.py`
- **Kernel gateway**: Started in the container on port `8888` (see `Dockerfile.hud`)

## Local Development

Use `hud dev` with hot-reload for fast iteration:

```bash
# 1. Build the container (first time, or after Dockerfile.hud changes)
hud build

# 2. Start dev server with hot-reload
hud dev -w scenarios -w evaluate -w setup -w tools --port 8765

# 3. In another terminal, run local tests
uv run local_test.py
```

### Hot-Reload

| Component        | Reloaded?           |
| ---------------- | ------------------- |
| `scenarios/*.py` | ✅ Yes              |
| `evaluate/*.py`  | ✅ Yes (if watched) |
| `setup/*.py`     | ✅ Yes (if watched) |
| `tools/*.py`     | ✅ Yes (if watched) |
| Jupyter kernel   | ❌ No (persists)    |

**When to rebuild:** Dockerfile changes, dependency changes.

## Structure

```text
hud-jupyter/
├── env.py                  # Environment definition (v5 SDK)
├── config.py               # Paths (/app/data, /app/shared_data)
├── pyproject.toml          # Dependencies and project config
├── Dockerfile.hud          # Container definition (kernelgateway + dataset download)
├── tools/
│   ├── __init__.py
│   └── jupyter.py          # Jupyter tool wrapper that records code to 1_solution.py
├── scenarios/
│   ├── __init__.py
│   └── spreadsheet.py      # SpreadSheetBench scenario
├── evaluate/
│   ├── __init__.py
│   ├── eval_all.py         # Executes/generalizes solution across 3 instances
│   ├── compare.py          # Cell-level comparison
│   └── generalize.py       # Generalize instance-1 code to instances 2 and 3
├── setup/
│   └── __init__.py         # Setup helpers (data is pre-loaded)
├── local_test.py           # Development testing script
└── remote_tasks.json       # Sample v5-format task
```

## How Evaluation Works

1. Agent receives a spreadsheet manipulation prompt + file paths
2. Agent uses the Jupyter tool to inspect and modify the spreadsheet via Python
3. Code is recorded to `/app/shared_data/1_solution.py`
4. Evaluation runs:
   - Generalize the recorded code to instances 2 and 3
   - Execute all three solutions
   - Compare outputs to ground truth (cell-level)
   - Reward = success_rate (0–1)

## Related Links

### HuggingFace Datasets (source data)

- [FRDY/SpreadSheetBench-v5](https://hud.ai/datasets/FRDY/SpreadSheetBench-v5) — v5 format tasks for this environment

- [Genteki/SpreadSheetBench-Tiny](https://huggingface.co/datasets/Genteki/SpreadSheetBench-Tiny) (10 tasks)
- [Genteki/SpreadSheetBench-200](https://huggingface.co/datasets/Genteki/SpreadSheetBench-200) (200 tasks)
- [Genteki/SpreadSheetBench](https://huggingface.co/datasets/Genteki/SpreadSheetBench) (912 tasks)

## Documentation

Full documentation: [docs.hud.ai](https://docs.hud.ai)
