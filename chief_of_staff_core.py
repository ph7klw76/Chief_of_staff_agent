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
CURRENT_SCHEMA_VERSION = "7.0"
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
IDENTITY_PATH = Path("chief_of_staff_identity.json")
CAPITAL_PATH = Path("chief_of_staff_capital.json")
RHYTHM_PATH = Path("chief_of_staff_rhythm.json")
OKRS_PATH = Path("chief_of_staff_okrs.json")
AUDIT_PATH = Path("chief_of_staff_audit.json")

# V7 constants
CAPITAL_TYPES = ["intellectual_capital","relationship_capital","reputation_capital","financial_capital","technical_capital","teaching_capital","institutional_capital","entrepreneurial_capital","energy_capital"]
SCENARIO_PATHS = ["research_first","grant_first","industry_first","teaching_first","public_influence_first","deeptech_venture_first","balanced","admin_reactive"]
SCENARIO_LABELS = {"research_first":"Research-First Path","grant_first":"Grant-First Path","industry_first":"Industry-Collaboration-First Path","teaching_first":"Teaching-Excellence-First Path","public_influence_first":"Public-Influence-First Path","deeptech_venture_first":"Deep-Tech-Venture-First Path","balanced":"Balanced Path","admin_reactive":"Admin-Reactive Path"}
SCENARIO_GOAL_FOCUS = {"research_first":"research_publication","grant_first":"grant_funding","industry_first":"industry_collaboration","teaching_first":"teaching_excellence","public_influence_first":"public_influence","deeptech_venture_first":"deeptech_venture","balanced":"balanced","admin_reactive":"admin_maintenance"}
DEFAULT_RHYTHMS = [
    {"rhythm_id":"r_daily_priorities","name":"Daily priorities","cadence":"daily","strategic_goal":"all","description":"Choose top 1-3 strategic tasks and protect first deep-work block.","trigger":"start of day","expected_output":"Ranked DO list","status":"active"},
    {"rhythm_id":"r_daily_evidence","name":"Daily evidence/reflection","cadence":"daily","strategic_goal":"all","description":"Record one evidence item or reflection.","trigger":"end of day","expected_output":"Evidence or reflection entry","status":"active"},
    {"rhythm_id":"r_weekly_delayed","name":"Weekly delayed review","cadence":"weekly","strategic_goal":"all","description":"Review delayed high-value tasks. Check admin percentage.","trigger":"Friday afternoon","expected_output":"Delay audit + admin % check","status":"active"},
    {"rhythm_id":"r_weekly_opps","name":"Weekly opportunity & relationship review","cadence":"weekly","strategic_goal":"all","description":"Review opportunities and relationships.","trigger":"Friday afternoon","expected_output":"Stale opportunity list, relationship follow-ups","status":"active"},
    {"rhythm_id":"r_monthly_allocation","name":"Monthly strategic allocation review","cadence":"monthly","strategic_goal":"all","description":"Review strategic allocation vs baseline. Update project statuses.","trigger":"first of month","expected_output":"Allocation audit + project status update","status":"active"},
    {"rhythm_id":"r_monthly_predictions","name":"Monthly prediction & assumption review","cadence":"monthly","strategic_goal":"all","description":"Review predictions and assumptions.","trigger":"first of month","expected_output":"Calibration check + assumption review","status":"active"},
    {"rhythm_id":"r_quarterly_rebalance","name":"Quarterly strategic rebalance","cadence":"quarterly","strategic_goal":"all","description":"Rebalance strategic goals. Kill or pause stale projects. Update doctrine.","trigger":"quarter start","expected_output":"Rebalance recommendation + kill-list","status":"active"},
    {"rhythm_id":"r_yearly_identity","name":"Yearly identity & mission review","cadence":"yearly","strategic_goal":"all","description":"Review identity, mission, and long-term outcomes.","trigger":"birthday or Jan 1","expected_output":"Updated identity + 365-day plan","status":"active"},
]
DEFAULT_IDENTITIES = {
    "world_class_researcher":"Become a world-class organic electronics researcher.",
    "grant_winning_pi":"Become a grant-winning principal investigator.",
    "industry_builder":"Build lasting industry collaborations.",
    "excellent_educator":"Be an excellent lecturer and mentor.",
    "public_communicator":"Be a visible public science communicator.",
    "deeptech_founder":"Eventually create a high-value deep-tech company.",
    "strategic_leader":"Be a strategic leader who builds systems, not just outputs.",
}
REVERSIBILITY_CLASSES = {"one_way_door":"Hard to reverse — requires major commitment","two_way_door":"Easy to reverse — low-cost decision","experiment_first":"Should be tested before full commitment"}

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
        shutil.copyfile(path, bak)
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

# V7 dataclasses
@dataclass
class StrategicIdentity:
    identity_id:str="";name:str="";statement:str="";role:str="";long_term_aim:str=""
    behaviors_that_support:list=field(default_factory=list)
    behaviors_that_contradict:list=field(default_factory=list)
    evidence_of_alignment:list=field(default_factory=list)
    evidence_of_drift:list=field(default_factory=list)
    last_reviewed:str="";status:str="active"

@dataclass
class StrategicCapital:
    capital_id:str="";capital_type:str="intellectual_capital";name:str=""
    current_score:int=5;evidence:list=field(default_factory=list)
    activities_that_increase:list=field(default_factory=list)
    activities_that_decrease:list=field(default_factory=list)
    linked_projects:list=field(default_factory=list)
    linked_assets:list=field(default_factory=list)
    linked_relationships:list=field(default_factory=list)
    last_reviewed:str=""

@dataclass
class Rhythm:
    rhythm_id:str="";name:str="";cadence:str="daily";strategic_goal:str="all"
    description:str="";trigger:str="";expected_output:str=""
    last_completed:str="";next_due:str="";status:str="active"

@dataclass
class KeyResult:
    kr_id:str="";description:str="";metric_type:str="";start_value:float=0.0
    target_value:float=0.0;current_value:float=0.0;progress_percent:float=0.0
    last_updated:str="";status:str="on_track"

@dataclass
class OKR:
    objective_id:str="";title:str="";strategic_goal:str="research_publication"
    period:str="quarterly";start_date:str="";end_date:str="";status:str="active"
    confidence:int=5;key_results:list=field(default_factory=list);notes:str=""

@dataclass
class AuditEntry:
    timestamp:str="";action_type:str="";entity_type:str="";entity_id:str=""
    summary:str="";before_hash:str="";after_hash:str=""

# V7 scenario result
@dataclass
class ScenarioResult:
    path_name:str="";horizon:int=90
    planned_time_allocation:dict=field(default_factory=dict)
    strategic_alignment:float=0.0;expected_compounding:float=0.0
    opportunity_capture:float=0.0;risk_control:float=0.0
    feasibility:float=0.0;energy_sustainability:float=0.0
    scenario_score:float=0.0
    risk_exposure:int=0;relationship_capital_effect:int=0
    publication_progress:int=0;grant_progress:int=0
    venture_progress:int=0;public_influence_effect:int=0
    likely_bottleneck:str="";recommended_correction:str=""

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

# ======================================================================
# V7 — STRATEGIC SIMULATION & GOVERNANCE
# ======================================================================

# --- AI Provider (no-op) ---
class AIProvider:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class NoOpAIProvider(AIProvider):
    def generate(self, prompt: str) -> str:
        return prompt

# --- Audit ---
import hashlib

def hash_dict(d):
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]

def record_audit_event(action_type, entity_type, entity_id, summary, before=None, after=None):
    entries = load_records(AUDIT_PATH)
    entry = AuditEntry(timestamp=datetime.now().isoformat(), action_type=action_type,
                       entity_type=entity_type, entity_id=entity_id, summary=summary,
                       before_hash=hash_dict(before) if before else "",
                       after_hash=hash_dict(after) if after else "")
    entries.append(entry.__dict__)
    save_records(AUDIT_PATH, entries)

def load_audit_log():
    return load_records(AUDIT_PATH)

# --- Scenario Simulator ---
def scenario_simulator(horizon, data):
    """Simulate 8 strategic paths and compare outcomes."""
    results = []
    for path in SCENARIO_PATHS:
        sr = simulate_path(path, horizon, data)
        sr.scenario_score = round(
            sr.strategic_alignment * 0.25 + sr.expected_compounding * 0.20 +
            sr.opportunity_capture * 0.15 + sr.risk_control * 0.15 +
            sr.feasibility * 0.15 + sr.energy_sustainability * 0.10, 2)
        results.append(sr)
    results.sort(key=lambda r: -r.scenario_score)
    return {"horizon": horizon, "scenarios": results, "best": results[0] if results else None}

def simulate_path(path, horizon, data):
    """Simulate a single strategic path."""
    sr = ScenarioResult(path_name=SCENARIO_LABELS.get(path, path), horizon=horizon)
    focus = SCENARIO_GOAL_FOCUS[path]
    # Time allocation simulation
    alloc = {g: 0 for g in STRATEGIC_GOALS}
    if path == "balanced":
        alloc = {"research_publication": 20, "grant_funding": 20, "industry_collaboration": 15,
                 "teaching_excellence": 15, "public_influence": 10, "deeptech_venture": 10, "admin_maintenance": 10}
    elif path == "admin_reactive":
        alloc = {"research_publication": 10, "grant_funding": 10, "industry_collaboration": 5,
                 "teaching_excellence": 10, "public_influence": 5, "deeptech_venture": 5, "admin_maintenance": 55}
    elif focus == "research_publication":
        alloc = {"research_publication": 35, "grant_funding": 20, "industry_collaboration": 10,
                 "teaching_excellence": 10, "public_influence": 10, "deeptech_venture": 10, "admin_maintenance": 5}
    elif focus == "grant_funding":
        alloc = {"research_publication": 15, "grant_funding": 40, "industry_collaboration": 15,
                 "teaching_excellence": 10, "public_influence": 5, "deeptech_venture": 5, "admin_maintenance": 10}
    elif focus == "industry_collaboration":
        alloc = {"research_publication": 15, "grant_funding": 15, "industry_collaboration": 35,
                 "teaching_excellence": 10, "public_influence": 10, "deeptech_venture": 10, "admin_maintenance": 5}
    elif focus == "teaching_excellence":
        alloc = {"research_publication": 15, "grant_funding": 10, "industry_collaboration": 10,
                 "teaching_excellence": 35, "public_influence": 15, "deeptech_venture": 5, "admin_maintenance": 10}
    elif focus == "public_influence":
        alloc = {"research_publication": 15, "grant_funding": 10, "industry_collaboration": 10,
                 "teaching_excellence": 10, "public_influence": 35, "deeptech_venture": 10, "admin_maintenance": 10}
    elif focus == "deeptech_venture":
        alloc = {"research_publication": 10, "grant_funding": 10, "industry_collaboration": 15,
                 "teaching_excellence": 5, "public_influence": 10, "deeptech_venture": 40, "admin_maintenance": 10}
    sr.planned_time_allocation = alloc
    # Compute dimension scores based on path and horizon
    cfg = data.get("config", DEFAULT_CONFIG)
    baseline = cfg.get("strategic_baseline", {})
    records = data.get("records", [])
    projs = data.get("projects", [])
    risks = data.get("risks", [])
    outcomes = data.get("outcomes", [])
    opps = data.get("opportunities", [])
    # Strategic alignment
    alignment_score = 5
    if path == "balanced": alignment_score = 8
    elif path == "admin_reactive": alignment_score = 2
    elif focus in ["research_publication", "grant_funding"]: alignment_score = 9
    elif focus in ["industry_collaboration", "deeptech_venture"]: alignment_score = 7
    elif focus in ["teaching_excellence", "public_influence"]: alignment_score = 6
    sr.strategic_alignment = alignment_score
    # Expected compounding
    compound_score = 5
    if focus == "research_publication": compound_score = 9
    elif focus == "grant_funding": compound_score = 8
    elif focus == "deeptech_venture": compound_score = 8
    elif focus == "industry_collaboration": compound_score = 7
    elif focus == "public_influence": compound_score = 6
    elif path == "balanced": compound_score = 7
    sr.expected_compounding = compound_score
    # Opportunity capture
    opp_score_val = 5
    if focus == "grant_funding": opp_score_val = 9
    elif focus == "industry_collaboration": opp_score_val = 8
    elif focus == "deeptech_venture": opp_score_val = 7
    elif path == "balanced": opp_score_val = 7
    elif path == "admin_reactive": opp_score_val = 2
    sr.opportunity_capture = opp_score_val
    # Risk control
    risk_vals = {"research_first": 7, "grant_first": 6, "industry_first": 5, "teaching_first": 7,
                 "public_influence_first": 5, "deeptech_venture_first": 4, "balanced": 7, "admin_reactive": 3}
    sr.risk_control = risk_vals.get(path, 5)
    # Feasibility
    feas = {"research_first": 8, "grant_first": 7, "industry_first": 7, "teaching_first": 8,
            "public_influence_first": 7, "deeptech_venture_first": 5, "balanced": 8, "admin_reactive": 9}
    sr.feasibility = feas.get(path, 5)
    # Energy sustainability
    energy = {"research_first": 6, "grant_first": 7, "industry_first": 7, "teaching_first": 8,
              "public_influence_first": 7, "deeptech_venture_first": 5, "balanced": 8, "admin_reactive": 5}
    sr.energy_sustainability = energy.get(path, 5)
    # Path-specific effects
    h_factor = horizon / 90
    sr.risk_exposure = round(risk_vals.get(path, 5) * h_factor)
    sr.publication_progress = round(alloc.get("research_publication", 0) / 5 * h_factor)
    sr.grant_progress = round(alloc.get("grant_funding", 0) / 5 * h_factor)
    sr.venture_progress = round(alloc.get("deeptech_venture", 0) / 5 * h_factor)
    sr.public_influence_effect = round(alloc.get("public_influence", 0) / 5 * h_factor)
    sr.relationship_capital_effect = round(alloc.get("industry_collaboration", 0) / 5 * h_factor)
    # Bottleneck
    if sr.risk_exposure >= 7: sr.likely_bottleneck = "risk_exposure"
    elif alloc.get("admin_maintenance", 0) > 30: sr.likely_bottleneck = "admin_overload"
    elif path == "deeptech_venture_first" and horizon < 180: sr.likely_bottleneck = "time_horizon_too_short"
    else: sr.likely_bottleneck = "none_specific"
    # Recommendation
    if path == "admin_reactive": sr.recommended_correction = "Shift to any active strategic path immediately."
    elif sr.risk_exposure >= 7: sr.recommended_correction = "Add risk mitigations before committing."
    elif alloc.get("admin_maintenance", 0) < 5: sr.recommended_correction = "Ensure admin does not drop below minimum sustainable level."
    else: sr.recommended_correction = "Path viable — monitor leading indicators."
    return sr

# --- Trade-off Engine ---
def tradeoff_engine(option_a, option_b, option_c=None):
    """Compare 2-3 options across multiple dimensions."""
    options = [option_a, option_b]
    if option_c: options.append(option_c)
    results = []
    for i, opt in enumerate(options):
        ev = opt.get("expected_value", 5) * 0.25 + opt.get("risk", 3) * -0.15 + opt.get("strategic_goal_served_score", 5) * 0.20 + opt.get("opportunity_cost", 3) * -0.15 + opt.get("evidence_strength", 5) * 0.15 + opt.get("reversibility_score", 5) * 0.10
        results.append({"option": chr(65 + i), "label": opt.get("label", f"Option {chr(65+i)}"), "expected_value": opt.get("expected_value", 5), "risk": opt.get("risk", 3), "opportunity_cost": opt.get("opportunity_cost", 3), "evidence_strength": opt.get("evidence_strength", 5), "reversibility_class": opt.get("reversibility_class", "two_way_door"), "uncertainty": opt.get("uncertainty", "medium"), "hidden_cost": opt.get("hidden_cost", ""), "score": round(ev, 2)})
    results.sort(key=lambda r: -r["score"])
    best = results[0]
    rec = f"Recommend: {best['label']} (score: {best['score']})"
    change_rec = ""
    if len(results) >= 2 and best["score"] - results[1]["score"] < 0.5:
        change_rec = "Close call — small new evidence could change the recommendation."
    elif best["uncertainty"] == "high":
        change_rec = "High uncertainty — gather more evidence before committing."
    return {"options": results, "recommendation": rec, "what_would_change": change_rec or "Recommendation is stable with current evidence."}

# --- Operating Rhythm ---
def load_rhythms():
    data = load_records(RHYTHM_PATH)
    if not data:
        defaults = [Rhythm(**r) for r in DEFAULT_RHYTHMS]
        save_records(RHYTHM_PATH, [r.__dict__ for r in defaults])
        return defaults
    return [Rhythm(**r) for r in data]

def save_rhythms(rs):
    save_records(RHYTHM_PATH, [r.__dict__ for r in rs])

def rhythm_review(rhythms=None):
    if rhythms is None: rhythms = load_rhythms()
    now = date.today()
    overdue = []
    cadence_days = {"daily": 0, "weekly": 7, "monthly": 30, "quarterly": 90, "yearly": 365}
    for r in rhythms:
        if r.status != "active": continue
        if r.last_completed:
            try:
                last = date.fromisoformat(r.last_completed)
                days_since = (now - last).days
                if days_since > cadence_days.get(r.cadence, 7):
                    overdue.append({"name": r.name, "cadence": r.cadence, "days_overdue": days_since,
                                    "last_completed": r.last_completed, "trigger": r.trigger})
            except ValueError:
                overdue.append({"name": r.name, "cadence": r.cadence, "days_overdue": "unknown",
                                "last_completed": r.last_completed, "trigger": r.trigger})
        else:
            overdue.append({"name": r.name, "cadence": r.cadence, "days_overdue": "never",
                            "last_completed": "never", "trigger": r.trigger})
    return {"total": len(rhythms), "active": sum(1 for r in rhythms if r.status == "active"),
            "overdue": overdue, "summary": f"{len(overdue)} of {len(rhythms)} rhythm items overdue."}

# --- Identity Review ---
def identity_review(identities, records, tasks, decisions):
    """Compare behavior against declared identity and detect drift."""
    if not identities: return {"message": "No identities defined. Use --add-identity."}
    results = []
    for ident in identities:
        alignment = []; drift = []
        role = ident.role or ident.name
        role_goals = {"World-Class Researcher": "research_publication", "Grant-Winning PI": "grant_funding",
                      "Industry Builder": "industry_collaboration", "Excellent Educator": "teaching_excellence",
                      "Public Communicator": "public_influence", "Deep-Tech Founder": "deeptech_venture",
                      "Strategic Leader": "balanced"}
        expected_goal = role_goals.get(role, "research_publication")
        # Check time allocation against identity role
        if records:
            goal_mins = {g: 0 for g in STRATEGIC_GOALS}
            for r in records[-14:]:
                for g in STRATEGIC_GOALS:
                    goal_mins[g] += r.get("portfolio", {}).get("by_goal", {}).get(g, {}).get("minutes", 0)
            total = sum(goal_mins.values()) or 1
            # Map identity to expected goals
            goal_pct = goal_mins.get(expected_goal, 0) / total * 100
            if goal_pct >= 15:
                alignment.append(f"{goal_pct:.0f}% time on {expected_goal} — aligned with {role}.")
            else:
                drift.append(f"Only {goal_pct:.0f}% time on {expected_goal} — drifting from {role}.")
            admin_pct = goal_mins.get("admin_maintenance", 0) / total * 100
            if admin_pct > 25:
                drift.append(f"Admin at {admin_pct:.0f}% — may crowd out {expected_goal}.")
        # Delayed tasks
        delayed = []
        for r in records[-14:]:
            for t in r.get("delay", []):
                n = t.get("name", ""); delayed.append(n)
        if len(delayed) > 5:
            drift.append(f"{len(delayed)} delayed tasks in last 14 days.")
        corrections = []
        if drift:
            corrections.append(f"Protect two 90-minute {expected_goal} blocks before admin tasks.")
            if admin_pct > 25: corrections.append("Reduce admin by batching or delegating non-strategic tasks.")
        results.append({"identity": ident.name, "role": role, "alignment": alignment, "drift": drift,
                        "corrections": corrections, "verdict": "Aligned" if not drift else "Drift detected"})
    return {"identities": results, "overall_drift": sum(1 for r in results if r["verdict"] != "Aligned")}

# --- Strategic Capital ---
def capital_review(capitals):
    """Review strategic capital: growing, decaying, most important."""
    if not capitals:
        return {"total": 0, "message": "No capital defined. Use --add-capital."}
    growing = [c for c in capitals if c.current_score >= 7]
    decaying = [c for c in capitals if c.current_score <= 3]
    sorted_cap = sorted(capitals, key=lambda c: -c.current_score)
    recommendations = []
    for c in decaying:
        if c.activities_that_increase:
            recommendations.append(f"Increase {c.capital_type}: {c.activities_that_increase[0]}")
    return {"total": len(capitals), "growing": len(growing), "decaying": len(decaying),
            "top_3": [{"name": c.name, "type": c.capital_type, "score": c.current_score} for c in sorted_cap[:3]],
            "decaying_details": [{"name": c.name, "type": c.capital_type, "score": c.current_score,
                                  "how_to_increase": c.activities_that_increase[:2]} for c in decaying],
            "recommendations": recommendations,
            "summary": f"{len(growing)} capitals growing, {len(decaying)} decaying."}

# --- 30/90/365-day Plan Generator ---
def plan_generator(horizon, data):
    """Generate a strategic plan for a given horizon."""
    outcomes = data.get("outcomes", [])
    projs = data.get("projects", [])
    opps = data.get("opportunities", [])
    risks = data.get("risks", [])
    assets = data.get("assets", [])
    decisions = data.get("decisions", [])
    relationships = data.get("relationships", [])
    hypotheses = data.get("hypotheses", [])
    experiments = data.get("experiments", [])
    predictions = data.get("predictions", [])
    records = data.get("records", [])
    cfg = data.get("config", DEFAULT_CONFIG)
    goal_mins = {g: 0 for g in STRATEGIC_GOALS}
    for r in records:
        for g in STRATEGIC_GOALS: goal_mins[g] += r.get("portfolio", {}).get("by_goal", {}).get(g, {}).get("minutes", 0)
    total = sum(goal_mins.values()) or 1
    active_projs = [p for p in projs if getattr(p, "status", "active") == "active"]
    top_opps = sorted(opps, key=lambda o: opp_score(o) if hasattr(o, "potential_value") else 0, reverse=True)[:3]
    top_risks = sorted(risks, key=lambda r: risk_score(r) if hasattr(r, "probability") else 0, reverse=True)[:3]
    active_rels = [r for r in relationships if getattr(r, "status", "active") == "active"]
    top_assets = sorted(assets, key=lambda a: getattr(a, "estimated_future_value", 0), reverse=True)[:3]
    stale_opps = [o for o in opps if getattr(o, "status", "") == "open" and getattr(o, "last_touched_date", "") and getattr(o, "last_touched_date", "") < today_str()]
    unresolved_decisions = [d for d in decisions if not getattr(d, "actual_outcome", "")]
    unresolvable_preds = [p for p in predictions if not getattr(p, "resolved", False)]
    return {
        "horizon": horizon,
        "strategic_thesis": f"Over {horizon} days: {'Build deep research capability.' if horizon <= 30 else 'Establish grant pipeline and industry partnerships.' if horizon <= 90 else 'Build a self-sustaining research program with diversified funding, public influence, and venture optionality.'}",
        "top_outcomes": [getattr(o, "name", str(o)) for o in outcomes[:3]] if outcomes else ["Define 3 strategic outcomes"],
        "projects_to_protect": [getattr(p, "name", str(p)) for p in active_projs[:3]] if active_projs else ["Prioritize one active project"],
        "opportunities_to_pursue": [getattr(o, "name", str(o)) for o in top_opps] if top_opps else ["Identify one grant or collaboration opportunity"],
        "relationships_to_strengthen": [getattr(r, "name", str(r)) for r in active_rels[:3]] if active_rels else ["Reconnect with one dormant collaborator"],
        "assets_to_build": [getattr(a, "name", str(a)) for a in top_assets] if top_assets else ["Create one reusable template or dataset"],
        "risks_to_mitigate": [getattr(r, "title", str(r)) for r in top_risks] if top_risks else ["Identify and mitigate top 3 risks"],
        "assumptions_to_test": [getattr(h, "statement", str(h)) for h in hypotheses[:3]] if hypotheses else ["Test one key assumption about your strategy"],
        "experiments_to_run": [getattr(e, "title", str(e)) for e in experiments[:3]] if experiments else ["Run one minimum viable experiment"],
        "rhythms_to_schedule": ["Daily: priorities + deep work block", "Weekly: delayed tasks + admin % check"],
        "kill_list_items": [f"Stale opportunity: {getattr(o, 'name', str(o))}" for o in stale_opps[:2]] + [f"Unresolved decision: {getattr(d, 'title', str(d))}" for d in unresolved_decisions[:2]] + [f"Unresolved prediction: {getattr(p, 'prediction_statement', str(p))}" for p in unresolvable_preds[:2]],
        "success_metrics": [f"Complete {max(1, horizon // 30)} major milestone(s)", f"Keep admin < 25% of time", f"Resolve all predictions within horizon"],
    }

# --- Backcasting ---
def backcast_generator(outcome, target_date_str, why_matters, success_metric):
    """Reverse-engineer a long-term goal into milestones and present action."""
    try: target = date.fromisoformat(target_date_str)
    except ValueError: target = date.today() + timedelta(days=365)
    days = (target - date.today()).days
    if days <= 0: days = 365
    milestones = []
    months = max(3, days // 30)
    chunk = max(1, months // 4)
    for i in range(months, 0, -chunk):
        m = months - i + chunk
        if m <= 1: milestones.append(f"Month 1: Define scope, identify collaborators, draft concept note.")
        elif m <= months * 0.5: milestones.append(f"Month {m}: Build preliminary data, materials, or relationships.")
        elif m <= months * 0.8: milestones.append(f"Month {m}: Draft full proposal, gather feedback, iterate.")
        else: milestones.append(f"Month {m}: Finalize, submit, or launch.")
    return {"desired_outcome": outcome, "target_date": target_date_str, "why_it_matters": why_matters,
            "success_metric": success_metric, "total_months": months,
            "milestones": milestones, "required_weekly_rhythm": "Dedicate 2 focused blocks per week to this outcome.",
            "leading_indicators": ["Concept note drafted", "Collaborator confirmed", "Preliminary data collected",
                                    "First draft complete", "Feedback received"],
            "risks": ["Scope creep", "Competing priorities", "Collaborator availability"],
            "first_next_action": f"This week: Draft the one-page concept note and contact one potential collaborator."}

# --- OKR ---
def load_okrs():
    data = load_records(OKRS_PATH)
    return [OKR(**o) for o in data] if data else []

def save_okrs(okrs):
    records = []
    for o in okrs:
        d = o.__dict__.copy()
        d["key_results"] = [kr.__dict__ if isinstance(kr, KeyResult) else kr for kr in d.get("key_results", [])]
        records.append(d)
    save_records(OKRS_PATH, records)

def okr_review(okrs=None):
    if okrs is None: okrs = load_okrs()
    if not okrs: return {"total": 0, "message": "No OKRs defined. Use --add-okr."}
    results = []
    for o in okrs:
        krs = o.key_results if isinstance(o.key_results, list) else []
        kr_status = []
        for kr in krs:
            if isinstance(kr, dict):
                pct = kr.get("progress_percent", 0)
                kr_status.append({"description": kr.get("description", ""), "progress": pct,
                                  "status": "on_track" if pct >= 50 else ("at_risk" if pct >= 25 else "blocked")})
            elif isinstance(kr, KeyResult):
                kr_status.append({"description": kr.description, "progress": kr.progress_percent,
                                  "status": kr.status})
        avg_progress = round(sum(k["progress"] for k in kr_status) / len(kr_status), 1) if kr_status else 0
        blocked = [k for k in kr_status if k["status"] == "blocked"]
        results.append({"objective": o.title, "strategic_goal": o.strategic_goal, "period": o.period,
                        "confidence": o.confidence, "avg_progress": avg_progress,
                        "key_results": kr_status, "blocked_count": len(blocked),
                        "next_action": "Unblock a key result" if blocked else "Update progress on all KRs"})
    return {"total": len(okrs), "objectives": results,
            "summary": f"{len(okrs)} objectives, avg progress: {round(sum(r['avg_progress'] for r in results)/len(results), 1) if results else 0}%"}

# --- Rebalance ---
def rebalance_engine(records, config, okrs, outcomes, capitals):
    """Compare actual allocation to baseline + strategic needs and recommend changes."""
    cfg = config or DEFAULT_CONFIG
    baseline = cfg.get("strategic_baseline", {})
    goal_mins = {g: 0 for g in STRATEGIC_GOALS}
    for r in records[-30:]:
        for g in STRATEGIC_GOALS:
            goal_mins[g] += r.get("portfolio", {}).get("by_goal", {}).get(g, {}).get("minutes", 0)
    total = sum(goal_mins.values()) or 1
    actual_pcts = {g: round(goal_mins[g] / total * 100, 1) for g in STRATEGIC_GOALS}
    adjustments = []
    for g in STRATEGIC_GOALS:
        actual = actual_pcts.get(g, 0)
        target = baseline.get(g, 15)
        gap = target - actual
        if gap > 10: adjustments.append({"goal": g, "actual_pct": actual, "target_pct": target,
                                          "gap": round(gap, 1), "action": f"Increase {g} by {round(gap)}% (~{round(gap * 2)} min/day)."})
        elif gap < -10: adjustments.append({"goal": g, "actual_pct": actual, "target_pct": target,
                                             "gap": round(gap, 1), "action": f"Reduce {g} by {round(-gap)}%."})
    # Check capital needs
    if capitals:
        decaying = [c for c in capitals if c.current_score <= 3]
        if decaying:
            adjustments.append({"goal": "strategic_capital", "action": f"Invest in decaying capital: {decaying[0].capital_type}."})
    # Check OKR needs
    if okrs:
        active_okrs = [o for o in okrs if o.status == "active"]
        for o in active_okrs[:2]:
            adjustments.append({"goal": f"okr:{o.title}", "action": f"Allocate time to advance OKR: {o.title}."})
    return {"actual_allocation": actual_pcts, "baseline": baseline,
            "adjustments": adjustments,
            "summary": f"{len(adjustments)} adjustment(s) recommended." if adjustments else "Allocation is aligned. No changes needed.",
            "top_recommendation": adjustments[0]["action"] if adjustments else "Maintain current allocation."}

# --- Integrity Check ---
def integrity_check():
    """Check data integrity across all stores."""
    issues = []
    stores = {"projects": (PROJECTS_PATH, Project), "opportunities": (OPPORTUNITIES_PATH, Opportunity),
              "decisions": (DECISIONS_PATH, Decision), "experiments": (EXPERIMENTS_PATH, Experiment),
              "risks": (RISKS_PATH, Risk), "relationships": (RELATIONSHIPS_PATH, Relationship),
              "principles": (PRINCIPLES_PATH, Principle), "outcomes": (OUTCOMES_PATH, Outcome),
              "evidence": (EVIDENCE_PATH, Evidence), "assumptions": (ASSUMPTIONS_PATH, Assumption),
              "predictions": (PREDICTIONS_PATH, Prediction), "hypotheses": (HYPOTHESES_PATH, Hypothesis),
              "assets": (ASSETS_PATH, Asset), "doctrine": (DOCTRINE_PATH, Doctrine),
              "identity": (IDENTITY_PATH, StrategicIdentity), "capital": (CAPITAL_PATH, StrategicCapital),
              "rhythm": (RHYTHM_PATH, Rhythm), "okrs": (OKRS_PATH, OKR)}
    # Check JSON files for corruption
    for name, (path, _) in stores.items():
        if path.exists():
            try: json.loads(path.read_text())
            except json.JSONDecodeError: issues.append(f"Corrupt JSON: {path}")
    # Check schema versions
    for name, (path, _) in stores.items():
        if path.exists():
            try:
                data = json.loads(path.read_text())
                if isinstance(data, dict) and "records" in data:
                    if "schema_version" not in data: issues.append(f"Missing schema_version: {name}")
                    if "updated_at" not in data: issues.append(f"Missing updated_at: {name}")
            except: pass
    # Check for duplicate IDs
    for name, (path, cls) in stores.items():
        if path.exists():
            try:
                data = json.loads(path.read_text())
                records = data.get("records", data) if isinstance(data, dict) else data
                if isinstance(records, list):
                    ids = {}
                    for r in records:
                        if isinstance(r, dict):
                            for id_field in [f"{name.rstrip('s')}_id", "id"]:
                                if id_field in r and r[id_field]:
                                    if r[id_field] in ids: issues.append(f"Duplicate ID {r[id_field]} in {name}")
                                    ids[r[id_field]] = True
                                    break
            except: pass
    # Check broken project links
    proj_ids = set()
    if PROJECTS_PATH.exists():
        try:
            data = json.loads(PROJECTS_PATH.read_text())
            records = data.get("records", data) if isinstance(data, dict) else data
            proj_ids = {r.get("project_id", "") for r in records if isinstance(r, dict)}
        except: pass
    for name, (path, _) in stores.items():
        if name == "projects" or not path.exists(): continue
        try:
            data = json.loads(path.read_text())
            records = data.get("records", data) if isinstance(data, dict) else data
            if isinstance(records, list):
                for r in records:
                    if isinstance(r, dict):
                        pid = r.get("project_id") or r.get("linked_project_id")
                        if pid and pid not in proj_ids and proj_ids: issues.append(f"Broken project link in {name}: {pid}")
        except: pass
    return {"issues": issues, "total_issues": len(issues),
            "summary": f"{len(issues)} integrity issue(s) found." if issues else "All integrity checks passed."}

def repair_integrity():
    """Safely repair fixable integrity issues. Never deletes user data."""
    repairs = []
    stores = [(PROJECTS_PATH, "projects"), (OPPORTUNITIES_PATH, "opportunities"),
              (DECISIONS_PATH, "decisions"), (EXPERIMENTS_PATH, "experiments"),
              (RISKS_PATH, "risks"), (RELATIONSHIPS_PATH, "relationships"),
              (PRINCIPLES_PATH, "principles"), (OUTCOMES_PATH, "outcomes"),
              (EVIDENCE_PATH, "evidence"), (ASSUMPTIONS_PATH, "assumptions"),
              (PREDICTIONS_PATH, "predictions"), (HYPOTHESES_PATH, "hypotheses"),
              (ASSETS_PATH, "assets"), (DOCTRINE_PATH, "doctrine"),
              (IDENTITY_PATH, "identity"), (CAPITAL_PATH, "capital"),
              (RHYTHM_PATH, "rhythm"), (OKRS_PATH, "okrs")]
    for path, name in stores:
        if not path.exists(): continue
        try:
            data = json.loads(path.read_text())
            modified = False
            if isinstance(data, dict) and "records" in data:
                if "schema_version" not in data:
                    data["schema_version"] = CURRENT_SCHEMA_VERSION; modified = True
                    repairs.append(f"Added schema_version to {name}")
                if "updated_at" not in data:
                    data["updated_at"] = today_str(); modified = True
                    repairs.append(f"Added updated_at to {name}")
                # Remove empty IDs
                records = data.get("records", [])
                if isinstance(records, list):
                    for r in records:
                        if isinstance(r, dict):
                            for id_field in [f"{name.rstrip('s')}_id"]:
                                if id_field in r and not r[id_field]:
                                    r[id_field] = uid(); modified = True
                                    repairs.append(f"Assigned new ID in {name}")
            if modified:
                bak = path.with_suffix(path.suffix + ".bak")
                if not bak.exists(): shutil.copyfile(path, bak)
                path.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, OSError): pass
    return {"repairs": repairs, "total_repairs": len(repairs),
            "summary": f"{len(repairs)} repair(s) applied." if repairs else "No repairs needed."}

# --- Local Search ---
def local_search(query):
    """Search across all JSON stores for a query string."""
    q = query.lower()
    results = []
    stores = [(PROJECTS_PATH, "Project"), (OPPORTUNITIES_PATH, "Opportunity"),
              (DECISIONS_PATH, "Decision"), (EXPERIMENTS_PATH, "Experiment"),
              (RISKS_PATH, "Risk"), (RELATIONSHIPS_PATH, "Relationship"),
              (OUTCOMES_PATH, "Outcome"), (EVIDENCE_PATH, "Evidence"),
              (ASSUMPTIONS_PATH, "Assumption"), (PREDICTIONS_PATH, "Prediction"),
              (HYPOTHESES_PATH, "Hypothesis"), (ASSETS_PATH, "Asset"),
              (DOCTRINE_PATH, "Doctrine"), (OKRS_PATH, "OKR"),
              (IDENTITY_PATH, "Identity"), (CAPITAL_PATH, "Capital"),
              (RHYTHM_PATH, "Rhythm")]
    for path, store_type in stores:
        if not path.exists(): continue
        try:
            data = json.loads(path.read_text())
            records = data.get("records", data) if isinstance(data, dict) else data
            if isinstance(records, list):
                for r in records:
                    if isinstance(r, dict) and q in json.dumps(r).lower():
                        name = r.get("name") or r.get("title") or r.get("statement") or r.get("principle") or r.get("prediction_statement") or r.get("description", "")
                        results.append({"store": store_type, "name": str(name)[:60],
                                        "match": str(r.get("name") or r.get("title") or "")[:60]})
        except: pass
    # Search history
    for f in sorted(HISTORY_DIR.glob("*_plan.json")) if HISTORY_DIR.exists() else []:
        try:
            data = json.loads(f.read_text())
            if q in json.dumps(data).lower():
                results.append({"store": "History", "name": f.stem.replace("_plan", ""), "match": f"Plan from {f.stem.replace('_plan', '')}"})
        except: pass
    return {"query": query, "results": results, "total": len(results),
            "summary": f"Found {len(results)} result(s) for '{query}'."}

# --- Report Pack ---
def generate_report_pack(export_dir=None):
    """Generate a folder of strategic reports."""
    if export_dir is None:
        export_dir = Path(f"reports/{today_str()}_strategy_pack")
    export_dir = Path(export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    reports = {}
    # Dashboard
    try:
        tasks = demo_tasks()
        do_tasks = [t for t in tasks if t.get("final_score", 0) >= 4][:3]
        do_names = [t["name"] for t in do_tasks]
        reports["dashboard.txt"] = f"DO ({len(do_names)}): {', '.join(do_names)}\n"
    except: reports["dashboard.txt"] = "Dashboard unavailable.\n"
    # Scorecard
    try:
        data = gather_all_data()
        sc = strategic_scorecard(data.get("tasks", []), data.get("outcomes", []), data.get("predictions", []), data.get("decisions", []), data.get("records", []))
        reports["scorecard.txt"] = f"Overall: {sc['overall_score']}/10 ({sc['grade']})\n" + "\n".join(f"{d['dimension']}: {d['score']}/10 — {d['detail']}" for d in sc["dimensions"])
    except: reports["scorecard.txt"] = "Scorecard unavailable.\n"
    # Strategy memo
    try:
        memo_lines = []
        records = load_recent_history(30); cfg = load_config()
        projs = [Project(**p) for p in load_json(PROJECTS_PATH, [])] if PROJECTS_PATH.exists() else []
        opps = [Opportunity(**o) for o in load_json(OPPORTUNITIES_PATH, [])] if OPPORTUNITIES_PATH.exists() else []
        risks = [Risk(**r) for r in load_json(RISKS_PATH, [])] if RISKS_PATH.exists() else []
        memo_lines.append(f"STRATEGIC MEMO — {today_str()}")
        memo_lines.append(f"Active projects: {sum(1 for p in projs if p.status=='active')}")
        memo_lines.append(f"Open opportunities: {sum(1 for o in opps if o.status=='open')}")
        memo_lines.append(f"Active risks: {sum(1 for r in risks if r.status=='active')}")
        reports["strategy_memo.txt"] = "\n".join(memo_lines)
    except: reports["strategy_memo.txt"] = "Strategy memo unavailable.\n"
    # Red-team and board memo prompts
    try:
        data = gather_all_data()
        reports["red_team_prompt.txt"] = red_team_prompt(data.get("tasks", []), data.get("outcomes", []), data.get("decisions", []), data.get("risks", []), data.get("records", []))
        reports["board_memo_prompt.txt"] = board_memo_prompt(data.get("outcomes", []), data.get("decisions", []), data.get("assets", []), data.get("risks", []), data.get("records", []))
    except:
        reports["red_team_prompt.txt"] = "Red-team prompt unavailable.\n"
        reports["board_memo_prompt.txt"] = "Board memo prompt unavailable.\n"
    # Write all reports
    for filename, content in reports.items():
        (export_dir / filename).write_text(str(content))
    return {"export_dir": str(export_dir), "files": list(reports.keys()), "count": len(reports)}

def gather_all_data():
    """Gather all store data for report pack generation."""
    data = {}
    data["config"] = load_config()
    data["records"] = load_recent_history(90)
    for path, name in [(PROJECTS_PATH, "projects"), (OPPORTUNITIES_PATH, "opportunities"),
                        (DECISIONS_PATH, "decisions"), (EXPERIMENTS_PATH, "experiments"),
                        (RISKS_PATH, "risks"), (RELATIONSHIPS_PATH, "relationships"),
                        (OUTCOMES_PATH, "outcomes"), (EVIDENCE_PATH, "evidence"),
                        (ASSUMPTIONS_PATH, "assumptions"), (PREDICTIONS_PATH, "predictions"),
                        (HYPOTHESES_PATH, "hypotheses"), (ASSETS_PATH, "assets"), (DOCTRINE_PATH, "doctrine")]:
        try:
            if path.exists():
                raw = json.loads(path.read_text())
                data[name] = raw.get("records", raw) if isinstance(raw, dict) else raw
        except: data[name] = []
    # Get demo tasks
    try:
        result = demo_tasks()
        data["tasks"] = [Task(**t) for t in result] if result else []
    except: data["tasks"] = []
    return data

def demo_tasks():
    """Return demo ranked tasks as dicts without importing agent."""
    ah = 6.0; energy = 7
    tasks = [Task("Write grant proposal outline", 9, 9, 10, 8, 10, 9, 8, 2, 9, 120, "grant_funding", "Open Overleaf and draft the 1-page outline"),
             Task("Review literature on OPV materials", 6, 5, 9, 7, 9, 4, 7, 3, 7, 90, "research_publication", "Pull 5 recent papers from Google Scholar"),
             Task("Prepare slides for lab meeting", 5, 8, 4, 3, 5, 8, 6, 3, 4, 45, "teaching_excellence", "Copy template and update figures", True),
             Task("Reply to industry partner email", 7, 6, 8, 6, 8, 5, 7, 2, 3, 20, "industry_collaboration", "Draft reply in 3 bullet points"),
             Task("Update CV & publication list", 5, 3, 7, 5, 7, 2, 5, 4, 3, 60, "public_influence", "Add the 2 recent accepted papers", True),
             Task("Organise lab inventory", 2, 2, 1, 1, 1, 1, 2, 8, 2, 90, "admin_maintenance", "", True)]
    ranked = rank_tasks(tasks)
    return [ser_task(t) for t in ranked]

# --- AI Council Prompt ---
def ai_council_prompt():
    """Generate a multi-role AI council prompt."""
    data = gather_all_data()
    tasks = data.get("tasks", [])
    records = data.get("records", [])
    projs = data.get("projects", [])
    risks = data.get("risks", [])
    opps = data.get("opportunities", [])
    outcomes = data.get("outcomes", [])
    predictions = data.get("predictions", [])
    decisions = data.get("decisions", [])
    capitals = data.get("capital", [])
    scorecard = strategic_scorecard(tasks, outcomes, predictions, decisions, records)
    top_tasks = [t.name for t in tasks[:3]] if tasks else ["(none)"]
    top_risks = [r.get("title", "") if isinstance(r, dict) else r.title for r in risks[:3]] if risks else ["(none)"]
    return f"""=== AI STRATEGIC COUNCIL PROMPT ===
(COPY INTO YOUR AI ASSISTANT)

You are a council of 10 strategic advisors. Review the data and provide your candid assessment.

--- STRATEGIC DATA ---
Scorecard: {scorecard['overall_score']}/10 ({scorecard['grade']})
Top priorities: {'; '.join(top_tasks)}
Top risks: {'; '.join(top_risks)}
Open opportunities: {len(opps) if isinstance(opps, list) else 0}
Active projects: {sum(1 for p in projs if (isinstance(p, dict) and p.get('status')=='active') or (hasattr(p, 'status') and p.status=='active')) if isinstance(projs, list) else 0}
Capital health: {sum(1 for c in capitals if (isinstance(c, dict) and c.get('current_score', 5) >= 7) or (hasattr(c, 'current_score') and c.current_score >= 7)) if isinstance(capitals, list) else 0} growing / {sum(1 for c in capitals if (isinstance(c, dict) and c.get('current_score', 5) <= 3) or (hasattr(c, 'current_score') and c.current_score <= 3)) if isinstance(capitals, list) else 0} decaying

--- COUNCIL ROLES ---
For each role, provide: Diagnosis, one recommendation, one concern, one question, one deletion candidate.

1. CHIEF OF STAFF
2. PRINCIPAL INVESTIGATOR
3. GRANT REVIEWER
4. INDUSTRY PARTNER
5. DEEP-TECH FOUNDER
6. VENTURE CAPITALIST
7. TEACHING MENTOR
8. PUBLIC INTELLECTUAL STRATEGIST
9. RISK OFFICER
10. PERSONAL SUSTAINABILITY COACH

--- FINAL SYNTHESIS ---
Highest-leverage move in 24 hours:
Highest-leverage move in 7 days:
Highest-leverage move in 30 days:
One strategic bet:
One thing to stop immediately:
=== END AI COUNCIL PROMPT ==="""

# --- Migration ---
def get_store_version(path):
    if not path.exists(): return None
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            return data.get("schema_version", "unknown")
    except: return "corrupt"
    return "unknown"

def migrate_v6_to_v7(data):
    """Migrate a v6 store to v7 format."""
    if not isinstance(data, dict): return data
    if "records" not in data:
        data = {"schema_version": CURRENT_SCHEMA_VERSION, "created_at": today_str(),
                "updated_at": today_str(), "records": data if isinstance(data, list) else []}
    data["schema_version"] = CURRENT_SCHEMA_VERSION
    if "updated_at" not in data: data["updated_at"] = today_str()
    if "created_at" not in data: data["created_at"] = today_str()
    return data

def migrate_store(path):
    """Migrate a single store from v6 to v7."""
    if not path.exists(): return "skipped (not found)"
    bak = path.with_suffix(path.suffix + ".v6.bak")
    if not bak.exists(): shutil.copyfile(path, bak)
    try:
        data = json.loads(path.read_text())
        migrated = migrate_v6_to_v7(data)
        path.write_text(json.dumps(migrated, indent=2))
        return "migrated"
    except json.JSONDecodeError: return "skipped (corrupt)"

def migrate_all_stores():
    """Migrate all stores to v7."""
    results = {}
    stores = [PROJECTS_PATH, OPPORTUNITIES_PATH, DECISIONS_PATH, EXPERIMENTS_PATH,
              RISKS_PATH, RELATIONSHIPS_PATH, PRINCIPLES_PATH, OUTCOMES_PATH,
              EVIDENCE_PATH, ASSUMPTIONS_PATH, PREDICTIONS_PATH, HYPOTHESES_PATH,
              ASSETS_PATH, DOCTRINE_PATH, IDENTITY_PATH, CAPITAL_PATH, RHYTHM_PATH, OKRS_PATH]
    for path in stores:
        results[path.name] = migrate_store(path)
    return {"results": results, "summary": f"Migrated {sum(1 for v in results.values() if v == 'migrated')} stores."}
