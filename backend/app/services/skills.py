"""Skill category dictionary.

The dictionary is intentionally small at the framework stage. The data team
should extend it together with the skill vocabulary in
``docs/data-dictionary.md``; otherwise many skills fall into ``其他``.
"""

from __future__ import annotations

SKILL_CATEGORIES: dict[str, str] = {
    # 编程语言
    "python": "编程语言",
    "java": "编程语言",
    "c++": "编程语言",
    "c": "编程语言",
    "c#": "编程语言",
    "go": "编程语言",
    "javascript": "编程语言",
    "typescript": "编程语言",
    "rust": "编程语言",
    "php": "编程语言",
    "kotlin": "编程语言",
    "swift": "编程语言",
    "scala": "编程语言",
    "r": "编程语言",
    "sql": "编程语言",
    "shell": "编程语言",
    # 开发框架
    "spring": "开发框架",
    "spring boot": "开发框架",
    "spring cloud": "开发框架",
    "django": "开发框架",
    "flask": "开发框架",
    "fastapi": "开发框架",
    "vue": "开发框架",
    "react": "开发框架",
    "angular": "开发框架",
    "node.js": "开发框架",
    "express": "开发框架",
    "mybatis": "开发框架",
    "netty": "开发框架",
    "gin": "开发框架",
    "unity": "开发框架",
    "flutter": "开发框架",
    # 前端技术
    "html/css": "前端技术",
    "微信小程序": "前端技术",
    "webpack": "前端技术",
    "vite": "前端技术",
    # 数据库
    "mysql": "数据库",
    "postgresql": "数据库",
    "oracle": "数据库",
    "sql server": "数据库",
    "数据库设计": "数据库",
    "mongodb": "数据库",
    "redis": "数据库",
    "sqlite": "数据库",
    "elasticsearch": "数据库",
    "clickhouse": "数据库",
    "hive": "数据库",
    # 工具与基础设施
    "git": "工具与平台",
    "linux": "工具与平台",
    "docker": "工具与平台",
    "kubernetes": "工具与平台",
    "jenkins": "工具与平台",
    "ci/cd": "工具与平台",
    "maven": "工具与平台",
    "gradle": "工具与平台",
    "nginx": "工具与平台",
    "kafka": "工具与平台",
    "rabbitmq": "工具与平台",
    "spark": "工具与平台",
    "hadoop": "工具与平台",
    "ffmpeg": "工具与平台",
    "postman": "工具与平台",
    "jmeter": "工具与平台",
    "pandas": "工具与平台",
    "数据可视化": "工具与平台",
    # 人工智能
    "机器学习": "人工智能",
    "深度学习": "人工智能",
    "pytorch": "人工智能",
    "tensorflow": "人工智能",
    "nlp": "人工智能",
    "计算机视觉": "人工智能",
    "大模型": "人工智能",
    "llm": "人工智能",
    "推荐系统": "人工智能",
    # 测试
    "自动化测试": "测试",
    "接口测试": "测试",
    "性能测试": "测试",
    "selenium": "测试",
    "pytest": "测试",
    "junit": "测试",
    "测试用例": "测试",
    # 计算机基础
    "数据结构": "计算机基础",
    "算法": "计算机基础",
    "计算机网络": "计算机基础",
    "操作系统": "计算机基础",
    "单片机": "计算机基础",
    "微服务": "计算机基础",
    "分布式": "计算机基础",
    "高并发": "计算机基础",
    "多线程": "计算机基础",
    # 安全
    "网络安全": "安全",
    "渗透测试": "安全",
    "密码学": "安全",
}

OTHER_CATEGORY = "其他"


def categorize_skill(skill: str) -> str:
    return SKILL_CATEGORIES.get(skill.strip().lower(), OTHER_CATEGORY)


__all__ = ["SKILL_CATEGORIES", "OTHER_CATEGORY", "categorize_skill"]
