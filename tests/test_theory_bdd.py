"""tests for T-BDDS"""

from copy import deepcopy
from theorydd.tdd.theory_bdd import TheoryBDD
import theorydd.formula as formula
from theorydd.solvers.mathsat_total import MathSATTotalEnumerator
from theorydd.solvers.mathsat_partial_extended import MathSATExtendedPartialEnumerator
from pysmt.shortcuts import Or, LT, REAL, Symbol, And, Not, Iff, is_sat
import pytest


def test_init_default():
    """tests BDD generation"""
    phi = Or(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = MathSATExtendedPartialEnumerator()
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
    partial = MathSATExtendedPartialEnumerator()
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
    partial = MathSATExtendedPartialEnumerator()
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
    ), "Old field of Logger should not be changed"


def test_init_unsat_formula():
    """tests BDD generation"""
    phi = And(
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    )
    partial = MathSATExtendedPartialEnumerator()
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
    partial = MathSATExtendedPartialEnumerator()
    partial.check_all_sat(phi, None)
    tbdd = TheoryBDD(phi, "partial")
    assert tbdd.count_nodes() == 1, "TBDD is only True node"
    assert (
        tbdd.count_models() == 2
    ), "TBDD should have 2 models (atom True and atom false)"


def _create_disjunct(model):
    literals = []
    for atom, truth in model.items():
        if truth:
            literals.append(atom)
        else:
            literals.append(Not(atom))
    return And(*literals)


test_phi = [
    Or(  # SAT
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    ),
    And(  # UNSAT
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        LT(Symbol("Y", REAL), Symbol("Zr", REAL)),
        LT(Symbol("Zr", REAL), Symbol("X", REAL)),
    ),
    Or(  # VALID
        LT(Symbol("X", REAL), Symbol("Y", REAL)),
        Not(LT(Symbol("X", REAL), Symbol("Y", REAL))),
    ),
    formula.read_phi("./tests/items/rng.smt"),
]


@pytest.mark.parametrize("phi", test_phi)
def test_init_models_partial(phi):
    """tests that models of the T-BDD are also models of phi"""
    partial = MathSATExtendedPartialEnumerator()
    partial.check_all_sat(phi, None)
    tlemmas = partial.get_theory_lemmas()
    tbdd = TheoryBDD(phi, solver=partial, tlemmas=tlemmas)
    ddmodels = tbdd.pick_all()

    # check SMT of not (phi <=> encoding)
    # if UNSAT => encoding is correct
    phi_iff_encoding = Not(Iff(phi, Or(*[_create_disjunct(m) for m in ddmodels])))
    assert not is_sat(phi_iff_encoding), "not phi iff models should be UNSAT"

    # check all models are also models of phi
    for model in ddmodels:
        phi_and_model = And(phi, _create_disjunct(model))
        assert is_sat(phi_and_model), "Every model should be also a model for phi"


@pytest.mark.parametrize("phi", test_phi)
def test_init_models_total(phi):
    """tests that models of the T-BDD are also models of phi"""
    total = MathSATTotalEnumerator()
    total.check_all_sat(phi, None)
    tbdd = TheoryBDD(phi, solver=total)
    ddmodels = tbdd.pick_all()

    # check SMT of not (phi <=> encoding)
    # if UNSAT => encoding is correct
    phi_iff_encoding = Not(Iff(phi, Or(*[_create_disjunct(m) for m in ddmodels])))
    assert not is_sat(phi_iff_encoding), "not phi iff models should be UNSAT"

    # check all models are also models of phi
    for model in ddmodels:
        phi_and_model = And(phi, _create_disjunct(model))
        assert is_sat(phi_and_model), "Every model should be also a model for phi"


def test_lemma_loading_total():
    """tests loading data with total solver"""
    phi = formula.read_phi("./tests/items/rng.smt")
    total = MathSATTotalEnumerator()
    tbdd = TheoryBDD(phi, solver=total, load_lemmas="./tests/items/rng_lemmas.smt")
    other_phi = formula.read_phi("./tests/items/rng.smt")
    other_total = MathSATTotalEnumerator()
    other_tbdd = TheoryBDD(other_phi, solver=other_total)
    assert (
        tbdd.count_models() == other_tbdd.count_models()
    ), "Same modles should come from different loading"


def test_lemma_loading_partial():
    """tests loading data with partial solver"""
    phi = formula.read_phi("./tests/items/rng.smt")
    partial = MathSATExtendedPartialEnumerator()
    tbdd = TheoryBDD(phi, solver=partial, load_lemmas="./tests/items/rng_lemmas.smt")
    other_phi = formula.read_phi("./tests/items/rng.smt")
    other_partial = MathSATExtendedPartialEnumerator()
    other_tbdd = TheoryBDD(other_phi, solver=other_partial)
    assert (
        tbdd.count_models() == other_tbdd.count_models()
    ), "Same modles should come from different loading"
