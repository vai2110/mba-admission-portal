"""Run the production agent without publishing its generation commit.

The agent's existing commit() function creates a local commit and pushes it.
For the production queue we need a transaction boundary: generate locally,
run every mandatory audit locally, then publish only after the audits pass.
This wrapper intercepts only the agent's git push call. It does not bypass any
creation, validation, research, or audit logic.
"""

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_PATH = ROOT / "scripts" / "college_queue_agent.py"

spec = importlib.util.spec_from_file_location("college_queue_agent", AGENT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load college_queue_agent.py")

agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

original_run = agent.subprocess.run


def run_without_publish(cmd, *args, **kwargs):
    """Allow the agent to commit locally but defer git push until audits pass."""
    if isinstance(cmd, (list, tuple)) and list(cmd)[:2] == ["git", "push"]:
        print("QUEUE TRANSACTION: generation commit created locally; publish deferred until all audits pass.")
        return subprocess.CompletedProcess(cmd, 0)
    return original_run(cmd, *args, **kwargs)


agent.subprocess.run = run_without_publish

if __name__ == "__main__":
    agent.main()
