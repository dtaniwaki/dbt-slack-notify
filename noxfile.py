"""Nox sessions for dbt-slack-notify."""

import nox

PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]

nox.options.default_venv_backend = "uv"


@nox.session(python=PYTHON_VERSIONS)
def test(session: nox.Session) -> None:
    session.install("-e", ".[dev]")
    session.run(
        "pytest",
        "--cov=dbt_slack_notify",
        "--cov-report=term-missing",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS[-1])
def lint(session: nox.Session) -> None:
    session.install("-e", ".[dev]")
    session.run("ruff", "check", "src/", "tests/")


@nox.session(python=PYTHON_VERSIONS[-1])
def typecheck(session: nox.Session) -> None:
    session.install("-e", ".[dev]")
    session.run("mypy")
