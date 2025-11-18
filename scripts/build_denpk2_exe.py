"""Utility script for building a Windows-friendly executable for denpk2.

The script automates downloading (or pointing at) the upstream repository,
optionally installs PyInstaller, and then invokes it with sane defaults to
produce a standalone binary.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from string import Template
from pathlib import Path
from typing import Iterable
from urllib.request import urlretrieve
import zipfile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download hax0r31337/denpk2 and build a single-file executable using "
            "PyInstaller."
        )
    )
    parser.add_argument(
        "--repo-url",
        default="https://github.com/hax0r31337/denpk2",
        help="Git repository URL to clone from.",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Git branch to download (default: %(default)s).",
    )
    parser.add_argument(
        "--entry-script",
        default="main.py",
        help=(
            "Python entry script inside the repository that launches the app. "
            "Update this if the project uses a different filename."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "denpk2-dist",
        help="Directory where the finished executable should be copied.",
    )
    parser.add_argument(
        "--local-repo",
        type=Path,
        help="Skip downloading and reuse an existing local checkout.",
    )
    parser.add_argument(
        "--pyinstaller-arg",
        action="append",
        dest="pyinstaller_args",
        default=[],
        help="Extra arguments forwarded to PyInstaller.",
    )
    parser.add_argument(
        "--name",
        default="denpk2",
        help="Name for the produced executable (default: %(default)s).",
    )
    parser.add_argument(
        "--keep-build-artifacts",
        action="store_true",
        help="Do not delete PyInstaller build directories after finishing.",
    )
    parser.add_argument(
        "--skip-pyinstaller-install",
        action="store_true",
        help="Assume PyInstaller is already installed.",
    )
    parser.add_argument(
        "--enable-drag-drop-wrapper",
        action="store_true",
        help=(
            "Inject a helper entry point that accepts files dropped onto the "
            "executable and forwards them to the original entry script."
        ),
    )
    return parser.parse_args()


def ensure_pyinstaller_installed(skip_install: bool) -> None:
    if importlib.util.find_spec("PyInstaller"):
        return
    if skip_install:
        raise RuntimeError(
            "PyInstaller is not installed and automatic installation was skipped."
        )
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyinstaller"], check=True
    )


def download_repo_archive(repo_url: str, branch: str, workdir: Path) -> Path:
    archive_url = repo_url.rstrip("/") + f"/archive/refs/heads/{branch}.zip"
    archive_path = workdir / "repo.zip"
    print(f"Downloading {archive_url} ...")
    urlretrieve(archive_url, archive_path)
    with zipfile.ZipFile(archive_path) as zf:
        zf.extractall(workdir)
        root = zf.namelist()[0].split("/")[0]
    return workdir / root


def run_pyinstaller(
    repo_dir: Path,
    entry_script: str,
    output_dir: Path,
    exe_name: str,
    extra_args: Iterable[str],
    keep_artifacts: bool,
) -> Path:
    script_path = repo_dir / entry_script
    if not script_path.exists():
        raise FileNotFoundError(
            f"Could not find entry script {entry_script!r} in {repo_dir}."
        )

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        exe_name,
        *extra_args,
        str(script_path),
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=repo_dir)

    produced = repo_dir / "dist" / (exe_name + (".exe" if os.name == "nt" else ""))
    if not produced.exists():
        raise FileNotFoundError("PyInstaller did not produce the expected binary.")
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / produced.name
    shutil.copy2(produced, final_path)

    if not keep_artifacts:
        shutil.rmtree(repo_dir / "build", ignore_errors=True)
        shutil.rmtree(repo_dir / "dist", ignore_errors=True)
        spec_file = repo_dir / f"{exe_name}.spec"
        if spec_file.exists():
            spec_file.unlink()
    return final_path


def create_drag_and_drop_entry(repo_dir: Path, target_entry: str) -> Path:
    """Create a temporary entry script that emulates drag-and-drop behavior."""

    wrapper_path = repo_dir / "_dragdrop_entry.py"
    template = Template(
        """
        \"\"\"A helper entry point that forwards dropped files to denpk2.\"\"\"
        import runpy
        import sys
        from pathlib import Path

        TARGET = Path(__file__).with_name($target_entry)

        def run_for_each(targets):
            if not TARGET.exists():
                raise SystemExit(f"Unable to locate {TARGET}")
            for raw in targets:
                candidate = Path(raw)
                if not candidate.exists():
                    print(f"Skipping {raw}: file not found", file=sys.stderr)
                    continue
                argv_backup = sys.argv[:]
                try:
                    sys.argv = [str(TARGET), str(candidate)]
                    runpy.run_path(str(TARGET), run_name="__main__")
                finally:
                    sys.argv = argv_backup

        def main():
            if len(sys.argv) == 1:
                print("Drag .npk/.nxpk files onto this executable to decode them.")
                return
            run_for_each(sys.argv[1:])

        if __name__ == "__main__":
            main()
        """
    )
    wrapper_code = textwrap.dedent(
        template.substitute(target_entry=repr(target_entry))
    )
    wrapper_path.write_text(wrapper_code, encoding="utf-8")
    return wrapper_path


def main() -> None:
    args = parse_args()
    ensure_pyinstaller_installed(args.skip_pyinstaller_install)

    def build_from_repo(repo_dir: Path) -> Path:
        entry_script = args.entry_script
        wrapper_path: Path | None = None
        if args.enable_drag_drop_wrapper:
            wrapper_path = create_drag_and_drop_entry(repo_dir, entry_script)
            entry_script = str(wrapper_path.relative_to(repo_dir))

        try:
            return run_pyinstaller(
                repo_dir,
                entry_script,
                args.output_dir,
                args.name,
                args.pyinstaller_args,
                args.keep_build_artifacts,
            )
        finally:
            if wrapper_path and wrapper_path.exists():
                wrapper_path.unlink()

    if args.local_repo:
        final_path = build_from_repo(args.local_repo.resolve())
        print(f"Executable available at {final_path}")
        return

    with tempfile.TemporaryDirectory() as tmp:
        repo_dir = download_repo_archive(args.repo_url, args.branch, Path(tmp)).resolve()
        final_path = build_from_repo(repo_dir)
        print(f"Executable available at {final_path}")


if __name__ == "__main__":
    main()
