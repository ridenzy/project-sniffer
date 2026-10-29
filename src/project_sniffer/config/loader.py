from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any


IgnoreConfig = dict[str, list[str]]

_PERSONAL_REGISTRY_FILENAME = "personal_ignores.json"
_SUPPORTED_SCHEMA_VERSION = 1
_PROFILE_KEYS = {
    "ROOT_NAME",
    "ROOT_PATH",
    "IGNORE_FOLDERS",
    "IGNORE_FILES",
}


class ConfigurationError(ValueError):
    """Raised when an ignore configuration cannot be used safely."""


def empty_ignore_config() -> IgnoreConfig:
    return {
        "IGNORE_FOLDERS": [],
        "IGNORE_FILES": [],
    }


def _validate_ignore_config(
    data: Any,
    source: str,
) -> IgnoreConfig:
    if not isinstance(
        data,
        dict,
    ):
        raise ConfigurationError(
            f"{source} must contain a JSON object."
        )

    validated = empty_ignore_config()

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


def _read_json_file(
    path: Path,
) -> Any:
    try:
        return json.loads(
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


def get_personal_registry_path() -> Path:
    """
    Return the local private personal-registry path.

    The registry lives beside Project Sniffer's package resources but is not
    distributed as package data and must remain untracked.
    """

    return (
        Path(__file__)
        .resolve()
        .parent
        .parent
        / "resources"
        / _PERSONAL_REGISTRY_FILENAME
    )


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


def _optional_profile_string(
    profile: dict[str, Any],
    key: str,
    source: str,
) -> str | None:
    value = profile.get(
        key
    )

    if value is None:
        return None

    if not isinstance(
        value,
        str,
    ):
        raise ConfigurationError(
            f"{source}: {key} must be a string."
        )

    value = value.strip()

    if not value:
        raise ConfigurationError(
            f"{source}: {key} must not be empty."
        )

    return value


def _profile_match_specificity(
    *,
    profile_id: str,
    profile: dict[str, Any],
    project_path: Path,
    source: str,
) -> int | None:
    root_name = _optional_profile_string(
        profile,
        "ROOT_NAME",
        source,
    )

    root_path_value = (
        _optional_profile_string(
            profile,
            "ROOT_PATH",
            source,
        )
    )

    if root_path_value is not None:
        try:
            configured_root = (
                Path(
                    root_path_value
                )
                .expanduser()
                .resolve()
            )

        except (
            OSError,
            RuntimeError,
        ) as error:
            raise ConfigurationError(
                f"{source}: ROOT_PATH could not "
                f"be resolved: {error}"
            ) from error

        if configured_root != project_path:
            return None

        if (
            root_name is not None
            and root_name
            != project_path.name
        ):
            return None

        return (
            3
            if root_name is not None
            else 2
        )

    if root_name is not None:
        if root_name == project_path.name:
            return 1

        return None

    if profile_id == project_path.name:
        return 0

    return None


def _load_project_profile(
    *,
    registry: dict[str, Any],
    project_path: Path,
    source: str,
) -> IgnoreConfig:
    unexpected = sorted(
        set(
            registry
        )
        - {
            "schema_version",
            "projects",
        }
    )

    if unexpected:
        raise ConfigurationError(
            f"{source}: unsupported top-level keys: "
            + ", ".join(
                unexpected
            )
        )

    schema_version = registry.get(
        "schema_version"
    )

    if (
        type(
            schema_version
        )
        is not int
        or schema_version
        != _SUPPORTED_SCHEMA_VERSION
    ):
        raise ConfigurationError(
            f"{source}: schema_version must be "
            f"{_SUPPORTED_SCHEMA_VERSION}."
        )

    projects = registry.get(
        "projects"
    )

    if not isinstance(
        projects,
        dict,
    ):
        raise ConfigurationError(
            f"{source}: projects must be a JSON object."
        )

    matches: list[
        tuple[
            int,
            str,
            IgnoreConfig,
        ]
    ] = []

    for profile_id, raw_profile in projects.items():
        if (
            not isinstance(
                profile_id,
                str,
            )
            or not profile_id.strip()
        ):
            raise ConfigurationError(
                f"{source}: every project profile ID "
                "must be a non-empty string."
            )

        profile_source = (
            f"{source}: "
            f"projects[{profile_id!r}]"
        )

        if not isinstance(
            raw_profile,
            dict,
        ):
            raise ConfigurationError(
                f"{profile_source} must be a JSON object."
            )

        unexpected_profile_keys = sorted(
            set(
                raw_profile
            )
            - _PROFILE_KEYS
        )

        if unexpected_profile_keys:
            raise ConfigurationError(
                f"{profile_source}: unsupported keys: "
                + ", ".join(
                    unexpected_profile_keys
                )
            )

        ignore_config = (
            _validate_ignore_config(
                raw_profile,
                profile_source,
            )
        )

        specificity = (
            _profile_match_specificity(
                profile_id=profile_id,
                profile=raw_profile,
                project_path=project_path,
                source=profile_source,
            )
        )

        if specificity is not None:
            matches.append(
                (
                    specificity,
                    profile_id,
                    ignore_config,
                )
            )

    if not matches:
        return empty_ignore_config()

    highest = max(
        item[0]
        for item in matches
    )

    best = [
        item
        for item in matches
        if item[0] == highest
    ]

    if len(
        best
    ) != 1:
        profile_ids = ", ".join(
            repr(
                item[1]
            )
            for item in best
        )

        raise ConfigurationError(
            f"{source}: multiple personal profiles "
            f"match {project_path}: {profile_ids}"
        )

    return best[0][2]


def load_personal_ignores(
    *,
    project_path: Path,
    registry_path: Path | None = None,
) -> IgnoreConfig:
    """
    Load schema-version-1 personal ignores for one resolved target project.

    The local private registry is read-only from Project Sniffer's perspective:
    this function never creates or modifies it.
    """

    path = (
        registry_path
        if registry_path is not None
        else get_personal_registry_path()
    )

    if not path.is_file():
        return empty_ignore_config()

    data = _read_json_file(
        path
    )

    if not isinstance(
        data,
        dict,
    ):
        raise ConfigurationError(
            f"{path} must contain a JSON object."
        )

    if (
        "schema_version" not in data
        and "projects" not in data
    ):
        raise ConfigurationError(
            f"{path}: personal registry must use "
            "schema-version-1 per-project format."
        )

    return _load_project_profile(
        registry=data,
        project_path=project_path,
        source=str(
            path
        ),
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
    *,
    project_path: Path,
    personal_registry_path: Path | None = None,
) -> IgnoreConfig:
    """
    Build the effective ignore configuration for one target project.

    Current behavior is additive:

        packaged recommended ignores
        + matching local private personal ignores
    """

    return merge_ignore_configs(
        load_recommended_ignores(),
        load_personal_ignores(
            project_path=project_path,
            registry_path=(
                personal_registry_path
            ),
        ),
    )
