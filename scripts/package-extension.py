#!/usr/bin/env python3
"""
CONTINUO — Chrome Extension Packaging Engine
Reproducible builder for creating clean, production-ready extension distribution ZIPs.

Tasks:
1. Validates extension/manifest.json (Manifest V3 schema & file existence).
2. Cleans previous dist/ artifacts.
3. Bundles strictly required extension files into dist/continuo-extension.zip.
4. Audits the archive to ensure:
   - manifest.json is present at root.
   - All runtime assets (popup, background, content script) are included.
   - Zero secrets, private keys, or credentials are leaked.
   - Zero repository/backend/database/test files are included.
"""

import os
import sys
import json
import shutil
import zipfile
import re
from pathlib import Path

# Paths relative to repository root
REPO_ROOT = Path(__file__).resolve().parent.parent
EXT_DIR = REPO_ROOT / "extension"
DIST_DIR = REPO_ROOT / "dist"
ZIP_PATH = DIST_DIR / "continuo-extension.zip"

FORBIDDEN_PATTERNS = [
    r"\.git",
    r"\.env",
    r"\.venv",
    r"__pycache__",
    r"backend",
    r"tests",
    r"\.db$",
    r"\.py$",
    r"node_modules",
    r"\.pem$",
    r"\.key$",
    r"secret",
    r"credentials"
]

SECRET_PATTERNS = [
    r"(?i)api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
    r"(?i)secret[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
    r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----",
    r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"  # Hardcoded JWT
]

def step(msg: str):
    print(f"[*] {msg}")

def pass_step(msg: str):
    print(f"  [PASS] {msg}")

def fail_step(msg: str):
    print(f"  [FAIL] {msg}")
    sys.exit(1)

def validate_manifest(manifest_path: Path) -> dict:
    step("Validating extension/manifest.json...")
    if not manifest_path.exists():
        fail_step(f"manifest.json not found at {manifest_path}")

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        fail_step(f"Failed to parse manifest.json: {e}")

    # Schema Checks
    if manifest.get("manifest_version") != 3:
        fail_step(f"manifest_version must be 3 (got {manifest.get('manifest_version')})")
    if not manifest.get("name"):
        fail_step("Manifest missing 'name'")
    if not manifest.get("version"):
        fail_step("Manifest missing 'version'")

    # File Reference Checks
    popup = manifest.get("action", {}).get("default_popup")
    if popup and not (EXT_DIR / popup).exists():
        fail_step(f"Action default_popup '{popup}' does not exist on disk.")

    sw = manifest.get("background", {}).get("service_worker")
    if sw and not (EXT_DIR / sw).exists():
        fail_step(f"Background service_worker '{sw}' does not exist on disk.")

    for cs in manifest.get("content_scripts", []):
        for js_file in cs.get("js", []):
            if not (EXT_DIR / js_file).exists():
                fail_step(f"Content script '{js_file}' does not exist on disk.")

    pass_step(f"Manifest V3 valid for '{manifest.get('name')}' (v{manifest.get('version')})")
    return manifest

def collect_extension_files(ext_dir: Path) -> list[tuple[Path, str]]:
    """
    Collect strictly necessary extension files.
    Returns list of (absolute_source_path, relative_archive_path).
    """
    step("Collecting extension assets...")
    collected = []
    
    # Required core files
    core_files = [
        "manifest.json",
        "popup.html",
        "popup.css",
        "popup.js",
        "background.js",
        "content.js"
    ]
    
    for filename in core_files:
        src = ext_dir / filename
        if src.exists():
            collected.append((src, filename))
        else:
            fail_step(f"Required extension file missing: {filename}")

    # Optional extension assets/icons
    assets_dir = ext_dir / "assets"
    if assets_dir.exists() and assets_dir.is_dir():
        for root, _, files in os.walk(assets_dir):
            for f in files:
                abs_f = Path(root) / f
                rel_f = abs_f.relative_to(ext_dir).as_posix()
                collected.append((abs_f, rel_f))

    for _, rel in collected:
        print(f"    + {rel}")
    pass_step(f"Collected {len(collected)} extension files.")
    return collected

def package_zip(collected_files: list[tuple[Path, str]], dest_zip: Path):
    step(f"Building archive {dest_zip.name}...")
    dest_zip.parent.mkdir(parents=True, exist_ok=True)

    if dest_zip.exists():
        dest_zip.unlink()

    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for abs_src, arc_rel in collected_files:
            zf.write(abs_src, arcname=arc_rel)

    size_kb = dest_zip.stat().st_size / 1024
    pass_step(f"Created {dest_zip} ({size_kb:.1f} KB)")

def audit_archive(dest_zip: Path):
    step("Auditing package contents for security & hygiene...")
    with zipfile.ZipFile(dest_zip, "r") as zf:
        namelist = zf.namelist()

        # 1. Root manifest check
        if "manifest.json" not in namelist:
            fail_step("Archive root does NOT contain manifest.json!")
        pass_step("Archive root contains manifest.json")

        # 2. Forbidden repository files check
        for name in namelist:
            for pat in FORBIDDEN_PATTERNS:
                if re.search(pat, name):
                    fail_step(f"Forbidden file/path detected in package: {name} (matched {pat})")
        pass_step("Archive contains zero repository/backend/database/test files")

        # 3. Secret and credential leak check
        for info in zf.infolist():
            if info.filename.endswith((".js", ".html", ".css", ".json")):
                with zf.open(info.filename) as f:
                    content = f.read().decode("utf-8", errors="ignore")
                    for sec_pat in SECRET_PATTERNS:
                        if re.search(sec_pat, content):
                            fail_step(f"Potential secret pattern found in {info.filename} (pattern: {sec_pat})")
        pass_step("Archive scanned: zero secrets or credentials detected")

def main():
    print("============================================================")
    print("CONTINUO CHROME EXTENSION PACKAGER")
    print("============================================================\n")

    manifest = validate_manifest(EXT_DIR / "manifest.json")
    collected = collect_extension_files(EXT_DIR)
    package_zip(collected, ZIP_PATH)
    audit_archive(ZIP_PATH)

    print("\n============================================================")
    print(f"SUCCESS: Package ready at {ZIP_PATH.relative_to(REPO_ROOT)}")
    print(f"Archive Size: {ZIP_PATH.stat().st_size} bytes")
    print("============================================================\n")

if __name__ == "__main__":
    main()
