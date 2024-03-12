"""tests for T-BDDS"""

from copy import deepcopy
from theorydd.theory_bdd import TheoryBDD
import theorydd.formula as formula
from theorydd.smt_solver_partial import PartialSMTSolver
from pysmt.shortcuts import Or, LT, REAL, Symbol, And, Not


def test_init_default():
    """tests BDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = PartialSMTSolver()
    partial.check_all_sat(phi, None)
    models = partial.get_models()
    tbdd = TheoryBDD(phi, "partial")
    assert tbdd.count_nodes() > 1, "TBDD is not only True or False node"
    assert tbdd.count_models() == len(
        models
    ), "TBDD should have the same models found during All-SMT computation"


def test_init_with_known_lemmas():
    """tests BDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = PartialSMTSolver()
    partial.check_all_sat(phi, None)
    lemmas = partial.get_theory_lemmas()
    models = partial.get_models()
    tbdd = TheoryBDD(phi, "partial", tlemmas=lemmas)
    assert tbdd.count_nodes() > 1, "TBDD is not only True or False node"
    assert tbdd.count_models() == len(
        models
    ), "TBDD should have the same models found during All-SMT computation"


def test_init_updated_computation_logger():
    """tests BDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = PartialSMTSolver()
    partial.check_all_sat(phi, None)
    models = partial.get_models()
    logger = {}
    logger["hi"] = "hello"
    copy_logger = deepcopy(logger)
    tbdd = TheoryBDD(phi, "partial", computation_logger=logger)
    assert tbdd.count_nodes() > 1, "TBDD is not only True or False node"
    assert tbdd.count_models() == len(
        models
    ), "TBDD should have the same models found during All-SMT computation"
    assert logger != copy_logger, "Computation logger should be updated"
    assert (
        logger["hi"] == copy_logger["hi"]
    ), "Old field of Logger should not be touched"


def test_init_unsat_formula():
    """tests BDD generation"""
    phi = And(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = PartialSMTSolver()
    partial.check_all_sat(phi, None)
    tbdd = TheoryBDD(phi, "partial")
    assert tbdd.count_nodes() == 1, "TBDD is only False node"
    assert tbdd.count_models() == 0, "TBDD should have no models"

def test_init_tautology():
    """tests BDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        Not(LT(Symbol("X", REAL), Symbol("Y", REAL))),
    )
    partial = PartialSMTSolver()
    partial.check_all_sat(phi, None)
    tbdd = TheoryBDD(phi, "partial")
    assert tbdd.count_nodes() == 1, "TBDD is only True node"
    assert tbdd.count_models() == 2, "TBDD should have 2 models (atom True and atom false)"
