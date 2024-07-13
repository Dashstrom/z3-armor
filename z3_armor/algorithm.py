"""Generator for constraints."""

import builtins
import logging
import pathlib
import random
from typing import Iterator, List, Optional, Tuple, Union

from jinja2 import Environment, FileSystemLoader, Template
from z3 import BitVec, Solver, sat

from .constraint import (
    CompareConstraint,
    Constraint,
    OperationConstraint,
)
from .operator import OPERATORS, REVERSIBLE_OPERATORS

# Load jinja Environnement
HERE = pathlib.Path(__file__).parent.resolve()
TEMPLATES = HERE / "templates"

# Logging
logger = logging.getLogger(__name__)


class NoMoreConstraintError(RecursionError):
    """No constraints can be generated."""


class Z3Armor:
    def __init__(
        self,
        secret: bytes,
        random_state: Optional[int] = None,
    ) -> None:
        """Instantiated Z3Armor."""
        self.indexes = {i: 0 for i in range(len(secret))}
        self.constraints: List[Constraint] = []
        if random_state is not None:
            self.rand = random.Random(random_state)  # noqa: S311
        else:
            self.rand = random.SystemRandom()
        self.secret = secret

    def __str__(self) -> str:
        """Represent the ConstraintGenerator."""
        return (
            f"<ConstraintGenerator constraints={len(self.constraints)} "
            f"secret={self.secret!r}>"
        )

    def solver(self) -> Tuple[Solver, List[BitVec]]:
        """Create the solver."""
        solver = Solver()
        terms = [BitVec(f"p[{i}]", 8) for i in range(len(self.secret))]
        for const in self.constraints:
            solver.add(const.apply(terms))
        return solver, terms

    def verify(self, secret: bytes) -> bool:
        """Verify a password on the constraint generator."""
        return all(const.check(secret) for const in self.constraints)

    def complete(self) -> bool:
        """Check that the solver has a valid unique solution."""
        # Get the current solver
        solver, terms = self.solver()

        # Check if model is sat
        result = solver.check()
        if result != sat:
            logger.debug("No complete because model solver is %s", result)
            return False

        # Check if one of secret characters is None
        model = solver.model()
        solution = [model[c] for c in terms]
        if any(c is None for c in solution):
            logger.debug("No complete because some char are missing")
            return False

        # Check if first guess is the secret
        guess: Optional[bytes] = bytes(c.as_long() for c in solution)
        if guess != self.secret:
            logger.debug("No complete because first guess is wrong")
            return False

        # Check if there are only one guess
        guess = None
        for secret in self.solutions():
            if guess:
                logger.debug("No complete because other guess exist")
                return False
            guess = secret
        if guess is None:
            raise TypeError

        # All is ok so return True
        logger.debug("Complete")
        return True

    def solutions(self) -> Iterator[bytes]:
        """Find all solution for the currents constraints."""
        # ref: https://stackoverflow.com/questions/11867611/z3py-checking-all-solutions-for-equation
        # ref: https://theory.stanford.edu/%7Enikolaj/programmingz3.html#sec-blocking-evaluations
        solver, terms = self.solver()
        previous = set()

        def _all_smt_rec(terms: List[BitVec]) -> Iterator[bytes]:
            if sat == solver.check():
                model = solver.model()
                solution = [model[c] for c in terms]
                if all(c is not None for c in solution):
                    password = bytes(c.as_long() for c in solution)
                    if password not in previous:
                        previous.add(password)
                        yield password
                for i in range(len(terms)):
                    solver.push()
                    try:
                        solver.add(terms[i] != model.eval(terms[i]))
                        for j in range(i):
                            solver.add(terms[j] == model.eval(terms[j]))
                        yield from _all_smt_rec(terms[i:])
                    finally:
                        solver.pop()

        yield from _all_smt_rec(terms)

    def weights(self) -> List[float]:
        """Computes the weights of each index."""
        total = sum(count for count in self.indexes.values())
        if total == 0:
            return [1 / len(self.indexes)] * len(self.indexes)
        return [count / total for count in self.indexes.values()]

    def generate(self, rand: Optional[random.Random] = None) -> Constraint:
        """Generate a new constraint and it into the generator."""
        # Generate an temporary generator
        if rand is None:
            seed = self.rand.random()
            rand = random.Random(seed)  # noqa: S311

        used_indexes = []
        const: Constraint

        # Create first constraints
        if rand.randint(0, 1) == 0:
            x, y = self.weighted_sampling(rand, 2)
            used_indexes.append(x)
            used_indexes.append(y)
            rev_op = rand.choice(list(REVERSIBLE_OPERATORS.values()))
            n = rev_op.reverse(self.secret[y], self.secret[x]) % 256
            # Avoid linkage of the same letter
            if n == 0:
                try:
                    return self.generate(rand=rand)
                except RecursionError:
                    error_message = "No more constraint can be generated."
                    raise NoMoreConstraintError(error_message) from None
            const = CompareConstraint(x, y, rev_op, n)

        # Create a OperationConstraint
        else:
            x, y = self.weighted_sampling(rand, 2)
            used_indexes.append(x)
            used_indexes.append(y)
            op = rand.choice(list(OPERATORS.values()))
            n = op(self.secret[x], self.secret[y]) % 256
            const = OperationConstraint(x, y, op, n)

        # Regenerate already existing constants
        if const in self.constraints:
            try:
                return self.generate(rand=rand)
            except RecursionError:
                error_message = "No more constraint can be generated."
                raise NoMoreConstraintError(error_message) from None

        # Use index
        for i in used_indexes:
            self.indexes[i] += 1
        self.constraints.append(const)
        logger.info("Generate new constraint %s", const)
        return const

    def fit(self) -> None:
        """Make solver sat."""
        while not self.complete():
            try:
                self.generate()
            except NoMoreConstraintError:  # noqa: PERF203
                logger.info("No more constraints")
                break
        self.reduce()
        if not self.complete():
            error_message = "Model is not sat after reduce"
            raise RuntimeError(error_message)

    def weighted_sampling(
        self,
        rand: random.Random,
        k: int,
    ) -> List[int]:
        """Get index using sampling."""
        if k > len(self.indexes):
            error_message = "Not enough indexes."
            raise IndexError(error_message)
        indexes = self.indexes.copy()
        chosen = []
        for _ in range(k):
            max_count = max(indexes.values())
            if min(indexes.values()) == max_count:
                max_count += 1
            weights = [max_count - v for v in indexes.values()]
            (choose,) = rand.choices(
                list(indexes.keys()), k=1, weights=weights
            )
            chosen.append(choose)
            indexes.pop(choose)
        return chosen

    def reduce(self) -> None:
        """Minimize the number of constraints."""
        logger.info("Start reduction")
        start_size = len(self.constraints)
        while True:
            for constraint in self.constraints:
                self.constraints.remove(constraint)
                if self.complete():
                    break
                self.constraints.append(constraint)
            else:
                break
        logger.info(
            "Reduction result: %s to %s",
            start_size,
            len(self.constraints),
        )

    def format(self, name: str) -> str:
        """Format the algorithm with the premade template."""
        env = Environment(
            loader=FileSystemLoader(TEMPLATES),
            autoescape=False,  # noqa: S701
        )
        for variable in dir(builtins):
            if not variable.startswith("_"):
                env.globals[variable] = getattr(builtins, variable)
        template = env.get_template(name + ".j2")
        return self.format_from_template(template)

    def format_from_path(self, path: Union[str, pathlib.Path]) -> str:
        """Format the algorithm with template on filesystem."""
        path = pathlib.Path(path).resolve()
        env = Environment(
            loader=FileSystemLoader(path.parent),
            autoescape=False,  # noqa: S701
        )
        for name in dir(builtins):
            if not name.startswith("_"):
                env.globals[name] = getattr(builtins, name)
        template = env.get_template(path.name)
        return self.format_from_template(template)

    def format_from_template(self, template: Template) -> str:
        """Format the algorithm with the provided template."""
        return template.render(
            secret=self.secret,
            constraints=self.constraints,
            size=len(self.secret),
        )
