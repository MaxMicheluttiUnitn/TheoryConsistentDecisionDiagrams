"""this module defines a Walker that takes a pysmt formula and converts it into an XSDD support"""

from typing import List
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker, handles
import pysmt.operators as op

from theorydd.util.custom_exceptions import UnsupportedNodeException


class XsddParser(DagWalker):
    """A walker to translate the DAG formula quickly with memoization into an XSDD compatible formula"""

    def __init__(
        self,
        bool_source: list,
        bool_dest: list,
        real_source: list,
        real_dest: list,
        env=None,
        invalidate_memoization=False,
    ):
        DagWalker.__init__(self, env, invalidate_memoization)
        self.bool_source = bool_source
        self.bool_dest = bool_dest
        self.real_source = real_source
        self.real_dest = real_dest
        return

    def _apply_mapping(self, arg: FNode, is_bool: bool):
        """applies the mapping when possible, returns None othrwise"""
        if is_bool:
            item_id = self.bool_source.index("xsdd_" + str(arg))
            return self.bool_dest[item_id]
        item_id = self.real_source.index("xsdd_" + str(arg))
        return self.real_dest[item_id]

    def walk_and(self, formula: FNode, args, **kwargs):
        """translate AND node"""
        # pylint: disable=unused-argument
        nodes: List = list(args)
        while len(nodes) > 1:
            first = nodes.pop(0)
            second = nodes.pop(0)
            nodes.append(first & second)
        return nodes[0]

    def walk_or(self, formula: FNode, args, **kwargs):
        """translate OR node"""
        # pylint: disable=unused-argument
        nodes: List = list(args)
        while len(nodes) > 1:
            first = nodes.pop(0)
            second = nodes.pop(0)
            nodes.append(first | second)
        return nodes[0]

    def walk_not(self, formula: FNode, args, **kwargs):
        """translate NOT node"""
        # pylint: disable=unused-argument
        return ~args[0]

    def walk_symbol(self, formula: FNode, args, **kwargs):
        """translate SYMBOL node"""
        # pylint: disable=unused-argument
        if str(formula.get_type()) == "Bool":
            return self._apply_mapping(formula, True)
        return self._apply_mapping(formula, False)

    def walk_bool_constant(self, formula: FNode, args, **kwargs):
        """translate BOOL const node"""
        # pylint: disable=unused-argument
        value = formula.constant_value()
        if value:
            return True
        return False

    def walk_iff(self, formula, args, **kwargs):
        """translate IFF node"""
        # pylint: disable=unused-argument
        return (args[0] & args[1]) | ((~args[0]) & (~args[1]))

    def walk_implies(self, formula, args, **kwargs):
        """translate IMPLIES node"""  # a -> b === (~ a) v b
        # pylint: disable=unused-argument
        return (~args[0]) | args[1]

    def walk_ite(self, formula, args, **kwargs):
        """translate ITE node"""
        # pylint: disable=unused-argument
        return ((~args[0]) | args[1]) & (args[0] | args[2])

    def walk_forall(self, formula, args, **kwargs):
        """translate For-all node"""
        # pylint: disable=unused-argument
        raise UnsupportedNodeException("Quantifiers are yet to be supported")

    def walk_exists(self, formula, args, **kwargs):
        """translate Exists node"""
        # pylint: disable=unused-argument
        raise UnsupportedNodeException("Quantifiers are yet to be supported")

    def walk_equals(self, formula, args, **kwargs):
        """translate equals relation"""
        # pylint: disable=unused-argument
        return ~((args[0] > args[1]) | (args[1] > args[0]))

    def walk_plus(self, formula, args, **kwargs):
        """translate Plus node"""
        # pylint: disable=unused-argument
        if len(args) == 1:
            return args[0]
        res = args[0]
        for i in range(1, len(args)):
            res = res + args[i]
        return res

    @handles(op.MINUS)
    def walk_minus(self, formula, args, **kwargs):
        """translate Minus node"""
        # pylint: disable=unused-argument
        if len(args) == 1:
            return -args[0]
        res = args[0]
        for i in range(1, len(args)):
            res = res - args[i]
        return res

    @handles(op.TIMES)
    def walk_times(self, formula, args, **kwargs):
        """translate Plus node"""
        # pylint: disable=unused-argument
        if len(args) == 1:
            return args[0]
        res = args[0]
        for i in range(1, len(args)):
            res = res * args[i]
        return res

    @handles(op.DIV)
    def walk_div(self, formula, args, **kwargs):
        """translate Plus node"""
        # pylint: disable=unused-argument
        if len(args) == 1:
            return args[0]
        res = args[0]
        for i in range(1, len(args)):
            res = res / args[i]
        return res

    @handles(op.LE)
    def walk_le(self, formula, args, **kwargs):
        """translate LE node"""
        # pylint: disable=unused-argument
        return args[0] <= args[1]

    @handles(op.LT)
    def walk_lt(self, formula, args, **kwargs):
        """translate LT node"""
        # pylint: disable=unused-argument
        return args[0] < args[1]

    @handles(op.REAL_CONSTANT, op.INT_CONSTANT)
    def walk_numeric_constant(self, formula, args, **kwargs):
        """translate real constant node"""
        # pylint: disable=unused-argument
        return formula.constant_value()

    @handles(
        *op.BV_OPERATORS,
        *op.BV_RELATIONS,
        *op.STR_OPERATORS,
        *op.STR_RELATIONS,
        *op.ARRAY_OPERATORS
    )
    def walk_theory(self, formula, args, **kwargs):
        """translate theory node"""
        # pylint: disable=unused-argument
        return None
