"""tests for module formula"""

from pysmt.shortcuts import (
    Or,
    FALSE,
    TRUE,
    Symbol,
    BOOL,
    And,
    REAL,
    LE,
    Real,
    Plus,
    Times,
    Not,
)
from pysmt.fnode import FNode
import theorydd.formula as formula
from theorydd.smt_solver import SMTSolver


def test_bottom():
    """test for formula.bottom()"""
    assert formula.bottom() == FALSE(), "bottom is the node False"


def test_top():
    """test for formula.top()"""
    assert formula.top() == TRUE(), "bottom is the node False"


def test_get_phi_and_lemmas():
    """tests for forula.get_phi_and_lemmas()"""
    phi = Or(Symbol("A", BOOL), Symbol("B", BOOL))
    tlemmas = [Symbol("C", BOOL), Or(Symbol("A", BOOL), Symbol("C", BOOL))]
    phi_and_lemmas = formula.get_phi_and_lemmas(phi, tlemmas)
    assert isinstance(phi_and_lemmas, FNode), "phi and lemmas should be an FNode"
    assert phi_and_lemmas == And(
        phi, tlemmas[0], tlemmas[1]
    ), "phi and lemmas is the big and of phi and all the lemmas"


def test_big_and():
    """tests for formula.big_and()"""
    tlemmas = [Symbol("C", BOOL), Or(Symbol("A", BOOL), Symbol("C", BOOL))]
    big_and = formula.big_and(tlemmas)
    assert isinstance(big_and, FNode), "phi and lemmas should be an FNode"
    assert big_and == And(
        tlemmas[0], tlemmas[1]
    ), "Big and should be the And of all the items"


def test_atom_diff():
    """tests for formula.atoms_difference()"""
    phi_atoms = [Symbol("A", BOOL), Symbol("B", BOOL)]
    tlemmas_atoms = [Symbol("A", BOOL), Symbol("B", BOOL), Symbol("C", BOOL)]
    diff = formula.atoms_difference(phi_atoms, tlemmas_atoms)
    assert diff == [
        Symbol("C", BOOL)
    ], "atom difference should show all items in the second list which are not in the first"
    tlemmas_atoms = [
        Symbol("A", BOOL),
        Symbol("B", BOOL),
        Symbol("C", BOOL),
        Symbol("C", BOOL),
    ]
    diff = formula.atoms_difference(phi_atoms, tlemmas_atoms)
    assert diff == [Symbol("C", BOOL)], "duplicate items shall not be counted twice"
    tlemmas_atoms = [Symbol("A", BOOL), Symbol("C", BOOL), Symbol("C", BOOL)]
    diff = formula.atoms_difference(phi_atoms, tlemmas_atoms)
    assert diff == [
        Symbol("C", BOOL)
    ], "items missing in the second set should not be considered"


def test_get_symbols():
    """tests for formula.get_symbols()"""
    phi = And(
        Symbol("F", BOOL),
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        Symbol("Z", BOOL),
    )
    assert len(formula.get_symbols(phi)) == 4, "the normalized formula has 4 symbols"
    phi = Or(
        And(
            Symbol("F", BOOL),
            LE(Symbol("X", REAL), Symbol("Y", REAL)),
            LE(Symbol("Y", REAL), Symbol("X", REAL)),
            Symbol("Z", BOOL),
        ),
        Not(LE(Symbol("X", REAL), Symbol("Y", REAL))),
        Not(LE(Symbol("Y", REAL), Symbol("X", REAL))),
    )
    assert (
        len(formula.get_symbols(phi)) == 4
    ), "the normalized formula has 4 symbols, even if some appear more than once"


def test_boolean_mapping():
    """tests for formula.get_boolean_mapping"""
    phi = formula.bottom()
    mapping = formula.get_boolean_mapping(phi)
    assert mapping == {}, "boolean mapping of empty formula should be empty"
    phi = And(
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Y", REAL), Symbol("X", REAL)),
    )
    mapping = formula.get_boolean_mapping(phi)
    assert mapping == {
        Symbol("fresh_a", BOOL): LE(Symbol("X", REAL), Symbol("Y", REAL)),
        Symbol("fresh_b", BOOL): LE(Symbol("Y", REAL), Symbol("X", REAL)),
    } or mapping == {
        Symbol("fresh_b", BOOL): LE(Symbol("X", REAL), Symbol("Y", REAL)),
        Symbol("fresh_a", BOOL): LE(Symbol("Y", REAL), Symbol("X", REAL)),
    }, "boolean mapping of formula should have 1 boolean for each T-atom" + str(
        mapping
    )
    phi = And(
        Symbol("F", BOOL),
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Y", REAL), Symbol("X", REAL)),
        Symbol("Z", BOOL),
    )
    mapping = formula.get_boolean_mapping(phi)
    assert mapping == {
        Symbol("fresh_a", BOOL): LE(Symbol("X", REAL), Symbol("Y", REAL)),
        Symbol("fresh_b", BOOL): LE(Symbol("Y", REAL), Symbol("X", REAL)),
    } or mapping == {
        Symbol("fresh_b", BOOL): LE(Symbol("X", REAL), Symbol("Y", REAL)),
        Symbol("fresh_a", BOOL): LE(Symbol("Y", REAL), Symbol("X", REAL)),
    }, "boolean mapping of formula should have only for T-atoms"


def test_get_atomss():
    """tyests for get atoms"""
    phi = And(
        Symbol("F", BOOL),
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Y", REAL), Symbol("X", REAL)),
        Symbol("Z", BOOL),
    )
    assert len(formula.get_atoms(phi)) == 4, "the normalized formula has 4 atoms"
    phi = Or(
        And(
            Symbol("F", BOOL),
            LE(Symbol("X", REAL), Symbol("Y", REAL)),
            LE(Symbol("Y", REAL), Symbol("X", REAL)),
            Symbol("Z", BOOL),
        ),
        Not(LE(Symbol("X", REAL), Symbol("Y", REAL))),
        Not(LE(Symbol("Y", REAL), Symbol("X", REAL))),
    )
    assert (
        len(formula.get_atoms(phi)) == 4
    ), "the normalized formula has 4 atoms, even if some appear more than once"


def test_normalization():
    """tests for get_normalized"""
    solver = SMTSolver()
    converter = solver.get_converter()
    # all atoms are different
    phi = And(
        Symbol("F", BOOL),
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Y", REAL), Symbol("X", REAL)),
        Symbol("Z", BOOL),
    )
    normal = formula.get_normalized(phi, converter)
    assert len(formula.get_atoms(normal)) == 4, "the normalized formula has 4 atoms"
    assert len(formula.get_atoms(normal)) == len(
        formula.get_atoms(phi)
    ), "different atoms should be normalized into different atoms"
    # 1st and 3rd LE are actually the same
    phi = And(
        Symbol("F", BOOL),
        LE(Symbol("X", REAL), Symbol("Y", REAL)),
        LE(Symbol("Y", REAL), Symbol("X", REAL)),
        LE(Plus(Symbol("X", REAL), Times(Real(-1), Symbol("Y", REAL))), Real(0)),
        Symbol("Z", BOOL),
    )
    normal = formula.get_normalized(phi, converter)
    assert len(formula.get_atoms(normal)) == 4, "the normalized formula has 4 atoms"
    assert len(formula.get_atoms(normal)) < len(
        formula.get_atoms(phi)
    ), "equivalent atoms should be normalized into the same atom"
