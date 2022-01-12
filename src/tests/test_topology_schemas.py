import json
from pathlib import Path

import jsonschema
import pytest
import yaml


@pytest.fixture()
def topology(filename):
    topology_file = Path(__file__).parent / f"data/{filename}"
    return yaml.safe_load(topology_file.read_text())


@pytest.fixture()
def topology_schema_file():
    """
    Returns the path to the topology schema file
    from evengsdk.schemas directory
    """
    return Path("src/evengsdk/schemas/lab-schema.json")


@pytest.fixture()
def schema(topology_schema_file):
    return json.loads(topology_schema_file.read_text())


@pytest.fixture()
def validator(schema):
    return jsonschema.Draft7Validator(schema=schema)


@pytest.mark.parametrize("filename", ["topology_missing_lab_name.yaml"])
def test_missing_lab_name_raises(topology, validator):
    """
    Verify topology schema is valid
    """
    with pytest.raises(jsonschema.exceptions.ValidationError) as e:
        validator.validate(topology)
    assert "'name' is a required property" in str(e.value)


@pytest.mark.parametrize("filename", ["topology_empty_lab_name.yaml"])
def test_null_lab_name_fails(topology, validator):
    """
    Verify topology schema is valid
    """
    with pytest.raises(jsonschema.exceptions.ValidationError):
        errors = validator.validate(topology)
        assert "is not of type" in errors
