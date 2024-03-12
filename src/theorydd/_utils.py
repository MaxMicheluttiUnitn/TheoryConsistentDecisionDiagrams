"""utility functions module"""

from pysmt.fnode import FNode
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
