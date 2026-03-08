/**
 * FarmBuddy AI — script.js
 * Updated: text/voice disease detection with full multilingual support
 */

// API_BASE_URL comes from translations.js (global)

// ─── Supported languages ──────────────────────────────────────────────────────
const INDIAN_LANGUAGES = {
  'en': 'English',
  'hi': 'हिन्दी',
  'bn': 'বাংলা',
  'te': 'తెలుగు',
  'ta': 'தமிழ்',
  'mr': 'मराठी',
  'gu': 'ગુજરાતી',
  'kn': 'ಕನ್ನಡ',
  'ml': 'മലയാളം',
  'pa': 'ਪੰਜਾਬੀ',
  'or': 'ଓଡ଼ିଆ',
  'as': 'অসমীয়া',
  'ur': 'اردو',
  'ne': 'नेपाली',
  'ks': 'कॉशुर',
};

// ─── Voice language map ───────────────────────────────────────────────────────
const VOICE_LANG_MAP = {
  hi:'hi-IN', ta:'ta-IN', te:'te-IN', bn:'bn-IN', mr:'mr-IN',
  gu:'gu-IN', kn:'kn-IN', ml:'ml-IN', pa:'pa-IN', ur:'ur-PK',
  or:'or-IN', as:'as-IN', ne:'ne-NP', ks:'ur-PK', en:'en-US'
};

// ─── RTL languages ────────────────────────────────────────────────────────────
const RTL_LANGUAGES = ['ur', 'ks'];

// ─── State ────────────────────────────────────────────────────────────────────
let currentLang = localStorage.getItem('farmbuddy_lang') || 'en';
let isTranslatingUI = false;

// ─── DOM References ───────────────────────────────────────────────────────────
let themeToggle, voiceBtn, queryInput, imageUpload, videoUpload;
let imagePreview, languageSelect, messagesContainer, loading;
let sendBtn, sidebar, menuBtn, closeSidebarBtn;
let newChatBtn, mobileNewChat, searchInput, historyList;

// ─── Conversation State ───────────────────────────────────────────────────────
let conversations = loadConversations();
let currentConversationId = getOrCreateConversation();

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async function () {
  initializeElements();
  initializeTheme();
  setupLanguageSelector();
  setupEventListeners();
  setupSidebar();
  loadCurrentConversation();
  renderHistory();
  addAnimationStyles();
  setPageDirection(currentLang);
  await loadInitialData();
  await forceApplyAllTranslations(currentLang);
});

function initializeElements() {
  themeToggle       = document.getElementById('themeToggle');
  voiceBtn          = document.getElementById('voiceBtn');
  sendBtn           = document.getElementById('sendBtn');
  queryInput        = document.getElementById('queryInput');
  imageUpload       = document.getElementById('imageUpload');
  videoUpload       = document.getElementById('videoUpload');
  imagePreview      = document.getElementById('imagePreview');
  languageSelect    = document.getElementById('languageSelect');
  messagesContainer = document.getElementById('messages');
  loading           = document.getElementById('loading');
  sidebar           = document.getElementById('sidebar');
  menuBtn           = document.getElementById('menuBtn');
  closeSidebarBtn   = document.getElementById('closeSidebar');
  newChatBtn        = document.getElementById('newChatBtn');
  mobileNewChat     = document.getElementById('mobileNewChat');
  searchInput       = document.getElementById('searchInput');
  historyList       = document.getElementById('historyList');
}

// ─── Force apply all translations ─────────────────────────────────────────────
async function forceApplyAllTranslations(lang) {
  if (lang !== 'en') await loadUITranslations(lang);
  await updateAllUIText(lang);
  updateElementsById(lang);
  document.title = `FarmBuddy AI - ${t('farmerAssistant', lang)}`;
}

async function updateAllUIText(lang) {
  const userPlan = document.querySelector('.user-plan');
  if (userPlan) userPlan.textContent = t('farmerAssistant', lang);

  const quickActionSpans   = document.querySelectorAll('.quick-action span');
  const quickActionButtons = document.querySelectorAll('.quick-action');
  const qaKeys = ['cropAdvisory', 'marketPrices', 'govtSchemes', 'diseaseDetection'];
  quickActionSpans.forEach((span, i) => {
    if (qaKeys[i]) span.textContent = t(qaKeys[i], lang);
  });
  quickActionButtons.forEach((btn, i) => {
    if (qaKeys[i]) btn.setAttribute('title', t(qaKeys[i], lang));
  });

  if (queryInput)  queryInput.placeholder  = t('inputPlaceholder', lang);
  if (searchInput) searchInput.placeholder = t('searchPlaceholder', lang);

  const disclaimer = document.querySelector('.disclaimer');
  if (disclaimer) disclaimer.textContent = t('disclaimer', lang);

  const loadingP = document.querySelector('.loading-overlay p');
  if (loadingP) loadingP.textContent = t('analyzing', lang);

  const weatherSpans = document.querySelectorAll('.weather-widget-top span');
  if (weatherSpans.length >= 3) weatherSpans[2].textContent = t('localWeather', lang);

  if (newChatBtn)   newChatBtn.title   = t('newChat', lang);
  if (mobileNewChat) mobileNewChat.title = t('newChat', lang);

  const emptyHistory = document.querySelector('.empty-history p');
  if (emptyHistory) emptyHistory.textContent = t('noConversations', lang);
}

function updateElementsById(lang) {
  ['newChatBtn','mobileNewChat','voiceBtn','attachBtn','videoAttachBtn','sendBtn']
    .forEach(id => {
      const el = document.getElementById(id);
      if (el && el.getAttribute('title')) {
        el.setAttribute('title',
          t(id.replace('Btn','').toLowerCase() + 'Title', lang) || el.getAttribute('title'));
      }
    });
}

// ─── Page direction ───────────────────────────────────────────────────────────
function setPageDirection(lang) {
  const dir = RTL_LANGUAGES.includes(lang) ? 'rtl' : 'ltr';
  document.documentElement.setAttribute('dir', dir);
  document.documentElement.setAttribute('lang', lang);
  if (lang === 'ur') {
    document.body.style.fontFamily = "'Noto Nastaliq Urdu','Inter',sans-serif";
  } else if (lang === 'ks') {
    document.body.style.fontFamily = "'Noto Sans Arabic','Inter',sans-serif";
  } else {
    document.body.style.fontFamily = "'Inter',sans-serif";
  }
}

// ─── Theme ────────────────────────────────────────────────────────────────────
function initializeTheme() {
  const saved = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
  if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
}

async function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateThemeIcon(next);
  showNotification(next === 'dark' ? t('darkMode', currentLang) : t('lightMode', currentLang), 'info');
}

function updateThemeIcon(theme) {
  if (!themeToggle) return;
  const icon = themeToggle.querySelector('i');
  if (icon) icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

// ─── Language selector ────────────────────────────────────────────────────────
function setupLanguageSelector() {
  if (!languageSelect) return;
  languageSelect.innerHTML = '';
  Object.entries(INDIAN_LANGUAGES).forEach(([code, name]) => {
    const opt = document.createElement('option');
    opt.value = code;
    opt.textContent = name;
    if (code === currentLang) opt.selected = true;
    languageSelect.appendChild(opt);
  });
  languageSelect.removeEventListener('change', handleLanguageChange);
  languageSelect.addEventListener('change', handleLanguageChange);
}

async function handleLanguageChange(e) {
  const lang = e.target.value;
  if (lang === currentLang) return;
  currentLang = lang;
  localStorage.setItem('farmbuddy_lang', lang);
  setPageDirection(lang);
  showNotification(t('translating', currentLang), 'info');
  await forceApplyAllTranslations(lang);
  const langName = INDIAN_LANGUAGES[lang] || 'English';
  showNotification(`${t('languageChanged', currentLang)} ${langName}`, 'success');
  await loadFAQs(lang);
  const conv = conversations.find(c => c.id === currentConversationId);
  if (conv && conv.messages.length === 0 && messagesContainer) {
    messagesContainer.innerHTML = '';
    await showWelcomeMessage(lang);
  }
}

async function maybeTranslate(text, lang) {
  const target = lang || currentLang;
  if (!target || target === 'en' || !text) return text;
  return await translateText(text, target);
}

// ─── FAQs ─────────────────────────────────────────────────────────────────────
async function loadFAQs(lang = 'en') {
  try {
    const res = await fetch(`${API_BASE_URL}/faqs?lang=${lang}`);
    const faqs = await res.json();
    if (!faqs.error) window.currentFAQs = faqs;
  } catch (_) {}
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function setupSidebar() {
  if (menuBtn)         menuBtn.addEventListener('click', toggleSidebar);
  if (closeSidebarBtn) closeSidebarBtn.addEventListener('click', toggleSidebar);
  if (newChatBtn)      newChatBtn.addEventListener('click', newChat);
  if (mobileNewChat)   mobileNewChat.addEventListener('click', newChat);
  if (searchInput)     searchInput.addEventListener('input', filterHistory);
  document.addEventListener('click', function (e) {
    if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) && menuBtn && !menuBtn.contains(e.target)) {
      toggleSidebar();
    }
  });
}

function toggleSidebar() {
  if (sidebar) sidebar.classList.toggle('open');
}

// ─── Event listeners ──────────────────────────────────────────────────────────
function setupEventListeners() {
  if (sendBtn) sendBtn.addEventListener('click', submitQuery);
  if (queryInput) {
    queryInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitQuery(); }
    });
    queryInput.addEventListener('input', autoResizeTextarea);
  }
  const attachBtn = document.getElementById('attachBtn');
  if (attachBtn) attachBtn.addEventListener('click', () => imageUpload && imageUpload.click());
  const videoAttachBtn = document.getElementById('videoAttachBtn');
  if (videoAttachBtn) videoAttachBtn.addEventListener('click', () => videoUpload && videoUpload.click());
  setupVoiceInput();
  setupImageUpload();
  setupVideoUpload();
}

function autoResizeTextarea() {
  if (!queryInput) return;
  queryInput.style.height = 'auto';
  queryInput.style.height = Math.min(queryInput.scrollHeight, 200) + 'px';
}

// ─── Voice input ──────────────────────────────────────────────────────────────
let _recognition = null;
let _isRecording = false;

function setupVoiceInput() {
  if (!voiceBtn) return;
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    voiceBtn.style.display = 'none';
    return;
  }
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  _recognition = new SpeechRecognition();
  _recognition.continuous      = false;
  _recognition.interimResults  = true;
  _recognition.lang            = VOICE_LANG_MAP[currentLang] || 'en-US';

  _recognition.onresult = (event) => {
    const transcript = Array.from(event.results).map(r => r[0].transcript).join('');
    if (queryInput) { queryInput.value = transcript; autoResizeTextarea(); }
  };

  _recognition.onend = async () => {
    _isRecording = false;
    voiceBtn.style.color = '';
    voiceBtn.querySelector('i').className = 'fas fa-microphone';
    if (queryInput && queryInput.value.trim()) {
      showNotification(t('voiceCaptured', currentLang), 'success');
      submitQuery();    // ← voice query goes through the same submitQuery → /api/chat flow
    }
  };

  _recognition.onerror = async () => {
    _isRecording = false;
    voiceBtn.style.color = '';
    voiceBtn.querySelector('i').className = 'fas fa-microphone';
    showNotification(t('voiceError', currentLang), 'error');
  };

  voiceBtn.addEventListener('click', function () {
    _recognition.lang = VOICE_LANG_MAP[currentLang] || 'en-US';
    if (_isRecording) {
      _recognition.stop();
    } else {
      _recognition.start();
      _isRecording = true;
      voiceBtn.style.color = 'var(--green-primary)';
      voiceBtn.querySelector('i').className = 'fas fa-stop';
      showNotification(t('voiceListening', currentLang) || 'Listening…', 'info');
    }
  });
}

// ─── Image upload ─────────────────────────────────────────────────────────────
function setupImageUpload() {
  if (!imageUpload || !imagePreview) return;
  imageUpload.addEventListener('change', async function (e) {
    imagePreview.innerHTML = '';
    if (e.target.files.length === 0) return;
    Array.from(e.target.files).forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = function (ev) {
        const item = document.createElement('div');
        item.className = 'preview-item';
        item.innerHTML = `
          <img src="${ev.target.result}" alt="Preview">
          <button class="remove-preview" onclick="removePreview(${index})">
            <i class="fas fa-times"></i>
          </button>`;
        imagePreview.appendChild(item);
      };
      reader.readAsDataURL(file);
    });
    showNotification(`${e.target.files.length} ${t('imageSelected', currentLang)}`, 'success');
    if (e.target.files.length >= 1) await analyzeDiseaseImage(e.target.files[0]);
  });
}

window.removePreview = function () {
  if (imagePreview) imagePreview.innerHTML = '';
  if (imageUpload)  imageUpload.value = '';
};

async function analyzeDiseaseImage(file) {
  showLoading();
  const formData = new FormData();
  formData.append('image', file);
  formData.append('lang', currentLang);
  try {
    const res  = await fetch(`${API_BASE_URL}/predict-disease`, { method:'POST', body:formData });
    const data = await res.json();
    if (data.error) {
      showNotification(await maybeTranslate(`Error: ${data.error}`, currentLang), 'error');
      hideLoading(); return;
    }
    await displayDiseaseResult(data, 'image');
  } catch (_) {
    showNotification(t('analysisFailed', currentLang), 'error');
  } finally {
    hideLoading();
  }
}

// ─── Disease result display — shared by image, video AND text/voice ───────────
/**
 * displayDiseaseResult(data, source)
 *   source: 'image' | 'video' | 'text'
 *
 * For text/voice the backend already returns a fully-formatted, translated
 * Markdown response string in data.response (via /api/chat).
 * For image/video results come from /api/predict-disease[-video] with raw fields.
 */
async function displayDiseaseResult(data, source = 'image') {

  // ── Text / voice: response already formatted + translated by backend ─────
  if (source === 'text') {
    const formattedResponse = formatMarkdown(data.response.replace(/\n/g, '<br>'));
    addMessageToUI(formattedResponse, 'ai', 'FarmBuddy AI');
    saveMessage(formattedResponse, 'ai');
    return;
  }

  // ── Image or video: build rich HTML card ──────────────────────────────────
  const disease    = (data.disease || 'Unknown').replace(/_/g, ' ');
  const confidence = ((data.confidence || 0) * 100).toFixed(2);
  const langName   = INDIAN_LANGUAGES[currentLang] || 'English';

  // Labels translated in parallel
  const [
    titleTr, diseaseLabelTr, confidenceLabelTr, treatmentLabelTr,
    diseaseTr, treatmentTr, noteTr
  ] = await Promise.all([
    maybeTranslate(
      source === 'video'
        ? t('videoAnalysisTitle', currentLang)
        : t('diseaseIdentified', currentLang),
      currentLang
    ),
    maybeTranslate(t('diseaseLabel',     currentLang), currentLang),
    maybeTranslate(t('confidenceLabel',  currentLang), currentLang),
    maybeTranslate(t('treatmentLabel',   currentLang), currentLang),
    maybeTranslate(disease,              currentLang),
    maybeTranslate(data.treatment || '', currentLang),
    maybeTranslate(`${t('translatedNote', currentLang)} ${langName}`, currentLang),
  ]);

  let extraHtml = '';
  if (source === 'video') {
    const frameCount = data.frame_count || 0;
    const summary    = data.video_summary || '';
    const framesLbl  = await maybeTranslate(t('framesAnalysed', currentLang), currentLang);
    extraHtml = summary
      ? `<p><i class="fas fa-film"></i> <strong>${framesLbl}:</strong> ${frameCount} frames — ${summary}</p>`
      : `<p><i class="fas fa-film"></i> <strong>${framesLbl}:</strong> ${frameCount}</p>`;
  }

  const text = `
    <strong>${titleTr}</strong>
    <div class="info-box">
      ${extraHtml}
      <p><i class="fas fa-leaf"></i> <strong>${diseaseLabelTr}:</strong> ${diseaseTr}</p>
      <p><i class="fas fa-chart-line"></i> <strong>${confidenceLabelTr}:</strong> ${confidence}%</p>
      <p><i class="fas fa-flask"></i> <strong>${treatmentLabelTr}:</strong> ${treatmentTr}</p>
    </div>
    ${currentLang !== 'en'
      ? `<span class="translation-note"><i class="fas fa-language"></i> ${noteTr}</span>`
      : ''}
  `;

  addMessageToUI(text, 'ai', 'FarmBuddy AI');
  saveMessage(text, 'ai');

  setTimeout(() => {
    if (imagePreview) imagePreview.innerHTML = '';
    if (imageUpload)  imageUpload.value = '';
  }, 3000);
}

// ─── Video upload ─────────────────────────────────────────────────────────────
function setupVideoUpload() {
  if (!videoUpload) return;
  videoUpload.addEventListener('change', async function (e) {
    if (e.target.files.length === 0) return;
    const file       = e.target.files[0];
    const fileName   = file.name;
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);

    if (imagePreview) {
      imagePreview.innerHTML = `
        <div class="preview-item video-preview-chip"
             style="width:auto;height:auto;padding:8px 14px;display:flex;
                    align-items:center;gap:8px;border-radius:12px;">
          <i class="fas fa-film" style="color:var(--green-primary);font-size:18px;"></i>
          <div style="display:flex;flex-direction:column;gap:2px;">
            <span style="font-size:13px;font-weight:600;color:var(--text-primary);
                         max-width:160px;overflow:hidden;text-overflow:ellipsis;
                         white-space:nowrap;">${fileName}</span>
            <span style="font-size:11px;color:var(--text-muted);">${fileSizeMB} MB</span>
          </div>
          <button class="remove-preview" onclick="removeVideoPreview()"
                  style="position:static;width:20px;height:20px;">
            <i class="fas fa-times"></i>
          </button>
        </div>`;
    }

    showNotification(`🎥 Video selected: ${fileName}`, 'success');
    addMessageToUI(
      `<span style="display:flex;align-items:center;gap:8px;">
         <i class="fas fa-film" style="color:var(--green-primary);"></i>
         <em>${t('videoUploaded', currentLang)}: ${fileName}</em>
       </span>`,
      'user', 'You'
    );
    await analyzeDiseaseVideo(file);
  });
}

window.removeVideoPreview = function () {
  if (imagePreview) imagePreview.innerHTML = '';
  if (videoUpload)  videoUpload.value = '';
};

async function analyzeDiseaseVideo(file) {
  showTypingIndicator();
  const loadingP = document.querySelector('.loading-overlay p');
  if (loadingP) loadingP.textContent = t('analyzingVideo', currentLang);
  showLoading();

  const formData = new FormData();
  formData.append('video', file);
  formData.append('lang', currentLang);

  try {
    const res  = await fetch(`${API_BASE_URL}/predict-disease-video`, { method:'POST', body:formData });
    const data = await res.json();
    hideTypingIndicator();
    hideLoading();
    const loadingPR = document.querySelector('.loading-overlay p');
    if (loadingPR) loadingPR.textContent = t('analyzing', currentLang);
    if (data.error) {
      showNotification(await maybeTranslate(`Error: ${data.error}`, currentLang), 'error');
      return;
    }
    await displayDiseaseResult(data, 'video');
  } catch (err) {
    hideTypingIndicator();
    hideLoading();
    showNotification(t('analysisFailed', currentLang) || 'Video analysis failed.', 'error');
  } finally {
    setTimeout(() => {
      if (imagePreview) imagePreview.innerHTML = '';
      if (videoUpload)  videoUpload.value = '';
    }, 4000);
  }
}

// ─── Submit query (text + voice) ──────────────────────────────────────────────
async function submitQuery() {
  if (!queryInput) return;
  const query = queryInput.value.trim();
  if (!query) { showNotification(t('enterQuestion', currentLang), 'warning'); return; }

  addMessageToUI(query, 'user', 'You');
  saveMessage(query, 'user');
  saveQueryToHistory(query);

  queryInput.value = '';
  autoResizeTextarea();
  showTypingIndicator();
  showLoading();

  try {
    const res  = await fetch(`${API_BASE_URL}/chat`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ query, lang: currentLang })
    });
    const data = await res.json();
    hideTypingIndicator();
    hideLoading();

    if (data.error) { showNotification(`Error: ${data.error}`, 'error'); return; }

    // ── Route disease responses to the shared disease display ─────────────
    if (data.intent === 'disease') {
      await displayDiseaseResult(data, 'text');
    } else {
      await displayChatResponse(data);
    }

  } catch (_) {
    hideTypingIndicator();
    hideLoading();
    showNotification(t('backendOffline', currentLang), 'warning');
    await generateAndDisplayFallback(query);
  }
}

// ─── Display chat response (non-disease) ──────────────────────────────────────
async function displayChatResponse(data) {
  let response = data.response || '';
  if (currentLang !== 'en' && data.response_language === 'en') {
    response = await translateText(response, currentLang);
  }

  const detectedLang = data.detected_language || 'en';
  const langName     = INDIAN_LANGUAGES[detectedLang] || 'English';

  let entityHTML = '';
  if (data.entities && Object.keys(data.entities).length > 0) {
    entityHTML = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">';
    for (const [key, value] of Object.entries(data.entities)) {
      if (value) {
        const vals = Array.isArray(value) ? value : [value];
        vals.forEach(val => {
          entityHTML += `<span style="background:var(--green-dim);color:var(--green-primary);
                                     padding:4px 12px;border-radius:20px;font-size:0.8rem;">
                           ${key}: ${val}
                         </span>`;
        });
      }
    }
    entityHTML += '</div>';
  }

  let detectedNote = '';
  if (detectedLang !== 'en') {
    const noteText = await maybeTranslate(
      `${t('translatedFrom', currentLang)} ${langName}`, currentLang
    );
    detectedNote = `<span class="translation-note">
                      <i class="fas fa-language"></i> ${noteText}
                    </span>`;
  }

  const formattedResponse = formatMarkdown(response.replace(/\n/g, '<br>'));
  const html = `${entityHTML}${formattedResponse}${detectedNote}`;
  addMessageToUI(html, 'ai', 'FarmBuddy AI');
  saveMessage(html, 'ai');
}

// ─── Fallback response (server offline) ──────────────────────────────────────
async function generateAndDisplayFallback(query) {
  const q = query.toLowerCase();
  let response = '';

  if (q.includes('tomato') || q.includes('टमाटर') || q.includes('தக்காளி')) {
    response = `<strong>🍅 Growing Tomatoes:</strong>
      <div class="info-box">
        <p><i class="fas fa-seedling"></i> <strong>Planting:</strong> Space plants 60–90 cm apart</p>
        <p><i class="fas fa-tint"></i> <strong>Watering:</strong> Keep soil moist, water at the base</p>
        <p><i class="fas fa-sun"></i> <strong>Sunlight:</strong> 6–8 hours daily</p>
        <p><i class="fas fa-exclamation-triangle"></i> <strong>Blight:</strong> Apply copper-based fungicide</p>
        <p><i class="fas fa-bug"></i> <strong>Pests:</strong> Use neem oil spray</p>
      </div>`;
  } else if (q.includes('wheat') || q.includes('गेहूं') || q.includes('ਕਣਕ')) {
    response = `<strong>🌾 Wheat Cultivation:</strong>
      <div class="info-box">
        <p><i class="fas fa-calendar"></i> <strong>Sowing:</strong> October–December (Rabi)</p>
        <p><i class="fas fa-seedling"></i> <strong>Seed Rate:</strong> 100–125 kg/hectare</p>
        <p><i class="fas fa-tint"></i> <strong>Irrigation:</strong> 4–5 times per season</p>
        <p><i class="fas fa-flask"></i> <strong>Fertilizer:</strong> 120 N, 60 P, 40 K kg/ha</p>
      </div>`;
  } else if (q.includes('price') || q.includes('भाव') || q.includes('rate') || q.includes('market')) {
    response = `<strong>📊 Market Prices (per quintal):</strong>
      <div class="info-box">
        <p><i class="fas fa-chart-line"></i> Wheat: ₹2,150–2,250</p>
        <p><i class="fas fa-chart-line"></i> Maize: ₹1,850–1,950</p>
        <p><i class="fas fa-chart-line"></i> Paddy: ₹1,940–2,040</p>
        <p><i class="fas fa-chart-line"></i> Onion: ₹800–1,200</p>
      </div>`;
  } else if (q.includes('disease') || q.includes('रोग') || q.includes('spot') ||
             q.includes('yellow') || q.includes('blight')) {
    response = `<strong>🔍 Disease Detection (Offline Mode):</strong>
      <div class="info-box">
        <p><i class="fas fa-info-circle"></i> Server is offline. For disease detection:</p>
        <p><i class="fas fa-camera"></i> Upload a plant photo when back online</p>
        <p><i class="fas fa-pencil-alt"></i> Or describe symptoms — e.g. "tomato yellow spots"</p>
      </div>`;
  } else {
    response = `<p>Thank you for your question about "<em>${query.substring(0, 60)}${query.length > 60 ? '…' : ''}</em>".</p>
      <div class="info-box">
        <p><i class="fas fa-info-circle"></i> I can help with crop advice, market prices, government schemes, and disease detection.</p>
        <p><i class="fas fa-camera"></i> Upload photos or videos for disease identification.</p>
      </div>`;
  }

  if (currentLang !== 'en') {
    const plainText = response.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    response = `<p>${await translateText(plainText, currentLang)}</p>`;
  }

  addMessageToUI(response, 'ai', 'FarmBuddy AI');
  saveMessage(response, 'ai');
}

// ─── Markdown formatter ───────────────────────────────────────────────────────
function formatMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g,     '<em>$1</em>')
    .replace(/`(.*?)`/g,       '<code>$1</code>')
    .replace(/(^|<br>)#{1,3}\s+(.*?)(?=<br>|$)/g,
             '$1<strong style="font-size:1.05em;">$2</strong>')
    .replace(/(^|<br>)[-•]\s+(.*?)(?=<br>|$)/g,
             '$1<span style="display:block;padding-left:14px;margin:2px 0;">• $2</span>')
    .replace(/(^|<br>)(\d+\.\s+)(.*?)(?=<br>|$)/g,
             '$1<span style="display:block;padding-left:14px;margin:2px 0;"><strong>$2</strong>$3</span>');
}

// ─── Message bubble ───────────────────────────────────────────────────────────
function addMessageToUI(text, sender, senderLabel) {
  if (!messagesContainer) return;
  const div    = document.createElement('div');
  div.className = `message ${sender}`;
  const time   = new Date().toLocaleTimeString('en-US', { hour:'numeric', minute:'2-digit' });
  const avatar = sender === 'user' ? 'fa-user' : 'fa-robot';
  const label  = senderLabel || (sender === 'user' ? 'You' : 'FarmBuddy AI');
  div.innerHTML = `
    <div class="message-avatar"><i class="fas ${avatar}"></i></div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-sender">${label}</span>
        <span class="message-time">${time}</span>
      </div>
      <div class="message-text">${formatMarkdown(text)}</div>
      <div class="message-actions">
        <button class="action-btn" onclick="copyMsg(this)" title="Copy">
          <i class="far fa-copy"></i>
        </button>
        <button class="action-btn" onclick="textToSpeech(this)" title="Listen">
          <i class="fas fa-volume-up"></i>
        </button>
        ${sender === 'ai' ? `
        <button class="action-btn" onclick="bookmarkResponse(this)" title="Bookmark">
          <i class="far fa-bookmark"></i>
        </button>
        <button class="action-btn" onclick="shareResponse(this)" title="Share">
          <i class="fas fa-share-alt"></i>
        </button>` : ''}
      </div>
    </div>`;
  messagesContainer.appendChild(div);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ─── Typing indicator ─────────────────────────────────────────────────────────
function showTypingIndicator() {
  if (!messagesContainer) return;
  const div = document.createElement('div');
  div.className = 'message ai';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="message-avatar"><i class="fas fa-robot"></i></div>
    <div class="message-content">
      <div class="typing-indicator"><span></span><span></span><span></span></div>
    </div>`;
  messagesContainer.appendChild(div);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
  const el = document.getElementById('typingIndicator');
  if (el) el.remove();
}

// ─── Quick action buttons ─────────────────────────────────────────────────────
window.setQuery = async function (type) {
  const lang = currentLang;
  const templates = {
    crop: () => `<strong>🌱 ${t('qaCropTitle', lang)}</strong><br><br>
${t('qaCropIntro', lang)}<br>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaCropEx1', lang)}</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaCropEx2', lang)}</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaCropEx3', lang)}</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaCropEx4', lang)}</span><br>
${t('qaTypeBelow', lang)}`,

    market: () => `<strong>📊 ${t('qaMarketTitle', lang)}</strong><br><br>
${t('qaMarketIntro', lang)}<br>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaMarketEx1', lang)}</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaMarketEx2', lang)}</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaMarketEx3', lang)}</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaMarketEx4', lang)}</span><br>
${t('qaTypeBelow', lang)}`,

    schemes: () => `<strong>📋 ${t('qaSchemesTitle', lang)}</strong><br><br>
${t('qaSchemesIntro', lang)}<br>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaSchemesEx1', lang)}</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaSchemesEx2', lang)}</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaSchemesEx3', lang)}</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• ${t('qaSchemesEx4', lang)}</span><br>
${t('qaTypeBelow', lang)}`,

    // Disease quick-action: now shows text input prompt + upload option
    disease: () => `<strong>🔍 ${t('qaDiseaseTitle', lang)}</strong><br><br>
${t('qaDiseaseTextPrompt', lang) ||
  'You can detect plant diseases in <strong>two ways</strong>:'}<br><br>
<span style="display:block;padding-left:14px;margin:2px 0;">
  📝 <strong>${t('qaDiseaseTextWay', lang) || 'Text/Voice'}</strong> — 
  ${t('qaDiseaseTextDesc', lang) || 'Describe symptoms, e.g. "tomato leaves have brown spots with yellow rings"'}
</span>
<span style="display:block;padding-left:14px;margin:2px 0;">
  📷 <strong>${t('qaDiseaseImageWay', lang) || 'Photo/Video'}</strong> — 
  ${t('qaDiseaseImageDesc', lang) || 'Upload a clear photo or video using the camera/video buttons below'}
</span><br>
<span class="translation-note">
  <i class="fas fa-info-circle"></i> 
  ${t('qaDiseaseNote', lang)}
</span>`,
  };

  if (!templates[type]) return;
  addMessageToUI(templates[type](), 'ai', 'FarmBuddy AI');
};

// ─── Text-to-speech ───────────────────────────────────────────────────────────
window.textToSpeech = async function (button) {
  const content = button.closest('.message-content');
  if (!content) return;
  const text = content.querySelector('.message-text').innerText;
  if (!('speechSynthesis' in window)) {
    showNotification(t('ttsNotSupported', currentLang), 'error'); return;
  }
  const isSpeaking = window.speechSynthesis.speaking;
  const icon = button.querySelector('i');
  if (isSpeaking && icon.classList.contains('fa-stop')) {
    window.speechSynthesis.cancel();
    icon.className = 'fas fa-volume-up';
    button.classList.remove('speaking');
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang   = VOICE_LANG_MAP[currentLang] || 'en-US';
  utterance.rate   = 1;
  utterance.onstart = () => { icon.className = 'fas fa-stop'; button.classList.add('speaking'); };
  utterance.onend   = () => { icon.className = 'fas fa-volume-up'; button.classList.remove('speaking'); };
  utterance.onerror = () => { icon.className = 'fas fa-volume-up'; button.classList.remove('speaking'); };
  window.speechSynthesis.speak(utterance);
};

// ─── Copy ─────────────────────────────────────────────────────────────────────
window.copyMsg = async function (button) {
  const text = button.closest('.message-content').querySelector('.message-text').innerText;
  try {
    await navigator.clipboard.writeText(text);
    showNotification(t('copied', currentLang), 'success');
  } catch (_) {
    showNotification(t('copyFailed', currentLang), 'error');
  }
};

// ─── Share ────────────────────────────────────────────────────────────────────
window.shareResponse = async function (button) {
  const text = button.closest('.message-content').querySelector('.message-text').innerText;
  if (navigator.share) {
    navigator.share({ title:'FarmBuddy', text, url:window.location.href })
      .catch(async () => { await navigator.clipboard.writeText(text); showNotification(t('copied', currentLang), 'success'); });
  } else {
    await navigator.clipboard.writeText(text);
    showNotification(t('copied', currentLang), 'success');
  }
};

// ─── Bookmark ─────────────────────────────────────────────────────────────────
window.bookmarkResponse = async function (button) {
  const icon    = button.querySelector('i');
  const content = button.closest('.message-content');
  if (!icon || !content) return;
  icon.classList.toggle('far');
  icon.classList.toggle('fas');
  if (icon.classList.contains('fas')) {
    let bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
    bookmarks.push({ id:Date.now(), title:'FarmBuddy AI',
                     content:content.querySelector('.message-text').innerHTML,
                     timestamp:new Date().toISOString() });
    if (bookmarks.length > 20) bookmarks = bookmarks.slice(-20);
    localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
    showNotification(t('bookmarkSaved', currentLang), 'success');
  } else {
    showNotification(t('bookmarkRemoved', currentLang), 'info');
  }
};

// ─── Loading ──────────────────────────────────────────────────────────────────
function showLoading() { if (loading) loading.style.display = 'flex'; }
function hideLoading()  { if (loading) loading.style.display = 'none'; }

// ─── Notifications ────────────────────────────────────────────────────────────
function showNotification(message, type = 'info') {
  const existing = document.querySelector('.notification');
  if (existing) existing.remove();
  const icons = { success:'fa-check-circle', error:'fa-exclamation-circle',
                  warning:'fa-exclamation-triangle', info:'fa-info-circle' };
  const n = document.createElement('div');
  n.className = `notification ${type}`;
  n.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i><span>${message}</span>`;
  document.body.appendChild(n);
  setTimeout(() => { n.style.animation = 'slideOut 0.3s ease'; setTimeout(() => n.remove(), 300); }, 3000);
}

// ─── History ──────────────────────────────────────────────────────────────────
function saveQueryToHistory(query) {
  if (!query.trim()) return;
  let history = JSON.parse(localStorage.getItem('queryHistory') || '[]');
  history.push({ query, timestamp:new Date().toISOString() });
  if (history.length > 20) history = history.slice(-20);
  localStorage.setItem('queryHistory', JSON.stringify(history));
}

// ─── Conversation management ──────────────────────────────────────────────────
function loadConversations() {
  const saved = localStorage.getItem('farmbuddy_conversations');
  return saved ? JSON.parse(saved) : [];
}

function saveConversations() {
  localStorage.setItem('farmbuddy_conversations', JSON.stringify(conversations));
}

function getOrCreateConversation() {
  if (conversations.length === 0) {
    const c = { id:Date.now().toString(), title:'New Chat', messages:[], timestamp:new Date().toISOString() };
    conversations.push(c);
    saveConversations();
    return c.id;
  }
  return conversations[0].id;
}

function saveMessage(text, sender) {
  const conv = conversations.find(c => c.id === currentConversationId);
  if (!conv) return;
  conv.messages.push({ text, sender, timestamp:new Date().toISOString() });
  if (sender === 'user' && conv.messages.filter(m => m.sender === 'user').length === 1) {
    const plain = text.replace(/<[^>]*>/g, '');
    conv.title = plain.substring(0, 35) + (plain.length > 35 ? '…' : '');
  }
  conv.timestamp = new Date().toISOString();
  saveConversations();
  renderHistory();
}

function loadCurrentConversation() {
  const conv = conversations.find(c => c.id === currentConversationId);
  if (!conv || conv.messages.length === 0) return;
  if (messagesContainer) messagesContainer.innerHTML = '';
  conv.messages.forEach(m => addMessageToUI(m.text, m.sender));
}

async function newChat() {
  const c = { id:Date.now().toString(), title:t('newChat', currentLang),
              messages:[], timestamp:new Date().toISOString() };
  conversations.unshift(c);
  currentConversationId = c.id;
  saveConversations();
  if (messagesContainer) messagesContainer.innerHTML = '';
  await loadInitialData();
  renderHistory();
  if (window.innerWidth <= 768) toggleSidebar();
}

async function loadConversationById(id) {
  currentConversationId = id;
  if (messagesContainer) messagesContainer.innerHTML = '';
  loadCurrentConversation();
  renderHistory();
  if (window.innerWidth <= 768) toggleSidebar();
}
window.loadConversation = loadConversationById;

async function deleteConversation(id, event) {
  event.stopPropagation();
  if (!confirm(t('deleteConfirm', currentLang))) return;
  conversations = conversations.filter(c => c.id !== id);
  if (conversations.length === 0) {
    await newChat();
  } else {
    if (currentConversationId === id) {
      currentConversationId = conversations[0].id;
      if (messagesContainer) messagesContainer.innerHTML = '';
      loadCurrentConversation();
    }
  }
  saveConversations();
  renderHistory();
}
window.deleteConversation = deleteConversation;

function renderHistory() {
  if (!historyList) return;
  if (conversations.length === 0) {
    historyList.innerHTML = `<div class="empty-history"><i class="fas fa-comment"></i>
      <p>${t('noConversations', currentLang)}</p></div>`;
    return;
  }
  historyList.innerHTML = conversations.map(c => `
    <div class="history-item ${c.id === currentConversationId ? 'active' : ''}"
         data-id="${c.id}" onclick="loadConversation('${c.id}')">
      <i class="fas fa-comment"></i>
      <span>${c.title}</span>
      <button class="delete-btn" onclick="deleteConversation('${c.id}', event)">
        <i class="fas fa-times"></i>
      </button>
    </div>`).join('');
}

function filterHistory() {
  const term = searchInput ? searchInput.value.toLowerCase() : '';
  document.querySelectorAll('.history-item').forEach(item => {
    const text = item.querySelector('span').textContent.toLowerCase();
    item.style.display = text.includes(term) ? 'flex' : 'none';
  });
}

// ─── Welcome message ──────────────────────────────────────────────────────────
async function loadInitialData() {
  await loadFAQs(currentLang);
  const conv = conversations.find(c => c.id === currentConversationId);
  if (conv && conv.messages.length > 0) return;
  await showWelcomeMessage(currentLang);
}

async function showWelcomeMessage(lang) {
  const welcomeHTML = `
    <p>🌾 <strong>${t('welcomeTitle', lang)}</strong></p>
    <p>${t('welcomeSubtitle', lang)}</p>
    <div class="info-box">
      <p><i class="fas fa-seedling"></i>   ${t('welcomeItem1', lang)}</p>
      <p><i class="fas fa-chart-line"></i> ${t('welcomeItem2', lang)}</p>
      <p><i class="fas fa-file-alt"></i>   ${t('welcomeItem3', lang)}</p>
      <p><i class="fas fa-search"></i>     ${t('welcomeItem4', lang)}</p>
      <p><i class="fas fa-language"></i>   ${t('welcomeItem5', lang)}</p>
    </div>
    <p>${t('welcomeQuestion', lang)}</p>`;
  addMessageToUI(welcomeHTML, 'ai', 'FarmBuddy AI');
}

// ─── Animation styles ─────────────────────────────────────────────────────────
function addAnimationStyles() {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn  { from{transform:translateX(100%);opacity:0} to{transform:translateX(0);opacity:1} }
    @keyframes slideOut { from{transform:translateX(0);opacity:1} to{transform:translateX(100%);opacity:0} }
  `;
  document.head.appendChild(style);
}