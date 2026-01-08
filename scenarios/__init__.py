"""Jupyter environment scenarios.

Scenarios must be registered with @env.scenario() since they're Environment-specific.
"""


def register_scenarios(env):
    """Register all scenarios with the environment."""
    from scenarios.spreadsheet import register_spreadsheet_scenarios
    register_spreadsheet_scenarios(env)
