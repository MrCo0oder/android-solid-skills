"""Behavior tests for the module generator; no Android SDK or third-party packages required."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "create_module.py"


class CreateModuleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "gradle").mkdir()
        (self.root / "gradle/libs.versions.toml").write_text("[versions]\n", encoding="utf-8")
        self.settings = self.root / "settings.gradle.kts"
        self.original = b'rootProject.name = "fixture"\r\ninclude(":app")\r\n'
        self.settings.write_bytes(self.original)

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--root", str(self.root),
             *([] if "--package" in args else ["--package", f"example.shop.{args[1]}"])],
            capture_output=True, text=True, check=False,
        )

    def test_feature_layout_and_registration(self):
        result = self.run_cli("feature", "order_history", "--flow", "details")
        self.assertEqual(0, result.returncode, result.stderr)
        module = self.root / "feature/order_history"
        source = module / "src/main/kotlin/example/shop/order_history"
        for file in (
            "details/ui/OrderHistoryDetailsScreen.kt",
            "details/state/OrderHistoryDetailsViewModel.kt",
            "details/state/OrderHistoryDetailsUiState.kt",
            "details/state/OrderHistoryDetailsUiEvent.kt",
            "details/state/OrderHistoryDetailsSideEffect.kt",
            "details/navigation/OrderHistoryDetailsNavigation.kt",
            "details/ui/components/.gitkeep", "shared/ui/.gitkeep",
            "shared/state/.gitkeep", "shared/util/.gitkeep",
        ):
            self.assertTrue((source / file).is_file(), file)
        self.assertIn("package example.shop.order_history.details.ui",
                      (source / "details/ui/OrderHistoryDetailsScreen.kt").read_text())
        self.assertEqual(self.original + b'include(":feature:order_history")\r\n',
                         self.settings.read_bytes())
        build = (module / "build.gradle.kts").read_text()
        for value in ('compose = true', 'VERSION_17', '"gms"', '"hms"',
                      '"production"', '"staging"', '"development"',
                      'libs.plugins.compose.compiler', 'libs.junit.jupiter.api'):
            self.assertIn(value, build)
        self.assertTrue((module / "src/main/AndroidManifest.xml").is_file())
        self.assertTrue((module / "consumer-rules.pro").is_file())
        self.assertTrue((module / "proguard-rules.pro").is_file())

    def test_data_layout_and_custom_package(self):
        result = self.run_cli("data", "checkout", "--package", "example.shop.checkout")
        self.assertEqual(0, result.returncode, result.stderr)
        module = self.root / "data/checkout"
        source = module / "src/main/kotlin/example/shop/checkout"
        for file in (
            "domain/model/Checkout.kt", "domain/repository/CheckoutRepository.kt",
            "domain/useCase/GetCheckoutUseCase.kt",
            "data/repository/CheckoutRepositoryImpl.kt",
            "data/remote/CheckoutService.kt", "data/remote/dto/CheckoutDto.kt",
            "data/local/CheckoutDatabase.kt", "data/local/CheckoutDao.kt",
            "data/local/entity/CheckoutEntity.kt", "data/mapper/CheckoutMapper.kt",
            "di/CheckoutModule.kt",
        ):
            self.assertTrue((source / file).is_file(), file)
        build = (module / "build.gradle.kts").read_text()
        self.assertIn('namespace = "example.shop.checkout.data"', build)
        self.assertIn("libs.room.compiler", build)
        self.assertNotIn("compose = true", build)
        self.assertNotIn("libs.plugins.compose.compiler", build)

    def test_default_flow_and_same_named_pair(self):
        for kind in ("feature", "data"):
            result = self.run_cli(kind, "checkout")
            self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((self.root / "feature/checkout/src/main/kotlin/example/shop/"
                         "checkout/main/state/CheckoutViewModel.kt").is_file())

    def test_dry_run_writes_nothing(self):
        before = sorted(p.relative_to(self.root) for p in self.root.rglob("*"))
        result = self.run_cli("data", "checkout", "--dry-run")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("CheckoutRepository.kt", result.stdout)
        self.assertIn('include(":data:checkout")', result.stdout)
        self.assertEqual(before, sorted(p.relative_to(self.root) for p in self.root.rglob("*")))
        self.assertEqual(self.original, self.settings.read_bytes())

    def test_invalid_inputs_write_nothing(self):
        for args in (
            ("feature", "../escape"), ("data", "BadName"), ("data", "when"),
            ("data", "foo__bar"), ("data", "foo_"), ("feature", "checkout", "--flow", "class"),
            ("feature", "checkout", "--package", "example..shop"),
            ("feature", "checkout", "--package", "example.class"),
            ("data", "checkout", "--flow", "details"),
            ("feature", "checkout", "--flow", ""),
            ("data", "checkout", "--package", ""),
            ("feature", "switch"),
            ("data", "checkout", "--package", "example.native"),
        ):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual(self.original, self.settings.read_bytes())
                self.assertFalse((self.root / "feature").exists())
                self.assertFalse((self.root / "data").exists())

    def test_existing_module_is_preserved(self):
        module = self.root / "feature/checkout"
        module.mkdir(parents=True)
        sentinel = module / "notes.txt"
        sentinel.write_text("user work")
        result = self.run_cli("feature", "checkout")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("user work", sentinel.read_text())
        self.assertEqual([sentinel], list(module.iterdir()))
        self.assertEqual(self.original, self.settings.read_bytes())

    def test_duplicate_registration_is_rejected(self):
        self.settings.write_bytes(self.original + b'include(":feature:checkout")\r\n')
        before = self.settings.read_bytes()
        result = self.run_cli("feature", "checkout")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, self.settings.read_bytes())
        self.assertFalse((self.root / "feature").exists())

    def test_namespace_collision_is_rejected(self):
        existing = self.root / "data/other"
        existing.mkdir(parents=True)
        (existing / "build.gradle.kts").write_text(
            'android { namespace = "example.shop.checkout.data" }')
        result = self.run_cli("data", "checkout")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("namespace", result.stderr.lower())
        self.assertFalse((self.root / "data/checkout").exists())

    def test_symlink_parent_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / "feature").symlink_to(outside, target_is_directory=True)
        result = self.run_cli("feature", "checkout")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual([], list(outside.iterdir()))

    def test_missing_repository_configuration_is_rejected(self):
        self.settings.unlink()
        result = self.run_cli("data", "checkout")
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.root / "data").exists())

    def load_generator(self):
        spec = importlib.util.spec_from_file_location("create_module", SCRIPT)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        return generator

    def test_gradle_accessor_collision_is_rejected(self):
        self.settings.write_bytes(self.original + b'include(":feature:fillCart")\r\n')
        result = self.run_cli("feature", "fill_cart")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("accessor", result.stderr.lower())
        self.assertFalse((self.root / "feature").exists())

    def test_registration_without_leading_colon_is_rejected(self):
        self.settings.write_bytes(self.original + b'include("data:checkout")\r\n')
        result = self.run_cli("data", "checkout")
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.root / "data").exists())

    def test_concurrent_generation_cannot_lose_registration(self):
        generator = self.load_generator()
        real_replace = generator.os.replace
        nested_results = []

        def concurrent_replace(source, destination):
            # Trigger another invocation at the former check/replace race window.
            with patch.object(generator.os, "replace", side_effect=real_replace):
                nested_results.append(
                    generator.main(["data", "second", "--root", str(self.root), "--package", "example.shop.second"])
                )
            real_replace(source, destination)

        with patch.object(generator.os, "replace", side_effect=concurrent_replace):
            self.assertEqual(0, generator.main(["data", "first", "--root", str(self.root), "--package", "example.shop.first"]))
        self.assertEqual([1], nested_results)
        self.assertIn(b'include(":data:first")', self.settings.read_bytes())
        self.assertFalse((self.root / "data/second").exists())
        self.assertFalse((self.root / ".create-module.lock").exists())

    def test_settings_failure_rolls_back_created_module(self):
        spec = importlib.util.spec_from_file_location("create_module", SCRIPT)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        with patch.object(generator.os, "replace", side_effect=OSError("write denied")):
            self.assertEqual(1, generator.main(["data", "checkout", "--root", str(self.root), "--package", "example.shop.checkout"]))
        self.assertFalse((self.root / "data/checkout").exists())
        self.assertEqual(self.original, self.settings.read_bytes())
        self.assertEqual([], list(self.root.glob(".create-module-*")))


    def test_package_is_required(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "feature", "checkout", "--root", str(self.root)],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("--package", result.stderr)
        self.assertFalse((self.root / "feature").exists())
        self.assertEqual(self.original, self.settings.read_bytes())

    def test_default_root_is_current_working_directory(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "data", "checkout",
             "--package", "example.shop.checkout"],
            cwd=self.root, capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((self.root / "data/checkout/build.gradle.kts").is_file())
        self.assertIn(b'include(":data:checkout")', self.settings.read_bytes())

    def test_settings_manual_change_is_preserved_and_module_rolled_back(self):
        generator = self.load_generator()
        target, settings, original, updated, files, _ = generator.plan_module(
            self.root, "data", "checkout", "example.shop.checkout", "main"
        )
        changed = original + b"// concurrent manual edit\r\n"
        settings.write_bytes(changed)
        with self.assertRaisesRegex(ValueError, "changed during generation"):
            generator.write_module(target, settings, original, updated, files)
        self.assertEqual(changed, settings.read_bytes())
        self.assertFalse(target.exists())
        self.assertEqual([], list(self.root.glob(".create-module-*")))

    def test_symlink_settings_are_rejected(self):
        original_settings = self.root / "original-settings.gradle.kts"
        self.settings.rename(original_settings)
        self.settings.symlink_to(original_settings)
        result = self.run_cli("data", "checkout")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(self.original, original_settings.read_bytes())
        self.assertFalse((self.root / "data").exists())


if __name__ == "__main__":
    unittest.main()
