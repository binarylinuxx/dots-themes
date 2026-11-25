#!/usr/bin/env python3
"""Checks the repository the way blxshell and the reviewers need it.

    python3 tools/validate.py

- list.json is well formed, ids are unique, and each path is a folder with a
  manifest.json whose id matches;
- each manifest passes schema/manifest.schema.json (when the jsonschema
  module is installed; CI installs it);
- every file a manifest names exists, and a plugin's program is executable;
- packages hold only regular files and folders (no links), under 64 MiB;
- no compiled binaries or archives: a compiled plugin commits its source and
  a build.sh, and only CI builds it (tools/build.py), so what reviewers read
  is what users run;
- no folder in plugins/ or themes/ is missing from list.json.

Exits 1 with a list of problems, 0 when everything passes.
"""
import json
import os
import stat
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
problems = []


def problem(where, text):
    problems.append(f"{where}: {text}")


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as error:
        problem(os.path.relpath(path, ROOT), f"can't read: {error}")
        return None


def schema_validator():
    try:
        import jsonschema
    except ImportError:
        print("note: jsonschema not installed, skipping schema checks (pip install jsonschema)")
        return None
    schema = load(os.path.join(ROOT, "schema", "manifest.schema.json"))
    return jsonschema.Draft202012Validator(schema) if schema else None


# Magic numbers of compiled code and archives. Anything starting with one of
# these is refused: a compiled plugin commits source and a build.sh instead.
BINARY_MAGIC = [
    (b"\x7fELF", "an ELF binary"),
    (b"\xfe\xed\xfa\xce", "a Mach-O binary"), (b"\xfe\xed\xfa\xcf", "a Mach-O binary"),
    (b"\xce\xfa\xed\xfe", "a Mach-O binary"), (b"\xcf\xfa\xed\xfe", "a Mach-O binary"),
    (b"\xca\xfe\xba\xbe", "a Mach-O or Java class file"),
    (b"MZ", "a Windows executable"),
    (b"\x00asm", "a WebAssembly module"),
    (b"!<arch>", "a static library"),
    (b"PK\x03\x04", "a zip archive"),
    (b"\x1f\x8b", "a gzip archive"),
    (b"\x28\xb5\x2f\xfd", "a zstd archive"),
    (b"BZh", "a bzip2 archive"),
    (b"\xfd7zXZ\x00", "an xz archive"),
    (b"7z\xbc\xaf\x27\x1c", "a 7z archive"),
    (b"Rar!", "a rar archive"),
]


def binary_kind(path):
    try:
        with open(path, "rb") as f:
            head = f.read(512)
    except OSError:
        return None
    for magic, kind in BINARY_MAGIC:
        if head.startswith(magic):
            # "MZ" and "BZh" are short; only count them with what follows.
            if magic == b"MZ" and b"PE\x00\x00" not in head and b"This program" not in head:
                continue
            return kind
    if len(head) >= 262 and head[257:262] == b"ustar":
        return "a tar archive"
    return None


def check_package(entry, validator, project="blxshell"):
    path = entry.get("path", "")
    where = path or "?"
    folder = os.path.normpath(os.path.join(ROOT, path))
    if not path or path.startswith("/") or ".." in path.split("/") or not folder.startswith(ROOT + os.sep):
        problem("list.json", f"bad path {path!r}")
        return
    if not os.path.isdir(folder):
        problem("list.json", f"{path} is not a folder")
        return
    total = 0
    for directory, folders, files in os.walk(folder):
        for name in folders + files:
            full = os.path.join(directory, name)
            mode = os.lstat(full).st_mode
            if stat.S_ISLNK(mode):
                problem(where, f"{os.path.relpath(full, folder)} is a symlink; packages hold only files and folders")
            elif stat.S_ISREG(mode):
                total += os.path.getsize(full)
                kind = binary_kind(full)
                if kind:
                    problem(where, f"{os.path.relpath(full, folder)} is {kind}. Compiled code isn't accepted: commit its "
                                   "source and a build.sh that builds it, and CI compiles it (see README)")
    if total > 64 << 20:
        problem(where, "larger than 64 MiB")
    manifest = load(os.path.join(folder, "manifest.json"))
    if manifest is None:
        return
    if validator:
        for error in validator.iter_errors(manifest):
            location = "/".join(str(part) for part in error.absolute_path) or "manifest"
            problem(where, f"{location}: {error.message}")
    if manifest.get("project", "blxshell") != project:
        problem(where, f"it's a package for {manifest.get('project')!r}, and this repository is for {project!r}")
    if manifest.get("id") != entry.get("id"):
        problem(where, f"manifest id {manifest.get('id')!r} doesn't match list.json's {entry.get('id')!r}")
    if os.path.basename(folder) != manifest.get("id"):
        problem(where, "the folder should be named after the id")
    named = list(manifest.get("previews", []))
    if manifest.get("icon"):
        named.append(manifest["icon"])
    if manifest.get("wallpaper"):
        named.append(manifest["wallpaper"])
    plugin = manifest.get("plugin") or {}
    program = plugin.get("exec") or []
    built = os.path.isfile(os.path.join(folder, "build.sh"))
    if plugin.get("facet"):
        named.append(plugin["facet"])
    # A program or library that build.sh makes isn't in the repository;
    # build.py checks it after building.
    if program and not built:
        named.append(program[0])
    if plugin.get("native") and not built:
        problem(where, "a native plugin commits its source and a build.sh; CI builds the library")
    for relative in named:
        target = os.path.join(folder, relative)
        if not os.path.isfile(target):
            problem(where, f"{relative} is named in the manifest but missing")
    if built and not os.access(os.path.join(folder, "build.sh"), os.X_OK):
        problem(where, f"build.sh is not executable (git update-index --chmod=+x {path}/build.sh)")
    if program and os.path.isfile(os.path.join(folder, program[0])):
        if not os.access(os.path.join(folder, program[0]), os.X_OK):
            problem(where, f"{program[0]} is not executable (git update-index --chmod=+x {path}/{program[0]})")
    if manifest.get("type") != "theme":
        problem(where, "this repository holds themes; plugins go to binarylinuxx/dots-plugins")
    if not manifest.get("previews"):
        problem(where, "themes need a preview (tools/wallpaper.py draws one next to the wallpaper)")


def main():
    listing = load(os.path.join(ROOT, "list.json"))
    if listing is None:
        return 1
    if listing.get("schema") != 1:
        problem("list.json", "schema must be 1")
    if not isinstance(listing.get("name"), str) or not listing["name"]:
        problem("list.json", "name is missing")
    entries = listing.get("packages")
    if not isinstance(entries, list):
        problem("list.json", "packages must be a list")
        entries = []
    validator = schema_validator()
    seen_ids, seen_paths = set(), set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not isinstance(entry.get("path"), str):
            problem("list.json", f"each package needs an id and a path: {entry!r}")
            continue
        if entry["id"] in seen_ids:
            problem("list.json", f"{entry['id']} is listed twice")
        seen_ids.add(entry["id"])
        seen_paths.add(os.path.normpath(entry["path"]))
        check_package(entry, validator, listing.get("project", "blxshell"))
    for kind in ("plugins", "themes"):
        base = os.path.join(ROOT, kind)
        if os.path.isdir(base):
            for name in sorted(os.listdir(base)):
                if os.path.isdir(os.path.join(base, name)) and os.path.normpath(f"{kind}/{name}") not in seen_paths:
                    problem(f"{kind}/{name}", "not listed in list.json")
    if problems:
        print("\n".join(problems))
        print(f"\n{len(problems)} problem(s)")
        return 1
    print(f"ok: {len(entries)} package(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
