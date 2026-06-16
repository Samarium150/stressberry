import configparser
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_PYTHON_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]


def test_package_metadata_advertises_supported_python_versions():
    config = configparser.ConfigParser()
    config.read(PROJECT_ROOT / "setup.cfg")

    assert config["options"]["python_requires"] == ">=3.11"

    classifiers = {
        classifier.strip()
        for classifier in config["metadata"]["classifiers"].strip().splitlines()
    }
    assert "Programming Language :: Python :: 3.10" not in classifiers
    for version in ("3.7", "3.8", "3.9"):
        assert f"Programming Language :: Python :: {version}" not in classifiers
    for version in SUPPORTED_PYTHON_VERSIONS:
        assert f"Programming Language :: Python :: {version}" in classifiers

    install_requires = config["options"]["install_requires"].strip().splitlines()
    assert not any(
        requirement.startswith("importlib_metadata") for requirement in install_requires
    )


def test_ci_matrix_matches_advertised_python_versions():
    with open(PROJECT_ROOT / ".github" / "workflows" / "ci.yml") as workflow_file:
        workflow = yaml.safe_load(workflow_file)

    matrix = workflow["jobs"]["build"]["strategy"]["matrix"]["python-version"]
    assert [str(version) for version in matrix] == SUPPORTED_PYTHON_VERSIONS
