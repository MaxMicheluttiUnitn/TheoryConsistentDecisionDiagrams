"""this module simplifies interactions with the pysmt library for handling SMT formulas"""

from io import StringIO
import json
import os

from typing import Iterable, List, Dict, Set, Tuple
from pysmt.shortcuts import (
    Symbol as _Symbol,
    REAL as _REAL,
    And as _And,
    Or as _Or,
    BOOL as _BOOL,
    Real as _Real,
    LT as _LT,
    Not as _Not,
    read_smtlib as _read_smtlib,
    write_smtlib as _write_smtlib,
    TRUE as _TRUE,
    FALSE as _FALSE,
)
from pysmt.fnode import FNode
from pysmt.smtlib.script import smtlibscript_from_formula as _script_from_formula
from pysmt.smtlib.parser.parser import get_formula as _get_formula
from theorydd.util._string_generator import SequentialStringGenerator

from theorydd.util.custom_exceptions import FormulaException
from theorydd.util.disjoint_set import DisjointSet
from theorydd.walkers.normalizer import NormalizerWalker
from theorydd.walkers.duoble_negation_walker import DoubleNegWalker


def default_phi() -> FNode:
    """Returns a default SMT formula's root FNode:
    [(x>0) ∧ (x<1)] ∧ [(y<1) ∨ ((x>y) ∧ (y>1/2))]

    This formula is only an example that can be used
    to test correct installation of the package
    or to generate simple example outputs
    showcasing what the package can do

    Returns:
        FNode: the default formula
    """
    x1, x2, b1 = (
        _Symbol("x1", _REAL),
        _Symbol("x2", _REAL),
        _Symbol("b1", _BOOL),
    )

    # phi = [(x>0) ∧ (x<1)] ∧ [(y<1) ∨ ((x>y) ∧ (y>1/2))] ∧ b1
    phi = _And(
        _And(_LT(_Real(0), x1), _LT(x1, _Real(1))),
        _Or(_LT(x2, _Real(1)), _And(_LT(x2, x1), _LT(_Real(0.5), x2))),
        b1,
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
    if not isinstance(filename, str):
        raise TypeError("Expected str found " + str(type(filename)))
    try:
        other_phi = _read_smtlib(filename)
        return other_phi
    except Exception as _e:
        raise FormulaException(
            "The input formula is not supported by the PYSMT package and cannot be read"
        ) from _e


def save_phi(phi: FNode, filename: str) -> None:
    """Saves the formula phi on a SMT file

    Args:
        filename (str): the name of the file
    """
    # pylint: disable=unused-argument
    if not isinstance(filename, str):
        raise TypeError("Expected str found " + str(type(filename)))
    _write_smtlib(phi, filename)


def get_atoms(phi: FNode) -> List[FNode]:
    """Returns a list of all the atoms in the SMT formula

    Args:
        phi (FNode): a pysmt formula

    Returns:
        List[FNode]: the atoms in the formula
    """
    if not isinstance(phi, FNode):
        raise TypeError("Expected FNode found " + str(type(phi)))
    return list(phi.get_atoms())


def get_symbols(phi: FNode) -> List[FNode]:
    """returns all symbols in phi

    Args:
        phi (FNode): a pysmt formula

    Returns:
        List[FNode]: the symbols in the formula
    """
    if not isinstance(phi, FNode):
        raise TypeError("Expected FNode found " + str(type(phi)))
    return list(phi.get_free_variables())


def get_normalized(phi: FNode, converter) -> FNode:
    """Returns a normalized version of phi

    Args:
        phi (FNode): a pysmt formula

    Returns:
        FNode: the provided formula normalized according to the converter
    """
    if not isinstance(phi, FNode):
        raise TypeError("Expected FNode found " + str(type(phi)))
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
    if not isinstance(phi, FNode):
        raise TypeError("Expected FNode found " + str(type(phi)))
    if not isinstance(tlemmas, list):
        raise TypeError("Expected List found " + str(type(tlemmas)))
    if len(tlemmas) == 0:
        return phi
    for lemma in tlemmas:
        if not isinstance(lemma, FNode):
            raise TypeError("Expected FNode found " + str(type(lemma)))
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


def save_refinement(mapping: Dict[object, FNode], mapping_file: str) -> None:
    """
    Saves a mapping from objects to pysmt atoms in a file.
    This mapping is used to define the REFINEMENT function

    Args:
        mapping (Dict[object,FNode]) -> a mapping that associates to objects a pysmt atom
        mapping_file (str) -> the path to the file where the mapping file will be saved
    """

    # collect serialized mapping items
    mapping_items: List[Tuple[object, str]] = []
    for k, v in mapping.items():
        # serialize formula into SMTlib script and read it on a string stream
        script = _script_from_formula(v)
        output_stream = StringIO()
        script.serialize(output_stream)
        serialized_item = output_stream.getvalue()
        # add serialized item to list
        mapping_items.append((k, serialized_item))

    # write mapping_items in mapping file
    with open(mapping_file, "w", encoding="utf8") as out:
        json.dump(mapping_items, out)


def save_abstraction_function(mapping: Dict[FNode, object], mapping_file: str) -> None:
    """
    Saves a mapping from pysmt atoms to objects in a file.
    This mapping is used to define the ABSTRACTION function

    Args:
        mapping (Dict[FNode,object]) -> a mapping that associates to each pysmt atom an object
        mapping_file (str) -> the path to the file where the mapping file will be saved
    """
    # collect serialized mapping items
    mapping_items: List[Tuple[str, object]] = []
    for k, v in mapping.items():
        # serialize formula into SMTlib script and read it on a string stream
        script = _script_from_formula(k)
        output_stream = StringIO()
        script.serialize(output_stream)
        serialized_item = output_stream.getvalue()
        # add serialized item to list
        mapping_items.append((serialized_item, v))

    # write mapping_items in mapping file
    with open(mapping_file, "w", encoding="utf8") as out:
        json.dump(mapping_items, out)


def load_refinement(mapping_path: str) -> Dict[object, FNode]:
    """
    Loads a mapping from objects to pysmt atoms from a file.
    This mapping is used to define the REFINEMENT function

    Args:
        mapping_path (str) -> the path to the folder where the mapping is saved

    Returns:
        (Dict[object,FNode]) -> a mapping that associates to objects a pysmt atom
    """
    if not os.path.exists(mapping_path):
        raise FileNotFoundError(
            f"The path {mapping_path} does not exist. Please create it before loading the mapping."
        )

    mapping: Dict[object, FNode] = {}
    with open(mapping_path, "r", encoding="utf8") as input_data:
        mapping_items: List[Tuple[int, str]] = json.load(input_data)
        for item in mapping_items:
            key = item[0]
            serialized_formula = item[1]
            # read serialized formula from string stream
            input_stream = StringIO(serialized_formula)
            mapping[key] = _get_formula(input_stream)
    return mapping


def load_abstraction_function(mapping_path: str) -> Dict[FNode, object]:
    """
    Loads a mapping from pysmt atoms to objects from a file.
    This mapping is used to define the ABSTRACTION function

    Args:
        mapping_path (str) -> the path to the folder where the mapping is saved

    Returns:
        (Dict[FNode,object]) -> a mapping that associates to each pysmt atom an object
    """
    if not os.path.exists(mapping_path):
        raise FileNotFoundError(
            f"The path {mapping_path} does not exist. Please create it before loading the mapping."
        )

    mapping: Dict[FNode, object] = {}
    with open(mapping_path, "r", encoding="utf8") as input_data:
        mapping_items: List[Tuple[int, str]] = json.load(input_data)
        for item in mapping_items:
            key = item[1]
            serialized_formula = item[0]
            # read serialized formula from string stream
            input_stream = StringIO(serialized_formula)
            mapping[_get_formula(input_stream)] = key
    return mapping


def without_double_neg(phi: FNode) -> FNode:
    """removes all double negations from phi

    Args:
        phi (FNode): a pysmt formula

    Returns:
        FNode: the formula without double negations
    """
    walker = DoubleNegWalker()
    return walker.walk(phi)


def get_atom_partitioning(phi: FNode) -> List[Set[FNode]]:
    """partitions atoms into set

    phi must be a normalized formula or the partitioning may not be correct

    Args:
        phi (FNode): a pysmt formula
        skip_normalization (bool): if True, the formula is not normalized before partitioning

    Returns:
        List[Set[FNode]]: a list of sets of atoms that are in the same partition
    """
    atoms = get_atoms(phi)
    all_vars = phi.get_free_variables()
    if all_vars is None:
        # no free variables in the formula
        return [set(atoms)]

    # merge all variables that appear in the same atom
    disjoint_set_vars = DisjointSet(all_vars)
    # associate to each atom the first free variable that appears in it
    atoms_repr_vars: Dict[FNode, FNode] = {}
    theory_atoms = []
    for atom in atoms:
        atom_vars = list(atom.get_free_variables())

        # skip boolean atoms (that do not have free variables)
        if len(atom_vars) == 0:
            continue

        # add the atom to the theory_atoms list
        theory_atoms.append(atom)

        # associate to the atom a representative variable
        atoms_repr_vars[atom] = atom_vars[0]

        # join all variables that appear in the same atom
        for index, var_1 in enumerate(atom_vars):
            for var_2 in atom_vars[(index + 1) :]:
                disjoint_set_vars.union(var_1, var_2)
    # now all atoms have a find result on the disjoint set
    # which is disjoint_set_vars.find(atom.get_free_variables()[0])

    # merge atoms that share a variable
    disjoint_set_atoms = DisjointSet(theory_atoms)
    for index, atom_1 in enumerate(theory_atoms):
        # get repr for atom_1's first variable
        atom_1_repr = disjoint_set_vars.find(atoms_repr_vars[atom_1])
        for atom_2 in atoms[(index + 1) :]:
            # get repr for atom_2's first variable
            atom_2_repr = disjoint_set_vars.find(atoms_repr_vars[atom_2])
            # join atoms if they share the repr of disjoint_set_vars of their repr variable
            if atom_1_repr == atom_2_repr:
                disjoint_set_atoms.union(atom_1, atom_2)

    # get partitioning of theory atoms
    atoms_sets = list(disjoint_set_atoms.get_sets().values())

    # add singleton partition for all boolean atoms
    for atom in atoms:
        if atom not in theory_atoms:
            singleton_set = set()
            singleton_set.add(atom)
            atoms_sets.append(singleton_set)

    return atoms_sets

def get_true_given_atoms(atoms: Iterable[FNode]) -> FNode:
    """returns the formula that is True given the atoms

    Args:
        atoms (Iterable[FNode]): a set of pysmt atoms

    Returns:
        FNode: the formula that is always True given the atoms
    """
    if len(atoms) == 0:
        return _TRUE()
    big_and_items = []
    for atom in atoms:
        big_and_items.append(_Or(atom, _Not(atom)))
    return _And(*big_and_items)

def negate(phi: FNode) -> FNode:
    """returns the negation of phi

    Args:
        phi (FNode): a pysmt formula

    Returns:
        FNode: the negation of phi
    """
    return _Not(phi)

if __name__ == "__main__":
    phi_test = default_phi()
    data = get_atom_partitioning(phi_test)
    print(data)
