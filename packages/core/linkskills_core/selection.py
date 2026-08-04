"""Release selection helpers for compatible usable Skill Packs."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence


def _as_tag_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value} if value else set()
    if isinstance(value, Mapping):
        tags: set[str] = set()
        for key in ("tags", "runtime_profile_tags", "profile_id", "runtime_profile_id"):
            if key in value:
                tags |= _as_tag_set(value[key])
        return tags
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return {str(item) for item in value if item is not None and str(item)}
    return {str(value)}


def filter_compatible_usable_releases(
    releases: Iterable[Mapping[str, Any]],
    runtime_profile_tags: Sequence[str] | Mapping[str, Any] | str,
) -> list[dict[str, Any]]:
    """Return usable releases whose runtime profile tags intersect the actor profile tags.

    A release is compatible when:
    - ``lifecycle_state`` / ``certification_state`` is ``usable``
    - its declared runtime profile tags intersect the provided tags
    - if no runtime tags are declared on the release, it is treated as incompatible
      (fail closed) unless ``compatible_runtime_profiles`` contains ``*`` / ``any``
    """
    wanted = _as_tag_set(runtime_profile_tags)
    if not wanted:
        return []

    selected: list[dict[str, Any]] = []
    for release in releases:
        state = str(
            release.get("lifecycle_state")
            or release.get("certification_state")
            or ""
        ).strip()
        if state != "usable":
            continue

        declared = (
            _as_tag_set(release.get("compatible_runtime_profiles"))
            | _as_tag_set(release.get("runtime_profile_tags"))
            | _as_tag_set(release.get("runtime_profiles"))
        )
        if not declared:
            continue
        if declared & {"*", "any"}:
            selected.append(dict(release))
            continue
        if declared & wanted:
            selected.append(dict(release))
    return selected
