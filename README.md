# Chief of Staff Agent — Strategic Intelligence & Execution System

**Version 10** | Python 3.12+ | Standard Library Only | No External APIs Required

A human-governed strategic autonomy system that functions as a personal Chief of Staff for researchers, PIs, founders, and knowledge workers. Tracks strategy, orchestrates execution, measures performance, and governs operations — all from the command line.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [System Design](#system-design)
   - [Version Progression](#version-progression)
   - [Data Model & Storage](#data-model--storage)
   - [Key Design Principles](#key-design-principles)
5. [Complete Command Reference](#complete-command-reference)
   - [Core Operations](#core-operations)
   - [Entity CRUD Commands](#entity-crud-commands)
   - [V6 — Strategic Intelligence](#v6--strategic-intelligence)
   - [V7 — Strategic Simulation](#v7--strategic-simulation)
   - [V8 — Execution Orchestration](#v8--execution-orchestration)
   - [V9 — Performance Measurement](#v9--performance-measurement)
   - [V10 — Governance & Autonomy](#v10--governance--autonomy)
   - [Utility Commands](#utility-commands)
6. [Data Stores](#data-stores)
7. [Workflows](#workflows)
   - [Default Workflows](#default-workflows)
   - [SOP Templates](#sop-templates)
   - [Draft Prompt Types](#draft-prompt-types)
8. [Strategic Scoring Systems](#strategic-scoring-systems)
9. [Governance Model](#governance-model)
   - [Autonomy Levels](#autonomy-levels)
   - [Policy Rules](#policy-rules)
   - [Approval Requirements](#approval-requirements)
10. [Testing](#testing)
11. [Integration Readiness](#integration-readiness)
12. [Usage Examples](#usage-examples)
13. [FAQ](#faq)
14. [Contributing](#contributing)

---

## Overview

The Chief of Staff Agent is a **closed-loop strategic operating system** that combines:

- **Strategic intelligence** — scorecards, bias detection, constraint diagnosis, leverage analysis
- **Simulation & planning** — scenario modeling, trade-off analysis, 30/90/365-day plans
- **Execution orchestration** — workflows, SOPs, playbooks, execution queue, next-action compiler
- **Performance measurement** — metrics, impact ledger, ROI, velocity, indicators, reforecasting
- **Governance** — command queue, approval system, policy rules, conflict detection, autonomy control

It replaces fragmented task managers, spreadsheets, and mental tracking with a single deterministic system.

### What This Is

- A **strategic command center** for knowledge work
- A **human-in-the-loop autonomy system** that recommends but never acts externally without approval
- A **personal data system** — all data stored locally as versioned JSON
- A **transparent reasoning tool** — every score, recommendation, and decision is explainable

### What This Is NOT

- A task manager (Todoist, Things, etc.) — it *coordinates* tasks but is not a checklist
- An AI agent that acts autonomously — it generates prompts for AI but never calls APIs
- A cloud service — everything runs locally, offline, with no telemetry

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/ph7klw76/Chief_of_staff_agent.git
cd Chief_of_staff_agent

# Run the demo
python3 chief_of_staff_agent.py --demo

# View the dashboard
python3 chief_of_staff_agent.py --dashboard

# Run the test suite
python3 -m unittest

# See all available commands
python3 chief_of_staff_agent.py --help
```

**Requirements**: Python 3.12 or later. No pip installs. No virtual environment needed. Standard library only.

---

## Architecture

```
Chief_of_staff_agent/
├── chief_of_staff_core.py          # All data models, scoring, analysis engines (3,226 lines)
├── chief_of_staff_agent.py         # CLI interface, command dispatch (2,619 lines)
├── test_chief_of_staff_agent.py    # 189 tests in 75 test classes (1,438 lines)
├── chief_of_staff_projects.json     # Project records
├── chief_of_staff_opportunities.json
├── chief_of_staff_risks.json
├── chief_of_staff_relationships.json
├── chief_of_staff_decisions.json
├── chief_of_staff_experiments.json
├── chief_of_staff_evidence.json
├── chief_of_staff_assumptions.json
├── chief_of_staff_predictions.json
├── chief_of_staff_outcomes.json
├── chief_of_staff_assets.json
├── chief_of_staff_doctrine.json
├── chief_of_staff_workflows.json
├── chief_of_staff_metrics.json
├── chief_of_staff_impact.json
├── chief_of_staff_indicators.json
├── chief_of_staff_policies.json
├── chief_of_staff_contracts.json
├── chief_of_staff_command_queue.json
├── chief_of_staff_execution_queue.json
├── chief_of_staff_captures.json
├── ... (additional store files)
└── README.md
```

**Two-module design:**

| Module | Purpose | Contents |
|---|---|---|
| `chief_of_staff_core.py` | Pure logic | 47 dataclasses, ~80 scoring/analysis functions, defaults, storage helpers |
| `chief_of_staff_agent.py` | Interface | CLI argument parsing, command dispatch, interactive modes, output formatting |

All state is stored in schema-versioned JSON files. No database, no server, no cloud.

---

## System Design

### Version Progression

The system evolved through five major versions, each adding a strategic layer:

| Version | Theme | Key Additions | Test Count |
|---|---|---|---|
| **V6** | Strategic Intelligence | Scorecard, bias detection, evidence tracking, assumptions, predictions, calibration | 68 |
| **V7** | Strategic Simulation | Scenario simulator, trade-off engine, OKRs, backcasting, operating rhythm, identity alignment | +42 (110) |
| **V8** | Execution Orchestration | Workflows, SOPs, playbooks, execution queue, knowledge graph, sprint planner, daily rituals | +27 (137) |
| **V9** | Performance Measurement | Metrics, impact ledger, ROI engine, velocity, indicators, review board, quality rubrics | +26 (163) |
| **V10** | Governance & Autonomy | Command queue, approval system, policy rules, conflict detection, initiative health, OS health | +26 (189) |

Each version is additive — no functionality is removed. All V6–V10 features are available simultaneously.

### Data Model & Storage

**Schema versioning**: Every JSON store includes a `schema_version` field. Current version: `"8.0"`. Migration functions handle V6→V7 upgrades with `.v6.bak` backups.

**Record format**: Most stores follow the pattern:
```json
{
  "schema_version": "8.0",
  "updated_at": "2026-05-22",
  "records": [
    { "entity_id": "...", "name": "...", "created_at": "...", ... }
  ]
}
```

**Resilience**: All loaders handle missing files, malformed JSON, and empty stores gracefully. No data is ever silently deleted.

### Key Design Principles

1. **Stdlib only** — zero pip dependencies, zero virtual environment, zero npm
2. **Deterministic** — all scoring formulas are explicit, transparent, and reproducible
3. **Human-in-the-loop** — recommendations are never actions; external actions require explicit approval
4. **No external APIs** — AI features are prompt-generation only; no API keys, no network calls
5. **Privacy-first** — all data stays local; redaction available for context export
6. **Additive** — each version extends the previous one; nothing is removed
7. **Offline-first** — no cloud, no sync, no telemetry

---

## Complete Command Reference

### Core Operations

| Command | Description |
|---|---|
| `--demo` | Guided interactive tour of all major features |
| `--dashboard` | Consolidated strategic dashboard |
| `--monthly-review` | Monthly strategic review with scorecard |
| `--weekly-review` | Weekly tactical review |
| `--strategy-memo [--export FILE]` | Generate and optionally export a strategy memo |
| `--project PROJECT_ID` | Detail view of a specific project |

### Entity CRUD Commands

Each entity type has list (`--plural`), add (`--add-singular`), and review (`--singular-review`) commands:

| Entity | List | Add | Review |
|---|---|---|---|
| Projects | `--projects` | `--add-project` | `--project-review` |
| Opportunities | `--opportunities` | `--add-opportunity` | `--opportunity-review` |
| Risks | `--risks` | `--add-risk` | `--risk-review` |
| Relationships | `--relationships` | `--add-relationship` | `--relationship-review` |
| Decisions | `--decisions` | `--add-decision` | `--decision-quality-review` |
| Experiments | `--experiments` | `--add-experiment` | — |
| Evidence | `--evidence` | `--add-evidence` | — |
| Assumptions | `--assumptions` | `--add-assumption` | — |
| Predictions | `--predictions` | `--add-prediction` | `--calibration-review` |
| Outcomes | `--outcomes` | `--add-outcome` | — |
| Assets | `--assets` | `--add-asset` | — |
| Doctrine | `--doctrine` | `--add-doctrine` | — |
| Principles | `--principles` | `--add-principle` | — |
| Hypotheses | `--hypotheses` | `--add-hypothesis` | — |

### V6 — Strategic Intelligence

| Command | Description |
|---|---|
| `--scorecard` | Strategic scorecard with multi-factor scoring |
| `--bias-review` | Cognitive bias detection across decisions |
| `--constraint-review` | Bottleneck and constraint diagnosis |
| `--leverage-review` | Leverage point identification |
| `--eighty-twenty-review` | 80/20 analysis — highest-leverage activities |
| `--kill-list` | Items to stop, pause, or kill |
| `--calibration-review` | Prediction calibration accuracy |
| `--decision-quality-review` | Decision quality retrospective |
| `--red-team-review` | Adversarial red-team prompt generation |
| `--board-memo` | Board-ready strategic memo prompt |

### V7 — Strategic Simulation

| Command | Description |
|---|---|
| `--simulate [--horizon N]` | Compare 8 strategic paths with multi-factor scoring |
| `--tradeoff` | Interactive 2/3-way trade-off comparison |
| `--rhythm` / `--add-rhythm` / `--rhythm-review` | Operating rhythm management |
| `--identity-review` | Behavior-vs-identity alignment detection |
| `--identities` / `--add-identity` | Strategic identity management |
| `--capital` / `--add-capital` / `--capital-review` | 9-type strategic capital tracker |
| `--plan-30` / `--plan-90` / `--plan-365` | Structured strategic plans |
| `--backcast` | Reverse-engineer outcomes into near-term actions |
| `--okrs` / `--add-okr` / `--okr-review` | OKR system with blocked KR detection |
| `--rebalance` | Portfolio allocation vs baseline comparison |
| `--integrity-check` / `--repair-integrity` | Data health check and safe repair |
| `--search QUERY` | Full-text search across all 20+ JSON stores |
| `--report-pack` | Export 5 strategic reports |
| `--ai-council` | 10-role AI council prompt (copy-paste ready) |
| `--migrate` | V6→V7 schema migration with backups |

### V8 — Execution Orchestration

| Command | Description |
|---|---|
| `--workflows` / `--add-workflow` | 9 default workflows across 8 categories |
| `--run-workflow ID` | Execute a workflow with steps and estimated time |
| `--generate-sop [--export NAME]` | 9 SOP templates, exportable to .txt |
| `--project-playbook ID [--export FILE]` | 12-section project execution architecture |
| `--queue` / `--add-to-queue` / `--queue-review` | Execution queue with priority scoring |
| `--complete-queue-item ID` | Mark queue item completed |
| `--compile-next-actions` | Scan 9 entity types for stale/missing actions |
| `--graph` / `--graph-review` | Knowledge graph: nodes, edges, dependency analysis |
| `--graph-entity ID` | Inspect entity's connections in the graph |
| `--execution-packet ID` | 10-element friction-free task start packet |
| `--draft-prompt TYPE` | 6 AI prompt types (grant, industry-email, linkedin, lecture, paper-review, venture) |
| `--prepare-meeting` | 7 meeting types with briefs, questions, and objection handling |
| `--followups` | Stale relationship + opportunity detection with optional AI prompts |
| `--sprint-plan` | Weekly theme, deep work blocks, admin containment, daily suggestions |
| `--startup` | Daily intention-setting ritual with first execution packet |
| `--shutdown` | Daily reflection + learning capture |
| `--asset-opportunities` | Identify repeated work to convert into reusable assets |
| `--capture` / `--captures` | 11-type knowledge capture (idea, insight, evidence, lesson, etc.) |
| `--context-prompt QUERY` | Assemble compact AI context from all local stores |
| `--export-context QUERY [--redact]` | Privacy-aware context export |
| `--dashboard-role ROLE` | 6 role-specific dashboards |
| `--one-page` | Compressed daily strategic overview |

### V9 — Performance Measurement

| Command | Description |
|---|---|
| `--metrics` / `--add-metric` / `--metrics-review` | Metrics registry with 11 categories |
| `--impact` / `--add-impact` / `--impact-review` | Impact ledger with 14 types and magnitude scoring |
| `--roi-review` | Strategic ROI: return − cost for all strategic investments |
| `--workflow-performance` | Completion rates, quality scores, estimation errors per workflow |
| `--estimates` / `--estimate-review` | Time/probability error tracking with correction factors |
| `--reforecast` | Update OKR/prediction confidence based on actual progress |
| `--velocity-review` | Strategic minutes/week, deep-work blocks, impact rate |
| `--indicators` / `--indicator-review` | 12 leading/lagging indicators with warnings |
| `--review-board` | 11-section executive-style strategic review |
| `--contracts` / `--add-contract` / `--contract-review` | Accountability commitments with minimum/stretch standards |
| `--adherence-review` | 7-dimension behavioral adherence score |
| `--rubrics` / `--score-output` | 9 quality rubrics with output scoring |
| `--attribution-review` | Which inputs produced which impacts |
| `--flywheel-review` | Compounding strategic loop detection |
| `--decay-review` | 7 entity types checked for strategic neglect |
| `--rebalance-optimized` | Energy/constraints-aware weekly allocation |
| `--export-csv STORE` / `--import-csv STORE` | CSV export/import for 5 stores |
| `--ai-performance-review` | 6-role performance review prompt (no API) |

### V10 — Governance & Autonomy

| Command | Description |
|---|---|
| `--commands` / `--generate-commands` | Strategic command queue with cross-subsystem generation |
| `--command-review` | Command queue review with pending/approved counts |
| `--approve-command ID` / `--reject-command ID` | Human approval for external-action commands |
| `--approvals` | Approval record listing |
| `--policies` / `--add-policy` / `--policy-review` | 10 default policies with scope/condition/action |
| `--conflict-review` | Detects project capacity, OKR competition, contract misalignment |
| `--capacity` / `--update-capacity` / `--capacity-review` | Feasibility-constrained planning |
| `--initiatives` / `--add-initiative` / `--initiative-review` | Multi-project strategic coordination |
| `--initiative ID` | Specific initiative view |
| `--governance-board [--export FILE]` | 12-section executive governance review |
| `--decision-packet ID` | Evidence-based decision support packet |
| `--command-packet ID` | Command execution packet |
| `--premortem ID` / `--postmortem ID` | Failure mode analysis and post-project learning |
| `--premortem-initiative ID` / `--postmortem-initiative ID` | Initiative-level pre/post-mortem |
| `--debt` / `--add-debt` / `--debt-review` | 10-type strategic debt tracker |
| `--complexity-audit` | Burden estimation with warning threshold |
| `--simplify` | Archive/pause/close recommendations |
| `--os-health` | 10-dimension operating system self-assessment |
| `--autonomy` / `--set-autonomy LEVEL` | 5 autonomy levels, Level 5 disabled |
| `--execute-approved` | Safe local-only command execution |
| `--ai-governance-review` | 6-role governance review prompt (no API) |

### Utility Commands

| Command | Description |
|---|---|
| `--json` | Output all results as clean JSON |
| `--export FILE` | Save text/JSON output to file |
| `--save-history` | Persist daily plan data to history |
| `--days N` | Set review window (default 7) |
| `--reflect YYYY-MM-DD` | End-of-day reflection for a specific date |
| `--redact` | Mask emails, phones, and account numbers in exports |

---

## Data Stores

The system maintains 26+ JSON stores. Each is self-contained and schema-versioned:

| Store File | Entity Type | Purpose |
|---|---|---|
| `chief_of_staff_projects.json` | Project | Research projects, grants, ventures, systems |
| `chief_of_staff_opportunities.json` | Opportunity | Grants, collaborations, conferences, ideas |
| `chief_of_staff_risks.json` | Risk | Research, grant, collaboration, overload risks |
| `chief_of_staff_relationships.json` | Relationship | Collaborators, mentors, partners, students |
| `chief_of_staff_decisions.json` | Decision | Strategic decisions with outcomes |
| `chief_of_staff_experiments.json` | Experiment | Controlled tests and MVEs |
| `chief_of_staff_evidence.json` | Evidence | Facts, data, and supporting material |
| `chief_of_staff_assumptions.json` | Assumption | Beliefs requiring validation |
| `chief_of_staff_predictions.json` | Prediction | Forecasts with calibration tracking |
| `chief_of_staff_outcomes.json` | Outcome | Desired strategic results |
| `chief_of_staff_assets.json` | Asset | Reusable templates, modules, checklists |
| `chief_of_staff_doctrine.json` | Doctrine | Personal strategic principles |
| `chief_of_staff_workflows.json` | Workflow | Repeatable execution steps |
| `chief_of_staff_execution_queue.json` | QueueItem | Prioritized execution queue |
| `chief_of_staff_metrics.json` | Metric | Quantified strategic progress |
| `chief_of_staff_impact.json` | Impact | Actual outcomes and achievements |
| `chief_of_staff_indicators.json` | Indicator | Leading and lagging indicators |
| `chief_of_staff_policies.json` | Policy | Automated recommendation rules |
| `chief_of_staff_contracts.json` | Contract | Accountability commitments |
| `chief_of_staff_command_queue.json` | Command | Governance command queue |
| `chief_of_staff_initiatives.json` | Initiative | Multi-project strategic initiatives |
| `chief_of_staff_captures.json` | Capture | Knowledge, ideas, and lessons |
| `chief_of_staff_graph.json` | Graph | Knowledge graph (auto-built) |
| `chief_of_staff_rubrics.json` | Rubric | Quality evaluation rubrics |
| `chief_of_staff_output_scores.json` | OutputScore | Scored outputs |
| `chief_of_staff_capacity.json` | Capacity | Time and attention constraints |
| `chief_of_staff_autonomy.json` | Autonomy | Autonomy level and permissions |

---

## Workflows

### Default Workflows (9)

| ID | Name | Category | Time |
|---|---|---|---|
| `wf_grant_concept` | Write one-page grant concept note | `grant_workflow` | 100 min |
| `wf_collab_pitch` | Prepare industry collaboration pitch | `industry_collaboration_workflow` | 70 min |
| `wf_manuscript` | Draft manuscript subsection | `research_workflow` | 70 min |
| `wf_paper_review` | Review research paper strategically | `research_workflow` | 45 min |
| `wf_lecture` | Prepare lecture using reusable assets | `teaching_workflow` | 55 min |
| `wf_linkedin` | Convert research insight into LinkedIn post | `public_influence_workflow` | 33 min |
| `wf_weekly_review` | Run weekly strategic review | `reflection_workflow` | 55 min |
| `wf_opp_followup` | Conduct opportunity follow-up | `admin_workflow` | 35 min |
| `wf_venture_hypothesis` | Build deep-tech venture hypothesis | `venture_workflow` | 55 min |

### SOP Templates (9)

`grant_concept_note` · `industry_outreach_email` · `research_paper_review` · `manuscript_subsection` · `lecture_preparation` · `linkedin_research_post` · `weekly_review` · `monthly_review` · `opportunity_review`

Generate with: `python3 chief_of_staff_agent.py --generate-sop --export grant_concept_note`

### Draft Prompt Types (6)

`grant` · `industry-email` · `linkedin` · `lecture` · `paper-review` · `venture`

Generate with: `python3 chief_of_staff_agent.py --draft-prompt grant`

---

## Strategic Scoring Systems

The system uses explicit, deterministic scoring formulas throughout:

### Opportunity Score
```
opp_score = alignment × 0.25 + feasibility × 0.20 + expected_value × 0.20 
          + momentum × 0.10 + relationship_value × 0.10 + evidence_strength × 0.10 
          - effort_required × 0.05
```

### Risk Score
```
risk_score = severity × 0.35 + likelihood × 0.25 + velocity × 0.15 
           + impact_radius × 0.15 - mitigation_strength × 0.10
```

### Strategic ROI
```
strategic_return = impact × 0.30 + compounding × 0.25 + relationship_value × 0.15 
                 + evidence_strength × 0.15 + future_option_value × 0.15

strategic_cost = time_cost × 0.35 + energy_cost × 0.25 + opportunity_cost × 0.25 
               + complexity_cost × 0.15

strategic_roi = strategic_return − strategic_cost
```

### Initiative Health
```
health_score = progress × 0.25 + metric_progress × 0.25 + risk_control × 0.15 
             + capacity_fit × 0.15 + relationship_support × 0.10 + momentum × 0.10
```

### Scenario Simulation
Eight paths are scored on 7 factors: alignment, compounding, opportunity capture, risk control, feasibility, energy, and an optimal allocation compared against a strategic baseline.

---

## Governance Model

### Autonomy Levels

| Level | Name | Allowed Actions |
|---|---|---|
| 0 | Record only | No recommendations, data storage only |
| 1 | Recommend | System gives recommendations |
| 2 | Prepare | Drafts, packets, prompts, and plans (default) |
| 3 | Queue for approval | Creates commands requiring human approval |
| 4 | Execute local reversible | Updates records after explicit approval |
| 5 | External action | **DISABLED in V10** — reserved for future |

### Policy Rules (10 default)

| ID | Rule | Severity |
|---|---|---|
| `p_admin_cap` | If admin > 25% of time, recommend delegation | High |
| `p_grant_protect` | If grant funding below baseline, block grant-writing sessions | High |
| `p_relationship_followup` | If high-value relationship untouched 60+ days, recommend follow-up | Medium |
| `p_project_stale` | If project has no progress 90+ days and low ROI, recommend pause/kill | Medium |
| `p_risk_mitigation` | If risk severity ≥ 8 and no mitigation, recommend immediate action | High |
| `p_outcome_reforecast` | If outcome probability < 50%, recommend reforecast | Medium |
| `p_workflow_to_sop` | If workflow used 3+ times with quality ≥ 7, recommend SOP conversion | Low |
| `p_asset_strengthen` | If asset reused 5+ times, recommend strengthening | Low |
| `p_estimation_correction` | If estimation error > 40%, recommend correction factor | Medium |
| `p_portfolio_reduce` | If active projects > capacity, recommend reduction | High |

### Approval Requirements

These command types **always require human approval** before execution:
- `prepare_email` — external communication
- `prepare_meeting` — external calendar commitment
- `follow_up` — external relationship contact
- `kill_or_pause_project` — irreversible project action

All other commands can be auto-approved if autonomy level ≥ 3.

---

## Testing

The test suite uses only `unittest`, `tempfile`, `json`, `pathlib`, `datetime`, and `re`:

```bash
# Run all tests
python3 -m unittest

# Run a specific test class
python3 -m unittest test_chief_of_staff_agent.TestV10GovernanceBoard

# Run with verbose output
python3 -m unittest -v
```

**Current test coverage**: 189 tests in 75 test classes, all passing.

Test breakdown by version:
| Version | Tests | Focus |
|---|---|---|
| V6 | 68 | Scoring, reviews, strategic intelligence |
| V7 | 42 | Simulation, OKRs, planning, migration |
| V8 | 27 | Workflows, queue, prompts, dashboards |
| V9 | 26 | Metrics, ROI, indicators, quality |
| V10 | 26 | Commands, governance, autonomy, integration |

---

## Integration Readiness

The system includes abstract provider classes and NoOp implementations for future integration:

```python
# Calendar integration (disabled)
from chief_of_staff_core import NoOpCalendarProvider
cal = NoOpCalendarProvider()
cal.create_event("Meeting")  # → {"status": "noop", "message": "Calendar integration disabled."}

# Email integration (disabled)
from chief_of_staff_core import NoOpEmailProvider
mail = NoOpEmailProvider()
mail.create_draft("Follow-up")  # → {"status": "noop", "message": "Email integration disabled."}

# Document integration (disabled)
from chief_of_staff_core import NoOpDocumentProvider
doc = NoOpDocumentProvider()
doc.create_document("Report")  # → {"status": "noop", "message": "Document integration disabled."}
```

These stubs exist so future versions can add real integrations while maintaining the same interface. The NoOp default ensures zero external contact unless explicitly configured.

---

## Usage Examples

### Daily Workflow

```bash
# Morning: start with intention
python3 chief_of_staff_agent.py --startup

# Check priorities
python3 chief_of_staff_agent.py --one-page

# Execute a workflow
python3 chief_of_staff_agent.py --run-workflow wf_grant_concept

# Log the workflow run
python3 chief_of_staff_agent.py --workflow-performance

# Evening: reflect and capture
python3 chief_of_staff_agent.py --shutdown
```

### Weekly Workflow

```bash
# Monday: Plan the sprint
python3 chief_of_staff_agent.py --sprint-plan

# Mid-week: Check for issues
python3 chief_of_staff_agent.py --compile-next-actions
python3 chief_of_staff_agent.py --followups

# Friday: Review the week
python3 chief_of_staff_agent.py --weekly-review
python3 chief_of_staff_agent.py --os-health
```

### Monthly Governance

```bash
# Start of month: Strategic review
python3 chief_of_staff_agent.py --monthly-review

# Performance audit
python3 chief_of_staff_agent.py --roi-review
python3 chief_of_staff_agent.py --velocity-review
python3 chief_of_staff_agent.py --indicator-review

# Governance
python3 chief_of_staff_agent.py --governance-board
python3 chief_of_staff_agent.py --generate-commands
python3 chief_of_staff_agent.py --command-review

# Maintenance
python3 chief_of_staff_agent.py --complexity-audit
python3 chief_of_staff_agent.py --simplify
python3 chief_of_staff_agent.py --decay-review
```

### Quarterly Strategic Review

```bash
# Simulation and planning
python3 chief_of_staff_agent.py --simulate --horizon 90
python3 chief_of_staff_agent.py --plan-90

# Deep reviews
python3 chief_of_staff_agent.py --review-board
python3 chief_of_staff_agent.py --reforecast
python3 chief_of_staff_agent.py --bias-review
python3 chief_of_staff_agent.py --flywheel-review

# Export for external review
python3 chief_of_staff_agent.py --ai-council
python3 chief_of_staff_agent.py --ai-performance-review
python3 chief_of_staff_agent.py --ai-governance-review
```

### Adding Data

```bash
# Track a new project
python3 chief_of_staff_agent.py --add-project

# Record an opportunity
python3 chief_of_staff_agent.py --add-opportunity

# Log a decision
python3 chief_of_staff_agent.py --add-decision

# Measure progress
python3 chief_of_staff_agent.py --add-metric
python3 chief_of_staff_agent.py --add-impact

# Create accountability
python3 chief_of_staff_agent.py --add-contract

# Capture learning
python3 chief_of_staff_agent.py --capture
```

### AI-Assisted Reviews (Copy-Paste Style)

```bash
# Get a strategic council prompt
python3 chief_of_staff_agent.py --ai-council

# Get a performance review prompt
python3 chief_of_staff_agent.py --ai-performance-review

# Get a governance review prompt
python3 chief_of_staff_agent.py --ai-governance-review

# Build context for a specific question
python3 chief_of_staff_agent.py --context-prompt "Should I prioritize the grant or the manuscript?"

# Export context safely (with redaction)
python3 chief_of_staff_agent.py --export-context "collaboration strategy" --redact
```

---

## FAQ

**Q: Why not use a real database?**
A: The system is designed for a single user. JSON files are portable, inspectable, version-controllable, and require zero setup. You can `cat chief_of_staff_projects.json` and read your data directly.

**Q: Can this send emails or post to social media?**
A: No. All external-action commands require explicit human approval. The integration stubs are NoOp-only. No email, calendar, or messaging APIs are called.

**Q: Does this require an AI API key?**
A: No. AI features are prompt-generation only — they produce text you can copy-paste into ChatGPT, Claude, or any AI assistant. No network calls are made.

**Q: How is this different from a task manager like Todoist?**
A: Task managers track checklists. The Chief of Staff Agent tracks strategy — it measures whether your tasks are producing the right outcomes, detects conflicts between goals, recommends what to stop doing, and evaluates whether your operating system itself is healthy.

**Q: How much time does it take to maintain?**
A: The system scales to your needs. Start with `--startup` and `--shutdown` (5 minutes/day). Add `--weekly-review` (15 minutes/week). Add `--monthly-review` and `--governance-board` (30 minutes/month). The `--complexity-audit` and `--simplify` commands help you reduce system overhead.

**Q: Can I add my own custom workflows and policies?**
A: Yes. `--add-workflow` creates custom workflows. `--add-policy` creates custom policy rules. `--add-rubric` (via code) creates custom quality rubrics. Everything is extensible.

**Q: What happens if a JSON file gets corrupted?**
A: `--integrity-check` detects corruption, broken links, duplicate IDs, and missing metadata. `--repair-integrity` fixes common issues (never deletes data). Migration functions create `.v6.bak` backups before any transformation.

**Q: Can I use this with git?**
A: Yes. All data is JSON, so it diffs cleanly. Add the store files to git for version-controlled strategic data.

---

## Contributing

This is an open-source personal tool. Contributions are welcome under the following guidelines:

1. **No external dependencies** — standard library imports only
2. **No API calls** — AI features must remain prompt-generation only
3. **Additive changes** — do not remove existing functionality
4. **Test coverage** — add tests for all new features
5. **Human-in-the-loop** — no automatic external actions
6. **Deterministic scoring** — all formulas must be transparent and documented

### Development Setup

```bash
git clone https://github.com/ph7klw76/Chief_of_staff_agent.git
cd Chief_of_staff_agent

# Make changes to chief_of_staff_core.py (logic) or chief_of_staff_agent.py (CLI)

# Run tests
python3 -m unittest

# Test your changes
python3 chief_of_staff_agent.py --demo
```

### Code Structure

- **Add new data models** in `chief_of_staff_core.py` — add dataclass, store path, load/save functions, and engine logic
- **Add CLI commands** in `chief_of_staff_agent.py` — add command function, arg definition, and dispatch
- **Add tests** in `test_chief_of_staff_agent.py` — add a test class with clear docstrings

---

Built with Python 3.12+. Standard library only. No external dependencies.

*"The Chief of Staff Agent turns strategic thinking into an operating system — not a to-do list."*
