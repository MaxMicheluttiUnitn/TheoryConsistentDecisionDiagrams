'''this module simplifies interactions with the pysmt library for handling SMT formulas'''

from typing import List, Dict
from pysmt.shortcuts import Symbol, REAL, And, Or, Xor, BOOL, Real, LT, Minus, Plus, Not, read_smtlib, Exists, write_smtlib, TRUE, FALSE
from pysmt.fnode import FNode
from theorydd._string_generator import SequentialStringGenerator

from theorydd.normalizer import NormalizerWalker


def get_phi() -> FNode:
    ' ' 'Returns the default SMT formula\'s root FNode' ' '
    x1, x2, x3, x4, a = Symbol("x1", REAL), Symbol(
        "x2", REAL), Symbol("x3", REAL), Symbol(
        "x4", REAL), Symbol("a", BOOL)
    left_xor = Or(x1 > x2, x2 > x1)
    right_xor = Or(x3 > x4, x4 > x3)
    phi = And(left_xor, right_xor, Xor(x1 > x4, x4 > x1), a)

    # phi = Xor(x1>x4,x4>x1)
    # [(x>0) ∧ (x<1)] ∧ [(y<1) ∨ ((x>y) ∧ (y>1/2))]
    phi = And(And(LT(Real(0), x1), LT(x1, Real(1))), Or(
        LT(x2, Real(1)), And(LT(x2, x1), LT(Real(0.5), x2))))

    b1 = LT(x1, Minus(x2, Real(1)))
    b2 = LT(Plus(x2, Real(1)), x1)
    a = LT(Real(20), x1)

    phi = And(Or(b1, b2), Or(Not(b1), a))

    # phi = Or(LT(x1,Real(0)),LT(Real(1),x1))
    return phi


def bottom() -> FNode:
    """return a FNode representing False"""
    return FALSE()

def read_phi(filename: str) -> FNode:
    ' ' 'Reads the SMT formula from a file and returns the corresponding root FNode' ' '
    # pylint: disable=unused-argument
    other_phi = read_smtlib(filename)
    return other_phi

def save_truth(filename: str) -> None:
    ' ' 'Save the valid formula with only a TRUE on a SMT file' ' '
    # pylint: disable=unused-argument
    truth = TRUE()
    write_smtlib(truth,filename)

def save_phi(phi: FNode, filename: str) -> None:
    ' ' 'Save the formula phi on a SMT file' ' '
    # pylint: disable=unused-argument
    write_smtlib(phi,filename)


def get_atoms(phi: FNode) -> List[FNode]:
    ' ' 'returns a list of all the atoms in the SMT formula' ' '
    return list(phi.get_atoms())


def get_symbols(phi: FNode) -> List[FNode]:
    '''returns all symbols in phi'''
    return list(phi.get_free_variables())


def get_normalized(phi: FNode, converter) -> FNode:
    '''Returns a normalized version of phi'''
    walker = NormalizerWalker(converter)
    return walker.walk(phi)


def get_phi_and_lemmas(phi: FNode, tlemmas: List[FNode]) -> FNode:
    ' ' 'Returns a formula that is equivalent to phi and lemmas as an FNode' ' '
    return And(phi, *tlemmas)


def get_boolean_mapping(phi: FNode) -> Dict[FNode, FNode]:
    """generates a new fresh atom for each T-atom in phi"""
    phi_atoms = get_atoms(phi)
    res: Dict[FNode, FNode] = {}
    gen = SequentialStringGenerator()
    for atom in phi_atoms:
        res.update({Symbol(f"fresh_{gen.next_string()}", BOOL): atom})
    return res


def atoms_difference(original: List[FNode], expanded: List[FNode]) -> List[FNode]:
    """computes the diffrence between expanded and original"""
    result: List[FNode] = []
    for atom in expanded:
        if not atom in original:
            result.append(atom)
    return result


def existentially_quantify(phi: FNode, atoms: List[FNode]) -> FNode:
    """existentially quantifies the formula over the given atoms"""
    return Exists(atoms, phi)


def big_and(nodes: List[FNode]) -> FNode:
    """returns the big and of all the arguments"""
    return And(*nodes)
