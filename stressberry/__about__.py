from importlib import metadata

try:
    __version__ = metadata.version("stressberry")
except metadata.PackageNotFoundError:
    __version__ = "unknown"
