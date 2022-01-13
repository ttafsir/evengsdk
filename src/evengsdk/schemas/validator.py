import json
from pathlib import Path

from jsonschema import Draft7Validator


SCHEMAFILE = Path(__file__).parent / "lab-schema.json"


class SchemaValidator:
    def __init__(self):
        self.schema = json.loads(SCHEMAFILE.read_text())
        self.validator = Draft7Validator(schema=self.schema)

    def validate(self, topology: dict):
        return self.validator.validate(topology)
