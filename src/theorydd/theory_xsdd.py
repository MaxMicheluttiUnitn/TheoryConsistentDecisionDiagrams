"""XSDD generation module"""

from typing import Dict
from pysmt.fnode import FNode
from pysmt.shortcuts import BOOL, REAL, INT
from pywmi.domain import Domain

import theorydd.formula as _formula
from theorydd.walker_xsdd import XsddParser
from theorydd.custom_exceptions import UnsupportedSymbolException


class TheoryXSDD:
    """class to build and handle XSDDs"""

    domain: Domain
    support: FNode

    def __init__(self, phi: FNode, computation_logger: Dict = None):
        if computation_logger is None:
            computation_logger = {}
        if computation_logger.get("XSDD") is None:
            computation_logger["XSDD"] = {}

        symbols = _formula.get_symbols(phi)
        boolean_symbols = []
        real_symbols = []

        for symbol in symbols:
            if symbol.get_type() == BOOL:
                boolean_symbols.append("xsdd_" + str(symbol))
            elif symbol.get_type() == REAL:
                real_symbols.append("xsdd_" + str(symbol))
            elif symbol.get_type() == INT:
                real_symbols.append("xsdd_" + str(symbol))
            else:
                raise UnsupportedSymbolException(
                    "Unsupported symbol by XSDD: " + str(symbol)
                )

        # bounds are necesssary (XSDD are designed for WMI), so I just put them very big
        self.domain = Domain.make(
            boolean_symbols, real_symbols, real_bounds=(-1000000, 1000000)
        )

        xsdd_boolean_symbols = self.domain.get_bool_symbols()
        xsdd_real_symbols = self.domain.get_real_symbols()

        walker = XsddParser(
            boolean_symbols, xsdd_boolean_symbols, real_symbols, xsdd_real_symbols
        )
        self.support: FNode = walker.walk(phi)
