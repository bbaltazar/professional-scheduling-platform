// ==================== CLIENT MANAGEMENT FUNCTIONS ====================

import { formatPhoneForDisplay } from './utils.js';

// Export state as an object so it can be mutated from other modules
export const clientState = {
    allClients: [],
    currentClientDetail: null,
    editModeActive: false,
    currentSortColumn: 'name',
    currentSortDirection: 'asc'
};

// Load all clients
export async function loadClients(currentSpecialistId) {
    console.log('[CLIENTS] loadClients called with specialist ID:', currentSpecialistId);
    
    if (!currentSpecialistId) {
        console.error('[CLIENTS] No specialist ID provided!');
        return;
    }

    const container = document.getElementById('clientsList');
    console.log('[CLIENTS] Container element:', container);
    renderClientsSkeleton(container);

    try {
        const url = `/professional/clients?specialist_id=${currentSpecialistId}`;
        console.log('[CLIENTS] Fetching from:', url);
        
        const response = await fetch(url);
        console.log('[CLIENTS] Response status:', response.status);
        
        if (!response.ok) throw new Error('Failed to load clients');

        const data = await response.json();
        console.log('[CLIENTS] Received data:', data);
        console.log('[CLIENTS] Number of clients:', data.length);
        
        clientState.allClients = data;
        console.log('[CLIENTS] Set clientState.allClients to:', clientState.allClients);

        // Update stats
        updateClientStats();

        // Apply default sort and display clients
        sortClientsList(clientState.allClients);
        console.log('[CLIENTS] Finished loading and displaying clients');

    } catch (error) {
        console.error('[CLIENTS] Load clients error:', error);
        container.innerHTML = '<div class="error">Failed to load clients</div>';
    }
}

// Display clients
export function displayClients(clients) {
    const container = document.getElementById('clientsList');

    if (clients.length === 0) {
        container.innerHTML = '<div style="text-align: center; color: rgba(212, 175, 55, 0.6); padding: 40px;">No clients yet. Clients will appear here after their first booking.</div>';
        return;
    }

    const checkboxHeader = clientState.editModeActive ? '<th style="width: 40px;"></th>' : '';

    const html = `
        <div class="table-wrapper">
          <table class="clients-table zebra">
            <thead>
                <tr>
                    ${checkboxHeader}
                    <th>Favorite</th>
                    <th class="sortable ${clientState.currentSortColumn === 'name' ? 'sort-' + clientState.currentSortDirection : ''}" onclick="window.sortClients('name')">Name</th>
                    <th class="sortable ${clientState.currentSortColumn === 'email' ? 'sort-' + clientState.currentSortDirection : ''}" onclick="window.sortClients('email')">Email</th>
                    <th class="sortable ${clientState.currentSortColumn === 'phone' ? 'sort-' + clientState.currentSortDirection : ''}" onclick="window.sortClients('phone')">Phone</th>
                    <th class="sortable ${clientState.currentSortColumn === 'total_bookings' ? 'sort-' + clientState.currentSortDirection : ''}" onclick="window.sortClients('total_bookings')">Visits</th>
                    <th class="sortable ${clientState.currentSortColumn === 'last_booking_date' ? 'sort-' + clientState.currentSortDirection : ''}" onclick="window.sortClients('last_booking_date')">Last Visit</th>
                    <th class="sortable ${clientState.currentSortColumn === 'next_booking_date' ? 'sort-' + clientState.currentSortDirection : ''}" onclick="window.sortClients('next_booking_date')">Next Visit</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${clients.map(client => {
        const lastBooking = client.last_booking_date ? new Date(client.last_booking_date).toLocaleDateString() : 'Never';
        const nextBooking = client.next_booking_date ? new Date(client.next_booking_date).toLocaleDateString() : '—';
        const isFavorite = client.is_favorite || false;
        const starIcon = isFavorite ? '⭐' : '☆';
        const starClass = isFavorite ? 'favorite-active' : 'favorite-inactive';

        const phoneDisplay = formatPhoneForDisplay(client.phone);
        const hasPhoneIssue = typeof phoneDisplay === 'object' && phoneDisplay.isInvalid;
        const phoneText = hasPhoneIssue ? phoneDisplay.formatted : phoneDisplay;
        const phoneError = hasPhoneIssue ? phoneDisplay.error : null;

        const problemRowClass = hasPhoneIssue ? 'problem-row' : '';
        const phoneWarning = hasPhoneIssue ? ` <span class="tag tag-danger" style="margin-left:6px;" title="${phoneError}">Invalid</span>` : '';

        const checkboxCell = clientState.editModeActive ? `<td><input type="checkbox" class="client-checkbox" data-consumer-id="${client.consumer_id}" onchange="window.updateSelectedCount()"></td>` : '';
        const rowClick = clientState.editModeActive ? '' : `onclick="window.viewClientDetail(${client.consumer_id})"`;

        return `
                        <tr ${rowClick} class="${problemRowClass}">
                            ${checkboxCell}
                            <td class="favorite-cell" onclick="event.stopPropagation(); window.toggleFavorite(${client.consumer_id}, ${!isFavorite})">
                                <span class="favorite-star ${starClass}">${starIcon}</span>
                            </td>
                            <td class="client-name-cell">${client.name}</td>
                            <td>${client.email || '—'}</td>
                            <td>${phoneText}${phoneWarning}</td>
                            <td>${client.total_bookings}</td>
                            <td>${lastBooking}</td>
                            <td>${nextBooking}</td>
                            <td>
                                ${client.has_profile ? '<span class="client-badge">Profile</span>' : ''}
                            </td>
                        </tr>
                    `;
    }).join('')}
            </tbody>
          </table>
        </div>
    `;

    container.innerHTML = html;

    // Add legend for invalid phone rows if any exist
    const hasProblemRows = container.querySelector('tr.problem-row');
    if (hasProblemRows) {
        const dismissed = localStorage.getItem('dismissInvalidPhoneLegend') === 'true';
        if (!dismissed) {
            const legend = document.createElement('div');
            legend.className = 'muted';
            legend.style.marginTop = '10px';
            legend.innerHTML = '<span class="tag tag-danger" style="margin-right:6px;">Invalid</span> Rows with a red background have invalid phone numbers. <button class="btn btn-outline" style="padding:4px 10px; font-size:0.55rem; letter-spacing:.5px; margin-left:8px;" onclick="window.dismissInvalidLegend(this)">Dismiss</button>';
            container.appendChild(legend);
        }
    }
}

export function dismissInvalidLegend(button) {
    localStorage.setItem('dismissInvalidPhoneLegend', 'true');
    const wrapper = button.closest('div');
    if (wrapper) wrapper.remove();
}

function renderClientsSkeleton(container) {
    const rows = 8;
    const skeletonRows = Array.from({ length: rows }).map(() => `
        <tr>
            <td><div class="skeleton" style="width:22px; height:18px;"></div></td>
            <td><div class="skeleton" style="width:120px; height:14px;"></div></td>
            <td><div class="skeleton" style="width:170px; height:14px;"></div></td>
            <td><div class="skeleton" style="width:120px; height:14px;"></div></td>
            <td><div class="skeleton" style="width:40px; height:14px;"></div></td>
            <td><div class="skeleton" style="width:80px; height:14px;"></div></td>
            <td><div class="skeleton" style="width:80px; height:14px;"></div></td>
            <td><div class="skeleton" style="width:60px; height:14px;"></div></td>
        </tr>
    `).join('');

    container.innerHTML = `
        <div class="table-wrapper">
          <table class="clients-table zebra">
            <thead>
                <tr>
                    <th>Favorite</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Visits</th>
                    <th>Last Visit</th>
                    <th>Next Visit</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>${skeletonRows}</tbody>
          </table>
        </div>`;
}

// Sort clients by column
export function sortClients(column) {
    if (clientState.currentSortColumn === column) {
        clientState.currentSortDirection = clientState.currentSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        clientState.currentSortColumn = column;
        clientState.currentSortDirection = 'asc';
    }

    const searchTerm = document.getElementById('clientSearch').value.toLowerCase();

    let filtered = clientState.allClients.filter(client => {
        const matchesSearch = !searchTerm ||
            client.name.toLowerCase().includes(searchTerm) ||
            (client.email && client.email.toLowerCase().includes(searchTerm)) ||
            (client.phone && client.phone.includes(searchTerm));

        return matchesSearch;
    });

    filtered.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];

        if (aVal === null || aVal === undefined) aVal = '';
        if (bVal === null || bVal === undefined) bVal = '';

        if (column === 'last_booking_date' || column === 'next_booking_date') {
            aVal = aVal ? new Date(aVal).getTime() : 0;
            bVal = bVal ? new Date(bVal).getTime() : 0;
        }

        if (typeof aVal === 'string' && typeof bVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }

        if (aVal < bVal) return clientState.currentSortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return clientState.currentSortDirection === 'asc' ? 1 : -1;
        return 0;
    });

    displayClients(filtered);
}

// Filter clients
export function filterClients() {
    const searchTerm = document.getElementById('clientSearch').value.toLowerCase();

    let filtered = clientState.allClients.filter(client => {
        const matchesSearch = !searchTerm ||
            client.name.toLowerCase().includes(searchTerm) ||
            (client.email && client.email.toLowerCase().includes(searchTerm)) ||
            (client.phone && client.phone.includes(searchTerm));

        return matchesSearch;
    });

    sortClientsList(filtered);
}

function sortClientsList(clients) {
    clients.sort((a, b) => {
        let aVal = a[clientState.currentSortColumn];
        let bVal = b[clientState.currentSortColumn];

        if (aVal === null || aVal === undefined) aVal = '';
        if (bVal === null || bVal === undefined) bVal = '';

        if (clientState.currentSortColumn === 'last_booking_date' || clientState.currentSortColumn === 'next_booking_date') {
            aVal = aVal ? new Date(aVal).getTime() : 0;
            bVal = bVal ? new Date(bVal).getTime() : 0;
        }

        if (typeof aVal === 'string' && typeof bVal === 'string') {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }

        if (aVal < bVal) return clientState.currentSortDirection === 'asc' ? -1 : 1;
        if (aVal > bVal) return clientState.currentSortDirection === 'asc' ? 1 : -1;
        return 0;
    });

    displayClients(clients);
}

export function updateClientStats() {
    document.getElementById('totalClientsCount').textContent = clientState.allClients.length;

    const upcomingCount = clientState.allClients.filter(c => c.next_booking_date).length;
    document.getElementById('upcomingAppointments').textContent = upcomingCount;
}

// Toggle favorite
export async function toggleFavorite(consumerId, isFavorite, currentSpecialistId) {
    if (!currentSpecialistId) return;

    try {
        const url = `/professional/clients/${consumerId}/profile?specialist_id=${currentSpecialistId}&is_favorite=${isFavorite}`;

        const response = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to update favorite status');
        }

        const client = clientState.allClients.find(c => c.consumer_id === consumerId);
        if (client) {
            client.is_favorite = isFavorite;
        }

        filterClients();

    } catch (error) {
        console.error('Toggle favorite error:', error);
        alert('Failed to update favorite status: ' + error.message);
    }
}
