const API_BASE_URL = 'http://127.0.0.1:5000/api';

const _translationCache = {};

const UI_STRINGS = {
  farmerAssistant:      'Farmer Assistant',
  newChat:              'New chat',
  searchPlaceholder:    'Search conversations...',
  noConversations:      'No conversations yet',
  deleteConfirm:        'Delete this conversation?',
  localWeather:         'Local Weather',

  cropAdvisory:         'Crop Advisory',
  marketPrices:         'Market Prices',
  govtSchemes:          'Govt Schemes',
  diseaseDetection:     'Disease Detection',

  inputPlaceholder:     'Ask your farming question or describe plant symptoms in any language...',
  disclaimer:           'FarmBuddy AI can make mistakes. Verify important information with experts.',

  analyzing:            'Analyzing your query...',
  analyzingVideo:       'Analyzing video frames...',

  darkMode:             'Dark mode enabled',
  lightMode:            'Light mode enabled',

  languageChanged:      'Language changed to',
  translating:          'Translating...',

  copied:               'Copied to clipboard!',
  copyFailed:           'Could not copy text',
  bookmarkSaved:        'Bookmarked!',
  bookmarkRemoved:      'Bookmark removed',
  voiceCaptured:        'Voice captured!',
  voiceListening:       'Listening… speak now',
  voiceError:           'Voice input error. Try again.',
  ttsNotSupported:      'Text-to-speech not supported in this browser',
  enterQuestion:        'Please enter a question or describe symptoms',
  backendOffline:       'Server offline. Showing cached response.',
  analysisFailed:       'Analysis failed. Please try again.',
  imageSelected:        'image(s) selected',
  videoSelected:        'Video selected',

  diseaseIdentified:    '🔍 Disease Analysis Result',
  diseaseLabel:         'Disease',
  confidenceLabel:      'Confidence',
  treatmentLabel:       'Treatment',
  translatedNote:       'Translated to',
  translatedFrom:       'Detected language:',
  videoAnalysisTitle:   '🎥 Video Disease Analysis',
  framesAnalysed:       'Frames analysed',
  videoUploaded:        'Uploaded video for disease analysis',

  textDiseaseTitle:     '🔍 Disease Identified from Description',
  textDiseaseNoMatch:   'Could not identify disease from description. Please add more symptom details or upload a photo.',
  textDiseasePrompt:    'Describe plant symptoms to identify disease — or upload a photo/video below',

  welcomeTitle:         'Welcome to FarmBuddy AI!',
  welcomeSubtitle:      'Your intelligent farming assistant. How can I help you today?',
  welcomeItem1:         'Crop prices — ask for any crop price by state',
  welcomeItem2:         'Market trends — get price trends and analysis',
  welcomeItem3:         'Government schemes — explore farmer welfare schemes',
  welcomeItem4:         'Disease detection — describe symptoms or upload a plant photo/video',
  welcomeItem5:         'Multi-language support — ask in any Indian language',
  welcomeQuestion:      'What would you like to know today?',

  qaCropTitle:          'Crop Advisory',
  qaCropIntro:          'I can help with growing advice for all crops. Try asking:',
  qaCropEx1:            'How to grow tomatoes?',
  qaCropEx2:            'Wheat fertilizer recommendation',
  qaCropEx3:            'Best season for rice cultivation',
  qaCropEx4:            'Onion farming tips',
  qaTypeBelow:          'Type your question below ⬇️',

  qaMarketTitle:        'Market Prices',
  qaMarketIntro:        'I can fetch live market prices. Try asking:',
  qaMarketEx1:          'Onion price in Maharashtra',
  qaMarketEx2:          'Wheat rate in Punjab',
  qaMarketEx3:          'Tomato price in Karnataka',
  qaMarketEx4:          'Rice price in West Bengal',

  qaSchemesTitle:       'Government Schemes',
  qaSchemesIntro:       'Available farmer welfare schemes:',
  qaSchemesEx1:         'PM-KISAN — ₹6,000/year direct income support',
  qaSchemesEx2:         'PM Fasal Bima — Crop insurance at low premiums',
  qaSchemesEx3:         'Kisan Credit Card — Easy credit up to ₹3 lakh at 4%',
  qaSchemesEx4:         'Soil Health Card — Free soil testing',

  qaDiseaseTitle:       'Disease Detection',
  qaDiseaseTextPrompt:  'You can detect plant diseases in two ways:',
  qaDiseaseTextWay:     '📝 Text / Voice',
  qaDiseaseTextDesc:    'Describe symptoms, e.g. "tomato leaves have brown spots with yellow rings"',
  qaDiseaseImageWay:    '📷 Photo / Video',
  qaDiseaseImageDesc:   'Upload a clear photo or video using the camera/video buttons below',
  qaDiseaseBody:        'Upload a clear photo or video of the affected plant, or describe the symptoms in text.',
  qaDiseaseNote:        'Tip: Mention the crop name + symptoms for best text-based results.',
};

async function loadUITranslations(lang) {
  if (lang === 'en') return UI_STRINGS;
  if (_translationCache[lang]) return _translationCache[lang];

  const keys   = Object.keys(UI_STRINGS);
  const values = Object.values(UI_STRINGS);

  try {
    const res = await fetch(`${API_BASE_URL}/translate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ texts: values, target_lang: lang })
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
    return UI_STRINGS;
  }
}

async function translateViaAPI(text, targetLang) {
  if (!text || targetLang === 'en') return text;
  try {
    const res = await fetch(`${API_BASE_URL}/translate`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ text, target_lang: targetLang })
    });
    const data = await res.json();
    return data.translated_text || text;
  } catch (_) {
    return text;
  }
}

function t(key, lang) {
  if (!lang || lang === 'en') return UI_STRINGS[key] || key;
  const cache = _translationCache[lang];
  if (cache && cache[key]) return cache[key];
  return UI_STRINGS[key] || key;
}

async function translateText(text, lang) {
  if (!lang || lang === 'en' || !text) return text;
  return await translateViaAPI(text, lang);
}

async function warmTranslationCache(lang) {
  if (lang === 'en' || _translationCache[lang]) return;
  await loadUITranslations(lang);
}

window.t                    = t;
window.translateText        = translateText;
window.loadUITranslations   = loadUITranslations;
window.warmTranslationCache = warmTranslationCache;
window.translateViaAPI      = translateViaAPI;