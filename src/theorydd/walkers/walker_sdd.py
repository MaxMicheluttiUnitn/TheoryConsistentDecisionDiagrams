"""this module defines a Walker that takes a pysmt formula and converts it into a SDD formula"""

from collections import deque
from pysdd.sdd import SddManager
from pysmt.fnode import FNode
from pysmt.walkers import DagWalker, handles
import pysmt.operators as op
from theorydd.util.custom_exceptions import UnsupportedNodeException


class SDDWalker(DagWalker):
    """A walker to translate the DAG formula quickly with memoization into the SDD"""

    def __init__(
        self,
        mapping: dict[FNode, int],
        manager: SddManager,
        env=None,
        invalidate_memoization=False,
    ):
        DagWalker.__init__(self, env, invalidate_memoization)
        self.mapping = mapping
        self.manager = manager
        return

    def _apply_mapping(self, arg):
        """applies the mapping when possible, returns None otherwise"""
        if self.mapping.get(arg) is not None:
            return self.mapping[arg]
        return None

    def walk_and(self, formula: FNode, args, **kwargs):
        """translate AND node"""
        # pylint: disable=unused-argument
        if None in args:
            return
        nodes: deque = deque(args)
        while len(nodes) > 1:
            first = nodes.popleft()
            second = nodes.popleft()
            nodes.append(first & second)
        return nodes.popleft()

    def walk_or(self, formula: FNode, args, **kwargs):
        """translate OR node"""
        # pylint: disable=unused-argument
        if None in args:
            return
        nodes: deque = deque(args)
        while len(nodes) > 1:
            first = nodes.popleft()
            second = nodes.popleft()
            nodes.append(first | second)
        return nodes.popleft()

    def walk_not(self, formula: FNode, args, **kwargs):
        """translate NOT node"""
        # pylint: disable=unused-argument
        if None in args:
            return
        return ~args[0]

    def walk_symbol(self, formula: FNode, args, **kwargs):
        """translate SYMBOL node"""
        # pylint: disable=unused-argument
        return self._apply_mapping(formula)

    def walk_bool_constant(self, formula: FNode, args, **kwargs):
        """translate BOOL const node"""
        # pylint: disable=unused-argument
        value = formula.constant_value()
        if value:
            return self.manager.true()
        return self.manager.false()

    def walk_real_constant(self, formula: FNode, args, **kwargs):
        """translate REAl const node"""
        # pylint: disable=unused-argument
        return formula.constant_value()

    def walk_iff(self, formula, args, **kwargs):
        """translate IFF node"""
        # pylint: disable=unused-argument
        if None in args:
            return
        return (args[0] & args[1]) | ((~args[0]) & (~args[1]))

    def walk_implies(self, formula, args, **kwargs):
        """translate IMPLIES node"""  # a -> b === (~ a) v b
        # pylint: disable=unused-argument
        if None in args:
            return
        return (~args[0]) | args[1]

    def walk_ite(self, formula, args, **kwargs):
        """translate ITE node"""
        # pylint: disable=unused-argument
        if None in args:
            return
        return ((~args[0]) | args[1]) & (args[0] | args[2])

    def walk_forall(self, formula, args, **kwargs):
        """translate For-all node"""
        # pylint: disable=unused-argument
        raise UnsupportedNodeException("Quantifiers are yet to be supported")

    def walk_exists(self, formula, args, **kwargs):
        """translate Exists node"""
        # pylint: disable=unused-argument
        raise UnsupportedNodeException("Quantifiers are yet to be supported")

    @handles(
        *op.THEORY_OPERATORS,
        *op.BV_RELATIONS,
        *op.IRA_RELATIONS,
        *op.STR_RELATIONS,
        op.EQUALS,
        op.FUNCTION
    )
    def walk_theory(self, formula, args, **kwargs):
        """translate theory node"""
        # pylint: disable=unused-argument
        return self._apply_mapping(formula)

    @handles(op.REAL_CONSTANT, op.INT_CONSTANT, op.BV_CONSTANT)
    def do_nothing(self, formula, args, **kwargs):
        """do nothing when seeing theory constants"""
        # pylint: disable=unused-argument
        # they are not a valid T-atom by themselves, no need to perform any computation
        return
        # raise UnsupportedNodeException("Pure Theory Constant Found: "+str(formula))
