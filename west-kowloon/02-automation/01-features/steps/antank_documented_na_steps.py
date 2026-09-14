"""Step definitions for antank_documented_na.feature.

These steps are intentionally trivial — every scenario in that file is
tagged @na and so the environment.py before_scenario hook skips it before
these step bodies ever run. They exist only to make Behave's step-loader
happy.
"""
from behave import given, then  # type: ignore


@given("the case is documented in the xlsx but not executable here")
def step_documented(context):
    # Defensive: if for some reason @na was stripped and this step runs,
    # surface a clear error instead of silently passing.
    raise RuntimeError(
        "the @na before_scenario skip did not fire — "
        "this scenario is documented-only and has no executable behavior. "
        "Either re-add @na to the scenario, or move it into the appropriate "
        "antank_<flow>.feature with real step definitions."
    )


@then("the harness records it as Skipped for 1:1 traceability")
def step_recorded_skipped(context):
    # Same defensive guard as the Given step.
    raise RuntimeError(
        "the @na before_scenario skip did not fire — see the Given step above."
    )
