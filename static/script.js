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
