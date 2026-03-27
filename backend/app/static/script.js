// ========================================
// Smart Debugger - Main JavaScript
// ========================================

// ---- Configuration ----
const API_BASE = window.location.origin; // FastAPI serves both frontend + API

// ---- DOM Elements ----
const themeToggle = document.getElementById('themeToggle');
const codeInput = document.getElementById('codeInput');
const lineNumbers = document.getElementById('lineNumbers');
const languageSelect = document.getElementById('languageSelect');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const fileName = document.getElementById('fileName');
const analyzeBtn = document.getElementById('analyzeBtn');
const clearBtn = document.getElementById('clearBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');

const modeTabs = document.querySelectorAll('.mode-tab');
const resultTabs = document.querySelectorAll('.result-tab');
const tabContents = document.querySelectorAll('.tab-content');

const resultPlaceholder = document.getElementById('resultPlaceholder');
const resultContent = document.getElementById('resultContent');
const issuesList = document.getElementById('issuesList');
const suggestedCode = document.getElementById('suggestedCode');
const explanation = document.getElementById('explanation');

const diffOriginal = document.getElementById('diffOriginal');
const diffFixed = document.getElementById('diffFixed');

const qualityFill = document.getElementById('qualityFill');
const qualityValue = document.getElementById('qualityValue');
const performanceFill = document.getElementById('performanceFill');
const performanceValue = document.getElementById('performanceValue');
const securityFill = document.getElementById('securityFill');
const securityValue = document.getElementById('securityValue');
const maintainabilityFill = document.getElementById('maintainabilityFill');
const maintainabilityValue = document.getElementById('maintainabilityValue');

// ---- State ----
let currentMode = 'debug';
let currentTab = 'analysis';
let isAnalyzing = false;
let lastResults = null; // cache for copy/download

// ========================================
// Theme Toggle
// ========================================
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    themeToggle.classList.add('animating');
    setTimeout(() => themeToggle.classList.remove('animating'), 300);
}

themeToggle.addEventListener('click', toggleTheme);
initTheme();

// ========================================
// Line Numbers
// ========================================
function updateLineNumbers() {
    const lines = codeInput.value.split('\n').length;
    lineNumbers.innerHTML = Array.from({ length: lines }, (_, i) => `<span>${i + 1}</span>`).join('');
}

function syncScroll() {
    lineNumbers.scrollTop = codeInput.scrollTop;
}

codeInput.addEventListener('input', updateLineNumbers);
codeInput.addEventListener('scroll', syncScroll);
setTimeout(updateLineNumbers, 100);

// ========================================
// Mode Tabs
// ========================================
modeTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        modeTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentMode = tab.dataset.mode;

        const modeLabels = {
            debug: 'Analyze Code',
            optimize: 'Optimize Code',
            explain: 'Explain Code',
            review: 'Review Code',
            convert: 'Convert Code'
        };
        const btnContent = analyzeBtn.querySelector('.btn-content');
        btnContent.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            ${modeLabels[currentMode]}
        `;
    });
});

// ========================================
// Result Tabs
// ========================================
resultTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        resultTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentTab = tab.dataset.tab;

        tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === `${currentTab}Tab`) {
                content.classList.add('active');
            }
        });
    });
});

// ========================================
// File Upload
// ========================================
uploadBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        fileName.textContent = file.name;
        const reader = new FileReader();
        reader.onload = (event) => {
            codeInput.value = event.target.result;
            updateLineNumbers();
            const ext = file.name.split('.').pop().toLowerCase();
            const langMap = { js: 'javascript', ts: 'typescript', py: 'python', java: 'java', cpp: 'cpp', c: 'cpp', rs: 'rust', go: 'go' };
            if (langMap[ext]) languageSelect.value = langMap[ext];
            showToast('File loaded successfully!');
        };
        reader.readAsText(file);
    }
});

// Drag and drop
const editorPanel = document.querySelector('.panel-editor');
editorPanel.addEventListener('dragover', (e) => { e.preventDefault(); editorPanel.classList.add('drag-over'); });
editorPanel.addEventListener('dragleave', () => editorPanel.classList.remove('drag-over'));
editorPanel.addEventListener('drop', (e) => {
    e.preventDefault();
    editorPanel.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
            codeInput.value = event.target.result;
            updateLineNumbers();
            fileName.textContent = file.name;
            showToast('File loaded successfully!');
        };
        reader.readAsText(file);
    }
});

// ========================================
// Clear Button
// ========================================
if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        codeInput.value = '';
        updateLineNumbers();
        fileName.textContent = '';
        resultPlaceholder.style.display = 'flex';
        resultContent.style.display = 'none';
        lastResults = null;
        showToast('Editor cleared');
    });
}

// ========================================
// Analysis — Real API Call
// ========================================
analyzeBtn.addEventListener('click', async () => {
    const code = codeInput.value.trim();
    if (!code) {
        showToast('Please enter some code to analyze', 'error');
        return;
    }
    await performAnalysis(code);
});

async function performAnalysis(code) {
    if (isAnalyzing) return;

    isAnalyzing = true;
    analyzeBtn.classList.add('loading');
    analyzeBtn.disabled = true;
    showLoading();
    startLoadingSteps();

    try {
        const response = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code,
                language: languageSelect.value,
                mode: currentMode
            })
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Server error ${response.status}`);
        }

        const results = await response.json();

        // Finish loading animation
        await finishLoadingSteps();

        // Store and display
        lastResults = results;
        displayResults(results, code);
        showToast('Analysis complete!');

    } catch (error) {
        console.error('Analysis error:', error);
        showToast(error.message || 'Analysis failed. Please try again.', 'error');
    } finally {
        isAnalyzing = false;
        analyzeBtn.classList.remove('loading');
        analyzeBtn.disabled = false;
        hideLoading();
    }
}

// ========================================
// Loading Step Animation
// ========================================
let loadingStepInterval = null;

function startLoadingSteps() {
    const steps = document.querySelectorAll('.loader-step');
    steps.forEach(s => s.classList.remove('active', 'done'));
    let idx = 0;
    steps[0].classList.add('active');

    loadingStepInterval = setInterval(() => {
        if (idx < steps.length) {
            steps[idx].classList.remove('active');
            steps[idx].classList.add('done');
        }
        idx++;
        if (idx < steps.length) {
            steps[idx].classList.add('active');
        } else {
            clearInterval(loadingStepInterval);
            loadingStepInterval = null;
        }
    }, 1200);
}

async function finishLoadingSteps() {
    if (loadingStepInterval) clearInterval(loadingStepInterval);
    const steps = document.querySelectorAll('.loader-step');
    steps.forEach(s => { s.classList.remove('active'); s.classList.add('done'); });
    await sleep(400);
    steps.forEach(s => s.classList.remove('active', 'done'));
}

// ========================================
// Display Results
// ========================================
function displayResults(results, originalCode) {
    resultPlaceholder.style.display = 'none';
    resultContent.style.display = 'block';

    // Issues
    const issues = results.issues || [];
    if (issues.length === 0) {
        issuesList.innerHTML = `
            <div class="issue-item issue-info">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
                </svg>
                <span>No major issues found. Code looks good!</span>
            </div>`;
    } else {
        issuesList.innerHTML = issues.map(issue => {
            const severity = issue.severity || issue.type || 'error';
            const cssClass = severity === 'warning' ? 'issue-warning' : severity === 'info' ? 'issue-info' : '';
            const iconPath = severity === 'warning'
                ? '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
                : severity === 'info'
                ? '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>'
                : '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>';
            return `
                <div class="issue-item ${cssClass}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${iconPath}</svg>
                    <span>${escapeHtml(issue.message)}</span>
                </div>`;
        }).join('');
    }

    // Suggested code
    const fixedCode = results.optimized_code || results.optimizedCode || '';
    suggestedCode.innerHTML = `<pre>${escapeHtml(fixedCode)}</pre>`;

    // Explanation
    explanation.textContent = results.explanation || '';

    // Diff view
    diffOriginal.textContent = originalCode || codeInput.value;
    diffFixed.textContent = fixedCode;

    // Metrics
    const scores = results.scores || {};
    animateMetric(qualityFill, qualityValue, scores.quality || 0);
    animateMetric(performanceFill, performanceValue, scores.performance || 0);
    animateMetric(securityFill, securityValue, scores.security || 0);
    animateMetric(maintainabilityFill, maintainabilityValue, scores.maintainability || 0);

    // Breakdown bars
    const breakdown = results.breakdown || {};
    const breakdownItems = document.querySelectorAll('.breakdown-item');
    const breakdownKeys = ['complexity', 'readability', 'best_practices', 'error_handling'];
    const breakdownKeysFallback = ['complexity', 'readability', 'bestPractices', 'errorHandling'];

    breakdownItems.forEach((item, index) => {
        const value = breakdown[breakdownKeys[index]] ?? breakdown[breakdownKeysFallback[index]] ?? 0;
        const fill = item.querySelector('.breakdown-fill');
        const valueEl = item.querySelector('.breakdown-value');
        setTimeout(() => {
            fill.style.setProperty('--width', `${value}%`);
            valueEl.textContent = value;
        }, 100 * index);
    });
}

function animateMetric(fillElement, valueElement, targetValue) {
    const circumference = 251.2;
    const offset = circumference - (targetValue / 100) * circumference;

    let color;
    if (targetValue >= 80) color = '#22c55e';
    else if (targetValue >= 60) color = '#f59e0b';
    else color = '#ef4444';

    fillElement.style.stroke = color;
    setTimeout(() => {
        fillElement.style.strokeDashoffset = offset;
        valueElement.textContent = targetValue;
    }, 100);
}

// ========================================
// Loading Overlay
// ========================================
function showLoading() { loadingOverlay.classList.add('show'); }
function hideLoading() { loadingOverlay.classList.remove('show'); }

// ========================================
// Toast Notifications
// ========================================
function showToast(message, type = 'success') {
    toastMessage.textContent = message;
    const icon = toast.querySelector('.toast-icon');
    if (type === 'error') {
        icon.innerHTML = '<path d="M18 6L6 18M6 6l12 12"/>';
        icon.style.color = '#ef4444';
    } else {
        icon.innerHTML = '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>';
        icon.style.color = '#22c55e';
    }
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// ========================================
// Utility Functions
// ========================================
function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========================================
// Keyboard Shortcuts
// ========================================
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        analyzeBtn.click();
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        toggleTheme();
    }
});

// ========================================
// Copy and Download
// ========================================
const copyBtn = document.getElementById('copyBtn');
const downloadBtn = document.getElementById('downloadBtn');

if (copyBtn) {
    copyBtn.addEventListener('click', () => {
        const code = suggestedCode.querySelector('pre')?.textContent || '';
        if (code) {
            navigator.clipboard.writeText(code);
            showToast('Code copied to clipboard!');
        } else {
            showToast('Nothing to copy yet', 'error');
        }
    });
}

if (downloadBtn) {
    downloadBtn.addEventListener('click', () => {
        const code = suggestedCode.querySelector('pre')?.textContent || '';
        if (code) {
            const extMap = { python: 'py', javascript: 'js', typescript: 'ts', java: 'java', cpp: 'cpp', rust: 'rs', go: 'go' };
            const ext = extMap[languageSelect.value] || 'txt';
            const blob = new Blob([code], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `optimized-code.${ext}`;
            a.click();
            URL.revokeObjectURL(url);
            showToast('File downloaded!');
        } else {
            showToast('Nothing to download yet', 'error');
        }
    });
}

// ========================================
// Challenge Section
// ========================================
const challengeBtn = document.querySelector('.btn-challenge');
if (challengeBtn) {
    challengeBtn.addEventListener('click', () => {
        codeInput.value = `// Daily Challenge: Fix the Memory Leak
// This React component has a memory leak issue.
// Can you identify and fix it?

function UserTracker({ userId }) {
    const [user, setUser] = useState(null);

    useEffect(() => {
        const fetchUser = async () => {
            const response = await fetch(\`/api/users/\${userId}\`);
            const data = await response.json();
            setUser(data);
        };

        fetchUser();

        // Subscribe to user updates
        const socket = new WebSocket('ws://api.example.com');
        socket.onmessage = (event) => {
            const update = JSON.parse(event.data);
            if (update.userId === userId) {
                setUser(update.user);
            }
        };

        // Bug: No cleanup function!
        // What happens when component unmounts?
    }, [userId]);

    return <div>{user?.name}</div>;
}`;
        updateLineNumbers();
        languageSelect.value = 'javascript';
        showToast('Challenge loaded! Find and fix the memory leak.');
        document.querySelector('.panel-editor').scrollIntoView({ behavior: 'smooth' });
    });
}

// ========================================
// Mobile Menu
// ========================================
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const navLinks = document.querySelector('.nav-links');
if (mobileMenuBtn && navLinks) {
    mobileMenuBtn.addEventListener('click', () => {
        navLinks.classList.toggle('mobile-open');
        mobileMenuBtn.classList.toggle('open');
    });
}

// ========================================
// Initialize
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    updateLineNumbers();
    const panels = document.querySelectorAll('.panel');
    panels.forEach((panel, index) => {
        panel.style.opacity = '0';
        panel.style.transform = 'translateY(20px)';
        setTimeout(() => {
            panel.style.transition = 'all 0.5s ease';
            panel.style.opacity = '1';
            panel.style.transform = 'translateY(0)';
        }, 100 * index);
    });

    // Health check
    fetch(`${API_BASE}/api/health`)
        .then(r => r.json())
        .then(data => {
            if (data.status === 'healthy') {
                console.log('✅ Backend connected —', data.ai_provider);
            }
        })
        .catch(() => console.warn('⚠️ Backend not reachable at', API_BASE));
});
