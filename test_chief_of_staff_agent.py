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
