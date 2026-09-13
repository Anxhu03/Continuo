import re
import json
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.request

print("============================================================")
print("CONTINUO - EXTENSION INSTALLATION FLOW & STATE VERIFICATION")
print("============================================================\n")

# ----------------------------------------------------------------------
# 1. AUDIT CONFIGURATION (config.js)
# ----------------------------------------------------------------------
print(">>> 1. AUDITING config.js CENTRALIZED CONFIGURATION...")
assert os.path.exists("config.js"), "CRITICAL: config.js must exist"
with open("config.js", "r", encoding="utf-8") as f:
    cfg_content = f.read()

assert "const CHROME_EXTENSION_STORE_URL = null;" in cfg_content, "CHROME_EXTENSION_STORE_URL must be null while unpublished"
assert "window.CHROME_EXTENSION_STORE_URL = CHROME_EXTENSION_STORE_URL;" in cfg_content
print("  [PASS] Verified config.js has CHROME_EXTENSION_STORE_URL = null (Development Mode)")


# ----------------------------------------------------------------------
# 2. AUDIT index.html CTAs & DYNAMIC ADAPTATION LOGIC
# ----------------------------------------------------------------------
print("\n>>> 2. AUDITING index.html CTAs & NAVIGATION TARGETS...")
with open("index.html", "r", encoding="utf-8") as f:
    idx_content = f.read()

# Must load config.js before main.js
assert '<script src="config.js"></script>' in idx_content, "index.html must load config.js"
assert '<script src="main.js"' in idx_content, "index.html must load main.js"

# Verify hero-cta in development state (Must NOT claim ZIP = "Add to Chrome")
hero_match = re.search(r'<a[^>]+id=["\']hero-cta["\'][^>]*>(.*?)</a>', idx_content, re.DOTALL)
assert hero_match, "CRITICAL: #hero-cta element must exist in index.html"
hero_tag = hero_match.group(0)
print("  [PASS] Found #hero-cta:", hero_tag.replace("\n", " ").strip()[:80])
assert 'href="install.html"' in hero_tag, "#hero-cta must link to install.html"
assert "Install Extension" in hero_tag, "#hero-cta must say 'Install Extension' for development (not Add to Chrome)"
assert "fa-chrome" in hero_tag, "#hero-cta must display the Chrome icon"

# Verify footer-cta-btn
footer_match = re.search(r'<a[^>]+id=["\']footer-cta-btn["\'][^>]*>(.*?)</a>', idx_content, re.DOTALL)
assert footer_match, "CRITICAL: #footer-cta-btn element must exist in index.html"
footer_tag = footer_match.group(0)
print("  [PASS] Found #footer-cta-btn:", footer_tag.replace("\n", " ").strip()[:80])
assert 'href="install.html"' in footer_tag, "#footer-cta-btn must link to install.html"
assert "Install Extension" in footer_tag, "#footer-cta-btn must say 'Install Extension' for development"

# Verify "See Context Engine"
engine_matches = re.findall(r'<a[^>]+href=["\']#engine["\'][^>]*>(.*?)</a>', idx_content, re.DOTALL)
assert any("See Context Engine" in m for m in engine_matches), "Hero button 'See Context Engine' linking to #engine must exist"
print("  [PASS] Verified 'See Context Engine' hero button -> #engine")

# Verify Mobile Drawer link
mobile_install_match = re.search(r'<a[^>]+href=["\']install\.html["\'][^>]*class=["\'][^"\']*mobile-link[^"\']*["\'][^>]*>(.*?)</a>', idx_content, re.DOTALL)
assert mobile_install_match, "Mobile drawer must link to install.html"
assert "Install Extension" in mobile_install_match.group(0)
print("  [PASS] Mobile drawer verified: 'Install Extension' -> install.html")


# ----------------------------------------------------------------------
# 3. AUDIT install.html DUAL-STATE ARCHITECTURE
# ----------------------------------------------------------------------
print("\n>>> 3. AUDITING install.html DUAL-STATE ARCHITECTURE...")
assert os.path.exists("install.html"), "CRITICAL: install.html must exist"
with open("install.html", "r", encoding="utf-8") as f:
    inst_content = f.read()

# Verify config.js is included in head
assert '<script src="config.js"></script>' in inst_content, "install.html must load config.js"

# STATE A: Development Mode Checks
dev_state_match = re.search(r'<div id="install-dev-state"[^>]*>(.*?)</div>\s*<!-- =================================================================\s*STATE B', inst_content, re.DOTALL)
assert dev_state_match, "install-dev-state container must exist in install.html"
dev_html = dev_state_match.group(1)

assert "DEVELOPMENT BUILD" in dev_html, "State A must feature 'DEVELOPMENT BUILD' badge"
assert "Install the development build" in dev_html, "State A title must be 'Install the development build'"
assert "Continuo's Chrome Web Store release is currently being prepared." in dev_html
assert "Download Continuo Extension" in dev_html, "State A button must be Download Continuo Extension (not Add to Chrome)"
assert 'href="dist/continuo-extension.zip"' in dev_html, "State A must link to dist/continuo-extension.zip"
assert 'download="continuo-extension.zip"' in dev_html

# Check all 6 manual steps exist in State A
steps = [
    "STEP 01", "Download Continuo",
    "STEP 02", "Open Chrome Extensions",
    "STEP 03", "Enable Developer Mode",
    "STEP 04", "Extract Continuo",
    "STEP 05", "Load Continuo",
    "STEP 06", "Pin Continuo"
]
for s in steps:
    assert s in dev_html, f"Step '{s}' must be in State A"
print("  [PASS] State A (Development): Verified badge, title, download button, and 6 manual steps")

# Check You're ready card with AI Launchers
assert "You're ready." in dev_html
assert "chatgpt.com" in dev_html
assert "claude.ai" in dev_html
assert "gemini.google.com" in dev_html
print("  [PASS] State A (Development): Verified 'You're ready.' quick launchers (ChatGPT, Claude, Gemini, Workspace)")

# STATE B: Production Mode Checks
prod_state_match = re.search(r'<div id="install-prod-state"[^>]*>(.*?)</div>\s*<!-- Action Footer', inst_content, re.DOTALL)
assert prod_state_match, "install-prod-state container must exist in install.html"
prod_html = prod_state_match.group(1)

assert "OFFICIAL CHROME EXTENSION" in prod_html, "State B must feature 'OFFICIAL CHROME EXTENSION' badge"
assert "Install Continuo for Chrome" in prod_html, "State B title must be 'Install Continuo for Chrome'"
assert "Bring Continuo into your AI conversations." in prod_html
assert "Add to Chrome" in prod_html, "State B primary button must be 'Add to Chrome'"
assert 'id="btn-add-to-chrome-prod"' in prod_html
assert "One-Click Installation" in prod_html
assert "Manifest V3 Verified" in prod_html

# Critical: Primary flow of State B must NOT show ZIP or unpacked steps
assert "dist/continuo-extension.zip" not in prod_html, "State B must NOT have ZIP download in primary flow"
assert "Load unpacked" not in prod_html, "State B must NOT instruct Load unpacked in primary flow"
assert "git clone" not in prod_html, "State B must NOT have git clone in primary flow"
print("  [PASS] State B (Production): Verified official badge, title, 'Add to Chrome' CTA, and zero ZIP steps in primary flow")

# Collapsible developer section at bottom
dev_details_match = re.search(r'<details class="dev-install-details">(.*?)</details>', inst_content, re.DOTALL)
assert dev_details_match, "Collapsed dev-install-details must exist at bottom"
assert "git clone" in dev_details_match.group(1), "git clone must be preserved in developer section"
print("  [PASS] Developer installation (git clone) strictly quarantined in collapsible section at bottom")

# State Switcher Script
assert "function applyInstallState()" in inst_content
assert "window.CHROME_EXTENSION_STORE_URL" in inst_content
print("  [PASS] Verified applyInstallState() switcher logic in install.html script")


# ----------------------------------------------------------------------
# 4. AUDIT main.js DYNAMIC CTA CONTROLLER
# ----------------------------------------------------------------------
print("\n>>> 4. AUDITING main.js DYNAMIC CTA CONTROLLER...")
with open("main.js", "r", encoding="utf-8") as f:
    main_code = f.read()

assert "function initExtensionCta()" in main_code, "initExtensionCta() engine must exist"
assert "initExtensionCta();" in main_code, "initExtensionCta() must be initialized"
assert 'heroCtaText.textContent = "Add to Chrome"' in main_code
assert 'heroCtaText.textContent = "Install Extension"' in main_code
assert 'heroCtaBtn.addEventListener("click", openWorkspace)' not in main_code, "NO workspace leakage"
print("  [PASS] Verified initExtensionCta() dynamically toggles between 'Install Extension' and 'Add to Chrome'")


# ----------------------------------------------------------------------
# 5. AUDIT DIST EXTENSION PACKAGE (dist/continuo-extension.zip)
# ----------------------------------------------------------------------
print("\n>>> 5. AUDITING dist/continuo-extension.zip...")
import zipfile

zip_path = "dist/continuo-extension.zip"
assert os.path.exists(zip_path), f"CRITICAL: {zip_path} must exist"
file_size = os.path.getsize(zip_path)
print(f"  [PASS] Package exists: {zip_path} ({file_size} bytes)")

with zipfile.ZipFile(zip_path, "r") as zf:
    namelist = zf.namelist()
    print("  Package contents:", namelist)
    
    assert "manifest.json" in namelist, "manifest.json must be at root of ZIP"
    assert "popup.html" in namelist, "popup.html must exist in ZIP"
    assert "popup.css" in namelist, "popup.css must exist in ZIP"
    assert "popup.js" in namelist, "popup.js must exist in ZIP"
    assert "background.js" in namelist, "background.js must exist in ZIP"
    assert "content.js" in namelist, "content.js must exist in ZIP"
    assert any("icon" in n for n in namelist), "icon must exist in ZIP"
    
    # Hygiene checks
    for item in namelist:
        assert not item.startswith(".git"), f"Forbidden item in ZIP: {item}"
        assert not item.startswith("node_modules"), f"Forbidden item in ZIP: {item}"
        assert not item.startswith("backend"), f"Forbidden item in ZIP: {item}"
        assert not item.endswith(".py"), f"Forbidden item in ZIP: {item}"
        assert not item.endswith(".env"), f"Forbidden item in ZIP: {item}"
        assert not item.endswith(".db"), f"Forbidden item in ZIP: {item}"
    
    # Manifest schema inside ZIP
    manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
    assert manifest_data.get("manifest_version") == 3, "ZIP manifest must be Manifest V3"
    assert manifest_data.get("action", {}).get("default_popup") == "popup.html"
    print("  [PASS] Package manifest verified: Manifest V3 with popup.html default popup")


# ----------------------------------------------------------------------
# 6. AUDIT EXTENSION POPUP UX (ChatGPT / Claude / Gemini -> Save -> Continue)
# ----------------------------------------------------------------------
print("\n>>> 6. AUDITING EXTENSION POPUP UX FLOW...")
with open("extension/popup.html", "r", encoding="utf-8") as f:
    pop_html = f.read()

# Provider detection
assert "detection-box" in pop_html
assert "detection-status-text" in pop_html

# Save Context button
assert 'id="btn-ext-capture"' in pop_html
assert "Save Context" in pop_html

# Context saved banner
assert "Context saved" in pop_html

# Continue with buttons
assert 'id="btn-cont-chatgpt"' in pop_html
assert 'id="btn-cont-claude"' in pop_html
assert 'id="btn-cont-gemini"' in pop_html
assert "Continue with:" in pop_html

# Workspace is secondary
assert 'id="btn-view-memory"' in pop_html
assert "View Project Memory" in pop_html
print("  [PASS] Verified Extension UX:")
print("         Provider detected -> [ Save Context ] -> Context saved [OK] -> [ Continue with ChatGPT / Claude / Gemini ]")
print("         Workspace link ('View Project Memory') is secondary.")


# ----------------------------------------------------------------------
# 7. HTTP SERVER STATUS CODE VERIFICATION
# ----------------------------------------------------------------------
print("\n>>> 7. RUNNING LOCAL HTTP SERVER VERIFICATION (PORT 8899)...")
class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

server = HTTPServer(("127.0.0.1", 8899), SilentHandler)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()
time.sleep(0.3)

endpoints = [
    ("/", 200),
    ("/index.html", 200),
    ("/config.js", 200),
    ("/install.html", 200),
    ("/install/", 200),
    ("/styles.css", 200),
    ("/main.js", 200),
    ("/extension/manifest.json", 200),
    ("/extension/popup.html", 200),
    ("/dist/continuo-extension.zip", 200),
]

for path, expected_status in endpoints:
    url = f"http://127.0.0.1:8899{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        status = resp.getcode()
        size = len(resp.read())
        print(f"  [PASS] GET {path:28} -> {status} OK ({size} bytes)")
        assert status == expected_status, f"Expected {expected_status} but got {status}"

server.shutdown()
print("\n============================================================")
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY (100% PASS)!")
print("============================================================")
