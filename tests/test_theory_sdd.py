"""tests for T-SDDS"""

from copy import deepcopy
from theorydd.theory_sdd import TheorySDD
import theorydd.formula as formula
from theorydd.smt_solver_partial import PartialSMTSolver
from pysmt.shortcuts import Or, LT, REAL, Symbol, And, Not


def test_init_default():
    """tests SDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = PartialSMTSolver()
    partial.check_all_sat(phi, None)
    models = partial.get_models()
    tsdd = TheorySDD(phi, "partial")
    assert tsdd.count_nodes() > 1, "TSDD is not only True or False node"
    assert tsdd.count_models() == len(
        models
    ), "TSDD should have the same models found during All-SMT computation"


def test_init_with_known_lemmas():
    """tests SDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = PartialSMTSolver()
    partial.check_all_sat(phi, None)
    lemmas = partial.get_theory_lemmas()
    models = partial.get_models()
    tsdd = TheorySDD(phi, "partial", tlemmas=lemmas)
    assert tsdd.count_nodes() > 1, "TSDD is not only True or False node"
    assert tsdd.count_models() == len(
        models
    ), "TSDD should have the same models found during All-SMT computation"


def test_init_updated_computation_logger():
    """tests SDD generation"""
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
    tsdd = TheorySDD(phi, "partial", computation_logger=logger)
    assert tsdd.count_nodes() > 1, "TSDD is not only True or False node"
    assert tsdd.count_models() == len(
        models
    ), "TSDD should have the same models found during All-SMT computation"
    assert logger != copy_logger, "Computation logger should be updated"
    assert (
        logger["hi"] == copy_logger["hi"]
    ), "Old field of Logger should not be touched"


def test_init_unsat_formula():
    """tests SDD generation"""
    phi = And(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = PartialSMTSolver()
    partial.check_all_sat(phi, None)
    tsdd = TheorySDD(phi, "partial")
    assert tsdd.count_nodes() == 1, "TSDD is only False node"
    assert tsdd.count_models() == 0, "TSDD should have no models"


def test_init_tautology():
    """tests SDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        Not(LT(Symbol("X", REAL), Symbol("Y", REAL))),
    )
    partial = PartialSMTSolver()
    partial.check_all_sat(phi, None)
    tsdd = TheorySDD(phi, "partial")
    assert tsdd.count_nodes() == 1, "TSDD is only True node"
    assert (
        tsdd.count_models() == 2
    ), "TSDD should have 2 models (atom True and atom false)"


def test_one_variable():
    """tests SDD generation"""
    phi = LT(Symbol("a", REAL), Symbol("b", REAL))
    tsdd = TheorySDD(phi, "partial")
    assert tsdd.count_nodes() <= 1, "TSDD is only True node"
    assert tsdd.count_models() == 1, "TSDD should have 1 model (atom True)"
