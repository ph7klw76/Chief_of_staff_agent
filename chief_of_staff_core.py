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

def _uid(): return uuid.uuid4().hex[:8]
def _today(): return date.today().isoformat()

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
        content = {"schema_version": SCHEMA_VERSION, "created_at": _today(), "updated_at": _today(), "records": data}
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
