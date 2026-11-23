# Solid Skills for Kotlin and Android

Professional Kotlin and Android engineering skills for AI coding agents. Transforms code into senior-engineer quality software through SOLID principles, TDD, clean code practices, and professional software design.

Skills follow the [Agent Skills](https://github.com/anthropics/skills) format.

## Available Skills

### solid

Transform junior-level code into senior-engineer quality software. Adapted for **Kotlin** and **Android** projects, including coroutines, Flow, ViewModels, Jetpack Compose, and existing XML/Views screens.

**Use when:**

- Writing any code (features, fixes, utilities)
- Refactoring existing code
- Planning or designing architecture
- Reviewing code quality
- Debugging issues
- Creating tests
- Making design decisions

**Core principles:**

| Principle | Focus |
|-----------|-------|
| TDD | Red-Green-Refactor for new logic; behavioral verification appropriate to the change |
| SOLID | Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion |
| Clean Code | Meaningful names, cohesive functions, useful rationale and contracts |
| Design Patterns | Creational, Structural, Behavioral patterns |
| Architecture | Vertical slicing, dependency rule, Android UI/data ownership, optional domain layer |

**Reference documentation included:**

- `solid-principles.md` - SOLID principles with Kotlin examples
- `tdd.md` - Test-Driven Development practices
- `testing.md` - Testing strategies and patterns
- `clean-code.md` - Clean code guidelines
- `code-smells.md` - Code smell detection and fixes
- `design-patterns.md` - GoF patterns with examples
- `architecture.md` - Clean architecture principles
- `object-design.md` - Object stereotypes and responsibilities
- `complexity.md` - Managing essential vs accidental complexity

**Key features:**

- Encourages test-first new logic and focused regression coverage
- Guides code-smell review and scoped fixes when requested
- Applies SOLID principles with Kotlin and Android context
- Uses value objects where domain distinctions or invariants justify them
- Follows Law of Demeter and Tell Don't Ask
- Judges cohesion and clarity without fixed method, class, or field limits

**Android guidance also covers:**

- Structured concurrency, cancellation, main-safe operations, and lifecycle-aware Flow collection.
- Compose state hoisting and effects, plus Fragment view lifecycle and ViewBinding cleanup.
- ViewModel state, repository/cache contracts, navigation ownership, and restoration.
- Existing DI and architecture conventions, with verification suited to the actual module and variant.

## Installation

### With npx

Install from GitHub into your current project:

```bash
npx skills add MrCo0oder/android-solid-skills --skill solid
```

Choose your supported agent when prompted. For Codex specifically:

```bash
npx skills add MrCo0oder/android-solid-skills --skill solid --agent codex
```

Add `--global` for a user-wide installation. The current Skills CLI requires
Node.js 22.20 or later; see its [installation documentation](https://github.com/vercel-labs/skills).

For a local checkout, run `npx skills add . --skill solid` from this repository.
The entire skill folder is installed, including its reference guides and Python
module generator. Python 3.10+ is needed only when running the generator.

### Manually

Clone this repository or download and extract its ZIP from GitHub. Copy the
complete `skills/solid` folder into your agent's supported skills directory.

For a project-scoped Codex installation, run these commands from your Android
project. The destination must not already exist:

```bash
git clone --depth 1 https://github.com/MrCo0oder/android-solid-skills.git android-solid-skills
mkdir -p .agents/skills
test ! -e .agents/skills/solid && test ! -L .agents/skills/solid && cp -R android-solid-skills/skills/solid .agents/skills/solid
```

For a user-wide Codex installation, copy that folder to `~/.agents/skills/solid`
instead. Other agents may use a different directory; consult their documentation.
Keep `SKILL.md`, `references/`, and `scripts/` together. Start a fresh agent session
if the installed skill is not discovered immediately.

This repository distributes an Agent Skill directly from GitHub. No separate npm
package or plugin-store submission is required for the installation methods above.

## Usage

Invoke `solid` using your agent's skill mechanism, or let a supporting agent discover it for Kotlin/Android tasks. Discovery depends on the agent's configuration.

**Examples:**

- "Implement an Android registration feature using the existing architecture"
- "Refactor this ViewModel and Compose screen while preserving behavior"
- "Review this code for quality issues"
- "Add deterministic coroutine and repository tests for this module"
- "Design the architecture for a payment system"

## Module generator

The standalone [Python module generator](scripts/create_module.py) creates the documented feature/data layout, Android library Gradle files, and settings registration using the supplied PC-Revamp conventions.

```bash
python3 scripts/create_module.py feature checkout --package example.shop.checkout --root /path/to/android-project --dry-run
python3 scripts/create_module.py data checkout --package example.shop.checkout --root /path/to/android-project
```

Remove `--dry-run` to create the feature. Existing modules are never overwritten. See [generator usage and Gradle prerequisites](scripts/create_module.md) for catalog aliases, named flows, safety behavior, and tests. The generator also ships inside the installed skill at `scripts/create_module.py`; read its bundled `references/module-generator.md` for prerequisites.

## Skill Structure

```
skills/
└── solid/
    ├── SKILL.md           # Main skill instructions
    ├── scripts/
    │   └── create_module.py
    └── references/        # Supporting documentation
        ├── solid-principles.md
        ├── tdd.md
        ├── testing.md
        ├── clean-code.md
        ├── code-smells.md
        ├── design-patterns.md
        ├── architecture.md
        ├── object-design.md
        ├── complexity.md
        └── module-generator.md
```

## Provenance

Inspired from [ramziddin/solid-skills](https://github.com/ramziddin/solid-skills), preserving its teaching structure and general explanations while translating examples to Kotlin. Use the installation instructions above for this repository; the upstream source installs the upstream skill. The clean-code guide retains its original course attribution.

Examples identify partial app context and dependencies where relevant. Their illustrative business rules are not universal app requirements. Verification should distinguish documentation checks, compilation, local tests, device behavior, visual parity, and live services.

## Publishing updates

The GitHub install command uses files committed and pushed to
`MrCo0oder/android-solid-skills`. Local edits do not update GitHub installations.
Validate the skill and generator, review the changes, then commit and push them
to the repository's default branch. You do not need to run `npm publish`.

Consumers can preview discovery without installing:

```bash
npx skills add MrCo0oder/android-solid-skills --list
```

The repo-level `scripts/create_module.py` remains a convenience entry point;
the installed skill is self-contained and does not depend on it.
