# Android module generator

Requires Python 3.10+ and an Android project using the Gradle conventions below.
No Python dependencies are required. The target root defaults to the current
working directory; use `--root` to select another project. `--package` is required.
The script is standalone and can be copied into an Android project's `scripts/`
directory, or invoked by absolute path from this repository.

## Usage

```bash
# Create and register :feature:checkout with a main flow.
python3 scripts/create_module.py feature checkout --package example.shop.checkout

# Create a feature with a named flow.
python3 scripts/create_module.py feature order_history --package example.shop.order_history --flow details

# Create and register :data:checkout.
python3 scripts/create_module.py data checkout --package example.shop.checkout

# Preview every generated path and the settings registration.
python3 scripts/create_module.py data checkout --package example.shop.checkout --dry-run

# Select the target Android repository explicitly.
python3 /path/to/solid-skills/scripts/create_module.py feature checkout --package example.shop.checkout --root /path/to/project
python3 /path/to/solid-skills/scripts/create_module.py data checkout --package example.shop.checkout --root /path/to/project
```

Module names and flow names must use lowercase snake_case and cannot be Kotlin
or Java keywords. Custom package segments follow the same keyword restriction. Kotlin type names use PascalCase: order_history becomes OrderHistory.
The default main flow uses the module's type prefix (CheckoutScreen); a named
flow appends its name (OrderHistoryDetailsScreen). The --flow option is feature-only.

Supply the Kotlin base package explicitly, for example `--package example.shop.checkout`.
Android resource namespaces append `.feature` or `.data` to that package, so a
feature and data module with the same name can coexist. The generated Kotlin
sources use the base package; the namespace suffix does not move those sources.

## Generated structure

```text
feature/<name>/
  build.gradle.kts
  consumer-rules.pro
  proguard-rules.pro
  src/main/
    AndroidManifest.xml
    kotlin/<package>/
      <flow>/
        ui/
          <Prefix>Screen.kt
          components/.gitkeep
        state/
          <Prefix>ViewModel.kt
          <Prefix>UiState.kt
          <Prefix>UiEvent.kt
          <Prefix>SideEffect.kt
        navigation/
          <Prefix>Navigation.kt
      shared/
        ui/.gitkeep
        state/.gitkeep
        util/.gitkeep

data/<name>/
  build.gradle.kts
  consumer-rules.pro
  proguard-rules.pro
  src/main/
    AndroidManifest.xml
    kotlin/<package>/
      domain/
        model/<Name>.kt
        repository/<Name>Repository.kt
        useCase/Get<Name>UseCase.kt
      data/
        repository/<Name>RepositoryImpl.kt
        remote/
          <Name>Service.kt
          dto/<Name>Dto.kt
        local/
          <Name>Database.kt
          <Name>Dao.kt
          entity/<Name>Entity.kt
        mapper/<Name>Mapper.kt
      di/<Name>Module.kt
```

Both templates follow the supplied PC-Revamp generator: Android libraries with Java 17, catalog SDK versions,
GMS/HMS and production/staging/development flavors, Hilt, and standard JVM test
dependencies. Feature modules enable Compose, lifecycle, and navigation. Data
modules include coroutines, Retrofit, and Room without Compose.


## Gradle conventions

The build templates are adapted from the PC-Revamp module generator supplied as
the reference. They use version-catalog aliases rather than pinning dependency or
plugin versions. Running this standalone script does not read or depend on that
reference project's files.

The target must already contain `settings.gradle.kts` and
`gradle/libs.versions.toml`. The templates expect these catalog accessors:

| Group | Required accessors |
| --- | --- |
| Plugins, both kinds | `libs.plugins.android.lib`, `libs.plugins.kotlin`, `libs.plugins.kapt`, `libs.plugins.hilt` |
| Plugin, feature only | `libs.plugins.compose.compiler` |
| SDK versions | `libs.versions.compileSdk`, `libs.versions.minSdk` |
| Shared libraries | `libs.core.ktx`, `libs.hilt.android`, `libs.hilt.android.compiler`, `libs.kotlinx.coroutines.core` |
| Feature libraries | `libs.compose.bom`, `libs.compose.ui`, `libs.compose.foundation`, `libs.material3`, `libs.compose.navigation`, `libs.bundles.viewModelLifecycle` |
| Data libraries | `libs.bundles.retrofit`, `libs.room.runtime`, `libs.androidx.room.ktx`, `libs.room.compiler` |
| JVM tests | `libs.junit.jupiter.api`, `libs.junit.jupiter.engine`, `libs.mockk`, `libs.truth`, `libs.turbine`, `libs.kotlinx.coroutines.test` |

As in the reference project, the root build must configure Kotlin's JVM target to
17 and local test tasks to use JUnit Platform, including the required test runtime
launcher. The script checks for the catalog file, but does not resolve aliases,
plugins, or dependencies. If your project uses different conventions, adapt
`build_file()` before generation.

The generator appends an explicit `include(":feature:<name>")` or
`include(":data:<name>")` to settings. It does not modify root build scripts,
version catalogs, app dependencies, or existing modules. This utility is maintained
in this repository's `scripts/` directory and is separate from the installable
`solid` skill folder.

## Complete the feature contract

The generated files are declaration skeletons, with TODO(confirm) markers for
business decisions. Sync and build them in the target project's configured toolchain
before treating them as build-verified. There are no invented API endpoints, fields, queries, or
repository operations. The screen is stateless; the ViewModel exposes StateFlow.
UI implementation types are internal. Domain types remain accessible to consumers.

The data skeleton binds its empty repository implementation with Hilt. Its database
is abstract and intentionally has no @Database annotation until entities and a
schema version are defined. Its entity, service, DTO, mapper, and use case are
extension points; they do not implement persistence or network behavior yet.

Add consumer project dependencies and wire navigation yourself. Creating either
module does not require or link a matching module of the other type. The script
does not edit app code, add version catalog entries, or run Gradle automatically.

## Safety and verification

The generator checks identifiers, existing module paths, explicit Gradle includes,
normalized Gradle project accessor names (fillCart conflicts with fill_cart),
and literal Kotlin-DSL Android namespace declarations before writing. It refuses
symlink module parents and settings files. Existing modules are never merged or
overwritten. Settings content, permissions, and newline style are preserved.
If settings change during generation, it aborts; write failures remove only the
new module and its temporary settings file. Mutating invocations use an exclusive
.create-module.lock file at the repository root; a second invocation fails fast
instead of losing a settings registration. The lock is removed on normal exit or
handled errors. After a forced process termination, remove a stale lock only after
confirming no generator is running. Dry runs create no lock.

Avoid concurrent manual project structure edits while running the generator.
Computed namespaces and dynamically generated Gradle includes require manual
collision checks.

Run generator tests from the solid-skills repository root (fixtures are temporary;
these tests do not write to your Android project):

```bash
python3 -m unittest discover -s scripts/tests -p 'test_create_module.py' -v
```

After generating a module, sync Gradle, then validate it:

```bash
./gradlew :feature:checkout:testGmsStagingDebugUnitTest :feature:checkout:assembleGmsStagingDebug
./gradlew :data:checkout:testGmsStagingDebugUnitTest :data:checkout:assembleGmsStagingDebug
./gradlew :app:assembleGmsStagingDebug
```
