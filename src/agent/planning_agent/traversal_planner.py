"""
TraversalPlanner — Phase 3 Step 1 analog for the Testing Agent.

Reads the full list of non-dropped enriched test cases and produces a
strategically ordered execution sequence BEFORE the browser session starts.

Ordering strategy (pure heuristic, no LLM call required):
  Phase A — Public TCs (requires_auth=False, non-destructive)
  Phase B — Authenticated TCs (requires_auth=True, non-destructive)
  Phase C — Destructive TCs (Logout, Reset App State — always last)

Within each phase, TCs are ordered by priority: High → Medium → Low.

Rationale: Destructive test cases (logout, state reset) would invalidate
the shared browser session for all subsequent authenticated tests if run
out of order. This planner guarantees session integrity across the run.
"""

from typing import List, Dict, Any


class TraversalPlanner:
    """
    Produces a strategically ordered test case execution plan.

    Mirrors the NavigationPlanner agent from AutoTestGenX Phase 3, which
    separates execution into 'public' and 'authenticated' phases and forces
    destructive actions (logout, reset state) to the end of the queue.
    """

    # Modules whose execution permanently alters session or app state.
    # These must always run last, after all other functional tests.
    DESTRUCTIVE_MODULES = {"Logout", "Reset App State"}

    # Priority order mapping (lower number = higher priority = runs first)
    PRIORITY_RANK: Dict[str, int] = {
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }

    def plan(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return test_cases in a strategically ordered sequence.

        Args:
            test_cases: List of non-dropped enriched test case dicts.

        Returns:
            Ordered list in execution sequence:
            Phase A (public, non-destructive)
              → Phase B (authenticated, non-destructive)
              → Phase C (destructive)
        """
        def phase_key(tc: Dict[str, Any]) -> int:
            module = tc.get("module", "")
            if module in self.DESTRUCTIVE_MODULES:
                return 2  # Phase C — always last
            if tc.get("requires_auth", False):
                return 1  # Phase B — authenticated
            return 0      # Phase A — public

        def priority_key(tc: Dict[str, Any]) -> int:
            return self.PRIORITY_RANK.get(tc.get("priority", "Low"), 2)

        ordered = sorted(test_cases, key=lambda tc: (phase_key(tc), priority_key(tc)))

        # Log the plan summary for the run summary / debug output
        phase_labels = {0: "Public", 1: "Authenticated", 2: "Destructive"}
        print("\n📋 TraversalPlanner — Execution Plan:")
        current_phase = -1
        for tc in ordered:
            p = phase_key(tc)
            if p != current_phase:
                current_phase = p
                print(f"  ── Phase {phase_labels[p]} ──")
            name = f"{tc.get('module', '?')} / {tc.get('tc_id', '?')}"
            print(f"    [{tc.get('priority', '?')}] {name}: {tc.get('title', '')[:60]}")
        print()

        return ordered
