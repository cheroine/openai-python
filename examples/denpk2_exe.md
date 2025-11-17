# Building a denpk2 executable

This repository cannot ship binaries directly, but the helper script
`scripts/build_denpk2_exe.py` automates packaging
[hax0r31337/denpk2](https://github.com/hax0r31337/denpk2) into a single-file
executable with [PyInstaller](https://pyinstaller.org/).

## Prerequisites

* Python 3.9+ on Windows is recommended if you need a `.exe`. Building on
  Linux or macOS will produce a binary for that platform instead.
* `pip` needs to be able to install `PyInstaller`. The script automatically
  installs it unless you pass `--skip-pyinstaller-install`.

## Usage

```powershell
# from the repository root
python scripts/build_denpk2_exe.py `
  --entry-script denpk2.py `
  --name denpk2 `
  --output-dir C:\\path\\to\\dist
```

The script downloads the repository archive from GitHub, extracts it into a
temporary directory, installs PyInstaller if missing, and then invokes it with
the `--onefile` flag so that the output is a single executable.

If you already have a checkout of the repository locally, reuse it with:

```powershell
python scripts/build_denpk2_exe.py --local-repo C:\\code\\denpk2 --entry-script denpk2.py
```

Additional PyInstaller flags (for example `--windowed`) can be forwarded by
specifying `--pyinstaller-arg --windowed`.

After the command finishes, the executable is copied into the folder specified
via `--output-dir`. On Windows it will have the `.exe` extension and can be run
immediately.
