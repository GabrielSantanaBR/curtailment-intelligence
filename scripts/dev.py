from __future__ import annotations

import argparse
import importlib.util
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def doctor() -> int:
    checks: list[tuple[str, bool, str]] = []
    py_ok = sys.version_info >= (3, 11)
    checks.append(("Python >= 3.11", py_ok, platform.python_version()))

    for module in ["fastapi", "pandas", "sklearn", "scipy", "sqlalchemy"]:
        available = importlib.util.find_spec(module) is not None
        checks.append((f"Python module: {module}", available, "installed" if available else "missing"))

    for relative in ["app/main.py", "ml/modeling.py", "web/index.html", "requirements.txt"]:
        exists = (ROOT / relative).exists()
        checks.append((relative, exists, "found" if exists else "missing"))

    optional = [
        ("Demo dataset", ROOT / "data/demo/curtailment_demo.csv"),
        ("Classifier artifact", ROOT / "artifacts/curtailment_classifier.joblib"),
        ("Metrics artifact", ROOT / "artifacts/metrics.json"),
    ]

    print("Curtailment Intelligence — environment doctor\n")
    failed = False
    for label, ok, detail in checks:
        print(f"[{'OK' if ok else 'FAIL'}] {label}: {detail}")
        failed = failed or not ok

    print("\nOptional demo assets:")
    for label, path in optional:
        print(f"[{'OK' if path.exists() else 'INFO'}] {label}: {'ready' if path.exists() else 'run bootstrap'}")

    if failed:
        print("\nEnvironment is not ready. Install requirements-dev.txt and try again.")
        return 1

    print("\nEnvironment is ready.")
    return 0


def check() -> None:
    run([sys.executable, "-m", "compileall", "-q", "app", "ml", "scripts", "tests"])
    if importlib.util.find_spec("ruff") is not None:
        run([sys.executable, "-m", "ruff", "check", "app", "ml", "scripts", "tests"])
    else:
        print("INFO: Ruff is not installed; skipping lint. Install requirements-dev.txt to enable it.")
    run([sys.executable, "-m", "pytest"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Developer commands for Curtailment Intelligence")
    parser.add_argument("command", choices=["doctor", "bootstrap", "run", "test", "check"])
    args = parser.parse_args()

    if args.command == "doctor":
        return doctor()
    if args.command == "bootstrap":
        run([sys.executable, "scripts/bootstrap_demo.py"])
    elif args.command == "run":
        run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload"])
    elif args.command == "test":
        run([sys.executable, "-m", "pytest"])
    elif args.command == "check":
        check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
