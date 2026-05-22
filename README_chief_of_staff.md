# Chief of Staff Agent (v2 — dataclass refactor)

A Python CLI that acts as your personal Chief of Staff. Prioritises
daily tasks across **8 dimensions** with energy-aware capacity,
consistency warnings, portfolio diagnosis, and JSON export.

Built entirely on the Python standard library — no external packages,
no API keys.

## What It Does

1. Collects your available time, deadlines, meetings, and energy level.
2. For each task, collects 8 dimension scores (1–10), estimated minutes,
   strategic goal category, next action, and delegatable flag.
3. Ranks tasks using:
   ```
   weighted_score = impact*0.20 + urgency*0.15 + strategic_value*0.20
                  + compounding_effect*0.15 + goal_alignment*0.15
                  + deadline_pressure*0.10 + energy_fit*0.05
   final_score = weighted_score - opportunity_cost*0.15
   ```
4. Outputs:
   - **Today's Strategic Diagnosis**
   - **Daily Portfolio Diagnosis** (task distribution across 7 strategic goals)
   - **Top 3 Priorities** (all 8 dimension scores + warnings)
   - **Do / Delay / Delegate / Ignore** (energy-aware capacity)
   - **Consistency Warnings** (scoring anomalies)
   - **First 30 Minutes** (uses next_action if available)

## Strategic Goal Categories

| Category | Description |
|---|---|
| research_publication | Papers, experiments, literature |
| grant_funding | Proposals, budget planning |
| industry_collaboration | Partner meetings, joint projects |
| teaching_excellence | Lectures, mentoring, slides |
| public_influence | Talks, social media, CV |
| deeptech_venture | Startup planning, IP strategy |
| admin_maintenance | Email, inventory, paperwork |

## Energy-Aware DO Capacity

| Energy | DO Capacity |
|---|---|
| 1–3 | 1 task |
| 4–6 | 2 tasks |
| 7–10 | 3 tasks (2 if < 3 hours available) |

## How to Run

### Demo mode (sample data, no input)

```bash
python3 chief_of_staff_agent.py --demo
```

### Demo with JSON export

```bash
python3 chief_of_staff_agent.py --demo --json
```

### Interactive mode (your real tasks)

```bash
python3 chief_of_staff_agent.py
```

### Interactive with JSON export

```bash
python3 chief_of_staff_agent.py --json
```

### Run tests

```bash
python3 test_chief_of_staff.py
```

## How to Make It Executable

```bash
chmod +x chief_of_staff_agent.py
./chief_of_staff_agent.py --demo
```

## How to Verify It Is Working

1. Syntax check: `python3 -m py_compile chief_of_staff_agent.py`
2. Demo run: `python3 chief_of_staff_agent.py --demo`
3. Test suite: `python3 test_chief_of_staff.py` (should show `OK`)

## Customising the Scoring Model

Edit the `WEIGHTS` dict and `OPPORTUNITY_COST_WEIGHT` near the top of
`chief_of_staff_agent.py`. Weights should sum to 1.0.

## Requirements

- Python 3.7+ (uses `dataclasses` and `from __future__ import annotations`)
- Standard library only — no external packages
- No API keys needed
