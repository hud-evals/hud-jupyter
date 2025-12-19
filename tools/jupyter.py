import os
from hud.tools.jupyter import JupyterTool
from config import SOLUTIONS_PATH


class JupyterToolWithRecord(JupyterTool):
    """Jupyter Tool with code recording and lazy kernel registration."""
    
    _shared_kernel_registered = False

    async def _execute(self, code: str, execution_timeout: int = 30) -> str:
        """Execute code with recording. Increased timeout for emulation."""
        # Parent class handles kernel connection
        result = await super()._execute(code, execution_timeout)
        
        # Register shared kernel after first successful execution
        if not JupyterToolWithRecord._shared_kernel_registered and self._kernel_id:
            JupyterToolWithRecord.register_shared_kernel("SpreadSheetBench", self._kernel_id)
            JupyterToolWithRecord._shared_kernel_registered = True

        # Record code if no error
        is_error = (
            "-----" in result
            or "Error" in result
            or "Traceback" in result
            or "Execution timed out" in result
        )
        if not is_error:
            with open(os.path.join(SOLUTIONS_PATH, "1_solution.py"), "a") as f:
                f.write(code)
                f.write("\n\n")

        return result
