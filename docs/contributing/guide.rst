.. _contributing:

Contributing to lynguine
========================

Thank you for considering a contribution to lynguine.

This project tracks design in ``cip/`` and work items in ``backlog/``. Substantial changes should start there (or as a GitHub issue) rather than as a surprise pull request.

How to contribute
-----------------

- Typo and small doc fixes: open a pull request.
- Bugs: open a GitHub issue with a title, what you expected, what happened, and a short snippet if you can.
- Features or architecture: write or update a CIP, or open an issue first so the design can be reviewed.
- Include tests for code changes. Run them with ``poetry run pytest``.
- Follow :doc:`style_guide`.

Pull requests
-------------

1. Branch from current ``main``.
2. Keep the change scoped to one issue or CIP.
3. Make sure CI status checks pass.
4. Reference the CIP or backlog item in the pull request.

The review may still ask for design, tests, or documentation before merge.

Where to look
-------------

- :doc:`setup` — Poetry development install
- :doc:`testing` — running the test suite
- :doc:`style_guide` — Ruff and PEP 8
- GitHub issues: https://github.com/lawrennd/lynguine/issues

Git commit messages
-------------------

- Present tense, imperative mood (``Add feature``, not ``Added feature``)
- First line 72 characters or less
- Reference issues, CIPs, or pull requests after the first line
