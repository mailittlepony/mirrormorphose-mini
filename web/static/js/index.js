/*
 * index.js
 * Copyright (C) 2025 stantonik <stantonik@stantonik-mba.local>
 *
 * Distributed under terms of the GPLv3 license.
 */

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

// Click to open file dialog
dropZone.addEventListener('click', () => {
    fileInput.click();
});

// File selected via dialog
fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        uploadFile(fileInput.files[0]);
    }
});

// Drag events
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        uploadFile(file);
    } else {
        dropZone.textContent = 'Please upload a valid image (PNG or JPEG).';
    }
});

// Upload function
function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/experience/start', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.text();
        })
        .then(result => {
            dropZone.textContent = 'Upload successful!\nPlease look at the mirror, the experience will begin...';
        })
        .catch(error => {
            console.error('Upload error:', error);
            dropZone.textContent = 'Upload failed.';
        });
}

