import os
import json
import jsonschema


def for_schema(schema_name):
    return ParValidator(schema_name)


class ParValidationError(Exception):
    pass


class ParValidator():
    def __init__(self, schema_name):
        self.schema = None
        self.schema_dir = os.path.join(os.path.dirname(__file__),
                                       "par_schemas")

        schema_file = self.locate_schema(schema_name)

        if schema_file is None:
            raise Exception("Failed to find schema definition for '%s'" %
                            (schema_name))

        with open(schema_file, 'r') as f:
            self.schema = json.load(f)

        self.resolver = LocalResolver(self)

    def locate_schema(self, schema_name):
        for schema_file in os.listdir(self.schema_dir):
            basename, ext = os.path.splitext(schema_file)

            if ext == '.json' and basename == schema_name:
                return os.path.join(self.schema_dir, schema_file)

        return None

    def parse_and_validate(self, json_str):
        parsed = json.loads(json_str)

        try:
            jsonschema.validate(parsed, self.schema,
                                resolver=self.resolver)
            return parsed
        except jsonschema.ValidationError as e:
            raise e
            raise ParValidationError(e.message)


class LocalResolver(jsonschema.RefResolver):

    def __init__(self, validator):
        self.validator = validator
        jsonschema.RefResolver.__init__(self, 'file:' + validator.schema_dir,
                                        validator.schema)

    # Deal with a URL like https://example.com/path/to/something.json/#/some/subpath
    def resolve_from_url(self, url):
        segments = url.split('/')
        path = []
        while len(segments) > 0:
            segment = segments.pop()
            if segment.endswith('.json'):
                schema_name = os.path.splitext(segment)[0]
                return self._read_schema(schema_name, path)
            else:
                if segment != '#':
                    path.insert(0, segment)

        raise Exception("Failed to resolve URL: %s" % (url))

    def _read_schema(self, schema_name, path=[]):
        schema_file = self.validator.locate_schema(schema_name)

        if schema_file is None:
            raise Exception("Failed to find schema definition for '%s'" %
                            (schema_name))

        with open(schema_file, 'r') as f:
            tree = json.load(f)
            while len(path) > 0:
                tree = tree[path.pop(0)]

            return tree
