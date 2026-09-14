/**
 * CONTINUO GLOBAL EXTENSION DISTRIBUTION CONFIGURATION
 * 
 * Single source of truth for Chrome Extension distribution across the platform.
 * 
 * - STATE A: DEVELOPMENT BUILD (Unpublished)
 *   Keep CHROME_EXTENSION_STORE_URL as null.
 *   - Landing page CTA displays "Install Extension" and navigates to install.html.
 *   - install.html presents the "Development Installation" guide with the direct
 *     continuo-extension.zip download and 6 manual unpacked installation steps.
 * 
 * - STATE B: PRODUCTION RELEASE (Published on Chrome Web Store)
 *   Set CHROME_EXTENSION_STORE_URL to the official Chrome Web Store listing URL:
 *   e.g. const CHROME_EXTENSION_STORE_URL = "https://chromewebstore.google.com/detail/continuo/abcdefghijklmnop";
 *   - Landing page CTA automatically displays "Add to Chrome" and opens the official store listing.
 *   - install.html switches to official production installation mode (direct "Add to Chrome" CTA,
 *     zero ZIP / Developer Mode instructions in the primary flow).
 */
const CHROME_EXTENSION_STORE_URL = null;

/**
 * BACKEND API GATEWAY CONFIGURATION
 * Set this to your production backend API gateway URL:
 * e.g. const CONTINUO_API_URL = "https://api.continuo.ai/api/v1";
 * When null, the application dynamically resolves the API:
 * - Localhost dev: uses http://127.0.0.1:8008/api/v1
 * - Live production: uses https://api.continuo.ai/api/v1 (or origin /api/v1)
 */
const CONTINUO_API_URL = null;

// Expose globally for browser environments
if (typeof window !== "undefined") {
  window.CHROME_EXTENSION_STORE_URL = CHROME_EXTENSION_STORE_URL;
  window.CONTINUO_API_URL = CONTINUO_API_URL;
}

// Expose for Node.js / module test environments
if (typeof module !== "undefined" && module.exports) {
  module.exports = { CHROME_EXTENSION_STORE_URL, CONTINUO_API_URL };
}
