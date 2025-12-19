"""Local test script for the Jupyter environment.

Development workflow (Docker with hot-reload):
1. Build: hud build
2. Start: hud dev -w scenarios -w evaluate -w tools --port 8765
3. Test: python local_test.py

The container runs the environment with tools/scenarios.
This script connects to it and runs agent evaluations.
"""
import asyncio
import json
import os
from pathlib import Path

import hud
from hud import Environment
from hud.agents import OpenAIChatAgent
from hud.settings import settings
from openai import AsyncOpenAI

# Use HUD inference gateway - see all models at https://hud.ai/models
client = AsyncOpenAI(base_url="https://inference.hud.ai", api_key=settings.api_key)

# Connect to running container (scenarios/tools are defined there)
DEV_URL = os.getenv("HUD_DEV_URL", "http://localhost:8765/mcp")

env = Environment("jupyter")
env.connect_url(DEV_URL)

# Load task data
def load_tasks(n: int = 10) -> list[dict]:
    """Load first N tasks from full_tasks.json."""
    tasks_file = Path(__file__).parent / "full_tasks.json"
    if not tasks_file.exists():
        print(f"Warning: {tasks_file} not found, using hardcoded tasks only")
        return []
    
    with open(tasks_file) as f:
        all_tasks = json.load(f)
    
    return all_tasks[:n]


async def test_tools_standalone():
    """Test environment tools directly."""
    print("=== Test 1: Standalone Tools ===")

    async with env:
        print(f"Tools: {[t.name for t in env.as_tools()]}")


async def test_spreadsheet_scenario():
    """Test spreadsheet scenario with manual OpenAI calls."""
    print("\n=== Test 2: Spreadsheet Scenario (Manual Agent Loop) ===")

    task = env("spreadsheet",
        id="22-12",
        instruction="I need a macro for my Excel file that updates the values in column E based on the data in columns A and D. Specifically, if column A is equal to 'USS', then for each corresponding row, check column D for the pay level; if the pay level equals 'R01', change the total in column E to 15.00, and if the pay level is any other 'R' level, assign varying amounts as follows: R01=15, R02=17, R03=23, R04=27, R05=32, R06=34. If the pay level does not match these specified 'R' levels, the total should be changed to 10.",
        spreadsheet_path="/app/data/all_data_912/spreadsheet/22-12/1_22-12_input.xlsx",
        instruction_type="Sheet-Level Manipulation",
        answer_position="E2:E19",
        output_path="/app/data/all_data_912/spreadsheet/22-12/1_22-12_output.xlsx",
    )

    async with hud.eval(task) as ctx:
        messages = [{"role": "user", "content": ctx.prompt}]

        while True:
            response = await client.chat.completions.create(
                model="claude-sonnet-4-5",  # https://hud.ai/models
                messages=messages,
                tools=ctx.as_openai_chat_tools(),
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                await ctx.submit(msg.content or "")
                break

            messages.append(msg)
            for tc in msg.tool_calls:
                result = await ctx.call_tool(tc)
                messages.append(result)
    
    reward_value = getattr(ctx, "reward", None)
    print(f"Reward: {reward_value}")


async def test_with_agent():
    """Test spreadsheet scenario with OpenAIChatAgent."""
    print("\n=== Test 3: Spreadsheet Scenario with Agent ===")

    task = env("spreadsheet",
        id="24-23",
        instruction="In my Excel spreadsheet, which has over 13,000 rows, I need to filter column A for the groups labeled '@9T', 'SAL', and 'T9A', and then delete these rows.",
        spreadsheet_path="/app/data/all_data_912/spreadsheet/24-23/1_24-23_input.xlsx",
        instruction_type="Sheet-Level Manipulation",
        answer_position="A2:D207",
        output_path="/app/data/all_data_912/spreadsheet/24-23/1_24-23_output.xlsx",
    )

    async with hud.eval(task) as ctx:
        agent = OpenAIChatAgent.create(model="gpt-4o")  # https://hud.ai/models
        await agent.run(ctx)
    
    reward_value = getattr(ctx, "reward", None)
    print(f"Reward: {reward_value}")


async def test_multiple_tasks():
    """Test multiple tasks from full_tasks.json with agent."""
    print("\n=== Test 4: Multiple Tasks (First 10 from dataset) ===")
    
    tasks_data = load_tasks(n=10)
    if not tasks_data:
        print("No tasks loaded, skipping this test")
        return
    
    print(f"Loaded {len(tasks_data)} tasks")
    results = []
    
    for i, task_data in enumerate(tasks_data, 1):
        args = task_data["args"]
        task_id = args["id"]
        
        print(f"\n[{i}/{len(tasks_data)}] Running task {task_id}...")
        
        try:
            task = env(
                "spreadsheet",
                id=args["id"],
                instruction=args["instruction"],
                spreadsheet_path=args["spreadsheet_path"],
                instruction_type=args["instruction_type"],
                answer_position=args["answer_position"],
                output_path=args["output_path"],
            )
            
            async with hud.eval(task) as ctx:
                agent = OpenAIChatAgent.create(model="gpt-4o")
                await agent.run(ctx, max_steps=10)
            
            reward = getattr(ctx, "reward", None)
            
            results.append({
                "task_id": task_id,
                "reward": reward,
                "success": True
            })
            
            print(f"[{i}/{len(tasks_data)}] ✓ Task {task_id} complete - Reward: {reward}")
        
        except Exception as e:
            print(f"[{i}/{len(tasks_data)}] ✗ Task {task_id} failed: {e}")
            results.append({
                "task_id": task_id,
                "reward": None,
                "success": False,
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    successful = sum(1 for r in results if r["success"])
    print(f"Total:      {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed:     {len(results) - successful}")
    
    rewards = [r["reward"] for r in results if r["reward"] is not None]
    if rewards:
        avg_reward = sum(rewards) / len(rewards)
        print(f"Avg Reward: {avg_reward:.3f}")
    
    return results


async def main():
    print("Jupyter Environment - Local Test")
    print("=" * 50)
    print(f"Container URL: {DEV_URL}")
    print("Make sure the container is running:")
    print("  hud dev -w scenarios -w evaluate -w tools --port 8765")
    print("=" * 50)
    print()

    await test_tools_standalone()
    # Uncomment to run scenarios:
    await test_spreadsheet_scenario()
    await test_with_agent()
    # await test_multiple_tasks()


if __name__ == "__main__":
    asyncio.run(main())
