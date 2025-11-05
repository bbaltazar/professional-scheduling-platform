// ========================
// SERVICES MODULE
// Handles service management (create, edit, delete, display)
// ========================

console.log('Loading services.js module...');

import { showResponse } from './utils.js';

// ========================
// SERVICE DISPLAY & MANAGEMENT
// ========================

// Display existing services in the management section
export function displayExistingServices(services) {
    const existingServicesSection = document.getElementById('existingServicesSection');
    const existingServicesList = document.getElementById('existingServicesList');

    if (!existingServicesSection || !existingServicesList) return;

    if (services && services.length > 0) {
        existingServicesSection.style.display = 'block';

        existingServicesList.innerHTML = services.map(service => `
            <div class="existing-service-card" data-service-id="${service.id}">
                <div class="service-card-header">
                    <h3 class="service-card-title">${service.name}</h3>
                    <div class="service-card-actions">
                        <button class="btn-edit" onclick="editService(${service.id})">
                            ✏️ Edit
                        </button>
                        <button class="btn-delete" onclick="confirmDeleteService(${service.id}, '${service.name}')">
                            🗑️ Delete
                        </button>
                    </div>
                </div>
                
                <div class="service-card-details">
                    <div class="service-detail">
                        <span class="service-detail-icon">💰</span>
                        <span class="service-detail-value">$${service.price}</span>
                    </div>
                    <div class="service-detail">
                        <span class="service-detail-icon">⏱️</span>
                        <span class="service-detail-value">${service.duration} minutes</span>
                    </div>
                </div>
                
                <div class="service-edit-form" id="edit-form-${service.id}">
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Service Name</label>
                            <input type="text" id="edit-name-${service.id}" value="${service.name}">
                        </div>
                        <div class="form-group">
                            <label>Price ($)</label>
                            <input type="number" id="edit-price-${service.id}" value="${service.price}" step="0.01">
                        </div>
                        <div class="form-group">
                            <label>Duration (minutes)</label>
                            <input type="number" id="edit-duration-${service.id}" value="${service.duration}">
                        </div>
                    </div>
                    <div class="service-edit-buttons">
                        <button class="btn-cancel" onclick="cancelEdit(${service.id})">Cancel</button>
                        <button class="btn-save" onclick="saveServiceEdit(${service.id})">Save Changes</button>
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        existingServicesSection.style.display = 'none';
    }
}

// Edit service function
export function editService(serviceId) {
    const editForm = document.getElementById(`edit-form-${serviceId}`);
    const serviceCard = document.querySelector(`[data-service-id="${serviceId}"]`);

    if (editForm && serviceCard) {
        // Hide all other edit forms
        document.querySelectorAll('.service-edit-form').forEach(form => {
            form.style.display = 'none';
        });

        // Show this edit form
        editForm.style.display = 'block';
        serviceCard.style.background = 'rgba(212, 175, 55, 0.2)';
    }
}

// Cancel edit function
export function cancelEdit(serviceId) {
    const editForm = document.getElementById(`edit-form-${serviceId}`);
    const serviceCard = document.querySelector(`[data-service-id="${serviceId}"]`);

    if (editForm && serviceCard) {
        editForm.style.display = 'none';
        serviceCard.style.background = 'rgba(212, 175, 55, 0.1)';
    }
}

// Save service edit function
export async function saveServiceEdit(serviceId) {
    const currentSpecialistId = window.currentSpecialistId;

    const name = document.getElementById(`edit-name-${serviceId}`).value;
    const price = parseFloat(document.getElementById(`edit-price-${serviceId}`).value);
    const duration = parseInt(document.getElementById(`edit-duration-${serviceId}`).value);

    if (!name || !price || !duration) {
        showResponse('existingServicesResponse', 'Please fill in all fields', 'error');
        return;
    }

    try {
        // Get current services first
        const currentServices = await getCurrentServices();

        // Update the service in the array
        const updatedServices = currentServices.map(service =>
            service.id === serviceId ? { name, price, duration } : service
        );

        // Send updated services to server
        const response = await fetch(`/specialist/${currentSpecialistId}/services`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedServices)
        });

        if (response.ok) {
            showResponse('existingServicesResponse', '✅ Service updated successfully!', 'success');

            // Refresh the services display
            window.loadExistingData();
        } else {
            const result = await response.json();
            showResponse('existingServicesResponse', `Update failed: ${result.detail}`, 'error');
        }
    } catch (error) {
        showResponse('existingServicesResponse', `Connection error: ${error.message}`, 'error');
    }
}

// Delete service confirmation
export function confirmDeleteService(serviceId, serviceName) {
    if (confirm(`Are you sure you want to delete "${serviceName}"? This action cannot be undone.`)) {
        deleteService(serviceId);
    }
}

// Delete service function
export async function deleteService(serviceId) {
    const currentSpecialistId = window.currentSpecialistId;

    try {
        // Get current services first
        const currentServices = await getCurrentServices();

        // Remove the service from the array
        const updatedServices = currentServices.filter(service => service.id !== serviceId);

        // Send updated services to server
        const response = await fetch(`/specialist/${currentSpecialistId}/services`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedServices)
        });

        if (response.ok) {
            showResponse('existingServicesResponse', '✅ Service deleted successfully!', 'success');

            // Refresh the services display
            window.loadExistingData();
        } else {
            const result = await response.json();
            showResponse('existingServicesResponse', `Delete failed: ${result.detail}`, 'error');
        }
    } catch (error) {
        showResponse('existingServicesResponse', `Connection error: ${error.message}`, 'error');
    }
}

// Helper function to get current services
async function getCurrentServices() {
    const currentSpecialistId = window.currentSpecialistId;

    const response = await fetch(`/specialist/${currentSpecialistId}/services`);
    if (response.ok) {
        return await response.json();
    }
    return [];
}

// Load existing services into the form
export function loadExistingServices(services) {
    const servicesContainer = document.querySelector('#servicesForm .dynamic-list');
    if (!servicesContainer) return;

    // Clear any existing empty items
    servicesContainer.innerHTML = '';

    services.forEach((service, index) => {
        const serviceItem = document.createElement('div');
        serviceItem.className = 'dynamic-item';
        serviceItem.innerHTML = `
            <div class="service-row">
                <input type="text" placeholder="Service Name" class="service-name" value="${service.name}">
                <input type="number" placeholder="Price ($)" step="0.01" class="service-price" value="${service.price}">
                <input type="number" placeholder="Duration (min)" class="service-duration" value="${service.duration}">
                <button type="button" onclick="removeItem(this)" class="remove-btn">Remove</button>
            </div>
        `;
        servicesContainer.appendChild(serviceItem);
    });

    // Show success message
    showResponse('servicesResponse', `✅ Loaded ${services.length} existing services`, 'success');
}

// ========================
// SERVICE CREATION
// ========================

export function addServiceField() {
    const container = document.getElementById('servicesContainer');
    const newService = document.createElement('div');
    newService.className = 'dynamic-item';
    newService.innerHTML = `
        <div class="form-grid">
            <div class="form-group">
                <label>Service Name</label>
                <input type="text" class="service-name" placeholder="Premium Consultation">
            </div>
            <div class="form-group">
                <label>Investment ($)</label>
                <input type="number" class="service-price" placeholder="300.00" step="0.01">
            </div>
            <div class="form-group">
                <label>Duration (minutes)</label>
                <input type="number" class="service-duration" placeholder="45">
            </div>
        </div>
    `;
    container.appendChild(newService);
}

export async function saveServices() {
    const currentSpecialistId = window.currentSpecialistId;

    if (!currentSpecialistId) {
        showResponse('servicesResponse', 'Please establish your profile first', 'error');
        return;
    }

    const serviceItems = document.querySelectorAll('.dynamic-item');
    const newServices = [];

    serviceItems.forEach(item => {
        const nameInput = item.querySelector('.service-name');
        const priceInput = item.querySelector('.service-price');
        const durationInput = item.querySelector('.service-duration');

        if (nameInput && priceInput && durationInput) {
            const name = nameInput.value;
            const price = parseFloat(priceInput.value);
            const duration = parseInt(durationInput.value);

            if (name && price && duration) {
                newServices.push({ name, price, duration });
            }
        }
    });

    if (newServices.length === 0) {
        showResponse('servicesResponse', 'Please add at least one premium service', 'error');
        return;
    }

    try {
        // Get existing services first
        const existingServices = await getCurrentServices();

        // Combine existing services with new services
        const allServices = [...existingServices, ...newServices];

        const response = await fetch(`/specialist/${currentSpecialistId}/services`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(allServices)
        });

        const result = await response.json();
        if (response.ok) {
            showResponse('servicesResponse', `✅ ${newServices.length} new premium services added successfully! Total: ${allServices.length}`, 'success');

            // Refresh the existing services display
            window.loadExistingData();

            // Clear the form
            document.querySelectorAll('.dynamic-item .service-name').forEach(input => input.value = '');
            document.querySelectorAll('.dynamic-item .service-price').forEach(input => input.value = '');
            document.querySelectorAll('.dynamic-item .service-duration').forEach(input => input.value = '');
        } else {
            showResponse('servicesResponse', `Publishing failed: ${result.detail}`, 'error');
        }
    } catch (error) {
        showResponse('servicesResponse', `Connection error: ${error.message}`, 'error');
    }
}

console.log('Services.js module loaded successfully!');
