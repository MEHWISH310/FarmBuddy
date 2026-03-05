/**
 * FarmBuddy AI - Merged Script
 * Frontend: New ChatGPT-style layout
 * Functionality: Original script.js logic (API calls, voice, disease detection, TTS, bookmarks, history)
 */

const API_BASE_URL = 'http://127.0.0.1:5000/api';

const INDIAN_LANGUAGES = {
    'as': 'অসমীয়া', 'bn': 'বাংলা', 'brx': 'बर', 'doi': 'डोगरी',
    'en': 'English', 'gu': 'ગુજરાતી', 'hi': 'हिन्दी', 'kn': 'ಕನ್ನಡ',
    'ks': 'कॉशुर', 'kok': 'कोंकणी', 'mai': 'मैथिली', 'ml': 'മലയാളം',
    'mni': 'মৈতৈলোন্', 'mr': 'मराठी', 'ne': 'नेपाली', 'or': 'ଓଡ଼ିଆ',
    'pa': 'ਪੰਜਾਬੀ', 'sa': 'संस्कृतम्', 'sat': 'ᱥᱟᱱᱛᱟᱲᱤ', 'sd': 'सिन्धी',
    'ta': 'தமிழ்', 'te': 'తెలుగు', 'ur': 'اردو'
};

// ─── DOM References ──────────────────────────────────────────────────────────
let themeToggle, voiceBtn, fabButton;
let queryInput, imageUpload, videoUpload, imagePreview, languageSelect;
let messagesContainer, loading, sendBtn, sidebar, menuBtn, closeSidebar;
let newChatBtn, mobileNewChat, searchInput, historyList;

// ─── Conversation State ───────────────────────────────────────────────────────
let conversations = loadConversations();
let currentConversationId = getOrCreateConversation();

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    initializeElements();
    initializeTheme();
    setupLanguageSelector();
    setupEventListeners();
    loadInitialData();
    addAnimationStyles();
    setupSidebar();
    loadCurrentConversation();
    renderHistory();
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
    closeSidebar      = document.getElementById('closeSidebar');
    newChatBtn        = document.getElementById('newChatBtn');
    mobileNewChat     = document.getElementById('mobileNewChat');
    searchInput       = document.getElementById('searchInput');
    historyList       = document.getElementById('historyList');
}

// ─── Theme ────────────────────────────────────────────────────────────────────
function initializeTheme() {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeIcon(next);
    showNotification(`${next === 'dark' ? 'Dark' : 'Light'} mode activated`, 'info');
}

function updateThemeIcon(theme) {
    if (!themeToggle) return;
    const icon = themeToggle.querySelector('i');
    if (icon) icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

// ─── Language Selector ────────────────────────────────────────────────────────
function setupLanguageSelector() {
    if (!languageSelect) return;
    languageSelect.innerHTML = '';
    Object.entries(INDIAN_LANGUAGES).forEach(([code, name]) => {
        const opt = document.createElement('option');
        opt.value = code;
        opt.textContent = name;
        if (code === 'en') opt.selected = true;
        languageSelect.appendChild(opt);
    });
    languageSelect.addEventListener('change', async function (e) {
        const lang = e.target.value;
        showNotification(`Language changed to ${INDIAN_LANGUAGES[lang] || 'English'}`, 'info');
        await loadFAQs(lang);
    });
}

async function loadFAQs(lang = 'en') {
    try {
        const res = await fetch(`${API_BASE_URL}/faqs?lang=${lang}`);
        const faqs = await res.json();
        if (!faqs.error) window.currentFAQs = faqs;
    } catch (_) { /* silent */ }
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function setupSidebar() {
    if (menuBtn)      menuBtn.addEventListener('click', toggleSidebar);
    if (closeSidebar) closeSidebar.addEventListener('click', toggleSidebar);
    if (newChatBtn)   newChatBtn.addEventListener('click', newChat);
    if (mobileNewChat) mobileNewChat.addEventListener('click', newChat);
    if (searchInput)  searchInput.addEventListener('input', filterHistory);

    document.addEventListener('click', function (e) {
        if (window.innerWidth <= 768 &&
            sidebar && sidebar.classList.contains('open') &&
            !sidebar.contains(e.target) &&
            menuBtn && !menuBtn.contains(e.target)) {
            toggleSidebar();
        }
    });
}

function toggleSidebar() {
    if (sidebar) sidebar.classList.toggle('open');
}

// ─── Event Listeners ──────────────────────────────────────────────────────────
function setupEventListeners() {
    // Send button
    if (sendBtn) sendBtn.addEventListener('click', submitQuery);

    // Enter key in textarea
    if (queryInput) {
        queryInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitQuery();
            }
        });
        // Auto-resize
        queryInput.addEventListener('input', autoResizeTextarea);
    }

    // Attach image button → triggers hidden input
    const attachBtn = document.getElementById('attachBtn');
    if (attachBtn) attachBtn.addEventListener('click', () => imageUpload && imageUpload.click());

    // Attach video button
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

// ─── Voice Input ──────────────────────────────────────────────────────────────
function setupVoiceInput() {
    if (!voiceBtn) return;

    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        voiceBtn.style.display = 'none';
        return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    let isRecording = false;

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results).map(r => r[0].transcript).join('');
        if (queryInput) {
            queryInput.value = transcript;
            autoResizeTextarea();
        }
    };

    recognition.onend = () => {
        isRecording = false;
        voiceBtn.style.color = '';
        voiceBtn.querySelector('i').className = 'fas fa-microphone';
        if (queryInput && queryInput.value.trim()) {
            showNotification('Voice captured!', 'success');
            submitQuery();
        }
    };

    recognition.onerror = () => {
        isRecording = false;
        voiceBtn.style.color = '';
        voiceBtn.querySelector('i').className = 'fas fa-microphone';
        showNotification('Could not recognize voice. Please try again.', 'error');
    };

    voiceBtn.addEventListener('click', function () {
        if (isRecording) {
            recognition.stop();
        } else {
            recognition.start();
            isRecording = true;
            voiceBtn.style.color = 'var(--green-primary)';
            voiceBtn.querySelector('i').className = 'fas fa-stop';
        }
    });
}

// ─── Image Upload ─────────────────────────────────────────────────────────────
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
                    </button>
                `;
                imagePreview.appendChild(item);
            };
            reader.readAsDataURL(file);
        });

        showNotification(`${e.target.files.length} image(s) selected`, 'success');

        if (e.target.files.length >= 1) {
            await analyzeDiseaseImage(e.target.files[0]);
        }
    });
}

window.removePreview = function (index) {
    if (imagePreview) imagePreview.innerHTML = '';
    if (imageUpload) imageUpload.value = '';
};

async function analyzeDiseaseImage(file) {
    showLoading();
    const formData = new FormData();
    formData.append('image', file);

    try {
        const res = await fetch(`${API_BASE_URL}/predict-disease`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();

        if (data.error) {
            showNotification(`Error: ${data.error}`, 'error');
            hideLoading();
            return;
        }

        displayDiseaseResult(data);
    } catch (_) {
        showNotification('Failed to analyze image', 'error');
    } finally {
        hideLoading();
    }
}

function displayDiseaseResult(data) {
    const disease = data.disease.replace(/_/g, ' ');
    const confidence = (data.confidence * 100).toFixed(2);
    const currentLang = languageSelect ? languageSelect.value : 'en';

    const text = `
        <strong>Disease Identified:</strong>
        <div class="info-box">
            <p><i class="fas fa-leaf"></i> <strong>Disease:</strong> ${disease}</p>
            <p><i class="fas fa-chart-line"></i> <strong>Confidence:</strong> ${confidence}%</p>
            <p><i class="fas fa-flask"></i> <strong>Treatment:</strong> ${data.treatment}</p>
        </div>
        ${currentLang !== 'en' ? `<span class="translation-note"><i class="fas fa-language"></i> Showing in ${INDIAN_LANGUAGES[currentLang]}</span>` : ''}
    `;

    addMessageToUI(text, 'ai', 'FarmBuddy AI');
    saveMessage(text, 'ai');

    // Clear previews after 3s
    setTimeout(() => {
        if (imagePreview) imagePreview.innerHTML = '';
        if (imageUpload) imageUpload.value = '';
    }, 3000);
}

// ─── Video Upload ─────────────────────────────────────────────────────────────
function setupVideoUpload() {
    if (!videoUpload) return;
    videoUpload.addEventListener('change', function (e) {
        if (e.target.files.length > 0) {
            showNotification(`Video selected: ${e.target.files[0].name}`, 'success');
            showNotification('Video processing coming soon!', 'info');
        }
    });
}

// ─── Submit Query (Chat) ──────────────────────────────────────────────────────
async function submitQuery() {
    if (!queryInput) return;
    const query = queryInput.value.trim();
    if (!query) {
        showNotification('Please enter a question', 'warning');
        return;
    }

    // Show user message immediately
    addMessageToUI(query, 'user', 'You');
    saveMessage(query, 'user');
    saveQueryToHistory(query);

    queryInput.value = '';
    autoResizeTextarea();

    // Typing indicator
    showTypingIndicator();
    showLoading();

    try {
        const res = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const data = await res.json();

        hideTypingIndicator();
        hideLoading();

        if (data.error) {
            showNotification(`Error: ${data.error}`, 'error');
            return;
        }

        displayChatResponse(data);

    } catch (_) {
        hideTypingIndicator();
        hideLoading();
        showNotification('Backend offline — showing local response', 'warning');
        const fallback = generateFallbackResponse(query);
        addMessageToUI(fallback, 'ai', 'FarmBuddy AI');
        saveMessage(fallback, 'ai');
    }
}

function generateFallbackResponse(query) {
    const q = query.toLowerCase();

    if (q.includes('tomato') || q.includes('टमाटर') || q.includes('தக்காளி')) {
        return `<strong>🍅 Growing Tomatoes:</strong>
        <div class="info-box">
            <p><i class="fas fa-seedling"></i> <strong>Planting:</strong> Space plants 60–90 cm apart in well-draining soil</p>
            <p><i class="fas fa-tint"></i> <strong>Watering:</strong> Keep soil moist, water at the base — avoid wetting leaves</p>
            <p><i class="fas fa-sun"></i> <strong>Sunlight:</strong> 6–8 hours of direct sunlight daily</p>
            <p><i class="fas fa-exclamation-triangle"></i> <strong>Blight:</strong> Remove affected leaves, apply copper-based fungicide every 7 days</p>
            <p><i class="fas fa-bug"></i> <strong>Pests:</strong> Handpick hornworms or use neem oil spray</p>
        </div>`;
    }
    else if (q.includes('wheat') || q.includes('गेहूं') || q.includes('கோதுமை')) {
        return `<strong>🌾 Wheat Cultivation:</strong>
        <div class="info-box">
            <p><i class="fas fa-calendar"></i> <strong>Sowing Time:</strong> October–December (Rabi season)</p>
            <p><i class="fas fa-seedling"></i> <strong>Seed Rate:</strong> 100–125 kg per hectare</p>
            <p><i class="fas fa-tint"></i> <strong>Irrigation:</strong> 4–5 times per season</p>
            <p><i class="fas fa-flask"></i> <strong>Fertilizer:</strong> 120 kg N, 60 kg P, 40 kg K per hectare</p>
            <p><i class="fas fa-bug"></i> <strong>Watch for:</strong> Rust, aphids, and termites</p>
        </div>`;
    }
    else if (q.includes('price') || q.includes('भाव') || q.includes('rate') || q.includes('मूल्य') || q.includes('market')) {
        return `<strong>📊 Current Market Prices (per quintal):</strong>
        <div class="info-box">
            <p><i class="fas fa-chart-line"></i> Wheat: ₹2,150–2,250</p>
            <p><i class="fas fa-chart-line"></i> Maize: ₹1,850–1,950</p>
            <p><i class="fas fa-chart-line"></i> Paddy: ₹1,940–2,040</p>
            <p><i class="fas fa-chart-line"></i> Gram: ₹5,200–5,400</p>
            <p><i class="fas fa-chart-line"></i> Groundnut: ₹5,500–5,700</p>
            <p><i class="fas fa-chart-line"></i> Onion: ₹800–1,200</p>
        </div>
        <span class="translation-note"><i class="fas fa-info-circle"></i> Prices vary by mandi and quality. Check local mandi for exact rates.</span>`;
    }
    else if (q.includes('scheme') || q.includes('subsid') || q.includes('सरकार') || q.includes('योजना')) {
        return `<strong>📋 Key Government Schemes for Farmers:</strong>
        <div class="info-box">
            <p><i class="fas fa-file-alt"></i> <strong>PM-KISAN:</strong> ₹6,000/year direct income support</p>
            <p><i class="fas fa-file-alt"></i> <strong>PM Fasal Bima:</strong> Crop insurance at low premiums</p>
            <p><i class="fas fa-file-alt"></i> <strong>Kisan Credit Card:</strong> Easy credit up to ₹3 lakh at 4% interest</p>
            <p><i class="fas fa-file-alt"></i> <strong>Soil Health Card:</strong> Free soil testing and recommendations</p>
            <p><i class="fas fa-file-alt"></i> <strong>eNAM:</strong> Online national agriculture market platform</p>
        </div>`;
    }
    else if (q.includes('disease') || q.includes('yellow') || q.includes('spot') || q.includes('blight')) {
        return `<strong>🔍 Plant Disease Advice:</strong>
        <div class="info-box">
            <p><i class="fas fa-check-circle"></i> Remove and destroy infected leaves immediately</p>
            <p><i class="fas fa-check-circle"></i> Apply copper-based fungicide every 7 days</p>
            <p><i class="fas fa-check-circle"></i> Water at the base — avoid wetting foliage</p>
            <p><i class="fas fa-check-circle"></i> Ensure good air circulation between plants</p>
            <p><i class="fas fa-camera"></i> Upload a photo for accurate AI disease detection!</p>
        </div>`;
    }
    else {
        return `<p>Thank you for your question about "<em>${query.substring(0, 60)}${query.length > 60 ? '…' : ''}</em>".</p>
        <div class="info-box">
            <p><i class="fas fa-info-circle"></i> I can help with crop advice, market prices, government schemes, and disease detection.</p>
            <p><i class="fas fa-camera"></i> Upload photos of affected plants for disease identification.</p>
            <p><i class="fas fa-language"></i> Ask in any of 22 Indian languages!</p>
        </div>
        <span class="translation-note"><i class="fas fa-wifi"></i> Note: Connect your backend at localhost:5000 for full AI responses.</span>`;
    }
}

function displayChatResponse(data) {
    const response     = data.response;
    const detectedLang = data.detected_language || 'en';
    const intent       = data.intent || 'general';
    const langName     = INDIAN_LANGUAGES[detectedLang] || 'English';

    // Entity tags
    let entityHTML = '';
    if (data.entities && Object.keys(data.entities).length > 0) {
        entityHTML = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">';
        Object.entries(data.entities).forEach(([key, value]) => {
            if (value) {
                const vals = Array.isArray(value) ? value : [value];
                vals.forEach(val => {
                    entityHTML += `<span style="background:var(--green-dim);color:var(--green-primary);padding:4px 12px;border-radius:20px;font-size:0.8rem;">${key}: ${val}</span>`;
                });
            }
        });
        entityHTML += '</div>';
    }

    const formattedResponse = formatMarkdown(response.replace(/\n/g, '<br>'));
    const html = `
        ${entityHTML}
        ${formattedResponse}
        ${detectedLang !== 'en' ? `<span class="translation-note"><i class="fas fa-language"></i> Translated from English to ${langName}</span>` : ''}
    `;

    addMessageToUI(html, 'ai', 'FarmBuddy AI');
    saveMessage(html, 'ai');
}

// ─── Markdown Formatter ───────────────────────────────────────────────────────
function formatMarkdown(text) {
    return text
        // **bold**
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // *italic*
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // `code`
        .replace(/`(.*?)`/g, '<code>$1</code>')
        // ### heading
        .replace(/(^|<br>)#{1,3}\s+(.*?)(?=<br>|$)/g, '$1<strong style="font-size:1.05em;">$2</strong>')
        // bullet: lines starting with - or •
        .replace(/(^|<br>)[-•]\s+(.*?)(?=<br>|$)/g, '$1<span style="display:block;padding-left:14px;margin:2px 0;">• $2</span>')
        // numbered list: 1. 2. etc
        .replace(/(^|<br>)(\d+\.\s+)(.*?)(?=<br>|$)/g, '$1<span style="display:block;padding-left:14px;margin:2px 0;"><strong>$2</strong>$3</span>');
}

// ─── Render a message bubble in the new chat UI ───────────────────────────────
function addMessageToUI(text, sender, senderLabel) {
    if (!messagesContainer) return;

    const div = document.createElement('div');
    div.className = `message ${sender}`;

    const time = new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    const avatar = sender === 'user' ? 'fa-user' : 'fa-robot';
    const label = senderLabel || (sender === 'user' ? 'You' : 'FarmBuddy AI');

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
        </div>
    `;

    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ─── Typing Indicator ─────────────────────────────────────────────────────────
function showTypingIndicator() {
    if (!messagesContainer) return;
    const div = document.createElement('div');
    div.className = 'message ai';
    div.id = 'typingIndicator';
    div.innerHTML = `
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

// ─── Quick Action Buttons ─────────────────────────────────────────────────────
window.setQuery = function (type) {
    const messages = {
        crop: `<strong>🌱 Crop Advisory</strong><br><br>
Ask me anything about growing crops! For example:<br>
<span style="display:block;padding-left:14px;margin:2px 0;">• How to grow tomatoes in the rainy season?</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• Best fertilizer for wheat?</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• When to sow rice in Maharashtra?</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• How to increase potato yield?</span><br>
Type your question below in any language!`,

        market: `<strong>📊 Market Prices</strong><br><br>
Ask me about current crop prices! For example:<br>
<span style="display:block;padding-left:14px;margin:2px 0;">• What is the price of onion in Maharashtra?</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• Current wheat rate in Punjab?</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• Tomato mandi price today?</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• Rice price in Andhra Pradesh?</span><br>
Type your question below in any language!`,

        schemes: `<strong>📋 Government Schemes</strong><br><br>
Ask me about farmer schemes and subsidies! For example:<br>
<span style="display:block;padding-left:14px;margin:2px 0;">• What schemes are available for small farmers?</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• How to apply for PM Kisan Yojana?</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• What is Fasal Bima Yojana?</span>
<span style="display:block;padding-left:14px;margin:2px 0;">• Subsidies for drip irrigation?</span><br>
Type your question below in any language!`,

        disease: `<strong>🔍 Disease Detection</strong><br><br>
Upload a photo of your plant using the <strong>📷 camera button</strong> in the input box below.<br><br>
I will analyze it and identify any diseases along with treatment recommendations.<br><br>
<span class="translation-note"><i class="fas fa-info-circle"></i> Supports: Tomato, Potato, Apple, Grape, Corn, Peach, Pepper, Strawberry, and more.</span>`
    };

    if (messages[type]) {
        addMessageToUI(messages[type], 'ai', 'FarmBuddy AI');
    }
};

// ─── Text-to-Speech ───────────────────────────────────────────────────────────
window.textToSpeech = function (button) {
    const content = button.closest('.message-content');
    if (!content) return;
    const text = content.querySelector('.message-text').innerText;

    if (!('speechSynthesis' in window)) {
        showNotification('Text-to-speech not supported', 'error');
        return;
    }

    const lang = languageSelect ? languageSelect.value : 'en';
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const langMap = { hi:'hi-IN', ta:'ta-IN', te:'te-IN', bn:'bn-IN', mr:'mr-IN',
                      gu:'gu-IN', kn:'kn-IN', ml:'ml-IN', pa:'pa-IN', ur:'ur-PK' };
    utterance.lang = langMap[lang] || 'en-US';
    utterance.rate = 1; utterance.pitch = 1; utterance.volume = 1;

    utterance.onstart = () => { button.querySelector('i').className = 'fas fa-stop'; };
    utterance.onend   = () => { button.querySelector('i').className = 'fas fa-volume-up'; };
    utterance.onerror = () => { button.querySelector('i').className = 'fas fa-volume-up'; };

    window.speechSynthesis.speak(utterance);
};

// ─── Copy ─────────────────────────────────────────────────────────────────────
window.copyMsg = async function (button) {
    const text = button.closest('.message-content').querySelector('.message-text').innerText;
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Copied to clipboard!', 'success');
    } catch (_) {
        showNotification('Failed to copy', 'error');
    }
};

// ─── Share ────────────────────────────────────────────────────────────────────
window.shareResponse = function (button) {
    const text = button.closest('.message-content').querySelector('.message-text').innerText;
    if (navigator.share) {
        navigator.share({ title: 'FarmBuddy Advice', text, url: window.location.href }).catch(() => copyToClipboard(text));
    } else {
        copyToClipboard(text);
    }
};

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(() => showNotification('Failed to copy', 'error'));
}

// ─── Bookmark ─────────────────────────────────────────────────────────────────
window.bookmarkResponse = function (button) {
    const icon = button.querySelector('i');
    const content = button.closest('.message-content');
    if (!icon || !content) return;

    icon.classList.toggle('far');
    icon.classList.toggle('fas');

    if (icon.classList.contains('fas')) {
        let bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
        bookmarks.push({
            id: Date.now(),
            title: 'FarmBuddy AI',
            content: content.querySelector('.message-text').innerHTML,
            timestamp: new Date().toISOString()
        });
        if (bookmarks.length > 20) bookmarks = bookmarks.slice(-20);
        localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
        showNotification('Saved to bookmarks', 'success');
    } else {
        showNotification('Removed from bookmarks', 'info');
    }
};

// ─── Loading ──────────────────────────────────────────────────────────────────
function showLoading() { if (loading) loading.style.display = 'flex'; }
function hideLoading()  { if (loading) loading.style.display = 'none'; }

// ─── Notifications ────────────────────────────────────────────────────────────
function showNotification(message, type = 'info') {
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const icons = { success: 'fa-check-circle', error: 'fa-exclamation-circle',
                    warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };

    const n = document.createElement('div');
    n.className = `notification ${type}`;
    n.innerHTML = `<i class="fas ${icons[type] || icons.info}"></i><span>${message}</span>`;
    document.body.appendChild(n);

    setTimeout(() => {
        n.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => n.remove(), 300);
    }, 3000);
}

// ─── History (localStorage) ───────────────────────────────────────────────────
function saveQueryToHistory(query) {
    if (!query.trim()) return;
    let history = JSON.parse(localStorage.getItem('queryHistory') || '[]');
    history.push({ query, timestamp: new Date().toISOString() });
    if (history.length > 20) history = history.slice(-20);
    localStorage.setItem('queryHistory', JSON.stringify(history));
}

// ─── Conversation Management ──────────────────────────────────────────────────
function loadConversations() {
    const saved = localStorage.getItem('farmbuddy_conversations');
    return saved ? JSON.parse(saved) : [];
}

function saveConversations() {
    localStorage.setItem('farmbuddy_conversations', JSON.stringify(conversations));
}

function getOrCreateConversation() {
    if (conversations.length === 0) {
        const c = { id: Date.now().toString(), title: 'New Conversation', messages: [], timestamp: new Date().toISOString() };
        conversations.push(c);
        saveConversations();
        return c.id;
    }
    return conversations[0].id;
}

function saveMessage(text, sender) {
    const conv = conversations.find(c => c.id === currentConversationId);
    if (!conv) return;

    conv.messages.push({ text, sender, timestamp: new Date().toISOString() });

    // Title from first user message
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

function newChat() {
    const c = { id: Date.now().toString(), title: 'New Conversation', messages: [], timestamp: new Date().toISOString() };
    conversations.unshift(c);
    currentConversationId = c.id;
    saveConversations();

    if (messagesContainer) messagesContainer.innerHTML = '';

    // Show welcome immediately
    loadInitialData();
    renderHistory();

    if (window.innerWidth <= 768) toggleSidebar();
}

function loadConversation(id) {
    currentConversationId = id;
    if (messagesContainer) messagesContainer.innerHTML = '';
    loadCurrentConversation();
    renderHistory();
    if (window.innerWidth <= 768) toggleSidebar();
}
window.loadConversation = loadConversation;

function deleteConversation(id, event) {
    event.stopPropagation();
    if (!confirm('Delete this conversation?')) return;

    conversations = conversations.filter(c => c.id !== id);

    if (conversations.length === 0) {
        newChat();
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
        historyList.innerHTML = `<div class="empty-history"><i class="fas fa-comment"></i><p>No conversations yet</p></div>`;
        return;
    }

    historyList.innerHTML = conversations.map(c => `
        <div class="history-item ${c.id === currentConversationId ? 'active' : ''}"
             data-id="${c.id}"
             onclick="loadConversation('${c.id}')">
            <i class="fas fa-comment"></i>
            <span>${c.title}</span>
            <button class="delete-btn" onclick="deleteConversation('${c.id}', event)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function filterHistory() {
    const term = searchInput ? searchInput.value.toLowerCase() : '';
    document.querySelectorAll('.history-item').forEach(item => {
        const text = item.querySelector('span').textContent.toLowerCase();
        item.style.display = text.includes(term) ? 'flex' : 'none';
    });
}

// ─── Welcome / Initial Load ───────────────────────────────────────────────────
async function loadInitialData() {
    await loadFAQs('en');

    const conv = conversations.find(c => c.id === currentConversationId);
    // Only show welcome if no messages yet
    if (conv && conv.messages.length > 0) return;

    const welcomeHTML = `
        <p>🌾 <strong>Welcome to FarmBuddy!</strong></p>
        <p>I can help you with:</p>
        <div class="info-box">
            <p><i class="fas fa-seedling"></i> Crop advisory and farming tips</p>
            <p><i class="fas fa-chart-line"></i> Market prices for all crops</p>
            <p><i class="fas fa-file-alt"></i> Government scheme information</p>
            <p><i class="fas fa-search"></i> Disease detection from photos</p>
            <p><i class="fas fa-language"></i> Support for 22 Indian languages</p>
        </div>
        <p>How can I help you today?</p>
    `;
    addMessageToUI(welcomeHTML, 'ai', 'FarmBuddy AI');
}

// ─── Animation Styles ─────────────────────────────────────────────────────────
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to   { transform: translateX(0);    opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0);    opacity: 1; }
            to   { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}