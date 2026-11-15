"""Strict, schema-first inventory boundary (seam 8 RED entry points)."""


class ManifestError(ValueError):
    """A rejected manifest; never treat invalid input as an empty inventory."""


def parse_manifest(data):
    return None


def load_manifest(path):
    raise ManifestError("manifest validation is not implemented")
