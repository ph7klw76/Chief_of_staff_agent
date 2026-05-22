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
SCHEMA_VERSION_V8 = "8.0"
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

# V8 store paths
WORKFLOWS_PATH = Path("chief_of_staff_workflows.json")
EXECUTION_QUEUE_PATH = Path("chief_of_staff_execution_queue.json")
GRAPH_PATH = Path("chief_of_staff_graph.json")
CAPTURES_PATH = Path("chief_of_staff_captures.json")

# V9 store paths
METRICS_PATH = Path("chief_of_staff_metrics.json")
IMPACT_PATH = Path("chief_of_staff_impact.json")
WORKFLOW_RUNS_PATH = Path("chief_of_staff_workflow_runs.json")
ESTIMATES_PATH = Path("chief_of_staff_estimates.json")
INDICATORS_PATH = Path("chief_of_staff_indicators.json")
CONTRACTS_PATH = Path("chief_of_staff_contracts.json")
RUBRICS_PATH = Path("chief_of_staff_rubrics.json")
OUTPUT_SCORES_PATH = Path("chief_of_staff_output_scores.json")

# V10 store paths
COMMAND_QUEUE_PATH = Path("chief_of_staff_command_queue.json")
APPROVALS_PATH = Path("chief_of_staff_approvals.json")
POLICIES_PATH = Path("chief_of_staff_policies.json")
CAPACITY_PATH = Path("chief_of_staff_capacity.json")
INITIATIVES_PATH = Path("chief_of_staff_initiatives.json")
STRATEGIC_DEBT_PATH = Path("chief_of_staff_strategic_debt.json")
AUTONOMY_PATH = Path("chief_of_staff_autonomy.json")

# V8 constants
WORKFLOW_CATEGORIES = ["research_workflow","grant_workflow","industry_collaboration_workflow","teaching_workflow","public_influence_workflow","venture_workflow","admin_workflow","reflection_workflow"]
MEETING_TYPES = ["research_collaboration","industry_partner","grant_partner","student_supervision","teaching_meeting","venture_discussion","administrative_meeting"]
CAPTURE_TYPES = ["idea","insight","evidence","lesson","quote","experiment_result","meeting_note","paper_note","grant_note","teaching_note","venture_note"]
DRAFT_PROMPT_TYPES = ["grant","industry-email","linkedin","lecture","paper-review","venture"]
GRAPH_NODE_TYPES = ["task","project","opportunity","relationship","risk","decision","experiment","evidence","assumption","prediction","outcome","asset","workflow","okr","doctrine","capital"]
GRAPH_EDGE_TYPES = ["supports","depends_on","blocks","contradicts","informs","belongs_to","produces","risks","strengthens","weakens"]
ROLE_DASHBOARDS = ["researcher","pi","lecturer","collaborator","founder","public-intellectual"]

# V9 constants
METRIC_CATEGORIES = ["research_output","grant_progress","industry_collaboration","teaching_quality","public_influence","venture_progress","relationship_capital","execution_quality","energy_sustainability","financial_progress","strategic_capital"]
IMPACT_TYPES = ["paper_submitted","paper_accepted","grant_submitted","grant_awarded","collaboration_started","industry_meeting_secured","student_outcome_improved","lecture_asset_reused","linkedin_post_engaged","venture_hypothesis_validated","asset_reused","relationship_strengthened","risk_reduced","decision_improved"]
INDICATOR_TYPES = ["leading","lagging"]
ESTIMATE_TYPES = ["time","probability","effort","impact"]
ADHERENCE_CHECK_ITEMS = ["operating_rhythms","contracts","doctrine","okrs","sprint_plan","startup_shutdown","followup_discipline"]

# V10 constants
COMMAND_TYPES = ["schedule_block","prepare_email","prepare_meeting","follow_up","review_decision","update_project","mitigate_risk","kill_or_pause_project","capture_evidence","update_metric","run_workflow","generate_report","rebalance_portfolio"]
APPROVAL_REQUIRED_COMMANDS = ["prepare_email","prepare_meeting","follow_up","kill_or_pause_project"]
APPROVAL_STATUSES = ["pending","approved","rejected","executed","cancelled"]
DEBT_TYPES = ["admin_debt","relationship_debt","documentation_debt","technical_debt","teaching_asset_debt","grant_pipeline_debt","research_backlog_debt","decision_debt","risk_debt","energy_debt"]
AUTONOMY_LEVELS = {0: "Record only", 1: "Recommend", 2: "Prepare", 3: "Queue for approval", 4: "Execute local reversible", 5: "External action (disabled)"}
EXTERNAL_ACTION_TYPES = ["prepare_email","prepare_meeting","follow_up"]

DEFAULT_POLICIES = [
    {"policy_id":"p_admin_cap","title":"Admin maintenance cap","description":"If admin > 25% of time, recommend delegation.","scope":"admin_maintenance","condition":"admin_pct > 25","recommended_action":"Review admin tasks — delegate or batch.","severity":"high","active":True},
    {"policy_id":"p_grant_protect","title":"Grant funding protection","description":"If grant funding below baseline for 2 weeks, protect grant block.","scope":"grant_funding","condition":"grant_metrics_below_baseline","recommended_action":"Block 3 x 90-minute grant writing sessions this week.","severity":"high","active":True},
    {"policy_id":"p_relationship_followup","title":"Relationship follow-up","description":"If high-value relationship untouched 60+ days, recommend follow-up.","scope":"relationship","condition":"last_contact > 60_days","recommended_action":"Draft a warm follow-up message.","severity":"medium","active":True},
    {"policy_id":"p_project_stale","title":"Stale project review","description":"If project has no progress for 90 days and low ROI, recommend pause/kill.","scope":"project","condition":"no_progress > 90_days AND roi < 2","recommended_action":"Review this project for pause or kill.","severity":"medium","active":True},
    {"policy_id":"p_risk_mitigation","title":"Unmitigated high risk","description":"If risk severity >= 8 and no mitigation, recommend immediate action.","scope":"risk","condition":"severity >= 8 AND no_mitigation","recommended_action":"Assign mitigation owner and create action within 48 hours.","severity":"high","active":True},
    {"policy_id":"p_outcome_reforecast","title":"Outcome reforecast","description":"If outcome probability < 50%, recommend reforecast.","scope":"outcome","condition":"probability < 50","recommended_action":"Reforecast or adjust the target date.","severity":"medium","active":True},
    {"policy_id":"p_workflow_to_sop","title":"Workflow to SOP promotion","description":"If workflow used 3+ times with avg quality >= 7, recommend SOP.","scope":"workflow","condition":"runs >= 3 AND avg_quality >= 7","recommended_action":"Convert this workflow into a formal SOP.","severity":"low","active":True},
    {"policy_id":"p_asset_strengthen","title":"Asset strengthening","description":"If asset reused 5+ times, recommend strengthening.","scope":"asset","condition":"reuse_count >= 5","recommended_action":"Polish and publish this reusable asset.","severity":"low","active":True},
    {"policy_id":"p_estimation_correction","title":"Estimation correction","description":"If estimation error > 40%, recommend correction factor.","scope":"estimation","condition":"error_pct > 40","recommended_action":"Apply correction factor to future estimates.","severity":"medium","active":True},
    {"policy_id":"p_portfolio_reduce","title":"Portfolio reduction","description":"If too many active projects, recommend reduction.","scope":"portfolio","condition":"active_projects > capacity","recommended_action":"Archive or kill lowest-ROI projects.","severity":"high","active":True},
]

DEFAULT_CAPACITY = {"weekly_available_hours": 40, "weekly_deep_work_hours": 15, "weekly_admin_limit": 10,
                   "max_active_projects": 5, "max_high_focus_tasks_per_day": 3,
                   "preferred_deep_work_days": ["Monday","Wednesday","Friday"],
                   "energy_pattern": {"Monday": 8, "Tuesday": 7, "Wednesday": 8, "Thursday": 6, "Friday": 7, "Saturday": 4, "Sunday": 3},
                   "protected_blocks": "Mon/Wed/Fri 8am-12pm", "recovery_blocks": "Daily 12-1pm, 6pm onwards"}

DEFAULT_AUTONOMY = {"level": 2, "label": "Prepare", "max_external_actions": 0,
                    "require_approval_for": APPROVAL_REQUIRED_COMMANDS,
                    "allowed_local_actions": ["update_metric","capture_evidence","run_workflow","generate_report","update_project"]}

DEFAULT_INDICATORS = [
    {"indicator_id":"i_research_leading_1","strategic_goal":"research_publication","indicator_type":"leading","name":"Manuscript deep-work hours","description":"Weekly hours spent on manuscript writing","current_value":0,"target_value":6,"warning_threshold":3},
    {"indicator_id":"i_research_leading_2","strategic_goal":"research_publication","indicator_type":"leading","name":"Papers reviewed strategically","description":"Papers reviewed using review workflow","current_value":0,"target_value":4,"warning_threshold":1},
    {"indicator_id":"i_research_lagging_1","strategic_goal":"research_publication","indicator_type":"lagging","name":"Papers submitted","description":"Papers submitted to journals","current_value":0,"target_value":4,"warning_threshold":1},
    {"indicator_id":"i_grant_leading_1","strategic_goal":"grant_funding","indicator_type":"leading","name":"Concept notes drafted","description":"One-page concept notes completed","current_value":0,"target_value":4,"warning_threshold":1},
    {"indicator_id":"i_grant_leading_2","strategic_goal":"grant_funding","indicator_type":"leading","name":"Collaborators contacted","description":"Grant collaborators engaged","current_value":0,"target_value":6,"warning_threshold":2},
    {"indicator_id":"i_grant_lagging_1","strategic_goal":"grant_funding","indicator_type":"lagging","name":"Grants submitted","description":"Proposals submitted","current_value":0,"target_value":3,"warning_threshold":1},
    {"indicator_id":"i_industry_leading_1","strategic_goal":"industry_collaboration","indicator_type":"leading","name":"Outreach messages drafted","description":"Industry outreach messages prepared","current_value":0,"target_value":6,"warning_threshold":2},
    {"indicator_id":"i_industry_lagging_1","strategic_goal":"industry_collaboration","indicator_type":"lagging","name":"Collaborations formalized","description":"Signed or agreed collaborations","current_value":0,"target_value":2,"warning_threshold":0},
    {"indicator_id":"i_influence_leading_1","strategic_goal":"public_influence","indicator_type":"leading","name":"Research posts drafted","description":"LinkedIn/public posts prepared","current_value":0,"target_value":12,"warning_threshold":4},
    {"indicator_id":"i_influence_lagging_1","strategic_goal":"public_influence","indicator_type":"lagging","name":"Meaningful conversations generated","description":"Substantive responses or invitations","current_value":0,"target_value":6,"warning_threshold":2},
    {"indicator_id":"i_venture_leading_1","strategic_goal":"deeptech_venture","indicator_type":"leading","name":"Hypotheses tested","description":"Venture hypotheses validated or falsified","current_value":0,"target_value":3,"warning_threshold":1},
    {"indicator_id":"i_venture_lagging_1","strategic_goal":"deeptech_venture","indicator_type":"lagging","name":"Validated venture thesis","description":"Clear validated venture direction","current_value":0,"target_value":1,"warning_threshold":0},
]

DEFAULT_RUBRICS = {
    "grant_concept_note": {"name":"Grant Concept Note Rubric","output_type":"grant_concept_note","strategic_goal":"grant_funding","criteria":["Research question clarity","Novelty statement strength","Outcome measurability","Collaborator identification","Call requirement alignment"],"scoring_scale":"1-10 per criterion","definition_of_excellent":"Clear question, compelling novelty, measurable outcomes, named collaborators, follows call exactly.","definition_of_poor":"Vague question, no novelty, fuzzy outcomes, no collaborators, ignores call."},
    "industry_email": {"name":"Industry Email Rubric","output_type":"industry_email","strategic_goal":"industry_collaboration","criteria":["Subject line specificity","First sentence relevance","Value proposition clarity","Call to action strength","Professional tone"],"scoring_scale":"1-10 per criterion","definition_of_excellent":"Specific subject, references their work, clear mutual value, explicit next step, warm professional tone.","definition_of_poor":"Generic subject, no reference to recipient, unclear value, no ask, too long."},
    "research_paper_review": {"name":"Paper Review Rubric","output_type":"research_paper_review","strategic_goal":"research_publication","criteria":["Core claim identification","Connection to own research","Weakness identification","Follow-up idea","Citation capture"],"scoring_scale":"1-10 per criterion","definition_of_excellent":"Clear claim, strong connection to own work, identified weakness, actionable follow-up, citation saved.","definition_of_poor":"No clear claim, no connection to own work, no weakness noted, no follow-up."},
    "manuscript_section": {"name":"Manuscript Section Rubric","output_type":"manuscript_section","strategic_goal":"research_publication","criteria":["Outline adherence","Reference quality","Figure integration","Logical flow","Draft quality"],"scoring_scale":"1-10 per criterion","definition_of_excellent":"Follows outline exactly, key references cited, figures well-placed, clear flow, readable draft.","definition_of_poor":"Off-outline, missing references, no figures, disjointed, poor writing."},
    "lecture_plan": {"name":"Lecture Plan Rubric","output_type":"lecture_plan","strategic_goal":"teaching_excellence","criteria":["Learning objective clarity","Example relevance","Socratic question quality","Misconception anticipation","Quiz question quality"],"scoring_scale":"1-10 per criterion","definition_of_excellent":"Clear objectives, relevant examples, thought-provoking questions, correct misconceptions, diagnostic quiz.","definition_of_poor":"Fuzzy objectives, irrelevant examples, no questions, no misconception check."},
    "linkedin_research_post": {"name":"LinkedIn Post Rubric","output_type":"linkedin_research_post","strategic_goal":"public_influence","criteria":["Hook engagement","Plain language quality","Personal reflection","Call to action","Accuracy"],"scoring_scale":"1-10 per criterion","definition_of_excellent":"Engaging hook, clear plain language, personal story, strong call to action, accurate.","definition_of_poor":"Boring hook, jargon-heavy, no personal angle, no call to action."},
    "venture_hypothesis": {"name":"Venture Hypothesis Rubric","output_type":"venture_hypothesis","strategic_goal":"deeptech_venture","criteria":["Technical insight clarity","Customer pain identification","Market hypothesis quality","MVE design","Assumption identification"],"scoring_scale":"1-10 per criterion","definition_of_excellent":"Clear insight, specific pain, plausible market, testable MVE, key assumptions explicit.","definition_of_poor":"Vague insight, no pain identified, no market analysis, untestable, no assumptions."},
    "meeting_brief": {"name":"Meeting Brief Rubric","output_type":"meeting_brief","strategic_goal":"all","criteria":["Purpose clarity","Desired outcome specificity","Value proposition quality","Question preparation","Objection anticipation"],"scoring_scale":"1-10 per criterion","definition_of_excellent":"Clear purpose, specific outcome, strong value prop, prepared questions, anticipated objections.","definition_of_poor":"Fuzzy purpose, no outcome, generic value prop, no questions."},
    "strategy_memo": {"name":"Strategy Memo Rubric","output_type":"strategy_memo","strategic_goal":"all","criteria":["Thesis clarity","Data support","Recommendation specificity","Risk acknowledgment","Actionability"],"scoring_scale":"1-10 per criterion","definition_of_excellent":"Clear thesis, data-backed, specific recommendations, risks noted, immediately actionable.","definition_of_poor":"No clear thesis, no data, vague recommendations, no risk awareness."},
}

DEFAULT_WORKFLOWS = [
    {"workflow_id":"wf_grant_concept","name":"Write one-page grant concept note","category":"grant_workflow","strategic_goal":"grant_funding","description":"Write a focused one-page grant concept note.","trigger":"Grant deadline approaching or new funding call","required_inputs":["funding call details","research idea","preliminary data summary"],"steps":["1. Read the funding call carefully (15 min)","2. Define the core research question (10 min)","3. Draft the novelty statement (15 min)","4. Outline expected outcomes (10 min)","5. Identify key collaborators (5 min)","6. Write the one-page draft (30 min)","7. Review and refine (15 min)"],"expected_output":"One-page concept note ready for internal review","estimated_total_minutes":100,"status":"active"},
    {"workflow_id":"wf_collab_pitch","name":"Prepare industry collaboration pitch","category":"industry_collaboration_workflow","strategic_goal":"industry_collaboration","description":"Prepare a concise collaboration pitch for industry partners.","trigger":"Industry conference, partner meeting, or cold outreach","required_inputs":["partner background","your relevant expertise","mutual benefit hypothesis"],"steps":["1. Research partner's recent work (15 min)","2. Identify mutual value proposition (10 min)","3. Draft 3-slide pitch outline (15 min)","4. Prepare one specific collaboration idea (10 min)","5. Anticipate objections (10 min)","6. Draft follow-up email draft (10 min)"],"expected_output":"Pitch-ready collaboration outline","estimated_total_minutes":70,"status":"active"},
    {"workflow_id":"wf_manuscript","name":"Draft manuscript subsection","category":"research_workflow","strategic_goal":"research_publication","description":"Draft one subsection of a manuscript.","trigger":"Manuscript deadline or writing session","required_inputs":["outline","references","data/figures"],"steps":["1. Review the subsection outline (5 min)","2. Gather relevant references (10 min)","3. Write the first draft without editing (25 min)","4. Insert figures and captions (10 min)","5. Self-edit for clarity (15 min)","6. Mark for co-author review (5 min)"],"expected_output":"Draft subsection ready for review","estimated_total_minutes":70,"status":"active"},
    {"workflow_id":"wf_paper_review","name":"Review research paper strategically","category":"research_workflow","strategic_goal":"research_publication","description":"Strategic paper review focusing on relevance and connections.","trigger":"New paper to review or literature survey","required_inputs":["paper PDF","research questions","note template"],"steps":["1. Skim abstract, figures, conclusion (10 min)","2. Identify the core claim (5 min)","3. Note connection to your research (10 min)","4. Identify weaknesses or gaps (10 min)","5. Note one follow-up experiment idea (5 min)","6. Save citation and notes (5 min)"],"expected_output":"Strategic paper review notes","estimated_total_minutes":45,"status":"active"},
    {"workflow_id":"wf_lecture","name":"Prepare lecture using reusable assets","category":"teaching_workflow","strategic_goal":"teaching_excellence","description":"Prepare a lecture leveraging reusable templates and assets.","trigger":"Upcoming lecture","required_inputs":["syllabus","previous lecture notes","teaching assets"],"steps":["1. Review learning objectives (5 min)","2. Select reusable teaching module (5 min)","3. Adapt examples for this cohort (15 min)","4. Prepare 3 Socratic questions (10 min)","5. Anticipate common misconceptions (5 min)","6. Prepare diagnostic quiz question (5 min)","7. Test run key explanation (10 min)"],"expected_output":"Lecture-ready materials","estimated_total_minutes":55,"status":"active"},
    {"workflow_id":"wf_linkedin","name":"Convert research insight into LinkedIn post","category":"public_influence_workflow","strategic_goal":"public_influence","description":"Convert a research insight into a public-facing post.","trigger":"New result, paper, or insight to share","required_inputs":["research insight","target audience","key takeaway"],"steps":["1. Identify the one key insight (5 min)","2. Write a hook sentence (5 min)","3. Explain why it matters in plain language (10 min)","4. Add context or personal reflection (5 min)","5. Draft a call to action (3 min)","6. Review for clarity and accuracy (5 min)"],"expected_output":"LinkedIn post draft","estimated_total_minutes":33,"status":"active"},
    {"workflow_id":"wf_weekly_review","name":"Run weekly strategic review","category":"reflection_workflow","strategic_goal":"all","description":"Conduct a structured weekly strategic review.","trigger":"End of week (Friday)","required_inputs":["weekly activity log","project statuses","opportunity list"],"steps":["1. Review completed vs delayed tasks (10 min)","2. Check admin percentage (5 min)","3. Review stale opportunities (10 min)","4. Check relationship follow-ups (5 min)","5. Update project statuses (10 min)","6. Plan next week's top 3 outcomes (10 min)","7. Record one lesson or evidence (5 min)"],"expected_output":"Weekly review completed, sprint plan for next week","estimated_total_minutes":55,"status":"active"},
    {"workflow_id":"wf_opp_followup","name":"Conduct opportunity follow-up","category":"admin_workflow","strategic_goal":"all","description":"Follow up on open opportunities systematically.","trigger":"Weekly or when opportunities become stale","required_inputs":["open opportunities list","last contact dates"],"steps":["1. Sort opportunities by score and staleness (5 min)","2. Identify top 3 to follow up (5 min)","3. Draft follow-up message for each (15 min)","4. Schedule follow-up actions (5 min)","5. Update opportunity statuses (5 min)"],"expected_output":"3 follow-ups completed","estimated_total_minutes":35,"status":"active"},
    {"workflow_id":"wf_venture_hypothesis","name":"Build deep-tech venture hypothesis","category":"venture_workflow","strategic_goal":"deeptech_venture","description":"Formulate and refine a venture hypothesis.","trigger":"Research yields commercializable insight","required_inputs":["research insight","market context","competitor awareness"],"steps":["1. State the core technical insight (10 min)","2. Identify customer pain point (10 min)","3. Draft value proposition (10 min)","4. Estimate market size hypothesis (10 min)","5. Identify minimum viable experiment (10 min)","6. Note key assumptions to test (5 min)"],"expected_output":"Venture hypothesis one-pager","estimated_total_minutes":55,"status":"active"},
]

DEFAULT_SOP_TEMPLATES = {
    "grant_concept_note": {"title":"Grant Concept Note SOP","purpose":"Produce a compelling one-page grant concept note.","when_to_use":"When responding to a funding call or initiating a grant application.","inputs":"Funding call, research idea, preliminary data.","steps":"1. Read the call 2. Define research question 3. Draft novelty statement 4. Outline outcomes 5. Identify collaborators 6. Write draft 7. Review","quality_checklist":["Core question is clear","Novelty is explicit","Outcomes are measurable","Collaborators identified"],"common_mistakes":["Too broad","No clear novelty","Missing collaborators","Ignoring call requirements"],"definition_of_done":"Concept note is reviewed by a colleague and ready for submission.","estimated_minutes":100,"strategic_goal":"grant_funding"},
    "industry_outreach_email": {"title":"Industry Outreach Email SOP","purpose":"Send effective cold or warm outreach to industry partners.","when_to_use":"When initiating or following up with industry contacts.","inputs":"Contact details, value proposition, collaboration idea.","steps":"1. Research contact 2. Craft subject line 3. Write 3-sentence email 4. Include specific value 5. Propose next step 6. Review 7. Send","quality_checklist":["Subject line is specific","First sentence references their work","Value is clear","Call to action is specific"],"common_mistakes":["Too long","Generic","No clear ask","No follow-up mechanism"],"definition_of_done":"Email sent and follow-up scheduled.","estimated_minutes":30,"strategic_goal":"industry_collaboration"},
    "research_paper_review": {"title":"Paper Review SOP","purpose":"Review a research paper efficiently and strategically.","when_to_use":"For literature review, peer review, or staying current.","inputs":"Paper PDF, research interests, note template.","steps":"1. Skim abstract/figures/conclusion 2. Identify core claim 3. Note connection to your work 4. Identify gaps 5. Note follow-up idea 6. Save notes","quality_checklist":["Core claim identified","Connection to your work noted","Weakness documented","Follow-up idea recorded"],"common_mistakes":["Reading linearly","No connection to own work","No actionable follow-up"],"definition_of_done":"Notes saved with citation and one follow-up action.","estimated_minutes":45,"strategic_goal":"research_publication"},
    "manuscript_subsection": {"title":"Manuscript Subsection SOP","purpose":"Draft one subsection of a manuscript efficiently.","when_to_use":"When writing a paper, thesis, or proposal.","inputs":"Outline, references, data/figures.","steps":"1. Review outline 2. Gather references 3. Draft without editing 4. Insert figures 5. Self-edit 6. Mark for review","quality_checklist":["Follows outline","References cited","Figures labeled","Flow is logical"],"common_mistakes":["Editing while writing","No outline","Missing references","Perfectionism on first draft"],"definition_of_done":"Draft subsection written and ready for co-author review.","estimated_minutes":70,"strategic_goal":"research_publication"},
    "lecture_preparation": {"title":"Lecture Preparation SOP","purpose":"Prepare an effective lecture using reusable assets.","when_to_use":"Before each lecture or teaching session.","inputs":"Syllabus, previous notes, teaching assets.","steps":"1. Review objectives 2. Select module 3. Adapt examples 4. Prepare questions 5. Anticipate misconceptions 6. Prepare quiz 7. Test run","quality_checklist":["Objectives clear","Examples relevant","Questions prepared","Misconceptions addressed"],"common_mistakes":["Overloading content","No interactivity","Ignoring prior knowledge"],"definition_of_done":"Lecture materials complete with questions and examples.","estimated_minutes":55,"strategic_goal":"teaching_excellence"},
    "linkedin_research_post": {"title":"LinkedIn Research Post SOP","purpose":"Convert research into engaging public content.","when_to_use":"When you have a result, insight, or opinion to share.","inputs":"Research insight, audience, key takeaway.","steps":"1. Identify insight 2. Write hook 3. Explain plainly 4. Add reflection 5. Call to action 6. Review","quality_checklist":["Hook is engaging","Plain language used","Personal reflection included","Call to action present"],"common_mistakes":["Too technical","No hook","No personal angle","No call to action"],"definition_of_done":"Post drafted and reviewed for accuracy.","estimated_minutes":33,"strategic_goal":"public_influence"},
    "weekly_review": {"title":"Weekly Review SOP","purpose":"Conduct a structured weekly strategic review.","when_to_use":"End of each week.","inputs":"Activity log, project statuses, opportunity list.","steps":"1. Review tasks 2. Check admin 3. Review opportunities 4. Check relationships 5. Update projects 6. Plan next week 7. Record lesson","quality_checklist":["Completed tasks reviewed","Admin % checked","Stale ops followed up","Next week planned"],"common_mistakes":["Skipping review","No action from insights","Ignoring admin creep"],"definition_of_done":"Review completed with lessons recorded and next week planned.","estimated_minutes":55,"strategic_goal":"all"},
    "monthly_review": {"title":"Monthly Review SOP","purpose":"Strategic monthly review and rebalancing.","when_to_use":"Start of each month.","inputs":"Monthly data, project reports, OKR progress.","steps":"1. Review strategic allocation 2. Check OKR progress 3. Review predictions 4. Check assumptions 5. Update kill-list 6. Rebalance if needed","quality_checklist":["Allocation reviewed","OKRs updated","Stale items killed","Rebalance considered"],"common_mistakes":["Skipping months","Not killing anything","Ignoring prediction drift"],"definition_of_done":"Monthly review complete with updated priorities.","estimated_minutes":90,"strategic_goal":"all"},
    "opportunity_review": {"title":"Opportunity Review SOP","purpose":"Systematic review and follow-up of opportunities.","when_to_use":"Weekly or when opportunities pile up.","inputs":"Opportunity list, last contact dates.","steps":"1. Sort by score/staleness 2. Pick top 3 3. Draft follow-ups 4. Schedule actions 5. Update statuses","quality_checklist":["Top 3 followed up","Stale ops addressed","Statuses updated"],"common_mistakes":["Not following up","Letting ops decay","No prioritization"],"definition_of_done":"Top 3 opportunities followed up and statuses updated.","estimated_minutes":35,"strategic_goal":"all"},
}

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

# V8 dataclasses
@dataclass
class Workflow:
    workflow_id:str="";name:str="";category:str="research_workflow";strategic_goal:str="all"
    description:str="";trigger:str="";required_inputs:list=field(default_factory=list)
    steps:list=field(default_factory=list);expected_output:str=""
    estimated_total_minutes:int=60;linked_project_id:str="";linked_outcome_id:str=""
    status:str="active";created_at:str="";updated_at:str=""

@dataclass
class QueueItem:
    queue_id:str="";title:str="";source_type:str="task";source_id:str=""
    strategic_goal:str="";priority_score:int=5;estimated_minutes:int=30
    energy_required:int=5;focus_required:int=5;deadline:str=""
    status:str="queued";next_action:str="";created_at:str="";updated_at:str=""

@dataclass
class Capture:
    capture_id:str="";date:str="";type:str="idea";title:str="";content:str=""
    related_strategic_goal:str="";linked_project_id:str="";linked_opportunity_id:str=""
    linked_relationship_id:str="";tags:list=field(default_factory=list);next_action:str=""

@dataclass
class SprintPlan:
    theme:str="";top_outcomes:list=field(default_factory=list)
    deep_work_blocks:list=field(default_factory=list)
    relationship_actions:list=field(default_factory=list)
    admin_containment:list=field(default_factory=list)
    risks_to_mitigate:list=field(default_factory=list)
    assets_to_build:list=field(default_factory=list)
    kill_defer:list=field(default_factory=list)
    daily_suggestions:list=field(default_factory=list)

# V9 dataclasses
@dataclass
class Metric:
    metric_id:str="";name:str="";strategic_goal:str="";category:str="execution_quality"
    description:str="";unit:str="";target_value:float=0.0;current_value:float=0.0
    baseline_value:float=0.0;measurement_frequency:str="weekly";source:str=""
    linked_outcome_id:str="";linked_project_id:str="";linked_okr_id:str=""
    last_updated:str="";notes:str=""

@dataclass
class Impact:
    impact_id:str="";date:str="";title:str="";strategic_goal:str=""
    impact_type:str="";description:str="";evidence:str=""
    magnitude:int=5;confidence:int=5
    linked_task_id:str="";linked_project_id:str="";linked_opportunity_id:str=""
    linked_relationship_id:str="";linked_asset_id:str="";notes:str=""

@dataclass
class WorkflowRun:
    run_id:str="";workflow_id:str="";date:str=""
    estimated_minutes:int=60;actual_minutes:int=0;completed:bool=False
    output_created:str="";quality_score:int=5
    friction_points:list=field(default_factory=list);improvement_note:str=""

@dataclass
class Estimate:
    estimate_id:str="";date:str="";entity_type:str="";entity_id:str=""
    estimate_type:str="time";estimated_value:float=0.0;actual_value:float=0.0
    error_value:float=0.0;error_percent:float=0.0;lesson:str=""

@dataclass
class Indicator:
    indicator_id:str="";strategic_goal:str="";indicator_type:str="leading"
    name:str="";description:str="";current_value:float=0.0
    target_value:float=0.0;warning_threshold:float=0.0;linked_metric_id:str=""

@dataclass
class Contract:
    contract_id:str="";title:str="";strategic_goal:str=""
    commitment:str="";start_date:str="";end_date:str=""
    success_metric:str="";minimum_standard:str="";stretch_standard:str=""
    consequence_if_missed:str="";reward_if_completed:str=""
    status:str="active";review_date:str=""

@dataclass
class Rubric:
    rubric_id:str="";name:str="";output_type:str="";strategic_goal:str=""
    criteria:list=field(default_factory=list);scoring_scale:str="1-10"
    definition_of_excellent:str="";definition_of_poor:str=""

@dataclass
class OutputScore:
    score_id:str="";date:str="";output_title:str="";output_type:str=""
    rubric_id:str="";scores_by_criterion:dict=field(default_factory=dict)
    overall_score:float=0.0;improvement_note:str=""

# V10 dataclasses
@dataclass
class Command:
    command_id:str="";date_created:str="";title:str="";description:str=""
    command_type:str="";source_system:str="";strategic_goal:str=""
    priority_score:int=5;urgency_score:int=5;risk_score:int=1
    reversibility:str="two_way_door";requires_human_approval:bool=False
    approval_status:str="pending";recommended_action:str=""
    expected_benefit:str="";opportunity_cost:str=""
    linked_project_id:str="";linked_opportunity_id:str=""
    linked_relationship_id:str="";linked_risk_id:str=""
    linked_outcome_id:str="";created_by:str="system";notes:str=""

@dataclass
class Approval:
    approval_id:str="";command_id:str="";requested_at:str=""
    approved_at:str="";approver:str="";approval_status:str="pending"
    reason:str="";conditions:str="";expiration_date:str=""

@dataclass
class Policy:
    policy_id:str="";title:str="";description:str="";scope:str=""
    condition:str="";recommended_action:str="";severity:str="medium"
    active:bool=True;created_at:str="";updated_at:str=""

@dataclass
class Initiative:
    initiative_id:str="";name:str="";thesis:str="";strategic_goal:str=""
    start_date:str="";target_date:str="";status:str="active"
    linked_outcomes:list=field(default_factory=list);linked_projects:list=field(default_factory=list)
    linked_opportunities:list=field(default_factory=list);linked_relationships:list=field(default_factory=list)
    linked_metrics:list=field(default_factory=list);linked_risks:list=field(default_factory=list)
    linked_assets:list=field(default_factory=list)
    success_criteria:str="";current_phase:str="";governance_notes:str=""

@dataclass
class StrategicDebt:
    debt_id:str="";title:str="";debt_type:str="admin_debt";description:str=""
    severity:int=5;interest_rate:int=3;linked_project_id:str=""
    linked_initiative_id:str="";created_date:str=""
    next_reduction_action:str="";status:str="active"

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

# ======================================================================
# V8 — EXECUTION ORCHESTRATION
# ======================================================================

# --- Workflows ---
def load_workflows():
    data = load_records(WORKFLOWS_PATH)
    if not data:
        defaults = [Workflow(**w) for w in DEFAULT_WORKFLOWS]
        save_records(WORKFLOWS_PATH, [w.__dict__ for w in defaults])
        return defaults
    return [Workflow(**w) for w in data]

def save_workflows(ws): save_records(WORKFLOWS_PATH, [w.__dict__ for w in ws])

def run_workflow(wf_id):
    wfs = load_workflows()
    for w in wfs:
        if w.workflow_id == wf_id or w.name.lower().startswith(wf_id.lower()):
            return {"workflow": w, "steps": w.steps, "estimated_minutes": w.estimated_total_minutes, "inputs": w.required_inputs, "expected_output": w.expected_output}
    return None

def workflow_review():
    wfs = load_workflows()
    by_cat = defaultdict(list)
    for w in wfs: by_cat[w.category].append(w.name)
    return {"total": len(wfs), "by_category": dict(by_cat), "summary": f"{len(wfs)} workflows across {len(by_cat)} categories."}

# --- SOP Generator ---
def generate_sop(template_name=None):
    if template_name and template_name in DEFAULT_SOP_TEMPLATES:
        return {"template": template_name, "sop": DEFAULT_SOP_TEMPLATES[template_name]}
    return {"templates": list(DEFAULT_SOP_TEMPLATES.keys()), "sop": None}

def interactive_sop():
    print("\n  SOP GENERATOR"); print("-" * 50)
    title = input("  SOP title: ").strip()
    goal = input("  Strategic goal: ").strip()
    when_use = input("  When to use: ").strip()
    inputs = input("  Required inputs: ").strip()
    output = input("  Expected output: ").strip()
    steps = input("  Main steps (comma-separated): ").strip()
    failures = input("  Common failure modes: ").strip()
    checklist = input("  Quality checklist (comma-separated): ").strip()
    return {"title": title, "strategic_goal": goal, "when_to_use": when_use,
            "inputs": inputs, "expected_output": output, "steps": steps,
            "common_failures": failures, "quality_checklist": checklist,
            "exported": True}

# --- Project Playbook ---
def project_playbook(project, opps, risks, assets, relationships, decisions):
    pname = getattr(project, "name", str(project))
    pid = getattr(project, "project_id", "")
    pgoal = getattr(project, "strategic_goal", "research_publication")
    pstatus = getattr(project, "status", "active")
    linked_opps = [o for o in opps if getattr(o, "linked_project_id", "") == pid or getattr(o, "project_id", "") == pid]
    linked_risks = [r for r in risks if getattr(r, "project_id", "") == pid or getattr(r, "linked_project_id", "") == pid]
    linked_assets = [a for a in assets if getattr(a, "linked_project_id", "") == pid or getattr(a, "project_id", "") == pid]
    return {"project_name": pname, "project_id": pid, "status": pstatus,
            "strategic_goal": pgoal, "thesis": f"This project advances {pgoal} through targeted execution.",
            "success_criteria": getattr(project, "success_criteria", "Define clear success criteria."),
            "milestones": getattr(project, "milestones", "Break into 3-5 milestones."),
            "linked_opportunities": [getattr(o, "name", str(o)) for o in linked_opps[:3]],
            "linked_risks": [getattr(r, "title", str(r)) for r in linked_risks[:3]],
            "linked_assets": [getattr(a, "name", str(a)) for a in linked_assets[:3]],
            "weekly_rhythm": "Dedicate 2 focused blocks per week.",
            "first_5_actions": ["Define scope", "Identify key collaborator", "Draft milestone 1 plan",
                               "Create project asset template", "Schedule first review"],
            "kill_criteria": "No progress for 60 days OR strategic goal shifts away."}

# --- Execution Queue ---
def load_queue():
    data = load_records(EXECUTION_QUEUE_PATH)
    return [QueueItem(**q) for q in data] if data else []

def save_queue(qs): save_records(EXECUTION_QUEUE_PATH, [q.__dict__ for q in qs])

def add_to_queue(title, source_type, source_id, strategic_goal="", priority=5, minutes=30):
    qs = load_queue()
    q = QueueItem(queue_id=uid(), title=title, source_type=source_type, source_id=source_id,
                  strategic_goal=strategic_goal, priority_score=priority, estimated_minutes=minutes,
                  next_action=title, created_at=today_str(), updated_at=today_str())
    qs.append(q); save_queue(qs); return q

def queue_review():
    qs = load_queue()
    active = [q for q in qs if q.status in ("queued", "active")]
    blocked = [q for q in qs if q.status == "blocked"]
    completed = [q for q in qs if q.status == "completed"]
    quick_wins = [q for q in active if q.estimated_minutes <= 20 and q.energy_required <= 5]
    deep_work = [q for q in active if q.estimated_minutes >= 60 and q.focus_required >= 7]
    stale = [q for q in active if q.updated_at and q.updated_at < (date.today() - timedelta(days=14)).isoformat()]
    return {"active": len(active), "blocked": len(blocked), "completed_today": sum(1 for q in completed if q.updated_at >= today_str()),
            "top_3": sorted(active, key=lambda q: -q.priority_score)[:3],
            "blocked_items": blocked, "quick_wins": quick_wins, "deep_work": deep_work,
            "stale": stale, "summary": f"{len(active)} active, {len(blocked)} blocked."}

# --- Next-Action Compiler ---
def compile_next_actions(projects, opps, risks, relationships, decisions, experiments, okrs, outcomes, workflows):
    missing = []
    for p in projects:
        if not getattr(p, "next_action", ""):
            missing.append({"source": "project", "name": getattr(p, "name", str(p)), "issue": "No next action defined."})
    for o in opps:
        last = getattr(o, "last_touched_date", "")
        if last and last < (date.today() - timedelta(days=14)).isoformat():
            missing.append({"source": "opportunity", "name": getattr(o, "name", str(o)), "issue": f"Untouched since {last}."})
    for r in risks:
        if not getattr(r, "mitigation_owner", ""):
            missing.append({"source": "risk", "name": getattr(r, "title", str(r)), "issue": "No mitigation owner."})
    for r in relationships:
        last = getattr(r, "last_contact_date", "")
        if last and last < (date.today() - timedelta(days=30)).isoformat():
            missing.append({"source": "relationship", "name": getattr(r, "name", str(r)), "issue": f"No contact since {last}."})
    for d in decisions:
        if not getattr(d, "actual_outcome", "") and getattr(d, "review_date", ""):
            if getattr(d, "review_date", "") < today_str():
                missing.append({"source": "decision", "name": getattr(d, "title", str(d)), "issue": "Review date has passed."})
    for o in okrs:
        if getattr(o, "status", "active") == "active":
            krs = getattr(o, "key_results", [])
            if isinstance(krs, list):
                blocked_krs = [k for k in krs if (isinstance(k, dict) and k.get("status") == "blocked") or (hasattr(k, "status") and k.status == "blocked")]
                if blocked_krs:
                    missing.append({"source": "okr", "name": getattr(o, "title", str(o)), "issue": f"{len(blocked_krs)} blocked key result(s)."})
    return {"missing_actions": missing, "total_missing": len(missing),
            "summary": f"{len(missing)} stale or missing next action(s)." if missing else "All items have current next actions."}

# --- Knowledge Graph ---
def load_graph():
    data = load_json(GRAPH_PATH, {})
    return data.get("nodes", []), data.get("edges", [])

def save_graph(nodes, edges):
    save_json(GRAPH_PATH, {"nodes": nodes, "edges": edges, "schema_version": SCHEMA_VERSION_V8, "updated_at": today_str()}, is_records=False)

def build_graph():
    """Build graph from all stores."""
    nodes = []; edges = []
    for path, ntype in [(PROJECTS_PATH, "project"), (OPPORTUNITIES_PATH, "opportunity"),
                         (RISKS_PATH, "risk"), (DECISIONS_PATH, "decision"),
                         (EXPERIMENTS_PATH, "experiment"), (RELATIONSHIPS_PATH, "relationship"),
                         (OUTCOMES_PATH, "outcome"), (EVIDENCE_PATH, "evidence"),
                         (ASSUMPTIONS_PATH, "assumption"), (PREDICTIONS_PATH, "prediction"),
                         (HYPOTHESES_PATH, "hypothesis"), (ASSETS_PATH, "asset"),
                         (WORKFLOWS_PATH, "workflow"), (OKRS_PATH, "okr"),
                         (DOCTRINE_PATH, "doctrine"), (CAPITAL_PATH, "capital")]:
        if not path.exists(): continue
        try:
            data = json.loads(path.read_text())
            recs = data.get("records", data) if isinstance(data, dict) else data
            if isinstance(recs, list):
                for r in recs:
                    if isinstance(r, dict):
                        nid = r.get("project_id") or r.get("opportunity_id") or r.get("risk_id") or r.get("decision_id") or r.get("experiment_id") or r.get("relationship_id") or r.get("outcome_id") or r.get("evidence_id") or r.get("assumption_id") or r.get("prediction_id") or r.get("hypothesis_id") or r.get("asset_id") or r.get("workflow_id") or r.get("objective_id") or r.get("doctrine_id") or r.get("capital_id") or uid()
                        labels = [{"name": r.get("name") or r.get("title") or r.get("statement") or r.get("principle") or ntype}]
                        nodes.append({"id": nid, "type": ntype, "labels": labels})
        except: pass
    # Build edges from linked fields
    for n in nodes:
        ntype, nid = n["type"], n["id"]
        # Find the source record
        for path, stype in [(PROJECTS_PATH, "project"), (OPPORTUNITIES_PATH, "opportunity")]:
            if not path.exists(): continue
            try:
                data = json.loads(path.read_text())
                recs = data.get("records", data) if isinstance(data, dict) else data
                if isinstance(recs, list):
                    for r in recs:
                        if isinstance(r, dict) and (r.get("project_id") == nid or r.get("opportunity_id") == nid):
                            for link_field, edge_type in [("linked_project_id", "depends_on"), ("project_id", "belongs_to"), ("linked_opportunity_id", "informs"), ("linked_outcome_id", "produces")]:
                                if r.get(link_field) and r.get(link_field) != nid:
                                    edges.append({"source": nid, "target": r[link_field], "type": edge_type})
            except: pass
    save_graph(nodes, edges)
    return {"nodes": len(nodes), "edges": len(edges), "summary": f"Graph built: {len(nodes)} nodes, {len(edges)} edges."}

def graph_review():
    nodes, edges = load_graph()
    node_by_id = {n["id"]: n for n in nodes}
    if not nodes:
        build_graph_result = build_graph()
        nodes, edges = load_graph()
        node_by_id = {n["id"]: n for n in nodes}
    # Most depended-on
    dep_count = defaultdict(int)
    for e in edges:
        if e.get("type") == "depends_on": dep_count[e["target"]] += 1
    most_depended = sorted(dep_count.items(), key=lambda x: -x[1])[:3]
    # Most connected
    conn_count = defaultdict(int)
    for e in edges: conn_count[e["source"]] += 1; conn_count[e["target"]] += 1
    most_connected = sorted(conn_count.items(), key=lambda x: -x[1])[:3]
    # Disconnected
    connected_ids = {e["source"] for e in edges} | {e["target"] for e in edges}
    disconnected = [n for n in nodes if n["id"] not in connected_ids]
    return {"total_nodes": len(nodes), "total_edges": len(edges),
            "most_depended": [{"id": nid, "type": node_by_id.get(nid, {}).get("type", "?"), "deps": cnt} for nid, cnt in most_depended],
            "most_connected": [{"id": nid, "type": node_by_id.get(nid, {}).get("type", "?"), "connections": cnt} for nid, cnt in most_connected],
            "disconnected_count": len(disconnected),
            "disconnected": [{"id": n["id"], "type": n["type"], "name": n["labels"][0]["name"] if n.get("labels") else ""} for n in disconnected[:5]],
            "summary": f"{len(nodes)} nodes, {len(edges)} edges, {len(disconnected)} disconnected."}

def graph_entity(entity_id):
    nodes, edges = load_graph()
    if not nodes: build_graph(); nodes, edges = load_graph()
    node = next((n for n in nodes if n["id"] == entity_id), None)
    if not node: return None
    related_edges = [e for e in edges if e["source"] == entity_id or e["target"] == entity_id]
    related_ids = set()
    for e in related_edges: related_ids.add(e["source"]); related_ids.add(e["target"])
    related_ids.discard(entity_id)
    return {"entity": node, "edges": related_edges, "related_nodes": [n for n in nodes if n["id"] in related_ids]}

# --- Execution Packet ---
def execution_packet(item_id):
    """Generate a concise execution packet for any item."""
    # Search across multiple stores
    for path, ntype in [(PROJECTS_PATH, "project"), (OPPORTUNITIES_PATH, "opportunity")]:
        if not path.exists(): continue
        try:
            data = json.loads(path.read_text())
            recs = data.get("records", data) if isinstance(data, dict) else data
            if isinstance(recs, list):
                for r in recs:
                    if isinstance(r, dict) and (r.get("project_id") == item_id or r.get("opportunity_id") == item_id):
                        name = r.get("name") or r.get("title", "Unnamed")
                        goal = r.get("strategic_goal", "")
                        return {"title": name, "strategic_goal": goal, "why": f"Advances {goal or 'your strategy'}.",
                                "definition_of_done": r.get("success_criteria", "Complete as defined."),
                                "estimated_time": f"{r.get('estimated_minutes', 30)} minutes",
                                "energy_focus": "Medium energy, high focus recommended.",
                                "inputs": "Review any linked notes or assets.",
                                "first_10_minutes": "Open relevant documents and review the objective.",
                                "steps": r.get("steps", ["Start.", "Execute.", "Review."]),
                                "quality_checklist": ["Objective met?", "Output saved?", "Next action defined?"],
                                "risks": "Scope creep or interruption.",
                                "stop_condition": "If blocked for >15 minutes, escalate or defer.",
                                "next_followup": "Record completion or blocker."}
        except: pass
    # Check queue
    qs = load_queue()
    for q in qs:
        if q.queue_id == item_id:
            return {"title": q.title, "strategic_goal": q.strategic_goal, "why": "Queued for execution.",
                    "definition_of_done": q.next_action, "estimated_time": f"{q.estimated_minutes} minutes",
                    "energy_focus": f"Energy {q.energy_required}/10, Focus {q.focus_required}/10",
                    "inputs": "Check linked project/opportunity.", "first_10_minutes": "Review the task and gather materials.",
                    "steps": ["Execute.", "Review quality.", "Mark complete."], "quality_checklist": ["Done?"],
                    "risks": "Interruption.", "stop_condition": "If blocked, mark blocked.", "next_followup": "Update queue."}
    return None

# --- Draft Prompt Generator ---
def draft_prompt(prompt_type):
    prompts = {
        "grant": """=== AI GRANT PROMPT ===
(COPY INTO YOUR AI ASSISTANT)
Write a one-page grant concept note for my research. Include:
1. Research question
2. Novelty statement (why this is new)
3. Expected outcomes (measurable)
4. Risk mitigation approach
5. Key collaborators needed
Use clear, non-jargon language. Target: funding body reviewer.""",
        "industry-email": """=== AI INDUSTRY OUTREACH PROMPT ===
(COPY INTO YOUR AI ASSISTANT)
Draft 3 email templates for industry outreach based on my research:
1. Cold outreach email (3 sentences, specific value proposition)
2. Follow-up email (1 week after no response)
3. Collaboration pitch (1 paragraph, mutual benefit focus)
Keep it professional, concise, and specific to organic electronics research.""",
        "linkedin": """=== AI LINKEDIN POST PROMPT ===
(COPY INTO YOUR AI ASSISTANT)
Convert this research insight into a LinkedIn post:
- Hook: one surprising fact (first sentence)
- Why it matters (in plain language)
- Personal reflection (why I care about this)
- Call to action (question for readers)
Keep under 1300 characters. Professional but accessible tone.""",
        "lecture": """=== AI LECTURE PROMPT ===
(COPY INTO YOUR AI ASSISTANT)
Prepare teaching materials for a lecture. Create:
1. Beginner-friendly explanation of the core concept
2. Three Socratic questions to spark discussion
3. List of common misconceptions
4. One diagnostic quiz question with answer
Target: undergraduate or graduate students.""",
        "paper-review": """=== AI PAPER REVIEW PROMPT ===
(COPY INTO YOUR AI ASSISTANT)
Review this research paper strategically:
1. One-sentence summary
2. What is novel about this work
3. Biggest weakness or gap
4. How it connects to my research on organic electronics
5. One follow-up experiment idea
Be critical but fair. Focus on scientific merit.""",
        "venture": """=== AI VENTURE PROMPT ===
(COPY INTO YOUR AI ASSISTANT)
Develop a venture hypothesis for my research:
1. Core technical insight (one sentence)
2. Customer pain point addressed
3. Market hypothesis (size, segment, early adopters)
4. Minimum viable experiment to test this
5. Key assumptions that could kill this
Focus on deeptech: long R&D cycles, high barriers, defensible IP.""",
    }
    if prompt_type in prompts: return prompts[prompt_type]
    return f"Unknown draft type '{prompt_type}'. Available: {', '.join(DRAFT_PROMPT_TYPES)}"

# --- Meeting Preparation ---
def prepare_meeting(title, person, meeting_type, goal, desired_outcome, context=""):
    return {"title": title, "person": person, "type": meeting_type, "goal": goal,
            "desired_outcome": desired_outcome,
            "what_they_likely_care_about": "Their research priorities, funding alignment, and mutual benefit.",
            "value_proposition": "My unique expertise in organic electronics and collaborative track record.",
            "questions_to_ask": ["What are your current research priorities?", "What collaboration models work best for you?"],
            "points_to_communicate": ["My current research focus", "Specific collaboration idea", "Timeline and resources needed"],
            "possible_objections": ["Timeline mismatch", "IP concerns", "Funding uncertainty"],
            "proposed_next_step": "Schedule a follow-up within 2 weeks with a one-page concept note.",
            "followup_draft": f"Dear {person},\\n\\nThank you for the meeting on {title}. I will send the concept note by [date].\\n\\nBest regards"}

# --- Follow-up Engine ---
def followup_review(relationships=None, opps=None, projects=None, decisions=None):
    if relationships is None:
        relationships_loaded = load_records(RELATIONSHIPS_PATH) if RELATIONSHIPS_PATH.exists() else []
        relationships = [Relationship(**r) for r in relationships_loaded] if relationships_loaded else []
    if opps is None:
        opps_loaded = load_records(OPPORTUNITIES_PATH) if OPPORTUNITIES_PATH.exists() else []
        opps = [Opportunity(**o) for o in opps_loaded] if opps_loaded else []
    due = []
    for r in relationships:
        last = getattr(r, "last_contact_date", "")
        if last and last < (date.today() - timedelta(days=45)).isoformat():
            due.append({"source": "relationship", "name": getattr(r, "name", ""), "type": getattr(r, "relationship_type", ""),
                       "last_contact": last, "days_since": (date.today() - date.fromisoformat(last)).days if last else 999})
    for o in opps:
        last = getattr(o, "last_touched_date", "")
        score = opp_score(o)
        if last and last < (date.today() - timedelta(days=14)).isoformat() and score >= 1:
            due.append({"source": "opportunity", "name": getattr(o, "name", ""), "score": score,
                       "last_touched": last, "days_since": (date.today() - date.fromisoformat(last)).days if last else 999})
    due.sort(key=lambda x: -x.get("days_since", 0))
    return {"followups": due, "total": len(due),
            "summary": f"{len(due)} follow-up(s) due." if due else "All relationships and opportunities current."}

# --- Sprint Planner ---
def sprint_planner(okrs, projects, queue, opportunities, risks, config, relationships, energy_patterns=None):
    active_queue = [q for q in queue if q.status in ("queued", "active")]
    top_3 = sorted(active_queue, key=lambda q: -q.priority_score)[:3]
    top_risks = sorted(risks, key=lambda r: risk_score(r), reverse=True)[:2]
    stale_opps = [o for o in opportunities if getattr(o, "last_touched_date", "") and getattr(o, "last_touched_date", "") < (date.today() - timedelta(days=21)).isoformat()]
    return {"theme": "Execute strategic priorities, protect deep work, nurture relationships.",
            "top_outcomes": [q.title for q in top_3] if top_3 else ["Define 3 sprint outcomes"],
            "deep_work_blocks": ["Mon 8-10am: Research deep work", "Wed 8-10am: Grant writing", "Fri 8-10am: Strategic review"],
            "relationship_actions": ["Follow up with 2 collaborators", "Review open opportunities"],
            "admin_containment": ["Batch admin to 3-4pm daily", "Limit email to 2 check-ins per day"],
            "risks_to_mitigate": [getattr(r, "title", str(r)) for r in top_risks] if top_risks else ["Identify key risks"],
            "assets_to_build": ["Grant concept note template", "Paper review checklist"],
            "kill_defer": [f"Stale opportunity: {getattr(o, 'name', str(o))}" for o in stale_opps[:3]] if stale_opps else ["Review stale items"],
            "daily_suggestions": ["Mon: Deep work block", "Tue: Collaboration & meetings", "Wed: Deep work block",
                                  "Thu: Admin & follow-ups", "Fri: Review & plan next week"]}

# --- Startup/Shutdown ---
def startup_ritual(queue, projects, risks):
    active = [q for q in queue if q.status in ("queued", "active")]
    top = sorted(active, key=lambda q: -q.priority_score)[:1]
    top_risk = sorted(risks, key=lambda r: risk_score(r), reverse=True)[:1] if risks else []
    return {"top_objective": top[0].title if top else "No queued items — prioritize one task.",
            "first_packet": execution_packet(top[0].queue_id) if top else None,
            "risks_to_avoid": [getattr(r, "title", str(r)) for r in top_risk],
            "one_thing_not_to_do": "Don't start the day with email or admin. Protect the first 90 minutes.",
            "first_30_minutes": "1. Open execution packet. 2. Close email/chat. 3. Start the top task."}

def shutdown_ritual():  # interactive
    print("\n  SHUTDOWN REFLECTION"); print("-" * 50)
    completed = input("  What was completed today? ").strip()
    delayed = input("  What was delayed? ").strip()
    unexpected = input("  What appeared unexpectedly? ").strip()
    evidence = input("  What evidence was created? ").strip()
    queued = input("  What should be queued for tomorrow? ").strip()
    lesson = input("  What lesson should update doctrine, assumptions, or workflows? ").strip()
    return {"date": today_str(), "completed": completed, "delayed": delayed, "unexpected": unexpected,
            "evidence_created": evidence, "queued_for_tomorrow": queued, "lesson": lesson}

# --- Asset Creation Recommender ---
def asset_opportunities(records, projects, assets, workflows):
    """Identify repeated work that could become reusable assets."""
    recommendations = []
    # Check for repeated grant writing
    grant_workflows = [w for w in workflows if w.category == "grant_workflow"]
    if len(grant_workflows) >= 1:
        grant_assets = [a for a in assets if a.asset_type == "proposal_template"]
        if not grant_assets:
            recommendations.append("You repeatedly write grant proposals. Create a reusable proposal objective bank.")
    # Check for repeated teaching
    teaching_wfs = [w for w in workflows if w.category == "teaching_workflow"]
    if len(teaching_wfs) >= 1:
        teach_assets = [a for a in assets if a.asset_type == "lecture_material"]
        if not teach_assets:
            recommendations.append("You prepare lectures regularly. Create a reusable teaching module library.")
    # Check for paper review
    review_wfs = [w for w in workflows if "review" in w.name.lower()]
    if len(review_wfs) >= 1:
        review_assets = [a for a in assets if "review" in a.name.lower()]
        if not review_assets:
            recommendations.append("You review papers regularly. Create a structured paper-review template asset.")
    # Check for industry outreach
    ind_wfs = [w for w in workflows if w.category == "industry_collaboration_workflow"]
    if len(ind_wfs) >= 1:
        ind_assets = [a for a in assets if a.asset_type == "collaboration_pitch"]
        if not ind_assets:
            recommendations.append("You contact industry partners. Create a collaboration pitch template asset.")
    return {"recommendations": recommendations, "total": len(recommendations),
            "summary": f"{len(recommendations)} asset creation opportunity(s)." if recommendations else "No obvious asset opportunities."}

# --- Knowledge Capture ---
def load_captures():
    data = load_records(CAPTURES_PATH)
    return [Capture(**c) for c in data] if data else []

def save_captures(cs): save_records(CAPTURES_PATH, [c.__dict__ for c in cs])

def add_capture_interactive_core(capture_type, title, content, goal="", project_id="", tags=""):
    cs = load_captures()
    c = Capture(capture_id=uid(), date=today_str(), type=capture_type, title=title,
                content=content, related_strategic_goal=goal,
                linked_project_id=project_id, tags=[t.strip() for t in tags.split(",") if t.strip()])
    cs.append(c); save_captures(cs); return c

# --- Context Prompt Builder ---
def context_prompt(query, redact=False):
    """Search and assemble a compact context block for AI use."""
    results = local_search(query)
    context = f"=== CONTEXT FROM YOUR STRATEGIC SYSTEM ===\nQuery: {query}\n\n"
    prev_store = None
    for res in results.get("results", [])[:15]:
        if res["store"] != prev_store:
            context += f"\n--- {res['store']} ---\n"
            prev_store = res["store"]
        text = res["match"]
        if redact: text = _redact_sensitive(text)
        context += f"- {text}\n"
    context += f"\n---\nTask: Use the context above to help me with: {query}\n=== END CONTEXT ==="
    return context

def _redact_sensitive(text):
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL-REDACTED]', text)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE-REDACTED]', text)
    text = re.sub(r'\b\d{2,5}\s*\d{5,8}\s*\d{5,8}\s*\d{2,5}\b', '[ACCOUNT-REDACTED]', text)
    return text

# --- Role Dashboards ---
def role_dashboard(role):
    data = gather_all_data()
    role_configs = {
        "researcher": {"goals": ["research_publication"], "sections": ["projects", "experiments", "evidence", "assets", "workflows"]},
        "pi": {"goals": ["grant_funding", "research_publication"], "sections": ["projects", "opportunities", "risks", "relationships", "outcomes"]},
        "lecturer": {"goals": ["teaching_excellence"], "sections": ["projects", "assets", "workflows", "experiments"]},
        "collaborator": {"goals": ["industry_collaboration"], "sections": ["relationships", "opportunities", "projects", "followups"]},
        "founder": {"goals": ["deeptech_venture"], "sections": ["opportunities", "experiments", "risks", "assets", "predictions"]},
        "public-intellectual": {"goals": ["public_influence"], "sections": ["projects", "assets", "evidence", "opportunities"]},
    }
    cfg = role_configs.get(role, role_configs["researcher"])
    result = {"role": role, "strategic_goals": cfg["goals"]}
    for section in cfg["sections"]:
        items = data.get(section, [])
        if section == "followups":
            result[section] = [getattr(i, "name", str(i)) for i in items[:3]] if items else ["No pending follow-ups"]
        else:
            names = []
            for i in items[:5]:
                if isinstance(i, dict): names.append(i.get("name") or i.get("title", ""))
                elif hasattr(i, "name"): names.append(i.name)
                elif hasattr(i, "title"): names.append(i.title)
                else: names.append(str(i))
            result[section] = names if names else ["(none)"]
    return result

# --- One-Page Mode ---
def one_page():
    data = gather_all_data()
    tasks = data.get("tasks", [])
    projs = data.get("projects", [])
    opps = data.get("opportunities", [])
    risks = data.get("risks", [])
    rels = data.get("relationships", [])
    queue = load_queue()
    active = [q for q in queue if q.status in ("queued", "active")]
    top_q = sorted(active, key=lambda q: -q.priority_score)[:1]
    top_risk = sorted(risks, key=lambda r: risk_score(r), reverse=True)[:1] if risks else []
    top_opp = sorted(opps, key=lambda o: opp_score(o), reverse=True)[:1] if opps else []
    top_rel = sorted(rels, key=lambda r: r.relationship_strength, reverse=True)[:1] if rels else []
    stale_opps = [o for o in opps if getattr(o, "last_touched_date", "") and getattr(o, "last_touched_date", "") < (date.today() - timedelta(days=14)).isoformat()]
    return {"today": top_q[0].title if top_q else "Prioritize one strategic task.",
            "this_week": "Protect deep work. Follow up on opportunities. Limit admin to 25%.",
            "this_month": "Review strategic allocation. Update OKRs. Kill stale projects.",
            "top_project": getattr(projs[0], "name", "(none)") if projs else "(none)",
            "top_opportunity": getattr(top_opp[0], "name", "(none)") if top_opp else "(none)",
            "top_risk": getattr(top_risk[0], "title", "(none)") if top_risk else "(none)",
            "top_relationship": getattr(top_rel[0], "name", "(none)") if top_rel else "(none)",
            "one_thing_to_delete": f"Stale opportunity: {getattr(stale_opps[0], 'name', '(none)')}" if stale_opps else "Nothing obvious.",
            "one_thing_to_protect": "Your first deep-work block each day.",
            "next_best_move": "Start the top queued task with the execution packet."}

# --- Redaction helpers ---
import re

# --- gather_all_data extension for V8 ---
def _ext_gather_all_data(data):
    """Extend gather_all_data with V8 stores."""
    for path, name in [(WORKFLOWS_PATH, "workflows"), (EXECUTION_QUEUE_PATH, "queue"),
                        (CAPTURES_PATH, "captures")]:
        try:
            if path.exists():
                raw = json.loads(path.read_text())
                data[name] = raw.get("records", raw) if isinstance(raw, dict) else raw
        except: data[name] = []
    data["relationships"] = load_records(RELATIONSHIPS_PATH) if RELATIONSHIPS_PATH.exists() else []
    data["decisions"] = load_records(DECISIONS_PATH) if DECISIONS_PATH.exists() else []
    data["experiments"] = load_records(EXPERIMENTS_PATH) if EXPERIMENTS_PATH.exists() else []
    return data

# ======================================================================
# V9 — STRATEGIC PERFORMANCE MEASUREMENT
# ======================================================================
import statistics

# --- Metrics Registry ---
def load_metrics():
    data = load_records(METRICS_PATH)
    return [Metric(**m) for m in data] if data else []

def save_metrics(ms): save_records(METRICS_PATH, [m.__dict__ for m in ms])

def metrics_review():
    ms = load_metrics()
    if not ms: return {"total": 0, "message": "No metrics registered. Use --add-metric."}
    on_target = [m for m in ms if m.current_value >= m.target_value]
    below_target = [m for m in ms if m.current_value < (m.target_value * 0.5)]
    return {"total": len(ms), "on_target": len(on_target), "below_target": len(below_target),
            "latest": [{"name": m.name, "current": m.current_value, "target": m.target_value,
                        "unit": m.unit, "goal": m.strategic_goal} for m in ms[:10]],
            "summary": f"{len(on_target)} on target, {len(below_target)} below 50% of target."}

# --- Impact Ledger ---
def load_impacts():
    data = load_records(IMPACT_PATH)
    return [Impact(**i) for i in data] if data else []

def save_impacts(imps): save_records(IMPACT_PATH, [i.__dict__ for i in imps])

def impact_review():
    imps = load_impacts()
    if not imps: return {"total": 0, "message": "No impact recorded. Use --add-impact."}
    by_type = defaultdict(int)
    total_magnitude = 0
    for imp in imps:
        by_type[imp.impact_type] += 1
        total_magnitude += imp.magnitude
    return {"total": len(imps), "by_type": dict(by_type),
            "avg_magnitude": round(total_magnitude / len(imps), 1),
            "top_3": [{"title": i.title, "type": i.impact_type, "magnitude": i.magnitude}
                      for i in sorted(imps, key=lambda x: -x.magnitude)[:3]],
            "summary": f"{len(imps)} impacts, avg magnitude {total_magnitude / len(imps):.1f}/10."}

# --- Strategic ROI Engine ---
def roi_review(projects, workflows, relationships, opportunities, assets, metrics):
    """Strategic ROI: return - cost for each strategic investment."""
    def calc_roi(item, item_type):
        impact = getattr(item, "magnitude", getattr(item, "priority_score", 5))
        compound = getattr(item, "estimated_future_value", getattr(item, "current_score", 5))
        rel_value = getattr(item, "relationship_value", getattr(item, "relationship_strength", 5))
        evidence = getattr(item, "confidence", getattr(item, "evidence_strength", 5))
        future_opt = getattr(item, "potential_value", getattr(item, "opportunity_capture", 5))
        ret = (impact * 0.30 + compound * 0.25 + rel_value * 0.15 + evidence * 0.15 + future_opt * 0.15)
        time_c = getattr(item, "estimated_minutes", getattr(item, "estimated_total_minutes", 60)) / 60
        energy_c = getattr(item, "energy_required", getattr(item, "focus_required", 5))
        opp_c = getattr(item, "opportunity_cost", 3)
        complexity = getattr(item, "risk", getattr(item, "risk_exposure", 5))
        cost = (time_c * 0.35 + energy_c * 0.25 + opp_c * 0.25 + complexity * 0.15)
        return round(ret - cost, 2), ret, cost
    items = []
    for p in projects[:10]: r, s, c = calc_roi(p, "project"); items.append({"name": getattr(p, "name", str(p)), "type": "project", "roi": r, "return": round(s, 2), "cost": round(c, 2)})
    for w in workflows[:10]: r, s, c = calc_roi(w, "workflow"); items.append({"name": w.name, "type": "workflow", "roi": r, "return": round(s, 2), "cost": round(c, 2)})
    for o in opportunities[:10]: r, s, c = calc_roi(o, "opportunity"); items.append({"name": getattr(o, "name", str(o)), "type": "opportunity", "roi": r, "return": round(s, 2), "cost": round(c, 2)})
    items.sort(key=lambda x: -x["roi"])
    high = items[:5]; low = items[-5:] if len(items) >= 5 else []
    return {"high_roi": high, "low_roi": low, "total_analyzed": len(items),
            "summary": f"Highest ROI: {high[0]['name'] if high else 'N/A'}. Lowest: {low[0]['name'] if low else 'N/A'}."}

# --- Workflow Performance ---
def load_workflow_runs():
    data = load_records(WORKFLOW_RUNS_PATH)
    return [WorkflowRun(**w) for w in data] if data else []

def save_workflow_runs(wrs): save_records(WORKFLOW_RUNS_PATH, [w.__dict__ for w in wrs])

def log_workflow_run(wf_id, estimated, actual, completed, output, quality):
    wrs = load_workflow_runs()
    wr = WorkflowRun(run_id=uid(), workflow_id=wf_id, date=today_str(),
                     estimated_minutes=estimated, actual_minutes=actual,
                     completed=completed, output_created=output, quality_score=quality)
    wrs.append(wr); save_workflow_runs(wrs); return wr

def workflow_performance():
    wrs = load_workflow_runs()
    wfs = {w.workflow_id: w for w in load_workflows()}
    if not wrs: return {"total_runs": 0, "message": "No workflow runs logged."}
    by_wf = defaultdict(list)
    for wr in wrs: by_wf[wr.workflow_id].append(wr)
    results = []
    for wf_id, runs in by_wf.items():
        completed = [r for r in runs if r.completed]
        rates = []
        for r in runs:
            if r.actual_minutes > 0: rates.append(r.estimated_minutes / max(r.actual_minutes, 1))
        avg_est_error = round((1 - (sum(rates) / len(rates))) * 100, 1) if rates else 0
        results.append({"workflow": wfs.get(wf_id, Workflow(name=wf_id)).name,
                        "runs": len(runs), "completion_rate": round(len(completed) / len(runs) * 100, 0),
                        "avg_quality": round(sum(r.quality_score for r in runs) / len(runs), 1),
                        "estimation_error_pct": avg_est_error})
    return {"total_runs": len(wrs), "workflows": results,
            "summary": f"{len(wrs)} runs across {len(by_wf)} workflows."}

# --- Estimation Accuracy ---
def load_estimates():
    data = load_records(ESTIMATES_PATH)
    return [Estimate(**e) for e in data] if data else []

def save_estimates(es): save_records(ESTIMATES_PATH, [e.__dict__ for e in es])

def estimate_review():
    es = load_estimates()
    if not es: return {"total": 0, "message": "No estimates recorded."}
    time_ests = [e for e in es if e.estimate_type == "time"]
    prob_ests = [e for e in es if e.estimate_type == "probability"]
    time_errors = [e.error_percent for e in time_ests if e.error_percent != 0]
    prob_errors = [(e.estimated_value - e.actual_value) / max(abs(e.actual_value), 0.01) for e in prob_ests]
    by_entity = defaultdict(list)
    for e in es: by_entity[e.entity_type].append(e.error_percent)
    entity_errors = {k: round(statistics.mean(v), 1) for k, v in by_entity.items() if v}
    correction = None
    if time_errors:
        avg = statistics.mean(time_errors)
        if avg > 10: correction = f"Time underestimation: {avg:.0f}%. Multiply future time estimates by {1 + avg / 100:.2f}."
        elif avg < -10: correction = f"Time overestimation: {avg:.0f}%."
    return {"total": len(es), "avg_time_error_pct": round(statistics.mean(time_errors), 1) if time_errors else 0,
            "avg_prob_error": round(statistics.mean(prob_errors), 2) if prob_errors else 0,
            "by_entity_type": entity_errors, "correction": correction,
            "summary": correction or "Insufficient data for estimation patterns."}

# --- Reforecasting ---
def reforecast(okrs, metrics, predictions, estimates, queue):
    items = []
    for o in okrs:
        if o.status != "active": continue
        krs = o.key_results if isinstance(o.key_results, list) else []
        avg_progress = sum(kr.progress_percent if isinstance(kr, KeyResult) else kr.get("progress_percent", 0)
                          for kr in krs) / max(len(krs), 1)
        original_conf = o.confidence
        blocked = sum(1 for kr in krs if (isinstance(kr, dict) and kr.get("status") == "blocked")
                     or (isinstance(kr, KeyResult) and kr.status == "blocked"))
        adjusted_conf = max(1, original_conf - blocked * 2 - (10 - int(avg_progress / 10)) * 2)
        if adjusted_conf < original_conf:
            items.append({"entity": "okr", "name": o.title,
                         "original_confidence": original_conf, "adjusted_confidence": adjusted_conf,
                         "reason": f"Blocked KRs: {blocked}, avg progress: {avg_progress:.0f}%",
                         "recommendation": "Protect deep-work blocks or adjust target date."})
    for p in predictions:
        if getattr(p, "resolved", True): continue
        delay = p.get("actual_delay", 0) if isinstance(p, dict) else getattr(p, "actual_delay", 0)
        if delay > 0:
            items.append({"entity": "prediction", "name": p.get("prediction_statement", str(p)),
                         "original_confidence": 7, "adjusted_confidence": max(2, 7 - delay),
                         "reason": f"Delayed by {delay} periods.",
                         "recommendation": "Update prediction or accept revised outcome."})
    return {"forecasts": items, "total": len(items),
            "summary": f"{len(items)} item(s) need reforecasting." if items else "All items on track."}

# --- Velocity ---
def velocity_review(records, queue, impact, workflow_runs, estimates):
    if not records: return {"message": "No history data for velocity analysis."}
    weeks = max(1, len(records) // 7)
    total_minutes = sum(r.get("total_minutes", 0) for r in records if isinstance(r, dict))
    completed = sum(1 for q in queue if q.status == "completed")
    deep_work_blocks = sum(1 for wr in workflow_runs if wr.actual_minutes >= 60 and wr.completed)
    impacts_per_month = len(impact) / max(1, weeks / 4)
    assets_created = sum(1 for i in impact if i.impact_type == "asset_reused")
    return {"weekly_strategic_minutes": round(total_minutes / max(1, weeks), 0),
            "completed_queue_items": completed,
            "completed_deep_work_blocks": deep_work_blocks,
            "impacts_per_month": round(impacts_per_month, 1),
            "assets_created_or_reused": assets_created,
            "summary": f"Strategic velocity: {round(total_minutes / max(1, weeks), 0)} min/week."}

# --- Indicators ---
def load_indicators():
    data = load_records(INDICATORS_PATH)
    if not data:
        defaults = [Indicator(**i) for i in DEFAULT_INDICATORS]
        save_indicators(defaults)
        return defaults
    return [Indicator(**i) for i in data]

def save_indicators(inds): save_records(INDICATORS_PATH, [i.__dict__ for i in inds])

def indicator_review():
    inds = load_indicators()
    leaders = [i for i in inds if i.indicator_type == "leading"]
    laggers = [i for i in inds if i.indicator_type == "lagging"]
    warnings = [i for i in inds if i.current_value <= i.warning_threshold and i.target_value > 0]
    return {"total": len(inds), "leading": len(leaders), "lagging": len(laggers),
            "warnings": [{"name": i.name, "current": i.current_value, "warning": i.warning_threshold,
                          "target": i.target_value, "goal": i.strategic_goal} for i in warnings],
            "by_goal": {g: len([i for i in inds if i.strategic_goal == g]) for g in STRATEGIC_GOALS},
            "summary": f"{len(warnings)} indicator(s) below warning threshold." if warnings else "All indicators healthy."}

# --- Review Board ---
def review_board(data):
    ms = metrics_review(); ir = impact_review(); roi = roi_review(data.get("projects", []),
        data.get("workflows", []), data.get("relationships", []),
        data.get("opportunities", []), data.get("assets", []), data.get("metrics", []))
    vel = velocity_review(data.get("records", []), data.get("queue", []),
                          data.get("impact", []), data.get("workflow_runs", []), data.get("estimates", []))
    inds = indicator_review(); rf_result = reforecast(data.get("okrs", []), data.get("metrics", []),
        data.get("predictions", []), data.get("estimates", []), data.get("queue", []))
    risks = data.get("risks", [])
    return {"strategic_thesis": "Advance research, secure funding, build collaborations.",
            "metrics": ms, "impact": ir, "roi": roi, "velocity": vel,
            "indicators": inds, "reforecast": rf_result,
            "top_risks": [getattr(r, "title", str(r)) for r in risks[:3]] if risks else [],
            "recommended_decisions": ["Increase grant-writing blocks" if ms.get("below_target", 0) > 0 else "Maintain current allocation.",
                                      "Follow up stale relationships" if len(data.get("relationships", [])) > 0 else ""]}

# --- Contracts ---
def load_contracts():
    data = load_records(CONTRACTS_PATH)
    return [Contract(**c) for c in data] if data else []

def save_contracts(cs): save_records(CONTRACTS_PATH, [c.__dict__ for c in cs])

def contract_review():
    cs = load_contracts()
    if not cs: return {"total": 0, "message": "No contracts. Use --add-contract."}
    active = [c for c in cs if c.status == "active"]
    past_due = [c for c in active if c.review_date and c.review_date < today_str()]
    return {"total": len(cs), "active": len(active), "past_due_review": len(past_due),
            "latest": [{"title": c.title, "commitment": c.commitment[:60], "status": c.status} for c in cs[:5]],
            "summary": f"{len(active)} active contracts, {len(past_due)} past review date."}

# --- Adherence ---
def adherence_review(rhythms, contracts, doctrine, okrs, records):
    score = 0; max_score = 100; details = {}
    # Rhythms (30 pts)
    rr = rhythm_review(rhythms)
    rhythm_pct = (rr["active"] - len(rr["overdue"])) / max(rr["active"], 1) * 30
    score += rhythm_pct; details["rhythms"] = round(rhythm_pct, 1)
    # Contracts (25 pts)
    cs = contract_review()
    contract_pct = ((cs.get("active", 0) - cs.get("past_due_review", 0)) / max(cs.get("active", 0), 1)) * 25 if cs.get("active", 0) > 0 else 25
    score += contract_pct; details["contracts"] = round(contract_pct, 1)
    # Doctrine (15 pts)
    doctrine_score = 15 if doctrine else 5; score += doctrine_score; details["doctrine"] = doctrine_score
    # OKRs (15 pts)
    if okrs:
        active_okrs = [o for o in okrs if o.status == "active"]
        if active_okrs:
            krs_list = []
            for o in active_okrs:
                krs = o.key_results if isinstance(o.key_results, list) else []
                krs_list.extend(krs)
            okr_pct = sum(kr.progress_percent if isinstance(kr, KeyResult) else kr.get("progress_percent", 0)
                         for kr in krs_list) / max(len(krs_list), 1)
            okr_score = okr_pct / 100 * 15
        else: okr_score = 15
    else: okr_score = 5
    score += okr_score; details["okrs"] = round(okr_score, 1)
    # Sprint/records (15 pts)
    sprint_score = 15 if records and len(records) >= 1 else 5; score += sprint_score; details["sprint"] = sprint_score
    return {"adherence_score": round(score, 1), "details": details,
            "strengths": [k for k, v in details.items() if v >= 20],
            "weaknesses": [k for k, v in details.items() if v < 10],
            "summary": f"Adherence: {round(score, 1)}/100."}

# --- Rubrics & Output Scoring ---
def load_rubrics():
    data = load_records(RUBRICS_PATH)
    if not data:
        rubrics = [Rubric(rubric_id=k, **v) for k, v in DEFAULT_RUBRICS.items()]
        save_records(RUBRICS_PATH, [r.__dict__ for r in rubrics])
        return rubrics
    return [Rubric(**r) for r in data]

def load_output_scores():
    data = load_records(OUTPUT_SCORES_PATH)
    return [OutputScore(**o) for o in data] if data else []

def save_output_scores(oss): save_records(OUTPUT_SCORES_PATH, [o.__dict__ for o in oss])

def score_output(output_title, output_type, rubric_id=None, scores=None):
    """Score an output using a rubric."""
    rubrics = load_rubrics()
    rubric = next((r for r in rubrics if r.rubric_id == rubric_id or r.output_type == output_type), None)
    if not rubric and rubrics: rubric = rubrics[0]
    oss = load_output_scores()
    os_obj = OutputScore(score_id=uid(), date=today_str(), output_title=output_title,
                         output_type=output_type, rubric_id=rubric.rubric_id if rubric else "")
    if scores and rubric:
        n = len(rubric.criteria)
        for i, (criterion, score_val) in enumerate(zip(rubric.criteria[:len(scores)], scores)):
            os_obj.scores_by_criterion[criterion] = score_val
        os_obj.overall_score = round(sum(scores) / len(scores), 1) if scores else 0
    return os_obj

# --- Attribution ---
def attribution_review(impacts, projects, workflows, relationships, assets):
    if not impacts: return {"total": 0, "message": "No impacts for attribution analysis."}
    results = []
    for imp in impacts[:5]:
        attributions = []
        if imp.linked_project_id: attributions.append("project")
        if imp.linked_relationship_id: attributions.append("relationship")
        if imp.linked_asset_id: attributions.append("asset")
        if not attributions: attributions = ["direct execution"]
        results.append({"impact": imp.title, "type": imp.impact_type,
                       "magnitude": imp.magnitude, "attributions": attributions,
                       "recommendation": "Reuse linked asset and turn into formal workflow." if "asset" in attributions else "Log more linked entities for better attribution."})
    return {"results": results, "summary": f"{len(results)} impact(s) analyzed."}

# --- Flywheel Detector ---
def flywheel_review(impacts, projects, relationships, assets, evidence):
    flywheels = []
    research_impacts = [i for i in impacts if i.strategic_goal == "research_publication"]
    influence_impacts = [i for i in impacts if i.strategic_goal == "public_influence"]
    industry_impacts = [i for i in impacts if i.strategic_goal == "industry_collaboration"]
    grant_impacts = [i for i in impacts if i.strategic_goal == "grant_funding"]
    if research_impacts and influence_impacts and industry_impacts:
        flywheels.append({"flywheel": "Research → Public Influence → Industry Collaboration",
                         "evidence": f"{len(research_impacts)} research, {len(influence_impacts)} influence, {len(industry_impacts)} industry impacts.",
                         "recommendation": "Create repeatable workflow: paper insight → public explanation → targeted collaborator follow-up."})
    if research_impacts and grant_impacts:
        flywheels.append({"flywheel": "Research → Grant → More Research",
                         "evidence": f"Research and grant impacts coexist.",
                         "recommendation": "Use grant concept note workflow to convert research insights into fundable proposals."})
    if not flywheels:
        flywheels.append({"flywheel": "Undetected", "evidence": "Insufficient impact data to detect flywheels.",
                         "recommendation": "Record more impact events with linked entities."})
    return {"flywheels": flywheels, "summary": f"{len(flywheels)} potential flywheel(s) detected."}

# --- Decay Detector ---
def decay_review(relationships, projects, assets, assumptions, predictions, risks, workflows, okrs):
    decay = []
    now = date.today()
    for r in relationships:
        last = getattr(r, "last_contact_date", "")
        if last and last < (now - timedelta(days=60)).isoformat():
            decay.append({"type": "relationship", "name": getattr(r, "name", ""),
                         "issue": f"No contact in {(now - date.fromisoformat(last)).days} days."})
    for p in projects:
        if getattr(p, "status", "active") == "active" and getattr(p, "last_updated", ""):
            if getattr(p, "last_updated", "") < (now - timedelta(days=30)).isoformat():
                decay.append({"type": "project", "name": getattr(p, "name", str(p)),
                             "issue": "No progress update in 30+ days."})
    for a in assets:
        if getattr(a, "reuse_count", 0) == 0 and getattr(a, "created_date", ""):
            if getattr(a, "created_date", "") < (now - timedelta(days=90)).isoformat():
                decay.append({"type": "asset", "name": getattr(a, "name", ""),
                             "issue": "Created 90+ days ago, never reused."})
    for a in assumptions:
        last = getattr(a, "last_reviewed", "")
        if last and last < (now - timedelta(days=90)).isoformat():
            decay.append({"type": "assumption", "name": getattr(a, "statement", str(a))[:50],
                         "issue": "Not reviewed in 90+ days."})
    for p in predictions:
        if not getattr(p, "resolved", False):
            decay.append({"type": "prediction", "name": getattr(p, "prediction_statement", str(p))[:50],
                         "issue": "Unresolved prediction."})
    for r in risks:
        if not getattr(r, "mitigation_owner", ""):
            decay.append({"type": "risk", "name": getattr(r, "title", str(r)),
                         "issue": "No mitigation owner."})
    return {"decay_items": decay, "total": len(decay),
            "summary": f"{len(decay)} decaying strategic item(s)." if decay else "No strategic decay detected."}

# --- Optimized Rebalance ---
def rebalance_optimized(available_hours, energy_level, config, okrs, relationships, contracts, queue, risks):
    cfg = config or DEFAULT_CONFIG
    baseline = cfg.get("strategic_baseline", {g: 15 for g in STRATEGIC_GOALS})
    total_h = available_hours or 25
    # Start from baseline scaled to available hours
    alloc = {g: round(baseline.get(g, 15) / 100 * total_h, 1) for g in STRATEGIC_GOALS}
    # Adjust for energy
    if energy_level and energy_level <= 5: alloc["admin_maintenance"] = min(alloc["admin_maintenance"], total_h * 0.15)
    # Adjust for OKRs
    if okrs:
        active = [o for o in okrs if o.status == "active"]
        for o in active:
            if o.strategic_goal in alloc: alloc[o.strategic_goal] += 0.5
    # Adjust for overdue follow-ups
    stale_rels = sum(1 for r in relationships if getattr(r, "last_contact_date", "") and
                     getattr(r, "last_contact_date", "") < (date.today() - timedelta(days=45)).isoformat())
    if stale_rels > 2: alloc["industry_collaboration"] += 1
    # Protect deep work
    deep_work_goals = ["research_publication", "grant_funding", "deeptech_venture"]
    for g in deep_work_goals:
        if alloc.get(g, 0) < total_h * 0.1: alloc[g] = round(total_h * 0.1, 1)
    # Admin cap
    admin_cap = total_h * 0.25 if energy_level and energy_level >= 7 else total_h * 0.15
    alloc["admin_maintenance"] = min(alloc.get("admin_maintenance", 2), admin_cap)
    return {"allocation": alloc, "total_hours": total_h, "energy_level": energy_level or 7,
            "constraints": "3 deep-work blocks, max 2 high-focus tasks/day, 2 relationship follow-ups/week.",
            "recommendations": [f"Protect {alloc.get(g, 0):.1f}h for {g}" for g in deep_work_goals if alloc.get(g, 0) >= total_h * 0.1]}

# --- CSV Export / Import ---
import csv as csv_module

def export_csv(store_name, export_path):
    paths = {"metrics": METRICS_PATH, "projects": PROJECTS_PATH, "opportunities": OPPORTUNITIES_PATH,
             "impact": IMPACT_PATH, "risks": RISKS_PATH}
    if store_name not in paths: return {"error": f"Unknown store '{store_name}'. Options: {list(paths.keys())}"}
    path = paths[store_name]
    if not path.exists(): return {"error": f"Store '{store_name}' is empty."}
    data = json.loads(path.read_text())
    records = data.get("records", data) if isinstance(data, dict) else data
    if not isinstance(records, list) or not records:
        return {"error": f"No records in '{store_name}'."}
    export_path = Path(export_path) if export_path else Path(f"{store_name}_export.csv")
    with open(export_path, "w", newline="") as f:
        writer = csv_module.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader(); writer.writerows(records)
    return {"exported": str(export_path), "records": len(records), "store": store_name}

def import_csv(store_name, import_path):
    paths = {"metrics": (METRICS_PATH, "metrics"), "projects": (PROJECTS_PATH, "projects"),
             "opportunities": (OPPORTUNITIES_PATH, "opportunities"), "impact": (IMPACT_PATH, "impact"),
             "risks": (RISKS_PATH, "risks")}
    if store_name not in paths: return {"error": f"Unknown store '{store_name}'."}
    path, _ = paths[store_name]
    import_path = Path(import_path)
    if not import_path.exists(): return {"error": f"File not found: {import_path}"}
    with open(import_path, "r", newline="") as f:
        reader = csv_module.DictReader(f)
        records = list(reader)
    existing = json.loads(path.read_text()) if path.exists() else []
    existing_records = existing.get("records", existing) if isinstance(existing, dict) else existing
    if isinstance(existing_records, list): existing_records.extend(records)
    else: existing_records = records
    save_records(path, existing_records)
    return {"imported": len(records), "store": store_name, "total_records": len(existing_records)}

# --- AI Performance Review Prompt ---
def ai_performance_review_prompt():
    metrics_data = json.dumps({"metrics": metrics_review()}, default=str, indent=2)
    impact_data = json.dumps({"impact": impact_review()}, default=str, indent=2)
    return f"""=== AI PERFORMANCE REVIEW PROMPT ===
(COPY INTO YOUR AI ASSISTANT)

You are a board of strategic advisors conducting a performance review.
Roles: Chief of Staff, Research Mentor, Grant Strategist, Execution Coach, Founder/Investor, Sustainability Advisor.

Review the strategic performance data and answer:

1. What is working? (cite specific metrics or impacts)
2. What is NOT working?
3. What is overestimated?
4. What is underestimated?
5. What should be doubled down on?
6. What should be killed immediately?
7. What should be measured next?
8. Recommended 30-day correction plan.

--- PERFORMANCE DATA ---
{metrics_data}
{impact_data}

--- END DATA ---
Be ruthlessly honest. Prioritize long-term compounding over short-term comfort.
=== END AI PERFORMANCE REVIEW PROMPT ==="""

# ======================================================================
# V10 — STRATEGIC AUTONOMY & GOVERNANCE
# ======================================================================

# --- Command Queue ---
def load_commands():
    data = load_records(COMMAND_QUEUE_PATH); return [Command(**c) for c in data] if data else []
def save_commands(cs): save_records(COMMAND_QUEUE_PATH, [c.__dict__ for c in cs])

def generate_commands():
    """Generate commands from policy violations, conflicts, decay, and reviews."""
    cmds = []
    rels = load_records(RELATIONSHIPS_PATH) if RELATIONSHIPS_PATH.exists() else []; rels = [Relationship(**r) for r in rels] if rels else []
    projs = load_records(PROJECTS_PATH) if PROJECTS_PATH.exists() else []; projs = [Project(**p) for p in projs] if projs else []
    assets = load_core_records(ASSETS_PATH)
    assumps = load_core_records(ASSUMPTIONS_PATH)
    preds = load_core_records(PREDICTIONS_PATH)
    risks = load_core_records(RISKS_PATH)
    wfs = load_workflows(); okrs = load_records(OKRS_PATH) if OKRS_PATH.exists() else []; okrs = [OKR(**o) for o in okrs] if okrs else []
    oops = load_records(OPPORTUNITIES_PATH) if OPPORTUNITIES_PATH.exists() else []; oops = [Opportunity(**o) for o in oops] if oops else []
    decay = decay_review(rels, projs, assets, assumps, preds, risks, wfs, okrs)
    for d in decay.get("decay_items", [])[:5]:
        needs_approval = d["type"] == "relationship"
        cmds.append(Command(command_id=uid(), date_created=today_str(),
            title=f"Address decay: {d['name'][:50]}", description=d["issue"],
            command_type="follow_up" if d["type"]=="relationship" else "update_project",
            source_system="decay_review", priority_score=7, requires_human_approval=needs_approval,
            approval_status="pending" if needs_approval else "approved"))
    conflicts = conflict_review(get_data_for_conflict())
    for c in conflicts.get("conflicts", [])[:5]:
        cmds.append(Command(command_id=uid(), date_created=today_str(),
            title=f"Resolve conflict: {c['type'][:50]}", description=c.get("resolution", ""),
            command_type="rebalance_portfolio", source_system="conflict_review",
            priority_score=8, requires_human_approval=False))
    fups = followup_review(rels, oops)
    for f in fups.get("followups", [])[:3]:
        cmds.append(Command(command_id=uid(), date_created=today_str(),
            title=f"Follow up: {f['name'][:50]}", description=f"{f.get('days_since','?')} days since last contact",
            command_type="follow_up", source_system="followup_review",
            priority_score=6, requires_human_approval=True))
    existing = load_commands()
    existing_ids = {c.command_id for c in existing}
    new = [c for c in cmds if c.command_id not in existing_ids]
    existing.extend(new); save_commands(existing)
    return {"total_generated": len(new), "commands": [{"id": c.command_id, "title": c.title[:50]} for c in new],
            "summary": f"Generated {len(new)} command(s)." if new else "No new commands needed."}

def load_core_records(path):
    """Load raw records from path as dicts, returning empty list on any failure."""
    if not path.exists(): return []
    try:
        data = json.loads(path.read_text())
        return data.get("records", data) if isinstance(data, dict) else data
    except: return []

def load_projects_from_core():
    return [Project(**p) for p in (load_records(PROJECTS_PATH) or [])] if PROJECTS_PATH.exists() else []

def load_risks_from_core():
    return [Risk(**r) for r in (load_records(RISKS_PATH) or [])] if RISKS_PATH.exists() else []

def load_decisions_from_core():
    return [Decision(**d) for d in (load_records(DECISIONS_PATH) or [])] if DECISIONS_PATH.exists() else []

def load_rels_from_core():
    return [Relationship(**r) for r in (load_records(RELATIONSHIPS_PATH) or [])] if RELATIONSHIPS_PATH.exists() else []

def load_evidence_from_core():
    return [Evidence(**e) for e in (load_records(EVIDENCE_PATH) or [])] if EVIDENCE_PATH.exists() else []

def load_opps_from_core():
    return [Opportunity(**o) for o in (load_records(OPPORTUNITIES_PATH) or [])] if OPPORTUNITIES_PATH.exists() else []

def load_assets_from_core():
    return [StrategicAsset(**a) for a in (load_records(ASSETS_PATH) or [])] if ASSETS_PATH.exists() else []

def load_assums_from_core():
    return [Assumption(**a) for a in (load_records(ASSUMPTIONS_PATH) or [])] if ASSUMPTIONS_PATH.exists() else []

def load_preds_from_core():
    return [Prediction(**p) for p in (load_records(PREDICTIONS_PATH) or [])] if PREDICTIONS_PATH.exists() else []
def load_doctrine_from_core():
    return load_records(DOCTRINE_PATH) if DOCTRINE_PATH.exists() else []
    """Load raw records from path as dicts, returning empty list on any failure."""
    if not path.exists(): return []
    try:
        data = json.loads(path.read_text())
        return data.get("records", data) if isinstance(data, dict) else data
    except: return []

def command_review():
    cs = load_commands()
    if not cs: return {"total": 0, "message": "No commands. Use --generate-commands."}
    pending = [c for c in cs if c.approval_status == "pending"]
    approved = [c for c in cs if c.approval_status == "approved" and not c.title.startswith("Address decay: Follow up: Resolve conflict: ".split()[0])]
    return {"total": len(cs), "pending_approval": len(pending), "approved_ready": len([c for c in cs if c.approval_status == "approved"]),
            "top_pending": [{"id": c.command_id, "title": c.title[:60], "type": c.command_type, "needs_approval": c.requires_human_approval} for c in pending[:5]],
            "summary": f"{len(pending)} pending approval, {len(approved)} approved."}

def get_data_for_conflict():
    return {"projects": load_records(PROJECTS_PATH) if PROJECTS_PATH.exists() else [],
            "opportunities": load_records(OPPORTUNITIES_PATH) if OPPORTUNITIES_PATH.exists() else [],
            "risks": load_records(RISKS_PATH) if RISKS_PATH.exists() else [],
            "relationships": load_records(RELATIONSHIPS_PATH) if RELATIONSHIPS_PATH.exists() else [],
            "okrs": load_records(OKRS_PATH) if OKRS_PATH.exists() else [],
            "contracts": load_records(CONTRACTS_PATH) if CONTRACTS_PATH.exists() else [],
            "capacity": load_capacity(), "metrics": load_metrics(), "workflows": load_records(WORKFLOWS_PATH) if WORKFLOWS_PATH.exists() else []}

# --- Human Approval ---
def load_approvals():
    data = load_records(APPROVALS_PATH); return [Approval(**a) for a in data] if data else []
def save_approvals(aps): save_records(APPROVALS_PATH, [a.__dict__ for a in aps])

def approve_command(command_id, reason=""):
    cs = load_commands(); aps = load_approvals()
    for c in cs:
        if c.command_id == command_id:
            c.approval_status = "approved"
            aps.append(Approval(approval_id=uid(), command_id=command_id, requested_at=c.date_created,
                                approved_at=today_str(), approver="user", approval_status="approved", reason=reason))
            save_commands(cs); save_approvals(aps); return c
    return None

def reject_command(command_id, reason=""):
    cs = load_commands(); aps = load_approvals()
    for c in cs:
        if c.command_id == command_id:
            c.approval_status = "rejected"
            aps.append(Approval(approval_id=uid(), command_id=command_id, requested_at=c.date_created,
                                approved_at=today_str(), approver="user", approval_status="rejected", reason=reason))
            save_commands(cs); save_approvals(aps); return c
    return None

# --- Policies ---
def load_policies():
    data = load_records(POLICIES_PATH)
    if not data: return [Policy(**p, created_at=today_str()) for p in DEFAULT_POLICIES]
    return [Policy(**p) for p in data]
def save_policies(ps): save_records(POLICIES_PATH, [p.__dict__ for p in ps])

def policy_review():
    ps = load_policies(); active = [p for p in ps if p.active]
    return {"total": len(ps), "active": len(active),
            "by_severity": {"high": len([p for p in active if p.severity=="high"]),
                          "medium": len([p for p in active if p.severity=="medium"]),
                          "low": len([p for p in active if p.severity=="low"])},
            "summary": f"{len(active)} active policies."}

# --- Conflict Detection ---
def conflict_review(data):
    conflicts = []
    cap = data.get("capacity", {})
    projs = data.get("projects", []); active_projs = [p for p in projs if getattr(p, "status", "active")=="active"]
    max_projs = cap.get("max_active_projects", 5) if isinstance(cap, dict) else 5
    if len(active_projs) > max_projs:
        conflicts.append({"type": "project_capacity", "severity": "high",
                         "description": f"{len(active_projs)} active projects exceeds capacity ({max_projs}).",
                         "resolution": "Pause or merge lowest-ROI projects."})
    okrs = data.get("okrs", [])
    active_okrs = [o for o in okrs if getattr(o, "status", "active")=="active"]
    grant_okrs = [o for o in active_okrs if getattr(o, "strategic_goal","")=="grant_funding"]
    research_okrs = [o for o in active_okrs if getattr(o, "strategic_goal","")=="research_publication"]
    if len(grant_okrs) >= 2 and len(research_okrs) >= 2:
        conflicts.append({"type": "okr_competition", "severity": "medium",
                         "description": "Multiple grant and research OKRs compete for deep-work hours.",
                         "resolution": "Prioritize one per quarter; defer others."})
    contracts = data.get("contracts", [])
    active_contracts = [c for c in contracts if getattr(c, "status", "")=="active"]
    if active_contracts and len(active_okrs) == 0:
        conflicts.append({"type": "contract_no_okr", "severity": "low",
                         "description": "Active contracts exist but no OKRs to track them.",
                         "resolution": "Create an OKR linked to the contract."})
    return {"conflicts": conflicts, "total": len(conflicts),
            "summary": f"{len(conflicts)} conflict(s) detected." if conflicts else "No strategic conflicts detected."}

# --- Capacity ---
def load_capacity():
    data = load_json(CAPACITY_PATH, DEFAULT_CAPACITY)
    return data if isinstance(data, dict) else DEFAULT_CAPACITY
def save_capacity(c): save_json(CAPACITY_PATH, c, is_records=False)

def capacity_review(cap=None):
    cap = cap or load_capacity()
    projs = load_projects_from_core(); active = [p for p in projs if getattr(p, "status", "active")=="active"]
    max_projs = cap.get("max_active_projects", 5)
    feasible = len(active) <= max_projs
    return {"capacity": cap, "active_projects": len(active), "max_projects": max_projs,
            "feasible": feasible,
            "deep_work_conservative": cap.get("weekly_deep_work_hours", 15) >= 12,
            "summary": f"{len(active)}/{max_projs} projects active — {'feasible' if feasible else 'over-capacity'}."}

# --- Initiatives ---
def load_initiatives():
    data = load_records(INITIATIVES_PATH); return [Initiative(**i) for i in data] if data else []
def save_initiatives(ins): save_records(INITIATIVES_PATH, [i.__dict__ for i in ins])

def initiative_health_score(initiative, projs, metrics, risks):
    active_projs = [p for p in projs if getattr(p, "project_id", "") in initiative.linked_projects]
    progress = len([p for p in active_projs if getattr(p, "status","")=="active"]) / max(len(active_projs), 1) * 50
    linked_metrics = [m for m in metrics if m.metric_id in initiative.linked_metrics]
    metric_pct = sum(m.current_value / max(m.target_value, 0.01) for m in linked_metrics) / max(len(linked_metrics), 1) * 25
    risk_free = 15 if not any(getattr(r, "severity", 5) >= 7 for r in risks if getattr(r, "project_id","") in initiative.linked_projects) else 5
    score = progress + min(metric_pct, 25) + risk_free
    if score >= 70: label = "healthy"
    elif score >= 50: label = "watch"
    elif score >= 30: label = "at_risk"
    elif score >= 10: label = "critical"
    else: label = "stale"
    return {"score": round(score, 1), "label": label, "progress": round(progress, 1),
            "metric_component": round(metric_pct, 1), "risk_component": risk_free}

def initiative_review():
    ins = load_initiatives(); projs_all = load_projects_from_core(); ms = load_metrics(); rs = load_risks_from_core()
    if not ins: return {"total": 0, "message": "No initiatives. Use --add-initiative."}
    results = []
    for i in ins:
        hs = initiative_health_score(i, projs_all, ms, rs)
        results.append({"name": i.name, "goal": i.strategic_goal, "status": i.status,
                       "health": hs["label"], "health_score": hs["score"],
                       "phase": i.current_phase or "planning"})
    return {"total": len(ins), "initiatives": results,
            "summary": f"{len([r for r in results if r['health']=='healthy'])} healthy, "
                       f"{len([r for r in results if r['health']=='at_risk'])} at risk."}

# --- Governance Board ---
def governance_board():
    data = get_data_for_conflict()
    ins = initiative_review(); cmd_r = command_review(); pol_r = policy_review()
    conflicts = conflict_review(data); cap_r = capacity_review(data.get("capacity"))
    rels = [Relationship(**r) for r in (load_records(RELATIONSHIPS_PATH) or [])] if RELATIONSHIPS_PATH.exists() else []
    projs = [Project(**p) for p in (load_records(PROJECTS_PATH) or [])] if PROJECTS_PATH.exists() else []
    decay = decay_review(rels, projs, load_core_records(ASSETS_PATH),
                         load_core_records(ASSUMPTIONS_PATH), load_core_records(PREDICTIONS_PATH),
                         load_core_records(RISKS_PATH), load_workflows(), [OKR(**o) for o in (load_records(OKRS_PATH) or [])] if OKRS_PATH.exists() else [])
    return {"strategic_position": "Advance research, secure grants, build collaborations, govern carefully.",
            "initiatives": ins, "command_queue": cmd_r, "policies": pol_r,
            "conflicts": conflicts, "capacity": cap_r, "decay": decay.get("summary",""),
            "recommended_decisions": ["Approve pending safe commands",
                                      "Resolve conflicts" if conflicts.get("total",0) > 0 else "No conflicts",
                                      "Pay down strategic debt" if decay.get("total",0) > 0 else "No decay detected"]}

# --- Decision & Command Packets ---
def decision_packet(decision_id):
    decs = load_decisions_from_core()
    d = next((d for d in decs if d.decision_id == decision_id), None)
    if not d: return None
    return {"decision": d.title, "context": d.context or "No context recorded.",
            "options": d.options or "No options documented.",
            "evidence": d.evidence or "No evidence noted.",
            "decision_date": d.decision_date, "review_date": d.review_date,
            "actual_outcome": d.actual_outcome or "Pending"}

def command_packet(command_id):
    cs = load_commands()
    c = next((c for c in cs if c.command_id == command_id), None)
    if not c: return None
    return {"title": c.title, "type": c.command_type, "description": c.description,
            "action": c.recommended_action or c.description,
            "priority": c.priority_score, "urgency": c.urgency_score,
            "risk": c.risk_score, "needs_approval": c.requires_human_approval,
            "status": c.approval_status, "benefit": c.expected_benefit or "Strategic improvement.",
            "cost": c.opportunity_cost or "Minimal — local action."}

# --- Pre-mortem / Post-mortem ---
def premortem(project_id):
    projs = load_projects_from_core(); p = next((p for p in projs if p.project_id == project_id), None)
    name = p.name if p else project_id
    return {"entity": name, "type": "project",
            "failure_modes": ["Loss of key collaborator", "Funding gap", "Scope creep", "Competing priorities", "Technical dead end"],
            "early_warnings": ["Milestone delays > 30 days", "Weekly deep work < 2 hours", "Collaborator disengagement"],
            "prevention": ["Protect 2 deep-work blocks/week", "Weekly collaborator check-in", "30-day milestone review"],
            "contingency": "If delayed > 60 days, reduce scope or merge with adjacent project.",
            "owner": "Project lead"}

def postmortem(project_id):
    projs = load_projects_from_core(); p = next((p for p in projs if p.project_id == project_id), None)
    name = p.name if p else project_id
    return {"entity": name, "expected_vs_actual": "Expected: complete by target. Actual: review status.",
            "root_causes": ["Insufficient protected time", "Underestimated complexity", "Weak follow-up"],
            "avoidable_mistakes": ["No weekly review cadence", "Scope not constrained early"],
            "useful_surprises": ["List any unexpected positives."],
            "lessons": ["Protect deep work ruthlessly.", "Review scope at milestone 1.", "Log evidence weekly."],
            "doctrine_updates": ["Deep work is non-negotiable.", "Scope must be constrained at milestone 1."],
            "system_improvements": ["Add milestone-based project health check", "Auto-flag projects without weekly progress"]}

# --- Strategic Debt ---
def load_strategic_debt():
    data = load_records(STRATEGIC_DEBT_PATH); return [StrategicDebt(**d) for d in data] if data else []
def save_strategic_debt(ds): save_records(STRATEGIC_DEBT_PATH, [d.__dict__ for d in ds])

def debt_review():
    ds = load_strategic_debt()
    if not ds: return {"total": 0, "message": "No strategic debt recorded. Use --add-debt."}
    high_interest = sorted(ds, key=lambda d: -d.interest_rate)[:5]
    return {"total": len(ds), "by_type": {t: len([d for d in ds if d.debt_type==t]) for t in set(d.debt_type for d in ds)},
            "highest_interest": [{"title": d.title[:50], "type": d.debt_type, "interest": d.interest_rate} for d in high_interest],
            "summary": f"{len(ds)} debt items; highest interest: {high_interest[0].debt_type if high_interest else 'none'}."}

# --- Complexity Audit ---
def complexity_audit():
    active_projs = len([p for p in load_projects_from_core() if getattr(p, "status", "active")=="active"])
    active_opps = len([o for o in load_opps_from_core() if getattr(o, "status", "active")=="active"])
    active_wfs = len([w for w in load_workflows() if getattr(w, "status", "active")=="active"])
    unresolved_risks = len([r for r in load_risks_from_core() if not getattr(r, "mitigation_owner", "")])
    pending_cmds = len([c for c in load_commands() if c.approval_status=="pending"])
    stale_records = 0
    for path in [OPPORTUNITIES_PATH, PROJECTS_PATH, RISKS_PATH]:
        if path.exists():
            try:
                data = json.loads(path.read_text()); recs = data.get("records", data) if isinstance(data, dict) else data
                stale_records += sum(1 for r in recs if isinstance(r, dict) and r.get("last_touched_date", r.get("last_updated", "")) < (date.today() - timedelta(days=60)).isoformat())
            except: pass
    wf_runs = load_workflow_runs(); wrs_count = len(wf_runs)
    est_burden = active_projs * 2 + active_opps * 0.5 + active_wfs * 1 + pending_cmds * 0.3
    warning = est_burden > 15
    return {"active_projects": active_projs, "active_opportunities": active_opps, "active_workflows": active_wfs,
            "unresolved_risks": unresolved_risks, "pending_commands": pending_cmds,
            "stale_records": stale_records, "workflow_runs": wrs_count,
            "estimated_burden": round(est_burden, 1), "warning": warning,
            "summary": f"Complexity burden: {est_burden:.1f}. {'WARNING: exceeds safe threshold.' if warning else 'Manageable.'}"}

# --- Simplification Engine ---
def simplify():
    recommendations = []
    rels = [Relationship(**r) for r in (load_records(RELATIONSHIPS_PATH) or [])] if RELATIONSHIPS_PATH.exists() else []
    projs = [Project(**p) for p in (load_records(PROJECTS_PATH) or [])] if PROJECTS_PATH.exists() else []
    assets = load_core_records(ASSETS_PATH)
    decay = decay_review(rels, projs, assets,
                         load_core_records(ASSUMPTIONS_PATH), load_core_records(PREDICTIONS_PATH),
                         load_core_records(RISKS_PATH), load_workflows(),
                         [OKR(**o) for o in (load_records(OKRS_PATH) or [])] if OKRS_PATH.exists() else [])
    for d in decay.get("decay_items", []):
        if d["type"] == "project":
            recommendations.append(f"Pause or kill stale project: {d['name']}")
        elif d["type"] == "asset":
            recommendations.append(f"Archive unused asset: {d['name']}")
    opps = [Opportunity(**o) for o in (load_records(OPPORTUNITIES_PATH) or [])] if OPPORTUNITIES_PATH.exists() else []
    for o in opps:
        if getattr(o, "last_touched_date", "") and getattr(o, "last_touched_date", "") < (date.today() - timedelta(days=90)).isoformat():
            recommendations.append(f"Close stale opportunity: {getattr(o, 'name', str(o))}")
    wfs = load_workflows()
    if len(wfs) > 12: recommendations.append("Archive unused workflows — more than 12 active.")
    rois = roi_review(projs, wfs, rels, opps, assets, load_metrics())
    for item in rois.get("low_roi", [])[:3]:
        recommendations.append(f"Consider pausing low-ROI {item['type']}: {item['name']}")
    return {"recommendations": list(set(recommendations))[:10], "total": len(set(recommendations)),
            "summary": f"{len(set(recommendations))} simplification recommendation(s)."}

# --- OS Health Score ---
def os_health():
    score = 0
    # Data freshness (15 pts)
    ms = load_metrics(); recently_updated = sum(1 for m in ms if m.last_updated and m.last_updated >= (date.today() - timedelta(days=30)).isoformat())
    score += min(15, recently_updated * 3)
    # Review adherence (15 pts)
    adh = adherence_review(load_rhythms(), load_contracts(), load_doctrine_from_core(), load_okrs(), load_recent_history(14))
    score += adh["adherence_score"] / 100 * 15
    # Command queue clarity (10 pts)
    cs = load_commands(); pending_old = sum(1 for c in cs if c.approval_status=="pending" and c.date_created < (date.today() - timedelta(days=14)).isoformat())
    score += 10 - min(10, pending_old * 2)
    # Measurement quality (10 pts)
    score += min(10, len(ms) * 2)
    # Evidence quality (10 pts)
    ev = load_evidence_from_core(); score += min(10, len(ev) * 2)
    # Capacity realism (10 pts)
    cap_r = capacity_review(); score += 10 if cap_r["feasible"] else 3
    # Follow-up discipline (10 pts)
    fups = followup_review(load_rels_from_core(), load_opps_from_core()); score += 10 - min(10, fups.get("total", 0) * 1.5)
    # Decision review (10 pts)
    decs = load_decisions_from_core(); reviewed = sum(1 for d in decs if getattr(d, "actual_outcome", ""))
    score += min(10, reviewed * 3)
    # Complexity control (10 pts)
    ca = complexity_audit(); score += 10 if not ca["warning"] else 3
    score = round(min(100, max(0, score)), 1)
    return {"os_health_score": score, "status": "healthy" if score >= 70 else "needs_attention" if score >= 50 else "critical",
            "strengths": [k for k, v in {"data_freshness": recently_updated > 2, "low_complexity": not ca["warning"]}.items() if v],
            "weaknesses": [k for k, v in {"stale_commands": pending_old > 2, "over_capacity": not cap_r["feasible"], "poor_followup": fups.get("total", 0) > 3}.items() if v],
            "summary": f"OS Health: {score}/100 ({'healthy' if score >= 70 else 'needs_attention' if score >= 50 else 'critical'})."}

# --- Autonomy ---
def load_autonomy():
    data = load_json(AUTONOMY_PATH, DEFAULT_AUTONOMY)
    return data if isinstance(data, dict) else DEFAULT_AUTONOMY
def save_autonomy(a): save_json(AUTONOMY_PATH, a, is_records=False)

def set_autonomy_level(level):
    try: lv = int(level)
    except: return {"error": f"Invalid level: {level}. Use 0-4."}
    if lv > 4: return {"error": "Level 5 (external actions) is disabled in V10."}
    a = load_autonomy(); a["level"] = lv; a["label"] = AUTONOMY_LEVELS[lv]
    if lv <= 1: a["allowed_local_actions"] = []
    elif lv == 2: a["allowed_local_actions"] = ["update_metric","capture_evidence"]
    elif lv >= 4: a["allowed_local_actions"] = ["update_metric","capture_evidence","run_workflow","generate_report","update_project"]
    save_autonomy(a); return a

# --- Integration Stubs ---
class CalendarProvider:
    def create_event(self, *args, **kwargs): raise NotImplementedError
class EmailProvider:
    def create_draft(self, *args, **kwargs): raise NotImplementedError
class DocumentProvider:
    def create_document(self, *args, **kwargs): raise NotImplementedError

class NoOpCalendarProvider(CalendarProvider):
    def create_event(self, *args, **kwargs): return {"status": "noop", "message": "Calendar integration disabled."}
class NoOpEmailProvider(EmailProvider):
    def create_draft(self, *args, **kwargs): return {"status": "noop", "message": "Email integration disabled."}
class NoOpDocumentProvider(DocumentProvider):
    def create_document(self, *args, **kwargs): return {"status": "noop", "message": "Document integration disabled."}

# --- Local Command Execution ---
def execute_approved():
    cs = load_commands(); autonomy = load_autonomy()
    approved = [c for c in cs if c.approval_status == "approved"]
    executed = []; rejected = []
    for c in approved:
        if c.requires_human_approval and c.approval_status != "approved":
            rejected.append(c); continue
        if c.command_type in EXTERNAL_ACTION_TYPES and autonomy["level"] < 5:
            rejected.append(c); continue
        if c.command_type not in autonomy.get("allowed_local_actions", []) and autonomy["level"] < 3:
            rejected.append(c); continue
        # Execute safe local actions
        if c.command_type == "update_metric":
            ms = load_metrics()
            if c.linked_outcome_id:
                for m in ms:
                    if m.metric_id == c.linked_outcome_id: m.current_value += 1; m.last_updated = today_str()
                save_metrics(ms)
        elif c.command_type == "capture_evidence":
            ev = load_evidence_from_core(); ev_id = uid()
            ev.append(Evidence(evidence_id=ev_id, title=c.title[:50], description=c.description, source="command_execution"))
            save_evidence(ev)
        elif c.command_type == "update_project":
            pass  # Safe local update — no destructive action
        c.approval_status = "executed"; executed.append(c)
        _audit_log("execute_command", c.command_id, "approved", "executed")
    save_commands(cs)
    return {"executed": len(executed), "rejected": len(rejected),
            "summary": f"Executed {len(executed)}, rejected {len(rejected)}."}

def _audit_log(action, entity_id, old_state, new_state):
    """Simple audit trail for command execution."""
    audit_path = Path("chief_of_staff_audit_log.json")
    entries = json.loads(audit_path.read_text()).get("records", []) if audit_path.exists() else []
    entries.append({"timestamp": datetime.now().isoformat(), "action": action, "entity_id": entity_id,
                    "old_state": old_state, "new_state": new_state})
    save_json(audit_path, {"records": entries, "schema_version": "10.0"}, is_records=False)

# --- AI Governance Prompt ---
def ai_governance_review_prompt():
    gb = governance_board(); ca = complexity_audit(); oh = os_health()
    return f"""=== AI GOVERNANCE REVIEW PROMPT ===
(COPY INTO YOUR AI ASSISTANT)

You are a governance board reviewing a strategic operating system.
Roles: Governance Chief of Staff, Skeptical Board Member, Risk Officer, Execution Realist, Strategic Simplifier, Founder/PI Mentor.

Context:
- Initiatives: {gb['initiatives'].get('total', 0) if isinstance(gb.get('initiatives'), dict) else '?'} active
- Pending commands: {gb['command_queue'].get('pending_approval', 0) if isinstance(gb.get('command_queue'), dict) else '?'}
- Conflicts: {gb['conflicts'].get('total', 0) if isinstance(gb.get('conflicts'), dict) else '?'}
- OS Health: {oh['os_health_score']}/100
- Complexity: {'Warning' if ca.get('warning') else 'Manageable'}

Answer:
1. What should be approved?
2. What should be rejected?
3. What should be paused?
4. What should be killed?
5. What is overcomplicated?
6. What decision is being avoided?
7. What strategic debt matters most?
8. What 7-day correction is recommended?

Be governance-focused: prioritize safety, sustainability, and long-term compounding.
=== END AI GOVERNANCE REVIEW PROMPT ==="""
