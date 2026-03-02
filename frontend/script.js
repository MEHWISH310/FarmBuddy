// ===== FARM BUDDY FRONTEND - BACKEND INTEGRATED =====
// API Base URL - change this to your backend URL
const API_BASE_URL = 'http://localhost:5000/api';

// ===== ALL 22 CONSTITUTIONAL LANGUAGES OF INDIA =====
const INDIAN_LANGUAGES = {
    'as': 'অসমীয়া',      // Assamese
    'bn': 'বাংলা',        // Bengali
    'brx': 'बर',          // Bodo
    'doi': 'डोगरी',       // Dogri
    'en': 'English',      // English
    'gu': 'ગુજરાતી',      // Gujarati
    'hi': 'हिन्दी',        // Hindi
    'kn': 'ಕನ್ನಡ',        // Kannada
    'ks': 'कॉशुर',        // Kashmiri
    'kok': 'कोंकणी',       // Konkani
    'mai': 'मैथिली',       // Maithili
    'ml': 'മലയാളം',       // Malayalam
    'mni': 'মৈতৈলোন্',     // Manipuri
    'mr': 'मराठी',        // Marathi
    'ne': 'नेपाली',       // Nepali
    'or': 'ଓଡ଼ିଆ',        // Odia
    'pa': 'ਪੰਜਾਬੀ',       // Punjabi
    'sa': 'संस्कृतम्',     // Sanskrit
    'sat': 'ᱥᱟᱱᱛᱟᱲᱤ',      // Santali
    'sd': 'सिन्धी',       // Sindhi
    'ta': 'தமிழ்',        // Tamil
    'te': 'తెలుగు',       // Telugu
    'ur': 'اردو'          // Urdu
};

// DOM Elements
let themeToggle, sunIcon, moonIcon, voiceBtn, fabButton;
let queryInput, imageUpload, videoUpload, imagePreview, languageSelect;
let navItems, responseArea, loading;

// Initialize on Load
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    initializeTheme();
    setupLanguageSelector();
    setupEventListeners();
    loadInitialData();
    
    // Add animation styles
    addAnimationStyles();
});

// Initialize DOM Elements
function initializeElements() {
    themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        sunIcon = themeToggle.querySelector('.fa-sun');
        moonIcon = themeToggle.querySelector('.fa-moon');
    }
    
    voiceBtn = document.getElementById('voiceBtn');
    fabButton = document.getElementById('fabButton');
    queryInput = document.getElementById('queryInput');
    imageUpload = document.getElementById('imageUpload');
    videoUpload = document.getElementById('videoUpload');
    imagePreview = document.getElementById('imagePreview');
    languageSelect = document.querySelector('.language-select');
    navItems = document.querySelectorAll('.nav-item');
    responseArea = document.getElementById('responseArea');
    loading = document.getElementById('loading');
}

// ===== LANGUAGE SELECTOR WITH 22 LANGUAGES =====
function setupLanguageSelector() {
    if (!languageSelect) return;
    
    // Clear existing options
    languageSelect.innerHTML = '';
    
    // Add all 22 languages
    Object.entries(INDIAN_LANGUAGES).forEach(([code, name]) => {
        const option = document.createElement('option');
        option.value = code;
        option.textContent = name;
        if (code === 'en') option.selected = true;
        languageSelect.appendChild(option);
    });
    
    // Add change event
    languageSelect.addEventListener('change', async function(e) {
        const lang = e.target.value;
        const langName = INDIAN_LANGUAGES[lang] || 'English';
        showNotification(`Language changed to ${langName}`, 'info');
        
        // Update UI text if needed
        await loadFAQs(lang);
    });
}

// Load FAQs in selected language
async function loadFAQs(lang = 'en') {
    try {
        const response = await fetch(`${API_BASE_URL}/faqs?lang=${lang}`);
        const faqs = await response.json();
        
        if (faqs.error) {
            console.error('Error loading FAQs:', faqs.error);
            return;
        }
        
        // Store FAQs for later use
        window.currentFAQs = faqs;
        
    } catch (error) {
        console.error('Failed to load FAQs:', error);
    }
}

// ===== THEME TOGGLE =====
function initializeTheme() {
    if (!themeToggle || !sunIcon || !moonIcon) return;
    
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcons(savedTheme);
    
    themeToggle.addEventListener('click', toggleTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcons(newTheme);
    
    showNotification(`${newTheme === 'dark' ? '🌙 Dark' : '☀️ Light'} mode activated`, 'info');
}

function updateThemeIcons(theme) {
    if (!sunIcon || !moonIcon) return;
    
    if (theme === 'dark') {
        sunIcon.style.display = 'none';
        moonIcon.style.display = 'inline-block';
    } else {
        sunIcon.style.display = 'inline-block';
        moonIcon.style.display = 'none';
    }
}

// ===== VOICE INPUT =====
function setupVoiceInput() {
    if (!voiceBtn) return;
    
    voiceBtn.addEventListener('click', async function() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            showNotification('Voice recognition not supported in this browser', 'error');
            return;
        }
        
        const originalHTML = this.innerHTML;
        this.innerHTML = '<i class="fas fa-stop"></i><span>Listening...</span>';
        this.style.animation = 'pulse 1s infinite';
        
        try {
            const transcript = await startVoiceRecognition();
            if (queryInput) {
                queryInput.value = transcript;
                showNotification('Voice captured!', 'success');
                await submitQuery();
            }
        } catch (error) {
            showNotification('Could not recognize voice. Please try again.', 'error');
        } finally {
            this.innerHTML = originalHTML;
            this.style.animation = '';
        }
    });
}

function startVoiceRecognition() {
    return new Promise((resolve, reject) => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            resolve(transcript);
        };
        
        recognition.onerror = (event) => {
            reject(event.error);
        };
        
        recognition.start();
    });
}

// ===== IMAGE UPLOAD =====
function setupImageUpload() {
    if (!imageUpload || !imagePreview) return;
    
    imageUpload.addEventListener('change', async function(e) {
        imagePreview.innerHTML = '';
        
        if (e.target.files.length === 0) return;
        
        // Show preview
        Array.from(e.target.files).forEach(file => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                imagePreview.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
        
        showNotification(`${e.target.files.length} image(s) selected`, 'success');
        
        // Auto-analyze first image for disease
        if (e.target.files.length >= 1) {
            await analyzeDiseaseImage(e.target.files[0]);
        }
    });
}

async function analyzeDiseaseImage(file) {
    showLoading();
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch(`${API_BASE_URL}/predict-disease`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            showNotification(`Error: ${data.error}`, 'error');
            hideLoading();
            return;
        }
        
        displayDiseaseResult(data);
        
    } catch (error) {
        showNotification('Failed to analyze image', 'error');
        console.error(error);
    } finally {
        hideLoading();
    }
}

function displayDiseaseResult(data) {
    const disease = data.disease.replace(/_/g, ' ');
    const confidence = (data.confidence * 100).toFixed(2);
    const currentLang = languageSelect ? languageSelect.value : 'en';
    
    // Translate disease name if needed
    let displayDisease = disease;
    let displayTreatment = data.treatment;
    
    // Store original for translation
    window.lastDiseaseResult = data;
    
    const resultHTML = `
        <div class="response-card disease-result" data-disease="${data.disease}" data-treatment="${data.treatment}">
            <div class="response-header">
                <div class="avatar"><i class="fas fa-robot"></i></div>
                <div>
                    <h4>FarmBuddy AI - Disease Detection</h4>
                    <p class="time">Just now</p>
                </div>
            </div>
            <div class="response-content">
                <p>🔍 <strong>Disease Identified:</strong></p>
                <div class="info-box">
                    <p><i class="fas fa-leaf"></i> <strong>Disease:</strong> <span class="disease-name">${displayDisease}</span></p>
                    <p><i class="fas fa-chart-line"></i> <strong>Confidence:</strong> ${confidence}%</p>
                    <p><i class="fas fa-flask"></i> <strong>Treatment:</strong> <span class="treatment-text">${displayTreatment}</span></p>
                </div>
                ${currentLang !== 'en' ? `<p class="translation-note" style="color: var(--green-primary); margin-top: 10px;"><i class="fas fa-language"></i> Showing in ${INDIAN_LANGUAGES[currentLang]}</p>` : ''}
            </div>
            <div class="response-footer">
                <button class="listen-btn" onclick="textToSpeech(this)"><i class="fas fa-volume-up"></i> Listen</button>
                <div class="response-actions">
                    <button onclick="shareResponse(this)"><i class="fas fa-share-alt"></i></button>
                    <button onclick="bookmarkResponse(this)"><i class="far fa-bookmark"></i></button>
                </div>
            </div>
        </div>
    `;
    
    if (responseArea) {
        responseArea.innerHTML = resultHTML + (responseArea.innerHTML || '');
    }
}

// ===== VIDEO UPLOAD =====
function setupVideoUpload() {
    if (!videoUpload) return;
    
    videoUpload.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            showNotification(`Video selected: ${e.target.files[0].name}`, 'success');
            showNotification('Video processing coming soon!', 'info');
        }
    });
}

// ===== QUERY SUBMISSION =====
function setupQueryInput() {
    if (!queryInput) return;
    
    queryInput.addEventListener('keypress', async function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            await submitQuery();
        }
    });
}

async function submitQuery() {
    if (!queryInput) return;
    
    const query = queryInput.value.trim();
    if (!query) {
        showNotification('Please enter a question', 'warning');
        return;
    }
    
    saveQueryToHistory(query);
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showNotification(`Error: ${data.error}`, 'error');
            hideLoading();
            return;
        }
        
        displayChatResponse(data);
        
    } catch (error) {
        showNotification('Failed to get response', 'error');
        console.error(error);
    } finally {
        hideLoading();
    }
}

function displayChatResponse(data) {
    const response = data.response;
    const detectedLang = data.detected_language;
    const intent = data.intent;
    const originalQuery = data.original_query;
    
    // Get language name
    const langName = INDIAN_LANGUAGES[detectedLang] || 'English';
    
    // Create entity badges if any
    let entityHTML = '';
    if (data.entities && Object.keys(data.entities).length > 0) {
        entityHTML = '<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px;">';
        Object.entries(data.entities).forEach(([key, values]) => {
            if (values && values.length > 0) {
                values.forEach(value => {
                    entityHTML += `<span style="background: var(--green-dim); color: var(--green-primary); padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">${key}: ${value}</span>`;
                });
            }
        });
        entityHTML += '</div>';
    }
    
    const responseHTML = `
        <div class="response-card chat-response" data-original-query="${originalQuery}">
            <div class="response-header">
                <div class="avatar"><i class="fas fa-robot"></i></div>
                <div>
                    <h4>FarmBuddy AI</h4>
                    <p class="time">Detected: ${langName} | Intent: ${intent}</p>
                </div>
            </div>
            <div class="response-content">
                ${entityHTML || ''}
                <p>${response.replace(/\n/g, '<br>')}</p>
                ${detectedLang !== 'en' ? `<p class="translation-note" style="color: var(--green-primary); margin-top: 10px;"><i class="fas fa-language"></i> Translated from English to ${langName}</p>` : ''}
            </div>
            <div class="response-footer">
                <button class="listen-btn" onclick="textToSpeech(this)"><i class="fas fa-volume-up"></i> Listen</button>
                <div class="response-actions">
                    <button onclick="shareResponse(this)"><i class="fas fa-share-alt"></i></button>
                    <button onclick="bookmarkResponse(this)"><i class="far fa-bookmark"></i></button>
                </div>
            </div>
        </div>
    `;
    
    if (responseArea) {
        responseArea.innerHTML = responseHTML + (responseArea.innerHTML || '');
    }
}

// ===== QUICK ACTIONS =====
function setupQuickActions() {
    window.setQuery = async function(type) {
        if (!queryInput) return;
        
        const queries = {
            crop: "How to grow tomatoes in rainy season?",
            market: "What's the price of wheat in Punjab?",
            schemes: "What government schemes are available for farmers?",
            disease: "My tomato plants have yellow leaves with brown spots."
        };
        
        queryInput.value = queries[type];
        await submitQuery();
    };
}

// ===== TEXT TO SPEECH =====
window.textToSpeech = function(button) {
    const responseCard = button.closest('.response-card');
    if (!responseCard) return;
    
    const content = responseCard.querySelector('.response-content');
    if (!content) return;
    
    // Get text content
    const text = content.innerText;
    
    if (!('speechSynthesis' in window)) {
        showNotification('Text-to-speech not supported in this browser', 'error');
        return;
    }
    
    // Get selected language
    const lang = languageSelect ? languageSelect.value : 'en';
    
    // Stop any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Set language (simplified - browsers support limited languages)
    if (lang === 'hi') utterance.lang = 'hi-IN';
    else if (lang === 'ta') utterance.lang = 'ta-IN';
    else if (lang === 'te') utterance.lang = 'te-IN';
    else if (lang === 'bn') utterance.lang = 'bn-IN';
    else if (lang === 'mr') utterance.lang = 'mr-IN';
    else if (lang === 'gu') utterance.lang = 'gu-IN';
    else if (lang === 'kn') utterance.lang = 'kn-IN';
    else if (lang === 'ml') utterance.lang = 'ml-IN';
    else if (lang === 'pa') utterance.lang = 'pa-IN';
    else if (lang === 'ur') utterance.lang = 'ur-PK';
    else utterance.lang = 'en-US';
    
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    utterance.onstart = () => {
        button.innerHTML = '<i class="fas fa-stop"></i> Stop';
    };
    
    utterance.onend = () => {
        button.innerHTML = '<i class="fas fa-volume-up"></i> Listen';
    };
    
    utterance.onerror = () => {
        button.innerHTML = '<i class="fas fa-volume-up"></i> Listen';
        showNotification('Error playing speech', 'error');
    };
    
    window.speechSynthesis.speak(utterance);
};

// ===== SHARE RESPONSE =====
window.shareResponse = function(button) {
    const responseCard = button.closest('.response-card');
    if (!responseCard) return;
    
    const text = responseCard.querySelector('.response-content').innerText;
    
    if (navigator.share) {
        navigator.share({
            title: 'FarmBuddy Advice',
            text: text,
            url: window.location.href
        }).catch(() => {
            copyToClipboard(text);
        });
    } else {
        copyToClipboard(text);
    }
};

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy', 'error');
    });
}

// ===== BOOKMARK RESPONSE =====
window.bookmarkResponse = function(button) {
    const icon = button.querySelector('i');
    const responseCard = button.closest('.response-card');
    
    if (!icon || !responseCard) return;
    
    icon.classList.toggle('far');
    icon.classList.toggle('fas');
    
    if (icon.classList.contains('fas')) {
        saveToBookmarks(responseCard);
        showNotification('✓ Saved to bookmarks', 'success');
    } else {
        removeFromBookmarks(responseCard);
        showNotification('Removed from bookmarks', 'info');
    }
};

// ===== LOADING FUNCTIONS =====
function showLoading() {
    if (loading) loading.style.display = 'block';
}

function hideLoading() {
    if (loading) loading.style.display = 'none';
}

// ===== NOTIFICATION SYSTEM =====
function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    notification.innerHTML = `
        <i class="fas ${icons[type] || icons.info}"></i>
        <span>${message}</span>
    `;
    
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${isDark ? '#1a1a1a' : 'white'};
        color: ${isDark ? '#00ff88' : '#2e7d32'};
        padding: 12px 24px;
        border-radius: 30px;
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        border: 2px solid ${isDark ? '#00ff88' : '#2e7d32'};
        box-shadow: ${isDark ? '0 0 20px rgba(0,255,136,0.3)' : '0 5px 15px rgba(46,125,50,0.2)'};
        font-weight: 500;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ===== HISTORY FUNCTIONS =====
function saveQueryToHistory(query) {
    if (!query.trim()) return;
    
    let history = JSON.parse(localStorage.getItem('queryHistory') || '[]');
    history.push({
        query: query,
        timestamp: new Date().toISOString()
    });
    
    if (history.length > 20) {
        history = history.slice(-20);
    }
    
    localStorage.setItem('queryHistory', JSON.stringify(history));
}

function saveToBookmarks(card) {
    let bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
    const content = card.querySelector('.response-content').innerHTML;
    const header = card.querySelector('.response-header h4').innerText;
    
    bookmarks.push({
        id: Date.now(),
        title: header,
        content: content,
        timestamp: new Date().toISOString()
    });
    
    if (bookmarks.length > 20) {
        bookmarks = bookmarks.slice(-20);
    }
    
    localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
}

function removeFromBookmarks(card) {
    // Implementation for removing bookmarks
    // This would need a unique identifier
}

// ===== NAVIGATION FUNCTIONS =====
function setupNavigation() {
    if (!navItems || navItems.length === 0) return;
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
            
            const icon = this.querySelector('i').className;
            if (icon.includes('fa-history')) {
                showHistory();
            } else if (icon.includes('fa-bookmark')) {
                showSaved();
            } else if (icon.includes('fa-user')) {
                showProfile();
            } else {
                showHome();
            }
        });
    });
    
    // FAB button
    if (fabButton) {
        fabButton.addEventListener('click', () => {
            if (voiceBtn) voiceBtn.click();
        });
    }
}

function showHistory() {
    if (!responseArea) return;
    
    const history = JSON.parse(localStorage.getItem('queryHistory') || '[]');
    
    if (history.length === 0) {
        responseArea.innerHTML = `
            <div class="response-card">
                <div class="response-header">
                    <div class="avatar"><i class="fas fa-history"></i></div>
                    <div>
                        <h4>Query History</h4>
                    </div>
                </div>
                <div style="text-align: center; padding: 30px;">
                    <i class="fas fa-search" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 15px;"></i>
                    <p style="color: var(--text-muted);">No history yet. Start asking questions!</p>
                </div>
            </div>
        `;
        return;
    }
    
    let html = '<h3 style="margin-bottom: 20px;">Recent Queries</h3>';
    history.reverse().forEach(item => {
        const date = new Date(item.timestamp).toLocaleString();
        html += `
            <div class="response-card" style="cursor: pointer;" onclick="document.getElementById('queryInput').value = '${item.query.replace(/'/g, "\\'")}'; document.querySelector('.nav-item.active')?.classList.remove('active'); document.querySelector('.nav-item:first-child')?.classList.add('active');">
                <div class="response-header">
                    <div class="avatar"><i class="fas fa-history"></i></div>
                    <div>
                        <h4>${date}</h4>
                        <p class="time">Click to reuse</p>
                    </div>
                </div>
                <p style="color: var(--text-secondary);">${item.query}</p>
            </div>
        `;
    });
    responseArea.innerHTML = html;
}

function showSaved() {
    if (!responseArea) return;
    
    const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
    
    if (bookmarks.length === 0) {
        responseArea.innerHTML = `
            <div class="response-card">
                <div class="response-header">
                    <div class="avatar"><i class="fas fa-bookmark"></i></div>
                    <div>
                        <h4>Saved Items</h4>
                    </div>
                </div>
                <div style="text-align: center; padding: 30px;">
                    <i class="far fa-bookmark" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 15px;"></i>
                    <p style="color: var(--text-muted);">No saved items yet.</p>
                </div>
            </div>
        `;
        return;
    }
    
    let html = '<h3 style="margin-bottom: 20px;">Saved Items</h3>';
    bookmarks.reverse().forEach(bookmark => {
        html += `
            <div class="response-card">
                <div class="response-header">
                    <div class="avatar"><i class="fas fa-bookmark"></i></div>
                    <div>
                        <h4>${bookmark.title || 'Saved Advice'}</h4>
                        <p class="time">Saved on ${new Date(bookmark.timestamp).toLocaleDateString()}</p>
                    </div>
                </div>
                <div class="response-content">
                    ${bookmark.content}
                </div>
                <div class="response-footer">
                    <button class="listen-btn" onclick="textToSpeech(this)"><i class="fas fa-volume-up"></i> Listen</button>
                </div>
            </div>
        `;
    });
    responseArea.innerHTML = html;
}

function showProfile() {
    if (!responseArea) return;
    
    const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]').length;
    const history = JSON.parse(localStorage.getItem('queryHistory') || '[]').length;
    
    responseArea.innerHTML = `
        <div class="response-card">
            <div class="response-header">
                <div class="avatar"><i class="fas fa-user"></i></div>
                <div>
                    <h4>Farmer Profile</h4>
                    <p class="time">Member since ${new Date().toLocaleDateString()}</p>
                </div>
            </div>
            <div style="padding: 20px; text-align: center;">
                <div style="width: 100px; height: 100px; border-radius: 50%; background: linear-gradient(135deg, var(--green-primary), var(--green-secondary)); margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                    <i class="fas fa-seedling" style="font-size: 3rem; color: white;"></i>
                </div>
                <h3 style="margin-bottom: 10px;">Welcome, Farmer!</h3>
                <p style="color: var(--text-muted); margin-bottom: 30px;">Your personal farming assistant</p>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                    <div style="background: var(--bg-input); padding: 20px; border-radius: 20px; border: 2px solid var(--border-color);">
                        <i class="fas fa-comment" style="font-size: 2rem; color: var(--green-primary); margin-bottom: 10px;"></i>
                        <p style="font-size: 2rem; font-weight: bold;">${history}</p>
                        <p style="color: var(--text-muted);">Queries</p>
                    </div>
                    <div style="background: var(--bg-input); padding: 20px; border-radius: 20px; border: 2px solid var(--border-color);">
                        <i class="fas fa-bookmark" style="font-size: 2rem; color: var(--green-primary); margin-bottom: 10px;"></i>
                        <p style="font-size: 2rem; font-weight: bold;">${bookmarks}</p>
                        <p style="color: var(--text-muted);">Saved</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function showHome() {
    window.location.reload();
}

// ===== LOAD INITIAL DATA =====
async function loadInitialData() {
    // Load FAQs in default language
    await loadFAQs('en');
    
    // Show welcome message
    setTimeout(() => {
        if (responseArea) {
            const welcomeHTML = `
                <div class="response-card">
                    <div class="response-header">
                        <div class="avatar"><i class="fas fa-robot"></i></div>
                        <div>
                            <h4>FarmBuddy AI</h4>
                            <p class="time">Welcome</p>
                        </div>
                    </div>
                    <div class="response-content">
                        <p>🌾 <strong>Welcome to FarmBuddy!</strong></p>
                        <p>I can help you with:</p>
                        <div class="info-box">
                            <p><i class="fas fa-seedling"></i> Crop advisory and farming tips</p>
                            <p><i class="fas fa-chart-line"></i> Market prices for all crops</p>
                            <p><i class="fas fa-file-alt"></i> Government scheme information</p>
                            <p><i class="fas fa-search"></i> Disease detection from photos</p>
                            <p><i class="fas fa-language"></i> Support for 22 Indian languages</p>
                        </div>
                        <p style="margin-top: 15px;">How can I help you today?</p>
                    </div>
                </div>
            `;
            responseArea.innerHTML = welcomeHTML + responseArea.innerHTML;
        }
    }, 500);
}

// ===== SETUP ALL EVENT LISTENERS =====
function setupEventListeners() {
    setupVoiceInput();
    setupImageUpload();
    setupVideoUpload();
    setupQueryInput();
    setupQuickActions();
    setupNavigation();
}

// ===== ADD ANIMATION STYLES =====
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .translation-note {
            font-size: 0.85rem;
            padding: 5px 10px;
            background: var(--green-dim);
            border-radius: 20px;
            display: inline-block;
        }
    `;
    document.head.appendChild(style);
}