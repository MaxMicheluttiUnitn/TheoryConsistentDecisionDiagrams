"""tests for SMTSolver and PartialSMTSolver"""

from pysmt.shortcuts import (
    Or,
    FALSE,
    TRUE,
    Symbol,
    BOOL,
    And,
    REAL,
    LE,
    LT,
    Real,
    Plus,
    Times,
    Not,
)
from theorydd.smt_solver import SMTSolver
from theorydd.smt_solver_partial import PartialSMTSolver
import theorydd.formula as formula


def test_all_smt_total():
    """tests for all-SMT functionality of solvers"""
    solver = SMTSolver()
    phi_sat = And(
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Y", REAL), Symbol("X", REAL)),
    )
    assert solver.check_all_sat(
        phi_sat, None
    ), "Satisfiable formula should be SAT with SMTSolver"

    phi_unsat = And(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("X", REAL)),
    )
    assert not solver.check_all_sat(
        phi_unsat, None
    ), "Unsatisfiable formula should be UNSAT with SMTSolver"

def test_all_smt_total_bool_mapping():
    """tests for all-SMT functionality of total solver using boolean mapping"""
    solver = SMTSolver()
    phi_sat = And(
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Y", REAL), Symbol("X", REAL)),
    )
    assert solver.check_all_sat(
        phi_sat, formula.get_boolean_mapping(phi_sat)
    ), "Satisfiable formula should be SAT with SMTSolver"

    phi_unsat = And(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("X", REAL)),
    )
    assert not solver.check_all_sat(
        phi_unsat, formula.get_boolean_mapping(phi_unsat)
    ), "Unsatisfiable formula should be UNSAT with SMTSolver"


def test_all_smt_partial():
    """tests for all-SMT functionality of solvers"""
    partial_solver = PartialSMTSolver()
    phi_sat = And(
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Y", REAL), Symbol("X", REAL)),
    )
    assert partial_solver.check_all_sat(
        phi_sat, None
    ), "Satisfiable formula should be SAT with PartialSMTSolver"

    phi_unsat = And(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("X", REAL)),
    )
    assert not partial_solver.check_all_sat(
        phi_unsat, None
    ), "Unsatisfiable formula should be UNSAT with PartialSMTSolver"


def test_t_lemmas_partial():
    """tests for solvers.get_theory_lemmas()"""
    partial_solver = PartialSMTSolver()
    phi_sat = And(
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Zr", REAL), Symbol("W", REAL)),
    )
    partial_solver.check_all_sat(phi_sat, None)
    assert (
        len(partial_solver.get_theory_lemmas()) == 0
    ), "No T-lemmas should come for formula with non-conflicting T-atoms (partial)"

    phi_lemma = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial_solver.check_all_sat(phi_lemma, None)
    assert (
        len(partial_solver.get_theory_lemmas()) > 0
    ), "T-lemmas should come for formula with conflicting T-atoms (partial)"


def test_t_lemmas_total():
    """tests for solvers.get_theory_lemmas()"""
    solver = SMTSolver()
    phi_sat = And(
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Zr", REAL), Symbol("W", REAL)),
    )
    solver.check_all_sat(phi_sat, None)
    assert (
        len(solver.get_theory_lemmas()) == 0
    ), "No T-lemmas should come for formula with non-conflicting T-atoms"

    phi_lemma = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    solver.check_all_sat(phi_lemma, None)
    assert (
        len(solver.get_theory_lemmas()) > 0
    ), "T-lemmas should come for formula with conflicting T-atoms"
