from __future__ import annotations

import argparse
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
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


def _load_seed_module():
	path = Path(__file__).with_name("seed_hotels_bulk_impl.py")
	spec = spec_from_file_location("seed_hotels_bulk_impl_for_import", path)
	if not spec or not spec.loader:
		raise RuntimeError(f"无法加载 seed_hotels_bulk_impl: {path}")
	module = module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def add_arguments(parser) -> None:
	module = _load_seed_module()
	module.add_arguments(parser)


def run(command, *args, **options):
	module = _load_seed_module()
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
	parser = argparse.ArgumentParser(description="Import hotel seeds from dist images")
	add_arguments(parser)
	parser.add_argument("--use-docker", action="store_true", help="在 Docker 容器中执行")
	args = parser.parse_args()

	if args.use_docker:
		docker_cmd = [
			"docker",
			"exec",
			"hotelink-backend-dev",
			"python",
			"/scripts/generate/import_hotels_from_dist_images.py",
			"--count",
			str(args.count),
			"--seed",
			str(args.seed),
		]
		if args.overwrite:
			docker_cmd.append("--overwrite")
		if args.images_dir:
			docker_cmd.extend(["--images-dir", args.images_dir])
		print("[import-hotels] running in docker:", " ".join(docker_cmd))
		return subprocess.call(docker_cmd)

	_bootstrap_django()
	run(
		_CommandProxy(),
		count=args.count,
		overwrite=args.overwrite,
		images_dir=args.images_dir,
		seed=args.seed,
	)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
