.. role:: bash(code)
  :language: bash

********
Z3 Armor
********

|ci-docs| |ci-lint| |ci-tests| |pypi| |versions| |discord| |license|

.. |ci-docs| image:: https://github.com/Dashstrom/z3-armor/actions/workflows/docs.yml/badge.svg
  :target: https://github.com/Dashstrom/z3-armor/actions/workflows/docs.yml
  :alt: CI : Docs

.. |ci-lint| image:: https://github.com/Dashstrom/z3-armor/actions/workflows/lint.yml/badge.svg
  :target: https://github.com/Dashstrom/z3-armor/actions/workflows/lint.yml
  :alt: CI : Lint

.. |ci-tests| image:: https://github.com/Dashstrom/z3-armor/actions/workflows/tests.yml/badge.svg
  :target: https://github.com/Dashstrom/z3-armor/actions/workflows/tests.yml
  :alt: CI : Tests

.. |pypi| image:: https://img.shields.io/pypi/v/z3-armor.svg
  :target: https://pypi.org/project/z3-armor
  :alt: PyPI : z3-armor

.. |versions| image:: https://img.shields.io/pypi/pyversions/z3-armor.svg
  :target: https://pypi.org/project/z3-armor
  :alt: Python : versions

.. |discord| image:: https://img.shields.io/badge/Discord-dashstrom-5865F2?style=flat&logo=discord&logoColor=white
  :target: https://dsc.gg/dashstrom
  :alt: Discord

.. |license| image:: https://img.shields.io/badge/license-MIT-green.svg
  :target: https://github.com/Dashstrom/z3-armor/blob/main/LICENSE
  :alt: License : MIT

Description
###########

Constraint-based obfuscation using z3.

Documentation
#############

Documentation is available on https://dashstrom.github.io/z3-armor

Installation
############

You can install :bash:`z3-armor` using `pipx <https://pipx.pypa.io/stable/>`_
from `PyPI <https://pypi.org/project>`_

..  code-block:: bash

  pip install pipx
  pipx ensurepath
  pipx install z3-armor

Usage
#####

Generate C challenge
********************

..  code-block:: bash

  z3-armor --template crackme.c -p 'CTF{flag}' -s 0 -o chall.c
  gcc -o chall -fno-stack-protector -O0 chall.c
  ./chall
  password: CTF{flag}
  Valid password ┬─┬ ~( º-º~)

..  code-block:: c

  #include <stdio.h>
  #include <stdlib.h>
  #include <sys/types.h>
  #include <string.h>

  #define SIZE 9

  typedef unsigned char uc;
  static const char INVALID_PASSWORD[] = "Invalid password (\u256f\u00b0\u25a1\u00b0)\u256f \u253b\u2501\u253b\n";
  static const char VALID_PASSWORD[] = "Valid password \u252c\u2500\u252c ~( \u00ba-\u00ba~)\n";

  int main();

  int main() {
    char secret[SIZE + 1];
    printf("password: ");
    fgets(secret, SIZE + 1, stdin);
    secret[strcspn(secret, "\r\n")] = 0;
    size_t length = strlen(secret);
    if (length != SIZE) {
      printf(INVALID_PASSWORD);
      return 1;
    }
    if (
      (uc)(secret[1] ^ secret[4]) == 50
      && (uc)(secret[5] * secret[3]) == 228
      && secret[6] == (uc)(secret[3] + 230)
      && secret[7] == (uc)(secret[2] - 223)
      && (uc)(secret[7] - secret[8]) == 234
      && secret[7] == (uc)(secret[0] - 220)
      && (uc)(secret[8] ^ secret[1]) == 41
      && secret[6] == (uc)(secret[2] - 229)
      && (uc)(secret[4] + secret[0]) == 169
      && secret[8] == (uc)(secret[5] + 17)
    ) {
      printf(VALID_PASSWORD);
    } else {
      printf(INVALID_PASSWORD);
    }
    return 0;
  }

Generate Python Solution
************************

..  code-block:: bash

  z3-armor --template solver.py -p 'CTF{flag}' -s 0 -o solve.py
  python3 solve.py
  b'CTF{flag}'

..  code-block:: python

  """Solver for challenge."""
  from z3 import BitVec, Solver, sat


  def solve() -> None:
      """Solve challenge using z3."""
      p = [BitVec(f"p[{i}]", 8) for i in range(9)]
      s = Solver()
      s.add((p[1] ^ p[4]) == 50)
      s.add((p[5] * p[3]) == 228)
      s.add(p[6] == (p[3] + 230))
      s.add(p[7] == (p[2] - 223))
      s.add((p[7] - p[8]) == 234)
      s.add(p[7] == (p[0] - 220))
      s.add((p[8] ^ p[1]) == 41)
      s.add(p[6] == (p[2] - 229))
      s.add((p[4] + p[0]) == 169)
      s.add(p[8] == (p[5] + 17))
      if s.check() != sat:
          print("Cannot find secret.")
          return
      model = s.model()
      solutions = [model[c] for c in p]
      flag = bytes(s.as_long() for s in solutions)
      print(flag)

  if __name__ == "__main__":
      solve()

Development
###########

Contributing
************

Contributions are very welcome. Tests can be run with :bash:`poe check`, please
ensure the coverage at least stays the same before you submit a pull request.

Setup
*****

You need to install `Poetry <https://python-poetry.org/docs/#installation>`_
and `Git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_
for work with this project.

..  code-block:: bash

  git clone https://github.com/Dashstrom/z3-armor
  cd z3-armor
  poetry install --all-extras
  poetry run poe setup
  poetry shell

Poe
********

Poe is available for help you to run tasks.

..  code-block:: text

  test           Run test suite.
  lint           Run linters: ruff linter, ruff formatter and mypy.
  format         Run linters in fix mode.
  check          Run all checks: lint, test and docs.
  cov            Run coverage for generate report and html.
  open-cov       Open html coverage report in webbrowser.
  docs           Build documentation.
  open-docs      Open documentation in webbrowser.
  setup          Setup pre-commit.
  pre-commit     Run pre-commit.
  clean          Clean cache files

Skip commit verification
************************

If the linting is not successful, you can't commit.
For forcing the commit you can use the next command :

..  code-block:: bash

  git commit --no-verify -m 'MESSAGE'

Commit with commitizen
**********************

To respect commit conventions, this repository uses
`Commitizen <https://github.com/commitizen-tools/commitizen?tab=readme-ov-file>`_.

..  code-block:: bash

  cz c

How to add dependency
*********************

..  code-block:: bash

  poetry add 'PACKAGE'

Ignore illegitimate warnings
****************************

To ignore illegitimate warnings you can add :

- **# noqa: ERROR_CODE** on the same line for ruff.
- **# type: ignore[ERROR_CODE]** on the same line for mypy.
- **# pragma: no cover** on the same line to ignore line for coverage.
- **# doctest: +SKIP** on the same line for doctest.

Uninstall
#########

..  code-block:: bash

  pipx uninstall z3-armor

License
#######

This work is licensed under `MIT <https://github.com/Dashstrom/z3-armor/blob/main/LICENSE>`_.
