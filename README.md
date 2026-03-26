# ai-skills

A collection of agent skills for AI-assisted workflows.

Skills follow the [Agent Skills](https://github.com/agentskills/agentskills) open standard -- they work with GitHub Copilot CLI, Claude Code, VS Code Copilot, and any tool that supports the spec.

## Skills

| Skill | Description |
|-------|-------------|
| [kernel-memory-diagnosis](skills/kernel-memory-diagnosis/) | Diagnose Windows kernel memory leaks causing "Secure System" process growth. Systematic workflow using pool tag analysis, driver identification, and ETW session auditing. |
| [madr-author](skills/madr-author/) | Author Architecture Decision Records interactively using MADR 4.0.0 format. Includes template and helper scripts. |
| [running-ralphs](skills/running-ralphs/) | Race N agents on the same task with varied constraints. A/B testing for agentic workflows -- compare results, keep the winner, scavenge the losers. |
| [skill-authoring](skills/skill-authoring/) | Pattern for authoring and improving agent skills. Maximizes information density in SKILL.md files. |
| [stakeholder-alignment](skills/stakeholder-alignment/) | Map work priorities to management chain expectations for task planning and status updates. |
| [test-driven-development](skills/test-driven-development/) | Supervisor-orchestrated TDD with agent-per-step. Delegates setup, red-describe, red-implement, green, and refactor phases. Language sidecars for C# and Python. |

## Installation

### Personal skills (all projects)

Clone into your skills directory:

```bash
# GitHub Copilot CLI / Claude Code
git clone https://github.com/jmathes/ai-skills.git ~/.copilot/skills/ai-skills
```

Or copy individual skills:

```bash
cp -r skills/kernel-memory-diagnosis ~/.copilot/skills/
```

### Project skills (single repo)

Copy a skill into your repo's `.github/skills/` directory:

```bash
cp -r skills/kernel-memory-diagnosis .github/skills/
```

## Creating Skills

Each skill is a directory containing a `SKILL.md` file with YAML frontmatter and Markdown instructions, plus any supporting scripts or resources:

```
skills/
└── my-skill/
    ├── SKILL.md              # Required: skill definition
    └── helper-script.py      # Optional: supporting resources
```

See the [Agent Skills spec](https://github.com/agentskills/agentskills) for details.

## License

[MIT](LICENSE)
