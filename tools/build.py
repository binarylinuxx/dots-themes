#!/usr/bin/env python3
"""Builds every package in list.json into a .blx, plus index.json.

    python3 tools/build.py [--out build] [--base-url URL]

A .blx is a zstd-compressed tar with manifest.json at its root, the same as
`blxshell pack` makes. Entries are sorted and their times, owners and modes
normalised, so the same folder always gives the same bytes (and the same
sha256 in the index).

index.json is what `blxshell install <id>` and `blxshell search` read:

    {
      "schema": 1,
      "project": "blxshell",
      "name": "...",
      "repository": "owner/name",
      "packages": [
        { "id", "type", "name", "version", "description", "compositors",
          "permissions", "blxshell", "tags", "previews", "wallpaper",
          "file", "url", "sha256", "size" }

"wallpaper" is true for a theme that ships one, so the store can say so.
      ]
    }

`url` is where the file is published: base-url + file. The release workflow
uploads everything in the output folder to the "packages" release, so the
default base is that release's download address.
"""
import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compress(data: bytes) -> bytes:
    try:
        from compression import zstd  # Python 3.14+
        return zstd.compress(data, level=19)
    except ImportError:
        if not shutil.which("zstd"):
            sys.exit("need the zstd command (or Python 3.14+)")
        return subprocess.run(["zstd", "-19", "-q", "-c"], input=data, capture_output=True, check=True).stdout


def committed_files(folder: str) -> set:
    """The package's files as they are in the repository (relative paths)."""
    result = set()
    for directory, folders, files in os.walk(folder):
        folders[:] = [f for f in folders if f != "__pycache__"]
        for name in files:
            if not name.endswith(".pyc"):
                result.add(os.path.relpath(os.path.join(directory, name), folder).replace(os.sep, "/"))
    return result


def build(folder: str, manifest: dict, workdir: str) -> str:
    """Runs the package's build.sh in a copy of it; the folder to pack."""
    copy = os.path.join(workdir, manifest["id"])
    shutil.copytree(folder, copy, symlinks=True)
    print(f"building {manifest['id']} with build.sh", flush=True)
    result = subprocess.run(["bash", "-euo", "pipefail", "./build.sh"], cwd=copy, timeout=20 * 60)
    if result.returncode != 0:
        sys.exit(f"{manifest['id']}: build.sh failed ({result.returncode})")
    # Keep what was committed, plus bin/; drop the build's leftovers.
    keep = committed_files(folder)
    for directory, folders, files in os.walk(copy, topdown=False):
        for name in files:
            full = os.path.join(directory, name)
            relative = os.path.relpath(full, copy).replace(os.sep, "/")
            if os.path.islink(full):
                sys.exit(f"{manifest['id']}: the build made a symlink, {relative}")
            if relative not in keep and not relative.startswith(("bin/", "lib/")):
                os.remove(full)
        for name in folders:
            full = os.path.join(directory, name)
            if os.path.isdir(full) and not os.listdir(full):
                os.rmdir(full)
    native = (manifest.get("plugin") or {}).get("native")
    if native and not os.path.isfile(os.path.join(copy, native)):
        sys.exit(f"{manifest['id']}: build.sh didn't make {native}")
    program = (manifest.get("plugin") or {}).get("exec") or []
    if program:
        target = os.path.join(copy, program[0])
        if not os.path.isfile(target):
            sys.exit(f"{manifest['id']}: build.sh didn't make {program[0]}")
        if not os.access(target, os.X_OK):
            sys.exit(f"{manifest['id']}: {program[0]} isn't executable after the build")
    return copy


def pack(folder: str) -> bytes:
    """The folder as a reproducible tar.zst."""
    paths = []
    for directory, folders, files in os.walk(folder):
        folders[:] = sorted(f for f in folders if f != "__pycache__")
        for name in folders + files:
            full = os.path.join(directory, name)
            if name.endswith(".pyc"):
                continue
            if os.path.islink(full):
                sys.exit(f"{full} is a symlink; packages hold only files and folders")
            paths.append(full)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for full in sorted(paths, key=lambda p: os.path.relpath(p, folder)):
            relative = os.path.relpath(full, folder).replace(os.sep, "/")
            info = tar.gettarinfo(full, arcname=relative + ("/" if os.path.isdir(full) else ""))
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            if info.isdir():
                info.mode = 0o755
                tar.addfile(info)
            else:
                info.mode = 0o755 if os.access(full, os.X_OK) else 0o644
                with open(full, "rb") as f:
                    tar.addfile(info, f)
    return compress(buffer.getvalue())


def main():
    repository = os.environ.get("GITHUB_REPOSITORY", "binarylinuxx/dots-themes")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default=os.path.join(ROOT, "build"))
    parser.add_argument("--base-url", default=f"https://github.com/{repository}/releases/download/packages/")
    parser.add_argument("--raw-url", default=f"https://raw.githubusercontent.com/{repository}/main/")
    args = parser.parse_args()

    with open(os.path.join(ROOT, "list.json"), encoding="utf-8") as f:
        listing = json.load(f)
    if os.path.isdir(args.out):
        shutil.rmtree(args.out)
    os.makedirs(args.out)

    project = listing.get("project", "blxshell")
    index = {"schema": 1, "project": project, "name": listing.get("name", repository), "repository": repository,
             "packages": []}
    for entry in listing["packages"]:
        folder = os.path.join(ROOT, entry["path"])
        with open(os.path.join(folder, "manifest.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        file = f"{manifest['id']}-{manifest['version']}.blx"
        if os.path.isfile(os.path.join(folder, "build.sh")):
            with tempfile.TemporaryDirectory() as workdir:
                data = pack(build(folder, manifest, workdir))
        else:
            data = pack(folder)
        with open(os.path.join(args.out, file), "wb") as f:
            f.write(data)
        plugin = manifest.get("plugin") or {}
        index["packages"].append({
            "id": manifest["id"],
            "project": manifest.get("project", "blxshell"),
            "type": manifest["type"],
            "name": manifest["name"],
            "version": manifest["version"],
            "description": manifest.get("description", ""),
            "compositors": manifest.get("compositors", []),
            "permissions": plugin.get("permissions", []),
            "blxshell": manifest.get("blxshell", ""),
            "tags": manifest.get("tags", []),
            "wallpaper": bool(manifest.get("wallpaper")),
            "previews": [args.raw_url + entry["path"] + "/" + p for p in manifest.get("previews", [])],
            "readme": (args.raw_url + entry["path"] + "/README.md"
                       if os.path.isfile(os.path.join(folder, "README.md")) else ""),
            "license": manifest.get("license", ""),
            "authors": [a if isinstance(a, str) else a.get("name", "") for a in manifest.get("authors", [])],
            "file": file,
            "url": args.base_url + file,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        })
        print(f"{file}  {len(data)} bytes")

    with open(os.path.join(args.out, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"index.json  {len(index['packages'])} package(s)")


if __name__ == "__main__":
    main()
