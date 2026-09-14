#!/usr/bin/env python3
"""
CONTINUO — Chrome Extension Packaging Engine
Reproducible builder for creating clean, production-ready extension distribution ZIPs.

Tasks:
1. Validates extension/manifest.json (Manifest V3 schema & file existence).
2. Supports --production mode:
   - Stages extension assets into a temporary clean directory.
   - Replaces development localhost/port URLs with production HTTPS endpoints (api.continuo.ai).
   - Sanitizes manifest host permissions and content script matches to zero localhost.
   - Audits the final ZIP to enforce ZERO occurrences of localhost, 127.0.0.1, 8008, 8000.
3. Cleans previous dist/ artifacts.
4. Bundles strictly required extension files into dist/continuo-extension.zip.
5. Audits the archive to ensure:
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

def validate_manifest(manifest_path: Path, ext_base_dir: Path) -> dict:
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
    if popup and not (ext_base_dir / popup).exists():
        fail_step(f"Action default_popup '{popup}' does not exist on disk.")

    sw = manifest.get("background", {}).get("service_worker")
    if sw and not (ext_base_dir / sw).exists():
        fail_step(f"Background service_worker '{sw}' does not exist on disk.")

    for cs in manifest.get("content_scripts", []):
        for js_file in cs.get("js", []):
            if not (ext_base_dir / js_file).exists():
                fail_step(f"Content script '{js_file}' does not exist on disk.")

    # Icon Reference Checks
    icons = manifest.get("icons", {})
    for size, icon_path in icons.items():
        if not (ext_base_dir / icon_path).exists():
            fail_step(f"Manifest icon '{icon_path}' ({size}x{size}) does not exist on disk.")

    pass_step(f"Manifest V3 valid for '{manifest.get('name')}' (v{manifest.get('version')})")
    return manifest

def validate_state_machine(ext_dir: Path):
    step("Validating Extension 14-State Machine integrity...")
    popup_html = (ext_dir / "popup.html").read_text(encoding="utf-8")
    popup_js = (ext_dir / "popup.js").read_text(encoding="utf-8")

    required_html_elements = [
        "auth-panel",
        "no-ai-panel",
        "active-ai-panel",
        "handoff-panel",
        "error-panel",
        "session-expired-notice",
        "clipboard-fallback-box",
        "project-error-state",
        "destination-hint",
        "empty-chat-notice"
    ]

    for elem_id in required_html_elements:
        if elem_id not in popup_html:
            fail_step(f"popup.html missing state element: #{elem_id}")
        print(f"    [OK] Element #{elem_id} confirmed")

    required_js_states = [
        "isCapturing",
        "sessionExpiredNotice",
        "clipboardFallbackBox",
        "projectErrorState",
        "triggerContinuation",
        "resolveApiBase"
    ]

    for sym in required_js_states:
        if sym not in popup_js:
            fail_step(f"popup.js missing state controller symbol: {sym}")
        print(f"    [OK] State controller {sym} confirmed")

    pass_step("All required extension state machine handlers and DOM elements verified.")

def prepare_production_staging(source_dir: Path, staging_dir: Path) -> Path:
    step("Staging production extension assets (zero-localhost transformation)...")
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    shutil.copytree(source_dir, staging_dir)

    # 1. Transform manifest.json
    manifest_path = staging_dir / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Clean host_permissions: remove all localhost/127.0.0.1 and old placeholder
    new_host_perms = []
    for perm in manifest.get("host_permissions", []):
        if not ("127.0.0.1" in perm or "localhost" in perm or "continuo.ai" in perm):
            new_host_perms.append(perm)
    for prod_perm in ["https://api.continuo.run.place/*", "https://continuo.run.place/*", "https://*.continuo.run.place/*"]:
        if prod_perm not in new_host_perms:
            new_host_perms.append(prod_perm)
    manifest["host_permissions"] = new_host_perms

    # Clean content_scripts matches
    for cs in manifest.get("content_scripts", []):
        new_matches = []
        for match in cs.get("matches", []):
            if not ("127.0.0.1" in match or "localhost" in match or "continuo.ai" in match):
                new_matches.append(match)
        for prod_match in ["https://continuo.run.place/*", "https://*.continuo.run.place/*"]:
            if prod_match not in new_matches:
                new_matches.append(prod_match)
        cs["matches"] = new_matches

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    pass_step("Staged manifest.json: converted to live production origins (continuo.run.place)")

    # 2. Transform background.js
    bg_path = staging_dir / "background.js"
    bg_code = bg_path.read_text(encoding="utf-8")
    bg_code = bg_code.replace("http://127.0.0.1:8008/api/v1", "https://api.continuo.run.place/api/v1")
    bg_code = bg_code.replace("http://127.0.0.1:8000/api/v1", "https://api.continuo.run.place/api/v1")
    bg_code = bg_code.replace("https://api.continuo.ai/api/v1", "https://api.continuo.run.place/api/v1")
    bg_path.write_text(bg_code, encoding="utf-8")
    pass_step("Staged background.js: updated API endpoints to https://api.continuo.run.place/api/v1")

    # 3. Transform popup.js
    popup_js_path = staging_dir / "popup.js"
    p_code = popup_js_path.read_text(encoding="utf-8")
    p_code = p_code.replace("http://127.0.0.1:8008/api/v1", "https://api.continuo.run.place/api/v1")
    p_code = p_code.replace("http://127.0.0.1:8000/api/v1", "https://api.continuo.run.place/api/v1")
    p_code = p_code.replace("https://api.continuo.ai/api/v1", "https://api.continuo.run.place/api/v1")
    p_code = p_code.replace("http://localhost:8000/", "https://continuo.run.place/")
    p_code = p_code.replace("https://continuo.ai/", "https://continuo.run.place/")
    p_code = p_code.replace("127.0.0.1:8000 (Online)", "api.continuo.run.place (Online)")
    p_code = p_code.replace("api.continuo.ai (Online)", "api.continuo.run.place (Online)")
    p_code = p_code.replace("api.continuo.ai", "api.continuo.run.place")
    p_code = p_code.replace(
        'tab.url.includes("localhost") || tab.url.includes("127.0.0.1")',
        'tab.url.includes("continuo.run.place")'
    )
    p_code = p_code.replace(
        'DEFAULT_API_BASE.includes("127.0.0.1") || DEFAULT_API_BASE.includes("localhost")',
        'false'
    )
    popup_js_path.write_text(p_code, encoding="utf-8")
    pass_step("Staged popup.js: zero localhost references; updated workspace & API URLs to continuo.run.place")

    # 4. Transform popup.html
    popup_html_path = staging_dir / "popup.html"
    p_html = popup_html_path.read_text(encoding="utf-8")
    p_html = p_html.replace("127.0.0.1:8008", "api.continuo.run.place")
    p_html = p_html.replace("api.continuo.ai", "api.continuo.run.place")
    popup_html_path.write_text(p_html, encoding="utf-8")
    pass_step("Staged popup.html: gateway display updated to api.continuo.run.place")

    # 5. Transform content.js
    content_js_path = staging_dir / "content.js"
    c_code = content_js_path.read_text(encoding="utf-8")
    c_code = c_code.replace(
        'host === "localhost" || host === "127.0.0.1" || host.includes("continuo")',
        'host.includes("continuo")'
    )
    content_js_path.write_text(c_code, encoding="utf-8")
    pass_step("Staged content.js: token auto-sync scoped to production host")

    return staging_dir

def collect_extension_files(ext_dir: Path) -> list[tuple[Path, str]]:
    """
    Collect strictly necessary extension files.
    Returns list of (absolute_source_path, relative_archive_path).
    """
    step("Collecting extension assets...")
    collected = []
    
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

def audit_archive(dest_zip: Path, is_production: bool = False):
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

        # 4. Zero-localhost audit for production release
        if is_production:
            step("Executing strict zero-localhost production audit...")
            forbidden_dev_terms = ["127.0.0.1", "localhost", ":8008", ":8000", "continuo.ai"]
            for info in zf.infolist():
                if info.filename.endswith((".js", ".html", ".css", ".json")):
                    with zf.open(info.filename) as f:
                        content = f.read().decode("utf-8", errors="ignore")
                        for term in forbidden_dev_terms:
                            if term in content:
                                fail_step(f"Production audit violation: '{term}' detected in {info.filename}")
            pass_step("Production audit PASSED: ZERO localhost / 127.0.0.1 / development port references in archive")

def main():
    is_production = "--production" in sys.argv
    build_mode = "PRODUCTION RELEASE" if is_production else "DEVELOPMENT BUILD"

    print("============================================================")
    print(f"CONTINUO CHROME EXTENSION PACKAGER [{build_mode}]")
    print("============================================================\n")

    build_dir = EXT_DIR
    staging_dir = DIST_DIR / "staging_production"

    try:
        if is_production:
            build_dir = prepare_production_staging(EXT_DIR, staging_dir)

        manifest = validate_manifest(build_dir / "manifest.json", build_dir)
        validate_state_machine(build_dir)
        collected = collect_extension_files(build_dir)
        package_zip(collected, ZIP_PATH)
        audit_archive(ZIP_PATH, is_production=is_production)

        print("\n============================================================")
        print(f"SUCCESS: Package ready at {ZIP_PATH.relative_to(REPO_ROOT)}")
        print(f"Build Mode: {build_mode}")
        print(f"Archive Size: {ZIP_PATH.stat().st_size} bytes")
        print("============================================================\n")
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
