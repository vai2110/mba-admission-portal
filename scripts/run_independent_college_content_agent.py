#!/usr/bin/env python3
"""Batch runner for the independent MBA college content agent.

Production starts after the already-completed NIRF 2025 ranks 1-26.
Existing pages remain protected by the underlying v7 agent.
"""
import independent_college_content_agent_v7 as agent

START_AFTER_RANK = 26
_original_priority_rows = agent.priority_rows


def priority_rows_after_completed_batch(rows):
    ordered = _original_priority_rows(rows)
    eligible = []
    for row in ordered:
        try:
            rank = int(str(row.get("rank", "")).strip())
        except (TypeError, ValueError):
            continue
        if rank > START_AFTER_RANK:
            eligible.append(row)
    return eligible


agent.priority_rows = priority_rows_after_completed_batch

if __name__ == "__main__":
    agent.main()
