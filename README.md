# Jupyter Environment for SpreadSheetBench

A v5 SDK environment for evaluating spreadsheet manipulation tasks from SpreadSheetBench.

## Quick Start

### Local Development

```bash
# 1. Build the container (first time or after Dockerfile.hud changes)
hud build

# Start dev server with hot-reload
hud dev -w scenarios -w evaluate -w setup --port 8765

# 3. In another terminal, run local tests
uv run local_test.py

```

### Running on HUD Platform

```bash
hud eval Genteki/SpreadSheetBench --remote
```

## File Structure

```
hud-jupyter/
├── env.py                  # Main environment entrypoint (v5 SDK)
├── config.py               # Configuration (paths, etc.)
├── pyproject.toml          # Dependencies and project config
├── Dockerfile.hud          # Container definition
├── tools/
│   ├── __init__.py
│   └── jupyter.py          # JupyterToolWithRecord for code execution
├── scenarios/
│   ├── __init__.py
│   └── spreadsheet.py      # SpreadSheetBench scenario
├── evaluate/
│   ├── __init__.py
│   ├── eval_all.py         # Main evaluation logic (3 instances)
│   ├── compare.py          # Cell-level comparison
│   └── generalize.py       # Solution generalization
├── setup/
│   └── __init__.py         # Setup helpers (data is pre-loaded)
├── local_test.py           # Development testing script
├── remote_tasks.json       # Sample v5-format tasks
└── generate_tiny_tasks.py  # Generate tasks from dataset
```

## v5 SDK Environment Format

This environment uses the HUD v5 SDK format:

- **`env.py`**: Main entrypoint with `Environment` instance
- **`@env.initialize`**: Sets up Jupyter kernel and tools
- **`@env.scenario("spreadsheet")`**: Defines the evaluation flow
- **`env.add_tool()`**: Registers the `execute_code` tool

### Task Format (v5)

```json
{
  "env": { "name": "hud-jupyter" },
  "scenario": "spreadsheet",
  "args": {
    "id": "13-1",
    "instruction": "How can I combine data...",
    "spreadsheet_path": "/app/data/.../input.xlsx",
    "instruction_type": "Sheet-Level Manipulation",
    "answer_position": "A3:D32",
    "output_path": "/app/data/.../output.xlsx"
  }
}
```

## How Evaluation Works

1. Agent receives spreadsheet manipulation prompt
2. Agent uses `execute_code` tool to run Python code
3. Code is recorded to `1_solution.py`
4. On evaluation:
   - Code is generalized to instances 2 and 3
   - All three solutions are executed
   - Outputs are compared against ground truth
   - Reward = success_rate (0-1)

## Related Links

### HuggingFace Datasets

- [Genteki/SpreadSheetBench-Tiny](https://huggingface.co/datasets/Genteki/SpreadSheetBench-Tiny) (10 tasks)
- [Genteki/SpreadSheetBench-200](https://huggingface.co/datasets/Genteki/SpreadSheetBench-200) (200 tasks)
- [Genteki/SpreadSheetBench](https://huggingface.co/datasets/Genteki/SpreadSheetBench) (912 tasks)

### Example Traces

- [Single Test Task](https://www.hud.ai/trace/d31de170-e70a-4abb-8f95-70512515dade)
- [SpreadSheetBench-Tiny Test](https://www.hud.ai/jobs/2c426368-e352-4c79-af4a-aefb136e3f58)
