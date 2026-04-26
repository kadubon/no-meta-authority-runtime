"""Effect tag checker."""

from __future__ import annotations

from no_meta_authority_runtime.checkers.base import CheckerResult, allow, deny, halt

DENIED_TAGS = {"externalWrite", "infoRelease", "delegation", "memoryWrite", "publicAction"}
HALT_TAGS = {"unknown", "checkerUpdate", "kernelUpdate"}


def check_no_external_effect(effect_tags: list[str]) -> CheckerResult:
    if HALT_TAGS & set(effect_tags):
        return halt("unknownOrUpdateEffect", {"effectTags": effect_tags})
    if DENIED_TAGS & set(effect_tags):
        return deny("externalEffectDenied", {"effectTags": effect_tags})
    return allow("noExternalEffect", {"effectTags": effect_tags})
