// ==================== CLIENT DETAIL MODAL MODULE ====================
// Handles client detail modal, manual booking, appointment notes, and client history

import { formatTime } from './utils.js';

// View client detail
export async function viewClientDetail(consumerId) {
    if (!window.currentSpecialistId) return;

    try {
        const response = await fetch(`/professional/clients/${consumerId}?specialist_id=${window.currentSpecialistId}`);
        if (!response.ok) throw new Error('Failed to load client details');

        const clientData = await response.json();
        console.log('[CLIENT-DETAIL] Received client data:', clientData);

        // Use clientState directly instead of window.clientState.currentClientDetail
        window.clientState.currentClientDetail = clientData;
        console.log('[CLIENT-DETAIL] Set clientState.currentClientDetail');

        showClientModal();

    } catch (error) {
        console.error('Load client detail error:', error);
        alert('Failed to load client details');
    }
}

// Show client modal
function showClientModal() {
    const modal = document.getElementById('clientModal');
    const client = window.clientState.currentClientDetail;

    console.log('[CLIENT-DETAIL] showClientModal - client:', client);

    if (!client) {
        console.error('[CLIENT-DETAIL] currentClientDetail is null!');
        alert('Failed to load client data');
        return;
    }

    // Set header info
    document.getElementById('modalClientName').textContent = client.consumer.name;

    // Populate contact form fields
    document.getElementById('clientName').value = client.consumer.name || '';
    document.getElementById('clientEmail').value = client.consumer.email || '';
    document.getElementById('clientPhone').value = client.consumer.phone || '';

    document.getElementById('modalClientSince').textContent = client.first_booking_date ?
        new Date(client.first_booking_date).toLocaleDateString() : 'Unknown';
    document.getElementById('modalClientRevenue').textContent = `$${client.total_revenue.toFixed(2)}`;

    // Set profile data
    if (client.profile) {
        document.getElementById('modalClientBio').value = client.profile.bio || '';

        // Display appointment notes
        displayAppointmentNotes(client.profile.notes || []);
    } else {
        document.getElementById('modalClientBio').value = '';
        displayAppointmentNotes([]);
    }

    // Display bookings
    displayModalBookings(client.bookings_future, 'modalFutureBookings');
    displayModalBookings(client.bookings_past, 'modalPastBookings');

    // Display service statistics
    displayServiceStatistics(client);

    // Load changelog history
    loadClientChangelog();

    // Load services for manual booking
    loadServicesForManualBooking();

    // Set minimum date to today for manual booking
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('manualBookingDate').min = today;

    modal.style.display = 'block';
}

// Load services for manual booking dropdown
async function loadServicesForManualBooking() {
    if (!window.currentSpecialistId) return;

    try {
        const response = await fetch(`/specialist/${window.currentSpecialistId}/services`);
        if (!response.ok) throw new Error('Failed to load services');

        const services = await response.json();
        const select = document.getElementById('manualBookingService');

        select.innerHTML = '<option value="">Select a service...</option>' +
            services.map(service =>
                `<option value="${service.id}" data-price="${service.price}" data-duration="${service.duration}">
                    ${service.name} - $${service.price} (${service.duration} min)
                </option>`
            ).join('');
    } catch (error) {
        console.error('Failed to load services:', error);
    }
}

// Display service statistics with inline bar chart
function displayServiceStatistics(client) {
    const container = document.getElementById('serviceStatsContent');

    // Combine past and future bookings
    const allBookings = [...(client.bookings_past || []), ...(client.bookings_future || [])];

    if (allBookings.length === 0) {
        container.innerHTML = '<div style="color: var(--color-text-tertiary); text-align: center; padding: 20px;">No service history yet</div>';
        return;
    }

    // Aggregate services
    const serviceStats = {};
    allBookings.forEach(booking => {
        const serviceName = booking.service_name || 'Unknown Service';
        if (!serviceStats[serviceName]) {
            serviceStats[serviceName] = {
                count: 0,
                revenue: 0
            };
        }
        serviceStats[serviceName].count++;
        serviceStats[serviceName].revenue += booking.service_price || 0;
    });

    // Sort by count (most popular first)
    const sortedServices = Object.entries(serviceStats)
        .sort((a, b) => b[1].count - a[1].count);

    const maxCount = sortedServices[0][1].count;

    // Build HTML with inline bar chart
    let html = '<div style="display: flex; flex-direction: column; gap: 14px;">';

    sortedServices.forEach(([serviceName, stats]) => {
        const percentage = (stats.count / maxCount) * 100;
        html += `
            <div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: 500; color: var(--color-text-primary);">${serviceName}</span>
                    <span style="color: var(--color-text-secondary); font-size: 0.9rem;">
                        ${stats.count} ${stats.count === 1 ? 'visit' : 'visits'} • $${stats.revenue.toFixed(2)}
                    </span>
                </div>
                <div style="background: rgba(255, 255, 255, 0.05); border-radius: 4px; height: 8px; overflow: hidden;">
                    <div style="
                        background: linear-gradient(90deg, var(--color-accent), var(--color-accent-hover));
                        height: 100%;
                        width: ${percentage}%;
                        transition: width 0.3s ease;
                        border-radius: 4px;
                    "></div>
                </div>
            </div>
        `;
    });

    // Add total summary
    const totalVisits = allBookings.length;
    const totalRevenue = sortedServices.reduce((sum, [_, stats]) => sum + stats.revenue, 0);

    html += `
        </div>
        <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--color-border); display: flex; justify-content: space-between; font-weight: 600;">
            <span style="color: var(--color-accent);">Total Services Rendered</span>
            <span style="color: var(--color-text-primary);">${totalVisits} ${totalVisits === 1 ? 'visit' : 'visits'} • $${totalRevenue.toFixed(2)}</span>
        </div>
    `;

    container.innerHTML = html;
}

// Update service info display
export function updateManualBookingServiceInfo() {
    const select = document.getElementById('manualBookingService');
    const infoDiv = document.getElementById('manualBookingServiceInfo');

    if (select.value) {
        const option = select.options[select.selectedIndex];
        const price = option.getAttribute('data-price');
        const duration = option.getAttribute('data-duration');
        infoDiv.innerHTML = `<span style="color: var(--color-accent);">💰 $${price}</span> • <span style="color: var(--color-text-secondary);">⏱️ ${duration} minutes</span>`;

        // Reset date and time when service changes
        document.getElementById('manualBookingDate').value = '';
        document.getElementById('manualBookingTime').innerHTML = '<option value="">Select date first...</option>';
        document.getElementById('manualBookingTime').disabled = true;
    } else {
        infoDiv.innerHTML = '';
    }
}

// Load available time slots for manual booking
export async function loadManualBookingTimeSlots() {
    const serviceId = document.getElementById('manualBookingService').value;
    const date = document.getElementById('manualBookingDate').value;
    const timeSelect = document.getElementById('manualBookingTime');
    const helpText = document.getElementById('manualBookingTimeHelp');

    // Clear alternative dates container on new load
    const existingContainer = document.getElementById('alternativeDatesContainer');
    if (existingContainer) {
        existingContainer.remove();
    }

    if (!serviceId || !date) {
        timeSelect.disabled = true;
        return;
    }

    timeSelect.innerHTML = '<option value="">Loading...</option>';
    timeSelect.disabled = true;
    helpText.textContent = 'Loading available time slots...';

    try {
        // Use the correct endpoint: /specialist/{id}/availability/{date}?service_id={id}
        const response = await fetch(`/specialist/${window.currentSpecialistId}/availability/${date}?service_id=${serviceId}`);
        if (!response.ok) throw new Error('Failed to load availability');

        const data = await response.json();

        // The API returns an array of slot objects with start_time and end_time
        if (data && data.length > 0) {
            timeSelect.innerHTML = '<option value="">Select a time...</option>' +
                data.map(slot => {
                    // slot.start_time and slot.end_time are time strings like "14:00:00"
                    const startTime = slot.start_time;
                    const endTime = slot.end_time;
                    return `<option value="${startTime}">${formatTime(startTime)} - ${formatTime(endTime)}</option>`;
                }).join('');
            timeSelect.disabled = false;
            helpText.innerHTML = `<span style="color: var(--color-accent);">${data.length} slots available</span>`;
        } else {
            // No slots available for this date - find closest previous and next available dates
            timeSelect.innerHTML = '<option value="">No slots available</option>';
            helpText.innerHTML = '<span style="color: #dc2626;">No available time slots for this date</span>';

            // Add alternative date suggestions
            showAlternativeDateSlots(serviceId, date).catch(err => {
                console.error('Error showing alternative dates:', err);
            });
        }
    } catch (error) {
        console.error('Failed to load time slots:', error);
        timeSelect.innerHTML = '<option value="">Error loading slots</option>';
        helpText.innerHTML = '<span style="color: #dc2626;">Failed to load availability</span>';
    }
}

// Show alternative date slots when selected date has no availability
async function showAlternativeDateSlots(serviceId, selectedDate) {
    console.log('Looking for alternative dates for:', selectedDate, 'service:', serviceId);
    const helpText = document.getElementById('manualBookingTimeHelp');

    // Create container for alternative dates
    let alternativesContainer = document.getElementById('alternativeDatesContainer');
    if (!alternativesContainer) {
        alternativesContainer = document.createElement('div');
        alternativesContainer.id = 'alternativeDatesContainer';
        alternativesContainer.style.marginTop = '15px';
        helpText.parentNode.insertBefore(alternativesContainer, helpText.nextSibling);
    }

    alternativesContainer.innerHTML = '<div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">Finding nearby available dates...</div>';

    const today = new Date().toISOString().split('T')[0];
    const selected = new Date(selectedDate);

    let closestPrevious = null;
    let closestNext = null;

    // Search up to 14 days before and after
    const searchRange = 14;

    console.log('Searching for previous dates...');
    // Search for previous available date (not in the past)
    for (let i = 1; i <= searchRange; i++) {
        const checkDate = new Date(selected);
        checkDate.setDate(checkDate.getDate() - i);
        const dateStr = checkDate.toISOString().split('T')[0];

        // Skip if in the past
        if (dateStr < today) {
            console.log('Skipping past date:', dateStr);
            continue;
        }

        try {
            console.log('Checking previous date:', dateStr);
            const resp = await fetch(`/specialist/${window.currentSpecialistId}/availability/${dateStr}?service_id=${serviceId}`);
            if (resp.ok) {
                const slots = await resp.json();
                console.log('  -> Response for', dateStr, ':', slots.length, 'slots available');
                if (slots && slots.length > 0) {
                    closestPrevious = { date: dateStr, slots: slots };
                    console.log('✓ Found previous date:', dateStr, 'with', slots.length, 'slots - STOPPING SEARCH');
                    break;
                } else {
                    console.log('  -> No slots on', dateStr, '- continuing search');
                }
            } else {
                console.log('  -> Failed to fetch for', dateStr, '- status:', resp.status);
            }
        } catch (e) {
            console.error('Error checking date:', dateStr, e);
        }
    }

    console.log('Searching for next dates...');
    // Search for next available date
    for (let i = 1; i <= searchRange; i++) {
        const checkDate = new Date(selected);
        checkDate.setDate(checkDate.getDate() + i);
        const dateStr = checkDate.toISOString().split('T')[0];

        try {
            const resp = await fetch(`/specialist/${window.currentSpecialistId}/availability/${dateStr}?service_id=${serviceId}`);
            if (resp.ok) {
                const slots = await resp.json();
                if (slots && slots.length > 0) {
                    closestNext = { date: dateStr, slots: slots };
                    console.log('Found next date:', dateStr, 'with', slots.length, 'slots');
                    break;
                }
            }
        } catch (e) {
            console.error('Error checking date:', dateStr, e);
        }
    }

    console.log('Alternative dates found - Previous:', closestPrevious, 'Next:', closestNext);

    // Display alternative dates
    if (closestPrevious || closestNext) {
        let html = '<div style="padding: 15px; background: rgba(212, 175, 55, 0.05); border-radius: 8px; border: 1px solid rgba(212, 175, 55, 0.2);">';
        html += '<div style="color: var(--color-accent); font-weight: 500; margin-bottom: 10px;">📅 Nearby Available Dates:</div>';
        html += '<div style="display: flex; gap: 10px; flex-wrap: wrap;">';

        if (closestPrevious) {
            const formattedDate = new Date(closestPrevious.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
            html += `<button type="button" onclick="selectAlternativeDate('${closestPrevious.date}')" 
                style="padding: 8px 16px; background: linear-gradient(135deg, #D4AF37 0%, #F7E7AD 100%); border: none; border-radius: 20px; color: #1a1a1a; font-weight: 500; cursor: pointer; font-size: 0.9rem; transition: transform 0.2s;" 
                onmouseover="this.style.transform='scale(1.05)'" 
                onmouseout="this.style.transform='scale(1)'">
                ← ${formattedDate} (${closestPrevious.slots.length} slots)
            </button>`;
        }

        if (closestNext) {
            const formattedDate = new Date(closestNext.date + 'T12:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
            html += `<button type="button" onclick="selectAlternativeDate('${closestNext.date}')" 
                style="padding: 8px 16px; background: linear-gradient(135deg, #D4AF37 0%, #F7E7AD 100%); border: none; border-radius: 20px; color: #1a1a1a; font-weight: 500; cursor: pointer; font-size: 0.9rem; transition: transform 0.2s;" 
                onmouseover="this.style.transform='scale(1.05)'" 
                onmouseout="this.style.transform='scale(1)'">
                ${formattedDate} → (${closestNext.slots.length} slots)
            </button>`;
        }

        html += '</div></div>';
        alternativesContainer.innerHTML = html;
    } else {
        alternativesContainer.innerHTML = '<div style="color: rgba(255, 107, 107, 0.8); font-size: 0.9rem; margin-top: 10px;">⚠️ No available dates found within the next 2 weeks</div>';
    }
}

// Select an alternative date
export function selectAlternativeDate(date) {
    document.getElementById('manualBookingDate').value = date;
    loadManualBookingTimeSlots();
}

// Submit manual booking
export async function submitManualBooking() {
    const form = document.getElementById('manualBookingForm');
    const responseDiv = document.getElementById('manualBookingResponse');

    // Get form values
    const serviceId = document.getElementById('manualBookingService').value;
    const date = document.getElementById('manualBookingDate').value;
    const startTime = document.getElementById('manualBookingTime').value;
    const notes = document.getElementById('manualBookingNotes').value;

    // Validate required fields
    if (!serviceId || !date || !startTime) {
        responseDiv.style.display = 'block';
        responseDiv.className = 'error';
        responseDiv.textContent = 'Please fill in all required fields (Service, Date, and Time)';
        return;
    }

    if (!window.clientState.currentClientDetail || !window.clientState.currentClientDetail.consumer) {
        responseDiv.style.display = 'block';
        responseDiv.className = 'error';
        responseDiv.textContent = 'Client information not found';
        return;
    }

    // Prepare booking data - match BookingCreate model fields exactly
    const bookingData = {
        specialist_id: window.currentSpecialistId,
        service_id: parseInt(serviceId),
        booking_date: date,  // Note: API expects 'booking_date' not 'date'
        start_time: startTime,
        client_name: window.clientState.currentClientDetail.consumer.name,
        client_email: window.clientState.currentClientDetail.consumer.email || '',
        client_phone: window.clientState.currentClientDetail.consumer.phone || null,
        notes: notes || null,
        source_workplace_id: null
    };

    console.log('Submitting booking data:', bookingData);

    try {
        responseDiv.style.display = 'block';
        responseDiv.className = 'response';
        responseDiv.textContent = 'Creating booking...';

        const response = await fetch('/booking/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bookingData)
        });

        if (response.ok) {
            const booking = await response.json();
            responseDiv.className = 'response success';
            responseDiv.textContent = `✅ Booking created successfully! Appointment scheduled for ${new Date(date).toLocaleDateString()} at ${formatTime(startTime)}`;

            // Reset form
            form.reset();
            document.getElementById('manualBookingServiceInfo').innerHTML = '';
            document.getElementById('manualBookingTime').innerHTML = '<option value="">Select date first...</option>';
            document.getElementById('manualBookingTime').disabled = true;

            // Reload client details to show new booking
            setTimeout(() => {
                viewClientDetail(window.clientState.currentClientDetail.consumer.id);
            }, 1500);
        } else {
            const error = await response.json();
            responseDiv.className = 'response error';
            responseDiv.textContent = `❌ Failed to create booking: ${error.detail || 'Unknown error'}`;
        }
    } catch (error) {
        console.error('Error creating booking:', error);
        responseDiv.className = 'response error';
        responseDiv.textContent = `❌ Connection error: ${error.message}`;
    }
}

// Close client modal
export function closeClientModal() {
    document.getElementById('clientModal').style.display = 'none';
    window.clientState.currentClientDetail = null;
}

// Display appointment notes
function displayAppointmentNotes(notes) {
    const container = document.getElementById('appointmentNotesList');

    if (!notes || notes.length === 0) {
        container.innerHTML = '<div style="color: rgba(212, 175, 55, 0.6); padding: 20px; text-align: center;">No notes yet</div>';
        return;
    }

    const html = notes.map(note => `
        <div class="appointment-note">
            <div class="appointment-note-date">${new Date(note.date).toLocaleDateString()} ${new Date(note.date).toLocaleTimeString()}</div>
            <div class="appointment-note-text">${note.note}</div>
        </div>
    `).join('');

    container.innerHTML = html;
}

// Display modal bookings
function displayModalBookings(bookings, containerId) {
    const container = document.getElementById(containerId);

    if (!bookings || bookings.length === 0) {
        container.innerHTML = `<div style="color: rgba(212, 175, 55, 0.6); padding: 20px; text-align: center;">
            ${containerId === 'modalFutureBookings' ? 'No upcoming appointments' : 'No past appointments'}
        </div>`;
        return;
    }

    const isPastBookings = containerId === 'modalPastBookings';

    const html = bookings.map(booking => `
        <div class="booking-card ${isPastBookings ? 'past-appointment-card' : ''}" 
             data-booking-id="${booking.id}"
             ${isPastBookings ? 'onclick="toggleAppointmentNoteEditor(' + booking.id + ')" style="cursor: pointer;"' : ''}>
            <div class="booking-card-header">
                <div class="booking-card-date">${new Date(booking.date).toLocaleDateString()}</div>
                <div style="color: rgba(212, 175, 55, 0.7); font-size: 0.9rem;">${booking.status}</div>
            </div>
            <div class="booking-card-details">
                <div>⏰ ${booking.start_time} - ${booking.end_time}</div>
                <div>💼 ${booking.service_name} - $${booking.service_price.toFixed(2)}</div>
                ${booking.notes ? `<div style="margin-top: 8px; padding: 8px; background: rgba(139, 168, 255, 0.08); border-radius: 6px; font-style: italic; font-size: 0.85rem;">
                    <div style="color: var(--color-accent); font-size: 0.7rem; font-weight: 600; margin-bottom: 4px;">CLIENT NOTE:</div>
                    ${booking.notes}
                </div>` : ''}
            </div>
            ${isPastBookings ? `
                <div class="appointment-note-section" id="note-section-${booking.id}" style="display: none; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--color-border-subtle);">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="color: var(--color-accent); font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">📝 Your Notes</span>
                    </div>
                    <div id="note-display-${booking.id}" style="display: ${booking.specialist_notes ? 'block' : 'none'}; padding: 10px; background: rgba(139, 168, 255, 0.05); border-radius: 6px; margin-bottom: 8px; font-size: 0.85rem; line-height: 1.5;">
                        ${booking.specialist_notes || ''}
                    </div>
                    <textarea 
                        id="note-input-${booking.id}" 
                        class="appointment-note-input" 
                        placeholder="Add notes about this appointment..."
                        onclick="event.stopPropagation();"
                        style="width: 100%; min-height: 80px; padding: 10px; background: var(--color-bg-elevated); border: 1px solid var(--color-border-subtle); border-radius: 6px; color: var(--color-text-primary); font-family: var(--font-ui); font-size: 0.85rem; resize: vertical;"
                    >${booking.specialist_notes || ''}</textarea>
                    <div style="display: flex; gap: 8px; margin-top: 8px;">
                        <button class="btn btn-accent" onclick="saveAppointmentNote(${booking.id}); event.stopPropagation();" style="padding: 6px 14px; font-size: 0.8rem;">
                            💾 Save Note
                        </button>
                        <button class="btn btn-outline" onclick="toggleAppointmentNoteEditor(${booking.id}); event.stopPropagation();" style="padding: 6px 14px; font-size: 0.8rem;">
                            Cancel
                        </button>
                    </div>
                </div>
            ` : ''}
        </div>
    `).join('');

    container.innerHTML = html;
}

// Save client profile
export async function saveClientProfile() {
    if (!window.currentSpecialistId || !window.clientState.currentClientDetail) return;

    const bio = document.getElementById('modalClientBio').value;

    // Get existing notes from profile
    const existingNotes = window.clientState.currentClientDetail.profile?.notes || [];

    const messageDiv = document.getElementById('profileSaveMessage');
    messageDiv.textContent = 'Saving...';
    messageDiv.style.color = '#fbbf24';

    try {
        const response = await fetch(`/professional/clients/${window.clientState.currentClientDetail.consumer.id}/profile?specialist_id=${window.currentSpecialistId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bio: bio,
                notes: JSON.stringify(existingNotes)
            })
        });

        if (!response.ok) throw new Error('Failed to save profile');

        const updatedProfile = await response.json();
        window.clientState.currentClientDetail.profile = updatedProfile;

        // Update the client in allClients array
        const clientIndex = window.clientState.allClients.findIndex(c => c.consumer_id === window.clientState.currentClientDetail.consumer.id);
        if (clientIndex !== -1) {
            window.clientState.allClients[clientIndex].has_profile = true;
        }

        // Also update the profile reference in main clients module
        const profileResponse = await fetch(
            `/professional/clients/${window.clientState.currentClientDetail.consumer.id}/profile?specialist_id=${window.currentSpecialistId}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bio: bio || null })
            }
        );

        if (!profileResponse.ok) {
            throw new Error('Failed to save profile');
        }

        // Success!
        messageDiv.textContent = '✅ Saved successfully!';
        messageDiv.style.color = 'var(--color-success)';

        // Close modal after brief delay
        setTimeout(() => {
            closeClientModal();
            // Reload client list in background
            window.loadClients().catch(err => console.error('Failed to reload clients:', err));
        }, 1000);

    } catch (error) {
        console.error('Save error:', error);
        messageDiv.textContent = `❌ ${error.message}`;
        messageDiv.style.color = 'var(--color-danger)';
    }
}

// Add appointment note
export async function addAppointmentNote() {
    if (!window.currentSpecialistId || !window.clientState.currentClientDetail) return;

    const noteText = document.getElementById('newAppointmentNote').value.trim();
    if (!noteText) {
        alert('Please enter a note');
        return;
    }

    // Get existing notes
    const existingNotes = window.clientState.currentClientDetail.profile?.notes || [];

    // Add new note
    const newNote = {
        date: new Date().toISOString(),
        note: noteText
    };
    existingNotes.push(newNote);

    // Save profile with new note
    const bio = document.getElementById('modalClientBio').value;

    try {
        const response = await fetch(`/professional/clients/${window.clientState.currentClientDetail.consumer.id}/profile?specialist_id=${window.currentSpecialistId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bio: bio,
                notes: JSON.stringify(existingNotes)
            })
        });

        if (!response.ok) throw new Error('Failed to add note');

        const updatedProfile = await response.json();
        window.clientState.currentClientDetail.profile = updatedProfile;

        // Update the client in allClients array
        const clientIndex = window.clientState.allClients.findIndex(c => c.consumer_id === window.clientState.currentClientDetail.consumer.id);
        if (clientIndex !== -1) {
            window.clientState.allClients[clientIndex].has_profile = true;
        }

        // Clear input and refresh notes display
        document.getElementById('newAppointmentNote').value = '';
        displayAppointmentNotes(updatedProfile.notes);

        // Update table display
        window.filterClients();

    } catch (error) {
        console.error('Add note error:', error);
        alert('Failed to add note');
    }
}

// Toggle appointment note editor
export function toggleAppointmentNoteEditor(bookingId) {
    const noteSection = document.getElementById(`note-section-${bookingId}`);
    const noteInput = document.getElementById(`note-input-${bookingId}`);

    if (noteSection.style.display === 'none' || noteSection.style.display === '') {
        noteSection.style.display = 'block';
        // Focus on textarea after a brief delay to ensure it's visible
        setTimeout(() => noteInput.focus(), 100);
    } else {
        noteSection.style.display = 'none';
    }
}

// Save appointment-specific note
export async function saveAppointmentNote(bookingId) {
    if (!window.currentSpecialistId) return;

    const noteInput = document.getElementById(`note-input-${bookingId}`);
    const noteText = noteInput.value.trim();

    try {
        // Call backend API to save note for this specific booking
        const response = await fetch(`/professional/bookings/${bookingId}/note?specialist_id=${window.currentSpecialistId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ note: noteText })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to save note');
        }

        const result = await response.json();

        // Update the display
        const noteDisplay = document.getElementById(`note-display-${bookingId}`);
        if (noteText) {
            noteDisplay.textContent = noteText;
            noteDisplay.style.display = 'block';
        } else {
            noteDisplay.style.display = 'none';
        }

        // Update the booking in currentClientDetail if it exists
        if (window.clientState.currentClientDetail && window.clientState.currentClientDetail.bookings) {
            const booking = window.clientState.currentClientDetail.bookings.find(b => b.id === bookingId);
            if (booking) {
                booking.specialist_notes = noteText;
            }
        }

        // Close the editor
        toggleAppointmentNoteEditor(bookingId);

        // Show success message briefly
        const noteSection = document.getElementById(`note-section-${bookingId}`);
        const successMsg = document.createElement('div');
        successMsg.className = 'tag tag-success';
        successMsg.textContent = '✓ Saved';
        successMsg.style.marginTop = '8px';
        noteSection.appendChild(successMsg);
        setTimeout(() => successMsg.remove(), 2000);

    } catch (error) {
        console.error('Save appointment note error:', error);
        alert('Failed to save note: ' + error.message);
    }
}

// Load client changelog
async function loadClientChangelog() {
    if (!window.clientState.currentClientDetail || !window.currentSpecialistId) return;

    try {
        const response = await fetch(`/professional/clients/${window.clientState.currentClientDetail.consumer.id}/changelog?specialist_id=${window.currentSpecialistId}&limit=20`);

        if (!response.ok) {
            console.error('Failed to load changelog');
            return;
        }

        const data = await response.json();

        // Show/hide the section based on whether there's history
        const section = document.getElementById('changelogSection');
        const listDiv = document.getElementById('changelogList');

        if (data.total_changes === 0) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';

        // Build the changelog HTML
        let html = '';
        data.history.forEach(entry => {
            const date = new Date(entry.changed_at);
            const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });

            const fieldLabel = {
                'name': 'Name',
                'email': 'Email',
                'phone': 'Phone'
            }[entry.field_changed] || entry.field_changed;

            html += `
                <div style="padding: 12px; background: var(--color-bg-secondary); border-radius: 8px; margin-bottom: 8px; border-left: 3px solid var(--color-accent);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 6px;">
                        <span style="font-weight: 600; color: var(--color-accent); font-size: 0.85rem;">${fieldLabel} Updated</span>
                        <span class="muted" style="font-size: 0.7rem;">${dateStr} at ${timeStr}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--color-text-secondary);">
                        <div style="margin-bottom: 4px;">
                            <span class="muted">From:</span> 
                            <span style="text-decoration: line-through; opacity: 0.7;">${entry.old_value || '(empty)'}</span>
                        </div>
                        <div>
                            <span class="muted">To:</span> 
                            <span style="color: var(--color-success); font-weight: 500;">${entry.new_value || '(empty)'}</span>
                        </div>
                    </div>
                </div>
            `;
        });

        listDiv.innerHTML = html;

    } catch (error) {
        console.error('Error loading changelog:', error);
    }
}

export function toggleChangelog() {
    const section = document.getElementById('changelogSection');
    section.style.display = section.style.display === 'none' ? 'block' : 'none';
}

// Delete client functions
export function confirmDeleteClient() {
    if (!window.clientState.currentClientDetail) return;

    const modal = document.getElementById('deleteConfirmModal');
    const nameElement = document.getElementById('deleteClientName');
    nameElement.textContent = window.clientState.currentClientDetail.consumer.name;
    modal.style.display = 'flex';
}

export function closeDeleteConfirmModal() {
    const modal = document.getElementById('deleteConfirmModal');
    modal.style.display = 'none';
    document.getElementById('deleteMessage').textContent = '';
}

export async function deleteClient() {
    if (!window.currentSpecialistId || !window.clientState.currentClientDetail) return;

    const messageDiv = document.getElementById('deleteMessage');
    messageDiv.textContent = 'Deleting...';
    messageDiv.style.color = '#fbbf24';

    try {
        const response = await fetch(`/professional/clients/${window.clientState.currentClientDetail.consumer.id}?specialist_id=${window.currentSpecialistId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete client');
        }

        messageDiv.textContent = 'Client deleted successfully!';
        messageDiv.style.color = '#4ade80';

        // Remove client from allClients array
        const deletedConsumerId = window.clientState.currentClientDetail.consumer.id;
        window.clientState.allClients = window.clientState.allClients.filter(c => c.consumer_id !== deletedConsumerId);

        // Close both modals after a short delay
        setTimeout(() => {
            closeDeleteConfirmModal();
            closeClientModal();

            // Update display
            window.filterClients();
            window.updateClientStats();
        }, 1500);

    } catch (error) {
        console.error('Delete client error:', error);
        messageDiv.textContent = `${error.message}`;
        messageDiv.style.color = '#ef4444';
    }
}
