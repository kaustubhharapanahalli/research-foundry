---
type: ADR
title: "ADR 0010: Python 3.12 Support Floor"
description: Why research-foundry and generated projects support Python 3.12 and newer while keeping the selected interpreter separate.
resource: /docs/adr/0010-python-floor.md
tags: [adr, python, compatibility, tooling, continuous-integration]
timestamp: 2026-10-02T00:00:00Z
status: accepted
---

# ADR 0010: Python 3.12 support floor

## Context

Python versions in project metadata and development-tool configuration define
the oldest syntax and standard-library features that code may use. The
interpreter selected for local development, containers and documentation is a
separate concern: it can use the newest supported Python while the code stays
compatible with older research environments.

When the floor was set, Python 3.12 was the oldest version still receiving
security fixes and the version most research environments had available.
Python 3.12 therefore gives those environments a supported base without
holding the default interpreter behind the latest-versions policy.

## Decision

research-foundry supports Python 3.12 and newer and tests its checks on Python
3.12, 3.13 and 3.14. Its package metadata requires Python 3.12 or newer, and
its lint and type-check tools target Python 3.12.

Every generated project also requires Python 3.12 or newer. Each template
keeps that floor in the private `_python_floor` answer and keeps
`python_version` as the independently selected interpreter. The interpreter
defaults to Python 3.14 and continues to control `.python-version`, container
images and Read the Docs. Generation refuses an interpreter older than the
floor.

Lint and type-check tools in generated projects target the floor rather than
the selected interpreter. Checking against Python 3.12 is what prevents newer
syntax and standard-library features from entering code that claims Python
3.12 compatibility.

## Consequences

- Continuous integration runs the repository checks once on each supported
  Python version.
- Developers can select a supported interpreter for any `uv` command through
  `make <target> PYTHON=<version>`.
- Raising the default interpreter does not raise generated projects' support
  floor. The two values must be reviewed independently.
- A future floor change updates package metadata, tool targets, generation
  guards and the continuous-integration matrix together.
