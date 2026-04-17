#!/usr/bin/env python3
"""批量生成酒店数据脚本（统一由 scripts/generate 管理）。"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
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


def _run_local(args: argparse.Namespace) -> int:
    _bootstrap_django()
    from seed_hotels_bulk_impl import run

    run(
        _CommandProxy(),
        count=args.count,
        overwrite=args.overwrite,
        images_dir=args.images_dir,
        seed=args.seed,
        inventory_days=args.inventory_days,
    )
    return 0


def main() -> int:
    from seed_hotels_bulk_impl import add_arguments

    parser = argparse.ArgumentParser(description="Generate hotel seed data for HoteLink")
    add_arguments(parser)
    parser.add_argument("--use-docker", action="store_true", help="在 Docker 容器中执行")
    args = parser.parse_args()

    if args.use_docker:
        docker_cmd = [
            "docker",
            "exec",
            "hotelink-backend-dev",
            "python",
            "/scripts/generate/seed_hotels_bulk.py",
            "--count",
            str(args.count),
            "--seed",
            str(args.seed),
        ]
        if args.overwrite:
            docker_cmd.append("--overwrite")
        if args.images_dir:
            docker_cmd.extend(["--images-dir", args.images_dir])
        docker_cmd.extend(["--inventory-days", str(args.inventory_days)])
        print("[seed-hotels] running in docker:", " ".join(docker_cmd))
        return subprocess.call(docker_cmd)

    print("[seed-hotels] running locally via scripts/generate implementation")
    return _run_local(args)


if __name__ == "__main__":
    raise SystemExit(main())
