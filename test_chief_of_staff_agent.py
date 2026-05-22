#!/usr/bin/env python3
"""Tests for Chief of Staff Agent v6."""
from __future__ import annotations
import json, os, sys, unittest, tempfile, shutil
from pathlib import Path
from datetime import date, timedelta
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from chief_of_staff_core import *
from chief_of_staff_agent import *


class TestTaskScoring(unittest.TestCase):
    """V5 — Task scoring and ranking."""

    def setUp(self):
        self.t1 = Task("Grant proposal", impact=9, urgency=9, strategic_value=10,
                       compounding_effect=8, goal_alignment=10, deadline_pressure=9,
                       energy_fit=8, opportunity_cost=2, focus_requirement=9,
                       estimated_minutes=120, strategic_goal="grant_funding")
        self.t2 = Task("Admin cleanup", impact=2, urgency=2, strategic_value=1,
                       compounding_effect=1, goal_alignment=1, deadline_pressure=1,
                       energy_fit=2, opportunity_cost=8, focus_requirement=2,
                       estimated_minutes=90, strategic_goal="admin_maintenance")

    def test_compute_weighted_score(self):
        s = compute_weighted_score(self.t1)
        self.assertGreater(s, 8)
        self.assertLess(s, 10)

    def test_compute_final_score(self):
        s = compute_final_score(self.t1)
        self.assertGreater(s, 8)

    def test_score_label(self):
        self.assertEqual(score_label(9), "CRITICAL")
        self.assertEqual(score_label(7), "HIGH")
        self.assertEqual(score_label(5), "MEDIUM")
        self.assertEqual(score_label(3), "LOW")

    def test_score_task(self):
        st = score_task(self.t1)
        self.assertGreater(st.final_score, 8)
        self.assertTrue(st.label)

    def test_rank_tasks(self):
        ranked = rank_tasks([self.t2, self.t1])
        self.assertEqual(ranked[0].name, "Grant proposal")

    def test_generate_warnings_admin(self):
        w = generate_warnings(self.t2)
        self.assertTrue(any("opportunity cost" in x.lower() for x in w))

    def test_generate_warnings_urgency(self):
        t = Task("Fire drill", impact=3, urgency=9, strategic_value=2,
                 goal_alignment=2, energy_fit=5, focus_requirement=5)
        w = generate_warnings(t)
        self.assertTrue(any("low impact" in x.lower() for x in w))

    def test_do_capacity(self):
        self.assertEqual(do_capacity(3), 1)
        self.assertEqual(do_capacity(5), 2)
        self.assertEqual(do_capacity(8), 3)

    def test_classify_tasks(self):
        tasks = [self.t1, self.t2]
        ranked = rank_tasks(tasks)
        do, delay, dele, ignore, do_mins, over = classify_tasks(ranked, 7, 200)
        self.assertTrue(len(do) >= 1)

    def test_portfolio_diagnosis(self):
        cnt, mins, avg, total = portfolio_diagnosis([self.t1, self.t2])
        self.assertGreater(total, 0)
        self.assertIn("grant_funding", cnt)

    def test_opp_score(self):
        o = Opportunity(potential_value=8, probability=7, urgency=6,
                        relationship_value=5, effort_required=3)
        s = opp_score(o)
        self.assertGreater(s, 4)
        self.assertLess(s, 8)

    def test_risk_score(self):
        r = Risk(probability=8, severity=9, detectability=5)
        self.assertEqual(risk_score(r), 360)

    def test_decision_quality_score(self):
        d = Decision(clarity_of_objective=7, quality_of_options=6,
                     evidence_quality=5, opportunity_cost_awareness=4,
                     risk_awareness=6, outcome_quality=5)
        s = decision_quality_score(d)
        self.assertAlmostEqual(s, 5.5, delta=0.1)

    def test_make_execution_script(self):
        t = Task("test", strategic_goal="grant_funding")
        s = make_execution_script(t)
        self.assertTrue(len(s) >= 3)

    def test_suggest_decomposition_long_task(self):
        t = Task("Big task", estimated_minutes=240, final_score=3.0)
        steps = suggest_decomposition(t)
        self.assertTrue(len(steps) >= 2)

    def test_suggest_decomposition_short_task(self):
        t = Task("Small task", estimated_minutes=30, final_score=7.0)
        steps = suggest_decomposition(t)
        self.assertEqual(steps, [])


class TestMissingV5Functions(unittest.TestCase):
    """V5 — functions that were missing."""

    def test_make_first_30min(self):
        t = Task("Deep work", focus_requirement=9, estimated_minutes=120,
                 next_action="open file")
        result = make_first_30min([t])
        self.assertIn("Deep work", result)
        self.assertIn("Deep-work", result)

    def test_make_first_30min_empty(self):
        result = make_first_30min([])
        self.assertIn("No DO tasks", result)

    def test_make_first_30min_low_energy(self):
        t = Task("Hard task", energy_fit=2, estimated_minutes=60,
                 next_action="start")
        result = make_first_30min([t])
        self.assertIn("energy is highest", result)

    def test_ser_task(self):
        t = Task("Test", impact=5)
        d = ser_task(t)
        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["impact"], 5)

    def test_load_history_nonexistent(self):
        result = load_history("2099-01-01")
        self.assertIsNone(result)

    def test_build_and_save_history(self):
        t = Task("Test task", impact=5, estimated_minutes=30)
        ranked = rank_tasks([t])
        record = build_history_record([t], ranked, 6.0, 360, "none", "none",
                                       7, ranked[:1], [], [], [], 30, False, "Start task")
        self.assertEqual(record["date"], today_str())
        self.assertIn("do", record)
        save_history(record)
        loaded = load_history(today_str())
        self.assertIsNotNone(loaded)
        # Cleanup
        (HISTORY_DIR / f"{today_str()}_plan.json").unlink(missing_ok=True)

    def test_load_recent_history(self):
        records = load_recent_history(7)
        self.assertIsInstance(records, list)


class TestV6Dataclasses(unittest.TestCase):
    """V6 — dataclass instantiation."""

    def test_outcome(self):
        o = Outcome(name="Publish 3 papers", time_horizon="1_year",
                    current_status="drafting", desired_status="published",
                    confidence_level=7, importance=9)
        self.assertEqual(o.name, "Publish 3 papers")

    def test_evidence(self):
        e = Evidence(title="Paper accepted", evidence_type="result",
                     strength=8, reliability=9)
        self.assertEqual(e.evidence_type, "result")

    def test_assumption(self):
        a = Assumption(statement="Reviewers will understand the method",
                       category="research", confidence=6, importance=8)
        self.assertEqual(a.category, "research")

    def test_prediction(self):
        p = Prediction(prediction_statement="Grant will be funded",
                       category="grant", probability=60)
        self.assertEqual(p.probability, 60)

    def test_hypothesis(self):
        h = Hypothesis(statement="Publishing in higher-tier journal increases citations",
                       strategic_goal="research_publication", confidence_before=7)
        self.assertEqual(h.status, "untested")

    def test_asset(self):
        a = Asset(name="Grant proposal template", asset_type="proposal_template",
                  reuse_count=5, estimated_future_value=9)
        self.assertEqual(a.reuse_count, 5)

    def test_doctrine(self):
        d = Doctrine(principle="Never schedule deep work after 3pm",
                     rationale="Cognitive fatigue reduces output quality",
                     related_bias="planning_fallacy")
        self.assertIn("deep work", d.principle.lower())


class TestV6CoreFunctions(unittest.TestCase):
    """V6 — core analysis functions."""

    def setUp(self):
        self.demo_tasks = [
            Task("Grant proposal", 9, 9, 10, 8, 10, 9, 8, 2, 9, 120, "grant_funding"),
            Task("Literature review", 6, 5, 9, 7, 9, 4, 7, 3, 7, 90, "research_publication"),
            Task("Admin cleanup", 2, 2, 1, 1, 1, 1, 2, 8, 2, 90, "admin_maintenance"),
        ]
        self.demo_tasks = [score_task(t) for t in self.demo_tasks]

    def test_calibration_review_empty(self):
        r = calibration_review([])
        self.assertEqual(r["total_predictions"], 0)

    def test_calibration_review_no_resolved(self):
        p = Prediction(prediction_statement="Test", probability=70)
        r = calibration_review([p])
        self.assertEqual(r["resolved"], 0)
        self.assertIn("message", r)

    def test_calibration_review_well_calibrated(self):
        p = Prediction(prediction_statement="Well cal", probability=70,
                       resolved=True, actual_outcome=True, brier_score=0.09)
        r = calibration_review([p])
        self.assertEqual(r["resolved"], 1)
        self.assertLess(r["avg_brier_score"], 0.3)

    def test_decision_quality_review_empty(self):
        r = decision_quality_review([])
        self.assertIn("message", r)

    def test_decision_quality_review(self):
        d = Decision(title="Test", clarity_of_objective=8, quality_of_options=7,
                     evidence_quality=6, opportunity_cost_awareness=5,
                     risk_awareness=6, outcome_quality=5, actual_outcome="worked")
        r = decision_quality_review([d])
        self.assertEqual(r["total_decisions"], 1)
        self.assertGreater(r["avg_quality_score"], 5)

    def test_leverage_analysis(self):
        assets = [Asset(name="Template", asset_type="proposal_template",
                        reuse_count=3, estimated_future_value=9)]
        r = leverage_analysis(self.demo_tasks, [], assets)
        self.assertIn("high_leverage_tasks", r)
        self.assertTrue(len(r["compounding_assets"]) >= 1)

    def test_constraint_diagnosis(self):
        risks = [Risk(title="Grant rejection", severity=8, category="grant_failure",
                       status="active", mitigation="Draft backup plan")]
        r = constraint_diagnosis(self.demo_tasks, risks, [])
        self.assertTrue(len(r["constraints"]) >= 1)

    def test_eighty_twenty_review(self):
        r = eighty_twenty_review(self.demo_tasks, [])
        self.assertIn("top20_score_pct", r)
        self.assertGreater(r["total_tasks"], 0)

    def test_eighty_twenty_review_empty(self):
        r = eighty_twenty_review([], [])
        self.assertIn("message", r)

    def test_bias_detection(self):
        r = bias_detection(self.demo_tasks, [], [], [])
        self.assertIn("biases", r)

    def test_strategic_scorecard(self):
        r = strategic_scorecard(self.demo_tasks, [], [], [], [])
        self.assertIn("overall_score", r)
        self.assertIn("grade", r)
        self.assertEqual(len(r["dimensions"]), 5)

    def test_red_team_prompt(self):
        prompt = red_team_prompt(self.demo_tasks, [], [], [], [])
        self.assertIn("RED-TEAM", prompt)
        self.assertIn("blind spot", prompt)

    def test_board_memo_prompt(self):
        prompt = board_memo_prompt([], [], [], [], [])
        self.assertIn("BOARD MEMO", prompt)
        self.assertIn("Executive Summary", prompt)

    def test_kill_list_recommendation(self):
        r = kill_list_recommendation(self.demo_tasks, [], [], [])
        self.assertIn("kill_items", r)
        # Admin cleanup should be a kill candidate
        self.assertTrue(any("Admin" in k["target"] for k in r["kill_items"]))

    def test_compounding_asset_review_empty(self):
        r = compounding_asset_review([])
        self.assertEqual(r["total_assets"], 0)

    def test_compounding_asset_review(self):
        assets = [Asset(name="Template A", asset_type="proposal_template",
                        reuse_count=4, estimated_future_value=8),
                  Asset(name="Dataset B", asset_type="research_dataset",
                        reuse_count=1, estimated_future_value=9)]
        r = compounding_asset_review(assets)
        self.assertEqual(r["total_assets"], 2)
        self.assertEqual(r["reused_assets"], 1)
        self.assertTrue(len(r["promote"]) >= 1)


class TestV6Storage(unittest.TestCase):
    """V6 — schema-versioned storage with JSON recovery."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.test_path = Path(self.tmpdir) / "test_store.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load_records(self):
        records = [{"id": "1", "name": "Test"}]
        save_records(self.test_path, records)
        loaded = load_records(self.test_path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["name"], "Test")

    def test_load_missing_file(self):
        p = Path(self.tmpdir) / "nonexistent.json"
        loaded = load_json(p)
        self.assertEqual(loaded, [])

    def test_load_corrupt_json_no_backup(self):
        self.test_path.write_text("{this is not json")
        loaded = load_json(self.test_path)
        self.assertEqual(loaded, [])

    def test_load_corrupt_json_with_backup(self):
        bak = self.test_path.with_suffix(self.test_path.suffix + ".bak")
        bak.write_text(json.dumps([{"id": "backup"}]))
        self.test_path.write_text("{corrupt")
        loaded = load_json(self.test_path)
        self.assertEqual(loaded[0]["id"], "backup")

    def test_schema_version_in_records(self):
        records = [{"id": "1"}]
        save_records(self.test_path, records)
        content = json.loads(self.test_path.read_text())
        self.assertEqual(content["schema_version"], SCHEMA_VERSION)
        self.assertIn("created_at", content)

    def test_backup_on_save(self):
        records = [{"id": "orig"}]
        save_json(self.test_path, records, backup=False, is_records=True)
        records2 = [{"id": "updated"}]
        save_json(self.test_path, records2, backup=True, is_records=True)
        bak = self.test_path.with_suffix(self.test_path.suffix + ".bak")
        self.assertTrue(bak.exists())


class TestV6Constants(unittest.TestCase):
    """V6 — verify constants are properly defined."""

    def test_evidence_types(self):
        self.assertTrue(len(EVIDENCE_TYPES) >= 5)
        self.assertIn("observation", EVIDENCE_TYPES)

    def test_assumption_categories(self):
        self.assertTrue(len(ASSUMPTION_CATEGORIES) >= 5)
        self.assertIn("research", ASSUMPTION_CATEGORIES)

    def test_asset_types(self):
        self.assertTrue(len(ASSET_TYPES) >= 5)
        self.assertIn("proposal_template", ASSET_TYPES)

    def test_bias_types(self):
        self.assertTrue(len(BIAS_TYPES) >= 5)
        self.assertIn("planning_fallacy", BIAS_TYPES)

    def test_time_horizons(self):
        self.assertTrue(len(TIME_HORIZONS) >= 3)
        self.assertIn("1_year", TIME_HORIZONS)

    def test_schema_version(self):
        self.assertEqual(SCHEMA_VERSION, "6.0")


class TestV6Integration(unittest.TestCase):
    """V6 — integration tests: real CLI with seeded data."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Override store paths to use tmpdir
        self._orig_paths = {}
        for name in ["OUTCOMES_PATH", "EVIDENCE_PATH", "ASSUMPTIONS_PATH",
                      "PREDICTIONS_PATH", "HYPOTHESES_PATH", "ASSETS_PATH",
                      "DOCTRINE_PATH", "PROJECTS_PATH", "OPPORTUNITIES_PATH",
                      "DECISIONS_PATH", "EXPERIMENTS_PATH", "RISKS_PATH",
                      "RELATIONSHIPS_PATH", "PRINCIPLES_PATH", "CONFIG_PATH",
                      "TEMPLATES_PATH"]:
            self._orig_paths[name] = getattr(sys.modules["chief_of_staff_core"], name)
            setattr(sys.modules["chief_of_staff_core"], name, Path(self.tmpdir) / f"test_{name.lower()}.json")
        # Also update the agent module's references
        for name in ["OUTCOMES_PATH", "EVIDENCE_PATH", "ASSUMPTIONS_PATH",
                      "PREDICTIONS_PATH", "HYPOTHESES_PATH", "ASSETS_PATH",
                      "DOCTRINE_PATH", "PROJECTS_PATH", "OPPORTUNITIES_PATH",
                      "DECISIONS_PATH", "EXPERIMENTS_PATH", "RISKS_PATH",
                      "RELATIONSHIPS_PATH", "PRINCIPLES_PATH"]:
            setattr(sys.modules["chief_of_staff_agent"], name,
                    getattr(sys.modules["chief_of_staff_core"], name))

    def tearDown(self):
        for name, orig in self._orig_paths.items():
            setattr(sys.modules["chief_of_staff_core"], name, orig)
        for name, orig in self._orig_paths.items():
            if name != "CONFIG_PATH" and name != "TEMPLATES_PATH":
                setattr(sys.modules["chief_of_staff_agent"], name, orig)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _mock_inputs(self, inputs):
        """Helper to provide mock inputs for interactive functions."""
        return patch('builtins.input', side_effect=inputs)

    def test_add_and_list_outcomes(self):
        with self._mock_inputs(["Publish paper", "Nature submission", "1",
                                 "1", "Accepted", "Draft", "Final", "7", "9"]):
            add_outcome_interactive()
        os = load_outcomes()
        self.assertEqual(len(os), 1)
        self.assertEqual(os[0].name, "Publish paper")

    def test_add_and_list_evidence(self):
        with self._mock_inputs(["Paper accepted", "1", "research_publication",
                                 "Review process works", "Slow review hurts", "8", "7", "test note"]):
            add_evidence_interactive()
        es = load_evidence()
        self.assertEqual(len(es), 1)
        self.assertEqual(es[0].title, "Paper accepted")

    def test_add_and_list_assumptions(self):
        with self._mock_inputs(["Reviewers will be fair", "1", "7", "8",
                                 "Evidence of bias"]):
            add_assumption_interactive()
        ass = load_assumptions()
        self.assertEqual(len(ass), 1)
        self.assertEqual(ass[0].confidence, 7)

    def test_add_and_list_predictions(self):
        with self._mock_inputs(["Grant will be funded", "1", "70", "2026-12-31"]):
            add_prediction_interactive()
        ps = load_predictions()
        self.assertEqual(len(ps), 1)
        self.assertEqual(ps[0].probability, 70)

    def test_add_and_list_hypotheses(self):
        with self._mock_inputs(["Higher-tier journal = more citations",
                                 "1", "7", "Submit to 3 journals and compare"]):
            add_hypothesis_interactive()
        hs = load_hypotheses()
        self.assertEqual(len(hs), 1)
        self.assertEqual(hs[0].status, "untested")

    def test_add_and_list_assets(self):
        with self._mock_inputs(["Grant template v1", "1", "1",
                                 "Template for NSF", "5", "9", "low", ""]):
            add_asset_interactive()
        ass = load_assets()
        self.assertEqual(len(ass), 1)
        self.assertEqual(ass[0].reuse_count, 5)

    def test_add_and_list_doctrine(self):
        with self._mock_inputs(["Never schedule deep work after 3pm",
                                 "Cognitive fatigue", "Personal experience", "1"]):
            add_doctrine_interactive()
        ds = load_doctrine()
        self.assertEqual(len(ds), 1)

    def test_bias_review_with_data(self):
        # Add some decisions and tasks to trigger biases
        d = Decision(decision_id="1", date=today_str(), title="Test decision",
                     clarity_of_objective=2, quality_of_options=4,
                     evidence_quality=5, opportunity_cost_awareness=3,
                     risk_awareness=6, outcome_quality=5)
        save_decisions([d])
        r = bias_detection([], [d], [], [])
        self.assertIn("biases", r)

    def test_scorecard_with_data(self):
        os = [Outcome(name="Publish paper", current_status="draft",
                      desired_status="published", confidence_level=7)]
        r = strategic_scorecard([], os, [], [], [])
        self.assertEqual(r["dimensions"][2]["score"], 8)

    def test_kill_list_with_data(self):
        t = Task("Old admin", impact=1, urgency=1, strategic_value=1,
                 compounding_effect=1, goal_alignment=1, deadline_pressure=1,
                 energy_fit=5, opportunity_cost=8, focus_requirement=1,
                 estimated_minutes=60, strategic_goal="admin_maintenance")
        t = score_task(t)
        d = Decision(decision_id="1", date="2020-01-01", title="Old decision",
                     review_date="2020-06-01")
        r = kill_list_recommendation([t], [], [d], [])
        self.assertTrue(any("Old admin" in k["target"] for k in r["kill_items"]))


if __name__ == "__main__":
    unittest.main()


# ======================================================================
# V7 TESTS
# ======================================================================
class TestV7Dataclasses(unittest.TestCase):
    """V7 — dataclass instantiation."""

    def test_strategic_identity(self):
        si = StrategicIdentity(name="World Class Researcher", role="World-Class Researcher",
                               statement="Become a world-class organic electronics researcher.")
        self.assertEqual(si.role, "World-Class Researcher")

    def test_strategic_capital(self):
        sc = StrategicCapital(capital_type="intellectual_capital", name="Domain Expertise",
                              current_score=8)
        self.assertEqual(sc.current_score, 8)

    def test_rhythm(self):
        r = Rhythm(name="Daily priorities", cadence="daily",
                   description="Choose top 1-3 tasks.")
        self.assertEqual(r.cadence, "daily")

    def test_key_result(self):
        kr = KeyResult(description="Submit 3 papers", target_value=3, current_value=1)
        self.assertEqual(kr.target_value, 3)

    def test_okr(self):
        o = OKR(title="Publish more", strategic_goal="research_publication",
                period="quarterly", confidence=7)
        self.assertEqual(o.confidence, 7)

    def test_audit_entry(self):
        ae = AuditEntry(action_type="create", entity_type="project",
                        entity_id="abc123", summary="Created project")
        self.assertEqual(ae.entity_type, "project")


class TestV7ScenarioSimulator(unittest.TestCase):
    """V7 — scenario simulator."""

    def test_simulator_30_day(self):
        data = {"config": DEFAULT_CONFIG, "records": [], "projects": [],
                "risks": [], "outcomes": [], "opportunities": []}
        r = scenario_simulator(30, data)
        self.assertEqual(r["horizon"], 30)
        self.assertEqual(len(r["scenarios"]), 8)
        self.assertIsNotNone(r["best"])

    def test_simulator_90_day(self):
        data = {"config": DEFAULT_CONFIG, "records": [], "projects": [],
                "risks": [], "outcomes": [], "opportunities": []}
        r = scenario_simulator(90, data)
        self.assertEqual(len(r["scenarios"]), 8)
        self.assertGreater(r["best"].scenario_score, 0)

    def test_simulator_365_day(self):
        data = {"config": DEFAULT_CONFIG, "records": [], "projects": [],
                "risks": [], "outcomes": [], "opportunities": []}
        r = scenario_simulator(365, data)
        self.assertEqual(r["horizon"], 365)

    def test_best_path_has_score(self):
        data = {"config": DEFAULT_CONFIG, "records": [], "projects": [],
                "risks": [], "outcomes": [], "opportunities": []}
        r = scenario_simulator(90, data)
        best = r["best"]
        self.assertGreater(best.scenario_score, 0)
        self.assertTrue(best.path_name)

    def test_admin_reactive_worst(self):
        data = {"config": DEFAULT_CONFIG, "records": [], "projects": [],
                "risks": [], "outcomes": [], "opportunities": []}
        r = scenario_simulator(90, data)
        scores = {s.path_name: s.scenario_score for s in r["scenarios"]}
        admin_score = [v for k, v in scores.items() if "Admin" in k][0]
        best_score = r["best"].scenario_score
        self.assertLess(admin_score, best_score)


class TestV7TradeoffEngine(unittest.TestCase):
    """V7 — trade-off engine."""

    def test_basic_comparison(self):
        a = {"label": "Write grant", "expected_value": 9, "risk": 4,
             "strategic_goal_served_score": 9, "opportunity_cost": 2,
             "evidence_strength": 7, "reversibility_class": "two_way_door",
             "uncertainty": "low", "hidden_cost": ""}
        b = {"label": "Write paper", "expected_value": 7, "risk": 3,
             "strategic_goal_served_score": 8, "opportunity_cost": 3,
             "evidence_strength": 6, "reversibility_class": "two_way_door",
             "uncertainty": "medium", "hidden_cost": ""}
        r = tradeoff_engine(a, b)
        self.assertIn("options", r)
        self.assertEqual(len(r["options"]), 2)
        self.assertIn("recommendation", r)

    def test_three_way_comparison(self):
        a = {"label": "A", "expected_value": 8, "risk": 3,
             "strategic_goal_served_score": 7, "opportunity_cost": 2,
             "evidence_strength": 5, "reversibility_class": "two_way_door",
             "uncertainty": "low", "hidden_cost": ""}
        b = {"label": "B", "expected_value": 6, "risk": 5,
             "strategic_goal_served_score": 6, "opportunity_cost": 3,
             "evidence_strength": 5, "reversibility_class": "one_way_door",
             "uncertainty": "medium", "hidden_cost": ""}
        c = {"label": "C", "expected_value": 9, "risk": 7,
             "strategic_goal_served_score": 8, "opportunity_cost": 4,
             "evidence_strength": 3, "reversibility_class": "experiment_first",
             "uncertainty": "high", "hidden_cost": "Time away from research"}
        r = tradeoff_engine(a, b, c)
        self.assertEqual(len(r["options"]), 3)


class TestV7OperatingRhythm(unittest.TestCase):
    """V7 — operating rhythm."""

    def test_default_rhythms_created(self):
        rs = load_rhythms()
        self.assertGreaterEqual(len(rs), 8)

    def test_rhythm_review(self):
        rs = load_rhythms()
        r = rhythm_review(rs)
        self.assertIn("total", r)
        self.assertIn("overdue", r)


class TestV7IdentityReview(unittest.TestCase):
    """V7 — identity alignment review."""

    def test_identity_review_empty(self):
        r = identity_review([], [], [], [])
        self.assertIn("message", r)

    def test_identity_review_detects_drift(self):
        ids = [StrategicIdentity(name="Researcher", role="World-Class Researcher",
                                  statement="Become a researcher.",
                                  last_reviewed=today_str())]
        records = []
        r = identity_review(ids, records, [], [])
        self.assertEqual(len(r["identities"]), 1)
        self.assertEqual(r["identities"][0]["verdict"], "Aligned")

    def test_identity_review_with_records(self):
        ids = [StrategicIdentity(name="Grant Winner", role="Grant-Winning PI",
                                  statement="Become a grant-winning PI.",
                                  last_reviewed=today_str())]
        record = {"portfolio": {"by_goal": {g: {"minutes": 100 if g == "grant_funding" else 10} for g in STRATEGIC_GOALS}}}
        r = identity_review(ids, [record], [], [])
        self.assertEqual(r["identities"][0]["verdict"], "Aligned")


class TestV7CapitalModel(unittest.TestCase):
    """V7 — strategic capital."""

    def test_capital_review_empty(self):
        r = capital_review([])
        self.assertIn("message", r)

    def test_capital_review(self):
        cs = [StrategicCapital(name="Domain Expertise", capital_type="intellectual_capital",
                                current_score=8),
              StrategicCapital(name="Industry Contacts", capital_type="relationship_capital",
                                current_score=2, activities_that_increase=["Attend conferences"])]
        r = capital_review(cs)
        self.assertEqual(r["growing"], 1)
        self.assertEqual(r["decaying"], 1)
        self.assertGreater(len(r["recommendations"]), 0)


class TestV7PlanGenerator(unittest.TestCase):
    """V7 — plan generation."""

    def test_plan_30(self):
        data = {"config": DEFAULT_CONFIG, "records": [], "projects": [],
                "opportunities": [], "risks": [], "assets": [], "outcomes": [],
                "decisions": [], "relationships": [], "hypotheses": [],
                "experiments": [], "predictions": []}
        r = plan_generator(30, data)
        self.assertEqual(r["horizon"], 30)
        self.assertIn("strategic_thesis", r)

    def test_plan_90(self):
        data = {"config": DEFAULT_CONFIG, "records": [], "projects": [],
                "opportunities": [], "risks": [], "assets": [], "outcomes": [],
                "decisions": [], "relationships": [], "hypotheses": [],
                "experiments": [], "predictions": []}
        r = plan_generator(90, data)
        self.assertEqual(r["horizon"], 90)

    def test_plan_365(self):
        data = {"config": DEFAULT_CONFIG, "records": [], "projects": [],
                "opportunities": [], "risks": [], "assets": [], "outcomes": [],
                "decisions": [], "relationships": [], "hypotheses": [],
                "experiments": [], "predictions": []}
        r = plan_generator(365, data)
        self.assertEqual(r["horizon"], 365)


class TestV7Backcasting(unittest.TestCase):
    """V7 — backcasting."""

    def test_backcast_generator(self):
        r = backcast_generator("Secure major research grant", "2027-05-22",
                               "Career milestone", "Grant awarded")
        self.assertIn("desired_outcome", r)
        self.assertGreater(len(r["milestones"]), 2)
        self.assertIn("first_next_action", r)


class TestV7OKR(unittest.TestCase):
    """V7 — OKR system."""

    def test_okr_review_empty(self):
        r = okr_review([])
        self.assertIn("message", r)

    def test_okr_review_with_krs(self):
        kr = KeyResult(kr_id="kr1", description="Submit 3 papers", target_value=3,
                       current_value=1, progress_percent=33, status="on_track")
        o = OKR(title="Publish more", strategic_goal="research_publication",
                period="quarterly", key_results=[kr])
        r = okr_review([o])
        self.assertEqual(r["total"], 1)
        self.assertEqual(len(r["objectives"]), 1)


class TestV7Rebalance(unittest.TestCase):
    """V7 — portfolio rebalance."""

    def test_rebalance_empty(self):
        r = rebalance_engine([], DEFAULT_CONFIG, [], [], [])
        self.assertIn("adjustments", r)

    def test_rebalance_with_data(self):
        record = {"portfolio": {"by_goal": {g: {"minutes": 50 if g == "admin_maintenance" else 10} for g in STRATEGIC_GOALS}}}
        r = rebalance_engine([record], DEFAULT_CONFIG, [], [], [])
        self.assertGreater(len(r["adjustments"]), 0)


class TestV7Audit(unittest.TestCase):
    """V7 — audit log."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self._orig_audit_path = AUDIT_PATH
        # Use temp path
        import chief_of_staff_core as core
        core.AUDIT_PATH = Path(self.tmpdir) / "test_audit.json"

    def tearDown(self):
        import chief_of_staff_core as core
        core.AUDIT_PATH = self._orig_audit_path
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_record_audit_event(self):
        record_audit_event("create", "project", "test1", "Test creation")
        log = load_audit_log()
        self.assertGreaterEqual(len(log), 1)

    def test_audit_with_hashes(self):
        record_audit_event("update", "decision", "test2", "Updated decision",
                           before={"old": "value"}, after={"new": "value"})
        log = load_audit_log()
        last = log[-1]
        self.assertTrue(last.get("before_hash") or last.get("after_hash"))


class TestV7Integrity(unittest.TestCase):
    """V7 — data integrity."""

    def test_integrity_check(self):
        r = integrity_check()
        self.assertIn("total_issues", r)

    def test_repair_integrity_safe(self):
        r = repair_integrity()
        self.assertIn("total_repairs", r)


class TestV7Search(unittest.TestCase):
    """V7 — local search."""

    def test_search_no_results(self):
        r = local_search("xyznonexistent12345")
        self.assertEqual(r["total"], 0)

    def test_search_fuzzy(self):
        r = local_search("grant")
        self.assertIn("total", r)


class TestV7ReportPack(unittest.TestCase):
    """V7 — report pack."""

    def test_report_pack_generation(self):
        r = generate_report_pack("reports/test_pack")
        self.assertGreater(r["count"], 0)
        # Cleanup
        import shutil
        shutil.rmtree("reports/test_pack", ignore_errors=True)


class TestV7AICouncil(unittest.TestCase):
    """V7 — AI council prompt (no API)."""

    def test_council_prompt_generated(self):
        prompt = ai_council_prompt()
        self.assertIn("AI STRATEGIC COUNCIL", prompt)
        self.assertIn("CHIEF OF STAFF", prompt)
        self.assertIn("PRINCIPAL INVESTIGATOR", prompt)

    def test_noop_ai_provider(self):
        provider = NoOpAIProvider()
        result = provider.generate("test prompt")
        self.assertEqual(result, "test prompt")

    def test_ai_provider_abstract(self):
        provider = AIProvider()
        with self.assertRaises(NotImplementedError):
            provider.generate("test")


class TestV7Migration(unittest.TestCase):
    """V7 — v6 to v7 migration."""

    def setUp(self):
        import tempfile
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_migrate_v6_to_v7_adds_metadata(self):
        data = {"schema_version": "6.0", "records": [{"id": "1", "name": "test"}]}
        result = migrate_v6_to_v7(data)
        self.assertIn("schema_version", result)
        self.assertEqual(result["schema_version"], CURRENT_SCHEMA_VERSION)
        self.assertIn("records", result)

    def test_migration_preserves_records(self):
        data = {"records": [{"id": "1", "name": "test"}, {"id": "2", "name": "test2"}]}
        result = migrate_v6_to_v7(data)
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["records"][0]["name"], "test")

    def test_get_store_version(self):
        import json
        from pathlib import Path
        p = Path(self.tmpdir) / "test.json"
        p.write_text(json.dumps({"schema_version": "6.0", "records": []}))
        self.assertEqual(get_store_version(p), "6.0")

    def test_get_store_version_missing(self):
        from pathlib import Path
        self.assertIsNone(get_store_version(Path(self.tmpdir) / "nonexistent.json"))


# ======================================================================
# V8 TESTS
# ======================================================================
class TestV8Workflows(unittest.TestCase):
    """V8 — execution workflows."""

    def test_workflow_creation(self):
        wfs = load_workflows()
        self.assertGreaterEqual(len(wfs), 9)

    def test_run_workflow_generates_steps(self):
        r = run_workflow("wf_grant_concept")
        self.assertIsNotNone(r)
        self.assertIn("steps", r)
        self.assertGreater(len(r["steps"]), 0)

    def test_workflow_review(self):
        r = workflow_review()
        self.assertIn("total", r)
        self.assertIn("by_category", r)


class TestV8SOP(unittest.TestCase):
    """V8 — SOP generator."""

    def test_sop_generation_grant(self):
        r = generate_sop("grant_concept_note")
        self.assertIsNotNone(r["sop"])
        self.assertEqual(r["sop"]["strategic_goal"], "grant_funding")

    def test_sop_templates_available(self):
        r = generate_sop()
        self.assertIn("templates", r)
        self.assertGreater(len(r["templates"]), 5)


class TestV8ProjectPlaybook(unittest.TestCase):
    """V8 — project playbook."""

    def test_playbook_generation(self):
        project = Project(name="Test Project", strategic_goal="grant_funding",
                          project_id="test123", status="active")
        r = project_playbook(project, [], [], [], [], [])
        self.assertEqual(r["project_name"], "Test Project")
        self.assertEqual(r["strategic_goal"], "grant_funding")
        self.assertIn("first_5_actions", r)


class TestV8ExecutionQueue(unittest.TestCase):
    """V8 — execution queue."""

    def tearDown(self):
        qs = load_queue()
        save_queue([q for q in qs if not q.title.startswith("_test_")])

    def test_queue_add_and_list(self):
        q = add_to_queue("_test_ Write grant", "task", "test1", "grant_funding", 8, 60)
        qs = load_queue()
        self.assertTrue(any(x.title.startswith("_test_") for x in qs))

    def test_queue_complete(self):
        q = add_to_queue("_test_ Complete me", "task", "test2", "", 5, 30)
        qs = load_queue()
        for qi in qs:
            if qi.queue_id == q.queue_id:
                qi.status = "completed"; break
        save_queue(qs)
        # Verify it sticks
        qs2 = load_queue()
        completed = [x for x in qs2 if x.queue_id == q.queue_id]
        self.assertTrue(completed)

    def test_queue_review(self):
        r = queue_review()
        self.assertIn("active", r)
        self.assertIn("top_3", r)


class TestV8NextActionCompiler(unittest.TestCase):
    """V8 — next-action compiler."""

    def test_detects_missing_actions(self):
        r = compile_next_actions([], [], [], [], [], [], [], [], [])
        self.assertIn("total_missing", r)


class TestV8KnowledgeGraph(unittest.TestCase):
    """V8 — knowledge graph."""

    def test_graph_created(self):
        r = build_graph()
        self.assertIn("nodes", r)

    def test_graph_review(self):
        r = graph_review()
        self.assertIn("total_nodes", r)
        self.assertIn("total_edges", r)


class TestV8ExecutionPacket(unittest.TestCase):
    """V8 — execution packet."""

    def test_packet_not_found(self):
        r = execution_packet("nonexistent123456")
        self.assertIsNone(r)


class TestV8DraftPrompts(unittest.TestCase):
    """V8 — draft prompts."""

    def test_grant_prompt(self):
        p = draft_prompt("grant")
        self.assertIn("GRANT", p.upper())
        self.assertIn("AI", p)

    def test_industry_email_prompt(self):
        p = draft_prompt("industry-email")
        self.assertIn("INDUSTRY", p.upper())

    def test_linkedin_prompt(self):
        p = draft_prompt("linkedin")
        self.assertIn("LINKEDIN", p.upper())

    def test_no_api_call(self):
        for t in DRAFT_PROMPT_TYPES:
            p = draft_prompt(t)
            self.assertNotIn("http", p.lower())


class TestV8MeetingPrep(unittest.TestCase):
    """V8 — meeting preparation."""

    def test_meeting_preparation(self):
        r = prepare_meeting("Research Sync", "Prof. Smith",
                            "research_collaboration", "grant_funding",
                            "Agree on collaboration scope")
        self.assertEqual(r["title"], "Research Sync")
        self.assertIn("questions_to_ask", r)


class TestV8FollowupEngine(unittest.TestCase):
    """V8 — follow-up engine."""

    def test_followup_empty(self):
        r = followup_review([], [])
        self.assertEqual(r["total"], 0)


class TestV8SprintPlanner(unittest.TestCase):
    """V8 — sprint planner."""

    def test_sprint_plan_generation(self):
        r = sprint_planner([], [], [], [], [], {}, [])
        self.assertIn("theme", r)
        self.assertIn("top_outcomes", r)


class TestV8StartupShutdown(unittest.TestCase):
    """V8 — startup/shutdown."""

    def test_startup_output(self):
        r = startup_ritual([], [], [])
        self.assertIn("top_objective", r)
        self.assertIn("first_30_minutes", r)

    # shutdown_ritual is interactive so we skip it in automated tests


class TestV8AssetRecommender(unittest.TestCase):
    """V8 — asset creation recommender."""

    def test_asset_creation_recommendation_with_workflows(self):
        wfs = load_workflows()
        assets = load_assets()
        r = asset_opportunities([], [], assets, wfs)
        self.assertIn("recommendations", r)
        self.assertGreaterEqual(r["total"], 0)


class TestV8Capture(unittest.TestCase):
    """V8 — knowledge capture."""

    def test_capture_note_creation(self):
        c = add_capture_interactive_core("insight", "Test insight",
                                          "This is a test insight.",
                                          "research_publication", "", "test,v8")
        self.assertEqual(c.title, "Test insight")
        self.assertEqual(c.type, "insight")
        self.assertIn("test", c.tags)


class TestV8ContextPrompt(unittest.TestCase):
    """V8 — context prompt builder."""

    def test_context_prompt_builder(self):
        r = context_prompt("grant")
        self.assertIn("CONTEXT FROM YOUR STRATEGIC SYSTEM", r)
        self.assertIn("grant", r.lower())

    def test_redaction_masks_email(self):
        text = "Contact john.doe@university.edu for details."
        from chief_of_staff_core import _redact_sensitive
        result = _redact_sensitive(text)
        self.assertIn("EMAIL-REDACTED", result)
        self.assertNotIn("john.doe", result)


class TestV8RoleDashboard(unittest.TestCase):
    """V8 — role dashboards."""

    def test_role_dashboard_researcher(self):
        r = role_dashboard("researcher")
        self.assertEqual(r["role"], "researcher")


class TestV8OnePage(unittest.TestCase):
    """V8 — one-page mode."""

    def test_one_page_mode(self):
        r = one_page()
        self.assertIn("today", r)
        self.assertIn("next_best_move", r)
