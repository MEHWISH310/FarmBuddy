/**
 * FarmBuddy AI — translations.js
 * Pure dynamic translation engine.
 * All UI strings are translated via /api/translate at runtime.
 * English is always the default — no API calls on first load.
 * Translations are cached in memory per session.
 */

const API_BASE_URL = 'http://127.0.0.1:5000/api';

// ─── In-memory translation cache: { langCode: { key: translatedText } } ──────
const _translationCache = {};

// ─── All English UI strings (source of truth) ────────────────────────────────
const UI_STRINGS = {
  // Sidebar / header
  farmerAssistant:    'Farmer Assistant',
  newChat:            'New chat',
  searchPlaceholder:  'Search conversations...',
  noConversations:    'No conversations yet',
  deleteConfirm:      'Delete this conversation?',
  localWeather:       'Local Weather',

  // Quick actions
  cropAdvisory:       'Crop Advisory',
  marketPrices:       'Market Prices',
  govtSchemes:        'Govt Schemes',
  diseaseDetection:   'Disease Detection',

  // Input area
  inputPlaceholder:   'Ask your farming question in any language...',
  disclaimer:         'FarmBuddy AI can make mistakes. Verify important information with experts.',

  // Loading
  analyzing:          'Analyzing your query...',

  // Theme
  darkMode:           'Dark mode enabled',
  lightMode:          'Light mode enabled',

  // Language switch
  languageChanged:    'Language changed to',

  // Notifications
  copied:             'Copied to clipboard!',
  copyFailed:         'Could not copy text',
  bookmarkSaved:      'Bookmarked!',
  bookmarkRemoved:    'Bookmark removed',
  voiceCaptured:      'Voice captured!',
  voiceError:         'Voice input error. Try again.',
  ttsNotSupported:    'Text-to-speech not supported in this browser',
  enterQuestion:      'Please enter a question',
  backendOffline:     'Server offline. Showing cached response.',
  analysisFailed:     'Analysis failed. Please try again.',
  imageSelected:      'image(s) selected',
  videoSelected:      'Video selected',
  videoComingSoon:    'Video analysis coming soon!',
  translating:        'Translating...',

  // Disease result
  diseaseIdentified:  '🔍 Disease Analysis Result',
  diseaseLabel:       'Disease',
  confidenceLabel:    'Confidence',
  treatmentLabel:     'Treatment',
  translatedNote:     'Translated to',
  translatedFrom:     'Detected language:',

  // Welcome message
  welcomeTitle:       'Welcome to FarmBuddy AI!',
  welcomeSubtitle:    'Your intelligent farming assistant. How can I help you today?',
  welcomeItem1:       'Crop prices — ask for any crop price by state',
  welcomeItem2:       'Market trends — get price trends and analysis',
  welcomeItem3:       'Government schemes — explore farmer welfare schemes',
  welcomeItem4:       'Disease detection — upload a plant photo for diagnosis',
  welcomeItem5:       'Multi-language support — ask in any Indian language',
  welcomeQuestion:    'What would you like to know today?',

  // Quick action responses
  qaCropTitle:        'Crop Advisory',
  qaCropIntro:        'I can help with growing advice for all crops. Try asking:',
  qaCropEx1:          'How to grow tomatoes?',
  qaCropEx2:          'Wheat fertilizer recommendation',
  qaCropEx3:          'Best season for rice cultivation',
  qaCropEx4:          'Onion farming tips',
  qaTypeBelow:        'Type your crop question below ⬇️',

  qaMarketTitle:      'Market Prices',
  qaMarketIntro:      'I can fetch live market prices. Try asking:',
  qaMarketEx1:        'Onion price in Maharashtra',
  qaMarketEx2:        'Wheat rate in Punjab',
  qaMarketEx3:        'Tomato price in Karnataka',
  qaMarketEx4:        'Rice price in West Bengal',

  qaSchemesTitle:     'Government Schemes',
  qaSchemesIntro:     'Available farmer welfare schemes:',
  qaSchemesEx1:       'PM-KISAN — ₹6,000/year direct income support',
  qaSchemesEx2:       'PM Fasal Bima — Crop insurance at low premiums',
  qaSchemesEx3:       'Kisan Credit Card — Easy credit up to ₹3 lakh at 4%',
  qaSchemesEx4:       'Soil Health Card — Free soil testing',

  qaDiseaseTitle:     'Disease Detection',
  qaDiseaseBody: 'Upload a clear photo or video of the affected plant using the 📷 camera or 🎥 video button. I will identify the disease and suggest treatment.',
  qaDiseaseNote: 'Tip: Use a well-lit, close-up photo or short video for best results.',

  // ADD THESE:
  analyzingVideo:     'Analyzing video frames...',
  videoAnalysisTitle: 'Video Disease Analysis Complete',
  framesAnalysed:     'Frames analysed',
  videoUploaded:      'Uploaded video for disease analysis',
  };

// ─── Batch translate all UI strings for a language ───────────────────────────
/**
 * Fetches translations for all UI_STRINGS keys for the given language.
 * Results are cached so switching back is instant.
 * @param {string} lang  — language code e.g. 'hi', 'ta'
 * @returns {Promise<Object>} — { key: translatedText, ... }
 */
async function loadUITranslations(lang) {
  if (lang === 'en') return UI_STRINGS;
  if (_translationCache[lang]) return _translationCache[lang];

  const keys   = Object.keys(UI_STRINGS);
  const values = Object.values(UI_STRINGS);

  try {
    const res = await fetch(`${API_BASE_URL}/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texts: values, target_lang: lang })
    });
    const data = await res.json();
    const translatedValues = data.translated_texts || values;

    const translated = {};
    keys.forEach((key, idx) => {
      translated[key] = translatedValues[idx] || values[idx];
    });
    _translationCache[lang] = translated;
    return translated;
  } catch (_) {
    // fallback: return English
    return UI_STRINGS;
  }
}

// ─── Translate a single string via /api/translate ────────────────────────────
async function translateViaAPI(text, targetLang) {
  if (!text || targetLang === 'en') return text;
  try {
    const res = await fetch(`${API_BASE_URL}/translate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, target_lang: targetLang })
    });
    const data = await res.json();
    return data.translated_text || text;
  } catch (_) {
    return text;
  }
}

// ─── Get a single UI string (sync, from cache or English fallback) ────────────
/**
 * t(key, lang) — returns translated string from cache.
 * If cache not loaded yet, returns English fallback.
 * Always call loadUITranslations(lang) before calling t() for non-English.
 */
function t(key, lang) {
  if (!lang || lang === 'en') return UI_STRINGS[key] || key;
  const cache = _translationCache[lang];
  if (cache && cache[key]) return cache[key];
  return UI_STRINGS[key] || key; // fallback to English
}

// ─── Translate any arbitrary text dynamically ────────────────────────────────
/**
 * translateText(text, lang) — translates any string to the target language.
 * Use for AI responses, notifications, dynamic content.
 */
async function translateText(text, lang) {
  if (!lang || lang === 'en' || !text) return text;
  return await translateViaAPI(text, lang);
}

// ─── Pre-warm cache for a language (call on dropdown change) ─────────────────
async function warmTranslationCache(lang) {
  if (lang === 'en' || _translationCache[lang]) return;
  await loadUITranslations(lang);
}

// ─── Expose globally ──────────────────────────────────────────────────────────
window.t                    = t;
window.translateText        = translateText;
window.loadUITranslations   = loadUITranslations;
window.warmTranslationCache = warmTranslationCache;
window.translateViaAPI      = translateViaAPI;