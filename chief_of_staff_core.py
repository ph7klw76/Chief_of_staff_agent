#!/usr/bin/env python3
"""Chief of Staff v6 — core models, storage, scoring (stdlib only)."""
from __future__ import annotations
import json, sys, uuid, shutil
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from collections import defaultdict

SCHEMA_VERSION = "6.0"
STRATEGIC_GOALS = ["research_publication","grant_funding","industry_collaboration","teaching_excellence","public_influence","deeptech_venture","admin_maintenance"]
PROJECT_CATEGORIES = ["research_project","grant_proposal","industry_collaboration","teaching_project","public_influence","deeptech_venture","personal_system"]
OPPORTUNITY_TYPES = ["grant","collaboration","industry_partner","paper","conference","student_project","startup_idea","media_visibility","teaching_innovation"]
RISK_CATEGORIES = ["research_delay","grant_failure","collaboration_loss","teaching_overload","admin_overload","health_energy","financial","reputation","execution_drift"]
RELATIONSHIP_TYPES = ["research_collaborator","industry_partner","grant_partner","student","mentor","media_contact","investor","founder_peer"]
EVIDENCE_TYPES = ["observation","result","feedback","metric","failure","external_signal","intuition"]
ASSUMPTION_CATEGORIES = ["research","grant","industry","teaching","venture","personal_productivity","financial","reputation"]
ASSET_TYPES = ["proposal_template","lecture_material","research_dataset","manuscript_section","collaboration_pitch","industry_contact_list","linkedin_post_series","software_tool","analysis_script","business_model_canvas"]
BIAS_TYPES = ["planning_fallacy","urgency_bias","sunk_cost","novelty_bias","avoidance","overconfidence","underinvestment","relationship_neglect"]
TIME_HORIZONS = ["3_months","6_months","1_year","3_years","10_years"]
WEIGHTS = {"impact":0.20,"urgency":0.15,"strategic_value":0.20,"compounding_effect":0.15,"goal_alignment":0.15,"deadline_pressure":0.10,"energy_fit":0.05}
OPPORTUNITY_COST_WEIGHT = 0.15
SEP = "="*62
LONG_TERM_GOALS = "1. Become a world-class organic electronics researcher.\n2. Secure major research grants.\n3. Build industry collaborations.\n4. Grow influence in the field.\n5. Eventually create a high-value deep-tech company."
DEFAULT_CONFIG = {"strategic_baseline":{"research_publication":25,"grant_funding":20,"industry_collaboration":15,"teaching_excellence":15,"public_influence":10,"deeptech_venture":10,"admin_maintenance":5},"admin_time_warning_threshold":25,"overcommitment_warning_ratio":1.2,"low_completion_warning_threshold":50}
DEFAULT_TEMPLATES = {"grant_proposal":{"impact":9,"urgency":7,"strategic_value":10,"compounding_effect":9,"goal_alignment":10,"deadline_pressure":7,"energy_fit":6,"opportunity_cost":2,"focus_requirement":9,"estimated_minutes":120,"strategic_goal":"grant_funding"},"research_writing":{"impact":9,"urgency":6,"strategic_value":10,"compounding_effect":9,"goal_alignment":10,"deadline_pressure":5,"energy_fit":7,"opportunity_cost":2,"focus_requirement":9,"estimated_minutes":120,"strategic_goal":"research_publication"},"industry_email":{"impact":7,"urgency":6,"strategic_value":8,"compounding_effect":7,"goal_alignment":8,"deadline_pressure":5,"energy_fit":8,"opportunity_cost":2,"focus_requirement":4,"estimated_minutes":30,"strategic_goal":"industry_collaboration"},"admin_task":{"impact":3,"urgency":5,"strategic_value":2,"compounding_effect":2,"goal_alignment":2,"deadline_pressure":5,"energy_fit":7,"opportunity_cost":7,"focus_requirement":2,"estimated_minutes":30,"strategic_goal":"admin_maintenance"}}

# Paths
HISTORY_DIR = Path("chief_of_staff_history")
CONFIG_PATH = Path("chief_of_staff_config.json"); TEMPLATES_PATH = Path("chief_of_staff_templates.json")
PROJECTS_PATH = Path("chief_of_staff_projects.json"); OPPORTUNITIES_PATH = Path("chief_of_staff_opportunities.json")
DECISIONS_PATH = Path("chief_of_staff_decisions.json"); EXPERIMENTS_PATH = Path("chief_of_staff_experiments.json")
RISKS_PATH = Path("chief_of_staff_risks.json"); RELATIONSHIPS_PATH = Path("chief_of_staff_relationships.json")
PRINCIPLES_PATH = Path("chief_of_staff_principles.json")
OUTCOMES_PATH = Path("chief_of_staff_outcomes.json"); EVIDENCE_PATH = Path("chief_of_staff_evidence.json")
ASSUMPTIONS_PATH = Path("chief_of_staff_assumptions.json"); PREDICTIONS_PATH = Path("chief_of_staff_predictions.json")
HYPOTHESES_PATH = Path("chief_of_staff_hypotheses.json"); ASSETS_PATH = Path("chief_of_staff_assets.json")
DOCTRINE_PATH = Path("chief_of_staff_doctrine.json")

def uid(): return uuid.uuid4().hex[:8]
def today_str(): return date.today().isoformat()

# ======================================================================
# SCHEMA-VERSIONED STORAGE
# ======================================================================
def load_json(path, default=None):
    if default is None: default = []
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if isinstance(data, dict) and "records" in data:
                return data["records"]
            return data
        except (json.JSONDecodeError, OSError) as e:
            print(f"  !! Corrupt JSON in {path}: {e}", file=sys.stderr)
            bak = path.with_suffix(path.suffix + ".bak")
            if bak.exists():
                try: return json.loads(bak.read_text())
                except: pass
    return default

def save_json(path, data, backup=True, is_records=False):
    if backup and path.exists():
        bak = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, bak)
    if is_records:
        content = {"schema_version": SCHEMA_VERSION, "created_at": today_str(), "updated_at": today_str(), "records": data}
    else:
        content = data
    path.write_text(json.dumps(content, indent=2))

def load_records(path):
    """Load records from schema-versioned store."""
    return load_json(path, [])

def save_records(path, records):
    """Save records to schema-versioned store."""
    save_json(path, records, is_records=True)

def load_config():
    cfg = load_json(CONFIG_PATH, dict(DEFAULT_CONFIG))
    if not CONFIG_PATH.exists(): save_json(CONFIG_PATH, cfg, backup=False)
    return cfg

def load_templates():
    tmpl = load_json(TEMPLATES_PATH, dict(DEFAULT_TEMPLATES))
    if not TEMPLATES_PATH.exists(): save_json(TEMPLATES_PATH, tmpl, backup=False)
    return tmpl

# ======================================================================
# ALL DATACLASSES
# ======================================================================
@dataclass
class Task:
    name:str;impact:int=5;urgency:int=5;strategic_value:int=5;compounding_effect:int=5
    goal_alignment:int=5;deadline_pressure:int=5;energy_fit:int=5
    opportunity_cost:int=5;focus_requirement:int=5;estimated_minutes:int=60
    strategic_goal:str="research_publication";next_action:str="";delegatable:bool=False
    project_id:Optional[str]=None;milestone_id:Optional[str]=None
    weighted_score:float=0.0;final_score:float=0.0;score_per_hour:float=0.0
    label:str="";warnings:list=field(default_factory=list)

@dataclass
class Project:
    project_id:str="";name:str="";category:str="research_project";strategic_goal:str="research_publication"
    description:str="";status:str="active";start_date:str="";target_date:str=""
    success_criteria:str="";next_milestone:str="";related_tasks:list=field(default_factory=list)
    estimated_total_hours:float=0.0;actual_hours_logged:float=0.0
    priority_score:int=5;risk_level:str="medium";notes:str=""

@dataclass
class Opportunity:
    opportunity_id:str="";name:str="";type:str="grant";description:str="";strategic_goal:str="grant_funding"
    potential_value:int=5;probability:int=5;urgency:int=5;relationship_value:int=5;effort_required:int=5
    next_action:str="";status:str="open";source:str="";created_date:str="";last_touched_date:str="";notes:str=""
    score:float=0.0

@dataclass
class Decision:
    decision_id:str="";date:str="";title:str="";context:str="";options:list=field(default_factory=list)
    chosen_option:str="";rationale:str="";expected_outcome:str="";review_date:str=""
    actual_outcome:str="";lesson:str=""
    clarity_of_objective:int=5;quality_of_options:int=5;evidence_quality:int=5
    opportunity_cost_awareness:int=5;risk_awareness:int=5;outcome_quality:int=5
    quality_score:float=0.0

@dataclass
class Experiment:
    experiment_id:str="";title:str="";hypothesis:str="";strategic_goal:str="research_publication"
    start_date:str="";end_date:str="";success_metric:str="";expected_result:str=""
    actual_result:str="";status:str="planned";lesson:str=""

@dataclass
class Risk:
    risk_id:str="";title:str="";category:str="execution_drift";probability:int=5
    severity:int=5;detectability:int=5;mitigation:str="";owner:str="self"
    status:str="active";linked_project_id:Optional[str]=None;score:int=0

@dataclass
class Relationship:
    relationship_id:str="";name:str="";organization:str="";relationship_type:str="research_collaborator"
    strategic_goal:str="research_publication";last_contact_date:str=""
    next_contact_action:str="";value_to_them:str="";value_to_user:str=""
    status:str="active";notes:str=""

@dataclass
class Principle: principle_id:str="";title:str="";statement:str="";evidence:str="";date_created:str="";last_reviewed:str="";status:str="active"

@dataclass
class Outcome:
    outcome_id:str="";name:str="";description:str="";time_horizon:str="1_year";strategic_goal:str="research_publication"
    success_metric:str="";current_status:str="";desired_status:str="";confidence_level:int=5;importance:int=5
    linked_projects:list=field(default_factory=list);linked_opportunities:list=field(default_factory=list)
    linked_relationships:list=field(default_factory=list);linked_risks:list=field(default_factory=list);notes:str=""

@dataclass
class Evidence:
    evidence_id:str="";date:str="";title:str="";evidence_type:str="observation";related_goal:str=""
    related_project_id:str="";related_decision_id:str="";related_opportunity_id:str=""
    claim_supported:str="";claim_weakened:str="";strength:int=5;reliability:int=5;notes:str=""

@dataclass
class Assumption:
    assumption_id:str="";statement:str="";category:str="research";confidence:int=5;importance:int=5
    evidence_for:list=field(default_factory=list);evidence_against:list=field(default_factory=list)
    last_reviewed:str="";status:str="active";what_would_change_my_mind:str=""

@dataclass
class Prediction:
    prediction_id:str="";date_created:str="";prediction_statement:str="";category:str="research"
    probability:int=50;expected_resolution_date:str="";actual_outcome:bool=False
    resolved:bool=False;brier_score:float=0.0;lesson:str=""

@dataclass
class Hypothesis:
    hypothesis_id:str="";statement:str="";strategic_goal:str="research_publication"
    linked_assumptions:list=field(default_factory=list);linked_experiments:list=field(default_factory=list)
    linked_evidence:list=field(default_factory=list);confidence_before:int=5;confidence_after:int=5
    status:str="untested";next_test:str=""

@dataclass
class Asset:
    asset_id:str="";name:str="";asset_type:str="proposal_template";strategic_goal:str="research_publication"
    description:str="";created_date:str="";reuse_count:int=0;linked_project_id:str=""
    linked_outcome_id:str="";estimated_future_value:int=5;maintenance_required:str="low";notes:str=""

@dataclass
class Doctrine:
    doctrine_id:str="";principle:str="";rationale:str="";evidence:str=""
    related_bias:str="";last_reviewed:str="";status:str="active"

# ======================================================================
# SCORING
# ======================================================================
def compute_weighted_score(t): return round(sum(getattr(t,k,0)*w for k,w in WEIGHTS.items()),2)
def compute_final_score(t): return round(compute_weighted_score(t)-t.opportunity_cost*OPPORTUNITY_COST_WEIGHT,2)
def compute_score_per_hour(t):
    h=t.estimated_minutes/60.0; return round(t.final_score/h,2) if h>0 else 0.0
def score_label(s):
    if s>=8: return"CRITICAL"
    if s>=6: return"HIGH"
    if s>=4: return"MEDIUM"
    return"LOW"
def score_task(t):
    fs=compute_final_score(t)
    return replace(t,weighted_score=compute_weighted_score(t),final_score=fs,score_per_hour=compute_score_per_hour(replace(t,final_score=fs)),label=score_label(fs),warnings=generate_warnings(t))
def rank_tasks(tasks): return sorted([score_task(t)for t in tasks],key=lambda x:x.final_score,reverse=True)
def opp_score(o): return round(o.potential_value*0.30+o.probability*0.20+o.urgency*0.15+o.relationship_value*0.20-o.effort_required*0.15,1)
def risk_score(r): return r.probability*r.severity*r.detectability
def decision_quality_score(d):
    dims = [d.clarity_of_objective,d.quality_of_options,d.evidence_quality,d.opportunity_cost_awareness,d.risk_awareness,d.outcome_quality]
    return round(sum(dims)/len(dims),1) if dims else 0

# ======================================================================
# EXECUTION SCRIPTS
# ======================================================================
EXECUTION_SCRIPTS={"grant_funding":["Open proposal.","Write problem statement (3 sentences).","Write 3 objectives.","List expected outcomes.","Stop -- no budget/formatting."],"research_publication":["Open manuscript.","Revise ONE subsection.","Add citations as [PLACEHOLDER].","Do NOT polish.","Save & mark draft-complete."],"industry_collaboration":["Open email draft.","State mutual value (2 sentences).","Suggest ONE next step.","Propose meeting window.","Keep <200 words. Send."],"teaching_excellence":["Open slides/notes.","Outline 3 key takeaways.","Add one worked example.","Check timing (~2min/slide).","Save & mark ready."],"public_influence":["Open post/abstract/CV.","Write core message (2 sentences).","Add evidence (1 data point).","Trim to half length.","Publish or save."],"deeptech_venture":["Open BMC or IP log.","Identify ONE hypothesis.","Draft smallest experiment.","List resources needed.","Schedule experiment."],"admin_maintenance":["Open email/task list.","Sort by sender.","Delete/archive >2 weeks old.","Respond ONLY to blockers.","Close email. Do not reopen."]}
def make_execution_script(task): return EXECUTION_SCRIPTS.get(task.strategic_goal,EXECUTION_SCRIPTS["research_publication"])

# Forward declarations needed by legacy code
def generate_warnings(t):
    w=[]
    if t.urgency>=8 and t.strategic_value<=3:w.append("High urgency but low strategic value -- fire-drill.")
    if t.impact<=3 and t.urgency>=8:w.append("Low impact but high urgency -- truly urgent?")
    if t.opportunity_cost>=8:w.append("High opportunity cost -- blocks higher-value work.")
    if t.strategic_goal=="admin_maintenance" and t.strategic_value>=7:w.append("Admin with suspiciously high strategic score.")
    if t.estimated_minutes>=180 and t.final_score<5:w.append("Very long (>=3h) with low score -- break down or drop.")
    if t.strategic_goal=="admin_maintenance" and t.estimated_minutes>=60:w.append("Admin task >=1h -- batch, automate, or delegate.")
    if t.urgency>=8 and t.deadline_pressure<=3:w.append("High urgency but low deadline pressure -- artificial?")
    if t.goal_alignment<=3 and t.urgency>=7:w.append("Poor goal alignment despite high urgency.")
    if t.energy_fit<=3 and t.focus_requirement>=8:w.append("Low energy fit with high focus -- may need rescheduling.")
    return w

def do_capacity(energy):
    if energy<=3:return 1
    if energy<=6:return 2
    return 3

def classify_tasks(ranked,energy,available_minutes):
    cap=do_capacity(energy);do,delay,dele,ignore=[],[],[],[];do_mins,over=0,False
    for i,t in enumerate(ranked):
        if i<cap:
            if do_mins+t.estimated_minutes<=available_minutes:do.append(t);do_mins+=t.estimated_minutes
            elif t.deadline_pressure>=9:do.append(t);do_mins+=t.estimated_minutes;over=True
            else:delay.append(t)
        elif i<cap+2:
            if t.delegatable and energy>=6:dele.append(t)
            else:delay.append(t)
        else:ignore.append(t)
    return do,delay,dele,ignore,do_mins,over

def portfolio_diagnosis(tasks):
    cnt={g:0 for g in STRATEGIC_GOALS};mins={g:0 for g in STRATEGIC_GOALS};sl={g:[]for g in STRATEGIC_GOALS}
    for t in tasks:
        g=t.strategic_goal
        if g in cnt:cnt[g]+=1;mins[g]+=t.estimated_minutes;sl[g].append(t.final_score)
    total=sum(mins.values())or 1
    avg={g:round(sum(sl[g])/len(sl[g]),2)if sl[g]else 0.0 for g in STRATEGIC_GOALS}
    return cnt,mins,avg,total

def make_first_30min(do):
    """Generate first-30-minutes instruction."""
    if not do: return "No DO tasks -- review priorities."
    t = do[0]
    if t.energy_fit <= 3: return f"Tackle '{t.name}' early while energy is highest ({t.estimated_minutes}min). Start with the first concrete step: {t.next_action or 'open the file and begin'}."
    if t.focus_requirement >= 8: return f"Deep-work block on '{t.name}' -- close email, silence phone, set timer for {t.estimated_minutes}min. First action: {t.next_action or 'open the main document'}."
    return f"Start '{t.name}' immediately. First action: {t.next_action or 'open the task and begin'}. Estimated: {t.estimated_minutes}min."

def suggest_decomposition(t):
    """Suggest decomposition steps if task >3 hours or score <5 with long duration."""
    if t.estimated_minutes < 180 and t.final_score >= 5: return []
    steps = []
    sg = t.strategic_goal
    if sg == "grant_funding":
        steps = ["Draft problem statement (30 min)", "Outline 3 objectives (30 min)", "List expected outcomes (30 min)", "Draft budget rough (30 min)", "Review & refine (30 min)"]
    elif sg == "research_publication":
        steps = ["Outline section structure (20 min)", "Write 1 paragraph (30 min)", "Add citations as placeholders (20 min)", "Review 1 subsection (30 min)", "Polish intro/conclusion (30 min)"]
    elif sg == "industry_collaboration":
        steps = ["Draft mutual value proposition (15 min)", "List 3 collaboration angles (15 min)", "Draft email outline (15 min)", "Review & trim to 200 words (15 min)"]
    elif sg == "teaching_excellence":
        steps = ["Define 3 key takeaways (15 min)", "Create 1 worked example (20 min)", "Draft slide outline (20 min)", "Add timing notes (10 min)", "Review for clarity (15 min)"]
    elif sg == "public_influence":
        steps = ["Write core message (15 min)", "Add 1 data point/evidence (10 min)", "Trim to half length (15 min)", "Add call-to-action (5 min)", "Review & publish (10 min)"]
    elif sg == "deeptech_venture":
        steps = ["Identify 1 key hypothesis (15 min)", "Design smallest experiment (15 min)", "List resources needed (10 min)", "Set success criteria (10 min)", "Schedule experiment (10 min)"]
    elif sg == "admin_maintenance":
        steps = ["Sort by urgency (5 min)", "Archive/delete old items (10 min)", "Respond only to blockers (10 min)", "Close and do not reopen (5 min)"]
    else:
        steps = ["Define concrete first step (10 min)", "Do that step (20 min)", "Assess if more is needed (5 min)"]
    n = min(len(steps), max(2, t.estimated_minutes // 45))
    return steps[:n]

def ser_task(t):
    """Serialize a Task to a dict."""
    return {k: v for k, v in t.__dict__.items()}

def load_recent_history(days):
    """Load history records from the last N days."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = date.today() - timedelta(days=days)
    records = []
    for f in sorted(HISTORY_DIR.glob("*_plan.json")):
        try:
            d_str = f.stem.replace("_plan", "")
            d = date.fromisoformat(d_str)
            if d >= cutoff:
                records.append(json.loads(f.read_text()))
        except (ValueError, json.JSONDecodeError):
            continue
    return records

def load_history(date_str):
    """Load a specific day's plan."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    p = HISTORY_DIR / f"{date_str}_plan.json"
    if p.exists():
        try: return json.loads(p.read_text())
        except json.JSONDecodeError: return None
    return None

def build_history_record(tasks, ranked, available_hours, am, deadlines, meetings, energy, do, delay, dele, ignore, do_mins, over, first30):
    """Build a history record dict."""
    cnt, mins, _, _ = portfolio_diagnosis(ranked)
    return {
        "date": today_str(),
        "available_hours": available_hours,
        "available_minutes": am,
        "deadlines": deadlines,
        "meetings": meetings,
        "energy": energy,
        "tasks": [ser_task(t) for t in tasks],
        "ranked": [ser_task(t) for t in ranked],
        "do": [ser_task(t) for t in do],
        "delay": [ser_task(t) for t in delay],
        "delegate": [ser_task(t) for t in dele],
        "ignore": [ser_task(t) for t in ignore],
        "do_minutes": do_mins,
        "overcommitted": over,
        "total_planned_minutes": sum(t.estimated_minutes for t in do),
        "first_30_minutes": first30,
        "portfolio": {
            "by_goal": {
                g: {"count": cnt[g], "minutes": mins[g], "pct_time": round(mins[g] / (sum(mins.values()) or 1) * 100, 1)}
                for g in STRATEGIC_GOALS
            }
        },
    }

def save_history(record):
    """Save a history record to disk."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    p = HISTORY_DIR / f"{record['date']}_plan.json"
    p.write_text(json.dumps(record, indent=2))

# ======================================================================
# V6 — STRATEGIC INTELLIGENCE & JUDGMENT IMPROVEMENT
# ======================================================================

def calibration_review(predictions):
    """Analyze prediction calibration. Returns dict with Brier scores and calibration stats."""
    resolved = [p for p in predictions if p.resolved]
    if not resolved:
        return {"total_predictions": len(predictions), "resolved": 0,
                "message": "No resolved predictions yet. Resolve predictions to see calibration."}
    brier_scores = []
    overconfident = []
    well_calibrated = []
    for p in resolved:
        bs = (p.probability / 100 - (1 if p.actual_outcome else 0)) ** 2
        p.brier_score = round(bs, 3)
        brier_scores.append(bs)
        if p.probability >= 80 and not p.actual_outcome:
            overconfident.append(p)
        elif p.probability <= 20 and p.actual_outcome:
            overconfident.append(p)
        elif abs(p.probability - (100 if p.actual_outcome else 0)) <= 25:
            well_calibrated.append(p)
    avg_brier = round(sum(brier_scores) / len(brier_scores), 3) if brier_scores else 0
    bins = [(0, 59), (60, 79), (80, 100)]
    bin_stats = {}
    for lo, hi in bins:
        in_bin = [p for p in resolved if lo <= p.probability <= hi]
        if in_bin:
            actual_rate = round(sum(1 for p in in_bin if p.actual_outcome) / len(in_bin) * 100, 1)
            bin_stats[f"{lo}-{hi}%"] = {"count": len(in_bin), "actual_true_pct": actual_rate,
                                         "expected_mid": (lo + hi) / 2, "drift": round(actual_rate - (lo + hi) / 2, 1)}
    return {"total_predictions": len(predictions), "resolved": len(resolved),
            "avg_brier_score": avg_brier, "brier_grade": "Excellent" if avg_brier < 0.1 else ("Good" if avg_brier < 0.2 else ("Fair" if avg_brier < 0.3 else "Poor")),
            "overconfident_count": len(overconfident), "well_calibrated_count": len(well_calibrated),
            "overconfident": [p.prediction_statement for p in overconfident],
            "bin_stats": bin_stats,
            "recommendation": "Calibrate by widening confidence intervals." if avg_brier > 0.2 else "Calibration is reasonable."}

def decision_quality_review(decisions):
    """Analyze decision quality across logged decisions."""
    if not decisions:
        return {"total_decisions": 0, "message": "No decisions logged."}
    reviewed = [d for d in decisions if d.actual_outcome]
    scores = []
    for d in decisions:
        s = decision_quality_score(d)
        d.quality_score = s
        scores.append(s)
    avg = round(sum(scores) / len(scores), 1) if scores else 0
    weak_dims = defaultdict(int)
    for d in decisions:
        if d.clarity_of_objective <= 3: weak_dims["clarity_of_objective"] += 1
        if d.quality_of_options <= 3: weak_dims["quality_of_options"] += 1
        if d.evidence_quality <= 3: weak_dims["evidence_quality"] += 1
        if d.opportunity_cost_awareness <= 3: weak_dims["opportunity_cost_awareness"] += 1
        if d.risk_awareness <= 3: weak_dims["risk_awareness"] += 1
    unreviewed = [d for d in decisions if not d.actual_outcome and d.review_date and d.review_date < today_str()]
    return {"total_decisions": len(decisions), "reviewed_count": len(reviewed),
            "avg_quality_score": avg, "quality_grade": "High" if avg >= 7 else ("Adequate" if avg >= 5 else "Low"),
            "weakest_dimensions": sorted(weak_dims.items(), key=lambda x: -x[1]),
            "overdue_review": len(unreviewed),
            "overdue_titles": [d.title for d in unreviewed]}

def leverage_analysis(tasks, outcomes, assets):
    """Find the highest-leverage actions: where small effort creates outsized impact."""
    results = []
    for t in tasks:
        if t.estimated_minutes == 0: continue
        leverage = round(t.final_score / (t.estimated_minutes / 60), 2) if t.estimated_minutes > 0 else 0
        results.append({"name": t.name, "score": t.final_score, "est_hours": round(t.estimated_minutes / 60, 1),
                        "leverage_ratio": leverage, "goal": t.strategic_goal})
    results.sort(key=lambda x: -x["leverage_ratio"])
    # Identify compounding assets
    compounders = [{"name": a.name, "type": a.asset_type, "reuse_count": a.reuse_count,
                    "future_value": a.estimated_future_value} for a in assets if a.reuse_count >= 2 or a.estimated_future_value >= 8]
    return {"high_leverage_tasks": results[:5], "compounding_assets": compounders,
            "summary": f"Top leverage: {results[0]['name']} ({results[0]['leverage_ratio']} pts/hr)" if results else "No tasks to analyze."}

def constraint_diagnosis(tasks, risks, outcomes):
    """Diagnose the binding constraint on strategic progress."""
    constraints = []
    # Risk-based constraints
    high_risks = [r for r in risks if r.severity >= 7 and r.status == "active"]
    for r in high_risks:
        constraints.append({"type": "risk", "name": r.title, "severity": r.severity,
                           "mitigation": bool(r.mitigation), "category": r.category})
    # Stalled outcomes
    for o in outcomes:
        if o.current_status == o.desired_status: continue
        if o.confidence_level <= 3:
            constraints.append({"type": "outcome_uncertainty", "name": o.name,
                               "confidence": o.confidence_level, "gap": f"{o.current_status} -> {o.desired_status}"})
    # Task-based: what's the bottleneck goal?
    goal_counts = defaultdict(int)
    for t in tasks:
        if t.final_score >= 7:
            goal_counts[t.strategic_goal] += 1
    neglected = [g for g in STRATEGIC_GOALS if goal_counts.get(g, 0) == 0]
    if neglected:
        constraints.append({"type": "neglected_goal", "goals": neglected,
                           "detail": f"No high-score tasks for: {', '.join(neglected)}"})
    # Time-based: is too much going to admin?
    admin_mins = sum(t.estimated_minutes for t in tasks if t.strategic_goal == "admin_maintenance")
    total_mins = sum(t.estimated_minutes for t in tasks) or 1
    if admin_mins / total_mins > 0.25:
        constraints.append({"type": "admin_overload", "admin_pct": round(admin_mins / total_mins * 100),
                           "detail": f"Admin consumes {round(admin_mins/total_mins*100)}% of planned time."})
    if constraints:
        bc = constraints[0]
        if "name" in bc:
            rec = f"Address: {bc['name']}"
        elif bc["type"] == "neglected_goal":
            rec = f"Invest in neglected goals: {bc.get('detail', '')}"
        elif bc["type"] == "admin_overload":
            rec = f"Reduce admin time from {bc.get('admin_pct', '?')}%"
        else:
            rec = f"Address constraint: {bc['type']}"
    else:
        rec = "No clear binding constraint detected."
    return {"constraints": constraints, "binding_constraint": constraints[0] if constraints else None,
            "recommendation": rec}

def eighty_twenty_review(tasks, outcomes):
    """Pareto analysis: which 20% of efforts drive 80% of results."""
    if not tasks: return {"message": "No tasks to analyze."}
    sorted_tasks = sorted(tasks, key=lambda t: t.final_score, reverse=True)
    total_score = sum(t.final_score for t in sorted_tasks) or 1
    cumulative = 0
    top_20pct = []
    top20_n = max(1, len(sorted_tasks) // 5)
    for i, t in enumerate(sorted_tasks):
        cumulative += t.final_score
        if i < top20_n:
            top_20pct.append({"name": t.name, "score": t.final_score, "goal": t.strategic_goal})
    top20_score = sum(t.final_score for t in sorted_tasks[:top20_n])
    top20_pct = round(top20_score / total_score * 100, 1)
    bottom_80pct = [{"name": t.name, "score": t.final_score, "goal": t.strategic_goal}
                    for t in sorted_tasks[top20_n:]]
    kill_candidates = [t for t in sorted_tasks if t.final_score < 3 and t.strategic_goal == "admin_maintenance"]
    return {"total_tasks": len(tasks), "top20_count": top20_n,
            "top20_score_pct": top20_pct,
            "top20": top_20pct, "bottom80": bottom_80pct,
            "kill_candidates": [{"name": t.name, "score": t.final_score} for t in kill_candidates],
            "verdict": f"Top {top20_n} tasks deliver {top20_pct}% of total strategic value."}

def bias_detection(tasks, decisions, predictions, records):
    """Detect cognitive biases in planning and decision-making."""
    biases = []
    # Planning fallacy: overcommitted days
    over_days = sum(1 for r in records if r.get("overcommitted", False))
    if over_days >= 3:
        biases.append({"bias": "planning_fallacy", "confidence": min(90, 50 + over_days * 10),
                       "evidence": f"Overcommitted on {over_days} of {len(records)} days.",
                       "fix": "Reduce planned DO tasks by 30% and track actual completion times."})
    # Urgency bias: high urgency, low strategic value tasks
    urgency_tasks = [t for t in tasks if t.urgency >= 8 and t.strategic_value <= 3]
    if urgency_tasks:
        biases.append({"bias": "urgency_bias", "confidence": 70 + len(urgency_tasks) * 5,
                       "evidence": f"{len(urgency_tasks)} task(s) with urgency>=8 but strategic value<=3.",
                       "fix": "Ask: 'Does this truly need to be done today, or is urgency artificial?'"})
    # Sunk cost: projects with hours logged but no progress
    for d in decisions:
        if d.actual_outcome and "didn't work" in d.actual_outcome.lower() and not d.lesson:
            biases.append({"bias": "sunk_cost", "confidence": 65,
                           "evidence": f"Decision '{d.title}' had poor outcome but no lesson captured.",
                           "fix": "Explicitly identify when to walk away before starting."})
    # Avoidance: neglected goals
    if records:
        goal_mins = {g: 0 for g in STRATEGIC_GOALS}
        for r in records:
            for g in STRATEGIC_GOALS:
                goal_mins[g] += r.get("portfolio", {}).get("by_goal", {}).get(g, {}).get("minutes", 0)
        total = sum(goal_mins.values()) or 1
        fully_neglected = [g for g in STRATEGIC_GOALS if goal_mins[g] == 0]
        if fully_neglected:
            biases.append({"bias": "avoidance", "confidence": 60 + len(fully_neglected) * 10,
                           "evidence": f"Zero time on: {', '.join(fully_neglected)}.",
                           "fix": f"Schedule one 30-min block on {fully_neglected[0]} this week."})
    # Overconfidence: predictions with high probability but wrong
    resolved = [p for p in predictions if p.resolved]
    overconf = [p for p in resolved if (p.probability >= 80 and not p.actual_outcome) or
                (p.probability <= 20 and p.actual_outcome)]
    if overconf:
        biases.append({"bias": "overconfidence", "confidence": 60 + len(overconf) * 10,
                       "evidence": f"{len(overconf)} of {len(resolved)} resolved predictions were overconfident.",
                       "fix": "Use 'outside view' reference class for probability estimates."})
    return {"biases_detected": len(biases), "biases": biases,
            "summary": f"Detected {len(biases)} cognitive bias(es)." if biases else "No strong bias signals detected."}

def strategic_scorecard(tasks, outcomes, predictions, decisions, records):
    """Generate a strategic scorecard with scores across dimensions."""
    # Task execution
    completed = sum(len((r.get("reflection") or {}).get("completed_tasks", [])) for r in records)
    total_do = sum(len(r.get("do", [])) for r in records)
    exec_rate = round(completed / total_do * 100, 1) if total_do else 0
    exec_score = 10 if exec_rate >= 80 else (7 if exec_rate >= 60 else (4 if exec_rate >= 40 else 2))
    # Strategic allocation
    if records:
        goal_mins = {g: 0 for g in STRATEGIC_GOALS}
        for r in records:
            for g in STRATEGIC_GOALS:
                goal_mins[g] += r.get("portfolio", {}).get("by_goal", {}).get(g, {}).get("minutes", 0)
        total = sum(goal_mins.values()) or 1
        admin_pct = goal_mins.get("admin_maintenance", 0) / total * 100
        deep_pct = (goal_mins.get("research_publication", 0) + goal_mins.get("grant_funding", 0) +
                    goal_mins.get("deeptech_venture", 0)) / total * 100
    else:
        admin_pct = 0; deep_pct = 0
    alloc_score = 10 if admin_pct < 15 and deep_pct > 50 else (7 if admin_pct < 25 else (4 if admin_pct < 35 else 2))
    # Outcome progress
    progressed = sum(1 for o in outcomes if o.current_status != "" and o.current_status != o.desired_status)
    outcome_score = 8 if progressed > 0 else (5 if outcomes else 3)
    # Calibration
    resolved = [p for p in predictions if p.resolved]
    briers = [p.brier_score for p in resolved if p.brier_score > 0]
    avg_b = sum(briers) / len(briers) if briers else 0
    calib_score = 10 if avg_b < 0.1 else (7 if avg_b < 0.2 else (4 if avg_b < 0.3 else 2)) if briers else (5 if predictions else 5)
    # Decision quality
    d_scores = [decision_quality_score(d) for d in decisions]
    avg_d = sum(d_scores) / len(d_scores) if d_scores else 0
    dec_score = 10 if avg_d >= 7 else (7 if avg_d >= 5 else (4 if avg_d >= 3 else 2)) if d_scores else 5
    dimensions = [
        {"dimension": "Execution Rate", "score": exec_score, "detail": f"{exec_rate}% completion"},
        {"dimension": "Strategic Allocation", "score": alloc_score, "detail": f"{admin_pct:.0f}% admin, {deep_pct:.0f}% deep work"},
        {"dimension": "Outcome Progress", "score": outcome_score, "detail": f"{progressed}/{len(outcomes)} outcomes progressing" if outcomes else "No outcomes defined"},
        {"dimension": "Calibration", "score": calib_score, "detail": f"Avg Brier: {avg_b:.3f}" if briers else "No resolved predictions"},
        {"dimension": "Decision Quality", "score": dec_score, "detail": f"Avg quality: {avg_d:.1f}" if d_scores else "No decisions scored"},
    ]
    overall = round(sum(d["score"] for d in dimensions) / len(dimensions), 1)
    return {"overall_score": overall, "grade": "A" if overall >= 8 else ("B" if overall >= 6 else ("C" if overall >= 4 else "D")),
            "dimensions": dimensions}

def red_team_prompt(tasks, outcomes, decisions, risks, records):
    """Generate an AI red-team prompt to stress-test the strategy."""
    top_tasks = sorted(tasks, key=lambda t: t.final_score, reverse=True)[:3] if tasks else []
    top_risks = sorted(risks, key=lambda r: risk_score(r), reverse=True)[:3] if risks else []
    unresolved = [d for d in decisions if not d.actual_outcome]
    goal_mins = {g: 0 for g in STRATEGIC_GOALS}
    for r in records:
        for g in STRATEGIC_GOALS:
            goal_mins[g] += r.get("portfolio", {}).get("by_goal", {}).get(g, {}).get("minutes", 0)
    total = sum(goal_mins.values()) or 1
    return f"""=== RED-TEAM PROMPT ===
(COPY INTO YOUR AI ASSISTANT)

You are a hostile-but-fair red-team advisor. Your job is to find the flaws in my strategy.

CURRENT STRATEGY:
Top priorities: {'; '.join(t.name for t in top_tasks) if top_tasks else '(none)'}
Top risks: {'; '.join(r.title for r in top_risks) if top_risks else '(none)'}
Unresolved decisions: {len(unresolved)}
Time allocation: {'; '.join(f'{g}: {goal_mins.get(g, 0)/total*100:.0f}%' for g in STRATEGIC_GOALS if goal_mins.get(g, 0) > 0)}

RED-TEAM QUESTIONS:
1. What is the single biggest blind spot in this strategy?
2. If this strategy fails, what will be the root cause?
3. Which assumption, if proven wrong, would collapse the entire plan?
4. What is the most dangerous risk that has NO mitigation?
5. What competing priority is being neglected?
6. If a competitor wanted to exploit my weaknesses, what would they target?
7. What am I optimising for that I shouldn't be?
8. What should I stop doing immediately?

Provide your most uncomfortably honest diagnosis.
=== END RED-TEAM PROMPT ==="""

def board_memo_prompt(outcomes, decisions, assets, risks, records):
    """Generate an AI board-memo prompt for strategic communication."""
    progressed = [o for o in outcomes if o.current_status != o.desired_status] if outcomes else []
    top_assets = sorted(assets, key=lambda a: a.estimated_future_value, reverse=True)[:3] if assets else []
    resolved = [d for d in decisions if d.actual_outcome] if decisions else []
    goal_mins = {g: 0 for g in STRATEGIC_GOALS}
    for r in records:
        for g in STRATEGIC_GOALS:
            goal_mins[g] += r.get("portfolio", {}).get("by_goal", {}).get(g, {}).get("minutes", 0)
    total = sum(goal_mins.values()) or 1
    return f"""=== BOARD MEMO PROMPT ===
(COPY INTO YOUR AI ASSISTANT)

You are an AI strategy advisor. Write a board-level strategic memo based on the following data.

STRATEGIC OUTCOMES:
{chr(10).join(f'- {o.name}: {o.current_status} -> {o.desired_status} (confidence: {o.confidence_level}/10)' for o in progressed) if progressed else '(No outcomes defined)'}

KEY DECISIONS:
{chr(10).join(f'- {d.title}: {d.chosen_option} | Outcome: {d.actual_outcome or "pending"}' for d in resolved) if resolved else '(No resolved decisions)'}

COMPOUNDING ASSETS:
{chr(10).join(f'- {a.name} ({a.asset_type}): reused {a.reuse_count}x, future value: {a.estimated_future_value}/10' for a in top_assets) if top_assets else '(No compounding assets defined)'}

TOP RISKS: {'; '.join(r.title for r in risks[:3]) if risks else '(none)'}

TIME ALLOCATION: {'; '.join(f'{g}: {goal_mins.get(g,0)/total*100:.0f}%' for g in STRATEGIC_GOALS if goal_mins.get(g,0)>0)}

Write a board memo that covers:
1. Executive Summary (3 sentences)
2. Strategic Progress (outcomes achieved, trajectory)
3. Key Decisions Made (and what we learned)
4. Asset Accumulation (what's compounding)
5. Risk Assessment (what keeps us awake)
6. 90-Day Priorities (top 3 moves)
7. Resource Ask (what we need)

Keep it direct, evidence-based, and board-appropriate.
=== END BOARD MEMO PROMPT ===="""

def kill_list_recommendation(tasks, outcomes, decisions, predictions):
    """Recommend what to stop doing, kill, or abandon."""
    kills = []
    # Low-score admin
    for t in tasks:
        if t.strategic_goal == "admin_maintenance" and t.final_score < 3:
            kills.append({"target": t.name, "type": "low_value_admin", "score": t.final_score,
                         "saving_minutes": t.estimated_minutes, "reason": f"Admin task with score {t.final_score} — delete, automate, or batch."})
    # Stalled outcomes with low confidence
    for o in outcomes:
        if o.confidence_level <= 3 and o.current_status == o.desired_status:
            kills.append({"target": o.name, "type": "stalled_outcome", "reason": f"Low-confidence outcome with no progress gap."})
    # Unresolved decisions past review date
    for d in decisions:
        if not d.actual_outcome and d.review_date and d.review_date < today_str():
            kills.append({"target": d.title, "type": "overdue_decision", "reason": f"Decision past review date ({d.review_date}) without outcome."})
    # Predictions never resolved
    old_unresolved = [p for p in predictions if not p.resolved and p.expected_resolution_date and p.expected_resolution_date < today_str()]
    for p in old_unresolved[:3]:
        kills.append({"target": p.prediction_statement, "type": "unresolved_prediction",
                     "reason": f"Prediction past resolution date ({p.expected_resolution_date}) — resolve or archive."})
    total_saved = sum(k.get("saving_minutes", 0) for k in kills)
    return {"kill_items": kills, "total_items": len(kills),
            "total_minutes_saved": total_saved,
            "summary": f"Recommend killing/stopping {len(kills)} items, saving ~{total_saved} min." if kills else "Nothing to kill. All systems nominal."}

def compounding_asset_review(assets):
    """Review compounding assets for reuse and future value."""
    if not assets:
        return {"total_assets": 0, "message": "No assets defined. Assets are reusable templates, materials, contacts, etc."}
    by_type = defaultdict(list)
    for a in assets:
        by_type[a.asset_type].append(a)
    reused = [a for a in assets if a.reuse_count >= 2]
    high_value = [a for a in assets if a.estimated_future_value >= 8]
    # Find assets that should be promoted (high potential, low reuse)
    promote = [{"name": a.name, "type": a.asset_type, "future_value": a.estimated_future_value,
                "reuse": a.reuse_count, "action": "Increase reuse — make this a template."}
              for a in assets if a.estimated_future_value >= 7 and a.reuse_count <= 1]
    # Maintenance needed
    maintain = [{"name": a.name, "type": a.asset_type, "maintenance": a.maintenance_required}
               for a in assets if a.maintenance_required in ("medium", "high")]
    return {"total_assets": len(assets), "reused_assets": len(reused),
            "high_value_assets": len(high_value), "by_type": {k: len(v) for k, v in by_type.items()},
            "promote": promote, "needs_maintenance": maintain,
            "summary": f"{len(assets)} assets, {len(reused)} reused, {len(high_value)} high-value."}
