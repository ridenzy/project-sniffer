from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any


IgnoreConfig = dict[str, list[str]]


class ConfigurationError(ValueError):
    """Raised when an ignore configuration cannot be used safely."""


def _validate_ignore_config(
    data: Any,
    source: str,
) -> IgnoreConfig:
    if not isinstance(data, dict):
        raise ConfigurationError(
            f"{source} must contain a JSON object."
        )

    validated: IgnoreConfig = {
        "IGNORE_FOLDERS": [],
        "IGNORE_FILES": [],
    }

    for key in validated:
        value = data.get(
            key,
            [],
        )

        if not isinstance(
            value,
            list,
        ):
            raise ConfigurationError(
                f"{source}: {key} must be a list."
            )

        if not all(
            isinstance(
                item,
                str,
            )
            for item in value
        ):
            raise ConfigurationError(
                f"{source}: {key} must contain only strings."
            )

        validated[key] = list(
            value
        )

    return validated


def load_recommended_ignores() -> IgnoreConfig:
    resource = (
        files(
            "project_sniffer.resources"
        )
        .joinpath(
            "recommended_ignores.json"
        )
    )

    try:
        data = json.loads(
            resource.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        raise ConfigurationError(
            "Could not load packaged recommended "
            f"ignore rules: {error}"
        ) from error

    return _validate_ignore_config(
        data,
        "packaged recommended_ignores.json",
    )


def load_legacy_personal_ignores(
    working_directory: Path,
) -> IgnoreConfig:
    path = (
        working_directory
        / "personal_ignores.json"
    )

    if not path.is_file():
        return {
            "IGNORE_FOLDERS": [],
            "IGNORE_FILES": [],
        }

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        raise ConfigurationError(
            f"Could not load {path}: {error}"
        ) from error

    return _validate_ignore_config(
        data,
        str(path),
    )


def merge_ignore_configs(
    recommended: IgnoreConfig,
    personal: IgnoreConfig,
) -> IgnoreConfig:
    return {
        "IGNORE_FOLDERS": sorted(
            set(
                recommended[
                    "IGNORE_FOLDERS"
                ]
            )
            | set(
                personal[
                    "IGNORE_FOLDERS"
                ]
            )
        ),
        "IGNORE_FILES": sorted(
            set(
                recommended[
                    "IGNORE_FILES"
                ]
            )
            | set(
                personal[
                    "IGNORE_FILES"
                ]
            )
        ),
    }


def load_ignore_config(
    working_directory: Path,
) -> IgnoreConfig:
    """
    Load packaged recommended ignores plus the current legacy
    working-directory personal ignore file.

    The personal file is read only when it already exists.
    This function never creates or modifies it.
    """

    return merge_ignore_configs(
        load_recommended_ignores(),
        load_legacy_personal_ignores(
            working_directory
        ),
    )
