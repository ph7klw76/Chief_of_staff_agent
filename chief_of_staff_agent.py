#!/usr/bin/env python3
"""Chief of Staff Agent v6 — strategic intelligence & judgment improvement (stdlib only).
Usage: python3 chief_of_staff_agent.py [MODE]
Core: --demo | --dashboard | --monthly-review | --weekly-review | --strategy-memo
      --multi-agent-review | --ai-review | --antifragile-review | --scenario
V5:   --projects | --project-review | --opportunities | --opportunity-review
      --decisions | --experiments | --risks | --risk-review | --relationships
      --relationship-review | --principles
V6:   --outcomes | --evidence | --assumptions | --predictions | --calibration-review
      --decision-quality-review | --leverage-review | --constraint-review
      --eighty-twenty-review | --hypotheses | --bias-review | --scorecard
      --red-team-review | --board-memo | --kill-list | --assets | --doctrine
Other: --json | --export FILE | --save-history | --reflect YYYY-MM-DD | --days N
"""

from __future__ import annotations
import argparse, json, sys, uuid
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from collections import defaultdict
from chief_of_staff_core import *

# ======================================================================
# INPUT HELPERS
# ======================================================================
def _get_int(prompt,lo=1,hi=10):
    while True:
        try:v=int(input(prompt).strip())
        except ValueError:print(f"    !! Enter {lo}-{hi}.");continue
        if lo<=v<=hi:return v
        print(f"    !! Enter {lo}-{hi}.")
def _get_float(prompt,lo=0.5):
    while True:
        try:v=float(input(prompt).strip())
        except ValueError:print(f"    !! Enter number >={lo}.");continue
        if v>=lo:return v
        print(f"    !! Must be >={lo}.")
def _get_pos(prompt):
    while True:
        try:v=int(input(prompt).strip())
        except ValueError:print("    !! Positive integer.");continue
        if v>0:return v
        print("    !! Must be >0.")
def _get_yn(prompt):
    while True:
        r=input(prompt).strip().lower()
        if r in("y","yes"):return True
        if r in("n","no"):return False
        print("    !! y or n.")
def _get_goal():
    print("    Strategic goal categories:")
    for i,g in enumerate(STRATEGIC_GOALS,1):print(f"      {i}. {g}")
    while True:
        try:c=int(input("    -> Choose (1-7): ").strip())
        except ValueError:print("    !! 1-7.");continue
        if 1<=c<=7:return STRATEGIC_GOALS[c-1]
        print("    !! 1-7.")

# ======================================================================
# OUTPUT FORMATTERS
# ======================================================================
def _bullet(items):
    if not items:return"    (none)"
    lines=[]
    for t in items:
        tag="  [delegatable]" if t.delegatable else""
        lines.append(f"    * {t.name}{tag}")
        lines.append(f"      {t.estimated_minutes} min | goal: {t.strategic_goal} | score: {t.final_score} | spH: {t.score_per_hour}")
        for w in t.warnings:lines.append(f"      !! {w}")
        d=suggest_decomposition(t)
        if d:lines.append("      !! Too large -- decompose:");[lines.append(f"         {step}")for step in d]
    return"\n".join(lines)
def _exec_script_str(script):return"\n".join(f"    {i+1}. {s}"for i,s in enumerate(script))
def print_diagnosis(ah,am,deadlines,meetings,energy,tasks):
    print(SEP);print("  CHIEF OF STAFF v5 -- STRATEGIC DIAGNOSIS");print(SEP)
    print(f"  Available: {ah}h ({am} min) | Energy: {energy}/10 | DO cap: {do_capacity(energy)} | Tasks: {len(tasks)}")
    print(f"  Deadlines: {deadlines}");print(f"  Meetings:  {meetings}");print(SEP)
def print_portfolio(tasks,cfg=None):
    cnt,mins,avg,total=portfolio_diagnosis(tasks)
    print("\n  PORTFOLIO DIAGNOSIS");print(SEP)
    print(f"  {'Goal':<28s} {'#':>3s} {'Min':>6s} {'%Time':>6s} {'AvgScore':>8s}")
    print(f"  {'-'*28} {'-'*3} {'-'*6} {'-'*6} {'-'*8}")
    admin_pct=0;baseline=(cfg or{}).get("strategic_baseline",{})
    for g in STRATEGIC_GOALS:
        c=cnt.get(g,0);m=mins.get(g,0)
        if c==0 and m==0:continue
        pct=m/total*100;a=avg.get(g,0);bar="#"*c if c else"";bl=baseline.get(g,0);flag=""
        if bl>0:
            if pct<bl*0.5:flag=" < UNDER"
            elif pct>bl*1.5:flag=" > OVER"
        print(f"  {g:<28s} {c:>3d} {m:>6d} {pct:>5.1f}% {a:>8.2f}  {bar}{flag}")
        if g=="admin_maintenance":admin_pct=pct
    print(SEP);thresh=(cfg or{}).get("admin_time_warning_threshold",25)
    if admin_pct>thresh:print(f"  !! Admin is {admin_pct:.0f}% of planned time (>{thresh}%) -- reduce or delegate.\n"+SEP)
def print_top3(ranked):
    print("\n  TOP 3 PRIORITIES");print(SEP)
    for i,t in enumerate(ranked[:3],1):
        print(f"  {i}. {t.name}")
        print(f"       Impact:{t.impact} Urgency:{t.urgency} StratVal:{t.strategic_value} Compound:{t.compounding_effect}")
        print(f"       GoalAlign:{t.goal_alignment} Deadline:{t.deadline_pressure} EnergyFit:{t.energy_fit} OppCost:{t.opportunity_cost}")
        print(f"       EstMin:{t.estimated_minutes}  Weighted:{t.weighted_score}  Final:{t.final_score}  spH:{t.score_per_hour}  ({t.label})")
        print(f"       Goal:{t.strategic_goal}  Delegatable:{'Yes' if t.delegatable else'No'}  Project:{t.project_id or'-'}")
        if t.next_action:print(f"       Next: {t.next_action}")
        for w in t.warnings:print(f"       !! {w}")
    print(SEP)
def print_actions(do,delay,dele,ignore):
    for label,items in[("DO",do),("DELAY",delay),("DELEGATE",dele),("IGNORE",ignore)]:
        print(f"\n  {label}");print(SEP);print(_bullet(items))
def print_warnings(ranked):
    warned=[t for t in ranked if t.warnings]
    if not warned:return
    print(f"\n  CONSISTENCY WARNINGS");print(SEP)
    for t in warned:
        for w in t.warnings:print(f"  [{t.name}] {w}")
    print(SEP)
def print_overcommit(do_mins,avail,total_mins):
    print(f"\n  OVERCOMMITMENT");print(SEP)
    if do_mins>avail:print(f"  !! DO tasks: {do_mins} min vs {avail} min available (+{do_mins-avail} min).")
    if total_mins>avail*3:print(f"  !! Total: {total_mins} min = {total_mins/avail*100:.0f}% of available -- severe overplanning.")
    print(SEP)
def print_first_30(text):print(f"\n  FIRST 30 MINUTES");print(SEP);print(f"  {text}");print(SEP)
def print_execution_script(do_list):
    if not do_list:return
    script=make_execution_script(do_list[0])
    print(f'\n  EXECUTION SCRIPT -- "{do_list[0].name}"');print(SEP);print(_exec_script_str(script));print(SEP)

# ======================================================================
# PROJECTS
# ======================================================================
def load_projects():
    data = load_json(PROJECTS_PATH, [])
    return [Project(**p) for p in data] if data else []

def save_projects(projs):
    save_json(PROJECTS_PATH, [{k:v for k,v in p.__dict__.items()} for p in projs])

def add_project_interactive():
    projs = load_projects()
    print("\n  ADD PROJECT"); print("-"*40)
    p = Project(project_id=uid(), name=input("  Name: ").strip(),
                start_date=date.today().isoformat(), status="active")
    print("  Categories:"); [print(f"    {i+1}. {c}") for i,c in enumerate(PROJECT_CATEGORIES)]
    try: c=int(input("  Category (1-7): ")); p.category=PROJECT_CATEGORIES[c-1]
    except: p.category="research_project"
    print("  Strategic goals:"); [print(f"    {i+1}. {g}") for i,g in enumerate(STRATEGIC_GOALS)]
    try: c=int(input("  Goal (1-7): ")); p.strategic_goal=STRATEGIC_GOALS[c-1]
    except: pass
    p.description=input("  Description: ").strip()
    p.target_date=input("  Target date (YYYY-MM-DD): ").strip()
    p.success_criteria=input("  Success criteria: ").strip()
    p.next_milestone=input("  Next milestone: ").strip()
    p.estimated_total_hours=_get_float("  Estimated total hours: ",0.5)
    p.priority_score=_get_int("  Priority score (1-10): ")
    p.risk_level=input("  Risk level (low/medium/high): ").strip().lower() or "medium"
    projs.append(p); save_projects(projs)
    print(f"  Project '{p.name}' added. ({p.project_id})")

def list_projects():
    projs = load_projects()
    if not projs: print("  No projects. Use --add-project."); return
    print(f"\n  PROJECTS ({len(projs)})"); print(SEP)
    active = [p for p in projs if p.status=="active"]
    stagnant = [p for p in projs if p.status in("active","paused") and (not p.actual_hours_logged)]
    for p in projs:
        stag = " [STAGNANT]" if p in stagnant else ""
        print(f"  {p.project_id}  {p.name:<30s}  {p.status:<10s}  goal:{p.strategic_goal}  priority:{p.priority_score}{stag}")
    print(SEP)

def project_review():
    projs = load_projects()
    if not projs: print("  No projects."); return
    active = [p for p in projs if p.status=="active"]
    stagnant = [p for p in active if not p.actual_hours_logged]
    print(f"\n  PROJECT REVIEW"); print(SEP)
    print(f"  Total: {len(projs)} | Active: {len(active)} | Stagnant: {len(stagnant)}")
    if stagnant:
        print(f"\n  STAGNANT PROJECTS (no hours logged):")
        for p in stagnant: print(f"    - {p.name} ({p.project_id}) — {p.next_milestone or'no milestone'}")
    print(f"\n  BY CATEGORY:")
    for cat in PROJECT_CATEGORIES:
        ps=[p for p in projs if p.category==cat]
        if ps: print(f"    {cat}: {len(ps)} project(s)")
    print(SEP)

def project_detail(pid):
    projs = load_projects()
    for p in projs:
        if p.project_id==pid:
            print(f"\n  PROJECT: {p.name}"); print(SEP)
            for k,v in p.__dict__.items(): print(f"  {k}: {v}")
            print(SEP); return
    print(f"  Project '{pid}' not found.")

# ======================================================================
# OPPORTUNITIES
# ======================================================================
def load_opps():
    data = load_json(OPPORTUNITIES_PATH, [])
    return [Opportunity(**o) for o in data] if data else []

def save_opps(opps):
    save_json(OPPORTUNITIES_PATH, [{k:v for k,v in o.__dict__.items()} for o in opps])

def add_opportunity_interactive():
    opps = load_opps()
    print("\n  ADD OPPORTUNITY"); print("-"*40)
    o = Opportunity(opportunity_id=uid(), name=input("  Name: ").strip(), created_date=date.today().isoformat(), last_touched_date=date.today().isoformat())
    print("  Types:"); [print(f"    {i+1}. {t}") for i,t in enumerate(OPPORTUNITY_TYPES)]
    try: c=int(input("  Type (1-9): ")); o.type=OPPORTUNITY_TYPES[c-1]
    except: o.type="grant"
    o.description=input("  Description: ").strip()
    o.potential_value=_get_int("  Potential value (1-10): "); o.probability=_get_int("  Probability (1-10): ")
    o.urgency=_get_int("  Urgency (1-10): "); o.relationship_value=_get_int("  Relationship value (1-10): ")
    o.effort_required=_get_int("  Effort required (1-10): ")
    o.next_action=input("  Next action: ").strip(); o.status="open"
    o.source=input("  Source: ").strip()
    o.score=opp_score(o)
    opps.append(o); save_opps(opps)
    print(f"  Opportunity '{o.name}' added. Score: {o.score}")

def list_opps():
    opps=sorted(load_opps(),key=lambda o:opp_score(o),reverse=True)
    if not opps: print("  No opportunities."); return
    print(f"\n  OPPORTUNITIES ({len(opps)})"); print(SEP)
    for o in opps:
        s=opp_score(o); stale=(date.today()-date.fromisoformat(o.last_touched_date)).days if o.last_touched_date else 0
        stag=" [STALE >14d]" if stale>14 and o.status=="open" else""
        print(f"  {o.opportunity_id}  {o.name:<30s}  type:{o.type}  score:{s}  status:{o.status}{stag}")
    print(SEP)

def opportunity_review():
    opps = load_opps()
    if not opps: print("  No opportunities."); return
    scored=sorted(opps,key=lambda o:opp_score(o),reverse=True)
    stale=[o for o in opps if o.status=="open" and (date.today()-date.fromisoformat(o.last_touched_date)).days>14]
    print(f"\n  OPPORTUNITY REVIEW"); print(SEP)
    print(f"  Total: {len(opps)} | Open: {len([o for o in opps if o.status=='open'])} | Stale (>14d): {len(stale)}")
    if stale:
        print("\n  STALE (needs follow-up):")
        for o in stale: print(f"    - {o.name} ({o.opportunity_id}) score:{opp_score(o)} — {o.next_action or'no next action'}")
    print(f"\n  TOP 5 BY SCORE:")
    for o in scored[:5]: print(f"    {o.name}: {opp_score(o)} ({o.type})")
    print(SEP)

# ======================================================================
# DECISIONS, EXPERIMENTS, RISKS, RELATIONSHIPS, PRINCIPLES
# ======================================================================
def load_decisions():
    data=load_json(DECISIONS_PATH,[]); return [Decision(**d)for d in data]if data else[]
def save_decisions(ds): save_json(DECISIONS_PATH,[d.__dict__ for d in ds])

def add_decision_interactive():
    ds=load_decisions()
    d=Decision(decision_id=uid(),date=date.today().isoformat(),title=input("  Title: ").strip(),context=input("  Context: ").strip())
    print("  Enter options (blank to finish):")
    while True:
        opt=input("    Option: ").strip()
        if not opt:break
        d.options.append(opt)
    d.chosen_option=input("  Chosen option: ").strip()
    d.rationale=input("  Rationale: ").strip();d.expected_outcome=input("  Expected outcome: ").strip()
    d.review_date=(date.today()+timedelta(days=30)).isoformat()
    ds.append(d);save_decisions(ds);print(f"  Decision recorded. Review by {d.review_date}")

def list_decisions():
    ds=load_decisions()
    if not ds:print("  No decisions.");return
    print(f"\n  DECISIONS ({len(ds)})");print(SEP)
    for d in ds:print(f"  {d.decision_id}  {d.date}  {d.title:<30s}  choice:{d.chosen_option}")
    print(SEP)

def load_experiments():
    data=load_json(EXPERIMENTS_PATH,[]);return[Experiment(**e)for e in data]if data else[]
def save_experiments(es):save_json(EXPERIMENTS_PATH,[e.__dict__ for e in es])

def add_experiment_interactive():
    es=load_experiments()
    e=Experiment(experiment_id=uid(),title=input("  Title: ").strip(),hypothesis=input("  Hypothesis: ").strip(),start_date=date.today().isoformat())
    e.end_date=(date.today()+timedelta(days=7)).isoformat();e.strategic_goal=input("  Strategic goal: ").strip()
    e.success_metric=input("  Success metric: ").strip();e.expected_result=input("  Expected result: ").strip()
    es.append(e);save_experiments(es);print(f"  Experiment '{e.title}' added.")

def list_experiments():
    es=load_experiments()
    if not es:print("  No experiments.");return
    print(f"\n  EXPERIMENTS ({len(es)})");print(SEP)
    for e in es:print(f"  {e.experiment_id}  {e.title:<30s}  status:{e.status}  goal:{e.strategic_goal}")
    print(SEP)

def load_risks():
    data=load_json(RISKS_PATH,[]);return[Risk(**r)for r in data]if data else[]
def save_risks(rs):save_json(RISKS_PATH,[r.__dict__ for r in rs])

def add_risk_interactive():
    rs=load_risks()
    r=Risk(risk_id=uid(),title=input("  Title: ").strip())
    print("  Categories:");[print(f"    {i+1}. {c}")for i,c in enumerate(RISK_CATEGORIES)]
    try:c=int(input("  Category (1-9): "));r.category=RISK_CATEGORIES[c-1]
    except:r.category="execution_drift"
    r.probability=_get_int("  Probability (1-10): ");r.severity=_get_int("  Severity (1-10): ")
    r.detectability=_get_int("  Detectability (1-10): ");r.mitigation=input("  Mitigation: ").strip()
    r.owner=input("  Owner: ").strip()or"self";r.score=risk_score(r)
    rs.append(r);save_risks(rs);print(f"  Risk '{r.title}' added. Score: {r.score}")

def list_risks():
    rs=sorted(load_risks(),key=lambda r:risk_score(r),reverse=True)
    if not rs:print("  No risks.");return
    print(f"\n  RISKS ({len(rs)})");print(SEP)
    for r in rs:print(f"  {r.risk_id}  {r.title:<30s}  cat:{r.category}  score:{risk_score(r)}  status:{r.status}")
    print(SEP)

def risk_review():
    rs=load_risks()
    if not rs:print("  No risks.");return
    top=sorted(rs,key=lambda r:risk_score(r),reverse=True)[:3]
    no_mit=[r for r in rs if r.status=="active" and not r.mitigation]
    print(f"\n  RISK REVIEW");print(SEP)
    print(f"  Total: {len(rs)} | Active: {len([r for r in rs if r.status=='active'])} | No mitigation: {len(no_mit)}")
    print(f"\n  TOP 3 RISKS:")
    for r in top:print(f"    {r.title} (score:{risk_score(r)}) — {r.mitigation or'NO MITIGATION'}")
    print(SEP)

def load_relationships():
    data=load_json(RELATIONSHIPS_PATH,[]);return[Relationship(**r)for r in data]if data else[]
def save_relationships(rs):save_json(RELATIONSHIPS_PATH,[r.__dict__ for r in rs])

def add_relationship_interactive():
    rs=load_relationships()
    r=Relationship(relationship_id=uid(),name=input("  Name: ").strip(),organization=input("  Organization: ").strip())
    print("  Types:");[print(f"    {i+1}. {t}")for i,t in enumerate(RELATIONSHIP_TYPES)]
    try:c=int(input("  Type (1-8): "));r.relationship_type=RELATIONSHIP_TYPES[c-1]
    except:r.relationship_type="research_collaborator"
    r.strategic_goal=input("  Strategic goal: ").strip()
    r.last_contact_date=input("  Last contact (YYYY-MM-DD): ").strip()
    r.next_contact_action=input("  Next contact action: ").strip()
    r.value_to_them=input("  Value to them: ").strip();r.value_to_user=input("  Value to you: ").strip()
    rs.append(r);save_relationships(rs);print(f"  Relationship '{r.name}' added.")

def list_relationships():
    rs=load_relationships()
    if not rs:print("  No relationships.");return
    print(f"\n  RELATIONSHIPS ({len(rs)})");print(SEP)
    for r in rs:
        days=999
        if r.last_contact_date:
            try:days=(date.today()-date.fromisoformat(r.last_contact_date)).days
            except:pass
        stag=" [NO CONTACT >60d]" if days>60 else""
        print(f"  {r.relationship_id}  {r.name:<25s}  {r.relationship_type:<20s}  last:{r.last_contact_date or'?'}{stag}")
    print(SEP)

def relationship_review():
    rs=load_relationships()
    if not rs:print("  No relationships.");return
    stale=[r for r in rs if r.last_contact_date and (date.today()-date.fromisoformat(r.last_contact_date)).days>60]
    no_next=[r for r in rs if not r.next_contact_action]
    print(f"\n  RELATIONSHIP REVIEW");print(SEP)
    print(f"  Total: {len(rs)} | Stale (>60d): {len(stale)} | No next action: {len(no_next)}")
    if stale:
        print("\n  NEEDS FOLLOW-UP (>60d):")
        for r in stale:print(f"    - {r.name} ({r.organization})")
    print(SEP)

def load_principles():
    data=load_json(PRINCIPLES_PATH,[]);return[Principle(**p)for p in data]if data else[]
def save_principles(ps):save_json(PRINCIPLES_PATH,[p.__dict__ for p in ps])

def add_principle_interactive():
    ps=load_principles()
    p=Principle(principle_id=uid(),title=input("  Title: ").strip(),statement=input("  Statement: ").strip(),evidence=input("  Evidence: ").strip(),date_created=date.today().isoformat(),last_reviewed=date.today().isoformat())
    ps.append(p);save_principles(ps);print(f"  Principle '{p.title}' added.")

def list_principles():
    ps=load_principles()
    if not ps:print("  No principles.");return
    print(f"\n  OPERATING PRINCIPLES ({len(ps)})");print(SEP)
    for p in ps:print(f"  {p.principle_id}  {p.title}: {p.statement}")
    print(SEP)

# ======================================================================
# V6 — OUTCOMES
# ======================================================================
def load_outcomes():
    data=load_records(OUTCOMES_PATH);return[Outcome(**o)for o in data]if data else[]
def save_outcomes(os):save_records(OUTCOMES_PATH,[o.__dict__ for o in os])

def add_outcome_interactive():
    os=load_outcomes()
    print("\n  ADD STRATEGIC OUTCOME");print("-"*40)
    o=Outcome(outcome_id=uid(),name=input("  Name: ").strip(),description=input("  Description: ").strip())
    print("  Time horizons:");[print(f"    {i+1}. {h}")for i,h in enumerate(TIME_HORIZONS)]
    try:c=int(input("  Horizon (1-5): "));o.time_horizon=TIME_HORIZONS[c-1]
    except:o.time_horizon="1_year"
    print("  Strategic goals:");[print(f"    {i+1}. {g}")for i,g in enumerate(STRATEGIC_GOALS)]
    try:c=int(input("  Goal (1-7): "));o.strategic_goal=STRATEGIC_GOALS[c-1]
    except:pass
    o.success_metric=input("  Success metric: ").strip()
    o.current_status=input("  Current status: ").strip();o.desired_status=input("  Desired status: ").strip()
    o.confidence_level=_get_int("  Confidence level (1-10): ");o.importance=_get_int("  Importance (1-10): ")
    os.append(o);save_outcomes(os);print(f"  Outcome '{o.name}' added. ({o.outcome_id})")

def list_outcomes():
    os=load_outcomes()
    if not os:print("  No outcomes. Use --add-outcome.");return
    print(f"\n  STRATEGIC OUTCOMES ({len(os)})");print(SEP)
    for o in os:
        gap="→" if o.current_status!=o.desired_status else "="
        print(f"  {o.outcome_id}  {o.name:<30s}  {o.current_status} {gap} {o.desired_status}  confidence:{o.confidence_level}  importance:{o.importance}")
    print(SEP)

# ======================================================================
# V6 — EVIDENCE
# ======================================================================
def load_evidence():
    data=load_records(EVIDENCE_PATH);return[Evidence(**e)for e in data]if data else[]
def save_evidence(es):save_records(EVIDENCE_PATH,[e.__dict__ for e in es])

def add_evidence_interactive():
    es=load_evidence()
    print("\n  ADD EVIDENCE");print("-"*40)
    e=Evidence(evidence_id=uid(),date=today_str(),title=input("  Title: ").strip())
    print("  Types:");[print(f"    {i+1}. {t}")for i,t in enumerate(EVIDENCE_TYPES)]
    try:c=int(input("  Type (1-{0}): ".format(len(EVIDENCE_TYPES))));e.evidence_type=EVIDENCE_TYPES[c-1]
    except:e.evidence_type="observation"
    e.related_goal=input("  Related goal: ").strip();e.claim_supported=input("  Claim supported: ").strip()
    e.claim_weakened=input("  Claim weakened: ").strip()
    e.strength=_get_int("  Evidence strength (1-10): ");e.reliability=_get_int("  Source reliability (1-10): ")
    e.notes=input("  Notes: ").strip()
    es.append(e);save_evidence(es);print(f"  Evidence '{e.title}' added.")

def list_evidence():
    es=load_evidence()
    if not es:print("  No evidence. Use --add-evidence.");return
    print(f"\n  EVIDENCE ({len(es)})");print(SEP)
    for e in es:print(f"  {e.evidence_id}  {e.date}  {e.title:<30s}  type:{e.evidence_type}  strength:{e.strength}  reliability:{e.reliability}")
    print(SEP)

# ======================================================================
# V6 — ASSUMPTIONS
# ======================================================================
def load_assumptions():
    data=load_records(ASSUMPTIONS_PATH);return[Assumption(**a)for a in data]if data else[]
def save_assumptions(ass):save_records(ASSUMPTIONS_PATH,[a.__dict__ for a in ass])

def add_assumption_interactive():
    ass=load_assumptions()
    print("\n  ADD ASSUMPTION");print("-"*40)
    a=Assumption(assumption_id=uid(),statement=input("  Statement: ").strip(),last_reviewed=today_str())
    print("  Categories:");[print(f"    {i+1}. {c}")for i,c in enumerate(ASSUMPTION_CATEGORIES)]
    try:c=int(input("  Category (1-{0}): ".format(len(ASSUMPTION_CATEGORIES))));a.category=ASSUMPTION_CATEGORIES[c-1]
    except:a.category="research"
    a.confidence=_get_int("  Confidence (1-10): ");a.importance=_get_int("  Importance (1-10): ")
    a.what_would_change_my_mind=input("  What would change your mind? ").strip()
    ass.append(a);save_assumptions(ass);print(f"  Assumption added. ({a.assumption_id})")

def list_assumptions():
    ass=load_assumptions()
    if not ass:print("  No assumptions. Use --add-assumption.");return
    print(f"\n  ASSUMPTIONS ({len(ass)})");print(SEP)
    for a in ass:print(f"  {a.assumption_id}  {a.statement:<50s}  cat:{a.category}  conf:{a.confidence}  imp:{a.importance}  status:{a.status}")
    print(SEP)

# ======================================================================
# V6 — PREDICTIONS
# ======================================================================
def load_predictions():
    data=load_records(PREDICTIONS_PATH);return[Prediction(**p)for p in data]if data else[]
def save_predictions(ps):save_records(PREDICTIONS_PATH,[p.__dict__ for p in ps])

def add_prediction_interactive():
    ps=load_predictions()
    print("\n  ADD PREDICTION");print("-"*40)
    p=Prediction(prediction_id=uid(),date_created=today_str(),prediction_statement=input("  Prediction statement: ").strip())
    print("  Categories (uses assumption categories):");[print(f"    {i+1}. {c}")for i,c in enumerate(ASSUMPTION_CATEGORIES)]
    try:c=int(input("  Category (1-{0}): ".format(len(ASSUMPTION_CATEGORIES))));p.category=ASSUMPTION_CATEGORIES[c-1]
    except:p.category="research"
    p.probability=_get_int("  Your probability estimate (%): ",1,99)
    p.expected_resolution_date=input("  Expected resolution date (YYYY-MM-DD): ").strip()
    ps.append(p);save_predictions(ps);print(f"  Prediction added. ({p.prediction_id})")

def list_predictions():
    ps=load_predictions()
    if not ps:print("  No predictions. Use --add-prediction.");return
    print(f"\n  PREDICTIONS ({len(ps)})");print(SEP)
    for p in ps:
        res="✓" if p.resolved else("?" if not p.expected_resolution_date or p.expected_resolution_date>=today_str() else"⏰")
        print(f"  {p.prediction_id}  {res}  {p.prediction_statement:<50s}  prob:{p.probability}%  cat:{p.category}  resolved:{'yes' if p.resolved else'no'}")
    print(SEP)

def resolve_prediction_interactive():
    ps=load_predictions()
    unresolved=[p for p in ps if not p.resolved]
    if not unresolved:print("  No unresolved predictions.");return
    print("\n  RESOLVE PREDICTION");print("-"*40)
    for i,p in enumerate(unresolved,1):print(f"  {i}. {p.prediction_statement} (prob:{p.probability}%)")
    try:
        c=int(input("  -> Choose: ").strip())
        if 1<=c<=len(unresolved):
            p=unresolved[c-1];ans=input(f"  Did it happen? (y/n): ").strip().lower()
            p.actual_outcome=ans in("y","yes");p.resolved=True
            p.lesson=input("  Lesson: ").strip()
            bs=(p.probability/100-(1 if p.actual_outcome else 0))**2;p.brier_score=round(bs,3)
            save_predictions(ps);print(f"  Resolved. Brier score: {p.brier_score:.3f}")
    except (ValueError,IndexError):print("  Invalid choice.")

# ======================================================================
# V6 — HYPOTHESES
# ======================================================================
def load_hypotheses():
    data=load_records(HYPOTHESES_PATH);return[Hypothesis(**h)for h in data]if data else[]
def save_hypotheses(hs):save_records(HYPOTHESES_PATH,[h.__dict__ for h in hs])

def add_hypothesis_interactive():
    hs=load_hypotheses()
    print("\n  ADD STRATEGIC HYPOTHESIS");print("-"*40)
    h=Hypothesis(hypothesis_id=uid(),statement=input("  Hypothesis: ").strip())
    print("  Strategic goals:");[print(f"    {i+1}. {g}")for i,g in enumerate(STRATEGIC_GOALS)]
    try:c=int(input("  Goal (1-7): "));h.strategic_goal=STRATEGIC_GOALS[c-1]
    except:pass
    h.confidence_before=_get_int("  Confidence before testing (1-10): ");h.status="untested"
    h.next_test=input("  Next test: ").strip()
    hs.append(h);save_hypotheses(hs);print(f"  Hypothesis added. ({h.hypothesis_id})")

def list_hypotheses():
    hs=load_hypotheses()
    if not hs:print("  No hypotheses. Use --add-hypothesis.");return
    print(f"\n  STRATEGIC HYPOTHESES ({len(hs)})");print(SEP)
    for h in hs:
        conf=f"conf:{h.confidence_before}→{h.confidence_after}" if h.status!="untested" else f"conf:{h.confidence_before}"
        print(f"  {h.hypothesis_id}  {h.statement:<50s}  goal:{h.strategic_goal}  status:{h.status}  {conf}")
    print(SEP)

# ======================================================================
# V6 — ASSETS
# ======================================================================
def load_assets():
    data=load_records(ASSETS_PATH);return[Asset(**a)for a in data]if data else[]
def save_assets(ass):save_records(ASSETS_PATH,[a.__dict__ for a in ass])

def add_asset_interactive():
    ass=load_assets()
    print("\n  ADD COMPOUNDING ASSET");print("-"*40)
    a=Asset(asset_id=uid(),name=input("  Name: ").strip(),created_date=today_str())
    print("  Types:");[print(f"    {i+1}. {t}")for i,t in enumerate(ASSET_TYPES)]
    try:c=int(input("  Type (1-{0}): ".format(len(ASSET_TYPES))));a.asset_type=ASSET_TYPES[c-1]
    except:a.asset_type="proposal_template"
    print("  Strategic goals:");[print(f"    {i+1}. {g}")for i,g in enumerate(STRATEGIC_GOALS)]
    try:c=int(input("  Goal (1-7): "));a.strategic_goal=STRATEGIC_GOALS[c-1]
    except:pass
    a.description=input("  Description: ").strip();a.reuse_count=_get_int("  Reuse count: ",0,1000)
    a.estimated_future_value=_get_int("  Estimated future value (1-10): ")
    a.maintenance_required=input("  Maintenance required (low/medium/high): ").strip().lower()or"low"
    a.notes=input("  Notes: ").strip()
    ass.append(a);save_assets(ass);print(f"  Asset '{a.name}' added.")

def list_assets():
    ass=load_assets()
    if not ass:print("  No assets. Use --add-asset.");return
    print(f"\n  COMPOUNDING ASSETS ({len(ass)})");print(SEP)
    for a in ass:print(f"  {a.asset_id}  {a.name:<30s}  type:{a.asset_type}  reuse:{a.reuse_count}x  future_val:{a.estimated_future_value}  maint:{a.maintenance_required}")
    print(SEP)

# ======================================================================
# V6 — DOCTRINE
# ======================================================================
def load_doctrine():
    data=load_records(DOCTRINE_PATH);return[Doctrine(**d)for d in data]if data else[]
def save_doctrine(ds):save_records(DOCTRINE_PATH,[d.__dict__ for d in ds])

def add_doctrine_interactive():
    ds=load_doctrine()
    print("\n  ADD PERSONAL DOCTRINE");print("-"*40)
    d=Doctrine(doctrine_id=uid(),principle=input("  Principle: ").strip(),rationale=input("  Rationale: ").strip(),evidence=input("  Evidence: ").strip(),last_reviewed=today_str())
    print("  Related biases:");[print(f"    {i+1}. {b}")for i,b in enumerate(BIAS_TYPES)]
    try:c=int(input("  Related bias (0 to skip): "));d.related_bias=BIAS_TYPES[c-1]if 1<=c<=len(BIAS_TYPES)else""
    except:d.related_bias=""
    ds.append(d);save_doctrine(ds);print(f"  Doctrine '{d.principle[:40]}' added.")

def list_doctrine():
    ds=load_doctrine()
    if not ds:print("  No doctrine entries. Use --add-doctrine.");return
    print(f"\n  PERSONAL STRATEGY DOCTRINE ({len(ds)})");print(SEP)
    for d in ds:
        bias=f" [{d.related_bias}]" if d.related_bias else""
        print(f"  {d.doctrine_id}  {d.principle:<50s}{bias}")
        print(f"       Rationale: {d.rationale[:80]}")
    print(SEP)

# ======================================================================
# V6 — REVIEWS
# ======================================================================
def calibration_review_cmd():
    ps=load_predictions();r=calibration_review(ps)
    print(f"\n  CALIBRATION REVIEW");print(SEP)
    print(f"  Predictions: {r['total_predictions']} | Resolved: {r['resolved']}")
    if r.get("avg_brier_score") is not None:
        print(f"  Avg Brier Score: {r['avg_brier_score']:.3f} ({r['brier_grade']})")
        print(f"  Overconfident: {r['overconfident_count']} | Well-calibrated: {r['well_calibrated_count']}")
        if r.get("bin_stats"):
            print(f"\n  CALIBRATION BY PROBABILITY BIN:");print(f"  {'Bin':<12s} {'Count':>6s} {'Actual%':>8s} {'Expected':>8s} {'Drift':>8s}")
            for bin_name, stats in r["bin_stats"].items():
                print(f"  {bin_name:<12s} {stats['count']:>6d} {stats['actual_true_pct']:>7.1f}% {stats['expected_mid']:>7.0f}% {stats['drift']:>+7.1f}%")
        if r.get("overconfident"):
            print(f"\n  OVERCONFIDENT PREDICTIONS:");[print(f"    - {s}")for s in r["overconfident"]]
    print(f"  {r.get('message','')}{r.get('recommendation','')}");print(SEP)

def decision_quality_review_cmd():
    ds=load_decisions();r=decision_quality_review(ds)
    print(f"\n  DECISION QUALITY REVIEW");print(SEP)
    if r.get("message"):print(f"  {r['message']}");print(SEP);return
    print(f"  Decisions: {r['total_decisions']} | Reviewed: {r['reviewed_count']}")
    print(f"  Avg Quality Score: {r['avg_quality_score']} ({r['quality_grade']})")
    if r.get("weakest_dimensions"):
        print(f"\n  WEAKEST DIMENSIONS:");[print(f"    - {dim}: {count} decision(s) scored <=3")for dim,count in r["weakest_dimensions"]]
    if r.get("overdue_review",0)>0:
        print(f"\n  OVERDUE REVIEW ({r['overdue_review']}):");[print(f"    - {t}")for t in r["overdue_titles"]]
    print(SEP)

def leverage_review_cmd():
    tasks=[];result=demo(to_json=True)
    if result: tasks=[Task(**t)for t in result.get("ranked",[])]
    ass=load_assets();os=load_outcomes();r=leverage_analysis(tasks,os,ass)
    print(f"\n  LEVERAGE ANALYSIS");print(SEP)
    print(f"  {r['summary']}")
    if r.get("high_leverage_tasks"):
        print(f"\n  HIGHEST LEVERAGE TASKS:");print(f"  {'Task':<35s} {'Score':>6s} {'Hours':>6s} {'Pts/Hr':>8s} {'Goal'}")
        print(f"  {'-'*35} {'-'*6} {'-'*6} {'-'*8} {'-'*20}")
        for t in r["high_leverage_tasks"]:print(f"  {t['name']:<35s} {t['score']:>6.2f} {t['est_hours']:>6.1f} {t['leverage_ratio']:>8.2f} {t['goal']}")
    if r.get("compounding_assets"):
        print(f"\n  COMPOUNDING ASSETS:");[print(f"    - {a['name']} ({a['type']}): {a['reuse_count']}x reuse, future val:{a['future_value']}")for a in r["compounding_assets"]]
    print(SEP)

def constraint_review_cmd():
    tasks=[];result=demo(to_json=True)
    if result: tasks=[Task(**t)for t in result.get("ranked",[])]
    rs=load_risks();os=load_outcomes();r=constraint_diagnosis(tasks,rs,os)
    print(f"\n  CONSTRAINT DIAGNOSIS");print(SEP)
    if r["constraints"]:
        print(f"  Detected {len(r['constraints'])} constraint(s):")
        for c in r["constraints"]:
            if c["type"]=="risk":print(f"    - RISK: {c['name']} (severity:{c['severity']}, mitigated:{c['mitigation']})")
            elif c["type"]=="outcome_uncertainty":print(f"    - UNCERTAINTY: {c['name']} (confidence:{c['confidence']}): {c['gap']}")
            elif c["type"]=="neglected_goal":print(f"    - NEGLECTED: {c['detail']}")
            elif c["type"]=="admin_overload":print(f"    - ADMIN OVERLOAD: {c['detail']}")
    if r["binding_constraint"]:print(f"\n  BINDING CONSTRAINT: {r['binding_constraint'].get('name',r['binding_constraint'])}")
    print(f"  Recommendation: {r['recommendation']}");print(SEP)

def eighty_twenty_review_cmd():
    tasks=[];result=demo(to_json=True)
    if result: tasks=[Task(**t)for t in result.get("ranked",[])]
    os=load_outcomes();r=eighty_twenty_review(tasks,os)
    print(f"\n  80/20 ANALYSIS");print(SEP)
    if r.get("message"):print(f"  {r['message']}");print(SEP);return
    print(f"  Total tasks: {r['total_tasks']} | Top 20% ({r['top20_count']} tasks) = {r['top20_score_pct']}% of value")
    print(f"\n  TOP 20% (highest leverage):")
    for t in r["top20"]:print(f"    - {t['name']} ({t['goal']}): score {t['score']}")
    if r.get("kill_candidates"):
        print(f"\n  KILL CANDIDATES (low-value admin):");[print(f"    - {k['name']} (score:{k['score']})")for k in r["kill_candidates"]]
    print(f"  Verdict: {r['verdict']}");print(SEP)

def bias_review_cmd():
    tasks=[];result=demo(to_json=True)
    if result: tasks=[Task(**t)for t in result.get("ranked",[])]
    ds=load_decisions();ps=load_predictions();records=load_recent_history(30)
    r=bias_detection(tasks,ds,ps,records)
    print(f"\n  COGNITIVE BIAS DETECTION");print(SEP)
    print(f"  {r['summary']}")
    for b in r["biases"]:
        print(f"\n  [{b['bias'].upper()}] confidence:{b['confidence']}%")
        print(f"    Evidence: {b['evidence']}")
        print(f"    Fix: {b['fix']}")
    print(SEP)

def scorecard_cmd():
    tasks=[];result=demo(to_json=True)
    if result: tasks=[Task(**t)for t in result.get("ranked",[])]
    os=load_outcomes();ps=load_predictions();ds=load_decisions();records=load_recent_history(30)
    r=strategic_scorecard(tasks,os,ps,ds,records)
    print(f"\n  STRATEGIC SCORECARD");print(SEP)
    print(f"  Overall: {r['overall_score']}/10 ({r['grade']})")
    print(f"\n  {'Dimension':<25s} {'Score':>6s}  Detail")
    print(f"  {'-'*25} {'-'*6}  {'-'*30}")
    for d in r["dimensions"]:print(f"  {d['dimension']:<25s} {d['score']:>5d}/10  {d['detail']}")
    print(SEP)

def red_team_review_cmd():
    tasks=[];result=demo(to_json=True)
    if result: tasks=[Task(**t)for t in result.get("ranked",[])]
    os=load_outcomes();ds=load_decisions();rs=load_risks();records=load_recent_history(30)
    print(red_team_prompt(tasks,os,ds,rs,records))

def board_memo_cmd():
    os=load_outcomes();ds=load_decisions();ass=load_assets();rs=load_risks();records=load_recent_history(30)
    print(board_memo_prompt(os,ds,ass,rs,records))

def kill_list_cmd():
    tasks=[];result=demo(to_json=True)
    if result: tasks=[Task(**t)for t in result.get("ranked",[])]
    os=load_outcomes();ds=load_decisions();ps=load_predictions()
    r=kill_list_recommendation(tasks,os,ds,ps)
    print(f"\n  KILL LIST");print(SEP)
    print(f"  {r['summary']}")
    if r["kill_items"]:
        for k in r["kill_items"]:
            print(f"  [{k['type'].upper()}] {k['target']}")
            print(f"    Reason: {k['reason']}")
            if k.get("saving_minutes"):print(f"    Saves: {k['saving_minutes']} min")
    print(SEP)

def assets_review_cmd():
    ass=load_assets();r=compounding_asset_review(ass)
    print(f"\n  COMPOUNDING ASSET REVIEW");print(SEP)
    print(f"  {r['summary']}")
    if r.get("by_type"):
        print(f"\n  BY TYPE:");[print(f"    {t}: {c}")for t,c in r["by_type"].items()]
    if r.get("promote"):
        print(f"\n  PROMOTE (high value, low reuse):");[print(f"    - {p['name']} ({p['type']}): future_val={p['future_value']}, reuse={p['reuse']}x — {p['action']}")for p in r["promote"]]
    if r.get("needs_maintenance"):
        print(f"\n  NEEDS MAINTENANCE:");[print(f"    - {m['name']} ({m['type']}): maintenance={m['maintenance']}")for m in r["needs_maintenance"]]
    print(SEP)

# ======================================================================
# REVIEWS
# ======================================================================
def detect_strategic_drift(records,cfg):
    w=[];baseline=cfg.get("strategic_baseline",{});at=cfg.get("admin_time_warning_threshold",25);lc=cfg.get("low_completion_warning_threshold",50)
    goal_mins={g:0 for g in STRATEGIC_GOALS}
    for r in records:
        for g in STRATEGIC_GOALS:goal_mins[g]+=r.get("portfolio",{}).get("by_goal",{}).get(g,{}).get("minutes",0)
    total=sum(goal_mins.values())or 1
    ap=goal_mins.get("admin_maintenance",0)/total*100
    if ap>at:w.append(f"Admin is {ap:.0f}% of planned time (>{at}%) -- serious drift.")
    gp=goal_mins.get("grant_funding",0)/total*100
    if gp<10:w.append(f"grant_funding is only {gp:.0f}% (<10%) -- under-invested.")
    rp=goal_mins.get("research_publication",0)/total*100
    if rp<15:w.append(f"research_publication is only {rp:.0f}% (<15%) -- under-invested.")
    dp=goal_mins.get("deeptech_venture",0)/total*100
    if dp==0 and len(records)>=14:w.append("deeptech_venture at 0% for 14+ days -- neglected.")
    completed=sum(len((r.get("reflection")or{}).get("completed_tasks",[]))for r in records)
    total_do=sum(len(r.get("do",[]))for r in records)
    if total_do>0:
        rate=completed/total_do*100
        if rate<lc:w.append(f"Completion rate {rate:.0f}% (<{lc}%) -- overcommitted or unrealistic.")
    over_days=sum(1 for r in records if r.get("overcommitted",False))
    if over_days>3 and len(records)<=7:w.append(f"Overcommitted on {over_days}/{len(records)} days.")
    large=sum(1 for r in records for t in r.get("do",[])if t.get("estimated_minutes",0)>=180)
    if large>=3:w.append(f"{large} DO tasks >=3h -- break large tasks into smaller chunks.")
    return w

def weekly_review(days=7):
    records=load_recent_history(days)
    if not records:print("No history. Run with --save-history first.");return
    cfg=load_config();baseline=cfg.get("strategic_baseline",{})
    total_planned=sum(r.get("total_planned_minutes",0)for r in records)
    over_days=sum(1 for r in records if r.get("overcommitted",False))
    energies=[r.get("energy",5)for r in records]
    completed=sum(len((r.get("reflection")or{}).get("completed_tasks",[]))for r in records)
    total_do=sum(len(r.get("do",[]))for r in records)
    rate=round(completed/total_do*100,1)if total_do else 0
    goal_mins={g:0 for g in STRATEGIC_GOALS}
    for r in records:
        for g in STRATEGIC_GOALS:goal_mins[g]+=r.get("portfolio",{}).get("by_goal",{}).get(g,{}).get("minutes",0)
    total_mins=sum(goal_mins.values())or 1
    delayed_counts={}
    for r in records:
        for t in r.get("delay",[]):n=t["name"];delayed_counts[n]=delayed_counts.get(n,0)+1
    print("\n"+"="*62)
    print(f"  WEEKLY REVIEW -- last {days} day(s), {len(records)} record(s)")
    print("="*62)
    print(f"  Days: {len(records)} | Planned min: {total_planned} | DO tasks: {total_do}")
    print(f"  Completed: {completed} | Rate: {rate}% | Overcommitted: {over_days}")
    print(f"  Avg energy: {round(sum(energies)/len(energies),1)}")
    print(f"\n  {'Goal':<28s} {'Min':>6s} {'%Time':>6s} {'Target':>6s}")
    print(f"  {'-'*28} {'-'*6} {'-'*6} {'-'*6}")
    for g in STRATEGIC_GOALS:
        m=goal_mins[g];pct=m/total_mins*100;bl=baseline.get(g,0)
        print(f"  {g:<28s} {m:>6d} {pct:>5.1f}% {bl:>5d}%")
    if delayed_counts:
        top=sorted(delayed_counts.items(),key=lambda x:-x[1])[:3]
        print(f"\n  Top recurring delayed:");[print(f"    * {n} -- {c}x")for n,c in top]
    print(f"\n  STRATEGIC DRIFT");print("-"*62)
    drift=detect_strategic_drift(records,cfg)
    if drift:[print(f"  !! {d}")for d in drift]
    else:print("  No significant drift detected.")
    print("="*62)

def monthly_review(days=30):
    records=load_recent_history(days)
    if not records:print("No history. Run with --save-history first.");return
    cfg=load_config();baseline=cfg.get("strategic_baseline",{})
    projs=load_projects()
    total_planned=sum(r.get("total_planned_minutes",0)for r in records)
    completed=sum(len((r.get("reflection")or{}).get("completed_tasks",[]))for r in records)
    total_do=sum(len(r.get("do",[]))for r in records)
    rate=round(completed/total_do*100,1)if total_do else 0
    goal_mins={g:0 for g in STRATEGIC_GOALS}
    for r in records:
        for g in STRATEGIC_GOALS:goal_mins[g]+=r.get("portfolio",{}).get("by_goal",{}).get(g,{}).get("minutes",0)
    total_mins=sum(goal_mins.values())or 1
    admin_pct=goal_mins.get("admin_maintenance",0)/total_mins*100
    deep_work_pct=(goal_mins.get("research_publication",0)+goal_mins.get("grant_funding",0)+goal_mins.get("deeptech_venture",0))/total_mins*100
    stagnant=[p for p in projs if p.status=="active" and not p.actual_hours_logged]
    print("\n"+"="*62)
    print(f"  MONTHLY REVIEW -- last {days} day(s) from {len(records)} records")
    print("="*62)
    print(f"  Total planned: {total_planned} min ({total_planned/60:.1f}h) | DO tasks: {total_do}")
    print(f"  Completed: {completed} | Rate: {rate}%")
    print(f"\n  STRATEGIC ALLOCATION vs BASELINE:")
    print(f"  {'Goal':<28s} {'Planned%':>8s} {'Target%':>8s} {'Gap':>8s}")
    print(f"  {'-'*28} {'-'*8} {'-'*8} {'-'*8}")
    for g in STRATEGIC_GOALS:
        m=goal_mins[g];pct=m/total_mins*100;bl=baseline.get(g,0);gap=pct-bl
        flag=" < UNDER" if gap<-5 else(" > OVER" if gap>5 else"")
        print(f"  {g:<28s} {pct:>7.1f}% {bl:>7d}% {gap:>+7.1f}%{flag}")
    print(f"\n  Admin: {admin_pct:.0f}% | Deep work: {deep_work_pct:.0f}%")
    if projs:
        top5_time=sorted(projs,key=lambda p:p.estimated_total_hours or 0,reverse=True)[:5]
        print(f"\n  TOP 5 PROJECTS BY TIME:")
        for p in top5_time:print(f"    {p.name}: {p.estimated_total_hours}h est | status:{p.status}")
    if stagnant:
        print(f"\n  STAGNANT PROJECTS ({len(stagnant)}):")
        for p in stagnant:print(f"    - {p.name} ({p.project_id})")
    print(f"\n  STRATEGIC DRIFT");print("-"*62)
    drift=detect_strategic_drift(records,cfg)
    if drift:[print(f"  !! {d}")for d in drift]
    else:print("  No significant drift detected.")
    print(f"\n  RECOMMENDED CORRECTIONS:");print("-"*62)
    if admin_pct>25:print("  - Reduce admin/maintenance by protecting 2x90min deep-work blocks/week.")
    if goal_mins.get("grant_funding",0)/total_mins*100<10:print("  - Move grant_funding from reactive to scheduled weekly blocks.")
    if goal_mins.get("deeptech_venture",0)/total_mins*100<5:print("  - Break deeptech_venture into one minimum viable experiment.")
    if rate<50:print("  - Reduce planned DO tasks to increase completion reliability.")
    print("="*62)

def antifragile_review():
    records=load_recent_history(30)
    cfg=load_config();opps=load_opps()
    print("\n"+"="*62);print("  ANTI-FRAGILE REVIEW");print("="*62)
    print(f"\n  1. What improved because of stress/constraints?")
    if records:
        reflections=[(r.get("reflection")or{}).get("lesson","")for r in records if (r.get("reflection")or{}).get("lesson")]
        if reflections:print(f"     Recent lessons: {'; '.join(reflections[-3:])}")
        else:print("     (No reflections found. Run --reflect to capture lessons.)")
    print(f"\n  2. Which recurring problem can become a system?")
    delayed_counts={}
    for r in records:
        for t in r.get("delay",[]):n=t["name"];delayed_counts[n]=delayed_counts.get(n,0)+1
    if delayed_counts:
        worst=max(delayed_counts,key=delayed_counts.get)
        print(f"     '{worst}' delayed {delayed_counts[worst]}x — could be a process or a deletion.")
    print(f"\n  3. Which failure contains useful information?")
    incomplete={}
    for r in records:
        ref=r.get("reflection")or{}
        for name,reason in ref.get("reasons_incomplete",{}).items():incomplete[name]=incomplete.get(name,0)+1
    if incomplete:
        worsti=max(incomplete,key=incomplete.get)
        print(f"     '{worsti}' incomplete {incomplete[worsti]}x — why?")
    print(f"\n  4. Which relationship should be strengthened?")
    rels=load_relationships()
    if rels:
        high_val=[r for r in rels if r.last_contact_date and (date.today()-date.fromisoformat(r.last_contact_date)).days>60]
        if high_val:print(f"     {len(high_val)} relationship(s) with no contact >60d.")
    print(f"\n  5. Which task should be permanently removed?")
    admin_burden=0
    for r in records:
        port=r.get("portfolio",{}).get("by_goal",{}).get("admin_maintenance",{})
        admin_burden+=port.get("minutes",0)
    if admin_burden>0:print(f"     {admin_burden} min spent on admin — what can be deleted or automated?")
    print(f"\n  6. Which process should be automated or templated?")
    opps_stale=[o for o in opps if o.status=="open" and (date.today()-date.fromisoformat(o.last_touched_date)).days>14]
    if opps_stale:print(f"     {len(opps_stale)} stale opportunities — needs a weekly check-in template.")
    print("="*62)

# ======================================================================
# DASHBOARD
# ======================================================================
def recommend_next_best_move(ranked,do,ah,energy,records,projs,opps,risks):
    cfg=load_config();baseline=cfg.get("strategic_baseline",{})
    # Rule 1: high risk (>8 severity, no mitigation)
    for r in sorted(risks,key=lambda r:risk_score(r),reverse=True):
        if r.severity>=8 and not r.mitigation:return f"MITIGATE RISK: {r.title} — {r.mitigation or 'define mitigation immediately'}"
    # Rule 2: grant_funding below baseline
    goal_mins={g:0 for g in STRATEGIC_GOALS}
    for rec in records:goal_mins={g:goal_mins[g]+rec.get("portfolio",{}).get("by_goal",{}).get(g,{}).get("minutes",0)for g in STRATEGIC_GOALS}
    total_mins=sum(goal_mins.values())or 1
    gp=goal_mins.get("grant_funding",0)/total_mins*100
    if gp<baseline.get("grant_funding",10):
        active_grant=[p for p in projs if p.strategic_goal=="grant_funding" and p.status=="active"]
        if active_grant:return f"PROTECT GRANT WORK: {active_grant[0].name} — grant_funding is {gp:.0f}% vs {baseline.get('grant_funding',10)}% target."
    # Rule 3: research below baseline
    rp=goal_mins.get("research_publication",0)/total_mins*100
    if rp<baseline.get("research_publication",15):
        active_res=[p for p in projs if p.strategic_goal=="research_publication" and p.status=="active"]
        if active_res:return f"PROTECT RESEARCH: {active_res[0].name} — research is {rp:.0f}% vs {baseline.get('research_publication',15)}% target."
    # Rule 4: admin overload
    ap=goal_mins.get("admin_maintenance",0)/total_mins*100
    if ap>cfg.get("admin_time_warning_threshold",25):return f"CUT ADMIN: Admin at {ap:.0f}% (>25%) — delegate, delete, or batch."
    # Rule 5: high-value stale opportunity
    stale=[o for o in opps if o.status=="open" and o.last_touched_date and (date.today()-date.fromisoformat(o.last_touched_date)).days>14]
    if stale:return f"FOLLOW UP: {stale[0].name} (opportunity) — {stale[0].next_action or 'send a check-in message'}"
    # Rule 6: energy-aware
    if energy<=3 and do:return f"LOW ENERGY: Start with {do[0].name} ({do[0].estimated_minutes}min) — then reassess."
    # Default
    if do:return f"EXECUTE: {do[0].name} — top-ranked DO task ({do[0].label}, {do[0].final_score})"
    return "PLAN: No urgent moves — review strategy and prune low-value tasks."

def dashboard():
    records=load_recent_history(7)
    cfg=load_config();projs=load_projects();opps=load_opps();risks=load_risks()
    # Run demo pipeline
    ah=6.0;energy=7;deadlines="See projects";meetings="See calendar"
    result=demo(to_json=True)
    do_names=[t["name"]for t in result.get("do",[])]
    do_mins=result.get("overcommitment",{}).get("do_minutes",0)
    am=result.get("diagnosis",{}).get("available_minutes",360)
    first30=result.get("first_30_minutes","")
    over=result.get("overcommitment",{}).get("overcommitted",False)
    # Weekly stats
    completed=sum(len((r.get("reflection")or{}).get("completed_tasks",[]))for r in records)
    total_do=sum(len(r.get("do",[]))for r in records)
    rate=round(completed/total_do*100,1)if total_do else 0
    goal_mins={g:0 for g in STRATEGIC_GOALS}
    for r in records:
        for g in STRATEGIC_GOALS:goal_mins[g]+=r.get("portfolio",{}).get("by_goal",{}).get(g,{}).get("minutes",0)
    total_mins_week=sum(goal_mins.values())or 1
    admin_pct=goal_mins.get("admin_maintenance",0)/total_mins_week*100
    delayed_counts={}
    for r in records:
        for t in r.get("delay",[]):n=t["name"];delayed_counts[n]=delayed_counts.get(n,0)+1
    top_delayed=sorted(delayed_counts.items(),key=lambda x:-x[1])[:3]
    # Monthly
    records_m=load_recent_history(30)
    goal_mins_m={g:0 for g in STRATEGIC_GOALS}
    for r in records_m:
        for g in STRATEGIC_GOALS:goal_mins_m[g]+=r.get("portfolio",{}).get("by_goal",{}).get(g,{}).get("minutes",0)
    total_mins_m=sum(goal_mins_m.values())or 1
    stagnant=[p for p in projs if p.status=="active" and not p.actual_hours_logged]
    # Risks
    top_risks=sorted(risks,key=lambda r:risk_score(r),reverse=True)[:3]
    # Next move
    ranked=[Task(name=t["name"],final_score=t.get("final_score",0),label=t.get("label",""),estimated_minutes=t.get("estimated_minutes",0))for t in result.get("ranked",[])]
    do=[Task(name=t["name"],estimated_minutes=t.get("estimated_minutes",0))for t in result.get("do",[])]
    next_move=recommend_next_best_move(ranked,do,ah,energy,records,projs,opps,risks)
    # Print
    print("\n"+"="*62);print("  STRATEGIC DASHBOARD");print("="*62)
    print(f"\n  TODAY");print("-"*40)
    print(f"  DO ({len(do_names)}): {', '.join(do_names)}")
    print(f"  First 30: {first30}")
    if over:print(f"  !! OVERCOMMITTED: DO {do_mins} min vs {am} min available")
    print(f"\n  THIS WEEK ({len(records)} records)");print("-"*40)
    print(f"  Completion: {completed}/{total_do} ({rate}%) | Admin: {admin_pct:.0f}%")
    print(f"  Grant: {goal_mins.get('grant_funding',0)/total_mins_week*100:.0f}% | Research: {goal_mins.get('research_publication',0)/total_mins_week*100:.0f}% | Deep: {goal_mins.get('deeptech_venture',0)/total_mins_week*100:.0f}%")
    if top_delayed:
        print(f"  Top delayed: {', '.join(f'{n}({c}x)'for n,c in top_delayed)}")
    print(f"\n  THIS MONTH ({len(records_m)} records)");print("-"*40)
    print(f"  Projects: {len(projs)} active | Stagnant: {len(stagnant)}")
    opps_open=len([o for o in opps if o.status=="open"])
    stale_opps=len([o for o in opps if o.status=="open" and o.last_touched_date and (date.today()-date.fromisoformat(o.last_touched_date)).days>14])
    print(f"  Opportunities: {opps_open} open | Stale: {stale_opps}")
    print(f"\n  RISKS");print("-"*40)
    if top_risks:
        for r in top_risks:print(f"  {r.title} (score:{risk_score(r)}) — {r.mitigation or'NO MITIGATION'}")
    else:print("  No risks registered.")
    print(f"\n  NEXT BEST MOVE");print("-"*40)
    print(f"  {next_move}")
    print("="*62)

# ======================================================================
# STRATEGY MEMO & AI PROMPTS
# ======================================================================
def strategy_memo(export_path=None):
    records=load_recent_history(30);cfg=load_config()
    projs=load_projects();opps=load_opps();risks=load_risks()
    baseline=cfg.get("strategic_baseline",{})
    goal_mins={g:0 for g in STRATEGIC_GOALS}
    for r in records:
        for g in STRATEGIC_GOALS:goal_mins[g]+=r.get("portfolio",{}).get("by_goal",{}).get(g,{}).get("minutes",0)
    total_mins=sum(goal_mins.values())or 1
    active_projs=[p for p in projs if p.status=="active"]
    stagnant=[p for p in projs if p.status=="active" and not p.actual_hours_logged]
    stale_opps=[o for o in opps if o.status=="open" and o.last_touched_date and (date.today()-date.fromisoformat(o.last_touched_date)).days>14]
    top_risks=sorted(risks,key=lambda r:risk_score(r),reverse=True)[:3]
    completed=sum(len((r.get("reflection")or{}).get("completed_tasks",[]))for r in records)
    total_do=sum(len(r.get("do",[]))for r in records)
    rate=round(completed/total_do*100,1)if total_do else 0
    lines=[
        "="*62,
        f"  STRATEGIC MEMO — {date.today().isoformat()}",
        "="*62,
        f"\n  CURRENT TRAJECTORY:",
        f"  Completion rate: {rate}% over last {len(records)} days.",
        f"  Active projects: {len(active_projs)}. Stagnant: {len(stagnant)}.",
        f"  Open opportunities: {len(opps)}. Stale: {len(stale_opps)}.",
        f"  Top risks: {', '.join(r.title for r in top_risks) if top_risks else 'none'}.",
        f"\n  STRATEGIC ALLOCATION:",
    ]
    for g in STRATEGIC_GOALS:
        pct=goal_mins.get(g,0)/total_mins*100;bl=baseline.get(g,0)
        lines.append(f"  {g}: {pct:.0f}% (target {bl}%)")
    lines+=["\n  MAJOR RISKS:"]
    if top_risks:
        for r in top_risks:lines.append(f"  - {r.title}: {r.mitigation or'no mitigation'}")
    else:lines.append("  - None registered.")
    lines+=["\n  MAJOR OPPORTUNITIES:"]
    top_opps=sorted(opps,key=lambda o:opp_score(o),reverse=True)[:3]
    if top_opps:
        for o in top_opps:lines.append(f"  - {o.name} (score:{opp_score(o)}) — {o.next_action or'no next action'}")
    else:lines.append("  - None registered.")
    lines+=["\n  RECOMMENDED NEXT MOVES:",
    "  1. Protect the highest-leverage DO task for the next 24h.",
    "  2. Follow up on the highest-value stale opportunity.",
    "  3. Mitigate the highest-scoring active risk.",
    "\n  TASKS TO DELETE:",
    "  - Any admin task taking >60min without strategic alignment.",
    "  - Any recurring delayed task with no deadline.",
    "\n  PROJECTS TO PROTECT:",
    f"  - {'; '.join(p.name for p in active_projs[:3]) if active_projs else 'none'}",
    "\n  RELATIONSHIPS TO STRENGTHEN:",
    f"  - Follow up on any relationship with >60d no contact.",
    "\n  30-DAY STRATEGIC CORRECTION:",
    f"  - Reduce admin to <{cfg.get('admin_time_warning_threshold',25)}% of planned time.",
    "  - Move grant funding to scheduled weekly blocks.",
    "  - Convert one deeptech_venture idea into a minimum viable experiment.",
    "="*62,
    ]
    text="\n".join(lines); print(text)
    if export_path:Path(export_path).write_text(text+"\n");print(f"\n  [Memo saved to {export_path}]",file=sys.stderr)

def multi_agent_prompt():
    result=demo(to_json=True)
    if not result:return
    d=result["diagnosis"];ranked_names=[t["name"]for t in result.get("ranked",[])]
    do_names=[t["name"]for t in result.get("do",[])]
    delay_names=[t["name"]for t in result.get("delay",[])]
    dele_names=[t["name"]for t in result.get("delegate",[])]
    ignore_names=[t["name"]for t in result.get("ignore",[])]
    port=result.get("portfolio",{}).get("by_goal",{})
    over=result.get("overcommitment",{})
    p=f"""=== CHIEF OF STAFF MULTI-AGENT REVIEW PROMPT ===
(COPY INTO YOUR AI ASSISTANT)

LONG-TERM GOALS:
{LONG_TERM_GOALS}

TODAY: {d.get('available_hours')}h | Energy: {d.get('energy')}/10
Deadlines: {d.get('deadlines')} | Meetings: {d.get('meetings')}

RANKED: {', '.join(ranked_names)}
DO ({len(do_names)}): {', '.join(do_names)if do_names else'(none)'}
DELAY: {', '.join(delay_names)if delay_names else'(none)'}
DELEGATE: {', '.join(dele_names)if dele_names else'(none)'}
IGNORE: {', '.join(ignore_names)if ignore_names else'(none)'}

PORTFOLIO:
"""
    for g in STRATEGIC_GOALS:
        pg=port.get(g,{});pct=pg.get("pct_time",0)
        if pg.get("count",0)==0:continue
        p+=f"  {g}: {pg.get('count',0)} tasks, {pg.get('minutes',0)} min ({pct}%)\n"
    p+=f"""
OVERCOMMITMENT: {'YES' if over.get('overcommitted')else'no'} (DO:{over.get('do_minutes',0)}min vs {over.get('available_minutes',0)})

---

SIMULATE THESE 8 ADVISORY ROLES. For each, provide:
- Diagnosis
- One recommendation
- One thing to stop doing
- One hidden risk
- One leverage point

1. CHIEF OF STAFF
2. RESEARCH STRATEGIST
3. GRANT STRATEGIST
4. INDUSTRY COLLABORATION STRATEGIST
5. TEACHING EXCELLENCE STRATEGIST
6. DEEP-TECH VENTURE STRATEGIST
7. RISK OFFICER
8. ACCOUNTABILITY COACH

FINAL SYNTHESIS:
Give the single highest-leverage move for the next 24 hours, 7 days, and 30 days.
=== END OF PROMPT ==="""
    print(p)

def ai_review_prompt():
    result=demo(to_json=True)
    if not result:return
    d=result["diagnosis"];ranked_names=[t["name"]for t in result.get("ranked",[])]
    do_names=[t["name"]for t in result.get("do",[])]
    p=f"""=== AI ADVISORY PROMPT ===
LONG-TERM GOALS: {LONG_TERM_GOALS}
TODAY: {d.get('available_hours')}h | Energy: {d.get('energy')}/10
RANKED: {', '.join(ranked_names)}
DO: {', '.join(do_names)}

AS AI ADVISOR:
1. BRUTALLY HONEST DIAGNOSIS
2. ONE TASK TO DELETE
3. ONE TASK TO PROTECT
4. ONE HIDDEN OPPORTUNITY COST
5. ONE STRATEGIC RELATIONSHIP
6. ONE EXECUTION SCRIPT
7. ONE REFLECTION QUESTION
=== END ==="""
    print(p)

# ======================================================================
# SCENARIO
# ======================================================================
SCENARIOS={"A: Normal day":{"energy":7,"hours":6.0},"B: Low-energy day":{"energy":3,"hours":4.0},"C: Deadline crisis":{"energy":8,"hours":8.0},"D: Deep-work day":{"energy":9,"hours":5.0}}

def scenario_mode(tasks,ah,energy):
    print("\n"+"="*62);print("  SCENARIO PLANNING");print("="*62)
    for name,params in SCENARIOS.items():
        en=params["energy"];am=int(params["hours"]*60)
        ranked=rank_tasks(tasks);do,delay,dele,ignore,do_mins,over=classify_tasks(ranked,en,am)
        print(f"\n  --- {name} ---")
        print(f"  Energy:{en}/10 | Avail:{params['hours']}h ({am}min) | DO cap:{do_capacity(en)}")
        print(f"  DO ({len(do)}): {', '.join(t.name for t in do)}")
        print(f"  Delay:{len(delay)} | Delegate:{len(dele)} | Ignore:{len(ignore)} | Over:{'YES' if over else'no'}")
    print("\n"+"="*62)

# ======================================================================
# CORE PIPELINE
# ======================================================================
def run_pipeline(tasks,available_hours,deadlines,meetings,energy,*,to_json=False,save_hist=False):
    am=int(available_hours*60)
    errs=[]
    for t in tasks:errs.extend(validate_task(t))
    if errs:
        if to_json:return{"error":"validation_failed","details":errs}
        print("  VALIDATION ERRORS");[print(f"      {e}")for e in errs];return None
    ranked=rank_tasks(tasks)
    do,delay,dele,ignore,do_mins,over=classify_tasks(ranked,energy,am)
    first30=make_first_30min(do);total_mins=sum(t.estimated_minutes for t in tasks)
    if save_hist:
        rec=build_history_record(tasks,ranked,available_hours,am,deadlines,meetings,energy,do,delay,dele,ignore,do_mins,over,first30)
        save_history(rec)
    if to_json:return _build_json(tasks,ranked,available_hours,am,deadlines,meetings,energy,do,delay,dele,ignore,do_mins,over,first30,total_mins)
    print();print_diagnosis(available_hours,am,deadlines,meetings,energy,tasks)
    print_portfolio(ranked,load_config());print_top3(ranked)
    print_actions(do,delay,dele,ignore);print_warnings(ranked)
    if over or do_mins>am or total_mins>am*3:print_overcommit(do_mins,am,total_mins)
    print_execution_script(do);print_first_30(first30);print();return None

def _build_json(tasks,ranked,ah,am,deadlines,meetings,energy,do,delay,dele,ignore,do_mins,over,first30,total_mins):
    cnt,mins,avg,total=portfolio_diagnosis(ranked)
    return{"diagnosis":{"available_hours":ah,"available_minutes":am,"deadlines":deadlines,"meetings":meetings,"energy":energy,"do_capacity":do_capacity(energy),"tasks_submitted":len(tasks)},"ranked":[ser_task(t)for t in ranked],"do":[ser_task(t)for t in do],"delay":[ser_task(t)for t in delay],"delegate":[ser_task(t)for t in dele],"ignore":[ser_task(t)for t in ignore],"portfolio":{"by_goal":{g:{"count":cnt[g],"minutes":mins[g],"pct_time":round(mins[g]/(total or 1)*100,1),"avg_score":avg[g]}for g in STRATEGIC_GOALS},"total_minutes":total},"overcommitment":{"do_minutes":do_mins,"available_minutes":am,"do_exceeds":do_mins>am,"overcommitted":over,"total_task_minutes":total_mins,"total_pct_of_available":round(total_mins/(am or 1)*100,1)},"first_30_minutes":first30,"execution_script":make_execution_script(do[0])if do else[]}

def validate_task(t):
    errs=[]
    for f in["impact","urgency","strategic_value","compounding_effect","goal_alignment","deadline_pressure","energy_fit","opportunity_cost","focus_requirement"]:
        v=getattr(t,f)
        if not(1<=v<=10):errs.append(f"{f} must be 1-10, got {v}")
    if t.estimated_minutes<=0:errs.append("estimated_minutes must be positive")
    if t.strategic_goal not in STRATEGIC_GOALS:errs.append(f"bad strategic_goal '{t.strategic_goal}'")
    return errs

# ======================================================================
# DEMO
# ======================================================================
def demo(*,to_json=False,save_hist=False):
    ah=6.0;deadlines="Grant proposal draft due Friday";meetings="Lab meeting 10:00-11:00, Collaborator call 15:00-16:00";energy=7
    tasks=[Task("Write grant proposal outline",9,9,10,8,10,9,8,2,9,120,"grant_funding","Open Overleaf and draft the 1-page outline"),Task("Review literature on OPV materials",6,5,9,7,9,4,7,3,7,90,"research_publication","Pull 5 recent papers from Google Scholar"),Task("Prepare slides for lab meeting",5,8,4,3,5,8,6,3,4,45,"teaching_excellence","Copy template and update figures",True),Task("Reply to industry partner email",7,6,8,6,8,5,7,2,3,20,"industry_collaboration","Draft reply in 3 bullet points"),Task("Update CV & publication list",5,3,7,5,7,2,5,4,3,60,"public_influence","Add the 2 recent accepted papers",True),Task("Organise lab inventory",2,2,1,1,1,1,2,8,2,90,"admin_maintenance","",True)]
    return run_pipeline(tasks,ah,deadlines,meetings,energy,to_json=to_json,save_hist=save_hist)

# ======================================================================
# INTERACTIVE
# ======================================================================
def interactive(*,to_json=False,save_hist=False):
    print("\n  CHIEF OF STAFF AGENT v5  (interactive mode)");print(SEP)
    ah=_get_float("  Available focused work hours today: ",0.5)
    deadlines=input("  Deadlines: ").strip();meetings=input("  Meetings: ").strip()
    energy=_get_int("  Energy level (1-10): ",1,10)
    templates=load_templates()
    print("\n  Now enter your tasks. Leave task name blank to finish.\n")
    tasks=[]
    while True:
        name=input(f"  Task {len(tasks)+1} name (or Enter to stop): ").strip()
        if not name:break
        use_tmpl=_get_yn("    Use a template? (y/n): ")
        prefill={}
        if use_tmpl:
            tkeys=list(templates.keys())
            print("    Available templates:");[print(f"      {i}. {k}")for i,k in enumerate(tkeys,1)]
            try:c=int(input("    -> Choose (0 to skip): ").strip())
            except ValueError:c=0
            if 1<=c<=len(tkeys):prefill=dict(templates[tkeys[c-1]]);print(f"    Loaded: {tkeys[c-1]}")
        print(f"    -- Scoring: {name} --")
        def _p(label,key,default=5):
            if prefill:return _get_int(f"    {label} (1-10) [{prefill.get(key,default)}]: ")
            return _get_int(f"    {label} (1-10): ")
        impact=_p("Impact","impact");urgency=_p("Urgency","urgency")
        sv=_p("Strategic Value","strategic_value");ce=_p("Compounding Effect","compounding_effect")
        ga=_p("Goal Alignment","goal_alignment");dp=_p("Deadline Pressure","deadline_pressure")
        ef=_p("Energy Fit","energy_fit");oc=_p("Opportunity Cost","opportunity_cost")
        fr=_p("Focus Requirement","focus_requirement")
        if prefill:em=_get_pos(f"    Estimated minutes [{prefill.get('estimated_minutes',60)}]: ")
        else:em=_get_pos("    Estimated minutes: ")
        if prefill:sg=prefill.get("strategic_goal","research_publication");print(f"    Strategic goal (from template): {sg}")
        else:sg=_get_goal()
        na=input("    Next action: ").strip();deleg=_get_yn("    Delegatable? (y/n): ")
        # Link to project
        proj_id=None
        if _get_yn("    Link to a project? (y/n): "):
            projs=load_projects()
            active=[p for p in projs if p.status=="active"]
            if active:
                print("    Active projects:");[print(f"      {i}. {p.name} ({p.project_id})")for i,p in enumerate(active,1)]
                try:
                    c=int(input("    -> Choose (0 to skip): ").strip())
                    if 1<=c<=len(active):proj_id=active[c-1].project_id
                except ValueError:pass
        tasks.append(Task(name,impact,urgency,sv,ce,ga,dp,ef,oc,fr,em,sg,na,deleg,project_id=proj_id))
    if not tasks:print("  No tasks. Exiting.");return None
    return run_pipeline(tasks,ah,deadlines,meetings,energy,to_json=to_json,save_hist=save_hist)

def reflect(date_str):
    record=load_history(date_str)
    if not record:print(f"No plan found for {date_str}");return
    print(f"\n  REFLECTION -- {date_str}");print(SEP)
    do_tasks=[t["name"]for t in record.get("do",[])]
    print(f"  DO tasks planned: {', '.join(do_tasks) if do_tasks else'(none)'}\n")
    completed,incomplete,reasons=[],[],{}
    for name in do_tasks:
        ans=input(f'  Completed: "{name}"? (y/n): ').strip().lower()
        if ans in("y","yes"):completed.append(name)
        else:incomplete.append(name);reasons[name]=input("    Why not? ").strip()
    raw=input("  Unexpected tasks: ").strip()
    unexpected=[u.strip()for u in raw.split(",")if u.strip()]if raw else[]
    actual_energy=_get_int("  Actual energy level (1-10): ",1,10)
    lesson=input("  One lesson: ").strip()
    rate=round(len(completed)/len(do_tasks)*100,1)if do_tasks else 100.0
    record["reflection"]={"completed_tasks":completed,"incomplete_tasks":incomplete,"reasons_incomplete":reasons,"unexpected_tasks":unexpected,"actual_energy":actual_energy,"lesson":lesson,"completion_rate":rate}
    (HISTORY_DIR/f"{date_str}_plan.json").write_text(json.dumps(record,indent=2))
    print(f"\n  Reflection saved. Completion rate: {rate}%");print(f"  Lesson: {lesson}")

# ======================================================================
# CLI
# ======================================================================
def main():
    p=argparse.ArgumentParser(description="Chief of Staff Agent v6")
    g=p.add_mutually_exclusive_group()
    g.add_argument("--demo",action="store_true",help="Sample daily plan")
    g.add_argument("--dashboard",action="store_true",help="Strategic dashboard")
    g.add_argument("--monthly-review",action="store_true",help="Monthly strategic review")
    g.add_argument("--weekly-review",action="store_true",help="Weekly review")
    g.add_argument("--strategy-memo",action="store_true",help="Strategic memo")
    g.add_argument("--multi-agent-review",action="store_true",help="Multi-agent AI prompt")
    g.add_argument("--ai-review",action="store_true",help="AI advisory prompt")
    g.add_argument("--antifragile-review",action="store_true",help="Anti-fragile review")
    g.add_argument("--scenario",action="store_true",help="Scenario planning")
    g.add_argument("--projects",action="store_true",help="List projects")
    g.add_argument("--add-project",action="store_true",help="Add project")
    g.add_argument("--project-review",action="store_true",help="Project review")
    g.add_argument("--opportunities",action="store_true",help="List opportunities")
    g.add_argument("--add-opportunity",action="store_true",help="Add opportunity")
    g.add_argument("--opportunity-review",action="store_true",help="Opportunity review")
    g.add_argument("--decisions",action="store_true",help="List decisions")
    g.add_argument("--add-decision",action="store_true",help="Log a decision")
    g.add_argument("--experiments",action="store_true",help="List experiments")
    g.add_argument("--add-experiment",action="store_true",help="Add experiment")
    g.add_argument("--risks",action="store_true",help="List risks")
    g.add_argument("--add-risk",action="store_true",help="Add risk")
    g.add_argument("--risk-review",action="store_true",help="Risk review")
    g.add_argument("--relationships",action="store_true",help="List relationships")
    g.add_argument("--add-relationship",action="store_true",help="Add relationship")
    g.add_argument("--relationship-review",action="store_true",help="Relationship review")
    g.add_argument("--principles",action="store_true",help="List principles")
    g.add_argument("--add-principle",action="store_true",help="Add principle")
    # V6 commands
    g.add_argument("--outcomes",action="store_true",help="List strategic outcomes")
    g.add_argument("--add-outcome",action="store_true",help="Add strategic outcome")
    g.add_argument("--evidence",action="store_true",help="List evidence")
    g.add_argument("--add-evidence",action="store_true",help="Add evidence")
    g.add_argument("--assumptions",action="store_true",help="List assumptions")
    g.add_argument("--add-assumption",action="store_true",help="Add assumption")
    g.add_argument("--predictions",action="store_true",help="List predictions")
    g.add_argument("--add-prediction",action="store_true",help="Add prediction")
    g.add_argument("--resolve-prediction",action="store_true",help="Resolve a prediction")
    g.add_argument("--calibration-review",action="store_true",help="Prediction calibration review")
    g.add_argument("--decision-quality-review",action="store_true",help="Decision quality review")
    g.add_argument("--leverage-review",action="store_true",help="Leverage analysis")
    g.add_argument("--constraint-review",action="store_true",help="Constraint diagnosis")
    g.add_argument("--eighty-twenty-review",action="store_true",help="80/20 Pareto analysis")
    g.add_argument("--hypotheses",action="store_true",help="List strategic hypotheses")
    g.add_argument("--add-hypothesis",action="store_true",help="Add strategic hypothesis")
    g.add_argument("--bias-review",action="store_true",help="Cognitive bias detection")
    g.add_argument("--scorecard",action="store_true",help="Strategic scorecard")
    g.add_argument("--red-team-review",action="store_true",help="AI red-team prompt")
    g.add_argument("--board-memo",action="store_true",help="AI board memo prompt")
    g.add_argument("--kill-list",action="store_true",help="Kill/stop list")
    g.add_argument("--assets",action="store_true",help="List compounding assets")
    g.add_argument("--add-asset",action="store_true",help="Add compounding asset")
    g.add_argument("--doctrine",action="store_true",help="List personal doctrine")
    g.add_argument("--add-doctrine",action="store_true",help="Add personal doctrine entry")
    g.add_argument("--reflect",type=str,metavar="YYYY-MM-DD",help="End-of-day reflection")
    g.add_argument("--project",type=str,metavar="PROJECT_ID",help="Project detail")
    p.add_argument("--json",action="store_true",help="Clean JSON output")
    p.add_argument("--export",type=str,metavar="FILE",help="Save JSON/text to FILE")
    p.add_argument("--save-history",action="store_true",help="Persist daily plan")
    p.add_argument("--days",type=int,default=7,help="Days for review (default 7)")
    args=p.parse_args()

    if args.reflect: reflect(args.reflect); return
    if args.project: project_detail(args.project); return
    if args.projects: list_projects(); return
    if args.add_project: add_project_interactive(); return
    if args.project_review: project_review(); return
    if args.opportunities: list_opps(); return
    if args.add_opportunity: add_opportunity_interactive(); return
    if args.opportunity_review: opportunity_review(); return
    if args.decisions: list_decisions(); return
    if args.add_decision: add_decision_interactive(); return
    if args.experiments: list_experiments(); return
    if args.add_experiment: add_experiment_interactive(); return
    if args.risks: list_risks(); return
    if args.add_risk: add_risk_interactive(); return
    if args.risk_review: risk_review(); return
    if args.relationships: list_relationships(); return
    if args.add_relationship: add_relationship_interactive(); return
    if args.relationship_review: relationship_review(); return
    if args.principles: list_principles(); return
    if args.add_principle: add_principle_interactive(); return
    # V6 dispatch
    if args.outcomes: list_outcomes(); return
    if args.add_outcome: add_outcome_interactive(); return
    if args.evidence: list_evidence(); return
    if args.add_evidence: add_evidence_interactive(); return
    if args.assumptions: list_assumptions(); return
    if args.add_assumption: add_assumption_interactive(); return
    if args.predictions: list_predictions(); return
    if args.add_prediction: add_prediction_interactive(); return
    if args.resolve_prediction: resolve_prediction_interactive(); return
    if args.hypotheses: list_hypotheses(); return
    if args.add_hypothesis: add_hypothesis_interactive(); return
    if args.assets: list_assets(); return
    if args.add_asset: add_asset_interactive(); return
    if args.doctrine: list_doctrine(); return
    if args.add_doctrine: add_doctrine_interactive(); return
    if args.calibration_review: calibration_review_cmd(); return
    if args.decision_quality_review: decision_quality_review_cmd(); return
    if args.leverage_review: leverage_review_cmd(); return
    if args.constraint_review: constraint_review_cmd(); return
    if args.eighty_twenty_review: eighty_twenty_review_cmd(); return
    if args.bias_review: bias_review_cmd(); return
    if args.scorecard: scorecard_cmd(); return
    if args.red_team_review: red_team_review_cmd(); return
    if args.board_memo: board_memo_cmd(); return
    if args.kill_list: kill_list_cmd(); return
    if args.dashboard: dashboard(); return
    if args.monthly_review: monthly_review(days=args.days); return
    if args.weekly_review: weekly_review(days=args.days); return
    if args.antifragile_review: antifragile_review(); return
    if args.strategy_memo: strategy_memo(args.export); return
    if args.multi_agent_review: multi_agent_prompt(); return
    if args.ai_review: ai_review_prompt(); return

    if args.scenario:
        st=[Task("Write grant proposal",9,9,10,8,10,9,8,2,9,120,"grant_funding"),Task("Literature review",6,5,9,7,9,4,7,3,7,90,"research_publication"),Task("Lab meeting slides",5,8,4,3,5,8,6,3,4,45,"teaching_excellence",delegatable=True),Task("Industry partner email",7,6,8,6,8,5,7,2,3,20,"industry_collaboration"),Task("Admin cleanup",2,2,1,1,1,1,2,8,2,90,"admin_maintenance",delegatable=True)]
        scenario_mode(st,6.0,7); return

    want_json=args.json or args.export is not None; do_save=args.save_history
    if args.demo: result=demo(to_json=want_json,save_hist=do_save)
    else: result=interactive(to_json=want_json,save_hist=do_save)
    if want_json and result:
        jt=json.dumps(result,indent=2)
        if args.json:print(jt)
        if args.export:Path(args.export).write_text(jt+"\n");print(f"  [JSON saved to {args.export}]",file=sys.stderr)

if __name__=="__main__":main()
