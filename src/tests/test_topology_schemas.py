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


@pytest.mark.parametrize("filename", ["topology_lab_tests.yaml"])
def test_missing_lab_name_raises(topology, validator):
    """
    Verify topology schema is valid
    """
    test_topology = topology["missing_lab_name"]
    with pytest.raises(jsonschema.exceptions.ValidationError) as e:
        validator.validate(test_topology)
    assert "'name' is a required property" in str(e.value)


@pytest.mark.parametrize("filename", ["topology_lab_tests.yaml"])
def test_null_lab_name_fails(topology, validator):
    """
    Verify topology schema is valid
    """
    test_topology = topology["empty_lab_name"]
    with pytest.raises(jsonschema.exceptions.ValidationError) as e:
        validator.validate(test_topology)
    assert "is not of type" in str(e.value)


@pytest.mark.parametrize("filename", ["topology_node_tests.yaml"])
def test_missing_node_name_raises(topology, validator):
    """
    Verify topology schema is valid
    """
    test_topology = topology["missing_node_name"]
    with pytest.raises(jsonschema.exceptions.ValidationError) as e:
        validator.validate(test_topology)
    assert "'name' is a required property" in str(e.value)
    assert "'required' in schema['properties']['nodes']['items']" in str(e.value)


@pytest.mark.parametrize("filename", ["topology_node_tests.yaml"])
def test_missing_node_template_raises(topology, validator):
    """
    Verify topology schema is valid
    """
    test_topology = topology["missing_node_template"]
    with pytest.raises(jsonschema.exceptions.ValidationError) as e:
        validator.validate(test_topology)
    assert "'template' is a required property" in str(e.value)
    assert "'required' in schema['properties']['nodes']['items']" in str(e.value)


@pytest.mark.parametrize("filename", ["topology_node_tests.yaml"])
def test_missing_node_image_raises(topology, validator):
    """
    Verify topology schema is valid
    """
    test_topology = topology["missing_node_image"]
    with pytest.raises(jsonschema.exceptions.ValidationError) as e:
        validator.validate(test_topology)
    assert "'image' is a required property" in str(e.value)
    assert "'required' in schema['properties']['nodes']['items']" in str(e.value)


@pytest.mark.parametrize("filename", ["topology_node_tests.yaml"])
def test_node_config_null_raises(topology, validator):
    """
    Verify topology schema is valid
    """
    test_topology = topology["node_config_is_null"]
    with pytest.raises(jsonschema.exceptions.ValidationError) as e:
        validator.validate(test_topology)
    assert "None is not valid under any of the given schemas" in str(e.value)
    assert "On instance['nodes'][0]['configuration']" in str(e.value)


@pytest.mark.parametrize("filename", ["topology_node_tests.yaml"])
def test_node_config_invalid_type_raises(topology, validator):
    """
    Verify topology schema is valid
    """
    test_topology = topology["invalid_node_type"]
    with pytest.raises(jsonschema.exceptions.ValidationError) as e:
        validator.validate(test_topology)
    assert "None is not valid under any of the given schemas" in str(e.value)
