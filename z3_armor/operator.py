"""Base operator."""

import operator
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
)


@dataclass
class Operator:
    sign: str
    func: Callable[[Any, Any], Any]

    def __str__(self) -> str:
        """Represent the operator."""
        return self.sign

    def __call__(self, x: Any, y: Any) -> Any:
        """Call the current operator."""
        return self.func(x, y)


@dataclass
class ReversibleOperator(Operator):
    reverse: Callable[[Any, Any], Any]


OPERATORS = {
    o.sign: o
    for o in (
        Operator("+", operator.add),
        Operator("-", operator.sub),
        Operator("^", operator.xor),
        Operator("|", operator.or_),
        Operator("&", operator.and_),
        Operator("%", operator.mod),
        Operator("*", operator.mul),
    )
}

REVERSIBLE_OPERATORS = {
    o.sign: o
    for o in (
        ReversibleOperator("+", operator.add, lambda x, y: y - x),
        ReversibleOperator("-", operator.sub, lambda x, y: -(y - x)),
        ReversibleOperator("^", operator.xor, operator.xor),
    )
}
