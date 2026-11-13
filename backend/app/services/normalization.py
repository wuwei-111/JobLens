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
    # Campus-recruiting snapshots describe disclosure status rather than years.
    # Keep the distinction instead of pretending "not disclosed" means "不限".
    "校招；未单独披露工作年限": "未披露",
    "校招/毕业生招聘；未单独披露工作年限": "未披露",
    "校招；明确要求最高学历毕业后无全职工作经验": "应届生",
    "校招；原文提及工作年限或工作经历，见经验原文": "其他",
}

# The city datasets were produced with two compatible taxonomies. Map the
# older/newer labels onto one 12-category vocabulary so merged charts do not
# show the same direction twice. Values not listed here are kept verbatim.
JOB_TYPE_ALIASES: dict[str, str] = {
    "算法与人工智能": "人工智能与算法",
    "其他软件与系统研发": "软件开发",
    "软件测试": "软件测试与测试开发",
    "嵌入式与移动开发": "嵌入式与系统软件",
    "运维与技术支持": "运维与基础设施",
    "网络与信息安全": "网络安全",
}

FRESH_GRADUATE_EXPERIENCE = "应届生"


def normalize_job_type(value: str) -> str:
    value = value.strip()
    return JOB_TYPE_ALIASES.get(value, value)


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
    "JOB_TYPE_ALIASES",
    "normalize_education",
    "normalize_experience",
    "normalize_job_type",
    "normalize_skills",
]
