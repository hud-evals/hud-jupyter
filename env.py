"""Jupyter Environment for SpreadSheetBench.

This is a v5 SDK environment that provides:
- Jupyter kernel for Python code execution
- SpreadSheetBench evaluation scenarios
"""
import sys
import logging

from hud import Environment

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

# Create Environment instance
env = Environment(name="jupyter")

# Global tool instance (initialized lazily)
jupyter_tool = None


async def ensure_kernel_ready():
    """Ensure the Jupyter kernel is ready. Called lazily on first use."""
    global jupyter_tool
    
    if jupyter_tool is None:
        logger.warning("Jupyter tool not initialized")
        return None
    
    await jupyter_tool._ensure_kernel()
    
    from tools.jupyter import JupyterToolWithRecord
    if not JupyterToolWithRecord._shared_kernel_registered and jupyter_tool._kernel_id:
        JupyterToolWithRecord.register_shared_kernel("SpreadSheetBench", jupyter_tool._kernel_id)
        JupyterToolWithRecord._shared_kernel_registered = True
        logger.info("Jupyter kernel ready and registered for shared access")
    
    return jupyter_tool


@env.initialize
async def initialize_environment(ctx) -> None:
    """Initialize the Jupyter environment."""
    global jupyter_tool
    
    from tools.jupyter import JupyterToolWithRecord
    from hud.tools.base import BaseHub
    
    logger.info("Initializing jupyter environment")

    jupyter_tool = JupyterToolWithRecord(url_suffix="localhost:8888", kernel_name="python3")
    env.add_tool(jupyter_tool)
    
    evaluate_hub = BaseHub("evaluate")
    
    @evaluate_hub.tool("eval_all")
    async def eval_all_tool(id: str, answer_position: str, dataset_path: str = "all_data_912"):
        """Evaluate solution on all three instances (backward compatibility)."""
        await ensure_kernel_ready()
        
        from evaluate.eval_all import eval_all
        return await eval_all(id, answer_position, dataset_path)
    
    env.mount(evaluate_hub)
    
    logger.info("Jupyter environment initialized - kernel will connect on first use")


@env.shutdown
async def shutdown_environment() -> None:
    """Clean shutdown of the Jupyter environment."""
    global jupyter_tool

    from tools.jupyter import JupyterToolWithRecord
    
    if jupyter_tool and JupyterToolWithRecord._shared_kernel_registered:
        await jupyter_tool.shutdown()
        JupyterToolWithRecord._shared_kernel_registered = False
        logger.info("Jupyter kernel shut down")


from scenarios import register_scenarios
register_scenarios(env)


if __name__ == "__main__":
    env.run(transport="stdio")
