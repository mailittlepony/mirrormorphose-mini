/*
 * index.js
 * Copyright (C) 2025 stantonik <stantonik@stantonik-mba.local>
 *
 * Distributed under terms of the license.
 */

function on_load() {
    const form = document.getElementById('uploadForm');
    const resultDiv = document.getElementById('uploadResult');
    const button = form.querySelector('button');
    const fileInput = form.querySelector('input[type="file"]');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        button.disabled = true;
        resultDiv.textContent = "Uploading...";

        try {
            const response = await fetch('/upload_user_photo', {
                method: 'POST',
                body: formData,
            });

            const text = await response.text();

            if (!response.ok) {
                throw new Error(`Server error ${response.status}: ${text}`);
            }

            resultDiv.textContent = text;
        } catch (error) {
            resultDiv.textContent = 'Upload failed: ' + error.message;
        }
    });

    // Re-enable button only when a new file is selected
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            button.disabled = false;
            resultDiv.innerHTML = '';
        }
    });
}

document.addEventListener("DOMContentLoaded", on_load)
