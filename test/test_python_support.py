from pathlib import Path
import tomllib

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_PYTHON_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]


def load_pyproject():
    return tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())


def test_project_metadata_lives_in_pyproject():
    pyproject = load_pyproject()
    project = pyproject["project"]

    assert project["name"] == "stressberry"
    assert project["version"] == "0.3.3"
    assert project["requires-python"] == ">=3.11"
    assert project["readme"] == "README.md"
    assert project["license"] == "GPL-3.0-or-later"
    assert project["dependencies"] == ["matplotlib", "matplotx", "pyyaml"]
    assert project["scripts"] == {
        "stressberry-run": "stressberry.cli:run",
        "stressberry-plot": "stressberry.cli:plot",
    }


def test_package_metadata_advertises_supported_python_versions():
    pyproject = load_pyproject()
    classifiers = set(pyproject["project"]["classifiers"])

    assert "Programming Language :: Python :: 3.10" not in classifiers
    for version in ("3.7", "3.8", "3.9"):
        assert f"Programming Language :: Python :: {version}" not in classifiers
    for version in SUPPORTED_PYTHON_VERSIONS:
        assert f"Programming Language :: Python :: {version}" in classifiers

    install_requires = pyproject["project"]["dependencies"]
    assert not any(
        requirement.startswith("importlib_metadata")
        for requirement in install_requires
    )


def test_ci_matrix_matches_advertised_python_versions():
    with open(
        PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    ) as workflow_file:
        workflow = yaml.safe_load(workflow_file)

    matrix = workflow["jobs"]["build"]["strategy"]["matrix"]["python-version"]
    assert [str(version) for version in matrix] == SUPPORTED_PYTHON_VERSIONS


def test_uv_manages_development_tooling():
    pyproject = load_pyproject()

    assert (PROJECT_ROOT / "uv.lock").is_file()
    assert not (PROJECT_ROOT / "setup.cfg").exists()
    assert not (PROJECT_ROOT / "Makefile").exists()

    dependency_groups = pyproject["dependency-groups"]
    assert dependency_groups["test"] == ["pytest", "pytest-cov"]
    assert dependency_groups["lint"] == ["ruff"]
    assert {"include-group": "test"} in dependency_groups["dev"]
    assert {"include-group": "lint"} in dependency_groups["dev"]
    assert "build" not in dependency_groups

    build_system = pyproject["build-system"]
    assert build_system["build-backend"] == "setuptools.build_meta"
    assert build_system["requires"] == ["setuptools>=77", "wheel"]


def test_ruff_config_lives_in_pyproject():
    pyproject = load_pyproject()

    assert not (PROJECT_ROOT / ".flake8").exists()
    assert pyproject["tool"]["ruff"]["line-length"] == 80
    assert pyproject["tool"]["ruff"]["lint"]["select"] == [
        "B",
        "C",
        "E",
        "F",
        "W",
    ]


def test_uv_workflows_are_documented_without_make_or_publish_automation():
    readme = (PROJECT_ROOT / "README.md").read_text()
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    pyproject = load_pyproject()

    for command in (
        "uv sync --locked",
        "uv run ruff format --check .",
        "uv run ruff check .",
        "uv run pytest",
        "uv build",
    ):
        assert command in readme

    assert "make " not in readme.lower()
    assert "twine" not in workflow
    assert "pypi" not in workflow.lower()
    assert "publish" not in workflow.lower()
    assert "upload" not in workflow.lower()

    all_group_requirements = [
        requirement
        for requirements in pyproject["dependency-groups"].values()
        for requirement in requirements
        if isinstance(requirement, str)
    ]
    assert "twine" not in all_group_requirements
