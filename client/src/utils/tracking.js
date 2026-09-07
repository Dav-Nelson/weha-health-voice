// src/utils/tracking.js

const POSTHOG_API_KEY = process.env.REACT_APP_POSTHOG_KEY;
const POSTHOG_HOST = process.env.REACT_APP_POSTHOG_HOST || "https://eu.i.posthog.com";

export const startSilentTracking = async (selectedLanguage) => {
  if (!POSTHOG_API_KEY) {
    // Tracking disabled if the key isn't configured — fail silently.
    return;
  }

  let geoData = { city: "unknown", country: "unknown", country_code: "unknown" };

  try {
    const geoResponse = await fetch('https://ipapi.co/json/');
    if (geoResponse.ok) {
      const data = await geoResponse.json();
      geoData = {
        city: data.city || "unknown",
        country: data.country_name || "unknown",
        country_code: data.country || "unknown"
      };
    }
  } catch (error) {
    // Fail gracefully and completely silently
  }

  try {
    const timestamp = new Date().toISOString();
    const random6chars = Math.random().toString(36).substring(2, 8);
    const distinctId = `user_${Date.now()}_${random6chars}`;

    const languageSecondary = typeof navigator !== 'undefined' && navigator.language
      ? navigator.language
      : "unknown";

    const payload = {
      api_key: POSTHOG_API_KEY,
      event: "weha_health_session_start",
      properties: {
        distinct_id: distinctId,
        platform: "Weha Health",
        timestamp: timestamp,
        language_primary: selectedLanguage?.name || selectedLanguage || "unknown",
        language_secondary: languageSecondary,
        city: geoData.city,
        country: geoData.country,
        country_code: geoData.country_code
      }
    };

    fetch(`${POSTHOG_HOST}/capture/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      keepalive: true
    }).catch(() => {
      // Total silence if the tracking call itself gets blocked
    });

  } catch (error) {
    // Total silence for any execution errors
  }
};