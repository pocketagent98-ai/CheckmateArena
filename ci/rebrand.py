#!/usr/bin/env python3
"""
rebrand.py - one-shot, idempotent rebrander for this project.

Run from the repository root (CI runs it automatically):
    python3 ci/rebrand.py

It does four things:
  1. Replaces the code token "UnityChess" everywhere it appears in TEXT files
     (.cs, .asmdef, .unity scenes, .md, .gitignore, ...) with NEW_TOKEN.
     Assembly references inside .asmdef files are by GUID, so renaming the
     assemblies does NOT break references.
  2. Renames every file whose name contains the old token (the .asmdef files
     and their .meta companions, plus the demo .gif).
  3. Updates the app's visible name / company / package id in
     ProjectSettings/ProjectSettings.asset.
  4. Refuses to guess: if an asset is still a Git-LFS pointer it warns loudly.

To change the branding, edit ONLY the four values below.
"""

import os
import re
import sys

# ----------------------------------------------------------------------
#  >>> EDIT THESE FOUR VALUES TO CHANGE THE BRANDING <<<
# ----------------------------------------------------------------------
NEW_TOKEN   = "CheckmateArena"                    # C#-safe identifier (no spaces)
NEW_DISPLAY = "Checkmate Arena"                   # name shown under the app icon
NEW_COMPANY = "PocketArcade"                       # developer / company name
NEW_BUNDLE  = "com.pocketarcade.checkmatearena"    # Android package id
# ----------------------------------------------------------------------

OLD_TOKEN = "UnityChess"

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

SKIP_DIRS = {".git", "Library", "Temp", "obj", "bin", "Logs", "UserSettings",
             "build", "Build", "Builds", ".idea", ".vs"}

TEXT_EXT = {".cs", ".asmdef", ".unity", ".uxml", ".uss", ".tss",
            ".md", ".asset", ".json", ".txt", ".cginc", ".shader"}

SKIP_FILES = {"LICENSE"}


def walk(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            yield os.path.join(dp, f)


def main():
    if not os.path.isdir(os.path.join(ROOT, "Assets")):
        sys.exit("ERROR: run this from the Unity project root (no Assets/ found).")

    # ---- 1. content replacement -------------------------------------
    changed = 0
    for path in walk(ROOT):
        base = os.path.basename(path)
        if base in SKIP_FILES:
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext not in TEXT_EXT and base != ".gitignore":
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = fh.read()
        except (UnicodeDecodeError, OSError):
            continue
        if OLD_TOKEN not in data:
            continue
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(data.replace(OLD_TOKEN, NEW_TOKEN))
        changed += 1
    print(f"[rebrand] content files updated: {changed}")

    # ---- 2. rename files whose name carries the token ---------------
    renamed = 0
    for path in list(walk(ROOT)):
        base = os.path.basename(path)
        if OLD_TOKEN in base:
            new_path = os.path.join(os.path.dirname(path), base.replace(OLD_TOKEN, NEW_TOKEN))
            if os.path.exists(new_path):
                continue
            os.rename(path, new_path)
            renamed += 1
    print(f"[rebrand] files renamed: {renamed}")

    # ---- 3. ProjectSettings (app name / company / package) ----------
    ps = os.path.join(ROOT, "ProjectSettings", "ProjectSettings.asset")
    if os.path.exists(ps):
        with open(ps, "r", encoding="utf-8", errors="replace") as fh:
            t = fh.read()
        if "git-lfs.github.com" in t:
            print("[rebrand] !! WARNING: ProjectSettings.asset is still a Git-LFS "
                  "pointer - clone with `lfs: true` / `git lfs pull`. "
                  "App name will NOT be applied.")
        else:
            t = re.sub(r"(?m)^(\s*productName:\s*).*$", r"\g<1>" + NEW_DISPLAY, t)
            t = re.sub(r"(?m)^(\s*companyName:\s*).*$", r"\g<1>" + NEW_COMPANY, t)
            t = re.sub(r"(?m)^(\s*)(Android|Standalone|iPhone|WebGL|VisionOS|tvOS|"
                       r"Lumin|PS4|PS5|XboxOne|Nintendo Switch)\s*:\s*com\.[^\s]+",
                       lambda m: f"{m.group(1)}{m.group(2)}: {NEW_BUNDLE}", t)
            t = re.sub(r"(?m)^(\s*bundleVersion:\s*).*$", r"\g<1>1.0", t)
            with open(ps, "w", encoding="utf-8") as fh:
                fh.write(t)
            print("[rebrand] ProjectSettings patched: "
                  f"productName='{NEW_DISPLAY}', companyName='{NEW_COMPANY}', bundle='{NEW_BUNDLE}'")

    print(f"[rebrand] done. Branding -> {NEW_DISPLAY} / {NEW_COMPANY} / {NEW_BUNDLE}")


if __name__ == "__main__":
    main()
