#!/usr/bin/env python3
"""Chief of Staff Agent v8 — execution orchestration system (stdlib only).
Usage: python3 chief_of_staff_agent.py [MODE]
Core: --demo | --dashboard | --monthly-review | --weekly-review | --strategy-memo
V8:   --workflows | --run-workflow ID | --generate-sop | --project-playbook ID
      --queue | --add-to-queue | --queue-review | --compile-next-actions
      --graph | --graph-review | --execution-packet ID
      --draft-prompt TYPE | --prepare-meeting | --followups | --sprint-plan
      --startup | --shutdown | --asset-opportunities | --capture | --captures
      --context-prompt Q | --export-context Q [--redact]
      --dashboard-role ROLE | --one-page
V7:   --simulate | --tradeoff | --rhythm | --identity-review | --capital-review | --plan-30/90/365 | etc.
Other: --json | --export FILE | --save-history | --days N
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
# V7 — IDENTITY
# ======================================================================
def load_identities():
    data=load_records(IDENTITY_PATH);return[StrategicIdentity(**i)for i in data]if data else[]
def save_identities(ids):save_records(IDENTITY_PATH,[i.__dict__ for i in ids])

def add_identity_interactive():
    ids=load_identities()
    print("\n  ADD STRATEGIC IDENTITY");print("-"*40)
    stmt=input("  Statement: ").strip()
    print("  Identity roles:");roles=list(DEFAULT_IDENTITIES.keys())
    [print(f"    {i+1}. {r}")for i,r in enumerate(roles)]
    try:c=int(input("  Role (1-{0}): ".format(len(roles))));role=roles[c-1]
    except:role="world_class_researcher"
    i=StrategicIdentity(identity_id=uid(),name=stmt[:40],statement=stmt,role=role,long_term_aim=DEFAULT_IDENTITIES.get(role,""),last_reviewed=today_str())
    ids.append(i);save_identities(ids);print(f"  Identity added. ({i.identity_id})")

def list_identities():
    ids=load_identities()
    if not ids:print("  No identities. Use --add-identity.");return
    print(f"\n  STRATEGIC IDENTITIES ({len(ids)})");print(SEP)
    for i in ids:print(f"  {i.identity_id}  {i.name[:50]}  role:{i.role}  status:{i.status}")
    print(SEP)

# ======================================================================
# V7 — CAPITAL
# ======================================================================
def load_capitals():
    data=load_records(CAPITAL_PATH);return[StrategicCapital(**c)for c in data]if data else[]
def save_capitals(cs):save_records(CAPITAL_PATH,[c.__dict__ for c in cs])

def add_capital_interactive():
    cs=load_capitals()
    print("\n  ADD STRATEGIC CAPITAL");print("-"*40)
    print("  Capital types:");[print(f"    {i+1}. {t}")for i,t in enumerate(CAPITAL_TYPES)]
    try:c=int(input("  Type (1-{0}): ".format(len(CAPITAL_TYPES))));ct=CAPITAL_TYPES[c-1]
    except:ct="intellectual_capital"
    name=input("  Name: ").strip()
    score=_get_int("  Current score (1-10): ");c=StrategicCapital(capital_id=uid(),capital_type=ct,name=name,current_score=score,last_reviewed=today_str())
    cs.append(c);save_capitals(cs);print(f"  Capital '{name}' added.")

def list_capitals():
    cs=load_capitals()
    if not cs:print("  No capital entries. Use --add-capital.");return
    print(f"\n  STRATEGIC CAPITAL ({len(cs)})");print(SEP)
    for c in cs:print(f"  {c.capital_id}  {c.name:<30s}  type:{c.capital_type}  score:{c.current_score}")
    print(SEP)

# ======================================================================
# V7 — RHYTHM
# ======================================================================
def add_rhythm_interactive():
    rs=load_rhythms()
    print("\n  ADD OPERATING RHYTHM");print("-"*40)
    r=Rhythm(rhythm_id=uid(),name=input("  Name: ").strip(),cadence=input("  Cadence (daily/weekly/monthly/quarterly/yearly): ").strip(),description=input("  Description: ").strip(),trigger=input("  Trigger: ").strip(),expected_output=input("  Expected output: ").strip())
    rs.append(r);save_rhythms(rs);print(f"  Rhythm '{r.name}' added.")

def list_rhythms_cmd():
    rs=load_rhythms()
    if not rs:print("  No rhythms. Use --add-rhythm.");return
    print(f"\n  OPERATING RHYTHM ({len(rs)})");print(SEP)
    for r in rs:print(f"  {r.rhythm_id}  {r.name:<35s}  {r.cadence:<10s}  status:{r.status}")
    print(SEP)

def rhythm_review_cmd():
    rs=load_rhythms();rr=rhythm_review(rs)
    print(f"\n  RHYTHM REVIEW");print(SEP)
    print(f"  {rr['summary']}")
    if rr["overdue"]:
        print(f"\n  OVERDUE:")
        for o in rr["overdue"]:print(f"    - {o['name']} ({o['cadence']}): last done {o['last_completed']} ({o['days_overdue']} days)")
    print(SEP)

# ======================================================================
# V7 COMMANDS
# ======================================================================
def simulate_cmd(horizon=90):
    data={"config":load_config(),"records":load_recent_history(30),"projects":load_projects(),"risks":load_risks(),"outcomes":load_outcomes(),"opportunities":load_opps()}
    r=scenario_simulator(horizon,data)
    print(f"\n  STRATEGIC SCENARIO SIMULATOR — {horizon}-DAY HORIZON");print(SEP)
    for sr in r["scenarios"]:
        flag=" ★ BEST" if sr==r["best"] else""
        print(f"  {sr.path_name:<45s} Score:{sr.scenario_score}{flag}")
        print(f"    Alignment:{sr.strategic_alignment} Compounding:{sr.expected_compounding} OppCapture:{sr.opportunity_capture} RiskCtrl:{sr.risk_control} Feasibility:{sr.feasibility} Energy:{sr.energy_sustainability}")
        print(f"    Allocation: "+" ".join(f"{g}:{sr.planned_time_allocation.get(g,0)}%"for g in STRATEGIC_GOALS))
        print(f"    Bottleneck: {sr.likely_bottleneck} | Correction: {sr.recommended_correction}")
    print(SEP)
    best=r["best"]
    print(f"  BEST: {best.path_name} (score: {best.scenario_score})")
    print(f"  Reason: {best.recommended_correction}")
    # Extra warning for best path
    warnings=[]
    if best.planned_time_allocation.get("public_influence",0)<10:warnings.append("May under-invest in public influence.")
    if best.planned_time_allocation.get("deeptech_venture",0)<10:warnings.append("May under-invest in deep-tech venture work.")
    if best.risk_exposure>=7:warnings.append("Risk exposure is elevated.")
    if warnings:print(f"  Warning: {' '.join(warnings)}")
    print(SEP)

def tradeoff_cmd():
    print("\n  STRATEGIC TRADE-OFF ANALYSIS");print(SEP)
    a={"label":input("  Option A name: ").strip(),"expected_value":_get_int("    Expected value (1-10): "),"risk":_get_int("    Risk level (1-10, higher=riskier): "),"strategic_goal_served_score":_get_int("    Strategic goal alignment (1-10): "),"opportunity_cost":_get_int("    Opportunity cost (1-10, higher=more costly): "),"evidence_strength":_get_int("    Evidence strength (1-10): ")}
    print("  Reversibility:");[print(f"    {i+1}. {k}: {v}")for i,(k,v)in enumerate(REVERSIBILITY_CLASSES.items())]
    try:c=int(input("    Choice (1-3): "));a["reversibility_class"]=list(REVERSIBILITY_CLASSES.keys())[c-1]
    except:a["reversibility_class"]="two_way_door"
    a["uncertainty"]=input("    Uncertainty (low/medium/high): ").strip()or"medium"
    a["hidden_cost"]=input("    Hidden cost (optional): ").strip()
    b={"label":input("\n  Option B name: ").strip(),"expected_value":_get_int("    Expected value (1-10): "),"risk":_get_int("    Risk level (1-10): "),"strategic_goal_served_score":_get_int("    Strategic goal alignment (1-10): "),"opportunity_cost":_get_int("    Opportunity cost (1-10): "),"evidence_strength":_get_int("    Evidence strength (1-10): ")}
    try:c=int(input("    Reversibility (1-3, default 2): "));b["reversibility_class"]=list(REVERSIBILITY_CLASSES.keys())[c-1]
    except:b["reversibility_class"]="two_way_door"
    b["uncertainty"]=input("    Uncertainty (low/medium/high): ").strip()or"medium";b["hidden_cost"]=input("    Hidden cost (optional): ").strip()
    c_opt=None
    if _get_yn("\n  Add Option C? (y/n): "):
        c_opt={"label":input("  Option C name: ").strip(),"expected_value":_get_int("    Expected value (1-10): "),"risk":_get_int("    Risk level (1-10): "),"strategic_goal_served_score":_get_int("    Strategic goal alignment (1-10): "),"opportunity_cost":_get_int("    Opportunity cost (1-10): "),"evidence_strength":_get_int("    Evidence strength (1-10): "),"reversibility_class":"two_way_door","uncertainty":"medium","hidden_cost":""}
    r=tradeoff_engine(a,b,c_opt)
    print(f"\n  TRADE-OFF RESULTS");print(SEP)
    for o in r["options"]:
        print(f"  {o['option']}: {o['label']} (score: {o['score']})")
        print(f"    Value:{o['expected_value']} Risk:{o['risk']} OppCost:{o['opportunity_cost']} Evidence:{o['evidence_strength']} Reversibility:{o['reversibility_class']}")
    print(f"\n  {r['recommendation']}")
    print(f"  {r['what_would_change']}");print(SEP)

def identity_review_cmd():
    ids=load_identities()
    if not ids:
        print("\n  No identities defined. Creating defaults...")
        for role,aim in DEFAULT_IDENTITIES.items():
            ids.append(StrategicIdentity(identity_id=uid(),name=role.replace("_"," ").title(),statement=aim,role=role.replace("_"," ").title(),long_term_aim=aim,last_reviewed=today_str()))
        save_identities(ids);print(f"  Created {len(ids)} default identities.")
    records=load_recent_history(30);tasks=[];result=demo(to_json=True)
    if result:tasks=[Task(**t)for t in result.get("ranked",[])]
    r=identity_review(ids,records,tasks,[])
    print(f"\n  IDENTITY ALIGNMENT REVIEW");print(SEP)
    if r.get("message"):print(f"  {r['message']}");print(SEP);return
    for ident in r["identities"]:
        print(f"  [{ident['verdict'].upper()}] {ident['identity']} ({ident['role']})")
        if ident["alignment"]:[print(f"    + {a}")for a in ident["alignment"]]
        if ident["drift"]:[print(f"    - {d}")for d in ident["drift"]]
        if ident["corrections"]:[print(f"    → {c}")for c in ident["corrections"]]
    print(SEP)

def capital_review_cmd():
    cs=load_capitals();r=capital_review(cs)
    print(f"\n  STRATEGIC CAPITAL REVIEW");print(SEP)
    if r.get("message"):print(f"  {r['message']}");print(SEP);return
    print(f"  {r['summary']}")
    if r["top_3"]:
        print(f"\n  TOP 3 CAPITALS:");[print(f"    {c['name']} ({c['type']}): {c['score']}/10")for c in r["top_3"]]
    if r["decaying_details"]:
        print(f"\n  DECAYING CAPITALS:");[print(f"    {c['name']} ({c['type']}): {c['score']}/10 — Increase via: {c['how_to_increase']}")for c in r["decaying_details"]]
    if r["recommendations"]:print(f"\n  RECOMMENDATIONS:");[print(f"    - {rec}")for rec in r["recommendations"]]
    print(SEP)

def plan_cmd(horizon):
    data=gather_all_data();r=plan_generator(horizon,data)
    print(f"\n  {horizon}-DAY STRATEGIC PLAN");print(SEP)
    print(f"  THESIS: {r['strategic_thesis']}")
    sections=[("OUTCOMES","top_outcomes"),("PROJECTS TO PROTECT","projects_to_protect"),("OPPORTUNITIES","opportunities_to_pursue"),("RELATIONSHIPS","relationships_to_strengthen"),("ASSETS TO BUILD","assets_to_build"),("RISKS TO MITIGATE","risks_to_mitigate"),("ASSUMPTIONS TO TEST","assumptions_to_test"),("EXPERIMENTS","experiments_to_run"),("KILL-LIST","kill_list_items"),("SUCCESS METRICS","success_metrics")]
    for label,key in sections:
        items=r.get(key,[])
        if items:print(f"\n  {label}:");[print(f"    - {item}")for item in items[:5]]
    print(SEP)

def backcast_cmd():
    print("\n  STRATEGIC BACKCASTING");print(SEP)
    outcome=input("  Desired outcome: ").strip();target=input("  Target date (YYYY-MM-DD): ").strip()
    why=input("  Why it matters: ").strip();metric=input("  Success metric: ").strip()
    r=backcast_generator(outcome,target,why,metric)
    print(f"\n  BACKCAST: {outcome}");print(SEP)
    print(f"  Target: {r['target_date']} ({r['total_months']} months)")
    print(f"  Success metric: {r['success_metric']}")
    print(f"\n  MILESTONES:");[print(f"    {m}")for m in r["milestones"]]
    print(f"\n  WEEKLY RHYTHM: {r['required_weekly_rhythm']}")
    print(f"\n  LEADING INDICATORS:");[print(f"    - {li}")for li in r["leading_indicators"]]
    print(f"\n  RISKS:");[print(f"    - {risk}")for risk in r["risks"]]
    print(f"\n  FIRST ACTION: {r['first_next_action']}");print(SEP)

def okr_review_cmd():
    os=load_okrs();r=okr_review(os)
    print(f"\n  OKR REVIEW");print(SEP)
    if r.get("message"):print(f"  {r['message']}");print(SEP);return
    print(f"  {r['summary']}")
    for obj in r["objectives"]:
        print(f"\n  {obj['objective']} ({obj['period']}) — {obj['avg_progress']:.0f}% progress")
        for kr in obj["key_results"]:
            flag="⚠ BLOCKED" if kr["status"]=="blocked" else("◈ AT RISK" if kr["status"]=="at_risk" else"✓")
            print(f"    {flag} {kr['description'][:60]}: {kr['progress']:.0f}%")
        if obj["blocked_count"]:print(f"    → {obj['next_action']}")
    print(SEP)

def add_okr_interactive():
    os=load_okrs()
    print("\n  ADD OKR");print("-"*40)
    o=OKR(objective_id=uid(),title=input("  Objective: ").strip(),start_date=today_str())
    print("  Strategic goals:");[print(f"    {i+1}. {g}")for i,g in enumerate(STRATEGIC_GOALS)]
    try:c=int(input("  Goal (1-7): "));o.strategic_goal=STRATEGIC_GOALS[c-1]
    except:pass
    o.period=input("  Period (monthly/quarterly/yearly): ").strip()or"quarterly"
    o.end_date=(date.today()+timedelta(days=90)).isoformat()
    o.confidence=_get_int("  Confidence (1-10): ")
    print("  Key results (enter blank description to finish):")
    while True:
        desc=input("    KR description: ").strip()
        if not desc:break
        tgt=float(input("    Target value: ").strip()or"100")
        kr=KeyResult(kr_id=uid(),description=desc,target_value=tgt,start_value=0,last_updated=today_str())
        o.key_results.append(kr)
    os.append(o);save_okrs(os);print(f"  OKR '{o.title}' added.")

def list_okrs_cmd():
    os=load_okrs()
    if not os:print("  No OKRs. Use --add-okr.");return
    print(f"\n  OKRs ({len(os)})");print(SEP)
    for o in os:
        kr_count=len(o.key_results)if isinstance(o.key_results,list)else 0
        print(f"  {o.objective_id}  {o.title[:50]}  goal:{o.strategic_goal}  period:{o.period}  KRs:{kr_count}  status:{o.status}")
    print(SEP)

def rebalance_cmd():
    records=load_recent_history(30);cfg=load_config();okrs=load_okrs();capitals=load_capitals()
    r=rebalance_engine(records,cfg,okrs,[],capitals)
    print(f"\n  PORTFOLIO REBALANCE");print(SEP)
    print(f"  {r['summary']}")
    if r["adjustments"]:
        print(f"\n  RECOMMENDED ADJUSTMENTS:")
        for a in r["adjustments"]:print(f"    - {a['action']}")
    print(f"\n  ALLOCATION vs BASELINE:");print(f"  {'Goal':<28s} {'Actual':>7s} {'Target':>7s} {'Gap':>7s}")
    for g in STRATEGIC_GOALS:
        actual=r["actual_allocation"].get(g,0);target=r["baseline"].get(g,15);gap=round(actual-target,1)
        print(f"  {g:<28s} {actual:>6.1f}% {target:>6d}% {gap:>+6.1f}%")
    print(SEP)

def integrity_check_cmd():
    r=integrity_check()
    print(f"\n  DATA INTEGRITY CHECK");print(SEP)
    print(f"  {r['summary']}")
    if r["issues"]:[print(f"    - {i}")for i in r["issues"]]
    if r["total_issues"]>0:print(f"\n  Run --repair-integrity to fix safe issues.")
    print(SEP)

def repair_integrity_cmd():
    r=repair_integrity()
    print(f"\n  INTEGRITY REPAIR");print(SEP)
    print(f"  {r['summary']}")
    if r["repairs"]:[print(f"    - {rp}")for rp in r["repairs"]]
    print(SEP)

def search_cmd(query):
    r=local_search(query)
    print(f"\n  SEARCH: '{query}'");print(SEP)
    print(f"  {r['summary']}")
    for i,res in enumerate(r["results"],1):print(f"  {i}. [{res['store']}] {res['match']}")
    print(SEP)

def report_pack_cmd():
    r=generate_report_pack()
    print(f"\n  REPORT PACK GENERATED");print(SEP)
    print(f"  Directory: {r['export_dir']}")
    print(f"  Files ({r['count']}):")
    for f in r["files"]:print(f"    - {f}")
    print(SEP)

def ai_council_cmd():
    print(ai_council_prompt())

def migrate_cmd():
    r=migrate_all_stores()
    print(f"\n  MIGRATION V6 → V7");print(SEP)
    print(f"  {r['summary']}")
    for store,status in r["results"].items():print(f"    {store}: {status}")
    print(SEP)

# ======================================================================
# V8 — EXECUTION ORCHESTRATION
# ======================================================================
def workflows_cmd():
    wfs=load_workflows()
    print(f"\n  EXECUTION WORKFLOWS ({len(wfs)})");print(SEP)
    for w in wfs:print(f"  {w.workflow_id}  {w.name:<45s}  {w.category:<20s}  {w.estimated_total_minutes}min")
    print(SEP)

def add_workflow_cmd():
    print("\n  ADD WORKFLOW");print("-"*40)
    print("  Categories:");[print(f"    {i+1}. {c}")for i,c in enumerate(WORKFLOW_CATEGORIES)]
    try:cat_idx=int(input("  Category (1-{0}): ".format(len(WORKFLOW_CATEGORIES))));cat=WORKFLOW_CATEGORIES[cat_idx-1]
    except:cat="research_workflow"
    print("  Strategic goals:");[print(f"    {i+1}. {g}")for i,g in enumerate(STRATEGIC_GOALS)]
    try:sg_idx=int(input("  Goal (1-7): "));sg=STRATEGIC_GOALS[sg_idx-1]
    except:sg="research_publication"
    w=Workflow(workflow_id=uid(),name=input("  Name: ").strip(),category=cat,strategic_goal=sg,description=input("  Description: ").strip(),trigger=input("  Trigger: ").strip())
    print("  Steps (enter blank line to finish):")
    while True:
        step=input("    Step: ").strip()
        if not step:break
        w.steps.append(step)
    w.expected_output=input("  Expected output: ").strip()
    try:w.estimated_total_minutes=int(input("  Estimated minutes: ").strip()or"60")
    except:w.estimated_total_minutes=60
    wfs=load_workflows();wfs.append(w);save_workflows(wfs);print(f"  Workflow '{w.name}' added.")

def run_workflow_cmd(wf_id):
    r=run_workflow(wf_id)
    if not r:print(f"  Workflow '{wf_id}' not found.");return
    w=r["workflow"]
    print(f"\n  RUN WORKFLOW: {w.name}");print(SEP)
    print(f"  Description: {w.description}")
    print(f"  Estimated: {r['estimated_minutes']} minutes")
    print(f"\n  INPUTS REQUIRED:")
    for inp in r["inputs"]:print(f"    - {inp}")
    print(f"\n  STEPS:")
    for step in r["steps"]:print(f"    {step}")
    print(f"\n  EXPECTED OUTPUT: {r['expected_output']}")
    print(SEP)

def sop_cmd(template=None, export_path=None):
    if template:
        r=generate_sop(template)
        if r["sop"]:
            sop=r["sop"];print(f"\n  SOP: {sop['title']}");print(SEP)
            for k in ["purpose","when_to_use","inputs","steps","quality_checklist","common_mistakes","definition_of_done"]:
                val=sop.get(k,"")
                if isinstance(val,list):val=", ".join(val)
                print(f"  {k.replace('_',' ').upper()}: {val}")
            print(SEP)
            if export_path:Path(export_path).write_text("\n".join(f"{k}: {v}" for k,v in sop.items()));print(f"  Exported to {export_path}")
    else:
        r=generate_sop();print(f"\n  AVAILABLE SOP TEMPLATES:");[print(f"    - {t}")for t in r["templates"]]
        print(f"  Use --generate-sop --export TEMPLATE_NAME to generate one.")

def playbook_cmd(project_id, export_path=None):
    projs=load_projects();proj=next((p for p in projs if p.project_id==project_id),None)
    if not proj:print(f"  Project '{project_id}' not found.");return
    opps=load_opps();risks=load_risks();assets=load_assets();rels=load_relationships();decs=load_decisions()
    pb=project_playbook(proj,opps,risks,assets,rels,decs)
    print(f"\n  PROJECT PLAYBOOK: {pb['project_name']}");print(SEP)
    for k,v in pb.items():
        if k in ("project_id","project_name","status"):continue
        if isinstance(v,list):print(f"\n  {k.upper()}:");[print(f"    - {item}")for item in v]
        else:print(f"  {k.replace('_',' ').upper()}: {v}")
    print(SEP)
    if export_path:
        lines=[f"{k}: {v}"for k,v in pb.items()];Path(export_path).write_text("\n".join(lines));print(f"  Exported to {export_path}")

def queue_cmd():
    qs=load_queue();qr=queue_review()
    print(f"\n  EXECUTION QUEUE");print(SEP)
    print(f"  {qr['summary']}")
    if qr["top_3"]:
        print(f"\n  TOP 3:")
        for q in qr["top_3"]:print(f"    [{q.status}] {q.title[:60]} (priority:{q.priority_score}, {q.estimated_minutes}min)")
    if qr["quick_wins"]:print(f"\n  QUICK WINS: {len(qr['quick_wins'])} items <= 20 min")
    if qr["deep_work"]:print(f"\n  DEEP WORK: {len(qr['deep_work'])} items >= 60 min")
    if qr["blocked_items"]:print(f"\n  BLOCKED: {[q.title[:40] for q in qr['blocked_items']]}")
    if qr["stale"]:print(f"\n  STALE: {len(qr['stale'])} items not updated in 14+ days")
    print(SEP)

def add_to_queue_cmd():
    print("\n  ADD TO QUEUE");print("-"*40)
    title=input("  Title: ").strip();st=input("  Source type (task/project/opportunity): ").strip()or"task"
    sid=input("  Source ID (optional): ").strip();sg=input("  Strategic goal (optional): ").strip()
    try:pri=int(input("  Priority (1-10, default 5): ").strip()or"5")
    except:pri=5
    try:mins=int(input("  Estimated minutes (default 30): ").strip()or"30")
    except:mins=30
    q=add_to_queue(title,st,sid,sg,pri,mins);print(f"  Queued. ({q.queue_id})")

def complete_queue_item_cmd(qid):
    qs=load_queue()
    for i,q in enumerate(qs):
        if q.queue_id==qid or q.title.lower().startswith(qid.lower()):
            qs[i].status="completed";qs[i].updated_at=today_str();save_queue(qs)
            print(f"  Item '{q.title[:50]}' marked completed.");return
    print(f"  Queue item '{qid}' not found.")

def compile_next_actions_cmd():
    projs=load_projects();opps=load_opps();risks=load_risks();rels=load_relationships()
    decs=load_decisions();exps=load_experiments();okrs=load_okrs();outs=load_outcomes();wfs=load_workflows()
    r=compile_next_actions(projs,opps,risks,rels,decs,exps,okrs,outs,wfs)
    print(f"\n  NEXT-ACTION COMPILER");print(SEP)
    print(f"  {r['summary']}")
    for m in r["missing_actions"]:print(f"    [{m['source']}] {m['name'][:50]}: {m['issue']}")
    print(SEP)

def graph_cmd():
    r=graph_review()
    print(f"\n  STRATEGIC KNOWLEDGE GRAPH");print(SEP)
    print(f"  {r['summary']}")
    if r.get("most_depended"):
        print(f"\n  MOST DEPENDED-ON:");[print(f"    {m['id']} ({m['type']}): {m['deps']} deps")for m in r["most_depended"]]
    if r.get("disconnected_count",0)>0:
        print(f"\n  DISCONNECTED: {r['disconnected_count']}")
        for d in r.get("disconnected",[]):print(f"    {d['id']} ({d['type']}): {d['name']}")
    print(SEP)

def graph_entity_cmd(entity_id):
    r=graph_entity(entity_id)
    if not r:print(f"  Entity '{entity_id}' not found in graph.");return
    e=r["entity"]
    print(f"\n  GRAPH ENTITY: {e['id']}");print(SEP)
    print(f"  Type: {e['type']}");print(f"  Labels: {e['labels']}")
    print(f"  Edges ({len(r['edges'])}):");[print(f"    {edg['source'][:8]} --[{edg['type']}]--> {edg['target'][:8]}")for edg in r["edges"]]
    print(SEP)

def execution_packet_cmd(item_id):
    p=execution_packet(item_id)
    if not p:print(f"  No execution packet for '{item_id}'.");return
    print(f"\n  EXECUTION PACKET: {p['title']}");print(SEP)
    for k,v in p.items():
        if k=="title":continue
        if isinstance(v,list):print(f"\n  {k.upper()}:");[print(f"    {i+1}. {s}")for i,s in enumerate(v)]
        else:print(f"  {k.replace('_',' ').upper()}: {v}")
    print(SEP)

def draft_prompt_cmd(prompt_type):
    print(draft_prompt(prompt_type))

def prepare_meeting_cmd():
    print("\n  MEETING PREPARATION");print(SEP)
    title=input("  Meeting title: ").strip();person=input("  Person/organization: ").strip()
    print("  Meeting types:");[print(f"    {i+1}. {t}")for i,t in enumerate(MEETING_TYPES)]
    try:c=int(input("  Type (1-{0}): ".format(len(MEETING_TYPES))));mt=MEETING_TYPES[c-1]
    except:mt="research_collaboration"
    goal=input("  Strategic goal: ").strip();outcome=input("  Desired outcome: ").strip()
    context=input("  Known context: ").strip()
    r=prepare_meeting(title,person,mt,goal,outcome,context)
    print(f"\n  MEETING BRIEF: {r['title']}");print(SEP)
    for k,v in r.items():
        if k=="title":continue
        if isinstance(v,list):print(f"  {k.replace('_',' ').upper()}:");[print(f"    - {item}")for item in v]
        else:print(f"  {k.replace('_',' ').upper()}: {v}")
    print(SEP)

def followups_cmd(prompts=False):
    r=followup_review()
    print(f"\n  FOLLOW-UP REVIEW");print(SEP)
    print(f"  {r['summary']}")
    for f in r["followups"][:10]:
        print(f"    [{f['source']}] {f['name'][:50]}: {f.get('days_since','?')} days since last contact")
    if prompts and r["followups"]:
        print(f"\n  FOLLOW-UP PROMPTS:")
        for f in r["followups"][:3]:
            print(f"\n  To: {f['name']}");print(f"  Subject: Following up on our discussion");print(f"  Body: [Personalized follow-up referencing {f['source']}]")
    print(SEP)

def sprint_plan_cmd():
    okrs=load_okrs();projs=load_projects();queue=load_queue();opps=load_opps();risks=load_risks()
    cfg=load_config();rels=load_relationships()
    r=sprint_planner(okrs,projs,queue,opps,risks,cfg,rels)
    print(f"\n  WEEKLY SPRINT PLAN");print(SEP)
    for k,v in r.items():
        if isinstance(v,list):print(f"  {k.replace('_',' ').upper()}:");[print(f"    - {item}")for item in v]
        else:print(f"  {k.replace('_',' ').upper()}: {v}")
    print(SEP)

def startup_cmd():
    queue=load_queue();projs=load_projects();risks=load_risks()
    r=startup_ritual(queue,projs,risks)
    print(f"\n  DAILY STARTUP");print(SEP)
    print(f"  TODAY'S OBJECTIVE: {r['top_objective']}")
    print(f"  RISKS TO AVOID TODAY: {', '.join(r['risks_to_avoid']) if r['risks_to_avoid'] else 'none'}")
    print(f"  ONE THING NOT TO DO: {r['one_thing_not_to_do']}")
    print(f"\n  FIRST 30 MINUTES:")
    print(f"  {r['first_30_minutes']}")
    if r["first_packet"]:
        p=r["first_packet"];steps=p.get("steps",[])
        print(f"\n  FIRST EXECUTION PACKET: {p['title']}")
        if steps:print(f"  Steps:");[print(f"    {i+1}. {s}")for i,s in enumerate(steps)]
    print(SEP)

def shutdown_cmd():
    r=shutdown_ritual()
    print(f"\n  SHUTDOWN COMPLETE — {r['date']}");print(SEP)
    print(f"  Completed: {r['completed']}");print(f"  Delayed: {r['delayed']}")
    print(f"  Unexpected: {r['unexpected']}");print(f"  Evidence: {r['evidence_created']}")
    print(f"  Queued for tomorrow: {r['queued_for_tomorrow']}");print(f"  Lesson: {r['lesson']}")
    print(SEP)

def asset_opportunities_cmd():
    records=load_recent_history(30);projs=load_projects();assets=load_assets();wfs=load_workflows()
    r=asset_opportunities(records,projs,assets,wfs)
    print(f"\n  ASSET CREATION OPPORTUNITIES");print(SEP)
    print(f"  {r['summary']}")
    for rec in r["recommendations"]:print(f"    - {rec}")
    print(SEP)

def capture_cmd():
    print("\n  KNOWLEDGE CAPTURE");print(SEP)
    print("  Types:");[print(f"    {i+1}. {t}")for i,t in enumerate(CAPTURE_TYPES)]
    try:c=int(input("  Type (1-{0}): ".format(len(CAPTURE_TYPES))));ct=CAPTURE_TYPES[c-1]
    except:ct="idea"
    title=input("  Title: ").strip();content=input("  Content: ").strip()
    goal=input("  Related strategic goal (optional): ").strip()
    pid=input("  Linked project ID (optional): ").strip()
    tags=input("  Tags (comma-separated, optional): ").strip()
    cap=add_capture_interactive_core(ct,title,content,goal,pid,tags)
    print(f"  Captured. ({cap.capture_id})")

def list_captures_cmd():
    cs=load_captures()
    if not cs:print("  No captures. Use --capture.");return
    print(f"\n  KNOWLEDGE CAPTURES ({len(cs)})");print(SEP)
    for c in cs:print(f"  {c.capture_id}  [{c.type}] {c.title[:50]}  {c.date}")
    print(SEP)

def context_prompt_cmd(query,redact=False):
    print(context_prompt(query,redact))

def export_context_cmd(query,redact=False):
    print(context_prompt(query,redact))

def role_dashboard_cmd(role):
    r=role_dashboard(role)
    print(f"\n  {role.upper()} DASHBOARD");print(SEP)
    for k,v in r.items():
        if k in ("role","strategic_goals"):continue
        if isinstance(v,list):print(f"\n  {k.upper()}:");[print(f"    - {item}")for item in v[:5]]
    print(SEP)

def one_page_cmd():
    r=one_page()
    print(f"\n  ONE-PAGE STRATEGIC OVERVIEW — {today_str()}");print(SEP)
    for k,v in r.items():print(f"  {k.replace('_',' ').upper()}: {v}")
    print(SEP)

# ======================================================================
# V9 — PERFORMANCE MEASUREMENT
# ======================================================================
def metrics_list_cmd():
    ms=load_metrics()
    if not ms:print("  No metrics. Use --add-metric.");return
    print(f"\n  METRICS ({len(ms)})");print(SEP)
    for m in ms:print(f"  {m.metric_id}  {m.name[:40]}  target:{m.target_value}  current:{m.current_value}  {m.unit}")
    print(SEP)

def add_metric_cmd():
    print("\n  ADD METRIC");print("-"*40)
    print("  Categories:");[print(f"    {i+1}. {c}")for i,c in enumerate(METRIC_CATEGORIES)]
    try:c=int(input("  Category (1-{0}): ".format(len(METRIC_CATEGORIES))));cat=METRIC_CATEGORIES[c-1]
    except:cat="execution_quality"
    print("  Strategic goals:");[print(f"    {i+1}. {g}")for i,g in enumerate(STRATEGIC_GOALS)]
    try:sg_idx=int(input("  Goal (1-7): "));sg=STRATEGIC_GOALS[sg_idx-1]
    except:sg="research_publication"
    m=Metric(metric_id=uid(),name=input("  Name: ").strip(),strategic_goal=sg,category=cat,description=input("  Description: ").strip(),unit=input("  Unit (e.g., hours, count): ").strip(),target_value=float(input("  Target value: ").strip()or"1"),last_updated= today_str())
    ms=load_metrics();ms.append(m);save_metrics(ms);print(f"  Metric '{m.name}' added.")

def metrics_review_cmd():
    r=metrics_review()
    if r.get("message"):print(f"  {r['message']}");return
    print(f"\n  METRICS REVIEW");print(SEP);print(f"  {r['summary']}")
    for m in r["latest"]:print(f"    {m['name'][:45]}  {m['current']}/{m['target']} {m['unit']}")
    print(SEP)

def impact_list_cmd():
    imps=load_impacts()
    if not imps:print("  No impacts. Use --add-impact.");return
    print(f"\n  IMPACT LEDGER ({len(imps)})");print(SEP)
    for i in imps:print(f"  {i.impact_id}  [{i.impact_type}] {i.title[:50]}  magnitude:{i.magnitude}")
    print(SEP)

def add_impact_cmd():
    print("\n  ADD IMPACT");print("-"*40)
    print("  Impact types:");[print(f"    {i+1}. {t}")for i,t in enumerate(IMPACT_TYPES)]
    try:it=int(input("  Type (1-{0}): ".format(len(IMPACT_TYPES))));impact_type=IMPACT_TYPES[it-1]
    except:impact_type="paper_submitted"
    imp=Impact(impact_id=uid(),date=today_str(),title=input("  Title: ").strip(),strategic_goal=input("  Strategic goal: ").strip(),impact_type=impact_type,description=input("  Description: ").strip(),magnitude=int(input("  Magnitude (1-10): ").strip()or"5"),confidence=int(input("  Confidence (1-10): ").strip()or"5"))
    imps=load_impacts();imps.append(imp);save_impacts(imps);print(f"  Impact '{imp.title[:40]}' recorded.")

def impact_review_cmd():
    r=impact_review()
    if r.get("message"):print(f"  {r['message']}");return
    print(f"\n  IMPACT REVIEW");print(SEP);print(f"  {r['summary']}")
    if r["top_3"]:[print(f"    [{i['type']}] {i['title'][:50]} (magnitude:{i['magnitude']})")for i in r["top_3"]]
    print(SEP)

def roi_review_cmd():
    projs=load_projects();wfs=load_workflows();rels=load_relationships()
    opps=load_opps();assets=load_assets();ms=load_metrics()
    r=roi_review(projs,wfs,rels,opps,assets,ms)
    print(f"\n  STRATEGIC ROI REVIEW");print(SEP)
    print(f"  Analyzed: {r['total_analyzed']} items");print(f"  {r['summary']}")
    if r["high_roi"]:
        print(f"\n  HIGHEST ROI:");[print(f"    [{i['type']}] {i['name'][:45]}  ROI:{i['roi']}")for i in r["high_roi"]]
    if r["low_roi"]:
        print(f"\n  LOWEST ROI:");[print(f"    [{i['type']}] {i['name'][:45]}  ROI:{i['roi']}")for i in r["low_roi"]]
    print(SEP)

def workflow_performance_cmd():
    r=workflow_performance()
    if r.get("message"):print(f"  {r['message']}");return
    print(f"\n  WORKFLOW PERFORMANCE");print(SEP);print(f"  {r['summary']}")
    for w in r["workflows"]:print(f"    {w['workflow'][:45]}  runs:{w['runs']}  complete:{w['completion_rate']}%  quality:{w['avg_quality']}  est.error:{w['estimation_error_pct']}%")
    print(SEP)

def log_workflow_run_cmd():
    wfs=load_workflows();print("\n  LOG WORKFLOW RUN");print("-"*40)
    for i,w in enumerate(wfs):print(f"    {i+1}. {w.name}")
    try:idx=int(input("  Workflow (1-{0}): ".format(len(wfs))))-1;wf=wfs[idx]
    except:print("  Invalid selection.");return
    est=int(input("  Estimated minutes: ").strip()or"60");act=int(input("  Actual minutes: ").strip()or"60")
    comp=input("  Completed? (y/n): ").strip().lower()=="y";out=input("  Output created: ").strip()
    qual=int(input("  Quality (1-10): ").strip()or"5")
    wr=log_workflow_run(wf.workflow_id,est,act,comp,out,qual);print(f"  Run logged. ({wr.run_id})")

def estimate_review_cmd():
    r=estimate_review()
    if r.get("message"):print(f"  {r['message']}");return
    print(f"\n  ESTIMATION ACCURACY");print(SEP)
    print(f"  Time error: {r['avg_time_error_pct']}%");print(f"  Prob error: {r['avg_prob_error']}")
    if r["correction"]:print(f"\n  CORRECTION: {r['correction']}")
    print(SEP)

def reforecast_cmd():
    okrs=load_okrs();ms=load_metrics();preds=load_predictions();ests=load_estimates();queue=load_queue()
    r=reforecast(okrs,ms,preds,ests,queue)
    print(f"\n  REFORECAST REVIEW");print(SEP);print(f"  {r['summary']}")
    for f in r["forecasts"]:print(f"    [{f['entity']}] {f['name'][:50]}: {f['original_confidence']} → {f['adjusted_confidence']} | {f['reason']}")
    print(SEP)

def velocity_review_cmd():
    records=load_recent_history(90);queue=load_queue();impact=load_impacts()
    wrs=load_workflow_runs();ests=load_estimates()
    r=velocity_review(records,queue,impact,wrs,ests)
    if r.get("message"):print(f"  {r['message']}");return
    print(f"\n  PROGRESS VELOCITY");print(SEP)
    for k,v in r.items():
        if k in ("message","summary"):continue
        print(f"  {k.replace('_',' ').upper()}: {v}")
    print(SEP)

def indicators_cmd():
    inds=load_indicators()
    print(f"\n  INDICATORS ({len(inds)})");print(SEP)
    for i in inds:
        tag="⚠" if i.current_value <= i.warning_threshold else "✓"
        print(f"  {tag} [{i.indicator_type}] {i.name[:40]}  {i.current_value}/{i.target_value}  ({i.strategic_goal})")
    print(SEP)

def indicator_review_cmd():
    r=indicator_review()
    print(f"\n  INDICATOR REVIEW");print(SEP);print(f"  {r['summary']}")
    if r["warnings"]:[print(f"    [{w['goal']}] {w['name'][:40]}: {w['current']} (warning at {w['warning']})")for w in r["warnings"]]
    print(SEP)

def review_board_cmd():
    data={"projects":load_projects(),"workflows":load_workflows(),"relationships":load_relationships(),
          "opportunities":load_opps(),"assets":load_assets(),"metrics":load_metrics(),
          "records":load_recent_history(90),"queue":load_queue(),"impact":load_impacts(),
          "workflow_runs":load_workflow_runs(),"estimates":load_estimates(),
          "okrs":load_okrs(),"predictions":load_predictions(),"risks":load_risks()}
    r=review_board(data)
    print(f"\n  STRATEGIC REVIEW BOARD — {today_str()}");print(SEP)
    print(f"  THESIS: {r['strategic_thesis']}")
    print(f"  METRICS: {r['metrics'].get('summary','')}")
    print(f"  IMPACT: {r['impact'].get('summary','')}")
    print(f"  ROI: {r['roi'].get('summary','')}")
    print(f"  VELOCITY: {r['velocity'].get('summary','')}")
    print(f"  INDICATORS: {r['indicators'].get('summary','')}")
    print(f"  REFORECAST: {r['reforecast'].get('summary','')}")
    print(f"\n  TOP RISKS: {', '.join(r['top_risks'][:3]) if r['top_risks'] else 'none'}")
    print(f"  RECOMMENDED DECISIONS:");[print(f"    - {d}")for d in r['recommended_decisions'] if d]
    print(SEP)

def contracts_cmd():
    cs=load_contracts()
    if not cs:print("  No contracts. Use --add-contract.");return
    print(f"\n  ACCOUNTABILITY CONTRACTS ({len(cs)})");print(SEP)
    for c in cs:print(f"  {c.contract_id}  {c.title[:45]}  goal:{c.strategic_goal}  status:{c.status}")
    print(SEP)

def add_contract_cmd():
    print("\n  ADD CONTRACT");print("-"*40)
    c=Contract(contract_id=uid(),title=input("  Title: ").strip(),strategic_goal=input("  Strategic goal: ").strip(),commitment=input("  Commitment: ").strip(),start_date=today_str(),end_date=input("  End date (YYYY-MM-DD): ").strip(),success_metric=input("  Success metric: ").strip(),minimum_standard=input("  Minimum standard: ").strip(),stretch_standard=input("  Stretch standard (optional): ").strip(),consequence_if_missed=input("  Consequence if missed: ").strip(),reward_if_completed=input("  Reward if completed: ").strip(),review_date=input("  Review date (YYYY-MM-DD): ").strip())
    cs=load_contracts();cs.append(c);save_contracts(cs);print(f"  Contract '{c.title[:40]}' created.")

def contract_review_cmd():
    r=contract_review()
    if r.get("message"):print(f"  {r['message']}");return
    print(f"\n  CONTRACT REVIEW");print(SEP);print(f"  {r['summary']}")
    for c in r["latest"]:print(f"    {c['title'][:50]} [{c['status']}]")
    print(SEP)

def adherence_review_cmd():
    rhythms=load_rhythms();contracts=load_contracts();doctrine=load_doctrine()
    okrs=load_okrs();records=load_recent_history(14)
    r=adherence_review(rhythms,contracts,doctrine,okrs,records)
    print(f"\n  BEHAVIORAL ADHERENCE REVIEW");print(SEP)
    print(f"  Score: {r['adherence_score']}/100")
    print(f"  Strong: {', '.join(r['strengths']) if r['strengths'] else 'none'}")
    print(f"  Weak: {', '.join(r['weaknesses']) if r['weaknesses'] else 'none'}")
    print(f"  Details:");[print(f"    {k}: {v}/target")for k,v in r['details'].items()]
    print(SEP)

def rubrics_cmd():
    rbs=load_rubrics()
    print(f"\n  QUALITY RUBRICS ({len(rbs)})");print(SEP)
    for r in rbs:print(f"  {r.rubric_id}  {r.name}  ({r.output_type})")
    print(SEP)

def score_output_cmd():
    rbs=load_rubrics();print("\n  SCORE OUTPUT");print(SEP)
    for i,r in enumerate(rbs):print(f"    {i+1}. {r.name}")
    try:idx=int(input("  Rubric (1-{0}): ".format(len(rbs))))-1;rb=rbs[idx]
    except:print("  Invalid.");return
    title=input("  Output title: ").strip();scores=[]
    for crit in rb.criteria:
        try:s=float(input(f"  {crit} (1-10): ").strip());scores.append(s)
        except:scores.append(5)
    os=score_output(title,rb.output_type,rb.rubric_id,scores)
    oss=load_output_scores();oss.append(os);save_output_scores(oss)
    print(f"  Scored: {os.overall_score}/10")

def attribution_review_cmd():
    imps=load_impacts();projs=load_projects();wfs=load_workflows()
    rels=load_relationships();assets=load_assets()
    r=attribution_review(imps,projs,wfs,rels,assets)
    print(f"\n  OUTCOME ATTRIBUTION REVIEW");print(SEP)
    if r.get("message"):print(f"  {r['message']}");return
    for i in r["results"]:
        print(f"  [{i['type']}] {i['title'][:50]} (magnitude:{i['magnitude']})")
        print(f"    Attributions: {', '.join(i['attributions'])}")
        print(f"    Recommendation: {i['recommendation']}")
    print(SEP)

def flywheel_review_cmd():
    imps=load_impacts();projs=load_projects();rels=load_relationships()
    assets=load_assets();evidence=load_evidence()
    r=flywheel_review(imps,projs,rels,assets,evidence)
    print(f"\n  STRATEGIC FLYWHEEL REVIEW");print(SEP);print(f"  {r['summary']}")
    for f in r["flywheels"]:print(f"\n  FLYWHEEL: {f['flywheel']}\n    Evidence: {f['evidence']}\n    Next: {f['recommendation']}")
    print(SEP)

def decay_review_cmd():
    rels=load_relationships();projs=load_projects();assets=load_assets()
    assumps=load_assumptions();preds=load_predictions();risks=load_risks()
    wfs=load_workflows();okrs=load_okrs()
    r=decay_review(rels,projs,assets,assumps,preds,risks,wfs,okrs)
    print(f"\n  STRATEGIC DECAY DETECTOR");print(SEP);print(f"  {r['summary']}")
    for d in r["decay_items"][:10]:print(f"    [{d['type']}] {d['name'][:50]}: {d['issue']}")
    print(SEP)

def rebalance_optimized_cmd():
    try:ah=float(input("  Available hours per week: ").strip()or"25")
    except:ah=25
    try:energy=int(input("  Energy level (1-10): ").strip()or"7")
    except:energy=7
    cfg=load_config();okrs=load_okrs();rels=load_relationships()
    contracts=load_contracts();queue=load_queue();risks=load_risks()
    r=rebalance_optimized(ah,energy,cfg,okrs,rels,contracts,queue,risks)
    print(f"\n  OPTIMIZED REBALANCE");print(SEP)
    print(f"  Total hours: {r['total_hours']} | Energy: {r['energy_level']}/10")
    print(f"\n  RECOMMENDED ALLOCATION:")
    for g,h in r["allocation"].items():print(f"    {g}: {h:.1f} hours")
    print(f"\n  CONSTRAINTS: {r['constraints']}")
    if r["recommendations"]:print(f"\n  RECOMMENDATIONS:");[print(f"    - {rec}")for rec in r["recommendations"]]
    print(SEP)

def export_csv_cmd(store_name):
    r=export_csv(store_name, None)
    if r.get("error"):print(f"  Error: {r['error']}");return
    print(f"  Exported: {r['exported']} ({r['records']} records)")

def import_csv_cmd(store_name, path):
    r=import_csv(store_name, path)
    if r.get("error"):print(f"  Error: {r['error']}");return
    print(f"  Imported: {r['imported']} records into {r['store']} (total: {r['total_records']})")

def ai_performance_review_cmd():
    print(ai_performance_review_prompt())

# ======================================================================
# V10 — STRATEGIC AUTONOMY & GOVERNANCE
# ======================================================================
def commands_cmd():
    cs=load_commands()
    if not cs:print("  No commands. Use --generate-commands.");return
    print(f"\n  STRATEGIC COMMAND QUEUE ({len(cs)})");print(SEP)
    for c in cs:
        flag="⚠A" if c.requires_human_approval else "  "
        print(f"  {flag} {c.command_id}  [{c.approval_status}] {c.title[:55]}  {c.command_type}")
    print(SEP)

def generate_commands_cmd():
    r=generate_commands()
    print(f"\n  GENERATE COMMANDS");print(SEP);print(f"  {r['summary']}")
    for c in r["commands"]:print(f"    {c['id']}  {c['title']}")
    print(SEP)

def approve_command_cmd(command_id):
    r=approve_command(command_id)
    if r:print(f"  Command '{r.title[:50]}' approved.")
    else:print(f"  Command '{command_id}' not found.")

def reject_command_cmd(command_id):
    r=reject_command(command_id)
    if r:print(f"  Command '{r.title[:50]}' rejected.")
    else:print(f"  Command '{command_id}' not found.")

def command_review_cmd():
    r=command_review()
    if r.get("message"):print(f"  {r['message']}");return
    print(f"\n  COMMAND REVIEW");print(SEP);print(f"  {r['summary']}")
    if r["top_pending"]:
        print(f"\n  PENDING APPROVAL:")
        for c in r["top_pending"]:print(f"    {c['id']}  [{c['type']}] {c['title']} {'⚠needs approval' if c['needs_approval'] else ''}")
    print(SEP)

def approvals_cmd():
    aps=load_approvals()
    if not aps:print("  No approvals recorded.");return
    print(f"\n  APPROVAL RECORDS ({len(aps)})");print(SEP)
    for a in aps:print(f"  {a.approval_id}  cmd:{a.command_id[:8]}  [{a.approval_status}]  {a.approved_at}")
    print(SEP)

def policies_cmd():
    ps=load_policies()
    print(f"\n  STRATEGIC POLICIES ({len(ps)})");print(SEP)
    for p in ps:
        tag="✓" if p.active else "✗"
        print(f"  {tag} {p.policy_id}  [{p.severity}] {p.title} ({p.scope})")
    print(SEP)

def add_policy_cmd():
    print("\n  ADD POLICY");print("-"*40)
    p=Policy(policy_id=uid(),title=input("  Title: ").strip(),description=input("  Description: ").strip(),scope=input("  Scope: ").strip(),condition=input("  Condition: ").strip(),recommended_action=input("  Recommended action: ").strip(),severity=input("  Severity (low/medium/high): ").strip()or"medium",created_at=today_str())
    ps=load_policies();ps.append(p);save_policies(ps);print(f"  Policy '{p.title}' added.")

def policy_review_cmd():
    r=policy_review()
    print(f"\n  POLICY REVIEW");print(SEP);print(f"  {r['summary']}")
    print(f"  High: {r['by_severity']['high']}  Medium: {r['by_severity']['medium']}  Low: {r['by_severity']['low']}")
    print(SEP)

def conflict_review_cmd():
    data=get_data_for_conflict()
    r=conflict_review(data)
    print(f"\n  CONFLICT REVIEW");print(SEP);print(f"  {r['summary']}")
    for c in r["conflicts"]:print(f"\n  [{c['severity'].upper()}] {c['description']}\n    Resolution: {c['resolution']}")
    print(SEP)

def capacity_cmd():
    cap=load_capacity();r=capacity_review(cap)
    print(f"\n  STRATEGIC CAPACITY");print(SEP)
    for k,v in cap.items():print(f"  {k}: {v}")
    print(f"\n  {r['summary']}")
    print(SEP)

def update_capacity_cmd():
    print("\n  UPDATE CAPACITY");print("-"*40)
    cap=load_capacity()
    try:cap["weekly_available_hours"]=int(input(f"  Available hours/week [{cap.get('weekly_available_hours',40)}]: ").strip()or cap.get("weekly_available_hours",40))
    except:pass
    try:cap["weekly_deep_work_hours"]=int(input(f"  Deep work hours/week [{cap.get('weekly_deep_work_hours',15)}]: ").strip()or cap.get("weekly_deep_work_hours",15))
    except:pass
    try:cap["max_active_projects"]=int(input(f"  Max active projects [{cap.get('max_active_projects',5)}]: ").strip()or cap.get("max_active_projects",5))
    except:pass
    save_capacity(cap);print("  Capacity updated.")

def capacity_review_cmd():
    r=capacity_review()
    print(f"\n  CAPACITY REVIEW");print(SEP);print(f"  {r['summary']}")
    print(f"  Deep work: {r['capacity'].get('weekly_deep_work_hours',0)}h/week")
    print(SEP)

def initiatives_cmd():
    ins=load_initiatives()
    if not ins:print("  No initiatives. Use --add-initiative.");return
    print(f"\n  STRATEGIC INITIATIVES ({len(ins)})");print(SEP)
    for i in ins:print(f"  {i.initiative_id}  {i.name[:45]}  goal:{i.strategic_goal}  status:{i.status}")
    print(SEP)

def add_initiative_cmd():
    print("\n  ADD INITIATIVE");print("-"*40)
    i=Initiative(initiative_id=uid(),name=input("  Name: ").strip(),thesis=input("  Thesis: ").strip(),strategic_goal=input("  Strategic goal: ").strip(),start_date=today_str(),target_date=input("  Target date (YYYY-MM-DD): ").strip(),status="active",success_criteria=input("  Success criteria: ").strip(),current_phase=input("  Current phase: ").strip())
    ins=load_initiatives();ins.append(i);save_initiatives(ins);print(f"  Initiative '{i.name}' created.")

def initiative_review_cmd():
    r=initiative_review()
    if r.get("message"):print(f"  {r['message']}");return
    print(f"\n  INITIATIVE REVIEW");print(SEP);print(f"  {r['summary']}")
    for i in r["initiatives"]:print(f"    {i['name'][:45]}  [{i['health']}]  score:{i['health_score']}  phase:{i['phase']}")
    print(SEP)

def governance_board_cmd():
    r=governance_board()
    print(f"\n  GOVERNANCE BOARD — {today_str()}");print(SEP)
    print(f"  POSITION: {r['strategic_position']}")
    print(f"  INITIATIVES: {r['initiatives'].get('summary', 'none')}")
    print(f"  COMMANDS: {r['command_queue'].get('summary', 'none')}")
    print(f"  POLICIES: {r['policies'].get('summary', 'none')}")
    print(f"  CONFLICTS: {r['conflicts'].get('summary', 'none')}")
    print(f"  CAPACITY: {r['capacity'].get('summary', 'none')}")
    print(f"  DECAY: {r['decay']}")
    print(f"\n  RECOMMENDED DECISIONS:");[print(f"    - {d}")for d in r['recommended_decisions']]
    print(SEP)

def decision_packet_cmd(decision_id):
    r=decision_packet(decision_id)
    if not r:print(f"  Decision '{decision_id}' not found.");return
    print(f"\n  DECISION PACKET: {r['decision']}");print(SEP)
    for k,v in r.items():
        if k=="decision":continue
        print(f"  {k.upper()}: {v}")
    print(SEP)

def command_packet_cmd(command_id):
    r=command_packet(command_id)
    if not r:print(f"  Command '{command_id}' not found.");return
    print(f"\n  COMMAND PACKET: {r['title']}");print(SEP)
    for k,v in r.items():
        if k=="title":continue
        if isinstance(v,bool):v="YES" if v else "NO"
        print(f"  {k.upper()}: {v}")
    print(SEP)

def premortem_cmd(entity_id):
    r=premortem(entity_id)
    print(f"\n  PRE-MORTEM: {r['entity']}");print(SEP)
    print(f"  IMAGINE THIS FAILED. WHAT WENT WRONG?")
    print(f"\n  FAILURE MODES:");[print(f"    - {f}")for f in r["failure_modes"]]
    print(f"\n  EARLY WARNINGS:");[print(f"    - {w}")for w in r["early_warnings"]]
    print(f"\n  PREVENTION:");[print(f"    - {p}")for p in r["prevention"]]
    print(f"\n  CONTINGENCY: {r['contingency']}")
    print(SEP)

def postmortem_cmd(entity_id):
    r=postmortem(entity_id)
    print(f"\n  POST-MORTEM: {r['entity']}");print(SEP)
    for k,v in r.items():
        if k=="entity":continue
        if isinstance(v,list):print(f"  {k.upper()}:");[print(f"    - {item}")for item in v]
        else:print(f"  {k.replace('_',' ').upper()}: {v}")
    print(SEP)

def debt_list_cmd():
    ds=load_strategic_debt()
    if not ds:print("  No strategic debt. Use --add-debt.");return
    print(f"\n  STRATEGIC DEBT ({len(ds)})");print(SEP)
    for d in ds:print(f"  {d.debt_id}  [{d.debt_type}] {d.title[:45]}  interest:{d.interest_rate}  severity:{d.severity}")
    print(SEP)

def add_debt_cmd():
    print("\n  ADD STRATEGIC DEBT");print("-"*40)
    print("  Types:");[print(f"    {i+1}. {t}")for i,t in enumerate(DEBT_TYPES)]
    try:dt=int(input("  Type (1-{0}): ".format(len(DEBT_TYPES))));dtype=DEBT_TYPES[dt-1]
    except:dtype="admin_debt"
    d=StrategicDebt(debt_id=uid(),title=input("  Title: ").strip(),debt_type=dtype,description=input("  Description: ").strip(),severity=int(input("  Severity (1-10): ").strip()or"5"),interest_rate=int(input("  Interest rate (1-10): ").strip()or"3"),created_date=today_str(),next_reduction_action=input("  Next reduction action: ").strip())
    ds=load_strategic_debt();ds.append(d);save_strategic_debt(ds);print(f"  Debt '{d.title[:40]}' recorded.")

def debt_review_cmd():
    r=debt_review()
    if r.get("message"):print(f"  {r['message']}");return
    print(f"\n  STRATEGIC DEBT REVIEW");print(SEP);print(f"  {r['summary']}")
    for d in r["highest_interest"]:print(f"    [{d['type']}] {d['title']} (interest:{d['interest']})")
    print(SEP)

def complexity_audit_cmd():
    r=complexity_audit()
    print(f"\n  COMPLEXITY AUDIT");print(SEP);print(f"  {r['summary']}")
    for k,v in r.items():
        if k in ("summary","warning"):continue
        print(f"  {k.replace('_',' ')}: {v}")
    print(SEP)

def simplify_cmd():
    r=simplify()
    print(f"\n  SIMPLIFICATION RECOMMENDATIONS");print(SEP);print(f"  {r['summary']}")
    for rec in r["recommendations"]:print(f"    - {rec}")
    print(SEP)

def os_health_cmd():
    r=os_health()
    print(f"\n  OPERATING SYSTEM HEALTH");print(SEP)
    print(f"  Score: {r['os_health_score']}/100 ({r['status']})")
    if r["strengths"]:print(f"  Strengths: {', '.join(r['strengths'])}")
    if r["weaknesses"]:print(f"  Weaknesses: {', '.join(r['weaknesses'])}")
    print(SEP)

def autonomy_cmd():
    a=load_autonomy()
    print(f"\n  STRATEGIC AUTONOMY");print(SEP)
    print(f"  Level: {a['level']} — {a['label']}")
    print(f"  Max external actions: {a['max_external_actions']}")
    print(f"  Approved for: {a['allowed_local_actions']}")
    print(f"  Requires approval for: {a['require_approval_for']}")
    print(SEP)

def set_autonomy_cmd(level):
    r=set_autonomy_level(level)
    if r.get("error"):print(f"  Error: {r['error']}");return
    print(f"  Autonomy set to Level {r['level']}: {r['label']}")

def execute_approved_cmd():
    print("\n  EXECUTING APPROVED COMMANDS...")
    r=execute_approved()
    print(f"  {r['summary']}")

def ai_governance_review_cmd():
    print(ai_governance_review_prompt())

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
    # V7 commands
    g.add_argument("--simulate",action="store_true",help="Scenario simulator")
    g.add_argument("--tradeoff",action="store_true",help="Strategic trade-off analysis")
    g.add_argument("--rhythm",action="store_true",help="List operating rhythm")
    g.add_argument("--add-rhythm",action="store_true",help="Add rhythm item")
    g.add_argument("--rhythm-review",action="store_true",help="Rhythm review")
    g.add_argument("--identity-review",action="store_true",help="Identity alignment review")
    g.add_argument("--add-identity",action="store_true",help="Add strategic identity")
    g.add_argument("--identities",action="store_true",help="List identities")
    g.add_argument("--capital",action="store_true",help="List strategic capital")
    g.add_argument("--add-capital",action="store_true",help="Add strategic capital")
    g.add_argument("--capital-review",action="store_true",help="Capital review")
    g.add_argument("--plan-30",action="store_true",help="30-day strategic plan")
    g.add_argument("--plan-90",action="store_true",help="90-day strategic plan")
    g.add_argument("--plan-365",action="store_true",help="365-day strategic plan")
    g.add_argument("--backcast",action="store_true",help="Strategic backcasting")
    g.add_argument("--okrs",action="store_true",help="List OKRs")
    g.add_argument("--add-okr",action="store_true",help="Add OKR")
    g.add_argument("--okr-review",action="store_true",help="OKR review")
    g.add_argument("--rebalance",action="store_true",help="Portfolio rebalance")
    g.add_argument("--integrity-check",action="store_true",help="Data integrity check")
    g.add_argument("--repair-integrity",action="store_true",help="Repair data integrity")
    g.add_argument("--search",type=str,metavar="QUERY",help="Search across all stores")
    g.add_argument("--report-pack",action="store_true",help="Generate report pack")
    g.add_argument("--ai-council",action="store_true",help="AI council prompt")
    g.add_argument("--migrate",action="store_true",help="Migrate stores V6→V7")
    # V8 args
    g.add_argument("--workflows",action="store_true",help="List execution workflows")
    g.add_argument("--add-workflow",action="store_true",help="Add execution workflow")
    g.add_argument("--run-workflow",type=str,metavar="WF_ID",help="Run a workflow by ID")
    g.add_argument("--workflow-review",action="store_true",help="Review all workflows")
    g.add_argument("--generate-sop",action="store_true",help="Generate SOP from template")
    g.add_argument("--project-playbook",type=str,metavar="PROJECT_ID",help="Generate project playbook")
    g.add_argument("--queue",action="store_true",help="View execution queue")
    g.add_argument("--add-to-queue",action="store_true",help="Add item to execution queue")
    g.add_argument("--queue-review",action="store_true",help="Review execution queue")
    g.add_argument("--complete-queue-item",type=str,metavar="QID",help="Mark queue item complete")
    g.add_argument("--compile-next-actions",action="store_true",help="Find missing next actions")
    g.add_argument("--graph",action="store_true",help="Show knowledge graph summary")
    g.add_argument("--graph-entity",type=str,metavar="ENTITY_ID",help="Show graph entity details")
    g.add_argument("--graph-review",action="store_true",help="Review graph structure")
    g.add_argument("--execution-packet",type=str,metavar="ITEM_ID",help="Generate execution packet")
    g.add_argument("--draft-prompt",type=str,metavar="TYPE",help="Generate AI prompt (grant/industry-email/linkedin/lecture/paper-review/venture)")
    g.add_argument("--prepare-meeting",action="store_true",help="Prepare meeting brief")
    g.add_argument("--followups",action="store_true",help="Review follow-ups due")
    g.add_argument("--sprint-plan",action="store_true",help="Generate weekly sprint plan")
    g.add_argument("--startup",action="store_true",help="Daily startup ritual")
    g.add_argument("--shutdown",action="store_true",help="Daily shutdown reflection")
    g.add_argument("--asset-opportunities",action="store_true",help="Find asset creation opportunities")
    g.add_argument("--capture",action="store_true",help="Capture knowledge/idea/lesson")
    g.add_argument("--captures",action="store_true",help="List knowledge captures")
    g.add_argument("--context-prompt",type=str,metavar="QUERY",help="Build context prompt from local data")
    g.add_argument("--export-context",type=str,metavar="QUERY",help="Export context with optional redaction")
    g.add_argument("--dashboard-role",type=str,metavar="ROLE",help="Role-specific dashboard (researcher/pi/lecturer/collaborator/founder/public-intellectual)")
    g.add_argument("--one-page",action="store_true",help="One-page strategic overview")
    # V9 args
    g.add_argument("--metrics",action="store_true",help="List metrics")
    g.add_argument("--add-metric",action="store_true",help="Add metric")
    g.add_argument("--update-metric",type=str,metavar="METRIC_ID",help="Update metric value")
    g.add_argument("--metrics-review",action="store_true",help="Review metrics")
    g.add_argument("--impact",action="store_true",help="List impact records")
    g.add_argument("--add-impact",action="store_true",help="Add impact record")
    g.add_argument("--impact-review",action="store_true",help="Review impact ledger")
    g.add_argument("--roi-review",action="store_true",help="Strategic ROI analysis")
    g.add_argument("--workflow-performance",action="store_true",help="Workflow performance analytics")
    g.add_argument("--review-workflow-run",type=str,metavar="RUN_ID",help="Review a workflow run")
    g.add_argument("--estimates",action="store_true",help="View estimation accuracy")
    g.add_argument("--estimate-review",action="store_true",help="Estimation review")
    g.add_argument("--reforecast",action="store_true",help="Reforecast outcomes and OKRs")
    g.add_argument("--velocity-review",action="store_true",help="Progress velocity review")
    g.add_argument("--indicators",action="store_true",help="List leading/lagging indicators")
    g.add_argument("--indicator-review",action="store_true",help="Indicator health review")
    g.add_argument("--review-board",action="store_true",help="Strategic review board")
    g.add_argument("--contracts",action="store_true",help="List accountability contracts")
    g.add_argument("--add-contract",action="store_true",help="Create accountability contract")
    g.add_argument("--contract-review",action="store_true",help="Contract review")
    g.add_argument("--adherence-review",action="store_true",help="Behavioral adherence review")
    g.add_argument("--rubrics",action="store_true",help="List quality rubrics")
    g.add_argument("--score-output",action="store_true",help="Score an output using a rubric")
    g.add_argument("--attribution-review",action="store_true",help="Outcome attribution review")
    g.add_argument("--flywheel-review",action="store_true",help="Strategic flywheel review")
    g.add_argument("--decay-review",action="store_true",help="Strategic decay detector")
    g.add_argument("--rebalance-optimized",action="store_true",help="Optimized rebalance with constraints")
    g.add_argument("--export-csv",type=str,metavar="STORE",help="Export store as CSV (metrics/projects/opportunities/impact/risks)")
    g.add_argument("--import-csv",type=str,metavar="STORE",help="Import CSV into store (requires --export for file path)")
    g.add_argument("--ai-performance-review",action="store_true",help="AI performance review prompt")
    # V10 args
    g.add_argument("--commands",action="store_true",help="List strategic command queue")
    g.add_argument("--generate-commands",action="store_true",help="Generate commands from reviews")
    g.add_argument("--approve-command",type=str,metavar="COMMAND_ID",help="Approve a command")
    g.add_argument("--reject-command",type=str,metavar="COMMAND_ID",help="Reject a command")
    g.add_argument("--command-review",action="store_true",help="Command queue review")
    g.add_argument("--approvals",action="store_true",help="List approval records")
    g.add_argument("--approval-review",action="store_true",help="Approval review")
    g.add_argument("--policies",action="store_true",help="List strategic policies")
    g.add_argument("--add-policy",action="store_true",help="Add strategic policy")
    g.add_argument("--policy-review",action="store_true",help="Policy review")
    g.add_argument("--conflict-review",action="store_true",help="Strategic conflict detection")
    g.add_argument("--capacity",action="store_true",help="Show capacity model")
    g.add_argument("--update-capacity",action="store_true",help="Update capacity model")
    g.add_argument("--capacity-review",action="store_true",help="Capacity review")
    g.add_argument("--initiatives",action="store_true",help="List strategic initiatives")
    g.add_argument("--add-initiative",action="store_true",help="Create strategic initiative")
    g.add_argument("--initiative-review",action="store_true",help="Initiative health review")
    g.add_argument("--initiative",type=str,metavar="INITIATIVE_ID",help="View specific initiative")
    g.add_argument("--governance-board",action="store_true",help="Governance board review")
    g.add_argument("--decision-packet",type=str,metavar="DECISION_ID",help="Decision meeting packet")
    g.add_argument("--command-packet",type=str,metavar="COMMAND_ID",help="Command execution packet")
    g.add_argument("--premortem",type=str,metavar="PROJECT_ID",help="Pre-mortem analysis")
    g.add_argument("--premortem-initiative",type=str,metavar="INITIATIVE_ID",help="Initiative pre-mortem")
    g.add_argument("--postmortem",type=str,metavar="PROJECT_ID",help="Post-mortem analysis")
    g.add_argument("--postmortem-initiative",type=str,metavar="INITIATIVE_ID",help="Initiative post-mortem")
    g.add_argument("--debt",action="store_true",help="List strategic debt")
    g.add_argument("--add-debt",action="store_true",help="Add strategic debt")
    g.add_argument("--debt-review",action="store_true",help="Strategic debt review")
    g.add_argument("--complexity-audit",action="store_true",help="System complexity audit")
    g.add_argument("--simplify",action="store_true",help="Simplification recommendations")
    g.add_argument("--os-health",action="store_true",help="Operating system health score")
    g.add_argument("--autonomy",action="store_true",help="Show autonomy settings")
    g.add_argument("--set-autonomy",type=str,metavar="LEVEL",help="Set autonomy level (0-4)")
    g.add_argument("--execute-approved",action="store_true",help="Execute approved local commands")
    g.add_argument("--ai-governance-review",action="store_true",help="AI governance review prompt")
    g.add_argument("--reflect",type=str,metavar="YYYY-MM-DD",help="End-of-day reflection")
    g.add_argument("--project",type=str,metavar="PROJECT_ID",help="Project detail")
    p.add_argument("--json",action="store_true",help="Clean JSON output")
    p.add_argument("--redact",action="store_true",help="Redact sensitive info in export")
    p.add_argument("--export",type=str,metavar="FILE",help="Save JSON/text to FILE")
    p.add_argument("--save-history",action="store_true",help="Persist daily plan")
    p.add_argument("--days",type=int,default=7,help="Days for review (default 7)")
    p.add_argument("--horizon",type=int,default=90,help="Horizon in days for simulation (default 90)")
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
    # V7 dispatch
    if args.simulate: simulate_cmd(args.horizon); return
    if args.tradeoff: tradeoff_cmd(); return
    if args.rhythm: list_rhythms_cmd(); return
    if args.add_rhythm: add_rhythm_interactive(); return
    if args.rhythm_review: rhythm_review_cmd(); return
    if args.identity_review: identity_review_cmd(); return
    if args.add_identity: add_identity_interactive(); return
    if args.identities: list_identities(); return
    if args.capital: list_capitals(); return
    if args.add_capital: add_capital_interactive(); return
    if args.capital_review: capital_review_cmd(); return
    if args.plan_30: plan_cmd(30); return
    if args.plan_90: plan_cmd(90); return
    if args.plan_365: plan_cmd(365); return
    if args.backcast: backcast_cmd(); return
    if args.okrs: list_okrs_cmd(); return
    if args.add_okr: add_okr_interactive(); return
    if args.okr_review: okr_review_cmd(); return
    if args.rebalance: rebalance_cmd(); return
    if args.integrity_check: integrity_check_cmd(); return
    if args.repair_integrity: repair_integrity_cmd(); return
    if args.search: search_cmd(args.search); return
    if args.report_pack: report_pack_cmd(); return
    if args.ai_council: ai_council_cmd(); return
    if args.migrate: migrate_cmd(); return
    # V8 dispatch
    if args.workflows: workflows_cmd(); return
    if args.add_workflow: add_workflow_cmd(); return
    if args.run_workflow: run_workflow_cmd(args.run_workflow); return
    if args.workflow_review: workflows_cmd(); return
    if args.generate_sop:
        if args.export: sop_cmd(args.export, args.export)
        else:
            print("\n  Available SOP templates:");[print(f"    - {t}")for t in DEFAULT_SOP_TEMPLATES.keys()]
            print(f"  Use --generate-sop --export TEMPLATE_NAME to generate one.")
        return
    if args.project_playbook: playbook_cmd(args.project_playbook, args.export); return
    if args.queue: queue_cmd(); return
    if args.add_to_queue: add_to_queue_cmd(); return
    if args.queue_review: queue_cmd(); return
    if args.complete_queue_item: complete_queue_item_cmd(args.complete_queue_item); return
    if args.compile_next_actions: compile_next_actions_cmd(); return
    if args.graph or args.graph_review: graph_cmd(); return
    if args.graph_entity: graph_entity_cmd(args.graph_entity); return
    if args.execution_packet: execution_packet_cmd(args.execution_packet); return
    if args.draft_prompt: draft_prompt_cmd(args.draft_prompt); return
    if args.prepare_meeting: prepare_meeting_cmd(); return
    if args.followups: followups_cmd(prompts=bool(args.export)); return
    if args.sprint_plan: sprint_plan_cmd(); return
    if args.startup: startup_cmd(); return
    if args.shutdown: shutdown_cmd(); return
    if args.asset_opportunities: asset_opportunities_cmd(); return
    if args.capture: capture_cmd(); return
    if args.captures: list_captures_cmd(); return
    if args.context_prompt: context_prompt_cmd(args.context_prompt, args.redact); return
    if args.export_context: export_context_cmd(args.export_context, args.redact); return
    if args.dashboard_role: role_dashboard_cmd(args.dashboard_role); return
    if args.one_page: one_page_cmd(); return
    # V9 dispatch
    if args.metrics or args.metrics_review: metrics_review_cmd() if args.metrics_review else metrics_list_cmd(); return
    if args.add_metric: add_metric_cmd(); return
    if args.update_metric: print(f"  Use --add-metric with new value. Metric ID: {args.update_metric}"); return
    if args.impact: impact_list_cmd(); return
    if args.add_impact: add_impact_cmd(); return
    if args.impact_review: impact_review_cmd(); return
    if args.roi_review: roi_review_cmd(); return
    if args.workflow_performance: workflow_performance_cmd(); return
    if args.review_workflow_run: print(f"  Run ID: {args.review_workflow_run}"); return
    if args.estimates or args.estimate_review: estimate_review_cmd(); return
    if args.reforecast: reforecast_cmd(); return
    if args.velocity_review: velocity_review_cmd(); return
    if args.indicators: indicators_cmd(); return
    if args.indicator_review: indicator_review_cmd(); return
    if args.review_board: review_board_cmd(); return
    if args.contracts: contracts_cmd(); return
    if args.add_contract: add_contract_cmd(); return
    if args.contract_review: contract_review_cmd(); return
    if args.adherence_review: adherence_review_cmd(); return
    if args.rubrics: rubrics_cmd(); return
    if args.score_output: score_output_cmd(); return
    if args.attribution_review: attribution_review_cmd(); return
    if args.flywheel_review: flywheel_review_cmd(); return
    if args.decay_review: decay_review_cmd(); return
    if args.rebalance_optimized: rebalance_optimized_cmd(); return
    if args.export_csv: export_csv_cmd(args.export_csv); return
    if args.import_csv: import_csv_cmd(args.import_csv, args.export or ""); return
    if args.ai_performance_review: ai_performance_review_cmd(); return
    # V10 dispatch
    if args.commands or args.command_review: command_review_cmd() if args.command_review else commands_cmd(); return
    if args.generate_commands: generate_commands_cmd(); return
    if args.approve_command: approve_command_cmd(args.approve_command); return
    if args.reject_command: reject_command_cmd(args.reject_command); return
    if args.approvals or args.approval_review: approvals_cmd(); return
    if args.policies: policies_cmd(); return
    if args.add_policy: add_policy_cmd(); return
    if args.policy_review: policy_review_cmd(); return
    if args.conflict_review: conflict_review_cmd(); return
    if args.capacity: capacity_cmd(); return
    if args.update_capacity: update_capacity_cmd(); return
    if args.capacity_review: capacity_review_cmd(); return
    if args.initiatives: initiatives_cmd(); return
    if args.add_initiative: add_initiative_cmd(); return
    if args.initiative_review: initiative_review_cmd(); return
    if args.initiative: print(f"  Initiative: {args.initiative}"); return
    if args.governance_board: governance_board_cmd(); return
    if args.decision_packet: decision_packet_cmd(args.decision_packet); return
    if args.command_packet: command_packet_cmd(args.command_packet); return
    if args.premortem: premortem_cmd(args.premortem); return
    if args.premortem_initiative: premortem_cmd(args.premortem_initiative); return
    if args.postmortem: postmortem_cmd(args.postmortem); return
    if args.postmortem_initiative: postmortem_cmd(args.postmortem_initiative); return
    if args.debt: debt_list_cmd(); return
    if args.add_debt: add_debt_cmd(); return
    if args.debt_review: debt_review_cmd(); return
    if args.complexity_audit: complexity_audit_cmd(); return
    if args.simplify: simplify_cmd(); return
    if args.os_health: os_health_cmd(); return
    if args.autonomy: autonomy_cmd(); return
    if args.set_autonomy: set_autonomy_cmd(args.set_autonomy); return
    if args.execute_approved: execute_approved_cmd(); return
    if args.ai_governance_review: ai_governance_review_cmd(); return
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
