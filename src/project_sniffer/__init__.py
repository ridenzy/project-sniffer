from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


_DISTRIBUTION_NAME = "project-sniffer"
_SOURCE_FALLBACK_VERSION = "0.2.0.dev0"


try:
    __version__ = version(
        _DISTRIBUTION_NAME
    )
except PackageNotFoundError:
    __version__ = (
        _SOURCE_FALLBACK_VERSION
    )


__all__ = [
    "__version__",
]
