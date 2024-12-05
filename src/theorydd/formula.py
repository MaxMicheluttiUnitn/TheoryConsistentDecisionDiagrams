"""this module simplifies interactions with the pysmt library for handling SMT formulas"""

from typing import List, Dict, Set
from pysmt.shortcuts import (
    Symbol as _Symbol,
    REAL as _REAL,
    And as _And,
    Or as _Or,
    Xor as _Xor,
    BOOL as _BOOL,
    Real as _Real,
    LT as _LT,
    read_smtlib as _read_smtlib,
    write_smtlib as _write_smtlib,
    TRUE as _TRUE,
    FALSE as _FALSE,
)
from pysmt.fnode import FNode
from theorydd._string_generator import SequentialStringGenerator

from theorydd.normalizer import NormalizerWalker


def default_phi() -> FNode:
    """Returns a default SMT formula's root FNode:
    [(x>0) ∧ (x<1)] ∧ [(y<1) ∨ ((x>y) ∧ (y>1/2))]

    Returns:
        FNode: the default formula
    """
    x1, x2, x3, x4, a = (
        _Symbol("x1", _REAL),
        _Symbol("x2", _REAL),
        _Symbol("x3", _REAL),
        _Symbol("x4", _REAL),
        _Symbol("a", _BOOL),
    )
    left_xor = _Or(x1 > x2, x2 > x1)
    right_xor = _Or(x3 > x4, x4 > x3)
    phi = _And(left_xor, right_xor, _Xor(x1 > x4, x4 > x1), a)

    # phi = [(x>0) ∧ (x<1)] ∧ [(y<1) ∨ ((x>y) ∧ (y>1/2))]
    phi = _And(
        _And(_LT(_Real(0), x1), _LT(x1, _Real(1))),
        _Or(_LT(x2, _Real(1)), _And(_LT(x2, x1), _LT(_Real(0.5), x2))),
    )
    return phi


def bottom() -> FNode:
    """return a FNode representing False"""
    return _FALSE()

def top() -> FNode:
    """returns a FNode representing True"""
    return _TRUE()

def read_phi(filename: str) -> FNode:
    """Reads the SMT formula from a file and returns the corresponding root FNode

    Args:
        filename (str): the name of the file

    Returns:
        FNode: the pysmt formula read from the file 
    """
    # pylint: disable=unused-argument
    if not isinstance(filename,str):
        raise TypeError("Expected str found "+str(type(filename)))
    other_phi = _read_smtlib(filename)
    return other_phi


def save_phi(phi: FNode, filename: str) -> None:
    """Saves the formula phi on a SMT file

    Args:
        filename (str): the name of the file
    """
    # pylint: disable=unused-argument
    if not isinstance(filename,str):
        raise TypeError("Expected str found "+str(type(filename)))
    _write_smtlib(phi, filename)


def get_atoms(phi: FNode) -> List[FNode]:
    """Returns a list of all the atoms in the SMT formula

    Args:
        phi (FNode): a pysmt formula

    Returns:
        List[FNode]: the atoms in the formula
    """
    if not isinstance(phi,FNode):
        raise TypeError("Expected FNode found "+str(type(phi)))
    return list(phi.get_atoms())


def get_symbols(phi: FNode) -> List[FNode]:
    """returns all symbols in phi
    
    Args:
        phi (FNode): a pysmt formula

    Returns:
        List[FNode]: the symbols in the formula
    """
    if not isinstance(phi,FNode):
        raise TypeError("Expected FNode found "+str(type(phi)))
    return list(phi.get_free_variables())


def get_normalized(phi: FNode, converter) -> FNode:
    """Returns a normalized version of phi
    
    Args:
        phi (FNode): a pysmt formula

    Returns:
        FNode: the provided formula normalized according to the converter
    """
    if not isinstance(phi,FNode):
        raise TypeError("Expected FNode found "+str(type(phi)))
    walker = NormalizerWalker(converter)
    return walker.walk(phi)


def get_phi_and_lemmas(phi: FNode, tlemmas: List[FNode]) -> FNode:
    """Returns a formula that is equivalent to phi and lemmas as an FNode
    
    Args:
        phi (FNode): a pysmt formula
        tlemmas (List[FNode]): a list of pysmt formulas

    Returns:
        FNode: the big and of phi and the lemmas
    """
    if not isinstance(phi,FNode):
        raise TypeError("Expected FNode found "+str(type(phi)))
    if not isinstance(tlemmas,list):
        raise TypeError("Expected List found "+str(type(tlemmas)))
    if len(tlemmas) == 0:
        return phi
    for lemma in tlemmas:
        if not isinstance(lemma,FNode):
            raise TypeError("Expected FNode found "+str(type(lemma)))
    return _And(phi, *tlemmas)


def get_boolean_mapping(phi: FNode) -> Dict[FNode, FNode]:
    """Generates a new fresh atom for each T-atom in phi and maps them
    
    Args:
        phi (FNode): a pysmt formula

    Returns:
        Dict[FNode,FNode]: a dictionary containing the mapping, 
            where the fresh boolean atoms are keys and the T-atoms are items
    """
    phi_atoms = get_atoms(phi)
    res: Dict[FNode, FNode] = {}
    gen = SequentialStringGenerator()
    for atom in phi_atoms:
        if not atom.is_symbol():
            res.update({_Symbol(f"fresh_{gen.next_string()}", _BOOL): atom})
    return res


def atoms_difference(original: List[FNode], expanded: List[FNode]) -> List[FNode]:
    """Computes the diffrence between expanded and original
    
    Args:
        original (List[FNode]): a list the atoms of the original pysmt formula,
            before adding the lemmas
        tlemmas (List[FNode]): a list of the atoms the expanded formula, 
            with the lemmas 

    Returns:
        List[FNode]: the atoms that appear in expanded, but do not appear in original
    """
    result: Set[FNode] = set()
    for atom in expanded:
        if not atom in original:
            result.add(atom)
    return list(result)


def big_and(nodes: List[FNode]) -> FNode:
    """Returns the big and of all the arguments
    
    Args:
        nodes (List[FNode]): a list of pysmt formulas

    Returns:
        FNode: the big and of all the nodes. 
        If no atom is provided, this function returns the FNode for TRUE"""
    if len(nodes) == 0:
        return _TRUE()
    elif len(nodes) == 1:
        return nodes[0]
    return _And(*nodes)
