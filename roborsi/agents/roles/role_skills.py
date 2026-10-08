"""Role-scoped agent skills.

Each role (planner, engineer, reviewer, manager) has procedural skills under
``roborsi/embodied/skills/agent/`` with ``role: <role>`` in their frontmatter;
``role: shared`` skills apply to every role. Their bodies are added to the
role's system prompt. Engineer *tools* are the base/atomic skills; these are
the procedures each role follows.
"""
from __future__ import annotations

import re

from roborsi.embodied import skills as skill_discovery

ROLES = ("planner", "engineer", "reviewer", "manager")


def skills_for_role(role: str) -> list:
    if role not in ROLES:
        raise ValueError(f"unknown role {role!r}; expected one of {ROLES}")
    found = [s for s in skill_discovery.discover()
             if (s.frontmatter or {}).get("kind") == "agent"
             and (s.frontmatter or {}).get("role") in ("shared", role)]
    # Shared rules first, then the role's own procedures.
    return sorted(found, key=lambda s: ((s.frontmatter or {}).get("role") != "shared", s.name))


def role_skill_text(role: str) -> str:
    sections = []
    for skill in skills_for_role(role):
        body = str(skill.body or "").strip()
        lines = body.splitlines()
        if lines and lines[0].startswith("# "):
            body = "\n".join(lines[1:]).strip()
        sections.append(f"## Skill: {skill.name}\n{re.sub(chr(10) * 3 + '+', chr(10) * 2, body)}")
    if not sections:
        return ""
    return "ROLE SKILLS (binding procedures for this role):\n\n" + "\n\n".join(sections)


def with_role_skills(role: str, system_prompt: str) -> str:
    text = role_skill_text(role)
    return f"{text}\n\n{system_prompt}" if text else system_prompt
