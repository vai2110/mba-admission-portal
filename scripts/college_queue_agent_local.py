"""Production wrapper: enforce locked skills, management-course priority and queue control.

Generation commits are kept local until the production workflow finishes every audit.
"""

import importlib.util
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_PATH = ROOT / "scripts" / "college_queue_agent.py"
STATE_PATH = ROOT / "data" / "college-production-state.json"

spec = importlib.util.spec_from_file_location("college_queue_agent", AGENT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load college_queue_agent.py")

agent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)

ARCHITECTURE_SKILL = """
MANDATORY ARCHITECTURE SKILL: Follow the locked IIM Ahmedabad content-depth benchmark and SIBM Pune information architecture. Every generated page must be content-deep, student-intent focused, text-first, clearly navigable, mobile-first, and structured with Quick Answer, On This Page, concise keyword-focused H2s, useful tables/cards, FAQs, official-source discipline and relevant internal links. Do not invent a new information architecture.
"""

DESIGN_SKILL = """
MANDATORY DESIGN SKILL: Follow the existing college-page.css locked design system and SIBM Pune visual benchmark. Reuse the established typography, spacing, hero, navigation, cards, tables, buttons and responsive patterns. Do not invent a new frontend or redesign an individual college page.
"""


def queue_start_control():
    """Explicitly resume the queue from IIT Kanpur once, without falsely completing earlier colleges."""
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    colleges = state.setdefault("colleges", {})
    if state.get("queue_start_override") == "iit-kanpur-27":
        return

    cols = ["Overview Page", "Placement Page", "Course Page 1", "Course Page 2", "Course Page 3"]
    for rank in ("25", "26"):
        rec = colleges.setdefault(rank, {})
        rec["held"] = True
        rec["hold_reason"] = "Explicit queue start requested: resume production from IIT Kanpur (#27)."

    rec = colleges.setdefault("27", {})
    for key in cols:
        rec.pop(key, None)
    for key in ("course_plan", "course_filenames", "research_pack", "created_pages_last_run", "last_audit", "held", "hold_reason", "hold_timestamp_utc"):
        rec.pop(key, None)

    state["queue_start_override"] = "iit-kanpur-27"
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("QUEUE CONTROL: production explicitly resumed from IIT Kanpur (#27). Earlier unresolved colleges remain held, not falsely completed.")


queue_start_control()

original_gemini_json = agent.gemini_json


def management_course_priority(item):
    name = re.sub(r"[^a-z0-9]+", " ", str(item.get("name", "")).lower()).strip()
    if "executive mba" in name:
        return 2
    if re.search(r"\bmba\b", name) or "master of business administration" in name:
        return 0
    related = (
        "management", "business analytics", "analytics", "human resource", "finance",
        "marketing", "operations", "supply chain", "healthcare management",
        "pharmaceutical management", "international business", "entrepreneurship",
        "digital transformation", "pgdm", "post graduate programme in management"
    )
    if any(term in name for term in related):
        return 1
    return 99


def reorder_management_courses(result_text):
    try:
        data = json.loads(result_text)
    except Exception:
        return result_text
    if not isinstance(data, dict) or "courses" not in data:
        return result_text
    raw = [x for x in data.get("courses", []) if isinstance(x, dict) and x.get("name")]
    excluded = ("phd", "doctor of philosophy", "doctoral", "certificate", "short term", "short-term", "mdp", "fellowship")
    raw = [x for x in raw if not any(bad in str(x.get("name", "")).lower() for bad in excluded)]
    raw = sorted(raw, key=management_course_priority)
    data["courses"] = [x for x in raw if management_course_priority(x) < 99][:3]
    return json.dumps(data, ensure_ascii=False)


def enforced_gemini_json(prompt, max_output_tokens=12000):
    if "Create one production-ready HTML document" in prompt:
        prompt = ARCHITECTURE_SKILL + DESIGN_SKILL + "\n" + prompt
    result = original_gemini_json(prompt, max_output_tokens=max_output_tokens)
    if "\"courses\"" in result and "research_summary" in result:
        result = reorder_management_courses(result)
    return result


agent.gemini_json = enforced_gemini_json

original_run = agent.subprocess.run


def run_without_publish(cmd, *args, **kwargs):
    """Allow local generation commits but defer git push until all audits pass."""
    if isinstance(cmd, (list, tuple)) and list(cmd)[:2] == ["git", "push"]:
        print("QUEUE TRANSACTION: generation commit created locally; publish deferred until all audits pass.")
        return subprocess.CompletedProcess(cmd, 0)
    return original_run(cmd, *args, **kwargs)


agent.subprocess.run = run_without_publish

if __name__ == "__main__":
    agent.main()
