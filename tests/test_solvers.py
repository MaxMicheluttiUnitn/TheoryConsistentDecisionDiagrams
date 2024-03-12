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


def test_all_smt():
    """tests for all-SMT functionality of solvers"""
    solver = SMTSolver()
    partial_solver = PartialSMTSolver()
    phi_sat = And(
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Y", REAL), Symbol("X", REAL)),
    )
    assert solver.check_all_sat(
        phi_sat, None
    ), "Satisfiable formula should be SAT with SMTSolver"
    assert partial_solver.check_all_sat(
        phi_sat, None
    ), "Satisfiable formula should be SAT with PartialSMTSolver"

    phi_unsat = And(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("X", REAL)),
    )
    assert not solver.check_all_sat(
        phi_unsat, None
    ), "Unsatisfiable formula should be UNSAT with SMTSolver"
    assert not partial_solver.check_all_sat(
        phi_unsat, None
    ), "Unsatisfiable formula should be UNSAT with PartialSMTSolver"


def test_t_lemmas():
    """tests for solvers.get_theory_lemmas()"""
    solver = SMTSolver()
    partial_solver = PartialSMTSolver()
    phi_sat = And(
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Zr", REAL), Symbol("W", REAL)),
    )
    solver.check_all_sat(phi_sat, None)
    assert (
        len(solver.get_theory_lemmas()) == 0
    ), "No T-lemmas should come for formula with non-conflicting T-atoms"
    partial_solver.check_all_sat(phi_sat, None)
    assert (
        len(partial_solver.get_theory_lemmas()) == 0
    ), "No T-lemmas should come for formula with non-conflicting T-atoms (partial)"

    phi_lemma = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    solver.check_all_sat(phi_lemma, None)
    partial_solver.check_all_sat(phi_lemma, None)
    assert (
        len(solver.get_theory_lemmas()) > 0
    ), "T-lemmas should come for formula with conflicting T-atoms"
    assert (
        len(partial_solver.get_theory_lemmas()) > 0
    ), "T-lemmas should come for formula with conflicting T-atoms (partial)"
