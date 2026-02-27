// ===== API Configuration =====
const API_ENDPOINT = 'http://localhost:8000/analyze';

// ===== State Variables =====
let reviewText = '';
let reviewImage = null;
let isLoading = false;

// ===== DOM References =====
const reviewTextInput = document.getElementById('review-text');
const validationMsg = document.getElementById('validation-msg');
const charCounter = document.getElementById('char-counter');
const uploadZone = document.getElementById('auth-upload-zone');
const fileInput = document.getElementById('auth-file-input');
const browseLink = document.getElementById('auth-browse-link');
const imagePreview = document.getElementById('auth-image-preview');
const previewImg = document.getElementById('auth-preview-img');
const fileNameText = document.getElementById('auth-file-name-text');
const removeBtn = document.getElementById('auth-remove-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const analyzeLabel = document.getElementById('analyze-label');
const btnSpinner = document.getElementById('btn-spinner');
const inputContainer = document.getElementById('auth-input-container');

// ===== Review Text Input =====
reviewTextInput.addEventListener('input', () => {
    reviewText = reviewTextInput.value.trim();
    charCounter.textContent = reviewTextInput.value.length + ' characters';
    updateValidation();
    updateButtonState();
});

reviewTextInput.addEventListener('blur', () => {
    // Show validation on blur if empty
    if (reviewText.length === 0) {
        validationMsg.classList.add('visible');
    }
});

function updateValidation() {
    if (reviewText.length > 0) {
        validationMsg.classList.remove('visible');
    } else {
        validationMsg.classList.add('visible');
    }
}

function updateButtonState() {
    if (reviewText.length > 0 && !isLoading) {
        analyzeBtn.disabled = false;
        analyzeBtn.classList.add('enabled');
    } else {
        analyzeBtn.disabled = true;
        analyzeBtn.classList.remove('enabled');
    }
}

// ===== Image Upload =====
browseLink.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
});

uploadZone.addEventListener('click', () => {
    fileInput.click();
});

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
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
        alert('Please upload a JPG or PNG image.');
        return;
    }

    // Keep original file — no renaming
    reviewImage = file;
    fileNameText.textContent = file.name;

    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        imagePreview.classList.add('visible');
        uploadZone.style.display = 'none';
    };
    reader.readAsDataURL(file);
}

// Remove image
removeBtn.addEventListener('click', () => {
    reviewImage = null;
    fileInput.value = '';
    previewImg.src = '';
    imagePreview.classList.remove('visible');
    uploadZone.style.display = '';
});

// ===== Analyze Button =====
analyzeBtn.addEventListener('click', async () => {
    if (isLoading || reviewText.length === 0) return;

    // Enter loading state
    isLoading = true;
    analyzeBtn.classList.add('loading');
    analyzeBtn.disabled = true;
    analyzeBtn.classList.remove('enabled');
    btnSpinner.style.display = 'flex';

    // Disable inputs
    reviewTextInput.disabled = true;
    reviewTextInput.classList.add('disabled');

    try {
        // Make API call
        const formData = new FormData();
        
        if (reviewImage) {
            // Send actual image
            formData.append('image', reviewImage);
        } else {
            // Create text-based image from review
            const canvas = document.createElement('canvas');
            canvas.width = 800;
            canvas.height = 600;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, 800, 600);
            ctx.fillStyle = 'black';
            ctx.font = '16px Arial';
            const lines = reviewText.split('\n');
            let y = 30;
            lines.forEach(line => {
                if (line) ctx.fillText(line, 20, y);
                y += 30;
            });
            canvas.toBlob(blob => {
                formData.append('image', blob, 'review_text.png');
            });
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const result = await response.json();
        console.log('API Response:', result);
        
        // Show alert with results
        alert(`Trust Score: ${result.trustScore}%\nVerdict: ${result.verdict}\nSummary: ${result.summary}`);
    } catch (err) {
        console.error('API Error:', err);
        alert('Failed to analyze: ' + err.message);
    } finally {
        // Exit loading state
        isLoading = false;
        analyzeBtn.classList.remove('loading');
        btnSpinner.style.display = 'none';

        // Re-enable inputs
        reviewTextInput.disabled = false;
        reviewTextInput.classList.remove('disabled');

        updateButtonState();
    }
});
