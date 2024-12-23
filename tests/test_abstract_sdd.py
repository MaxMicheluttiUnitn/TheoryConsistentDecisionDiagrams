"""tests for Abstraction SDDs"""

from copy import deepcopy
from theorydd.abstractdd.abstraction_sdd import AbstractionSDD
from theorydd.solvers.mathsat_total import MathSATTotalEnumerator
from pysmt.shortcuts import Or, LT, REAL, Symbol, And, Not


def test_init_default():
    """tests abstraction SDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = MathSATTotalEnumerator()
    partial.check_all_sat(phi, None)
    models = partial.get_models()
    asdd = AbstractionSDD(phi, "partial")
    assert asdd.count_nodes() > 1, "abstr. SDD is not only True or False node"
    assert asdd.count_models() > len(
        models
    ), "abstr. SDD should have more models then the models found during All-SMT computation"


def test_init_updated_computation_logger():
    """tests abstraction SDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = MathSATTotalEnumerator()
    partial.check_all_sat(phi, None)
    models = partial.get_models()
    logger = {}
    logger["hi"] = "hello"
    copy_logger = deepcopy(logger)
    asdd = AbstractionSDD(phi, "partial", computation_logger=logger)
    assert asdd.count_nodes() > 1, "abstr. SDD is not only True or False node"
    assert asdd.count_models() >= len(
        models
    ), "abstr. SDD should have more models then the models found during All-SMT computation"
    assert logger != copy_logger, "Computation logger should be updated"
    assert (
        logger["hi"] == copy_logger["hi"]
    ), "Old field of Logger should not be touched"


def test_init_t_unsat_formula():
    """tests abstraction SDD generation"""
    phi = And(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = MathSATTotalEnumerator()
    partial.check_all_sat(phi, None)
    asdd = AbstractionSDD(phi, "partial")
    assert asdd.count_nodes() > 1, "abstr. SDD is not only False node"
    assert asdd.count_models() > 0, "abstr. SDD should have models"


def test_init_bool_unsat_formula():
    """tests abstraction SDD generation"""
    phi = And(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        Not(LT(Symbol("X", REAL), Symbol("Y", REAL))),
    )
    partial = MathSATTotalEnumerator()
    partial.check_all_sat(phi, None)
    asdd = AbstractionSDD(phi, "partial")
    assert asdd.count_nodes() == 1, "abstr. SDD is only False node"
    assert asdd.count_models() == 0, "abstr. SDD should have no models"


def test_init_tautology():
    """tests abstraction SDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        Not(LT(Symbol("X", REAL), Symbol("Y", REAL))),
    )
    partial = MathSATTotalEnumerator()
    partial.check_all_sat(phi, None)
    asdd = AbstractionSDD(phi, "partial")
    assert asdd.count_nodes() == 1, "TSDD is only True node"
    assert (
        asdd.count_models() == 2
    ), "TSDD should have 2 models (atom True and atom false)"
