// ==================== WORKPLACE MANAGEMENT MODULE ====================
// Handles Yelp search integration, workplace creation, and workplace management

// Search Yelp for businesses
export async function searchYelpBusinesses() {
    const term = document.getElementById('yelpSearchTerm').value;
    const location = document.getElementById('yelpSearchLocation').value;
    const resultsDiv = document.getElementById('yelpSearchResults');

    if (!term || !location) {
        resultsDiv.innerHTML = '<div class="error">Please enter both search term and location</div>';
        return;
    }

    resultsDiv.innerHTML = '<div class="loading-message">Searching Yelp...</div>';

    try {
        const response = await fetch(`/yelp/search?term=${encodeURIComponent(term)}&location=${encodeURIComponent(location)}`);

        if (!response.ok) {
            throw new Error('Search failed');
        }

        const businesses = await response.json();

        if (businesses.length === 0) {
            resultsDiv.innerHTML = '<div class="info-message">No businesses found. Try different search terms or add a custom workplace below.</div>';
            return;
        }

        let html = '<div class="yelp-results">';
        html += '<h4 style="color: #D4AF37; margin-bottom: 15px;">Search Results</h4>';

        businesses.forEach(business => {
            html += `
                <div class="yelp-business-card" style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <h5 style="color: #D4AF37; margin: 0 0 10px 0;">${business.name}</h5>
                            <p style="color: rgba(255, 255, 255, 0.7); margin: 5px 0;">${business.address}</p>
                            <p style="color: rgba(255, 255, 255, 0.6); margin: 5px 0; font-size: 0.9em;">
                                ${business.phone || 'No phone listed'} • ${business.is_closed ? 'Closed' : 'Open'}
                            </p>
                            ${business.rating ? `<p style="color: #D4AF37; margin: 5px 0;"> ${business.rating} (${business.review_count} reviews)</p>` : ''}
                        </div>
                        <button type="button" class="btn" onclick="addWorkplaceFromYelp('${business.id}')" style="margin-left: 15px;">
                            Add This Place
                        </button>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        resultsDiv.innerHTML = html;

    } catch (error) {
        console.error('Yelp search error:', error);
        resultsDiv.innerHTML = '<div class="error">Search failed. Please try again.</div>';
    }
}

// Add workplace from Yelp business
export async function addWorkplaceFromYelp(yelpBusinessId) {
    if (!window.currentSpecialistId) {
        alert('You must be logged in to add a workplace');
        return;
    }

    const responseDiv = document.getElementById('workplaceResponse');
    responseDiv.innerHTML = '<div class="loading-message">Adding workplace...</div>';

    try {
        const response = await fetch(`/workplaces/from-yelp/${yelpBusinessId}`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add workplace');
        }

        const workplace = await response.json();

        // Now associate the specialist with this workplace
        const assocResponse = await fetch(`/specialists/${window.currentSpecialistId}/workplaces/${workplace.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                role: 'owner',
                is_active: true
            })
        });

        if (!assocResponse.ok) {
            throw new Error('Failed to associate workplace with your account');
        }

        const assocData = await assocResponse.json();

        // Show appropriate message based on whether it was new or already existed
        if (assocData.already_exists) {
            responseDiv.innerHTML = '<div class="info-message">ℹ️ This workplace is already in your list!</div>';
        } else {
            responseDiv.innerHTML = '<div class="success">Workplace added successfully!</div>';
        }

        // Clear search results and reload workplace list
        document.getElementById('yelpSearchResults').innerHTML = '';
        document.getElementById('yelpSearchTerm').value = '';
        document.getElementById('yelpSearchLocation').value = '';

        setTimeout(() => {
            responseDiv.innerHTML = '';
            loadMyWorkplaces();
        }, 2000);

    } catch (error) {
        console.error('Add workplace error:', error);
        responseDiv.innerHTML = `<div class="error">${error.message}</div>`;
    }
}

// Create custom workplace
export async function createCustomWorkplace() {
    if (!window.currentSpecialistId) {
        alert('You must be logged in to add a workplace');
        return;
    }

    const name = document.getElementById('workplaceName').value;
    const address = document.getElementById('workplaceAddress').value;
    const city = document.getElementById('workplaceCity').value;
    const state = document.getElementById('workplaceState').value;
    const zipCode = document.getElementById('workplaceZipCode').value;
    const phone = document.getElementById('workplacePhone').value;
    const description = document.getElementById('workplaceDescription').value;

    if (!name || !address || !city) {
        document.getElementById('workplaceResponse').innerHTML = '<div class="error">Please fill in required fields (Name, Address, City)</div>';
        return;
    }

    const responseDiv = document.getElementById('workplaceResponse');
    responseDiv.innerHTML = '<div class="loading-message">Creating workplace...</div>';

    try {
        // Create the workplace
        const response = await fetch('/workplaces/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                address,
                city,
                state,
                zip_code: zipCode,
                phone,
                description
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create workplace');
        }

        const workplace = await response.json();

        // Associate specialist with workplace
        const assocResponse = await fetch(`/specialists/${window.currentSpecialistId}/workplaces/${workplace.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                role: 'owner',
                is_active: true
            })
        });

        if (!assocResponse.ok) {
            throw new Error('Failed to associate workplace with your account');
        }

        responseDiv.innerHTML = '<div class="success">Workplace created successfully!</div>';

        // Clear form
        document.getElementById('workplaceName').value = '';
        document.getElementById('workplaceAddress').value = '';
        document.getElementById('workplaceCity').value = '';
        document.getElementById('workplaceState').value = '';
        document.getElementById('workplaceZipCode').value = '';
        document.getElementById('workplacePhone').value = '';
        document.getElementById('workplaceDescription').value = '';

        setTimeout(() => {
            responseDiv.innerHTML = '';
            loadMyWorkplaces();
        }, 2000);

    } catch (error) {
        console.error('Create workplace error:', error);
        responseDiv.innerHTML = `<div class="error">${error.message}</div>`;
    }
}

// Load my workplaces
export async function loadMyWorkplaces() {
    if (!window.currentSpecialistId) return;

    const container = document.getElementById('workplacesContainer');
    container.innerHTML = '<div class="loading-message">Loading workplaces...</div>';

    try {
        const response = await fetch(`/specialists/${window.currentSpecialistId}/workplaces`);

        if (!response.ok) {
            throw new Error('Failed to load workplaces');
        }

        const workplaces = await response.json();

        if (workplaces.length === 0) {
            container.innerHTML = `
                <div class="info-message" style="text-align: center; padding: 40px;">
                    <p style="color: rgba(212, 175, 55, 0.8); font-size: 1.1em; margin-bottom: 10px;">
                        No workplaces added yet
                    </p>
                    <p style="color: rgba(255, 255, 255, 0.6);">
                        Search for your business on Yelp or add a custom workplace above
                    </p>
                </div>
            `;
            return;
        }

        let html = '';
        workplaces.forEach(wp => {
            const isYelp = wp.workplace.yelp_business_id ? 'Verified on Yelp' : 'Custom Location';
            html += `
                <div class="workplace-card" style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 12px; padding: 20px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <h4 style="color: #D4AF37; margin: 0 0 10px 0;">${wp.workplace.name}</h4>
                            <p style="color: rgba(255, 255, 255, 0.7); margin: 5px 0;">
                                ${wp.workplace.address}, ${wp.workplace.city}${wp.workplace.state ? ', ' + wp.workplace.state : ''}${wp.workplace.zip_code ? ' ' + wp.workplace.zip_code : ''}
                            </p>
                            ${wp.workplace.phone ? `<p style="color: rgba(255, 255, 255, 0.6); margin: 5px 0;"> ${wp.workplace.phone}</p>` : ''}
                            <p style="color: rgba(212, 175, 55, 0.7); margin: 10px 0 5px 0; font-size: 0.9em;">
                                ${isYelp} • Role: ${wp.role || 'Staff'} • ${wp.is_active ? 'Active' : 'Inactive'}
                            </p>
                            ${wp.workplace.description ? `<p style="color: rgba(255, 255, 255, 0.6); margin: 10px 0 0 0; font-size: 0.9em;">${wp.workplace.description}</p>` : ''}
                        </div>
                        <div style="display: flex; gap: 10px; margin-left: 15px;">
                            <button type="button" class="btn" onclick="toggleWorkplaceStatus(${wp.workplace.id}, ${!wp.is_active})" style="font-size: 0.9em; padding: 8px 16px;">
                                ${wp.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                            <button type="button" class="btn" onclick="removeWorkplace(${wp.workplace.id})" style="background: rgba(220, 53, 69, 0.8); font-size: 0.9em; padding: 8px 16px;">
                                Remove
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

    } catch (error) {
        console.error('Load workplaces error:', error);
        container.innerHTML = '<div class="error">Failed to load workplaces</div>';
    }
}

// Toggle workplace status
export async function toggleWorkplaceStatus(workplaceId, newStatus) {
    if (!window.currentSpecialistId) return;

    try {
        const response = await fetch(`/specialists/${window.currentSpecialistId}/workplaces/${workplaceId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                is_active: newStatus
            })
        });

        if (!response.ok) {
            throw new Error('Failed to update workplace status');
        }

        loadMyWorkplaces();

    } catch (error) {
        console.error('Toggle workplace error:', error);
        alert('Failed to update workplace status');
    }
}

// Remove workplace association
export async function removeWorkplace(workplaceId) {
    if (!window.currentSpecialistId) return;

    if (!confirm('Are you sure you want to remove this workplace? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/specialists/${window.currentSpecialistId}/workplaces/${workplaceId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to remove workplace');
        }

        loadMyWorkplaces();

    } catch (error) {
        console.error('Remove workplace error:', error);
        alert('Failed to remove workplace');
    }
}
