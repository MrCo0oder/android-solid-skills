# Android module generator

See the [bundled generator guide](../skills/solid/references/module-generator.md) for usage, required Gradle conventions, generated structure, and safety behavior.

The repository entry point remains available:

```bash
python3 scripts/create_module.py feature checkout --package example.shop.checkout --root /path/to/android-project --dry-run
```

The implementation lives in `skills/solid/scripts/create_module.py`, so it also ships with npx and manual skill installations.
