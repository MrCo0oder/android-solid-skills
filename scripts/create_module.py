#!/usr/bin/env python3
"""Generate a feature or data Android library using the documented catalog conventions."""
import argparse
from contextlib import contextmanager, nullcontext
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

# Includes hard/soft Kotlin keywords: package names must work without backticks.
KOTLIN_KEYWORDS = frozenset("""
as break class continue do else false for fun if in interface is null object
package return super this throw true try typealias typeof val var when while
by catch constructor delegate dynamic field file finally get import init param
property receiver set setparam where actual abstract annotation companion const
crossinline data enum expect external final infix inline inner internal lateinit
noinline open operator out override private protected public reified sealed
suspend tailrec vararg value context
""".split())
# Android namespaces and Hilt-generated sources must also be valid Java packages.
JAVA_KEYWORDS = frozenset("""
assert boolean byte case char default double extends float goto implements
instanceof int long native new short static strictfp switch synchronized
throws transient void volatile _
""".split())
RESERVED_WORDS = KOTLIN_KEYWORDS | JAVA_KEYWORDS


def identifier(value):
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", value):
        raise ValueError(f"Invalid identifier {value!r}: use lowercase snake_case.")
    if value in RESERVED_WORDS:
        raise ValueError(f"Reserved word cannot be used as an identifier: {value!r}")
    return value


def package_name(value):
    for part in value.split("."):
        # Custom packages may use mixed-case identifiers, but never keywords.
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", part) or part in RESERVED_WORDS:
            raise ValueError(f"Invalid Kotlin package: {value!r}")
    return value


def pascal_case(value):
    return "".join(part[0].upper() + part[1:] for part in value.split("_"))


def without_comments(text):
    """Remove Kotlin comments while preserving quoted strings."""
    return re.sub(
        r'"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/',
        lambda match: "" if match[0].startswith(("//", "/*")) else match[0],
        text,
    )


def build_file(kind, namespace):
    plugins = ["android.lib", "kotlin", "kapt", "hilt"]
    if kind == "feature":
        plugins.append("compose.compiler")
    plugin_lines = "\n".join(f"    alias(libs.plugins.{plugin})" for plugin in plugins)
    dependencies = [
        "implementation(libs.core.ktx)",
        "implementation(libs.hilt.android)",
        "kapt(libs.hilt.android.compiler)",
        "implementation(libs.kotlinx.coroutines.core)",
    ]
    if kind == "feature":
        dependencies += [
            "implementation(platform(libs.compose.bom))",
            "implementation(libs.compose.ui)",
            "implementation(libs.compose.foundation)",
            "implementation(libs.material3)",
            "implementation(libs.compose.navigation)",
            "implementation(libs.bundles.viewModelLifecycle)",
        ]
    else:
        dependencies += [
            "implementation(libs.bundles.retrofit)",
            "implementation(libs.room.runtime)",
            "implementation(libs.androidx.room.ktx)",
            "kapt(libs.room.compiler)",
        ]
    dependencies += [
        "testImplementation(libs.junit.jupiter.api)",
        "testRuntimeOnly(libs.junit.jupiter.engine)",
        "testImplementation(libs.mockk)",
        "testImplementation(libs.truth)",
        "testImplementation(libs.turbine)",
        "testImplementation(libs.kotlinx.coroutines.test)",
    ]
    dependency_lines = "\n".join(f"    {line}" for line in dependencies)
    compose = "\n        compose = true" if kind == "feature" else ""
    return f"""plugins {{
{plugin_lines}
}}

android {{
    namespace = "{namespace}"
    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {{
        minSdk = libs.versions.minSdk.get().toInt()
        consumerProguardFiles("consumer-rules.pro")
    }}

    buildTypes {{
        getByName("release") {{
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }}
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}

    buildFeatures {{
        buildConfig = true{compose}
    }}

    flavorDimensions += listOf("platform", "environment")
    productFlavors {{
        create("gms") {{ dimension = "platform" }}
        create("hms") {{ dimension = "platform" }}
        create("production") {{ dimension = "environment" }}
        create("staging") {{ dimension = "environment" }}
        create("development") {{ dimension = "environment" }}
    }}
}}

dependencies {{
{dependency_lines}
}}
"""


def source_files(kind, name, package, flow):
    """Return relative paths and contents; planning generation performs no I/O."""
    files = {}

    def kotlin(path, subpackage, body):
        files[f"src/main/kotlin/{package.replace('.', '/')}/{path}.kt"] = (
            f"package {package}.{subpackage}\n\n{body.rstrip()}\n"
        )

    prefix = pascal_case(name)
    if kind == "feature":
        if flow != "main":
            prefix += pascal_case(flow)
        kotlin(f"{flow}/ui/{prefix}Screen", f"{flow}.ui", f"""import androidx.compose.foundation.layout.Box
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import {package}.{flow}.state.{prefix}UiState

@Composable
internal fun {prefix}Screen(
    state: {prefix}UiState,
    modifier: Modifier = Modifier,
) {{
    // TODO(confirm): Render the feature's agreed UI from state.
    Box(modifier = modifier)
}}""")
        kotlin(f"{flow}/state/{prefix}ViewModel", f"{flow}.state", f"""import androidx.lifecycle.ViewModel
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

@HiltViewModel
internal class {prefix}ViewModel @Inject constructor() : ViewModel() {{
    private val _state = MutableStateFlow({prefix}UiState())
    val state = _state.asStateFlow()

    // TODO(confirm): Add event handling and business collaborators.
}}""")
        kotlin(f"{flow}/state/{prefix}UiState", f"{flow}.state",
               f"// TODO(confirm): Define the state fields required by this flow.\ninternal class {prefix}UiState")
        for suffix in ("UiEvent", "SideEffect"):
            kotlin(f"{flow}/state/{prefix}{suffix}", f"{flow}.state",
                   f"// TODO(confirm): Define the supported {suffix} cases.\ninternal sealed interface {prefix}{suffix}")
        kotlin(f"{flow}/navigation/{prefix}Navigation", f"{flow}.navigation",
               f"""// TODO(confirm): Register this route with the app's navigation graph.
internal object {prefix}Navigation {{
    const val ROUTE = "{name}/{flow}"
}}""")
        for path in (f"{flow}/ui/components", "shared/ui", "shared/state", "shared/util"):
            files[f"src/main/kotlin/{package.replace('.', '/')}/{path}/.gitkeep"] = ""
    else:
        kotlin(f"domain/model/{prefix}", "domain.model",
               f"// TODO(confirm): Define domain fields from the feature contract.\nclass {prefix}")
        kotlin(f"domain/repository/{prefix}Repository", "domain.repository",
               f"// TODO(confirm): Define the data operations required by the feature.\ninterface {prefix}Repository")
        kotlin(f"data/repository/{prefix}RepositoryImpl", "data.repository",
               f"""import javax.inject.Inject
import {package}.domain.repository.{prefix}Repository

internal class {prefix}RepositoryImpl @Inject constructor() : {prefix}Repository""")
        kotlin(f"domain/useCase/Get{prefix}UseCase", "domain.useCase",
               f"""import javax.inject.Inject
import {package}.domain.repository.{prefix}Repository

class Get{prefix}UseCase @Inject constructor(
    private val repository: {prefix}Repository,
) {{
    // TODO(confirm): Implement invoke after the repository contract is defined.
}}""")
        for path, subpackage, suffix in (
            ("data/remote", "data.remote", "Service"),
            ("data/remote/dto", "data.remote.dto", "Dto"),
            ("data/local/entity", "data.local.entity", "Entity"),
            ("data/mapper", "data.mapper", "Mapper"),
        ):
            declaration = "interface" if suffix == "Service" else "class"
            kotlin(f"{path}/{prefix}{suffix}", subpackage,
                   f"// TODO(confirm): Implement from the agreed API/domain/persistence contract.\ninternal {declaration} {prefix}{suffix}")
        kotlin(f"data/local/{prefix}Dao", "data.local",
               f"""import androidx.room.Dao

// TODO(confirm): Add queries after the entity schema is defined.
@Dao
internal interface {prefix}Dao""")
        kotlin(f"data/local/{prefix}Database", "data.local",
               f"""import androidx.room.RoomDatabase

// TODO(confirm): Add @Database, entities and version once the schema is agreed.
internal abstract class {prefix}Database : RoomDatabase() {{
    abstract fun {name}Dao(): {prefix}Dao
}}""")
        kotlin(f"di/{prefix}Module", "di", f"""import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import {package}.data.repository.{prefix}RepositoryImpl
import {package}.domain.repository.{prefix}Repository

@Module
@InstallIn(SingletonComponent::class)
internal abstract class {prefix}Module {{
    @Binds
    abstract fun bindRepository(implementation: {prefix}RepositoryImpl): {prefix}Repository
}}""")
    return files


def plan_module(root, kind, name, package, flow):
    root = root.resolve()
    settings = root / "settings.gradle.kts"
    if settings.is_symlink() or not settings.is_file():
        raise ValueError("Root must contain a regular settings.gradle.kts file.")
    if not (root / "gradle/libs.versions.toml").is_file():
        raise ValueError("Root must contain gradle/libs.versions.toml.")
    parent = root / kind
    target = parent / name
    if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
        raise ValueError(f"Module parent must be a regular directory: {parent}")
    if target.exists() or target.is_symlink():
        raise ValueError(f"Module already exists: {target}")
    original = settings.read_bytes()
    settings_text = original.decode("utf-8")
    module_path = f":{kind}:{name}"
    includes = re.findall(r"\binclude\s*\((.*?)\)", without_comments(settings_text), re.S)
    registered = [
        ":" + path.lstrip(":")
        for block in includes
        for path in re.findall(r'["\']([^"\']+)["\']', block)
    ]
    if module_path in registered:
        raise ValueError(f"Module is already registered: {module_path}")
    # Gradle turns names such as fillCart and fill_cart into the same accessor.
    def accessor(value):
        return "".join(part[0].upper() + part[1:] for part in re.split(r"[-_.]+", value) if part)

    for path in registered:
        parent_path, _, sibling = path.rpartition(":")
        if parent_path == f":{kind}" and accessor(sibling) == accessor(name):
            raise ValueError(f"Gradle project accessor conflicts with {path}: {name}")
    # Resource namespaces differ even when feature and data share the same package.
    namespace = f"{package}.{kind}"
    for directory, dirs, filenames in os.walk(root):
        dirs[:] = [entry for entry in dirs if not entry.startswith(".") and entry != "build"]
        if "build.gradle.kts" in filenames:
            build = Path(directory) / "build.gradle.kts"
            text = without_comments(build.read_text(encoding="utf-8"))
            if re.search(r'\bnamespace\s*=\s*["\']' + re.escape(namespace) + r'["\']', text):
                raise ValueError(f"Android namespace {namespace!r} already exists in {build}")
    newline = "\r\n" if "\r\n" in settings_text else "\n"
    registration = f'include("{module_path}")'
    updated = settings_text + ("" if settings_text.endswith(("\n", "\r")) else newline)
    updated = (updated + registration + newline).encode("utf-8")
    files = {
        "build.gradle.kts": build_file(kind, namespace),
        "src/main/AndroidManifest.xml": '<manifest />\n',
        "consumer-rules.pro": "# Add rules required by consumers of this library.\n",
        "proguard-rules.pro": "# Add module-specific shrinking rules when needed.\n",
        **source_files(kind, name, package, flow),
    }
    return target, settings, original, updated, files, registration


@contextmanager
def generation_lock(root):
    """Fail fast if another generator owns this repository's registration lock."""
    lock = root.resolve() / ".create-module.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError(f"Another generator is running (or a stale lock exists): {lock}") from None
    try:
        yield
    finally:
        os.close(descriptor)
        lock.unlink()


def write_module(target, settings, original, updated, files):
    """Only roll back the module this invocation created; preserve existing files."""
    if target.parent.is_symlink() or settings.is_symlink():
        raise ValueError("Module parent or settings became a symlink; retry.")
    parent_created = not target.parent.exists()
    created = False
    temporary_settings = None
    try:
        target.parent.mkdir(exist_ok=True)
        target.mkdir()  # Exclusive: never merge with another module.
        created = True
        for relative, text in files.items():
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="\n") as output:
                output.write(text)
        with tempfile.NamedTemporaryFile(
            prefix=".create-module-", dir=settings.parent, delete=False
        ) as output:
            temporary_settings = Path(output.name)
            output.write(updated)
        temporary_settings.chmod(settings.stat().st_mode)
        if settings.read_bytes() != original:
            raise ValueError("settings.gradle.kts changed during generation; retry.")
        os.replace(temporary_settings, settings)
    except BaseException:
        if created:
            shutil.rmtree(target)
        if parent_created:
            try:
                target.parent.rmdir()  # Remove only if empty.
            except OSError:
                pass
        raise
    finally:
        if temporary_settings is not None:
            temporary_settings.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=("feature", "data"))
    parser.add_argument("name", help="Lowercase snake_case module name")
    parser.add_argument("--package", required=True, help="Kotlin base package, e.g. com.example.checkout")
    parser.add_argument("--flow", help="Feature flow package (default: main; feature only)")
    parser.add_argument("--root", type=Path, default=Path.cwd(),
                        help="Target Android repository root (default: current working directory)")
    parser.add_argument("--dry-run", action="store_true", help="Show outputs without writing")
    args = parser.parse_args(argv)
    try:
        name = identifier(args.name)
        if args.kind == "data" and args.flow is not None:
            raise ValueError("--flow is only supported for feature modules.")
        flow = identifier("main" if args.flow is None else args.flow)
        package = package_name(args.package)
        # Dry runs never create a lock or any other file.
        with nullcontext() if args.dry_run else generation_lock(args.root):
            target, settings, original, updated, files, registration = plan_module(
                args.root, args.kind, name, package, flow
            )
            if args.dry_run:
                print(f"Dry run: {target}")
                for relative in sorted(files):
                    print(f"  {target / relative}")
                print(f"Append to {settings}: {registration}")
            else:
                write_module(target, settings, original, updated, files)
                print(f"Created {target} ({len(files)} files)")
                print(f"Registered {registration} in {settings}")
        return 0
    except (OSError, ValueError, UnicodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
