"""Module for constraints."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from typing_extensions import override
from z3 import BitVec, BoolRef

from .operator import Operator


class Constraint(ABC):
    @abstractmethod
    def __str__(self) -> str:
        """Representation of the constraint."""

    @abstractmethod
    def apply(self, terms: List[BitVec]) -> BoolRef:
        """Apply terms an BitVec Array."""

    @abstractmethod
    def check(self, secret: bytes) -> bool:
        """Check the password."""


@dataclass
class CompareConstraint(Constraint):
    """secret[0] == (secret[1] ^ 47)."""

    x: int
    y: int
    op: Operator
    n: int

    @override
    def __str__(self) -> str:
        return f"secret[{self.x}] == (secret[{self.y}] {self.op} {self.n})"

    @override
    def apply(self, terms: List[BitVec]) -> BoolRef:
        return terms[self.x] == self.op(terms[self.y], self.n)

    @override
    def check(self, secret: bytes) -> bool:
        return bool(secret[self.x] == self.op(secret[self.y], self.n) % 256)


@dataclass
class ConstantConstraint(Constraint):
    """6 == secret[0] ^ 47."""

    x: int
    k: int
    op: Operator
    n: int

    @override
    def __str__(self) -> str:
        return f"{self.k} == (secret[{self.x}] {self.op} {self.n})"

    @override
    def apply(self, terms: List[BitVec]) -> BoolRef:
        return self.op(terms[self.x], self.n) == self.k

    @override
    def check(self, secret: bytes) -> bool:
        return bool(self.op(secret[self.x], self.n) % 256 == self.k)


@dataclass
class OperationConstraint(Constraint):
    """secret[0] ^ secret[1] == 4."""

    x: int
    y: int
    op: Operator
    n: int

    @override
    def __str__(self) -> str:
        return f"(secret[{self.x}] {self.op} secret[{self.y}]) == {self.n}"

    @override
    def apply(self, terms: List[BitVec]) -> BoolRef:
        return self.op(terms[self.x], terms[self.y]) == self.n

    @override
    def check(self, secret: bytes) -> bool:
        return bool(self.op(secret[self.x], secret[self.y]) % 256 == self.n)
