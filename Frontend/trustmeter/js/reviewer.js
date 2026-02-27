// ===== Configuration =====
const API_ENDPOINT = ''; // POST /analyze-product — set your backend URL here

// ===== State =====
let userRequirements = '';
let specText = '';
let specImage = null;
let score = null;
let summary = '';
let pros = [];
let cons = [];

// ===== DOM =====
const requirementsInput = document.getElementById('user-requirements');
const specTextInput = document.getElementById('spec-text');
const uploadZone = document.getElementById('rv-upload-zone');
const fileInput = document.getElementById('rv-file-input');
const imagePreview = document.getElementById('rv-image-preview');
const previewImg = document.getElementById('rv-preview-img');
const fileNameText = document.getElementById('rv-file-name-text');
const removeBtn = document.getElementById('rv-remove-btn');
const generateBtn = document.getElementById('generate-btn');
const genSpinner = document.getElementById('gen-spinner');
const loadingOverlay = document.getElementById('loading-overlay');
const resultsSection = document.getElementById('rv-results');
const ringFill = document.getElementById('ring-fill');
const scoreValue = document.getElementById('rv-score-value');
const summaryEl = document.getElementById('rv-summary');
const prosEl = document.getElementById('rv-pros');
const consEl = document.getElementById('rv-cons');

// ===== Input Tracking & Button State =====
function updateGenerateState() {
    userRequirements = requirementsInput.value.trim();
    specText = specTextInput.value.trim();

    const hasSpecs = specText.length > 0 || specImage !== null;
    if (hasSpecs) {
        generateBtn.disabled = false;
        generateBtn.classList.add('enabled');
    } else {
        generateBtn.disabled = true;
        generateBtn.classList.remove('enabled');
    }
}

requirementsInput.addEventListener('input', updateGenerateState);
specTextInput.addEventListener('input', updateGenerateState);

// ===== Spec Image Upload =====
uploadZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleSpecFile(file);
});

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
    if (file) handleSpecFile(file);
});

function handleSpecFile(file) {
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
        alert('Please upload a JPG or PNG image.');
        return;
    }

    specImage = file;
    fileNameText.textContent = file.name;

    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        imagePreview.classList.add('visible');
        uploadZone.style.display = 'none';
    };
    reader.readAsDataURL(file);

    updateGenerateState();
}

removeBtn.addEventListener('click', () => {
    specImage = null;
    fileInput.value = '';
    previewImg.src = '';
    imagePreview.classList.remove('visible');
    uploadZone.style.display = '';
    updateGenerateState();
});

// ===== Generate =====
generateBtn.addEventListener('click', async () => {
    if (generateBtn.disabled) return;

    // Enter loading state
    generateBtn.classList.add('loading');
    genSpinner.style.display = 'flex';
    resultsSection.classList.remove('visible');

    let result;

    if (API_ENDPOINT) {
        try {
            const formData = new FormData();
            formData.append('userRequirements', userRequirements);
            formData.append('specText', specText);
            if (specImage) formData.append('specImage', specImage);

            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                body: formData,
            });
            result = await response.json();
        } catch (err) {
            console.error('API Error:', err);
            generateBtn.classList.remove('loading');
            genSpinner.style.display = 'none';
            alert('Failed to generate review. Please try again.');
            return;
        }
    } else {
        result = await mockAnalysis();
    }

    // Store state
    score = result.score;
    summary = result.summary;
    pros = result.pros;
    cons = result.cons;

    // Exit loading
    generateBtn.classList.remove('loading');
    genSpinner.style.display = 'none';

    displayResults(result);
});

// ===== Mock Backend =====
function mockAnalysis() {
    return new Promise((resolve) => {
        setTimeout(() => {
            const mockScore = Math.floor(Math.random() * 60) + 40; // 40–99

            const summaries = [
                'This product aligns well with your stated requirements. The specifications indicate strong performance in your primary use cases, though battery life may fall slightly short of expectations for extended mobile usage.',
                'Based on the provided specifications, this product is a solid match for your needs. The processing power and display quality are excellent, but the storage capacity may require supplementing with external solutions.',
                'The product meets most of your requirements effectively. It excels in performance and build quality, but the price-to-value ratio suggests exploring alternative options in the same category for better budget optimization.',
            ];

            const prosPool = [
                'High-performance processor matches your workload needs',
                'Excellent display quality for content creation',
                'Adequate RAM for multitasking',
                'Modern GPU supports your gaming requirements',
                'Good build quality and design',
                'Strong connectivity options (WiFi 6, Bluetooth 5.2)',
                'Competitive pricing in its segment',
                'Fast SSD storage for quick load times',
            ];

            const consPool = [
                'Battery life below your stated preference',
                'Heavier than average in this category',
                'Limited port selection may need adapters',
                'Fan noise under heavy load',
                'No SD card reader included',
                'Display brightness could be better outdoors',
                'Warranty coverage is basic',
            ];

            const selectedPros = prosPool.sort(() => 0.5 - Math.random()).slice(0, Math.floor(Math.random() * 2) + 3);
            const selectedCons = consPool.sort(() => 0.5 - Math.random()).slice(0, Math.floor(Math.random() * 2) + 2);

            resolve({
                score: mockScore,
                summary: summaries[Math.floor(Math.random() * summaries.length)],
                pros: selectedPros,
                cons: selectedCons,
            });
        }, 2200);
    });
}

// ===== Display Results =====
function displayResults(result) {
    // Circular score animation
    const circumference = 2 * Math.PI * 52; // r=52
    ringFill.style.strokeDasharray = circumference;
    ringFill.style.strokeDashoffset = circumference;

    // Score color
    let strokeColor;
    if (result.score < 40) strokeColor = 'var(--score-red)';
    else if (result.score < 60) strokeColor = 'var(--score-yellow)';
    else if (result.score < 80) strokeColor = '#3b82f6';
    else strokeColor = 'var(--score-green)';
    ringFill.style.stroke = strokeColor;

    // Show section first
    resultsSection.classList.add('visible');

    // Animate score after a tick
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            const offset = circumference - (result.score / 100) * circumference;
            ringFill.style.strokeDashoffset = offset;
        });
    });

    // Animate number
    animateCounter(scoreValue, 0, result.score, 1200);

    // Summary
    summaryEl.textContent = result.summary;

    // Pros
    prosEl.innerHTML = '';
    result.pros.forEach((p) => {
        const li = document.createElement('li');
        li.textContent = p;
        prosEl.appendChild(li);
    });

    // Cons
    consEl.innerHTML = '';
    result.cons.forEach((c) => {
        const li = document.createElement('li');
        li.textContent = c;
        consEl.appendChild(li);
    });

    // Scroll
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ===== Counter Animation =====
function animateCounter(el, from, to, duration) {
    const start = performance.now();
    function tick(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        const value = Math.round(from + (to - from) * eased);
        el.textContent = value;
        if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
}
