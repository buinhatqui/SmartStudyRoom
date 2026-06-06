#!/usr/bin/env python3
"""Terminal helper for Smart Study Room development tasks."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
IS_WINDOWS = platform.system().lower() == "windows"

BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
AI_DIR = ROOT / "ai-service"
IOT_DIR = ROOT / "iot-edge"
COMPOSE_FILE = ROOT / "infra" / "docker-compose.local.yml"
PYTHON_CACHE: dict[Path, str] = {}

SETUP_TARGETS = ("all", "env", "frontend", "ai", "iot", "db")
DEV_SERVICES = ("backend", "frontend", "ai", "gateway", "sensor", "commands", "all")
TEST_TARGETS = ("all", "backend", "frontend", "ai", "iot")
DB_ACTIONS = ("up", "down", "logs", "ps")


def command_text(command: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in command])


def npm_command(*args: str) -> list[str]:
    return ["npm.cmd" if IS_WINDOWS else "npm", *args]


def maven_executable() -> str | None:
    candidates = ("mvn.cmd", "mvn") if IS_WINDOWS else ("mvn",)
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def venv_python_path(service_dir: Path) -> Path:
    if IS_WINDOWS:
        return service_dir / ".venv" / "Scripts" / "python.exe"
    return service_dir / ".venv" / "bin" / "python"


def service_python(service_dir: Path) -> str:
    cache_key = service_dir.resolve()
    if cache_key in PYTHON_CACHE:
        return PYTHON_CACHE[cache_key]

    candidate = venv_python_path(service_dir)
    if candidate.exists():
        code, output = capture_command([str(candidate), "--version"], service_dir, timeout=5)
        if code == 0:
            PYTHON_CACHE[cache_key] = str(candidate)
            return PYTHON_CACHE[cache_key]

        reason = output.splitlines()[0] if output else "unknown error"
        print(
            "Local venv python is not usable; "
            f"falling back to current Python. ({candidate.relative_to(ROOT)}: {reason})"
        )

    PYTHON_CACHE[cache_key] = sys.executable
    return PYTHON_CACHE[cache_key]


def run_command(command: list[str], cwd: Path = ROOT) -> int:
    print(f"\n$ {command_text(command)}")
    print(f"cwd: {cwd}")
    try:
        completed = subprocess.run(command, cwd=str(cwd), check=False)
        return completed.returncode
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
        return 127
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


def capture_command(command: list[str], cwd: Path = ROOT, timeout: int = 8) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            timeout=timeout,
        )
        return completed.returncode, completed.stdout.strip()
    except FileNotFoundError:
        return 127, f"Command not found: {command[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"Timed out after {timeout}s: {command_text(command)}"


def is_inside_workspace(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def ensure_java_home() -> bool:
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        print("JAVA_HOME is not set. Backend Maven commands require a valid JDK.")
        return False

    java_bin = Path(java_home) / "bin" / ("java.exe" if IS_WINDOWS else "java")
    if not java_bin.exists():
        print(f"JAVA_HOME does not point to a JDK with java: {java_home}")
        return False

    return True


def backend_maven_command(goal: str) -> list[str] | None:
    maven = maven_executable()
    if maven:
        return [maven, goal]

    wrapper = BACKEND_DIR / ("mvnw.cmd" if IS_WINDOWS else "mvnw")
    if wrapper.exists():
        return [str(wrapper), goal]

    print("Maven was not found, and backend Maven wrapper is missing.")
    return None


def run_backend_maven(goal: str) -> int:
    if not ensure_java_home():
        return 1

    command = backend_maven_command(goal)
    if command is None:
        return 1

    return run_command(command, BACKEND_DIR)


def copy_env_files() -> int:
    pairs = [
        (BACKEND_DIR / ".env.example", BACKEND_DIR / ".env"),
        (FRONTEND_DIR / ".env.example", FRONTEND_DIR / ".env"),
        (AI_DIR / ".env.example", AI_DIR / ".env"),
        (IOT_DIR / ".env.example", IOT_DIR / ".env"),
    ]

    for source, target in pairs:
        if not source.exists():
            print(f"Missing example file: {source.relative_to(ROOT)}")
            continue
        if target.exists():
            print(f"Skip existing: {target.relative_to(ROOT)}")
            continue
        shutil.copy2(source, target)
        print(f"Created: {target.relative_to(ROOT)}")

    return 0


def create_venv_and_install(service_dir: Path, requirements: Path) -> int:
    venv_dir = service_dir / ".venv"
    if not venv_dir.exists():
        code = run_command([sys.executable, "-m", "venv", str(venv_dir)], ROOT)
        if code != 0:
            return code
    else:
        print(f"Skip existing venv: {venv_dir.relative_to(ROOT)}")

    python = str(venv_python_path(service_dir))
    return run_command([python, "-m", "pip", "install", "-r", str(requirements)], service_dir)


def setup_frontend() -> int:
    return run_command(npm_command("install"), FRONTEND_DIR)


def setup_ai() -> int:
    return create_venv_and_install(AI_DIR, AI_DIR / "requirements.txt")


def setup_iot() -> int:
    return create_venv_and_install(IOT_DIR, IOT_DIR / "requirements.txt")


def docker_compose(*args: str) -> int:
    return run_command(["docker", "compose", "-f", str(COMPOSE_FILE), *args], ROOT)


def db_up() -> int:
    return docker_compose("up", "-d", "mysql")


def db_down() -> int:
    return docker_compose("down")


def db_logs() -> int:
    return docker_compose("logs", "-f", "mysql")


def db_ps() -> int:
    return docker_compose("ps")


def run_setup(target: str) -> int:
    steps = {
        "env": copy_env_files,
        "frontend": setup_frontend,
        "ai": setup_ai,
        "iot": setup_iot,
        "db": db_up,
    }

    if target != "all":
        return steps[target]()

    for name in ("env", "frontend", "ai", "iot", "db"):
        print(f"\n== setup {name} ==")
        code = steps[name]()
        if code != 0:
            return code
    return 0


def dev_command(service: str) -> tuple[list[str], Path] | None:
    if service == "backend":
        command = backend_maven_command("spring-boot:run")
        if command is None:
            return None
        return command, BACKEND_DIR
    if service == "frontend":
        return npm_command("run", "dev"), FRONTEND_DIR
    if service == "ai":
        return [
            service_python(AI_DIR),
            "-m",
            "uvicorn",
            "service:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ], AI_DIR
    if service == "gateway":
        return [service_python(IOT_DIR), "gateway.py"], IOT_DIR
    if service == "sensor":
        return [service_python(IOT_DIR), "test_sensor_flow.py"], IOT_DIR
    if service == "commands":
        return [service_python(IOT_DIR), "test_device_control_flow.py"], IOT_DIR
    return None


def start_detached(service: str) -> int:
    resolved = dev_command(service)
    if resolved is None:
        return 1

    command, cwd = resolved
    print(f"Starting {service}: {command_text(command)}")
    try:
        if IS_WINDOWS:
            subprocess.Popen(
                command,
                cwd=str(cwd),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        else:
            subprocess.Popen(command, cwd=str(cwd))
        return 0
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
        return 127


def run_dev(service: str) -> int:
    if service == "all":
        code = db_up()
        if code != 0:
            return code

        for item in ("backend", "frontend", "ai", "sensor"):
            code = start_detached(item)
            if code != 0:
                return code
        print("Started backend, frontend, ai, and sensor in separate terminals.")
        return 0

    if service == "backend" and not ensure_java_home():
        return 1

    resolved = dev_command(service)
    if resolved is None:
        return 1

    command, cwd = resolved
    return run_command(command, cwd)


def python_files_for_compile(service_dir: Path) -> list[str]:
    ignored = {".venv", "venv", "__pycache__", "node_modules"}
    files: list[str] = []

    for path in service_dir.rglob("*.py"):
        try:
            relative = path.relative_to(service_dir)
        except ValueError:
            continue
        if any(part in ignored for part in relative.parts):
            continue
        files.append(str(relative))

    return sorted(files)


def test_python_service(service_dir: Path) -> int:
    files = python_files_for_compile(service_dir)
    if files:
        code = run_command([service_python(service_dir), "-m", "py_compile", *files], service_dir)
        if code != 0:
            return code

    return run_command([service_python(service_dir), "-m", "unittest", "discover", "-s", "tests"], service_dir)


def test_backend() -> int:
    return run_backend_maven("test")


def test_frontend() -> int:
    return run_command(npm_command("run", "build"), FRONTEND_DIR)


def test_ai() -> int:
    return test_python_service(AI_DIR)


def test_iot() -> int:
    return test_python_service(IOT_DIR)


def run_tests(target: str) -> int:
    steps = {
        "backend": test_backend,
        "frontend": test_frontend,
        "ai": test_ai,
        "iot": test_iot,
    }

    if target != "all":
        return steps[target]()

    for name in ("backend", "frontend", "ai", "iot"):
        print(f"\n== test {name} ==")
        code = steps[name]()
        if code != 0:
            return code
    return 0


def clean_targets() -> list[Path]:
    explicit = [
        FRONTEND_DIR / "node_modules",
        FRONTEND_DIR / "dist",
        FRONTEND_DIR / ".vite",
        ROOT / "front-end",
        BACKEND_DIR / "target",
        AI_DIR / ".venv",
        AI_DIR / "venv",
        AI_DIR / "__pycache__",
        IOT_DIR / ".venv",
        IOT_DIR / "venv",
        IOT_DIR / "__pycache__",
    ]

    targets: list[Path] = [path for path in explicit if path.exists()]
    skip_dirs = {".git", "node_modules", "target", ".venv", "venv", "dist", ".vite"}

    for current, dirs, _files in os.walk(ROOT):
        dirs[:] = [item for item in dirs if item not in skip_dirs]
        for dirname in list(dirs):
            if dirname == "__pycache__":
                targets.append(Path(current) / dirname)

    unique: list[Path] = []
    seen: set[Path] = set()
    for target in targets:
        resolved = target.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(target)
    return unique


def run_clean(yes: bool) -> int:
    targets = clean_targets()
    if not targets:
        print("Nothing to clean.")
        return 0

    print("Clean targets:")
    for target in targets:
        print(f"- {target.relative_to(ROOT)}")

    if not yes:
        answer = input("Delete these generated files/directories? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Clean cancelled.")
            return 0

    for target in targets:
        resolved = target.resolve()
        if not is_inside_workspace(resolved):
            print(f"Refusing to delete outside workspace: {resolved}")
            return 1
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
        print(f"Removed: {target.relative_to(ROOT)}")

    return 0


def print_check(name: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {name}{suffix}")


def check_version(name: str, command: list[str], required: bool = True) -> bool:
    executable = command[0]
    if not Path(executable).exists() and shutil.which(executable) is None:
        print_check(name, not required, f"not found: {executable}")
        return not required

    code, output = capture_command(command)
    first_line = output.splitlines()[0] if output else ""
    ok = code == 0
    print_check(name, ok, first_line)
    return ok or not required


def run_doctor() -> int:
    print(f"Project root: {ROOT}")
    all_ok = True

    all_ok &= check_version("Python", [sys.executable, "--version"])

    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java_bin = Path(java_home) / "bin" / ("java.exe" if IS_WINDOWS else "java")
        print_check("JAVA_HOME", java_bin.exists(), java_home)
        all_ok &= java_bin.exists()
    else:
        print_check("JAVA_HOME", False, "not set")
        all_ok = False

    all_ok &= check_version("Java", ["java", "-version"])

    maven = maven_executable()
    if maven:
        all_ok &= check_version("Maven", [maven, "-version"])
    else:
        wrapper = BACKEND_DIR / ("mvnw.cmd" if IS_WINDOWS else "mvnw")
        print_check("Maven", wrapper.exists(), f"wrapper: {wrapper.relative_to(ROOT)}")
        all_ok &= wrapper.exists()

    all_ok &= check_version("Node", ["node", "-v"])
    all_ok &= check_version("npm", npm_command("-v"))
    all_ok &= check_version("Docker", ["docker", "--version"], required=False)

    return 0 if all_ok else 1


def choose(title: str, options: list[tuple[str, str]]) -> str | None:
    print(f"\n== {title} ==")
    for index, (_value, label) in enumerate(options, start=1):
        print(f"{index}. {label}")
    print("0. Back")

    answer = input("Choose: ").strip()
    if answer in {"0", ""}:
        return None
    try:
        index = int(answer)
    except ValueError:
        print("Invalid choice.")
        return None
    if index < 1 or index > len(options):
        print("Invalid choice.")
        return None
    return options[index - 1][0]


def interactive_menu() -> int:
    while True:
        action = choose(
            "Smart Study Room",
            [
                ("setup", "Setup"),
                ("dev", "Dev"),
                ("db", "Database"),
                ("test", "Test"),
                ("clean", "Clean"),
                ("doctor", "Doctor"),
                ("exit", "Exit"),
            ],
        )

        if action is None:
            continue
        if action == "exit":
            return 0
        if action == "doctor":
            run_doctor()
            continue
        if action == "clean":
            run_clean(yes=False)
            continue
        if action == "setup":
            target = choose("Setup", [(item, item) for item in SETUP_TARGETS])
            if target:
                run_setup(target)
            continue
        if action == "dev":
            service = choose("Dev", [(item, item) for item in DEV_SERVICES])
            if service:
                run_dev(service)
            continue
        if action == "db":
            db_action = choose("Database", [(item, item) for item in DB_ACTIONS])
            if db_action:
                run_db(db_action)
            continue
        if action == "test":
            target = choose("Test", [(item, item) for item in TEST_TARGETS])
            if target:
                run_tests(target)


def run_db(action: str) -> int:
    if action == "up":
        return db_up()
    if action == "down":
        return db_down()
    if action == "logs":
        return db_logs()
    if action == "ps":
        return db_ps()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smart Study Room terminal helper.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    setup = subparsers.add_parser("setup", help="Prepare environment, dependencies, or DB.")
    setup.add_argument("target", nargs="?", default="all", choices=SETUP_TARGETS)

    dev = subparsers.add_parser("dev", help="Run development services.")
    dev.add_argument("service", choices=DEV_SERVICES)

    test = subparsers.add_parser("test", help="Run project checks.")
    test.add_argument("target", nargs="?", default="all", choices=TEST_TARGETS)

    db = subparsers.add_parser("db", help="Manage local MySQL compose service.")
    db.add_argument("action", choices=DB_ACTIONS)

    clean = subparsers.add_parser("clean", help="Remove generated files.")
    clean.add_argument("--yes", action="store_true", help="Skip confirmation prompt.")

    subparsers.add_parser("doctor", help="Check local development tools.")

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        return interactive_menu()

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "setup":
        return run_setup(args.target)
    if args.command == "dev":
        return run_dev(args.service)
    if args.command == "test":
        return run_tests(args.target)
    if args.command == "db":
        return run_db(args.action)
    if args.command == "clean":
        return run_clean(args.yes)
    if args.command == "doctor":
        return run_doctor()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
