// Update file name display and validate size before upload
function updateFileName(input) {
    const file = input.files[0];
    const display = document.getElementById('file-name-display');
    if (!file || !display) return;

    const maxBytes = 480 * 1024 * 1024;
    if (file.size > maxBytes) {
        display.textContent = 'File too large (max 480 MB)';
        display.classList.remove('text-success');
        display.classList.add('text-danger');
        input.value = '';
        return;
    }

    display.textContent = file.name;
    display.classList.add('text-success');
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
