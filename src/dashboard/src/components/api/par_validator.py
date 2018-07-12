import os
import json
import jsonschema


def for_schema(schema_name):
    return ParValidator(schema_name)


class ParValidationError(Exception):
    pass


class ParValidator:
    def __init__(self, schema_uri):
        self.schema_dir = os.path.join(os.path.dirname(__file__), "par_schemas")

        par_schemas = self._load_par_schemas()
        print(par_schemas)
        self.schema = par_schemas[schema_uri]
        self.resolver = jsonschema.RefResolver(
            "file:" + self.schema_dir, self.schema, store=par_schemas
        )

    def _load_par_schemas(self):
        result = {}

        for schema_file in os.listdir(self.schema_dir):
            if not schema_file.endswith(".json"):
                continue

            with open(os.path.join(self.schema_dir, schema_file), "r") as f:
                schema = json.load(f)
                uri = "http://www.parcore.org/schema/" + schema_file + "/"
                result[uri] = schema

        return result

    def parse_and_validate(self, json_str):
        parsed = json.loads(json_str)

        try:
            jsonschema.validate(parsed, self.schema, resolver=self.resolver)
            return parsed
        except jsonschema.ValidationError as e:
            raise ParValidationError(e.message)
