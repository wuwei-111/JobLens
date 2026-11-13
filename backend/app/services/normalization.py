"""Value normalization used during import.

The goal is a small, explainable canonical vocabulary — not an exhaustive
NLP pipeline. Any value outside the vocabulary is kept verbatim and surfaced
in statistics as-is, so nothing is silently rewritten.
"""

from __future__ import annotations

from collections.abc import Iterable

EDUCATION_ALIASES: dict[str, str] = {
    "学历不限": "不限",
    "不限学历": "不限",
    "无要求": "不限",
    "专科": "大专",
    "大学专科": "大专",
    "大专及以上": "大专",
    "大学本科": "本科",
    "统招本科": "本科",
    "本科及以上学历": "本科及以上",
    "本科以上": "本科及以上",
    "研究生": "硕士",
    "硕士研究生": "硕士",
    "硕士及以上": "硕士及以上",
    "博士研究生": "博士",
}

EXPERIENCE_ALIASES: dict[str, str] = {
    "经验不限": "不限",
    "无经验要求": "不限",
    "无工作经验要求": "不限",
    "应届毕业生": "应届生",
    "应届": "应届生",
    "在校/应届": "应届生",
    "1年以内": "1年以内",
    "一年以内": "1年以内",
    "1-3年": "1-3年",
    "1~3年": "1-3年",
    "3-5年": "3-5年",
    "3~5年": "3-5年",
    "5年以上": "5年以上",
    "五年以上": "5年以上",
}

FRESH_GRADUATE_EXPERIENCE = "应届生"


def normalize_education(value: str) -> str:
    value = value.strip()
    return EDUCATION_ALIASES.get(value, value)


def normalize_experience(value: str) -> str:
    value = value.strip()
    return EXPERIENCE_ALIASES.get(value, value)


def normalize_skills(skills: Iterable[str]) -> list[str]:
    """Trim, deduplicate case-insensitively and keep the first spelling."""
    seen: set[str] = set()
    result: list[str] = []
    for raw in skills:
        skill = raw.strip()
        if not skill:
            continue
        key = skill.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(skill)
    return result


__all__ = [
    "EDUCATION_ALIASES",
    "EXPERIENCE_ALIASES",
    "FRESH_GRADUATE_EXPERIENCE",
    "normalize_education",
    "normalize_experience",
    "normalize_skills",
]
