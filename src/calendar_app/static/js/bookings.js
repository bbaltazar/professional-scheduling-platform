// ==================== BOOKING MANAGEMENT ====================
// All booking-related functionality for professionals

import { formatTime, showResponse } from './utils.js';

// Store active timers
const activeTimers = {};

// Store pending completion data for the modal
let pendingCompletion = null;

// ========================
// BOOKING LIST MANAGEMENT
// ========================

export async function loadBookings() {
    const currentSpecialistId = window.currentSpecialistId;

    if (!currentSpecialistId) {
        document.getElementById('bookingsList').innerHTML =
            '<div class="no-bookings-message">Please log in to view your bookings.</div>';
        return;
    }

    try {
        showBookingsLoading();

        // Add cache busting parameter and headers to force fresh data
        const cacheBuster = `?_=${Date.now()}`;
        const response = await fetch(`/bookings/specialist/${currentSpecialistId}${cacheBuster}`, {
            cache: 'no-store',
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const bookings = await response.json();
        displayBookings(bookings);

    } catch (error) {
        console.error('Error loading bookings:', error);
        document.getElementById('bookingsList').innerHTML =
            '<div class="no-bookings-message">Failed to load bookings. Please try refreshing.</div>';
        showResponse('bookingsResponse', `Error loading bookings: ${error.message}`, 'error');
    }
}

// Helper function to format duration from timestamps
function formatDuration(startTime, endTime) {
    // Parse UTC times correctly
    let start, end;
    if (startTime.includes('Z') || startTime.includes('+')) {
        start = new Date(startTime);
    } else {
        start = new Date(startTime + 'Z');
    }
    if (endTime.includes('Z') || endTime.includes('+')) {
        end = new Date(endTime);
    } else {
        end = new Date(endTime + 'Z');
    }

    const totalSeconds = Math.floor((end - start) / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return minutes > 0 ? `${minutes} min ${seconds} sec` : `${seconds} sec`;
}

// Show loading state for bookings
function showBookingsLoading() {
    document.getElementById('bookingsList').innerHTML =
        '<div class="loading-message">Loading your bookings...</div>';
}

// Display bookings in the UI
function displayBookings(bookings) {
    const bookingsList = document.getElementById('bookingsList');

    if (!bookings || bookings.length === 0) {
        bookingsList.innerHTML = `
            <div class="no-bookings-message">
                No bookings yet.<br>
                <small style="margin-top: 10px; display: block;">Your client bookings will appear here once customers start scheduling services.</small>
            </div>
        `;
        return;
    }

    // Sort bookings by date and time (newest first)
    const sortedBookings = bookings.sort((a, b) => {
        const dateA = new Date(`${a.date} ${a.start_time}`);
        const dateB = new Date(`${b.date} ${b.start_time}`);
        return dateB - dateA;
    });

    bookingsList.innerHTML = sortedBookings.map(booking => createBookingCard(booking)).join('');

    // Restart any active timers
    sortedBookings.forEach(booking => {
        console.log(`Booking ${booking.id}: session_id=${booking.session_id}, session_started=${booking.session_started}, actual_duration=${booking.actual_duration}`);
        if (booking.session_started && !booking.actual_duration) {
            console.log(`Starting timer for booking ${booking.id}`);
            startTimer(booking.id, booking.session_started);
        }
    });
}

// Create a booking card HTML
function createBookingCard(booking) {
    const bookingDate = new Date(booking.date);
    const formattedDate = bookingDate.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    const startTime = formatTime(booking.start_time);
    const endTime = formatTime(booking.end_time);

    // Format phone number for display
    const phoneDisplay = booking.client_phone ? formatPhoneForDisplay(booking.client_phone) : null;
    const phoneHtml = phoneDisplay
        ? (typeof phoneDisplay === 'object' && phoneDisplay.isInvalid
            ? `<span class="tag tag-danger">${phoneDisplay.formatted} (invalid)</span>`
            : `<span class="text-secondary" style="font-size:0.8rem;">${phoneDisplay}</span>`)
        : '';

    const statusTag = `<span class="tag status-tag tag-${booking.status} ${booking.status === 'confirmed' ? 'tag-accent' : booking.status === 'completed' ? 'tag-success' : booking.status === 'cancelled' ? 'tag-danger' : ''}">${booking.status}</span>`;

    return `
        <div class="booking-card" data-booking-id="${booking.id}" data-status="${booking.status}">
          <div class="flex" style="justify-content:space-between; align-items:flex-start; gap:16px;">
            <div class="flex-col" style="gap:6px;">
              <div style="font-weight:600;">
                ${booking.consumer_id ? `<a href="#" onclick="event.preventDefault(); event.stopPropagation(); openClientProfile(${booking.consumer_id}); return false;" style="color: var(--color-accent); text-decoration: underline; text-decoration-color: rgba(212, 175, 55, 0.3); cursor: pointer; transition: all 0.2s;" onmouseover="this.style.color='var(--color-accent-hover)'; this.style.textDecorationColor='var(--color-accent-hover)';" onmouseout="this.style.color='var(--color-accent)'; this.style.textDecorationColor='rgba(212, 175, 55, 0.3)';" title="View client profile">${booking.client_name}</a>` : booking.client_name}
              </div>
              <div class="text-tertiary" style="font-size:0.7rem; letter-spacing:.5px;">${booking.client_email || ''}</div>
              ${phoneHtml}
            </div>
            ${statusTag}
          </div>
          <div class="flex" style="flex-wrap:wrap; gap:12px; margin-top:14px;">
            <div class="tag">${booking.service?.name || 'Service'}</div>
            <div class="tag">${formattedDate}</div>
            <div class="tag">${startTime} - ${endTime}</div>
            ${booking.service?.price ? `<div class="tag">$${booking.service.price}</div>` : ''}
          </div>
          ${booking.notes ? `<div class="text-secondary" style="margin-top:14px; font-size:0.75rem; line-height:1.4;">${booking.notes}</div>` : ''}
          
          ${booking.status === 'confirmed' ? `
            <!-- Stopwatch Timer for Appointment Tracking -->
            <div class="stopwatch-container" id="stopwatch-${booking.id}">
              ${booking.session_id && booking.session_started ? `
                <div class="stopwatch-status">In Progress</div>
                <div class="stopwatch-timer" id="timer-${booking.id}">00:00:00</div>
                <div class="stopwatch-label">Elapsed Time</div>
                <button 
                  type="button"
                  class="stopwatch-btn stopwatch-btn-stop" 
                  onclick="event.preventDefault(); event.stopPropagation(); finishAppointment(${booking.id}, ${booking.session_id}); return false;"
                  title="Complete and stop tracking">
                  <span class="stopwatch-icon">⏹</span>
                  <span class="stopwatch-text">Finish Appointment</span>
                </button>
              ` : `
                <button 
                  type="button"
                  class="stopwatch-btn stopwatch-btn-start" 
                  onclick="event.preventDefault(); event.stopPropagation(); startAppointment(${booking.id}); return false;"
                  title="Start tracking appointment time">
                  <span class="stopwatch-icon">▶</span>
                  <span class="stopwatch-text">Begin Timing Appointment</span>
                </button>
              `}
            </div>
            
            <div class="flex" style="gap:10px; margin-top:18px;">
              <button class="btn btn-danger" style="flex:1;" onclick="updateBookingStatus(${booking.id}, 'cancelled')">Cancel Booking</button>
            </div>
          ` : booking.status === 'completed' ? `
            ${booking.session_started && booking.session_ended ? `
              <div style="margin-top:14px; padding:12px; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:8px;">
                <div style="font-size:0.75rem; color:rgba(16,185,129,0.8); margin-bottom:4px;">ACTUAL DURATION</div>
                <div style="font-size:1.1rem; font-weight:600; color:#10b981;">
                  ${formatDuration(booking.session_started, booking.session_ended)}
                </div>
              </div>
            ` : ''}
          ` : ''}
        </div>`;
}

// Filter bookings by status
export function filterBookings() {
    const filter = document.getElementById('bookingStatusFilter').value;
    const bookingCards = document.querySelectorAll('.booking-card');

    bookingCards.forEach(card => {
        const status = card.getAttribute('data-status');
        if (filter === 'all' || status === filter) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Update booking status (complete/cancel)
export async function updateBookingStatus(bookingId, newStatus) {
    if (!confirm(`Are you sure you want to mark this booking as ${newStatus}?`)) {
        return;
    }

    try {
        const response = await fetch(`/booking/${bookingId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });

        if (response.ok) {
            showResponse('bookingsResponse', `Booking ${newStatus} successfully!`, 'success');
            await loadBookings(); // Refresh the bookings list
        } else {
            const error = await response.json();
            showResponse('bookingsResponse', `Failed to update booking: ${error.detail}`, 'error');
        }
    } catch (error) {
        showResponse('bookingsResponse', `Connection error: ${error.message}`, 'error');
    }
}

// ========================
// APPOINTMENT SESSION TRACKING
// ========================

// Start appointment tracking
export async function startAppointment(bookingId) {
    const currentSpecialistId = window.currentSpecialistId;

    console.log('startAppointment called with bookingId:', bookingId);
    console.log('currentSpecialistId:', currentSpecialistId);

    if (!currentSpecialistId) {
        showResponse('bookingsResponse', 'Error: Please log in to track appointments', 'error');
        return;
    }

    try {
        const url = `/specialist/${currentSpecialistId}/appointment-session/start`;
        console.log('Fetching:', url);

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ booking_id: bookingId })
        });

        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);

        if (response.ok) {
            const session = await response.json();
            console.log('Appointment session started:', session);

            // Show success message
            showResponse('bookingsResponse', '⏱️ Appointment tracking started!', 'success');

            // Update the UI inline without reloading entire list
            const stopwatchContainer = document.getElementById(`stopwatch-${bookingId}`);
            if (stopwatchContainer) {
                stopwatchContainer.innerHTML = `
                    <div class="stopwatch-status">In Progress</div>
                    <div class="stopwatch-timer" id="timer-${bookingId}">00:00:00</div>
                    <div class="stopwatch-label">Elapsed Time</div>
                    <button 
                      class="stopwatch-btn stopwatch-btn-stop" 
                      onclick="finishAppointment(${bookingId}, ${session.id})"
                      title="Complete and stop tracking">
                      <span class="stopwatch-icon">⏹</span>
                      <span class="stopwatch-text">Finish Appointment</span>
                    </button>
                `;

                // Start the visual timer
                startTimer(bookingId, session.actual_start);
            }
        } else {
            const error = await response.json();
            console.error('Server error:', error);
            showResponse('bookingsResponse', `Failed to start: ${error.detail || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error starting appointment:', error);
        console.error('Error stack:', error.stack);
        showResponse('bookingsResponse', `Connection error: ${error.message}`, 'error');
    }
}

// Finish appointment tracking
export async function finishAppointment(bookingId, sessionId) {
    // Check if user has disabled the confirmation prompt
    const skipConfirmation = localStorage.getItem('skipCompleteConfirmation') === 'true';

    if (skipConfirmation) {
        // Proceed directly without showing modal
        await executeCompleteAppointment(bookingId, sessionId);
    } else {
        // Store the data and show the custom modal
        pendingCompletion = { bookingId, sessionId };
        document.getElementById('completeAppointmentModal').style.display = 'block';
        // Reset checkbox state
        document.getElementById('dontAskCompleteAgain').checked = false;
    }
}

export function closeCompleteAppointmentModal() {
    document.getElementById('completeAppointmentModal').style.display = 'none';
    pendingCompletion = null;
}

export async function confirmCompleteAppointment() {
    // Check if user selected "don't ask again"
    const dontAsk = document.getElementById('dontAskCompleteAgain').checked;
    if (dontAsk) {
        localStorage.setItem('skipCompleteConfirmation', 'true');
    }

    // Close modal
    closeCompleteAppointmentModal();

    // Execute the completion if we have pending data
    if (pendingCompletion) {
        await executeCompleteAppointment(pendingCompletion.bookingId, pendingCompletion.sessionId);
        pendingCompletion = null;
    }
}

// Helper function to reset confirmation preferences (can be called from console or UI)
export function resetCompleteConfirmationPreference() {
    localStorage.removeItem('skipCompleteConfirmation');
    console.log('✅ Completion confirmation prompt has been re-enabled');
    alert('Completion confirmation prompt has been re-enabled. You will now see the confirmation dialog when completing appointments.');
}

async function executeCompleteAppointment(bookingId, sessionId) {
    const currentSpecialistId = window.currentSpecialistId;

    console.log('executeCompleteAppointment called:', { bookingId, sessionId, currentSpecialistId });

    try {
        const url = `/specialist/${currentSpecialistId}/appointment-session/${sessionId}/complete`;
        console.log('Fetching URL:', url);

        const response = await fetch(url, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({})
        });

        console.log('Response status:', response.status);

        if (response.ok) {
            const session = await response.json();
            console.log('Appointment completed:', session);

            // Stop the timer
            stopTimer(bookingId);

            // Note: The API endpoint already updates booking status to 'completed'
            // No need for a second fetch call

            // Calculate display duration - parse UTC times correctly
            let startDate, endDate;
            if (session.actual_start.includes('Z') || session.actual_start.includes('+')) {
                startDate = new Date(session.actual_start);
            } else {
                startDate = new Date(session.actual_start + 'Z');
            }
            if (session.actual_end.includes('Z') || session.actual_end.includes('+')) {
                endDate = new Date(session.actual_end);
            } else {
                endDate = new Date(session.actual_end + 'Z');
            }

            const totalSeconds = Math.floor((endDate - startDate) / 1000);
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            const durationText = minutes > 0 ? `${minutes} min ${seconds} sec` : `${seconds} sec`;

            // Show success message
            showResponse('bookingsResponse',
                `✅ Appointment completed! Actual duration: ${durationText}`,
                'success'
            );

            // Update the card inline to show completed status with duration
            const bookingCard = document.querySelector(`[data-booking-id="${bookingId}"]`);
            if (bookingCard) {
                // Find the stopwatch container and replace it with the duration display
                const stopwatchContainer = bookingCard.querySelector(`#stopwatch-${bookingId}`);
                if (stopwatchContainer) {
                    stopwatchContainer.outerHTML = `
                        <div style="margin-top:14px; padding:12px; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:8px;">
                            <div style="font-size:0.75rem; color:rgba(16,185,129,0.8); margin-bottom:4px;">ACTUAL DURATION</div>
                            <div style="font-size:1.1rem; font-weight:600; color:#10b981;">
                                ${durationText}
                            </div>
                        </div>
                    `;
                }

                // Remove the Cancel Booking button (it's in a flex container after the stopwatch)
                const cancelButtonContainer = bookingCard.querySelector('.flex button.btn-danger');
                if (cancelButtonContainer) {
                    // Remove the entire flex container that holds the Cancel button
                    cancelButtonContainer.closest('.flex').remove();
                }

                // Update status tag
                const statusTag = bookingCard.querySelector('.status-tag');
                if (statusTag) {
                    statusTag.className = 'tag status-tag tag-completed tag-success';
                    statusTag.textContent = 'completed';
                }

                // Update data attribute
                bookingCard.setAttribute('data-status', 'completed');
            }
        } else {
            const error = await response.json();
            showResponse('bookingsResponse', `Failed to complete: ${error.detail || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error completing appointment:', error);
        showResponse('bookingsResponse', `Connection error: ${error.message}`, 'error');
    }
}

// Open client profile from booking card
export function openClientProfile(consumerId) {
    if (!consumerId) {
        console.error('No consumer ID provided');
        return;
    }

    // Switch to clients tab
    window.switchTab('clients');

    // Wait a bit for the tab to load if needed, then open the client detail modal
    setTimeout(() => {
        window.viewClientDetail(consumerId);
    }, 100);
}

// ========================
// TIMER MANAGEMENT
// ========================

// Start visual timer
function startTimer(bookingId, startTime) {
    console.log(`startTimer called: bookingId=${bookingId}, startTime=${startTime}`);

    // Parse the UTC datetime string correctly
    // The server sends UTC time, we need to parse it as UTC
    let startDate;
    if (startTime.includes('Z') || startTime.includes('+')) {
        // Already has timezone info
        startDate = new Date(startTime);
    } else {
        // Assume UTC and add 'Z' suffix
        startDate = new Date(startTime + 'Z');
    }

    console.log(`startDate parsed: ${startDate}`);
    console.log(`startDate ISO: ${startDate.toISOString()}`);

    // Clear any existing timer
    if (activeTimers[bookingId]) {
        clearInterval(activeTimers[bookingId]);
    }

    // Update timer display every second
    activeTimers[bookingId] = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now - startDate) / 1000); // seconds

        const hours = Math.floor(elapsed / 3600);
        const minutes = Math.floor((elapsed % 3600) / 60);
        const seconds = elapsed % 60;

        const timeString = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

        const timerElement = document.getElementById(`timer-${bookingId}`);
        if (timerElement) {
            timerElement.textContent = timeString;
        } else {
            // Element not found, stop timer
            stopTimer(bookingId);
        }
    }, 1000);
}

// Stop visual timer
function stopTimer(bookingId) {
    if (activeTimers[bookingId]) {
        clearInterval(activeTimers[bookingId]);
        delete activeTimers[bookingId];
    }
}

// Clean up all timers when leaving page
window.addEventListener('beforeunload', () => {
    Object.keys(activeTimers).forEach(bookingId => {
        stopTimer(bookingId);
    });
});

console.log('Bookings.js module loaded successfully!');
