"""SpreadSheetBench scenarios - spreadsheet manipulation tasks."""
import logging

logger = logging.getLogger(__name__)


def register_spreadsheet_scenarios(env) -> None:
    """Register spreadsheet scenarios with the environment."""

    @env.scenario("spreadsheet")
    async def spreadsheet(
        id: str,
        instruction: str,
        spreadsheet_path: str,
        instruction_type: str,
        answer_position: str,
        output_path: str,
    ):
        """SpreadSheetBench task: manipulate spreadsheet via Python code.
        
        The agent receives a spreadsheet manipulation task and uses the
        execute_code tool to solve it via Python code execution.
        
        Args:
            id: Task ID (e.g., "13-1")
            instruction: The spreadsheet manipulation instruction
            spreadsheet_path: Path to input spreadsheet
            instruction_type: "Cell-Level Manipulation" or "Sheet-Level Manipulation"
            answer_position: Cell range to evaluate (e.g., "A3:D32")
            output_path: Path where agent should save output spreadsheet
        
        Example task:
            {
                "scenario": "spreadsheet",
                "args": {
                    "id": "13-1",
                    "instruction": "How can I combine data from...",
                    "spreadsheet_path": "/app/data/all_data_912/spreadsheet/13-1/1_13-1_input.xlsx",
                    "instruction_type": "Sheet-Level Manipulation",
                    "answer_position": "A3:D32",
                    "output_path": "/app/data/all_data_912/spreadsheet/13-1/1_13-1_output.xlsx"
                }
            }
        """
        prompt = f"""You are a spreadsheet expert who can manipulate spreadsheets through Python code.

You need to solve the given spreadsheet manipulation question, which contains six types of information:
- instruction: The question about spreadsheet manipulation.
- spreadsheet_path: The path of the spreadsheet file you need to manipulate.
- instruction_type: There are two values (Cell-Level Manipulation, Sheet-Level Manipulation) used to indicate whether the answer to this question applies only to specific cells or to the entire worksheet.
- answer_position: The position need to be modified or filled.
- output_path: You need to generate the modified spreadsheet file in this new path.

Below is the spreadsheet manipulation question you need to solve:
### instruction
{instruction}

### spreadsheet_path
{spreadsheet_path}

### instruction_type
{instruction_type}

### answer_position
{answer_position}

### output_path
{output_path}

The solution of the question can be generate through 10 rounds of interaction and you can do two types of actions.
1. Spreadsheet information acquisition: You can generate Python code to obtain the information in the spreadsheet file. In the next turn, the execution result of you Python code will provide to you.
2. Question solution generation: You can generate Python code for the final solution of the question. If error occur when executing code, the error traceback will provide to you for code refinement.

**IMPORTANT**: PLEASE FILL THE ANSWER WITH VALUES RATHER THAN FORMULAS
"""

        import os
        from config import SOLUTIONS_PATH
        solution_file = os.path.join(SOLUTIONS_PATH, "1_solution.py")
        if os.path.exists(solution_file):
            os.remove(solution_file)
        os.makedirs(SOLUTIONS_PATH, exist_ok=True)
        
        logger.info(f"Scenario {id}: Yielding prompt to agent")
        agent_response = yield prompt
        logger.info(f"Scenario {id}: Received agent response, starting evaluation")

        from env import ensure_kernel_ready
        await ensure_kernel_ready()

        if not os.path.exists(solution_file) or os.path.getsize(solution_file) == 0:
            logger.warning(f"Scenario {id}: Solution file is missing or empty at {solution_file}")
            logger.info(f"Scenario {id}: Yielding reward 0.0 - no solution recorded")
            yield 0.0
            return

        from evaluate.eval_all import eval_all
        
        try:
            logger.info(f"Scenario {id}: Calling eval_all")
            result = await eval_all(id, answer_position)
            reward = result.get("reward", 0.0)
            
            logger.info(
                "SpreadSheetBench task %s: reward=%.2f, passed=%d/%d instances",
                id,
                reward,
                result.get("info", {}).get("total_passed", 0),
                result.get("info", {}).get("total_instances", 3),
            )
            
            if reward == 0.0:
                instance_results = result.get("info", {}).get("instance_results", {})
                for instance_key, instance_result in instance_results.items():
                    if not instance_result.get("passed", False):
                        error_msg = (
                            instance_result.get("error") or 
                            instance_result.get("execution_error") or 
                            instance_result.get("message", "Unknown error")
                        )
                        logger.warning(f"Scenario {id}: {instance_key} failed - {error_msg[:200]}")
            
            logger.info(f"Scenario {id}: Yielding reward {reward}")
            yield reward
            
        except Exception as e:
            logger.error("Evaluation failed for task %s: %s", id, e, exc_info=True)
            logger.info(f"Scenario {id}: Yielding reward 0.0 due to error")
            yield 0.0
