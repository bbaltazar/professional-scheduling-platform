/**
 * CSV Upload Module
 * Handles CSV file upload and bulk client import
 */

import { loadClients } from './clients.js';

// Track selected CSV file
let selectedCsvFile = null;

/**
 * Open CSV upload modal
 */
function openCsvUploadModal() {
    const modal = document.getElementById('csvUploadModal');
    if (modal) {
        modal.style.display = 'flex';
    }

    // Reset state
    selectedCsvFile = null;

    const fileInput = document.getElementById('csvFileInput');
    if (fileInput) fileInput.value = '';

    const fileName = document.getElementById('selectedFileName');
    if (fileName) fileName.textContent = '';

    const uploadMessage = document.getElementById('uploadMessage');
    if (uploadMessage) uploadMessage.innerHTML = '';

    const uploadBtn = document.getElementById('uploadCsvBtn');
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.style.opacity = '0.5';
        uploadBtn.style.cursor = 'not-allowed';
    }

    const uploadProgress = document.getElementById('uploadProgress');
    if (uploadProgress) uploadProgress.style.display = 'none';
}

/**
 * Close CSV upload modal
 */
function closeCsvUploadModal() {
    const modal = document.getElementById('csvUploadModal');
    if (modal) {
        modal.style.display = 'none';
    }
    selectedCsvFile = null;
}

/**
 * Handle CSV file selection
 */
function handleCsvFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
        alert('Please select a CSV file');
        event.target.value = '';
        return;
    }

    selectedCsvFile = file;

    const fileName = document.getElementById('selectedFileName');
    if (fileName) {
        fileName.textContent = `Selected: ${file.name}`;
    }

    // Enable upload button
    const uploadBtn = document.getElementById('uploadCsvBtn');
    if (uploadBtn) {
        uploadBtn.disabled = false;
        uploadBtn.style.opacity = '1';
        uploadBtn.style.cursor = 'pointer';
    }
}

/**
 * Upload CSV file
 */
async function uploadCsvFile() {
    if (!selectedCsvFile || !window.currentSpecialistId) return;

    const uploadBtn = document.getElementById('uploadCsvBtn');
    const messageDiv = document.getElementById('uploadMessage');
    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('uploadProgressBar');

    // Disable button
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.style.opacity = '0.5';
        uploadBtn.textContent = 'Uploading...';
    }

    if (messageDiv) messageDiv.innerHTML = '';
    if (progressDiv) progressDiv.style.display = 'block';
    if (progressBar) progressBar.style.width = '30%';

    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', selectedCsvFile);

        // Upload
        const response = await fetch(`/professional/clients/upload-csv?specialist_id=${window.currentSpecialistId}`, {
            method: 'POST',
            body: formData
        });

        if (progressBar) progressBar.style.width = '70%';

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
        }

        const result = await response.json();
        if (progressBar) progressBar.style.width = '100%';

        // Show success message
        let message = `<div style="background: rgba(74, 222, 128, 0.1); padding: 15px; border-radius: 8px; border: 1px solid rgba(74, 222, 128, 0.3);">
            <p style="color: #4ade80; font-weight: 600; margin-bottom: 10px;">Upload Successful!</p>
            <ul style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem; margin-left: 20px;">
                <li>${result.created} clients added</li>
                <li>${result.skipped} duplicates skipped</li>
                <li>${result.total_rows} total rows processed</li>
            </ul>`;

        if (result.errors && result.errors.length > 0) {
            message += `<p style="color: #fbbf24; margin-top: 10px; font-size: 0.9rem;">⚠ ${result.errors.length} rows had errors</p>
            <ul style="color: rgba(255, 255, 255, 0.6); font-size: 0.85rem; margin-left: 20px; margin-top: 5px;">`;
            result.errors.forEach(error => {
                message += `<li>${error}</li>`;
            });
            message += `</ul>`;
        }

        message += `</div>`;
        if (messageDiv) messageDiv.innerHTML = message;

        // Reload clients after a short delay
        setTimeout(async () => {
            await loadClients();
            closeCsvUploadModal();
        }, 2000);

    } catch (error) {
        console.error('CSV upload error:', error);

        if (progressBar) progressBar.style.width = '0%';

        if (messageDiv) {
            messageDiv.innerHTML = `<div style="background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.3);">
                <p style="color: #ef4444; font-weight: 600;">Upload Failed</p>
                <p style="color: rgba(255, 255, 255, 0.7); font-size: 0.9rem; margin-top: 5px;">${error.message}</p>
            </div>`;
        }

        // Re-enable button
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.style.opacity = '1';
            uploadBtn.textContent = 'Upload Clients';
        }
    }
}

// Export functions
export {
    openCsvUploadModal,
    closeCsvUploadModal,
    handleCsvFileSelect,
    uploadCsvFile
};
