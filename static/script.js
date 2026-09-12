// Update file name display on upload
function updateFileName(input) {
    const fileName = input.files[0]?.name;
    const display = document.getElementById('file-name-display');
    if (fileName) {
        display.textContent = fileName;
        display.classList.add('text-success');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Sync slider value with display
    const slider = document.getElementById('intensity');
    const valueDisplay = document.getElementById('intensity-val');
    if (slider && valueDisplay) {
        slider.addEventListener('input', () => {
            valueDisplay.textContent = slider.value;
        });
    }
});

// Process audio function for edit page
function processAudio() {
    const intensity = document.getElementById('intensity').value;
    const mode = document.getElementById('mode-value').value;

    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    const fileSizeMb = parseFloat(document.getElementById('file-size').value) || 1;
    const estimatedDurationMs = Math.max(2000, fileSizeMb * 1500);
    const intervalTime = 50;
    const steps = estimatedDurationMs / intervalTime;
    const increment = 100 / steps;

    if (!progressContainer || !progressBar || !progressText) return;

    progressContainer.classList.remove('d-none');
    let progress = 0;

    const interval = setInterval(() => {
        progress += increment;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            progressBar.style.width = '100%';
            progressText.textContent = '100%';
            setTimeout(() => {
                window.location.href = `/process?mode=${mode}&intensity=${intensity}`;
            }, 500);
        } else {
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `${Math.floor(progress)}%`;
        }
    }, intervalTime);
}
