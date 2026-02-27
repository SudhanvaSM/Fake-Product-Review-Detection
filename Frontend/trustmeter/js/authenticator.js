// ===== Configuration =====
const API_ENDPOINT = 'http://127.0.0.1:8000'; // Set your backend URL here for real integration

// ===== DOM References =====
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const browseLink = document.getElementById('browse-link');
const imagePreview = document.getElementById('image-preview');
const previewImg = document.getElementById('preview-img');
const fileNameText = document.getElementById('file-name-text');
const removeBtn = document.getElementById('remove-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const loadingOverlay = document.getElementById('loading-overlay');
const resultsSection = document.getElementById('results-section');
const scoreDisplay = document.getElementById('score-display');
const scoreBarFill = document.getElementById('score-bar-fill');
const verdictContainer = document.getElementById('verdict-container');
const summaryText = document.getElementById('summary-text');
const keywordsList = document.getElementById('keywords-list');

let selectedFile = null;

// ===== Upload Handling =====

// Click to browse
browseLink.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

uploadZone.addEventListener('click', () => {
    fileInput.click();
});

// File input change
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
});

// Drag & drop
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
});

function handleFile(file) {
    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
        alert('Please upload a JPG or PNG image.');
        return;
    }

    selectedFile = file;
    fileNameText.textContent = file.name;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        imagePreview.classList.add('visible');
    };
    reader.readAsDataURL(file);

    // Enable analyze button
    analyzeBtn.classList.add('enabled');
    analyzeBtn.disabled = false;

    // Hide results if showing
    resultsSection.classList.remove('visible');
}

// Remove file
removeBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    previewImg.src = '';
    imagePreview.classList.remove('visible');
    analyzeBtn.classList.remove('enabled');
    analyzeBtn.disabled = true;
    resultsSection.classList.remove('visible');
});

// ===== Analyze =====
analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    // Show loading
    loadingOverlay.classList.add('visible');
    resultsSection.classList.remove('visible');

    let result;
    if (API_ENDPOINT) {
        // Real backend integration
        try {
            const formData = new FormData();
            formData.append('image', selectedFile);
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                body: formData,
            });
            result = await response.json();
        } catch (err) {
            console.error('API Error:', err);
            loadingOverlay.classList.remove('visible');
            alert('Failed to analyze. Please try again.');
            return;
        }
    } else {
        // Mock analysis (simulated delay)
        result = await mockAnalysis();
    }

    // Hide loading
    loadingOverlay.classList.remove('visible');

    // Show results
    displayResults(result);
});

// ===== Mock Backend =====
function mockAnalysis() {
    return new Promise((resolve) => {
        setTimeout(() => {
            const trustScore = Math.floor(Math.random() * 100) + 1;
            const isFake = trustScore < 50;

            const fakeSummaries = [
                'This review exhibits several hallmarks of inauthentic content. The language patterns suggest automated generation, with overly promotional tone and lack of specific product details. The sentiment appears artificially inflated.',
                'Analysis indicates a high probability of fabricated content. The review lacks contextual specificity and uses generic praise language commonly associated with incentivized or bot-generated reviews.',
                'Multiple indicators suggest this review may not be genuine. The writing style shows repetitive patterns and the emotional tone is inconsistent with organic user feedback.'
            ];

            const genuineSummaries = [
                'This review demonstrates authentic user experience characteristics. The language contains specific product references, balanced sentiment, and natural writing patterns consistent with genuine customer feedback.',
                'Analysis suggests this is a legitimate review. The content includes detailed product observations, realistic expectations, and organic language patterns typical of verified purchasers.',
                'The review shows strong indicators of authenticity. Specific usage details, balanced pros/cons, and natural language flow are consistent with genuine user experiences.'
            ];

            const fakeKeywords = ['too good', 'perfect', 'amazing product', 'best ever', 'five stars', 'highly recommend', 'life changing', 'must buy'];
            const genuineKeywords = ['decent', 'minor issue', 'overall good', 'expected better'];

            const allKeywords = isFake ? fakeKeywords : genuineKeywords;
            const selectedKeywords = allKeywords.sort(() => 0.5 - Math.random()).slice(0, Math.floor(Math.random() * 3) + 2);

            const summaryPool = isFake ? fakeSummaries : genuineSummaries;
            const summary = summaryPool[Math.floor(Math.random() * summaryPool.length)];

            resolve({
                trustScore,
                verdict: isFake ? 'Likely Fake' : 'Likely Genuine',
                isFake,
                summary,
                flaggedKeywords: selectedKeywords,
            });
        }, 2000);
    });
}

// ===== Display Results =====
function displayResults(result) {
    // Score
    scoreDisplay.textContent = result.trustScore + '%';

    // Score bar
    scoreBarFill.style.width = '0%';
    scoreBarFill.className = 'score-bar-fill';

    if (result.trustScore < 25) scoreBarFill.classList.add('low');
    else if (result.trustScore < 50) scoreBarFill.classList.add('medium');
    else if (result.trustScore < 75) scoreBarFill.classList.add('high');
    else scoreBarFill.classList.add('very-high');

    // Animate bar after a tick
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            scoreBarFill.style.width = result.trustScore + '%';
        });
    });

    // Verdict badge
    const verdictClass = result.isFake ? 'fake' : 'genuine';
    const verdictIcon = result.isFake
        ? '<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
        : '<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';

    verdictContainer.innerHTML = `<span class="verdict-badge ${verdictClass}">${verdictIcon} ${result.verdict}</span>`;

    // Summary
    summaryText.textContent = result.summary;

    // Keywords
    keywordsList.innerHTML = '';
    result.flaggedKeywords.forEach((kw) => {
        const li = document.createElement('li');
        li.textContent = kw;
        keywordsList.appendChild(li);
    });

    // Show section
    resultsSection.classList.add('visible');

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
