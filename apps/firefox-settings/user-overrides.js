// arkenfox user-overrides.js

// Re-enable DRM/EME (needed for Netflix, Spotify, Disney+, etc.)
user_pref("media.eme.enabled", true);

// Disable daily telemetry ping (separated from other telemetry in FF136+)
user_pref("datareporting.usage.uploadEnabled", false);

// Disable Pocket recommended stories on new tab page
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);

// Disable AccuWeather widget on new tab page
user_pref("browser.newtabpage.activity-stream.showWeather", false);

// Keep browsing history after closing Firefox
user_pref("privacy.clearOnShutdown_v2.browsingHistoryAndDownloads", false);

// Show default new tab page instead of blank
user_pref("browser.newtabpage.enabled", true);

// Enable disk cache for better performance
user_pref("browser.cache.disk.enable", true);
