from __future__ import annotations

import ast


def direct_plain_base_name(
    class_node: ast.ClassDef,
) -> str | None:
    """
    Return the one direct plain-name base for a narrow inheritance shape.

    Multiple bases, class keywords, and non-name base expressions remain
    unsupported so callers can preserve positive-proof semantics.
    """

    if (
        class_node.keywords
        or len(class_node.bases) != 1
    ):
        return None

    base = class_node.bases[0]

    if not isinstance(
        base,
        ast.Name,
    ):
        return None

    return base.id
