# ai-skills

A collection of agent skills for AI-assisted workflows.

Skills follow the [Agent Skills](https://github.com/agentskills/agentskills) open standard — they work with GitHub Copilot CLI, Claude Code, VS Code Copilot, and any tool that supports the spec.

## Skills

| Skill | Description |
|-------|-------------|
| [kernel-memory-diagnosis](skills/kernel-memory-diagnosis/) | Diagnose Windows kernel memory leaks causing "Secure System" process growth. Systematic workflow using pool tag analysis, driver identification, and ETW session auditing. |

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
