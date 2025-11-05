/**
 * Client Bulk Operations Module
 * Handles bulk editing, selection, and batch operations on clients
 */

import { clientState } from './clients.js';
import { filterClients, loadClients, updateClientStats } from './clients.js';

/**
 * Toggle edit mode for bulk operations
 */
function toggleEditMode() {
    clientState.editModeActive = !clientState.editModeActive;

    const editBtn = document.getElementById('editModeBtn');
    const actionsBar = document.getElementById('editModeActions');
    const clientsTableContainer = document.querySelector('.clients-section');

    if (clientState.editModeActive) {
        editBtn.innerHTML = '<span style="margin-right: 4px;">✓</span> Done';
        editBtn.classList.remove('btn-outline');
        editBtn.classList.add('btn-accent');
        actionsBar.style.display = 'flex';
        if (clientsTableContainer) clientsTableContainer.classList.add('edit-mode');
    } else {
        editBtn.innerHTML = '<span style="margin-right: 4px;">✏️</span> Edit Clients';
        editBtn.classList.remove('btn-accent');
        editBtn.classList.add('btn-outline');
        actionsBar.style.display = 'none';
        if (clientsTableContainer) clientsTableContainer.classList.remove('edit-mode');
        // Uncheck select all
        const selectAll = document.getElementById('selectAllClients');
        if (selectAll) selectAll.checked = false;
    }

    // Re-render clients table with/without checkboxes
    filterClients();
}

/**
 * Toggle select all clients
 */
function toggleSelectAll() {
    const selectAllCheckbox = document.getElementById('selectAllClients');
    const checkboxes = document.querySelectorAll('.client-checkbox');

    checkboxes.forEach(cb => {
        cb.checked = selectAllCheckbox.checked;
    });

    updateSelectedCount();
}

/**
 * Update count of selected clients
 */
function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.client-checkbox:checked');
    const count = checkboxes.length;

    const selectedCountEl = document.getElementById('selectedCount');
    if (selectedCountEl) {
        selectedCountEl.textContent = count + (count === 1 ? ' selected' : ' selected');
    }

    // Enable/disable all bulk action buttons
    const disabled = count === 0;
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const bulkFavoriteBtn = document.getElementById('bulkFavoriteBtn');
    const bulkUnfavoriteBtn = document.getElementById('bulkUnfavoriteBtn');
    const bulkMessageBtn = document.getElementById('bulkMessageBtn');

    if (bulkDeleteBtn) bulkDeleteBtn.disabled = disabled;
    if (bulkFavoriteBtn) bulkFavoriteBtn.disabled = disabled;
    if (bulkUnfavoriteBtn) bulkUnfavoriteBtn.disabled = disabled;
    if (bulkMessageBtn) bulkMessageBtn.disabled = disabled;
}

/**
 * Bulk delete selected clients
 */
async function bulkDeleteClients() {
    const checkboxes = document.querySelectorAll('.client-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.consumerId));

    if (selectedIds.length === 0) return;

    if (!confirm(`Are you sure you want to delete ${selectedIds.length} client(s)? This will remove their profiles and appointment history. This cannot be undone.`)) {
        return;
    }

    try {
        // Delete each client
        for (const consumerId of selectedIds) {
            const response = await fetch(`/professional/clients/${consumerId}?specialist_id=${window.currentSpecialistId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`Failed to delete client ${consumerId}`);
            }

            // Remove from allClients array
            clientState.allClients = clientState.allClients.filter(c => c.consumer_id !== consumerId);
        }

        alert(`Successfully deleted ${selectedIds.length} client(s)`);

        // Refresh display
        updateClientStats();
        filterClients();
        updateSelectedCount();

    } catch (error) {
        console.error('Bulk delete error:', error);
        alert('Failed to delete some clients. Please try again.');
        // Reload to ensure data consistency
        loadClients();
    }
}

/**
 * Bulk favorite selected clients
 */
async function bulkFavorite() {
    const checkboxes = document.querySelectorAll('.client-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.consumerId));

    if (selectedIds.length === 0) return;

    try {
        let successCount = 0;
        for (const consumerId of selectedIds) {
            const url = `/professional/clients/${consumerId}/profile?specialist_id=${window.currentSpecialistId}&is_favorite=true`;
            const response = await fetch(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                successCount++;
                // Update in allClients array
                const client = clientState.allClients.find(c => c.consumer_id === consumerId);
                if (client) client.is_favorite = true;
            }
        }

        alert(`Successfully favorited ${successCount} client(s)`);
        filterClients();
        updateSelectedCount();

    } catch (error) {
        console.error('Bulk favorite error:', error);
        alert('Failed to favorite some clients. Please try again.');
    }
}

/**
 * Bulk unfavorite selected clients
 */
async function bulkUnfavorite() {
    const checkboxes = document.querySelectorAll('.client-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.consumerId));

    if (selectedIds.length === 0) return;

    try {
        let successCount = 0;
        for (const consumerId of selectedIds) {
            const url = `/professional/clients/${consumerId}/profile?specialist_id=${window.currentSpecialistId}&is_favorite=false`;
            const response = await fetch(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                successCount++;
                // Update in allClients array
                const client = clientState.allClients.find(c => c.consumer_id === consumerId);
                if (client) client.is_favorite = false;
            }
        }

        alert(`Successfully unfavorited ${successCount} client(s)`);
        filterClients();
        updateSelectedCount();

    } catch (error) {
        console.error('Bulk unfavorite error:', error);
        alert('Failed to unfavorite some clients. Please try again.');
    }
}

/**
 * Bulk message selected clients
 */
async function bulkMessage() {
    const checkboxes = document.querySelectorAll('.client-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.consumerId));

    if (selectedIds.length === 0) return;

    // Get selected clients data
    const selectedClients = clientState.allClients.filter(c => selectedIds.includes(c.consumer_id));
    const emails = selectedClients.filter(c => c.email).map(c => c.email);
    const phones = selectedClients.filter(c => c.phone).map(c => c.phone);

    let message = `Selected ${selectedIds.length} client(s):\n\n`;
    if (emails.length > 0) {
        message += `📧 Emails (${emails.length}):\n${emails.join(', ')}\n\n`;
    }
    if (phones.length > 0) {
        message += `📱 Phones (${phones.length}):\n${phones.join(', ')}\n\n`;
    }
    message += 'Copy the contact information above to send messages via your preferred method (email client, SMS app, etc.).';

    alert(message);
}

/**
 * Open add client modal
 */
function openAddClientModal() {
    const modal = document.getElementById('addClientModal');
    if (modal) {
        modal.style.display = 'flex';
        // Reset form
        const form = document.getElementById('addClientForm');
        if (form) form.reset();
        const messageDiv = document.getElementById('addClientMessage');
        if (messageDiv) messageDiv.innerHTML = '';
    }
}

/**
 * Close add client modal
 */
function closeAddClientModal() {
    const modal = document.getElementById('addClientModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * Submit new client
 */
async function submitNewClient(event) {
    event.preventDefault();

    const name = document.getElementById('newClientName').value.trim();
    const phone = document.getElementById('newClientPhone').value.trim();
    const email = document.getElementById('newClientEmail').value.trim();

    const messageDiv = document.getElementById('addClientMessage');

    // Validate name
    if (!name) {
        messageDiv.innerHTML = '<div style="color: #ff6b6b; padding: 12px; background: rgba(255, 107, 107, 0.1); border-radius: 8px;">⚠️ Name is required</div>';
        return;
    }

    // Validate phone number - must be exactly 10 digits
    if (!phone) {
        messageDiv.innerHTML = '<div style="color: #ff6b6b; padding: 12px; background: rgba(255, 107, 107, 0.1); border-radius: 8px;">⚠️ Phone number is required</div>';
        return;
    }

    if (!/^\d{10}$/.test(phone)) {
        messageDiv.innerHTML = '<div style="color: #ff6b6b; padding: 12px; background: rgba(255, 107, 107, 0.1); border-radius: 8px;">⚠️ Phone must be exactly 10 digits (no dashes or spaces)<br><small>You entered: "' + phone + '" (' + phone.length + ' characters)</small></div>';
        return;
    }

    // Validate email format if provided
    if (email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            messageDiv.innerHTML = '<div style="color: #ff6b6b; padding: 12px; background: rgba(255, 107, 107, 0.1); border-radius: 8px;">⚠️ Please enter a valid email address<br><small>Example: client@example.com</small></div>';
            return;
        }
    }

    // Check for duplicates in existing client list
    const duplicateByPhone = clientState.allClients.find(client => client.phone === phone);
    if (duplicateByPhone) {
        messageDiv.innerHTML = '<div style="color: #ff6b6b; padding: 12px; background: rgba(255, 107, 107, 0.1); border-radius: 8px;">⚠️ A client with this phone number already exists<br><small><strong>' + duplicateByPhone.name + '</strong> - ' + duplicateByPhone.phone + '</small></div>';
        return;
    }

    if (email) {
        const duplicateByEmail = clientState.allClients.find(client => client.email && client.email.toLowerCase() === email.toLowerCase());
        if (duplicateByEmail) {
            messageDiv.innerHTML = '<div style="color: #ff6b6b; padding: 12px; background: rgba(255, 107, 107, 0.1); border-radius: 8px;">⚠️ A client with this email already exists<br><small><strong>' + duplicateByEmail.name + '</strong> - ' + duplicateByEmail.email + '</small></div>';
            return;
        }
    }

    try {
        // Prepare client data
        const clientData = {
            name: name,
            phone: phone
        };

        // Only include email if provided
        if (email) {
            clientData.email = email;
        }

        const response = await fetch(`/professional/clients?specialist_id=${window.currentSpecialistId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(clientData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            let errorMessage = 'Failed to create client';

            // Parse the error detail to provide more specific feedback
            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    // Pydantic validation errors
                    const errors = errorData.detail.map(err => {
                        const field = err.loc[err.loc.length - 1];
                        return `${field}: ${err.msg}`;
                    }).join('<br>');
                    errorMessage = errors;
                } else {
                    errorMessage = errorData.detail;
                }
            }

            throw new Error(errorMessage);
        }

        const result = await response.json();

        messageDiv.innerHTML = '<div style="color: #4ade80; padding: 12px; background: rgba(74, 222, 128, 0.1); border-radius: 8px;">✓ Client added successfully!</div>';

        // Refresh the clients list
        setTimeout(() => {
            closeAddClientModal();
            loadClients();
        }, 1500);

    } catch (error) {
        console.error('Error adding client:', error);
        messageDiv.innerHTML = `<div style="color: #ff6b6b; padding: 12px; background: rgba(255, 107, 107, 0.1); border-radius: 8px;">⚠️ ${error.message}</div>`;
    }
}

// Export functions
export {
    toggleEditMode,
    toggleSelectAll,
    updateSelectedCount,
    bulkDeleteClients,
    bulkFavorite,
    bulkUnfavorite,
    bulkMessage,
    openAddClientModal,
    closeAddClientModal,
    submitNewClient
};
