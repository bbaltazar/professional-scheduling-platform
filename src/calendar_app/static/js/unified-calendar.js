/**
 * UNIFIED CALENDAR MODULE
 * Combines recurring availability and actual bookings in one calendar view
 */

// State management
let currentWeekStart = null;
let unifiedCalendarData = {
    availability: [],  // Recurring availability blocks
    bookings: []       // Actual bookings for current week
};
let calendarFilters = {
    availability: true,
    confirmed: true,
    completed: true,
    cancelled: false
};
let isEditMode = false;
let workplaceColors = {}; // Map workplace IDs to colors

// Color palette for different workplaces/calendars
const CALENDAR_COLORS = [
    { bg: 'rgba(59, 130, 246, 0.15)', border: '#3b82f6', text: '#1e40af' },      // Blue
    { bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981', text: '#065f46' },      // Green
    { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', text: '#92400e' },      // Amber
    { bg: 'rgba(139, 92, 246, 0.15)', border: '#8b5cf6', text: '#5b21b6' },      // Purple
    { bg: 'rgba(236, 72, 153, 0.15)', border: '#ec4899', text: '#9f1239' },      // Pink
    { bg: 'rgba(20, 184, 166, 0.15)', border: '#14b8a6', text: '#115e59' },      // Teal
    { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', text: '#991b1b' },       // Red
    { bg: 'rgba(99, 102, 241, 0.15)', border: '#6366f1', text: '#3730a3' }       // Indigo
];

/**
 * Initialize the unified calendar
 */
function initializeUnifiedCalendar() {
    // Set current week to today
    const today = new Date();
    currentWeekStart = getWeekStart(today);

    // Load workplaces for filter dropdown
    loadWorkplacesForFilter();

    // Render the calendar grid
    renderUnifiedCalendarGrid();

    // Update week display
    updateWeekDisplay();

    // Load data
    refreshUnifiedCalendar();

    // Enable drag-to-create
    setTimeout(() => {
        enableDragToCreate();
    }, 500);
}

/**
 * Get the start of the week (Monday) for a given date
 */
function getWeekStart(date) {
    const d = new Date(date);
    const day = d.getDay(); // 0=Sunday, 1=Monday, etc.
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
    const weekStart = new Date(d.setDate(diff));
    weekStart.setHours(0, 0, 0, 0);
    console.log('[getWeekStart] Input date:', date.toDateString(), 'getDay():', day, 'Calculated week start:', weekStart.toDateString());
    return weekStart;
}

/**
 * Get the end of the week (Sunday)
 */
function getWeekEnd(weekStart) {
    const end = new Date(weekStart);
    end.setDate(end.getDate() + 6);
    return end;
}

/**
 * Format date for display
 */
function formatDate(date, format = 'short') {
    const options = format === 'short'
        ? { month: 'short', day: 'numeric' }
        : { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Format date as YYYY-MM-DD in local timezone (not UTC)
 * This prevents timezone offset issues when creating schedules
 */
function formatDateLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Parse YYYY-MM-DD string as local date (not UTC)
 * When you use new Date("2025-12-23"), JavaScript treats it as UTC midnight,
 * which can shift to the previous day in timezones behind UTC (e.g., PST).
 * This function ensures the date is parsed in local timezone.
 */
function parseDateLocal(dateString) {
    const [year, month, day] = dateString.split('-').map(Number);
    return new Date(year, month - 1, day);  // month is 0-indexed
}

/**
 * Update the week display text
 */
function updateWeekDisplay() {
    const weekEnd = getWeekEnd(currentWeekStart);
    const displayText = `Week of ${formatDate(currentWeekStart)} - ${formatDate(weekEnd)}`;
    const displayEl = document.getElementById('calendarPeriodDisplay') || document.getElementById('currentWeekDisplay');
    if (displayEl) {
        displayEl.textContent = displayText;
    }
}

/**
 * Update month display
 */
function updateMonthDisplay() {
    if (!currentMonthStart) return;

    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    const displayText = `${monthNames[currentMonthStart.getMonth()]} ${currentMonthStart.getFullYear()}`;
    const displayEl = document.getElementById('calendarPeriodDisplay');
    if (displayEl) {
        displayEl.textContent = displayText;
    }
}

/**
 * Update period display based on current view mode
 */
function updatePeriodDisplay() {
    if (currentViewMode === 'month') {
        updateMonthDisplay();
    } else {
        updateWeekDisplay();
    }
}

/**
 * Navigate to previous/next week
 */
function navigateWeek(direction) {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(newDate.getDate() + (direction * 7));
    currentWeekStart = newDate;

    updateWeekDisplay();
    refreshUnifiedCalendar().then(() => {
        // Reapply day filter after calendar is refreshed
        if (typeof reapplyDayFilter === 'function') {
            reapplyDayFilter();
        }
    });
}

/**
 * Go to current week
 */
function goToToday() {
    const today = new Date();

    if (currentViewMode === 'month') {
        currentMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
    } else {
        currentWeekStart = getWeekStart(today);
        updateWeekDisplay();
    }

    refreshUnifiedCalendar();
}

/**
 * Toggle calendar layer visibility
 */
function toggleCalendarLayer(layer) {
    calendarFilters[layer] = document.getElementById(`show${layer.charAt(0).toUpperCase() + layer.slice(1)}`).checked;
    renderUnifiedCalendarData();
}

/**
 * Toggle edit mode for availability
 */
function toggleEditMode() {
    isEditMode = !isEditMode;
    const btn = document.getElementById('editModeBtn');

    if (isEditMode) {
        btn.textContent = '✓ View Mode';
        btn.style.background = 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)';
        btn.style.color = 'white';
    } else {
        btn.textContent = '✏️ Edit Availability';
        btn.style.background = '';
        btn.style.color = '';
    }

    // Re-render to enable/disable drag interactions
    renderUnifiedCalendarData();
}

/**
 * Refresh all calendar data
 */
async function refreshUnifiedCalendar() {
    try {
        // Re-render the grid structure (week or month based on currentViewMode)
        renderUnifiedCalendarGrid();

        // Update period display
        updatePeriodDisplay();

        // Load recurring availability
        await loadRecurringAvailability();

        // Load bookings for current week
        await loadWeekBookings();

        // Render the combined data
        renderUnifiedCalendarData();

        // Update stats
        updateCalendarStats();

    } catch (error) {
        console.error('Error refreshing unified calendar:', error);
    }
}

/**
 * Load recurring availability patterns
 */
async function loadRecurringAvailability() {
    if (!window.currentSpecialistId) return;

    try {
        // Calculate current week's date range
        const weekStart = new Date(currentWeekStart);
        const weekEnd = new Date(currentWeekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);

        // Use local timezone formatting to avoid UTC offset issues
        const startDateStr = formatDateLocal(weekStart);
        const endDateStr = formatDateLocal(weekEnd);

        // Use the new endpoint that returns individual instances with IDs
        // Pass date range so backend can generate instances on-demand
        const url = `/specialist/${window.currentSpecialistId}/calendar-instances?start_date=${startDateStr}&end_date=${endDateStr}`;

        const response = await fetch(url);

        if (response.ok) {
            const instances = await response.json();
            console.log('[loadRecurringAvailability] Received instances:', instances);

            // Assign colors to workplaces
            const uniqueWorkplaces = [...new Set(instances.map(i => i.workplace_id))];
            uniqueWorkplaces.forEach((workplaceId, index) => {
                if (!workplaceColors[workplaceId]) {
                    workplaceColors[workplaceId] = CALENDAR_COLORS[index % CALENDAR_COLORS.length];
                }
            });

            // Convert instances to availability blocks with individual IDs
            unifiedCalendarData.availability = instances.map(instance => ({
                day: instance.day_of_week,
                start_time: instance.start_time,
                end_time: instance.end_time,
                instance_id: instance.instance_id,  // Individual database ID
                recurring_event_id: instance.recurring_event_id,  // Series ID
                base_event_id: instance.base_event_id,  // Base template ID
                workplace_id: instance.workplace_id,
                workplace_name: instance.workplace?.name || 'Personal',
                recurrence_type: instance.recurrence_type,
                date: instance.date,  // Actual date of this instance
            }));
            
            console.log('[loadRecurringAvailability] Mapped availability:', unifiedCalendarData.availability);
        } else {
            console.error('[loadRecurringAvailability] ❌ Response not ok:', response.status, response.statusText);
            const errorText = await response.text();
            console.error('[loadRecurringAvailability] Error details:', errorText);
        }
    } catch (error) {
        console.error('[loadRecurringAvailability] ❌ Exception:', error);
    }
}

/**
 * Load bookings for the current week
 */
async function loadWeekBookings() {
    if (!window.currentSpecialistId) return;

    try {
        const response = await fetch(`/bookings/specialist/${window.currentSpecialistId}`);
        if (response.ok) {
            const allBookings = await response.json();
            console.log('[loadWeekBookings] All bookings:', allBookings);

            // Filter to current week and map field names
            const weekEnd = getWeekEnd(currentWeekStart);
            console.log('[loadWeekBookings] Week range:', currentWeekStart, 'to', weekEnd);
            
            unifiedCalendarData.bookings = allBookings
                .map(booking => ({
                    ...booking,
                    booking_date: booking.date, // Map 'date' to 'booking_date'
                    // Keep original fields too
                }))
                .filter(booking => {
                    const bookingDate = new Date(booking.booking_date);
                    const inRange = bookingDate >= currentWeekStart && bookingDate <= weekEnd;
                    console.log('[loadWeekBookings] Booking:', booking.booking_date, 'inRange:', inRange);
                    return inRange;
                });
            
            console.log('[loadWeekBookings] Filtered bookings for week:', unifiedCalendarData.bookings);
        } else {
            console.warn('[loadWeekBookings] Failed to load bookings:', response.status);
            unifiedCalendarData.bookings = [];
        }
    } catch (error) {
        console.error('[loadWeekBookings] Error loading bookings:', error);
        unifiedCalendarData.bookings = [];
    }
}

/**
 * Render the unified calendar grid structure
 */
function renderUnifiedCalendarGrid() {
    if (currentViewMode === 'month') {
        renderMonthCalendarGrid();
    } else {
        renderWeekCalendarGrid();
    }
}

/**
 * Render week view calendar grid
 */
function renderWeekCalendarGrid() {
    const calendar = document.getElementById('unifiedCalendar');
    if (!calendar) {
        console.error('[UnifiedCalendar] ERROR: unifiedCalendar element not found!');
        return;
    }

    // Ensure we have a week start date
    if (!currentWeekStart) {
        console.warn('[UnifiedCalendar] currentWeekStart is null, setting to today');
        const today = new Date();
        currentWeekStart = getWeekStart(today);
    }

    // Time column labels - use active time filter if set, otherwise default to 6am-9pm
    const timeLabels = [];
    let startHour, endHour;
    
    if (window.activeTimeRange) {
        startHour = window.activeTimeRange.start;
        endHour = window.activeTimeRange.end;
    } else {
        // Default to 6am-9pm
        startHour = 6;
        endHour = 21;
    }

    for (let hour = startHour; hour <= endHour; hour++) {
        const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
        const period = hour >= 12 ? 'PM' : 'AM';
        timeLabels.push({ label: `${displayHour} ${period}`, hour });
    }

    // Days of week with actual dates
    const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const days = [];

    // Generate dates for the current week
    for (let i = 0; i < 7; i++) {
        const date = new Date(currentWeekStart);
        date.setDate(date.getDate() + i);
        days.push({
            name: dayNames[i],
            date: date.getDate(),
            month: date.getMonth() + 1,
            fullDate: date,
            dayIndex: i
        });
    }

    // Calculate height based on visible hours (60px per hour + 60px header)
    const calendarHeight = (timeLabels.length * 60) + 60;

    let html = `
        <div style="display: flex; gap: 0; width: 100%; min-height: ${calendarHeight}px; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; background: #fafafa; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <!-- Time Column -->
            <div class="time-column" style="flex-shrink: 0; width: 80px; background: linear-gradient(to right, #f9fafb, #ffffff);">
                <div class="time-header" style="height: 60px; border-bottom: 1px solid #e5e7eb; background: #f9fafb;"></div>
                ${timeLabels.map(t => `
                    <div class="time-label" style="height: 60px; padding: 8px 4px; font-size: 0.7rem; color: #6b7280; border-bottom: 1px solid #f3f4f6; display: flex; align-items: flex-start; justify-content: center; font-weight: 500; padding-top: 4px;">${t.label}</div>
                `).join('')}
            </div>
            
            <!-- Day Columns -->
            <div style="display: flex !important; flex: 1 !important; gap: 0; min-width: 0;">
                ${days.map(day => {
        const isToday = new Date().toDateString() === day.fullDate.toDateString();
        return `
                    <div class="day-column" data-day="${day.dayIndex}" style="flex: 1 !important; min-width: 100px; border-left: 1px solid #e5e7eb; display: flex !important; flex-direction: column; background: white;">
                        <div class="day-header" style="height: 60px; padding: 8px; text-align: center; font-weight: 600; background: ${isToday ? 'linear-gradient(to bottom, #fef3c7, #fef9e7)' : 'linear-gradient(to bottom, #f9fafb, #ffffff)'}; border-bottom: 1px solid ${isToday ? '#fbbf24' : '#e5e7eb'}; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0;">
                            <div style="font-size: 0.7rem; color: ${isToday ? '#92400e' : '#9ca3af'}; margin-bottom: 2px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">${day.name}</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: ${isToday ? '#D4AF37' : '#1f2937'}; line-height: 1;">${day.date}</div>
                            <div style="font-size: 0.65rem; color: ${isToday ? '#92400e' : '#9ca3af'}; margin-top: 2px;">${day.month}/${day.date}</div>
                        </div>
                        <div class="time-slots-container" data-day="${day.dayIndex}" style="position: relative; flex: 1; background: white;">
                            ${timeLabels.map(t => {
            return `
                                <div class="hour-block" style="height: 60px; position: relative; border-bottom: 1px solid #f3f4f6;">
                                    ${[0, 15, 30, 45].map(minutes => `
                                        <div class="time-slot" data-day="${day.dayIndex}" data-hour="${t.hour}" data-minutes="${minutes}" style="height: 15px; position: relative; background: transparent; border: none; box-sizing: border-box; transition: background-color 0.15s ease;"></div>
                                    `).join('')}
                                </div>
                                `;
        }).join('')}
                        </div>
                    </div>
                `;
    }).join('')}
            </div>
        </div>
    `;

    calendar.innerHTML = html;
}

/**
 * Render month view calendar grid
 */
function renderMonthCalendarGrid() {
    const calendar = document.getElementById('unifiedCalendar');
    if (!calendar) {
        console.error('[UnifiedCalendar] ERROR: unifiedCalendar element not found!');
        return;
    }

    // Ensure we have a month start date
    if (!currentMonthStart) {
        const today = new Date();
        currentMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
    }

    const year = currentMonthStart.getFullYear();
    const month = currentMonthStart.getMonth();

    // Get first day of month and last day
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);

    // Find the Monday before or on the first day
    const startDate = new Date(firstDay);
    const dayOfWeek = firstDay.getDay();
    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    startDate.setDate(firstDay.getDate() - daysToMonday);

    // Generate 6 weeks (42 days) for month view to ensure all days are visible
    const weeks = [];
    let currentDate = new Date(startDate);

    for (let week = 0; week < 6; week++) {
        const weekDays = [];
        for (let day = 0; day < 7; day++) {
            const dateObj = new Date(currentDate);
            const isCurrentMonth = dateObj.getMonth() === month;
            const isToday = new Date().toDateString() === dateObj.toDateString();

            weekDays.push({
                date: dateObj.getDate(),
                month: dateObj.getMonth() + 1,
                year: dateObj.getFullYear(),
                fullDate: dateObj,
                isCurrentMonth,
                isToday,
                dayIndex: day
            });

            currentDate.setDate(currentDate.getDate() + 1);
        }
        weeks.push(weekDays);
    }

    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'];
    const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    let html = `
        <div style="width: 100%; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <!-- Month Header -->
            <div style="background: linear-gradient(to bottom, #f9fafb, #ffffff); border-bottom: 2px solid #e5e7eb; padding: 20px; text-align: center;">
                <h3 style="margin: 0; font-size: 1.5rem; color: #1f2937; font-weight: 700;">${monthNames[month]} ${year}</h3>
            </div>
            
            <!-- Day Headers -->
            <div style="display: grid; grid-template-columns: repeat(7, 1fr); border-bottom: 1px solid #e5e7eb; background: #f9fafb;">
                ${dayNames.map(name => `
                    <div style="padding: 12px; text-align: center; font-weight: 600; font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">${name}</div>
                `).join('')}
            </div>
            
            <!-- Calendar Grid -->
            <div style="display: grid; grid-template-rows: repeat(6, 1fr);">
                ${weeks.map(week => `
                    <div style="display: grid; grid-template-columns: repeat(7, 1fr); border-bottom: 1px solid #f3f4f6;">
                        ${week.map(day => {
        const bgColor = day.isToday ? '#fef3c7' : (day.isCurrentMonth ? 'white' : '#fafafa');
        const textColor = day.isToday ? '#D4AF37' : (day.isCurrentMonth ? '#1f2937' : '#9ca3af');

        return `
                            <div class="month-day-cell" data-date="${day.fullDate.toISOString()}" style="min-height: 100px; padding: 8px; border-right: 1px solid #f3f4f6; background: ${bgColor}; position: relative; cursor: pointer; transition: background 0.2s;">
                                <div style="font-weight: ${day.isToday ? '700' : '500'}; font-size: 0.9rem; color: ${textColor}; margin-bottom: 4px;">${day.date}</div>
                                <div class="month-day-events" data-date="${day.fullDate.toISOString()}" style="font-size: 0.7rem; line-height: 1.4;">
                                    <!-- Events will be populated here -->
                                </div>
                            </div>
                            `;
    }).join('')}
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    calendar.innerHTML = html;
}

/**
 * Render availability and booking blocks
 */
function renderUnifiedCalendarData() {
    if (currentViewMode === 'month') {
        renderMonthCalendarData();
    } else {
        renderWeekCalendarData();
    }
}

/**
 * Render week view calendar data
 */
function renderWeekCalendarData() {
    // Clear existing blocks
    document.querySelectorAll('.time-slots-container').forEach(container => {
        container.querySelectorAll('.time-block').forEach(block => block.remove());
    });

    // Render availability blocks (background layer)
    if (calendarFilters.availability) {
        renderAvailabilityBlocks();
    }

    // Render booking blocks (foreground layer)
    renderBookingBlocks();
}

/**
 * Render month view calendar data
 */
function renderMonthCalendarData() {
    // Clear existing event dots
    document.querySelectorAll('.month-day-events').forEach(container => {
        container.innerHTML = '';
    });

    // Render availability blocks in month view (if filter is on)
    if (calendarFilters.availability && unifiedCalendarData.availability.length > 0) {
        unifiedCalendarData.availability.forEach(avail => {
            // Find cells for this day of week in current month
            const dayCells = document.querySelectorAll('.month-day-cell');
            dayCells.forEach(cell => {
                const cellDate = new Date(cell.dataset.date);
                cellDate.setHours(0, 0, 0, 0);
                const cellDayOfWeek = (cellDate.getDay() + 6) % 7; // Convert to Monday=0

                if (cellDayOfWeek === avail.day) {
                    const eventContainer = cell.querySelector('.month-day-events');
                    if (eventContainer) {
                        const color = workplaceColors[avail.workplace_id] || CALENDAR_COLORS[0];
                        const availDot = document.createElement('div');
                        availDot.style.cssText = `
                            padding: 2px 6px;
                            margin-bottom: 2px;
                            background: ${color.border};
                            border-radius: 3px;
                            color: white;
                            font-weight: 500;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            white-space: nowrap;
                            opacity: 0.6;
                        `;
                        availDot.textContent = avail.workplace_name || 'Available';
                        availDot.title = `${avail.workplace_name}: ${formatTime(avail.start_time)} - ${formatTime(avail.end_time)}`;
                        eventContainer.appendChild(availDot);
                    }
                }
            });
        });
    }

    // Render bookings as event dots in month view
    unifiedCalendarData.bookings.forEach(booking => {
        const bookingDate = new Date(booking.booking_date);
        // Normalize to date only (remove time component)
        bookingDate.setHours(0, 0, 0, 0);

        // Find matching day cell by comparing dates
        const dayCells = document.querySelectorAll('.month-day-cell');
        dayCells.forEach(cell => {
            const cellDateStr = cell.dataset.date;
            const cellDate = new Date(cellDateStr);
            cellDate.setHours(0, 0, 0, 0);

            if (cellDate.getTime() === bookingDate.getTime()) {
                const eventContainer = cell.querySelector('.month-day-events');

                if (eventContainer) {
                    const eventDot = document.createElement('div');
                    eventDot.style.cssText = `
                        padding: 2px 6px;
                        margin-bottom: 2px;
                        background: ${getBookingColor(booking.status)};
                        border-radius: 3px;
                        color: white;
                        font-weight: 500;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    `;
                    eventDot.textContent = booking.service_name || 'Booking';
                    eventDot.title = `${booking.service_name} - ${booking.client_name} at ${booking.booking_time}`;
                    eventContainer.appendChild(eventDot);
                }
            }
        });
    });
}

/**
 * Get color for booking status
 */
function getBookingColor(status) {
    switch (status) {
        case 'confirmed': return '#3b82f6';
        case 'completed': return '#22c55e';
        case 'cancelled': return '#ef4444';
        default: return '#6b7280';
    }
}

/**
 * Render availability blocks
 */
function renderAvailabilityBlocks() {
    unifiedCalendarData.availability.forEach(avail => {
        // Convert actual date to column index for current week
        // The backend provides the actual date of the instance
        if (!avail.date) {
            console.warn('[renderAvailabilityBlocks] No date provided for availability:', avail);
            return;
        }

        // Parse date in local timezone to avoid UTC offset issues
        const instanceDate = parseDateLocal(avail.date);
        const weekStart = new Date(currentWeekStart);

        // Normalize both dates to midnight for accurate day calculation
        instanceDate.setHours(0, 0, 0, 0);
        weekStart.setHours(0, 0, 0, 0);

        // Calculate which column (0-6) this date falls into for the current week
        const daysDiff = Math.floor((instanceDate - weekStart) / (1000 * 60 * 60 * 24));
        
        console.log(`[renderAvailabilityBlocks] Avail date=${avail.date}, instanceDate=${instanceDate.toDateString()}, weekStart=${weekStart.toDateString()}, daysDiff=${daysDiff}, day_of_week=${avail.day}`);

        // Only render if this instance is in the current week (0-6)
        if (daysDiff < 0 || daysDiff > 6) {
            return;
        }

        const dayColumn = document.querySelector(`.time-slots-container[data-day="${daysDiff}"]`);
        if (!dayColumn) {
            console.warn('[renderAvailabilityBlocks] Day column not found for column index', daysDiff);
            return;
        }

        const block = createAvailabilityBlock(avail);
        dayColumn.appendChild(block);
    });
}

/**
 * Create an availability block element
 */
function createAvailabilityBlock(avail) {
    const block = document.createElement('div');
    block.className = 'time-block availability-block';

    // Get workplace color
    const color = workplaceColors[avail.workplace_id] || CALENDAR_COLORS[0];

    block.style.cssText = `
        position: absolute;
        left: 0;
        right: 0;
        background: ${color.bg};
        border: 2px dashed ${color.border};
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
        z-index: 1;
    `;

    // Calculate position
    const startMinutes = timeToMinutes(avail.start_time);
    const endMinutes = timeToMinutes(avail.end_time);
    
    // Get the calendar's start hour from the active time filter
    const calendarStartHour = window.activeTimeRange ? window.activeTimeRange.start : 6;
    const calendarEndHour = window.activeTimeRange ? window.activeTimeRange.end : 21;
    const baseMinutes = calendarStartHour * 60;
    const maxMinutes = (calendarEndHour + 1) * 60;

    // Check if block is outside visible range
    if (endMinutes <= baseMinutes || startMinutes >= maxMinutes) {
        console.warn(`[createAvailabilityBlock] ⚠️ Block time ${avail.start_time}-${avail.end_time} is outside visible calendar range (${calendarStartHour}:00 - ${calendarEndHour + 1}:00). Block will not be visible!`);
    }

    // Each hour block is 60px tall
    const pixelsPerHour = 60;
    const top = ((startMinutes - baseMinutes) / 60) * pixelsPerHour;
    const height = ((endMinutes - startMinutes) / 60) * pixelsPerHour;

    block.style.top = `${top}px`;
    block.style.height = `${height}px`;

    // Content
    block.innerHTML = `
        <div style="padding: 6px; font-size: 0.75rem; color: ${color.text}; text-align: center;">
            <div style="font-weight: 600;">${formatTime(avail.start_time)} - ${formatTime(avail.end_time)}</div>
            <div style="opacity: 0.8; font-size: 0.65rem; margin-top: 2px;">${avail.workplace_name || 'Available'}</div>
        </div>
    `;

    // Hover effect
    block.addEventListener('mouseenter', () => {
        block.style.background = color.bg.replace('0.15', '0.25');
    });
    block.addEventListener('mouseleave', () => {
        block.style.background = color.bg;
    });

    // Click to edit/delete - always enabled for availability blocks
    block.addEventListener('click', (e) => {
        e.stopPropagation();
        console.log('[AvailabilityBlock] Clicked! Data:', avail);
        showScheduleEditModal(avail);
    });

    return block;
}

/**
 * Render booking blocks
 */
function renderBookingBlocks() {
    unifiedCalendarData.bookings.forEach(booking => {
        // Check if this status should be visible
        if (!calendarFilters[booking.status]) return;

        const bookingDate = new Date(booking.booking_date);
        const dayOfWeek = (bookingDate.getDay() + 6) % 7; // Convert Sunday=0 to Monday=0

        const dayColumn = document.querySelector(`.time-slots-container[data-day="${dayOfWeek}"]`);
        if (!dayColumn) return;

        const block = createBookingBlock(booking);
        dayColumn.appendChild(block);
    });
}

/**
 * Create a booking block element
 */
function createBookingBlock(booking) {
    const block = document.createElement('div');
    block.className = 'time-block booking-block';

    // Color based on status
    const colors = {
        confirmed: { bg: '#3b82f6', border: '#2563eb', text: '#ffffff' },
        completed: { bg: '#22c55e', border: '#16a34a', text: '#ffffff' },
        cancelled: { bg: 'rgba(239, 68, 68, 0.3)', border: '#dc2626', text: '#7f1d1d' }
    };

    const color = colors[booking.status] || colors.confirmed;

    block.style.cssText = `
        position: absolute;
        left: 0;
        right: 0;
        background: ${color.bg};
        border: 2px solid ${color.border};
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
        z-index: 10;
        color: ${color.text};
    `;

    // Calculate position
    const startMinutes = timeToMinutes(booking.start_time);
    const endMinutes = timeToMinutes(booking.end_time);
    
    // Get the calendar's start hour from the active time filter
    const calendarStartHour = window.activeTimeRange ? window.activeTimeRange.start : 6;
    const baseMinutes = calendarStartHour * 60;

    // Each hour block is 60px tall
    const pixelsPerHour = 60;
    const top = ((startMinutes - baseMinutes) / 60) * pixelsPerHour;
    const height = ((endMinutes - startMinutes) / 60) * pixelsPerHour;

    block.style.top = `${top}px`;
    block.style.height = `${height}px`;

    // Content
    block.innerHTML = `
        <div style="padding: 8px; font-size: 0.75rem;">
            <div style="font-weight: 700; margin-bottom: 2px;">${booking.client_name}</div>
            <div style="opacity: 0.9; font-size: 0.7rem;">${booking.service_name}</div>
            <div style="opacity: 0.8; font-size: 0.65rem; margin-top: 2px;">${formatTime(booking.start_time)} - ${formatTime(booking.end_time)}</div>
        </div>
    `;

    // Hover effect
    block.addEventListener('mouseenter', () => {
        block.style.transform = 'scale(1.02)';
        block.style.zIndex = '100';
        block.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
    });
    block.addEventListener('mouseleave', () => {
        block.style.transform = 'scale(1)';
        block.style.zIndex = '10';
        block.style.boxShadow = 'none';
    });

    // Click to view details
    block.addEventListener('click', () => {
        showBookingDetails(booking);
    });

    return block;
}

/**
 * Show booking details modal
 */
function showBookingDetails(booking) {
    // TODO: Implement booking details modal
    alert(`Booking Details:\n\nClient: ${booking.client_name}\nService: ${booking.service_name}\nTime: ${formatTime(booking.start_time)} - ${formatTime(booking.end_time)}\nStatus: ${booking.status}`);
}

/**
 * Update calendar stats
 */
function updateCalendarStats() {
    // Calculate available hours
    const availableHours = unifiedCalendarData.availability.reduce((total, avail) => {
        const minutes = timeToMinutes(avail.end_time) - timeToMinutes(avail.start_time);
        return total + (minutes / 60);
    }, 0);

    // Count confirmed and completed
    const confirmed = unifiedCalendarData.bookings.filter(b => b.status === 'confirmed').length;
    const completed = unifiedCalendarData.bookings.filter(b => b.status === 'completed').length;

    // Calculate booked hours
    const bookedHours = unifiedCalendarData.bookings
        .filter(b => b.status === 'confirmed' || b.status === 'completed')
        .reduce((total, booking) => {
            const minutes = timeToMinutes(booking.end_time) - timeToMinutes(booking.start_time);
            return total + (minutes / 60);
        }, 0);

    // Utilization rate
    const utilization = availableHours > 0 ? ((bookedHours / availableHours) * 100).toFixed(0) : 0;

    // Update DOM
    document.getElementById('statsAvailableHours').textContent = `${availableHours.toFixed(1)}h`;
    document.getElementById('statsConfirmed').textContent = confirmed;
    document.getElementById('statsCompleted').textContent = completed;
    document.getElementById('statsUtilization').textContent = `${utilization}%`;
}

/**
 * Convert time string to minutes
 */
function timeToMinutes(timeStr) {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
}

/**
 * Format time for display
 */
function formatTime(timeStr) {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours > 12 ? hours - 12 : (hours === 0 ? 12 : hours);
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
}

/**
 * Show manage availability section
 */
function showManageAvailabilitySection() {
    document.getElementById('manageAvailabilitySection').style.display = 'block';
    document.getElementById('manageAvailabilitySection').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Hide manage availability section
 */
function hideManageAvailabilitySection() {
    document.getElementById('manageAvailabilitySection').style.display = 'none';
    // Refresh calendar in case changes were made
    refreshUnifiedCalendar();
}

// Initialize on calendar tab load
if (typeof window.switchTab === 'function') {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function (tabName) {
        originalSwitchTab(tabName);
        if (tabName === 'calendar') {
            setTimeout(() => initializeUnifiedCalendar(), 100);
        }
    };
}

// Export functions
window.initializeUnifiedCalendar = initializeUnifiedCalendar;
window.navigateWeek = navigateWeek;
window.goToToday = goToToday;
window.toggleCalendarLayer = toggleCalendarLayer;
window.toggleEditMode = toggleEditMode;
window.refreshUnifiedCalendar = refreshUnifiedCalendar;
window.showManageAvailabilitySection = showManageAvailabilitySection;
window.hideManageAvailabilitySection = hideManageAvailabilitySection;

// ==================== NEW FEATURES FOR INTEGRATED CALENDAR ====================

let currentViewMode = 'week'; // 'week' or 'month'
let currentMonthStart = null;
let selectedWorkplaceId = 'all';
let isDragging = false;
let dragStartCell = null;
let dragSelection = [];

/**
 * Switch between week and month view
 */
function switchCalendarView(viewMode) {
    currentViewMode = viewMode;

    // Update button styles
    const weekBtn = document.getElementById('weekViewBtn');
    const monthBtn = document.getElementById('monthViewBtn');

    if (viewMode === 'week') {
        weekBtn.style.background = 'var(--color-accent)';
        weekBtn.style.color = 'white';
        monthBtn.style.background = 'transparent';
        monthBtn.style.border = '1px solid rgba(212, 175, 55, 0.3)';
        monthBtn.style.color = 'inherit';

        // Update navigation labels
        document.getElementById('prevPeriodBtn').innerHTML = '◀ Previous Week';
        document.getElementById('nextPeriodBtn').innerHTML = 'Next Week ▶';
    } else {
        monthBtn.style.background = 'var(--color-accent)';
        monthBtn.style.color = 'white';
        weekBtn.style.background = 'transparent';
        weekBtn.style.border = '1px solid rgba(212, 175, 55, 0.3)';
        weekBtn.style.color = 'inherit';

        // Set current month
        if (!currentMonthStart) {
            const today = new Date();
            currentMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
        }

        // Update navigation labels
        document.getElementById('prevPeriodBtn').innerHTML = '◀ Previous Month';
        document.getElementById('nextPeriodBtn').innerHTML = 'Next Month ▶';
    }

    refreshUnifiedCalendar();
}

/**
 * Navigate calendar view (week or month)
 */
function navigateCalendarView(direction) {
    if (currentViewMode === 'week') {
        navigateWeek(direction);
    } else {
        // Navigate month
        if (!currentMonthStart) {
            currentMonthStart = new Date();
            currentMonthStart.setDate(1);
        }
        currentMonthStart.setMonth(currentMonthStart.getMonth() + direction);
        refreshUnifiedCalendar();
    }
}

/**
 * Filter calendar by workplace
 */
function filterCalendarByWorkplace() {
    const select = document.getElementById('workplaceFilter');
    selectedWorkplaceId = select.value;
    refreshUnifiedCalendar();
}

/**
 * Load workplaces into the filter dropdown
 */
async function loadWorkplacesForFilter() {
    if (!window.currentSpecialistId) {
        console.error('[loadWorkplacesForFilter] No currentSpecialistId found!');
        return;
    }

    try {
        const response = await fetch(`/specialists/${window.currentSpecialistId}/workplaces`);

        if (response.ok) {
            const workplaces = await response.json();

            const select = document.getElementById('workplaceFilter');

            if (!select) {
                console.error('[loadWorkplacesForFilter] workplaceFilter element not found in DOM!');
                return;
            }

            // Clear existing options except "All"
            select.innerHTML = '<option value="all">All Calendars (Master View)</option>';

            // Assign colors and add workplace options
            // Note: API returns {workplace: {...}, role: ..., is_active: ...}
            workplaces.forEach((wp, index) => {
                const workplace = wp.workplace || wp; // Handle both nested and flat structures
                const workplaceId = workplace.id;
                const workplaceName = workplace.name;

                if (!workplaceColors[workplaceId]) {
                    workplaceColors[workplaceId] = CALENDAR_COLORS[index % CALENDAR_COLORS.length];
                }
                const option = document.createElement('option');
                option.value = workplaceId;
                option.textContent = workplaceName;
                select.appendChild(option);
            });

            // Update calendar legend (pass workplace objects)
            const workplaceObjects = workplaces.map(wp => wp.workplace || wp);
            updateCalendarLegend(workplaceObjects);
        } else {
            console.error('[loadWorkplacesForFilter] Response not OK:', response.status);
        }
    } catch (error) {
        console.error('[loadWorkplacesForFilter] Error loading workplaces:', error);
    }
}

/**
 * Update calendar legend showing workplace colors
 */
function updateCalendarLegend(workplaces) {
    const legendContainer = document.getElementById('calendarLegend');
    if (!legendContainer) return;

    if (workplaces.length === 0) {
        legendContainer.style.display = 'none';
        return;
    }

    legendContainer.style.display = 'flex';
    legendContainer.innerHTML = workplaces.map(wp => {
        const color = workplaceColors[wp.id] || CALENDAR_COLORS[0];
        return `
            <div style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; background: ${color.bg}; border: 1px solid ${color.border}; border-radius: 6px;">
                <div style="width: 12px; height: 12px; background: ${color.border}; border-radius: 2px;"></div>
                <span style="font-size: 0.75rem; color: ${color.text}; font-weight: 500;">${wp.name}</span>
            </div>
        `;
    }).join('');
}

/**
 * Enable drag-to-create new availability blocks
 */
function enableDragToCreate() {
    const calendar = document.getElementById('unifiedCalendar');
    if (!calendar) return;

    calendar.addEventListener('mousedown', handleDragStart);
    calendar.addEventListener('mousemove', handleDragMove);
    calendar.addEventListener('mouseup', handleDragEnd);
    calendar.addEventListener('mouseleave', handleDragEnd);
}

function handleDragStart(e) {
    // Try to find the cell from the event target first
    let cell = e.target.closest('.time-slot');
    
    // Fallback to month view
    if (!cell) {
        cell = e.target.closest('.month-day-cell');
    }
    
    if (!cell) {
        return;
    }

    // For week view
    if (currentViewMode === 'week') {
        if (!cell.dataset.day || !cell.dataset.hour) {
            return;
        }
        // Only allow dragging in empty slots
        if (cell.querySelector('.booking-block')) {
            return;
        }

        isDragging = true;
        dragStartCell = {
            day: parseInt(cell.dataset.day),
            hour: parseInt(cell.dataset.hour),
            minutes: parseInt(cell.dataset.minutes || 0),
            viewMode: 'week'
        };
        dragSelection = [dragStartCell];
        cell.classList.add('dragging-selection');
    }
    // For month view
    else if (currentViewMode === 'month') {
        if (!cell.dataset.date) return;

        isDragging = true;
        dragStartCell = {
            date: cell.dataset.date,
            element: cell,
            viewMode: 'month'
        };
        dragSelection = [dragStartCell];
        cell.classList.add('dragging-selection');
    }
}

function handleDragMove(e) {
    if (!isDragging) return;

    // Week view drag
    if (currentViewMode === 'week' && dragStartCell.viewMode === 'week') {
        const cell = e.target.closest('.time-slot');
        if (!cell || !cell.dataset.day || !cell.dataset.hour) return;

        const currentCell = {
            day: parseInt(cell.dataset.day),
            hour: parseInt(cell.dataset.hour),
            minutes: parseInt(cell.dataset.minutes || 0)
        };

        // Only allow dragging within the same day
        if (currentCell.day !== dragStartCell.day) return;

        // Clear previous selection highlights
        document.querySelectorAll('.dragging-selection').forEach(el => {
            el.classList.remove('dragging-selection');
        });

        // Calculate time range in minutes
        const startTotalMinutes = dragStartCell.hour * 60 + dragStartCell.minutes;
        const currentTotalMinutes = currentCell.hour * 60 + currentCell.minutes;
        const minMinutes = Math.min(startTotalMinutes, currentTotalMinutes);
        const maxMinutes = Math.max(startTotalMinutes, currentTotalMinutes);

        // Update selection - all quarter-hour slots in range
        dragSelection = [];
        for (let totalMinutes = minMinutes; totalMinutes <= maxMinutes; totalMinutes += 15) {
            const hour = Math.floor(totalMinutes / 60);
            const minutes = totalMinutes % 60;
            dragSelection.push({ day: currentCell.day, hour, minutes, viewMode: 'week' });

            // Highlight the cell
            const selector = `.time-slot[data-day="${currentCell.day}"][data-hour="${hour}"][data-minutes="${minutes}"]`;
            const slotEl = document.querySelector(selector);
            if (slotEl) {
                slotEl.classList.add('dragging-selection');
            }
        }
    }
    // Month view drag
    else if (currentViewMode === 'month' && dragStartCell.viewMode === 'month') {
        const cell = e.target.closest('.month-day-cell');
        if (!cell || !cell.dataset.date) return;

        // Clear previous selection highlights
        document.querySelectorAll('.dragging-selection').forEach(el => {
            el.classList.remove('dragging-selection');
        });

        // Get all day cells
        const allDayCells = Array.from(document.querySelectorAll('.month-day-cell'));
        const startDate = parseDateLocal(dragStartCell.date);
        const currentDate = parseDateLocal(cell.dataset.date);

        // Normalize to midnight for accurate comparison
        startDate.setHours(0, 0, 0, 0);
        currentDate.setHours(0, 0, 0, 0);

        const minDate = startDate < currentDate ? startDate : currentDate;
        const maxDate = startDate > currentDate ? startDate : currentDate;

        // Highlight all cells in range
        dragSelection = [];
        allDayCells.forEach(dayCell => {
            const cellDate = parseDateLocal(dayCell.dataset.date);
            cellDate.setHours(0, 0, 0, 0);
            if (cellDate >= minDate && cellDate <= maxDate) {
                dayCell.classList.add('dragging-selection');
                dragSelection.push({
                    date: dayCell.dataset.date,
                    element: dayCell,
                    viewMode: 'month'
                });
            }
        });
    }
}

function handleDragEnd(e) {
    if (!isDragging) return;

    isDragging = false;

    // Remove all selection highlights
    document.querySelectorAll('.dragging-selection').forEach(el => {
        el.classList.remove('dragging-selection');
    });

    // If selection is valid, show creation modal
    if (dragSelection.length > 0) {
        if (dragStartCell.viewMode === 'week') {
            // Week view - create time-based availability
            const day = dragSelection[0].day;
            const startTotalMinutes = Math.min(...dragSelection.map(s => s.hour * 60 + s.minutes));
            const endTotalMinutes = Math.max(...dragSelection.map(s => s.hour * 60 + s.minutes)) + 15;

            const startHour = Math.floor(startTotalMinutes / 60);
            const startMinutes = startTotalMinutes % 60;
            const endHour = Math.floor(endTotalMinutes / 60);
            const endMinutes = endTotalMinutes % 60;

            showAvailabilityModal({
                type: 'single-day',
                dayOfWeek: day,
                startHour,
                startMinutes,
                endHour,
                endMinutes
            });
        } else if (dragStartCell.viewMode === 'month') {
            // Month view - create multi-day availability
            const dates = dragSelection.map(s => parseDateLocal(s.date)).sort((a, b) => a - b);
            const startDate = dates[0];
            const endDate = dates[dates.length - 1];

            showAvailabilityModal({
                type: 'multi-day',
                startDate,
                endDate,
                days: dates
            });
        }
    }

    dragSelection = [];
    dragStartCell = null;
}

/**
 * Show availability creation modal with options
 */
function showAvailabilityModal(selectionData) {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    // Get available workplaces for dropdown - FRESH from the current DOM state
    const workplaceSelect = document.getElementById('workplaceFilter');
    if (!workplaceSelect) {
        console.error('Workplace filter dropdown not found');
        return;
    }

    const workplaceOptions = Array.from(workplaceSelect.options)
        .filter(opt => opt.value !== 'all')
        .map(opt => `<option value="${opt.value}" ${selectionData.preselectedWorkplaceId && opt.value == selectionData.preselectedWorkplaceId ? 'selected' : ''}>${opt.textContent}</option>`)
        .join('');

    // If no workplaces exist, show workplace creation form first
    if (!workplaceOptions || workplaceOptions.trim() === '') {
        showAddWorkplaceModal(selectionData);
        return;
    }

    if (selectionData.type === 'single-day') {
        // Single day in week view - show time-based options
        const dayName = days[selectionData.dayOfWeek];
        const startTime = formatTimeWithMinutes(selectionData.startHour, selectionData.startMinutes);
        const endTime = formatTimeWithMinutes(selectionData.endHour, selectionData.endMinutes);

        const modalHTML = `
            <div id="availabilityModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;">
                <div style="background: white; border-radius: 16px; padding: 32px; max-width: 500px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                    <h3 style="margin: 0 0 24px 0; color: #1f2937; font-size: 1.5rem;">Create Availability Block</h3>
                    
                    <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
                        <div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 8px;">Selection:</div>
                        <div style="color: #1f2937; font-weight: 600;">${dayName}</div>
                        <div style="color: #1f2937;">${startTime} - ${endTime}</div>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">📍 Calendar (Workplace) *</label>
                        <select id="modalWorkplaceSelect" required style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem;" onchange="if(this.value==='__add_new__'){closeAvailabilityModal();showAddWorkplaceModal(${JSON.stringify(selectionData).replace(/"/g, '&quot;')})}">
                            <option value="">Select a workplace...</option>
                            ${workplaceOptions}
                            <option value="__add_new__" style="border-top: 2px solid #e5e7eb; margin-top: 8px; font-weight: 600; color: #D4AF37;">+ Add New Workplace</option>
                        </select>
                        <div style="margin-top: 6px; font-size: 0.75rem; color: #6b7280;">Each workplace is a separate calendar</div>
                    </div>
                    
                    <div style="margin-bottom: 24px;">
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">Recurrence:</label>
                        <select id="recurrenceType" style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem;">
                            <option value="weekly">Every ${dayName}</option>
                            <option value="once">Just this week</option>
                            <option value="custom">Custom days...</option>
                        </select>
                    </div>
                    
                    <div id="lookaheadSection" style="margin-bottom: 24px;">
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">Pre-create availability for:</label>
                        <select id="lookaheadWeeks" style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem;">
                            <option value="4">4 weeks ahead</option>
                            <option value="8">8 weeks ahead</option>
                            <option value="12" selected>12 weeks ahead (recommended)</option>
                        </select>
                        <div style="margin-top: 6px; font-size: 0.75rem; color: #6b7280;">Instances automatically extend as days pass</div>
                    </div>
                    
                    <div id="customDaysSection" style="display: none; margin-bottom: 24px;">
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">Select Days:</label>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${days.map((day, idx) => `
                                <label style="display: flex; align-items: center; gap: 4px; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; ${idx === selectionData.dayOfWeek ? 'background: #fef3c7; border-color: #D4AF37;' : ''}">
                                    <input type="checkbox" name="customDay" value="${idx}" style="accent-color: #D4AF37;">
                                    <span style="font-size: 0.875rem;">${day.slice(0, 3)}</span>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 12px; margin-top: 32px;">
                        <button onclick="closeAvailabilityModal()" style="flex: 1; padding: 12px; background: #f3f4f6; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; color: #374151; font-weight: 500;">Cancel</button>
                        <button onclick="createAvailabilityFromModal(${JSON.stringify(selectionData).replace(/"/g, '&quot;')})" style="flex: 1; padding: 12px; background: linear-gradient(135deg, #D4AF37 0%, #F7E7AD 100%); border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; color: #1f2937; font-weight: 600;">Create</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Add event listener for recurrence type change
        const recurrenceSelect = document.getElementById('recurrenceType');
        const customSection = document.getElementById('customDaysSection');
        const lookaheadSection = document.getElementById('lookaheadSection');
        
        recurrenceSelect.addEventListener('change', function () {
            const isRecurring = this.value !== 'once';
            customSection.style.display = this.value === 'custom' ? 'block' : 'none';
            lookaheadSection.style.display = isRecurring ? 'block' : 'none';
            
            // When switching to custom, ensure the originally selected day is checked
            if (this.value === 'custom') {
                // Small delay to ensure DOM is ready
                setTimeout(() => {
                    const originalDayCheckbox = customSection.querySelector(`input[name="customDay"][value="${selectionData.dayOfWeek}"]`);
                    console.log('[DEBUG] Looking for checkbox with value:', selectionData.dayOfWeek);
                    console.log('[DEBUG] Found checkbox:', originalDayCheckbox);
                    if (originalDayCheckbox) {
                        console.log('[DEBUG] Current checked state:', originalDayCheckbox.checked);
                        originalDayCheckbox.checked = true;
                        console.log('[DEBUG] After setting:', originalDayCheckbox.checked);
                    }
                }, 10);
            }
        });

    } else if (selectionData.type === 'multi-day') {
        // Multi-day in month view
        const dayCount = selectionData.days.length;
        const startDateStr = formatDate(selectionData.startDate, 'long');
        const endDateStr = formatDate(selectionData.endDate, 'long');

        const modalHTML = `
            <div id="availabilityModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;">
                <div style="background: white; border-radius: 16px; padding: 32px; max-width: 500px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                    <h3 style="margin: 0 0 24px 0; color: #1f2937; font-size: 1.5rem;">Create Availability Block</h3>
                    
                    <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
                        <div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 8px;">Selection:</div>
                        <div style="color: #1f2937; font-weight: 600;">${dayCount} day${dayCount > 1 ? 's' : ''}</div>
                        <div style="color: #1f2937;">${startDateStr} - ${endDateStr}</div>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">📍 Calendar (Workplace) *</label>
                        <select id="modalWorkplaceSelect" required style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem;" onchange="if(this.value==='__add_new__'){closeAvailabilityModal();showAddWorkplaceModal(${JSON.stringify(selectionData).replace(/"/g, '&quot;')})}">
                            <option value="">Select a workplace...</option>
                            ${workplaceOptions}
                            <option value="__add_new__" style="border-top: 2px solid #e5e7eb; margin-top: 8px; font-weight: 600; color: #D4AF37;">+ Add New Workplace</option>
                        </select>
                        <div style="margin-top: 6px; font-size: 0.75rem; color: #6b7280;">Each workplace is a separate calendar</div>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">Start Time:</label>
                        <select id="multiDayStartTime" style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem;">
                            ${generateTimeOptions(6, 22)}
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 24px;">
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">End Time:</label>
                        <select id="multiDayEndTime" style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem;">
                            ${generateTimeOptions(6, 22, 18)}
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 24px;">
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">Recurrence:</label>
                        <select id="recurrenceType" style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem;">
                            <option value="weekly">Weekly (every ${days[selectionData.startDate.getDay() === 0 ? 6 : selectionData.startDate.getDay() - 1]})</option>
                            <option value="once">Just these specific dates</option>
                        </select>
                    </div>
                    
                    <div style="display: flex; gap: 12px; margin-top: 32px;">
                        <button onclick="closeAvailabilityModal()" style="flex: 1; padding: 12px; background: #f3f4f6; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; color: #374151; font-weight: 500;">Cancel</button>
                        <button onclick="createMultiDayAvailabilityFromModal(${JSON.stringify(selectionData).replace(/"/g, '&quot;')})" style="flex: 1; padding: 12px; background: linear-gradient(135deg, #D4AF37 0%, #F7E7AD 100%); border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; color: #1f2937; font-weight: 600;">Create</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
}

/**
 * Generate time options for select dropdown
 */
function generateTimeOptions(startHour, endHour, selectedHour = 9) {
    let options = '';
    for (let hour = startHour; hour <= endHour; hour++) {
        for (let minutes of [0, 15, 30, 45]) {
            const value = `${hour}:${minutes.toString().padStart(2, '0')}`;
            const label = formatTimeWithMinutes(hour, minutes);
            const selected = (hour === selectedHour && minutes === 0) ? 'selected' : '';
            options += `<option value="${value}" ${selected}>${label}</option>`;
        }
    }
    return options;
}

/**
 * Close availability modal
 */
function closeAvailabilityModal() {
    const modal = document.getElementById('availabilityModal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Show add workplace modal
 */
function showAddWorkplaceModal(selectionData) {
    const modalHTML = `
        <div id="availabilityModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 16px; padding: 32px; max-width: 500px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 1.5rem;">Add Your First Workplace</h3>
                <p style="margin: 0 0 24px 0; color: #6b7280; font-size: 0.875rem;">Before creating availability, you need at least one workplace calendar.</p>
                
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">Workplace Name *</label>
                    <input type="text" id="newWorkplaceName" required placeholder="e.g., Downtown Salon" style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem; box-sizing: border-box;">
                </div>
                
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">Address *</label>
                    <input type="text" id="newWorkplaceAddress" required placeholder="Street address" style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem; box-sizing: border-box;">
                </div>
                
                <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 12px; margin-bottom: 20px;">
                    <div>
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">City *</label>
                        <input type="text" id="newWorkplaceCity" required placeholder="City" style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem; box-sizing: border-box;">
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">ZIP *</label>
                        <input type="text" id="newWorkplaceZip" required placeholder="12345" style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem; box-sizing: border-box;">
                    </div>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">Your Role *</label>
                    <select id="newWorkplaceRole" required style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem;">
                        <option value="">Select your role...</option>
                        <option value="Owner">Owner</option>
                        <option value="Employee">Employee</option>
                    </select>
                </div>
                
                <div style="margin-bottom: 24px;">
                    <label style="display: block; margin-bottom: 8px; color: #374151; font-weight: 500;">Start Date *</label>
                    <input type="date" id="newWorkplaceStartDate" required style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1rem; box-sizing: border-box;">
                </div>
                
                <div id="workplaceErrorMsg" style="display: none; padding: 12px; background: #fee2e2; border: 1px solid #ef4444; border-radius: 8px; color: #991b1b; margin-bottom: 16px; font-size: 0.875rem;"></div>
                
                <div style="display: flex; gap: 12px; margin-top: 32px;">
                    <button onclick="closeAvailabilityModal()" style="flex: 1; padding: 12px; background: #f3f4f6; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; color: #374151; font-weight: 500;">Cancel</button>
                    <button onclick="createWorkplaceFromModal(${JSON.stringify(selectionData).replace(/"/g, '&quot;')})" style="flex: 1; padding: 12px; background: linear-gradient(135deg, #D4AF37 0%, #F7E7AD 100%); border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; color: #1f2937; font-weight: 600;">Create & Continue</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Set today as default start date (use local timezone)
    const today = formatDateLocal(new Date());
    document.getElementById('newWorkplaceStartDate').value = today;
}

/**
 * Create workplace from modal and continue to availability creation
 */
async function createWorkplaceFromModal(selectionData) {
    const name = document.getElementById('newWorkplaceName').value.trim();
    const address = document.getElementById('newWorkplaceAddress').value.trim();
    const city = document.getElementById('newWorkplaceCity').value.trim();
    const zip = document.getElementById('newWorkplaceZip').value.trim();
    const role = document.getElementById('newWorkplaceRole').value;
    const startDate = document.getElementById('newWorkplaceStartDate').value;

    const errorMsg = document.getElementById('workplaceErrorMsg');

    // Validate required fields
    if (!name || !address || !city || !zip || !role || !startDate) {
        errorMsg.textContent = 'Please fill in all required fields';
        errorMsg.style.display = 'block';
        return;
    }

    if (!window.currentSpecialistId) {
        errorMsg.textContent = 'Specialist ID not found. Please refresh and try again.';
        errorMsg.style.display = 'block';
        return;
    }

    try {
        // Step 1: Create the workplace
        const workplaceResponse = await fetch('/workplaces/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                address: address,
                city: city,
                zip_code: zip,
                country: 'US'
            })
        });

        if (!workplaceResponse.ok) {
            const error = await workplaceResponse.json();
            errorMsg.textContent = error.detail || 'Failed to create workplace';
            errorMsg.style.display = 'block';
            return;
        }

        const newWorkplace = await workplaceResponse.json();

        // Step 2: Associate the specialist with the workplace
        const associationResponse = await fetch(`/specialists/${window.currentSpecialistId}/workplaces/${newWorkplace.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                role: role,
                start_date: startDate,
                is_active: true
            })
        });

        if (!associationResponse.ok) {
            const error = await associationResponse.json();
            // Workplace was created but association failed - show warning
            errorMsg.textContent = `Workplace created but failed to associate: ${error.detail || 'Unknown error'}`;
            errorMsg.style.display = 'block';
            return;
        }

        // Close the workplace modal
        closeAvailabilityModal();

        // Reload workplaces to populate the filter - WAIT for this to complete
        try {
            await loadWorkplacesForFilter();
        } catch (err) {
            console.error('[createWorkplaceFromModal] Error in loadWorkplacesForFilter:', err);
        }

        // Verify the workplace was added to the DOM before proceeding
        const workplaceSelect = document.getElementById('workplaceFilter');
        const workplaceInDOM = workplaceSelect && Array.from(workplaceSelect.options).some(opt => opt.value == newWorkplace.id);

        if (!workplaceInDOM) {
            console.error('[createWorkplaceFromModal] Workplace was created but not found in filter dropdown. Reloading...');
            // Force a complete refresh and try again
            await loadWorkplacesForFilter();
        }

        // Show success message
        const successMsg = document.createElement('div');
        successMsg.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 10001;
            font-weight: 500;
        `;
        successMsg.textContent = `✅ Workplace "${name}" created successfully!`;
        document.body.appendChild(successMsg);

        setTimeout(() => {
            successMsg.remove();
        }, 3000);

        // Store the new workplace ID to pre-select it in the modal
        const previousSelection = selectionData;
        previousSelection.preselectedWorkplaceId = newWorkplace.id;

        // Show availability modal NOW (workplaces are already loaded above)
        showAvailabilityModal(previousSelection);

    } catch (error) {
        console.error('[createWorkplaceFromModal] Error creating workplace:', error);
        errorMsg.textContent = 'Network error. Please try again.';
        errorMsg.style.display = 'block';
    }
}

/**
 * Create availability from modal (single day)
 */
async function createAvailabilityFromModal(selectionData) {
    const workplaceSelect = document.getElementById('modalWorkplaceSelect');
    const workplaceId = workplaceSelect.value;

    if (!workplaceId) {
        alert('Please select a workplace (calendar) for this availability block.');
        workplaceSelect.focus();
        workplaceSelect.style.border = '2px solid #ef4444';
        return;
    }

    const recurrenceType = document.getElementById('recurrenceType').value;
    const lookaheadWeeks = parseInt(document.getElementById('lookaheadWeeks')?.value || 12);
    let daysToCreate = [];

    if (recurrenceType === 'weekly') {
        daysToCreate = [selectionData.dayOfWeek];
    } else if (recurrenceType === 'once') {
        // For "once" we'll still create as recurring but could be enhanced later
        daysToCreate = [selectionData.dayOfWeek];
    } else if (recurrenceType === 'custom') {
        const checkedBoxes = document.querySelectorAll('input[name="customDay"]:checked');
        daysToCreate = Array.from(checkedBoxes).map(cb => parseInt(cb.value));
    }

    if (daysToCreate.length === 0) {
        alert('Please select at least one day');
        return;
    }

    const startDecimal = selectionData.startHour + (selectionData.startMinutes / 60);
    const endDecimal = selectionData.endHour + (selectionData.endMinutes / 60);

    closeAvailabilityModal();

    // Show loading message
    const loadingMsg = document.createElement('div');
    loadingMsg.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10001;
        font-weight: 500;
    `;
    loadingMsg.textContent = '⏳ Creating availability...';
    document.body.appendChild(loadingMsg);

    let successCount = 0;
    let failCount = 0;

    // Send ONE request with ALL days to ensure they share the same recurring_event_id
    try {
        // Format times as HH:MM
        const startTimeStr = `${String(selectionData.startHour).padStart(2, '0')}:${String(selectionData.startMinutes || 0).padStart(2, '0')}`;
        const endTimeStr = `${String(selectionData.endHour).padStart(2, '0')}:${String(selectionData.endMinutes || 0).padStart(2, '0')}`;
        
        // Use the current week start as the base start_date for recurrence
        const startDateForRecurrence = formatDateLocal(new Date(currentWeekStart));

        const requestBody = {
            workplace_id: parseInt(workplaceId),
            recurrence_type: 'weekly',
            days_of_week: daysToCreate, // Send ALL days in one request
            start_time: startTimeStr,
            end_time: endTimeStr,
            start_date: startDateForRecurrence,
            end_date: null,
            lookahead_weeks: lookaheadWeeks
        };

        const response = await fetch(`/specialist/${window.currentSpecialistId}/recurring-schedule`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });

        if (response.ok) {
            const result = await response.json();
            successCount = 1;
        } else {
            failCount = 1;
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            console.error(`[createAvailabilityFromModal] Failed (${response.status}):`, errorData);
            alert(`Failed to create availability: ${errorData.detail || 'Unknown error'}`);
        }
    } catch (error) {
        failCount = 1;
        console.error(`[createAvailabilityFromModal] Error creating availability:`, error);
        alert(`Error creating availability: ${error.message}`);
    }

    // Remove loading message
    loadingMsg.remove();

    // Show result message
    const resultMsg = document.createElement('div');
    resultMsg.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, ${successCount > 0 ? '#10b981 0%, #059669' : '#ef4444 0%, #dc2626'} 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10001;
        font-weight: 500;
    `;

    if (successCount > 0 && failCount === 0) {
        resultMsg.textContent = `✅ ${successCount} availability block${successCount > 1 ? 's' : ''} created!`;
    } else if (successCount > 0 && failCount > 0) {
        resultMsg.textContent = `⚠️ Created ${successCount}, failed ${failCount}`;
    } else {
        resultMsg.textContent = `❌ Failed to create availability blocks`;
    }

    document.body.appendChild(resultMsg);
    setTimeout(() => resultMsg.remove(), 3000);

    // Refresh the calendar to show new availability (instances are pre-created synchronously)
    await refreshUnifiedCalendar();

    // Also refresh the recurring schedules list if it exists AND the container is present
    if (typeof window.loadRecurringSchedules === 'function' && document.getElementById('recurringSchedulesCalendar')) {
        window.loadRecurringSchedules();
    }
}

/**
 * Create multi-day availability from modal
 */
async function createMultiDayAvailabilityFromModal(selectionData) {
    const workplaceSelect = document.getElementById('modalWorkplaceSelect');
    const workplaceId = workplaceSelect.value;

    if (!workplaceId) {
        alert('Please select a workplace (calendar) for this availability block.');
        workplaceSelect.focus();
        workplaceSelect.style.border = '2px solid #ef4444';
        return;
    }

    const startTime = document.getElementById('multiDayStartTime').value;
    const endTime = document.getElementById('multiDayEndTime').value;
    const recurrenceType = document.getElementById('recurrenceType').value;

    const [startHour, startMinutes] = startTime.split(':').map(Number);
    const [endHour, endMinutes] = endTime.split(':').map(Number);

    const startDecimal = startHour + (startMinutes / 60);
    const endDecimal = endHour + (endMinutes / 60);

    if (startDecimal >= endDecimal) {
        alert('End time must be after start time');
        return;
    }

    closeAvailabilityModal();

    // Show loading message
    const loadingMsg = document.createElement('div');
    loadingMsg.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10001;
        font-weight: 500;
    `;
    loadingMsg.textContent = '⏳ Creating availability...';
    document.body.appendChild(loadingMsg);

    // Get unique days of week from selection
    const daysOfWeek = [...new Set(selectionData.days.map(date => {
        const day = date.getDay();
        return day === 0 ? 6 : day - 1; // Convert to Monday=0 format
    }))];

    let successCount = 0;
    let failCount = 0;

    // Create availability for each day of week
    for (const day of daysOfWeek) {
        try {
            // Format times as HH:MM
            const startTimeStr = `${String(startHour).padStart(2, '0')}:${String(startMinutes).padStart(2, '0')}`;
            const endTimeStr = `${String(endHour).padStart(2, '0')}:${String(endMinutes).padStart(2, '0')}`;

            // Use the current week start as the base start_date for recurrence
            // This ensures instances are generated for the week being viewed
            // Use local timezone formatting to avoid UTC offset issues
            const startDateForRecurrence = formatDateLocal(new Date(currentWeekStart));

            const requestBody = {
                workplace_id: parseInt(workplaceId),
                recurrence_type: 'weekly',
                days_of_week: [day],
                start_time: startTimeStr,
                end_time: endTimeStr,
                start_date: startDateForRecurrence, // Use current week start, not today
                end_date: null // No end date for indefinite recurrence
            };

            const response = await fetch(`/specialist/${window.currentSpecialistId}/recurring-schedule`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            if (response.ok) {
                const result = await response.json();
                successCount++;
            } else {
                failCount++;
                const error = await response.json();
                console.error(`[createMultiDayAvailabilityFromModal] Failed for day ${day} (${response.status}):`, error);
            }
        } catch (error) {
            failCount++;
            console.error(`[createMultiDayAvailabilityFromModal] Error creating availability for day ${day}:`, error);
        }
    }

    // Remove loading message
    loadingMsg.remove();

    // Show result message
    const resultMsg = document.createElement('div');
    resultMsg.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, ${successCount > 0 ? '#10b981 0%, #059669' : '#ef4444 0%, #dc2626'} 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10001;
        font-weight: 500;
    `;

    if (successCount > 0 && failCount === 0) {
        resultMsg.textContent = `✅ ${successCount} availability block${successCount > 1 ? 's' : ''} created!`;
    } else if (successCount > 0 && failCount > 0) {
        resultMsg.textContent = `⚠️ Created ${successCount}, failed ${failCount}`;
    } else {
        resultMsg.textContent = `❌ Failed to create availability blocks`;
    }

    document.body.appendChild(resultMsg);
    setTimeout(() => resultMsg.remove(), 3000);

    // Refresh the calendar to show new availability
    await refreshUnifiedCalendar();

    // Also refresh the recurring schedules list if it exists AND the container is present
    if (typeof window.loadRecurringSchedules === 'function' && document.getElementById('recurringSchedulesCalendar')) {
        window.loadRecurringSchedules();
    }
}


/**
 * Show modal to edit or delete a recurring schedule
 */
function showScheduleEditModal(schedule) {
    // Get schedule details - now using instance_id and recurring_event_id
    const instanceId = schedule.instance_id;
    const recurringEventId = schedule.recurring_event_id;
    const workplaceName = schedule.workplace_name || 'Personal';
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const dayName = days[schedule.day];
    const isDaily = schedule.recurrence_type === 'daily';

    // Format the actual date for display (parse as local date to avoid timezone shift)
    const actualDate = schedule.date ? parseDateLocal(schedule.date).toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    }) : dayName;

    // Check if modal exists, if not create it
    let modal = document.getElementById('availabilityModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'availabilityModal';
        modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 10000; display: flex; align-items: center; justify-content: center;';
        document.body.appendChild(modal);
    }

    // For daily schedules, show different messaging
    const scheduleTypeLabel = isDaily ? 'Daily Schedule (All Days)' : `Weekly Schedule`;

    // Create modal content
    modal.innerHTML = `
        <div onclick="event.stopPropagation()" style="background: white; border-radius: 16px; padding: 32px; max-width: 600px; width: 90%; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);">
            <h2 id="availabilityModalTitle" style="margin: 0 0 24px 0; font-size: 1.5rem; font-weight: 700; color: #1f2937;">Edit Recurring Schedule</h2>
            
            <div id="availabilityModalContent">
                <div style="display: flex; flex-direction: column; gap: 20px;">
                    <!-- Schedule Info -->
                    <div style="background: #f9fafb; padding: 16px; border-radius: 8px; border: 1px solid #e5e7eb;">
                        <div style="font-size: 0.875rem; color: #6b7280; margin-bottom: 8px;">Current Schedule</div>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                            <div><strong>Type:</strong> ${scheduleTypeLabel}</div>
                            <div><strong>Date:</strong> ${actualDate}</div>
                            <div><strong>Workplace:</strong> ${workplaceName}</div>
                            <div><strong>Time:</strong> ${formatTime(schedule.start_time)} - ${formatTime(schedule.end_time)}</div>
                            <div style="font-size: 0.875rem; color: #6b7280;"><strong>Instance ID:</strong> ${instanceId}</div>
                        </div>
                    </div>
                    
                    <!-- Edit Form -->
                    <div style="display: flex; flex-direction: column; gap: 16px;">
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #374151;">Start Time</label>
                            <input type="time" id="editStartTime" value="${schedule.start_time}" 
                                style="width: 100%; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem;">
                        </div>
                        
                        <div>
                            <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #374151;">End Time</label>
                            <input type="time" id="editEndTime" value="${schedule.end_time}" 
                                style="width: 100%; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 1rem;">
                        </div>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 12px;">
                        <button onclick="closeAvailabilityModal()" 
                            style="flex: 1; min-width: 120px; padding: 12px; background: #f3f4f6; border: none; border-radius: 8px; font-size: 0.95rem; cursor: pointer; color: #374151; font-weight: 500;">
                            Cancel
                        </button>
                        <button onclick="deleteSingleInstance(${instanceId}, '${dayName}')" 
                            style="flex: 1; min-width: 140px; padding: 12px; background: #f59e0b; border: none; border-radius: 8px; font-size: 0.95rem; cursor: pointer; color: white; font-weight: 600;">
                            🗑️ Delete This ${dayName}
                        </button>
                        <button onclick="deleteScheduleSeries('${recurringEventId}')" 
                            style="flex: 1; min-width: 140px; padding: 12px; background: #dc2626; border: none; border-radius: 8px; font-size: 0.95rem; cursor: pointer; color: white; font-weight: 600;">
                            🗑️ Delete All Days
                        </button>
                        <button onclick="updateScheduleInstance(${instanceId})" 
                            style="flex: 1; min-width: 140px; padding: 12px; background: linear-gradient(135deg, #D4AF37 0%, #F7E7AD 100%); border: none; border-radius: 8px; font-size: 0.95rem; cursor: pointer; color: #1f2937; font-weight: 600;">
                            💾 Save Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Show modal
    modal.style.display = 'flex';

    // Close on background click
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeAvailabilityModal();
        }
    };
}

/**
 * Update a calendar instance's time (simplified - uses instance_id)
 */
async function updateScheduleInstance(instanceId) {
    const startTime = document.getElementById('editStartTime').value;
    const endTime = document.getElementById('editEndTime').value;

    if (!startTime || !endTime) {
        showToast('⚠️ Please enter both start and end times', 'error');
        return;
    }

    if (startTime >= endTime) {
        showToast('⚠️ End time must be after start time', 'error');
        return;
    }

    showToast('⏳ Updating schedule...', 'info');

    try {
        // Note: For now we'll use the old endpoint since updating needs base_event_id
        // In a full implementation, you'd add a PUT /calendar-event/{instance_id} endpoint
        // For this demo, we'll keep the existing update logic
        showToast('⚠️ Update feature coming soon - please delete and recreate for now', 'info');

        // TODO: Implement PUT /calendar-event/{instance_id} endpoint

    } catch (error) {
        console.error('[updateScheduleInstance] Error:', error);
        showToast(`❌ Error: ${error.message}`, 'error');
    }
}

/**
 * Delete a specific calendar instance by its database ID
 */
async function deleteScheduleInstance(instanceId, dayName) {
    const confirmed = confirm(
        `Delete this specific ${dayName} occurrence?\n\n` +
        `⚠️ This will only remove this one instance. ` +
        `Other days in the series will remain unchanged.`
    );

    if (!confirmed) return;

    showToast('⏳ Deleting instance...', 'info');

    try {
        const response = await fetch(`/calendar-event/${instanceId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            let errorMessage = 'Failed to delete instance';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
                console.error('[deleteScheduleInstance] Server error:', error);
            } catch (e) {
                const errorText = await response.text();
                console.error('[deleteScheduleInstance] Server response:', errorText);
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();

        showToast('✅ Instance deleted successfully!', 'success');
        closeAvailabilityModal();
        await refreshUnifiedCalendar();

    } catch (error) {
        console.error('[deleteScheduleInstance] Error:', error);
        showToast(`❌ Error: ${error.message}`, 'error');
    }
}

/**
 * Delete a single calendar instance (just this one occurrence)
 */
async function deleteSingleInstance(instanceId, dayName) {
    const confirmed = confirm(
        `Delete this ${dayName} occurrence only?\n\n` +
        `This will only remove this single instance. Other days will remain unchanged.`
    );

    if (!confirmed) return;

    showToast('⏳ Deleting instance...', 'info');

    try {
        const response = await fetch(`/calendar-event/${instanceId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            let errorMessage = 'Failed to delete instance';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
                console.error('[deleteSingleInstance] Server error:', error);
            } catch (e) {
                const errorText = await response.text();
                console.error('[deleteSingleInstance] Server response:', errorText);
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();

        showToast('✅ Instance deleted successfully!', 'success');
        closeAvailabilityModal();
        await refreshUnifiedCalendar();

    } catch (error) {
        console.error('[deleteSingleInstance] Error:', error);
        showToast(`❌ Error: ${error.message}`, 'error');
    }
}

/**
 * Delete entire recurring schedule series by recurring_event_id
 */
async function deleteScheduleSeries(recurringEventId) {
    const confirmed = confirm(
        `Delete ALL instances from this recurring schedule?\n\n` +
        `⚠️ This will remove ALL availability blocks from ALL days in this series ` +
        `(Monday, Wednesday, etc.). This action cannot be undone.\n\n` +
        `Are you sure you want to delete the entire schedule?`
    );

    if (!confirmed) return;

    showToast('⏳ Deleting all instances...', 'info');

    try {
        const response = await fetch(`/calendar-event/series/${recurringEventId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete schedule series');
        }

        const result = await response.json();

        showToast(`✅ Deleted ${result.deleted_count} events from series!`, 'success');
        closeAvailabilityModal();
        await refreshUnifiedCalendar();

    } catch (error) {
        console.error('[deleteScheduleSeries] Error:', error);
        showToast(`❌ Error: ${error.message}`, 'error');
    }
}

// Legacy functions kept for backward compatibility
async function updateSchedule(scheduleId, dayOfWeek) {
    console.warn('[updateSchedule] Legacy function called - redirecting to updateScheduleInstance');
    await updateScheduleInstance(scheduleId);
}

async function deleteSchedule(scheduleId, dayOfWeek, dayName) {
    console.warn('[deleteSchedule] Legacy function called - redirecting to deleteScheduleInstance');
    await deleteScheduleInstance(scheduleId, dayName);
}

/**
 * Prompt user to create new availability block (legacy - keeping for compatibility)
 */
async function promptCreateAvailabilityBlock(dayOfWeek, startHour, endHour, startMinutes = 0, endMinutes = 0) {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const dayName = days[dayOfWeek];

    const startTime = formatTimeWithMinutes(startHour, startMinutes);
    const endTime = formatTimeWithMinutes(endHour, endMinutes);

    const confirm = window.confirm(
        `Create availability block?\n\n` +
        `Day: ${dayName}\n` +
        `Time: ${startTime} - ${endTime}\n\n` +
        `This will add a recurring availability block to your schedule.`
    );

    if (!confirm) return;

    // Get workplace selection
    const workplaceId = selectedWorkplaceId === 'all' ? null : selectedWorkplaceId;

    if (!workplaceId) {
        alert('Please select a workplace from the filter dropdown before creating availability blocks.');
        return;
    }

    // Convert to decimal hours for API (e.g., 9:15 = 9.25, 9:30 = 9.5, 9:45 = 9.75)
    const startDecimal = startHour + (startMinutes / 60);
    const endDecimal = endHour + (endMinutes / 60);

    // Create the availability block via API
    try {
        const response = await fetch('/recurring-schedules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                specialist_id: window.currentSpecialistId,
                workplace_id: workplaceId,
                day_of_week: dayOfWeek,
                start_hour: startDecimal,
                end_hour: endDecimal
            })
        });

        if (response.ok) {
            alert('✅ Availability block created successfully!');
            refreshUnifiedCalendar();
            // Also refresh the drag-and-drop editor
            if (typeof window.loadRecurringSchedules === 'function') {
                window.loadRecurringSchedules();
            }
        } else {
            const error = await response.json();
            alert(`❌ Error: ${error.detail || 'Failed to create availability block'}`);
        }
    } catch (error) {
        console.error('Error creating availability block:', error);
        alert('❌ Failed to create availability block. Please try again.');
    }
}

/**
 * Format time with minutes for display
 */
function formatTimeWithMinutes(hour, minutes) {
    const displayHour = hour === 0 ? 12 : (hour > 12 ? hour - 12 : hour);
    const period = hour >= 12 ? 'PM' : 'AM';
    const minutesStr = minutes === 0 ? '00' : minutes.toString().padStart(2, '0');
    return `${displayHour}:${minutesStr} ${period}`;
}

/**
 * Format hour for display (backward compatibility)
 */
function formatHour(hour) {
    if (hour === 0) return '12 AM';
    if (hour < 12) return `${hour} AM`;
    if (hour === 12) return '12 PM';
    return `${hour - 12} PM`;
}

// Export new functions
window.switchCalendarView = switchCalendarView;
window.navigateCalendarView = navigateCalendarView;
window.filterCalendarByWorkplace = filterCalendarByWorkplace;
window.loadWorkplacesForFilter = loadWorkplacesForFilter;
window.updateCalendarLegend = updateCalendarLegend;
window.showAvailabilityModal = showAvailabilityModal;
window.showAddWorkplaceModal = showAddWorkplaceModal;
window.createWorkplaceFromModal = createWorkplaceFromModal;
window.closeAvailabilityModal = closeAvailabilityModal;
window.createAvailabilityFromModal = createAvailabilityFromModal;
window.createMultiDayAvailabilityFromModal = createMultiDayAvailabilityFromModal;
window.showScheduleEditModal = showScheduleEditModal;
window.updateSchedule = updateSchedule;
window.deleteSchedule = deleteSchedule;
window.deleteScheduleSeries = deleteScheduleSeries;

/**
 * Show a toast notification message
 */
function showToast(message, type = 'info') {
    // Remove any existing toasts
    const existingToast = document.getElementById('calendar-toast');
    if (existingToast) {
        existingToast.remove();
    }

    const colors = {
        success: { bg: '#10b981', border: '#059669' },
        error: { bg: '#ef4444', border: '#dc2626' },
        info: { bg: '#3b82f6', border: '#2563eb' },
        warning: { bg: '#f59e0b', border: '#d97706' }
    };

    const color = colors[type] || colors.info;

    const toast = document.createElement('div');
    toast.id = 'calendar-toast';
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${color.bg};
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        border: 2px solid ${color.border};
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        font-size: 0.95rem;
        font-weight: 500;
        animation: slideIn 0.3s ease;
        max-width: 400px;
    `;

    toast.textContent = message;
    document.body.appendChild(toast);

    // Auto-dismiss after 3 seconds unless it's a loading message
    if (!message.includes('⏳')) {
        setTimeout(() => {
            if (toast && toast.parentNode) {
                toast.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }
        }, 3000);
    }
}

// Add toast animations to page if they don't exist
if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style');
    style.id = 'toast-animations';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// Auto-initialize if calendar element exists on page load
function tryAutoInit() {
    const calendarEl = document.getElementById('unifiedCalendar');
    if (calendarEl) {
        initializeUnifiedCalendar();
    }
}

// ==================== Filters ====================

// Store the current filter states
let activeDayFilter = null;

/**
 * Apply time filter by rebuilding the calendar with selected time range
 */
function applyTimeFilter() {
    const timeRangeSelect = document.getElementById('timeRangeFilter');
    if (!timeRangeSelect) return;
    
    const selectedValue = timeRangeSelect.value;
    const [startHour, endHour] = selectedValue.split('-').map(Number);
    
    // Store the time range globally
    window.activeTimeRange = { start: startHour, end: endHour - 1 };
    
    // Rebuild the calendar
    refreshUnifiedCalendar().then(() => {
        // Reapply day filter if active
        if (activeDayFilter && activeDayFilter.length < 7) {
            const dayColumns = document.querySelectorAll('.day-column');
            dayColumns.forEach((column) => {
                const dayValue = parseInt(column.dataset.day);
                column.style.display = activeDayFilter.includes(dayValue) ? 'flex' : 'none';
            });
        }
    });
}

/**
 * Apply day filter to hide/show day columns
 */
function applyDayFilter() {
    const checkedDays = Array.from(document.querySelectorAll('.dayFilter:checked'))
        .map(cb => parseInt(cb.value));
    
    // Store the filter state
    activeDayFilter = checkedDays;
    
    const dayColumns = document.querySelectorAll('.day-column');
    
    dayColumns.forEach((column) => {
        const dayValue = parseInt(column.dataset.day);
        column.style.display = checkedDays.includes(dayValue) ? 'flex' : 'none';
    });
}

/**
 * Reapply the active day filter (called after calendar refresh)
 */
function reapplyDayFilter() {
    if (activeDayFilter && activeDayFilter.length < 7) {
        const dayColumns = document.querySelectorAll('.day-column');
        dayColumns.forEach((column) => {
            const dayValue = parseInt(column.dataset.day);
            column.style.display = activeDayFilter.includes(dayValue) ? 'flex' : 'none';
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Set default time range to 6am-9pm
        window.activeTimeRange = { start: 6, end: 21 };
        tryAutoInit();
        enableDragToCreate();
    });
} else {
    // Set default time range to 6am-9pm
    window.activeTimeRange = { start: 6, end: 21 };
    tryAutoInit();
    enableDragToCreate();
}

