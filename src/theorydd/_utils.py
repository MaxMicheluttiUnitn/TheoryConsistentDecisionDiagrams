"""utility functions module"""

import pickle
from pysmt.fnode import FNode
from dd import cudd as cudd_bdd
from theorydd.constants import VALID_SOLVER


def is_valid_solver(solver: str) -> bool:
    """Checks if the provided solver name is valid
    
    Args:
        solver (str): the type of solver
    
    Returns:
        bool: True if the solver is valid, False otherwise
    """
    return solver in VALID_SOLVER


def get_string_from_atom(atom:FNode) -> str:
    """Changes special characters into ASCII encoding"""
    # svg format special characters source:
    # https://rdrr.io/cran/RSVGTipsDevice/man/encodeSVGSpecialChars.html
    atom_str = (
        str(atom)
        .replace("&", "&#38;")
        .replace("'", "&#30;")
        .replace('"', "&#34;")
        .replace("<", "&#60;")
        .replace(">", "&#62;")
    )
    if atom_str.startswith("("):
        return atom_str[1 : len(atom_str) - 1]
    return atom_str

def cudd_load(file_name: str, bdd: cudd_bdd.BDD) -> cudd_bdd.Function:
    """Unpickle variable order and load dddmp file.

    Loads the variable order,
    reorders `bdd` to match that order,
    turns off reordering,
    then loads the BDD,
    restores reordering.
    Assumes that:

      - `file_name` has no extension
      - pickle file name: `file_name.pickle`
      - dddmp file name: `file_name.dddmp`

    @param reordering:
        if `True`,
        then enable reordering during DDDMP load.
    """
    pickle_fname = f"{file_name}.pickle"
    dddmp_fname = f"{file_name}.dddmp"
    with open(pickle_fname, "rb") as f:
        d = pickle.load(f)
    order = d["variable_order"]
    for var in order:
        bdd.add_var(var)
    cudd_bdd.reorder(bdd, order)
    cfg = bdd.configure(reordering=False)
    u = bdd.load(dddmp_fname)
    bdd.configure(reordering=cfg["reordering"])
    return u[0]


def cudd_dump(root: object, file_name: str) -> None:
    """Pickle variable order and dump dddmp file."""
    bdd = root.bdd
    pickle_fname = f"{file_name}.pickle"
    dddmp_fname = f"{file_name}.dddmp"
    order = {var: bdd.level_of_var(var) for var in bdd.vars}
    d = dict(variable_order=order)
    with open(pickle_fname, "wb") as f:
        pickle.dump(d, f, protocol=2)
    bdd.dump(dddmp_fname, [root])