from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import os
import subprocess
import sys


class _Style:
    @staticmethod
    def SUCCESS(msg: str) -> str:
        return msg

    @staticmethod
    def WARNING(msg: str) -> str:
        return msg

    @staticmethod
    def ERROR(msg: str) -> str:
        return msg


class _Stdout:
    @staticmethod
    def write(msg: str) -> None:
        print(msg)


class _CommandProxy:
    style = _Style()
    stdout = _Stdout()


def _load_impl():
    path = Path(__file__).with_name("seed_demo_data_impl.py")
    spec = spec_from_file_location("seed_demo_data_impl_module", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"无法加载 seed_demo_data_impl: {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(command, *args, **options):
    module = _load_impl()
    return module.run(command, *args, **options)


def _bootstrap_django() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"
    if not (backend_dir / "manage.py").exists() and Path("/app/manage.py").exists():
        backend_dir = Path("/app")
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    import django

    django.setup()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed demo data from scripts/generate")
    parser.add_argument("--use-docker", action="store_true", help="在 Docker 容器中执行")
    args = parser.parse_args()

    if args.use_docker:
        docker_cmd = ["docker", "exec", "hotelink-backend-dev", "python", "/scripts/generate/seed_demo_data.py"]
        print("[seed-demo] running in docker:", " ".join(docker_cmd))
        return subprocess.call(docker_cmd)

    _bootstrap_django()
    run(_CommandProxy())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
