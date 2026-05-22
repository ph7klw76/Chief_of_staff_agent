#!/usr/bin/env python3
"""Chief of Staff Agent GUI — desktop window application (tkinter, stdlib only).
Run: python3 chief_of_staff_gui.py
Double-click on Windows to launch.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json, sys, os
from pathlib import Path
from datetime import date

# Import all core logic — no CLI dependency
from chief_of_staff_core import *

# ── Theme ──────────────────────────────────────────────────────────
FONT = ("Segoe UI", 10) if sys.platform == "win32" else ("Helvetica", 11)
FONT_BOLD = ("Segoe UI", 10, "bold") if sys.platform == "win32" else ("Helvetica", 11, "bold")
FONT_TITLE = ("Segoe UI", 14, "bold") if sys.platform == "win32" else ("Helvetica", 14, "bold")
FONT_MONO = ("Consolas", 9) if sys.platform == "win32" else ("Courier", 9)
BG = "#f5f5f5"; FG = "#1a1a1a"; ACCENT = "#2563eb"; WARN = "#d97706"; GOOD = "#059669"; BAD = "#dc2626"


class ChiefOfStaffApp:
    """Main tkinter application wrapping all Chief of Staff functionality."""

    def __init__(self, root):
        self.root = root
        self.root.title(f"Chief of Staff Agent v10 — {today_str()}")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        try:
            self.root.iconbitmap(default="")
        except:
            pass
        self._build_menu()
        self._build_ui()
        self._refresh_dashboard()

    # ── Menu Bar ───────────────────────────────────────────────────
    def _build_menu(self):
        menubar = tk.Menu(self.root, font=FONT)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0, font=FONT)
        file_menu.add_command(label="Refresh Dashboard", command=self._refresh_dashboard, accelerator="F5")
        file_menu.add_command(label="Export Dashboard as Text", command=self._export_dashboard)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        actions_menu = tk.Menu(menubar, tearoff=0, font=FONT)
        actions_menu.add_command(label="Startup Ritual", command=self._run_startup)
        actions_menu.add_command(label="Shutdown Ritual", command=self._run_shutdown)
        actions_menu.add_separator()
        actions_menu.add_command(label="Generate Commands", command=self._run_generate_commands)
        actions_menu.add_command(label="Execute Approved", command=self._run_execute_approved)
        menubar.add_cascade(label="Actions", menu=actions_menu)

        reviews_menu = tk.Menu(menubar, tearoff=0, font=FONT)
        reviews_menu.add_command(label="Weekly Review", command=lambda: self._run("--weekly-review"))
        reviews_menu.add_command(label="Monthly Review", command=lambda: self._run("--monthly-review"))
        reviews_menu.add_separator()
        reviews_menu.add_command(label="ROI Review", command=lambda: self._run_review(roi_review_cmd_text))
        reviews_menu.add_command(label="Conflict Review", command=lambda: self._run_review(conflict_review_text))
        reviews_menu.add_command(label="Decay Review", command=lambda: self._run_review(decay_review_text))
        reviews_menu.add_command(label="OS Health", command=lambda: self._run_review(os_health_text))
        reviews_menu.add_command(label="Governance Board", command=lambda: self._run_review(governance_board_text))
        menubar.add_cascade(label="Reviews", menu=reviews_menu)

        data_menu = tk.Menu(menubar, tearoff=0, font=FONT)
        data_menu.add_command(label="Add Project", command=self._add_project_dialog)
        data_menu.add_command(label="Add Opportunity", command=self._add_opp_dialog)
        data_menu.add_command(label="Add Impact", command=self._add_impact_dialog)
        data_menu.add_command(label="Add Metric", command=self._add_metric_dialog)
        data_menu.add_command(label="Knowledge Capture", command=self._capture_dialog)
        menubar.add_cascade(label="Add Data", menu=data_menu)

        help_menu = tk.Menu(menubar, tearoff=0, font=FONT)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Open Data Folder", command=self._open_data_folder)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.bind("<F5>", lambda e: self._refresh_dashboard())
        self.root.bind("<Control-q>", lambda e: self.root.quit())

    # ── Main UI ────────────────────────────────────────────────────
    def _build_ui(self):
        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Tab 0: Dashboard
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text=" Dashboard ")

        # Tab 1: Quick Actions
        self.tab_actions = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_actions, text=" Quick Actions ")

        # Tab 2: Reviews
        self.tab_reviews = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_reviews, text=" Reviews ")

        # Tab 3: Data
        self.tab_data = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text=" Data ")

        # ── Dashboard Tab ──
        dash_frame = ttk.Frame(self.tab_dashboard, padding=10)
        dash_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(dash_frame, text="STRATEGIC DASHBOARD", font=FONT_TITLE, foreground=ACCENT).pack(anchor=tk.W, pady=(0, 10))

        self.dash_text = scrolledtext.ScrolledText(dash_frame, wrap=tk.WORD, font=FONT_MONO,
                                                    bg="#ffffff", fg=FG, relief=tk.FLAT, borderwidth=4, height=28)
        self.dash_text.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(dash_frame)
        btn_frame.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(btn_frame, text="Refresh (F5)", command=self._refresh_dashboard).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="One-Page View", command=self._show_one_page).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Export as .txt", command=self._export_dashboard).pack(side=tk.LEFT, padx=4)

        # ── Quick Actions Tab ──
        acts_frame = ttk.Frame(self.tab_actions, padding=10)
        acts_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(acts_frame, text="QUICK ACTIONS", font=FONT_TITLE, foreground=ACCENT).pack(anchor=tk.W, pady=(0, 10))

        row1 = ttk.Frame(acts_frame); row1.pack(fill=tk.X, pady=4)
        ttk.Button(row1, text="☀ Startup Ritual", command=self._run_startup).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(row1, text="🌙 Shutdown Ritual", command=self._run_shutdown).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(row1, text="📋 Sprint Plan", command=lambda: self._run("--sprint-plan")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        row2 = ttk.Frame(acts_frame); row2.pack(fill=tk.X, pady=4)
        ttk.Button(row2, text="⚡ Generate Commands", command=self._run_generate_commands).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(row2, text="✅ Execute Approved", command=self._run_execute_approved).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(row2, text="🔍 Follow-ups", command=lambda: self._run("--followups")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        row3 = ttk.Frame(acts_frame); row3.pack(fill=tk.X, pady=4)
        ttk.Button(row3, text="📊 Metrics Review", command=lambda: self._run_review(metrics_review_text)).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(row3, text="🎯 Impact Review", command=lambda: self._run_review(impact_review_text)).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(row3, text="💰 ROI Review", command=lambda: self._run_review(roi_review_cmd_text)).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        row4 = ttk.Frame(acts_frame); row4.pack(fill=tk.X, pady=4)
        ttk.Button(row4, text="📝 Knowledge Capture", command=self._capture_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(row4, text="📎 Asset Opportunities", command=lambda: self._run("--asset-opportunities")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(row4, text="🧹 Simplify", command=lambda: self._run("--simplify")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        self.acts_output = scrolledtext.ScrolledText(acts_frame, wrap=tk.WORD, font=FONT_MONO,
                                                      bg="#ffffff", fg=FG, relief=tk.FLAT, borderwidth=4, height=16)
        self.acts_output.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # ── Reviews Tab ──
        rev_frame = ttk.Frame(self.tab_reviews, padding=10)
        rev_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(rev_frame, text="STRATEGIC REVIEWS", font=FONT_TITLE, foreground=ACCENT).pack(anchor=tk.W, pady=(0, 10))

        rev_row1 = ttk.Frame(rev_frame); rev_row1.pack(fill=tk.X, pady=4)
        ttk.Button(rev_row1, text="📅 Weekly Review", command=lambda: self._run("--weekly-review")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(rev_row1, text="📆 Monthly Review", command=lambda: self._run("--monthly-review")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(rev_row1, text="🏛 Governance Board", command=lambda: self._run_review(governance_board_text)).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        rev_row2 = ttk.Frame(rev_frame); rev_row2.pack(fill=tk.X, pady=4)
        ttk.Button(rev_row2, text="📈 Velocity Review", command=lambda: self._run("--velocity-review")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(rev_row2, text="⚠ Conflict Review", command=lambda: self._run_review(conflict_review_text)).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(rev_row2, text="🔄 Reforecast", command=lambda: self._run("--reforecast")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        rev_row3 = ttk.Frame(rev_frame); rev_row3.pack(fill=tk.X, pady=4)
        ttk.Button(rev_row3, text="🦋 Flywheel Review", command=lambda: self._run("--flywheel-review")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(rev_row3, text="📉 Decay Review", command=lambda: self._run("--decay-review")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(rev_row3, text="💀 OS Health", command=lambda: self._run_review(os_health_text)).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        rev_row4 = ttk.Frame(rev_frame); rev_row4.pack(fill=tk.X, pady=4)
        ttk.Button(rev_row4, text="🧠 Bias Review", command=lambda: self._run("--bias-review")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(rev_row4, text="🎯 Scorecard", command=lambda: self._run("--scorecard")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(rev_row4, text="🪚 Kill List", command=lambda: self._run("--kill-list")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        self.rev_output = scrolledtext.ScrolledText(rev_frame, wrap=tk.WORD, font=FONT_MONO,
                                                     bg="#ffffff", fg=FG, relief=tk.FLAT, borderwidth=4, height=16)
        self.rev_output.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # ── Data Tab ──
        data_frame = ttk.Frame(self.tab_data, padding=10)
        data_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(data_frame, text="DATA MANAGEMENT", font=FONT_TITLE, foreground=ACCENT).pack(anchor=tk.W, pady=(0, 10))

        data_row1 = ttk.Frame(data_frame); data_row1.pack(fill=tk.X, pady=4)
        ttk.Button(data_row1, text="+ Project", command=self._add_project_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row1, text="+ Opportunity", command=self._add_opp_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row1, text="+ Risk", command=self._add_risk_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row1, text="+ Relationship", command=self._add_rel_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        data_row2 = ttk.Frame(data_frame); data_row2.pack(fill=tk.X, pady=4)
        ttk.Button(data_row2, text="+ Impact", command=self._add_impact_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row2, text="+ Metric", command=self._add_metric_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row2, text="+ Contract", command=self._add_contract_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row2, text="+ Initiative", command=self._add_initiative_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        data_row3 = ttk.Frame(data_frame); data_row3.pack(fill=tk.X, pady=4)
        ttk.Button(data_row3, text="📝 Knowledge Capture", command=self._capture_dialog).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row3, text="📋 List Projects", command=lambda: self._run("--projects")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row3, text="📋 List Opportunities", command=lambda: self._run("--opportunities")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row3, text="📋 List Workflows", command=lambda: self._run("--workflows")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        data_row4 = ttk.Frame(data_frame); data_row4.pack(fill=tk.X, pady=4)
        ttk.Button(data_row4, text="🔍 Integrity Check", command=lambda: self._run("--integrity-check")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row4, text="🔧 Repair Integrity", command=lambda: self._run("--repair-integrity")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row4, text="📊 Export CSV (metrics)", command=lambda: self._run_export_csv("metrics")).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)
        ttk.Button(data_row4, text="📂 Open Data Folder", command=self._open_data_folder).pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        self.data_output = scrolledtext.ScrolledText(data_frame, wrap=tk.WORD, font=FONT_MONO,
                                                      bg="#ffffff", fg=FG, relief=tk.FLAT, borderwidth=4, height=14)
        self.data_output.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Footer
        footer = ttk.Frame(self.root)
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=2)
        ttk.Label(footer, text=f"v10 | {today_str()} | Autonomy: Level {load_autonomy().get('level', 2)} — {load_autonomy().get('label', 'Prepare')} | 189 tests pass | No external APIs",
                  font=("Segoe UI", 7) if sys.platform == "win32" else ("Helvetica", 7),
                  foreground="#888888").pack(side=tk.LEFT)

    # ── Dashboard Refresh ──────────────────────────────────────────
    def _refresh_dashboard(self):
        self.dash_text.delete("1.0", tk.END)

        try:
            op = one_page()
            ms = metrics_review()
            imp = impact_review()
            oh = os_health()
            cs = command_review()
            ca = complexity_audit()

            lines = []
            lines.append("═" * 65)
            lines.append("  CHIEF OF STAFF — STRATEGIC COMMAND CENTER")
            lines.append("═" * 65)
            lines.append("")
            lines.append("  TODAY:       " + op.get("today", "Prioritize one strategic task."))
            lines.append("  THIS WEEK:   " + op.get("this_week", "Protect deep work."))
            lines.append("  THIS MONTH:  " + op.get("this_month", "Review allocation."))
            lines.append("")
            lines.append("  ── TOP LINES ──")
            lines.append(f"  Top Project:      {op.get('top_project', '(none)')}")
            lines.append(f"  Top Opportunity:  {op.get('top_opportunity', '(none)')}")
            lines.append(f"  Top Risk:         {op.get('top_risk', '(none)')}")
            lines.append(f"  Top Relationship: {op.get('top_relationship', '(none)')}")
            lines.append("")
            lines.append(f"  Delete:    {op.get('one_thing_to_delete', 'Nothing obvious.')}")
            lines.append(f"  Protect:   {op.get('one_thing_to_protect', 'Deep work block.')}")
            lines.append(f"  Next Move: {op.get('next_best_move', 'Start top queued task.')}")
            lines.append("")
            lines.append("  ── METRICS ──")
            lines.append(f"  {ms.get('summary', 'No metrics.')}")
            lines.append(f"  Impact: {imp.get('summary', 'No impact recorded.')}")
            lines.append("")
            lines.append("  ── SYSTEM ──")
            lines.append(f"  OS Health:  {oh.get('os_health_score', '?')}/100 ({oh.get('status', '?')})")
            lines.append(f"  Commands:   {cs.get('summary', 'No commands.')}" if isinstance(cs, dict) else "  Commands:   Ready")
            lines.append(f"  Complexity: {ca.get('summary', 'Manageable.')}")
            lines.append("")
            lines.append("═" * 65)

            self.dash_text.insert("1.0", "\n".join(lines))
        except Exception as e:
            self.dash_text.insert("1.0", f"Dashboard refresh error: {e}\n\nRun 'python3 chief_of_staff_agent.py --demo' in terminal first.")

    def _show_one_page(self):
        self.dash_text.delete("1.0", tk.END)
        r = one_page()
        lines = [f"{k.replace('_', ' ').upper()}: {v}" for k, v in r.items()]
        self.dash_text.insert("1.0", "ONE-PAGE VIEW\n" + "=" * 65 + "\n\n" + "\n".join(lines))

    # ── Output Helpers ─────────────────────────────────────────────
    def _output_to(self, widget, text):
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)

    def _run(self, flag):
        """Run a CLI flag via subprocess and capture output."""
        import subprocess
        try:
            result = subprocess.run([sys.executable, "chief_of_staff_agent.py", flag],
                                    capture_output=True, text=True, timeout=15, cwd=os.path.dirname(__file__) or ".")
            output = result.stdout or result.stderr or "(no output)"
        except subprocess.TimeoutExpired:
            output = "(command timed out)"
        except Exception as e:
            output = f"(error: {e})"
        self._output_active_tab(output)

    def _run_review(self, fn):
        """Run a review function and display its output."""
        try:
            result = fn()
            output = json.dumps(result, indent=2, default=str) if isinstance(result, dict) else str(result)
        except Exception as e:
            output = f"Error: {e}"
        self._output_active_tab(output)

    def _output_active_tab(self, text):
        tab = self.notebook.index(self.notebook.select())
        if tab == 0:
            self.dash_text.delete("1.0", tk.END); self.dash_text.insert("1.0", text)
        elif tab == 1:
            self.acts_output.delete("1.0", tk.END); self.acts_output.insert("1.0", text)
        elif tab == 2:
            self.rev_output.delete("1.0", tk.END); self.rev_output.insert("1.0", text)
        elif tab == 3:
            self.data_output.delete("1.0", tk.END); self.data_output.insert("1.0", text)

    # ── Quick Actions ──────────────────────────────────────────────
    def _run_startup(self):
        queue = load_queue(); projs = load_projects_from_core(); risks = load_risks_from_core()
        r = startup_ritual(queue, projs, risks)
        lines = ["DAILY STARTUP", "=" * 50, "",
                 f"TODAY'S OBJECTIVE: {r['top_objective']}",
                 f"RISKS TO AVOID: {', '.join(r['risks_to_avoid']) if r['risks_to_avoid'] else 'none'}",
                 f"DON'T DO: {r['one_thing_not_to_do']}",
                 "", "FIRST 30 MINUTES:", r['first_30_minutes']]
        if r.get("first_packet"):
            p = r["first_packet"]; lines.append(f"\nFIRST PACKET: {p['title']}")
            for i, s in enumerate(p.get("steps", [])): lines.append(f"  {i+1}. {s}")
        self._output_to(self.acts_output, "\n".join(lines))

    def _run_shutdown(self):
        self._output_to(self.acts_output,
            "SHUTDOWN REFLECTION\n" + "=" * 50 + "\n\n"
            "Complete in terminal for interactive mode:\n"
            "  python3 chief_of_staff_agent.py --shutdown\n\n"
            "Questions to consider:\n"
            "1. What was completed today?\n"
            "2. What was delayed?\n"
            "3. What appeared unexpectedly?\n"
            "4. What evidence was created?\n"
            "5. What should be queued for tomorrow?\n"
            "6. What lesson should update doctrine/assumptions/workflows?")

    def _run_generate_commands(self):
        r = generate_commands()
        lines = ["GENERATE COMMANDS", "=" * 50, "", r.get("summary", "")]
        for c in r.get("commands", []): lines.append(f"  {c['id']}  {c['title']}")
        self._output_to(self.acts_output, "\n".join(lines))

    def _run_execute_approved(self):
        if not messagebox.askyesno("Confirm Execution",
            "Execute approved local commands?\n\n"
            "Only safe, reversible, local actions will run.\n"
            "No emails, calendar, or external actions."):
            return
        r = execute_approved()
        self._output_to(self.acts_output,
            "EXECUTION RESULTS\n" + "=" * 50 + "\n\n" + r.get("summary", "Done."))

    # ── Dialogs ────────────────────────────────────────────────────
    def _dialog(self, title, fields, callback):
        dlg = tk.Toplevel(self.root); dlg.title(title); dlg.geometry("500x400"); dlg.resizable(False, False)
        dlg.transient(self.root); dlg.grab_set()
        entries = {}
        for i, (label, default) in enumerate(fields):
            ttk.Label(dlg, text=label, font=FONT).grid(row=i, column=0, sticky=tk.W, padx=10, pady=6)
            var = tk.StringVar(value=default)
            if label.startswith("Description") or label.startswith("Content") or label.startswith("Commitment"):
                e = tk.Text(dlg, height=3, width=40, font=FONT); e.grid(row=i, column=1, padx=6, pady=4, sticky=tk.EW)
                e.insert("1.0", default); entries[label] = e
            else:
                e = ttk.Entry(dlg, textvariable=var, width=42, font=FONT); e.grid(row=i, column=1, padx=6, pady=4, sticky=tk.EW)
                entries[label] = var
        ttk.Button(dlg, text="Save", command=lambda: self._dialog_save(dlg, callback, entries)).grid(
            row=len(fields), column=0, columnspan=2, pady=16)
        dlg.columnconfigure(1, weight=1)

    def _dialog_save(self, dlg, callback, entries):
        values = {}
        for label, widget in entries.items():
            if isinstance(widget, tk.Text): values[label] = widget.get("1.0", "end-1c").strip()
            else: values[label] = widget.get().strip()
        dlg.destroy()
        try:
            result = callback(values)
            messagebox.showinfo("Saved", f"Saved: {result}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _add_project_dialog(self):
        def save(v):
            p = Project(project_id=uid(), name=v["Title"], strategic_goal=v["Strategic goal"],
                        description=v.get("Description", ""), status="active", created_at=today_str())
            recs = load_records(PROJECTS_PATH) if PROJECTS_PATH.exists() else []
            if not isinstance(recs, list): recs = []
            recs.append(p.__dict__); save_records(PROJECTS_PATH, recs)
            self._refresh_dashboard(); return p.name
        self._dialog("Add Project", [("Title", ""), ("Strategic goal", "research_publication"), ("Description", "")], save)

    def _add_opp_dialog(self):
        def save(v):
            o = Opportunity(opportunity_id=uid(), name=v["Title"], opportunity_type=v.get("Type", "grant"),
                           strategic_goal=v.get("Strategic goal", "research_publication"), created_at=today_str())
            recs = load_records(OPPORTUNITIES_PATH) if OPPORTUNITIES_PATH.exists() else []
            if not isinstance(recs, list): recs = []
            recs.append(o.__dict__); save_records(OPPORTUNITIES_PATH, recs)
            self._refresh_dashboard(); return o.name
        self._dialog("Add Opportunity", [("Title", ""), ("Type (grant/collaboration/etc.)", "grant"),
                      ("Strategic goal", "research_publication")], save)

    def _add_risk_dialog(self):
        def save(v):
            r = Risk(risk_id=uid(), title=v["Title"], risk_category=v.get("Category", "execution_drift"),
                     severity=int(v.get("Severity", "5")), created_date=today_str())
            recs = load_records(RISKS_PATH) if RISKS_PATH.exists() else []
            if not isinstance(recs, list): recs = []
            recs.append(r.__dict__); save_records(RISKS_PATH, recs)
            self._refresh_dashboard(); return r.title
        self._dialog("Add Risk", [("Title", ""), ("Category", "execution_drift"), ("Severity (1-10)", "5")], save)

    def _add_rel_dialog(self):
        def save(v):
            r = Relationship(relationship_id=uid(), name=v["Title"],
                           relationship_type=v.get("Type", "collaborator"), created_date=today_str())
            recs = load_records(RELATIONSHIPS_PATH) if RELATIONSHIPS_PATH.exists() else []
            if not isinstance(recs, list): recs = []
            recs.append(r.__dict__); save_records(RELATIONSHIPS_PATH, recs)
            self._refresh_dashboard(); return r.name
        self._dialog("Add Relationship", [("Title", ""), ("Type (collaborator/mentor/partner)", "collaborator")], save)

    def _add_impact_dialog(self):
        def save(v):
            imp = Impact(impact_id=uid(), date=today_str(), title=v["Title"],
                        impact_type=v.get("Type", "paper_submitted"),
                        strategic_goal=v.get("Strategic goal", ""),
                        magnitude=int(v.get("Magnitude", "5")))
            imps = load_impacts(); imps.append(imp); save_impacts(imps)
            self._refresh_dashboard(); return imp.title
        self._dialog("Add Impact", [("Title", ""), ("Type (paper_submitted/grant_awarded/etc.)", "paper_submitted"),
                      ("Strategic goal", ""), ("Magnitude (1-10)", "5")], save)

    def _add_metric_dialog(self):
        def save(v):
            m = Metric(metric_id=uid(), name=v["Title"], strategic_goal=v.get("Strategic goal", ""),
                      category=v.get("Category", "execution_quality"),
                      target_value=float(v.get("Target value", "1")),
                      current_value=float(v.get("Current value", "0")),
                      unit=v.get("Unit", "count"), last_updated=today_str())
            ms = load_metrics(); ms.append(m); save_metrics(ms)
            self._refresh_dashboard(); return m.name
        self._dialog("Add Metric", [("Title", ""), ("Category", "execution_quality"),
                      ("Strategic goal", ""), ("Target value", "1"), ("Current value", "0"), ("Unit", "count")], save)

    def _add_contract_dialog(self):
        def save(v):
            c = Contract(contract_id=uid(), title=v["Title"], strategic_goal=v.get("Strategic goal", ""),
                        commitment=v.get("Commitment", ""), start_date=today_str(),
                        end_date=v.get("End date (YYYY-MM-DD)", ""),
                        success_metric=v.get("Success metric", ""),
                        minimum_standard=v.get("Minimum standard", ""))
            cs = load_contracts(); cs.append(c); save_contracts(cs)
            self._refresh_dashboard(); return c.title
        self._dialog("Add Contract", [("Title", ""), ("Strategic goal", ""), ("Commitment", ""),
                      ("End date (YYYY-MM-DD)", ""), ("Success metric", ""), ("Minimum standard", "")], save)

    def _add_initiative_dialog(self):
        def save(v):
            i = Initiative(initiative_id=uid(), name=v["Title"], thesis=v.get("Thesis", ""),
                          strategic_goal=v.get("Strategic goal", ""), start_date=today_str(),
                          target_date=v.get("Target date (YYYY-MM-DD)", ""), status="active")
            ins = load_initiatives(); ins.append(i); save_initiatives(ins)
            self._refresh_dashboard(); return i.name
        self._dialog("Add Initiative", [("Title", ""), ("Thesis", ""),
                      ("Strategic goal", ""), ("Target date (YYYY-MM-DD)", "")], save)

    def _capture_dialog(self):
        def save(v):
            c = Capture(capture_id=uid(), date=today_str(), type=v.get("Type", "idea"),
                       title=v["Title"], content=v.get("Content", ""),
                       related_strategic_goal=v.get("Strategic goal", ""))
            cs = load_captures(); cs.append(c); save_captures(cs)
            self._refresh_dashboard(); return c.title
        self._dialog("Knowledge Capture", [("Type (idea/insight/evidence/lesson/etc.)", "idea"),
                      ("Title", ""), ("Content", ""), ("Strategic goal", "")], save)

    def _export_dashboard(self):
        text = self.dash_text.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"dashboard_{today_str()}.txt", title="Export Dashboard")
        if path:
            Path(path).write_text(text); messagebox.showinfo("Exported", f"Saved to {path}")

    def _run_export_csv(self, store):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], initialfile=f"{store}_export.csv", title="Export CSV")
        if path:
            r = export_csv(store, path)
            self._output_to(self.data_output,
                f"CSV EXPORT: {r.get('exported', 'error')}\n{r.get('records', 0)} records exported.")

    def _open_data_folder(self):
        folder = os.path.dirname(os.path.abspath(__file__)) or "."
        if sys.platform == "win32": os.startfile(folder)
        elif sys.platform == "darwin": os.system(f"open '{folder}'")
        else: os.system(f"xdg-open '{folder}' 2>/dev/null &")

    def _show_about(self):
        messagebox.showinfo("About Chief of Staff Agent",
            "Chief of Staff Agent v10\n\n"
            "Strategic Intelligence & Execution System\n"
            "Human-Governed Strategic Autonomy\n\n"
            "189 tests | 75 test classes | Python 3.12+\n"
            "Standard Library Only | No External APIs\n"
            "Offline-First | Privacy-Preserving\n\n"
            "github.com/ph7klw76/Chief_of_staff_agent")


# ── Review Functions (in-memory, no subprocess) ──────────────────
def metrics_review_text():
    r = metrics_review()
    lines = ["METRICS REVIEW", "=" * 50, "", r.get("summary", "")]
    for m in r.get("latest", []): lines.append(f"  {m['name'][:45]}  {m['current']}/{m['target']} {m['unit']}")
    return "\n".join(lines)

def impact_review_text():
    r = impact_review()
    lines = ["IMPACT REVIEW", "=" * 50, "", r.get("summary", "")]
    for i in r.get("top_3", []): lines.append(f"  [{i['type']}] {i['title'][:50]} (magnitude: {i['magnitude']})")
    return "\n".join(lines)

def roi_review_cmd_text():
    data = get_data_for_conflict()
    projs = [Project(**p) for p in (load_records(PROJECTS_PATH) or [])] if PROJECTS_PATH.exists() else []
    opps = [Opportunity(**o) for o in (load_records(OPPORTUNITIES_PATH) or [])] if OPPORTUNITIES_PATH.exists() else []
    r = roi_review(projs, load_workflows(), load_rels_from_core(), opps, load_assets_from_core(), load_metrics())
    lines = ["STRATEGIC ROI REVIEW", "=" * 50, "", r.get("summary", "")]
    for i in r.get("high_roi", []): lines.append(f"  HIGH [{i['type']}] {i['name'][:45]}  ROI:{i['roi']}")
    for i in r.get("low_roi", []): lines.append(f"  LOW  [{i['type']}] {i['name'][:45]}  ROI:{i['roi']}")
    return "\n".join(lines)

def conflict_review_text():
    r = conflict_review(get_data_for_conflict())
    lines = ["CONFLICT REVIEW", "=" * 50, "", r.get("summary", "")]
    for c in r.get("conflicts", []): lines.append(f"  [{c['severity'].upper()}] {c['description']}")
    return "\n".join(lines)

def decay_review_text():
    r = decay_review(load_rels_from_core() if RELATIONSHIPS_PATH.exists() else [],
                     load_projects_from_core(), load_assets_from_core(),
                     load_assums_from_core(), load_preds_from_core(),
                     load_risks_from_core(), load_workflows(),
                     [OKR(**o) for o in (load_records(OKRS_PATH) or [])] if OKRS_PATH.exists() else [])
    lines = ["DECAY REVIEW", "=" * 50, "", r.get("summary", "")]
    for d in r.get("decay_items", [])[:10]: lines.append(f"  [{d['type']}] {d['name'][:50]}: {d['issue']}")
    return "\n".join(lines)

def os_health_text():
    r = os_health()
    return f"OS HEALTH SCORE: {r['os_health_score']}/100 ({r['status']})\n" + \
           f"Strengths: {', '.join(r['strengths']) if r['strengths'] else 'none'}\n" + \
           f"Weaknesses: {', '.join(r['weaknesses']) if r['weaknesses'] else 'none'}"

def governance_board_text():
    r = governance_board()
    lines = ["GOVERNANCE BOARD", "=" * 50, "",
             f"POSITION: {r['strategic_position']}",
             f"INITIATIVES: {r['initiatives'].get('summary', 'none') if isinstance(r.get('initiatives'), dict) else '?'}",
             f"COMMANDS: {r['command_queue'].get('summary', 'none') if isinstance(r.get('command_queue'), dict) else '?'}",
             f"CONFLICTS: {r['conflicts'].get('summary', 'none') if isinstance(r.get('conflicts'), dict) else '?'}",
             f"CAPACITY: {r['capacity'].get('summary', 'none') if isinstance(r.get('capacity'), dict) else '?'}",
             f"DECAY: {r['decay']}",
             "", "RECOMMENDED DECISIONS:"]
    for d in r.get("recommended_decisions", []): lines.append(f"  - {d}")
    return "\n".join(lines)


# ── Entry Point ────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ChiefOfStaffApp(root)
        root.mainloop()
    except tk.TclError as e:
        print(f"\n  GUI Error: {e}")
        print("  Make sure tkinter is installed:")
        print("    Ubuntu/Debian: sudo apt install python3-tk")
        print("    macOS:         brew install python-tk")
        print("    Windows:       tkinter is included with Python (reinstall if missing)")
        print(f"\n  The CLI remains fully functional:")
        print(f"    python3 chief_of_staff_agent.py --demo")
        sys.exit(1)
