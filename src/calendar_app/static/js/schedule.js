// ========================
// SCHEDULE MODULE
// Handles weekly calendar, recurring schedules, availability, and PTO management
// ========================

console.log('Loading schedule.js module...');

import { showResponse } from './utils.js';

// ========================
// STATE MANAGEMENT
// ========================

// Weekly Calendar Drag & Drop State
let weeklyScheduleData = {}; // {day: [{start: hour (decimal), end: hour (decimal)}]}
let isSelecting = false;
let isResizing = false;
let resizingDay = null;
let resizingIndex = null;
let resizingEdge = null; // 'top' or 'bottom'
let currentDay = null;
let startHour = null;
let previewElement = null;
let viewStartHour = 6; // Default view starts at 6 AM
let viewEndHour = 23; // Default view ends at 11 PM
const GRANULARITY_MINUTES = 5; // 5-minute increments
const GRANULARITY_HOURS = GRANULARITY_MINUTES / 60; // 0.0833... hours

// ========================
// PTO MANAGEMENT
// ========================

export function togglePtoTimes() {
    const fullDay = document.getElementById('ptoFullDay').checked;
    const timeFields = document.getElementById('ptoTimeFields');
    timeFields.style.display = fullDay ? 'none' : 'grid';
}

export async function createPTOBlock() {
    const currentSpecialistId = window.currentSpecialistId;

    if (!currentSpecialistId) {
        showResponse('ptoResponse', 'Please establish your profile first', 'error');
        return;
    }

    const title = document.getElementById('ptoTitle').value;
    const type = document.getElementById('ptoType').value;
    const startDate = document.getElementById('ptoStartDate').value;
    const endDate = document.getElementById('ptoEndDate').value;
    const fullDay = document.getElementById('ptoFullDay').checked;
    const startTime = document.getElementById('ptoStartTime').value;
    const endTime = document.getElementById('ptoEndTime').value;
    const description = document.getElementById('ptoDescription').value;

    if (!title || !startDate || !endDate) {
        showResponse('ptoResponse', 'Please fill in all required fields', 'error');
        return;
    }

    if (!fullDay && (!startTime || !endTime)) {
        showResponse('ptoResponse', 'Please specify start and end times for partial day PTO', 'error');
        return;
    }

    const ptoData = {
        title: title,
        description: description || null,
        start_date: startDate,
        end_date: endDate,
        pto_type: type,
        is_full_day: fullDay,
        start_time: fullDay ? null : startTime,
        end_time: fullDay ? null : endTime
    };

    try {
        const response = await fetch(`/specialist/${currentSpecialistId}/pto`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(ptoData)
        });

        if (response.ok) {
            const result = await response.json();
            showResponse('ptoResponse', '✅ PTO block created successfully!', 'success');
            loadPTOBlocks();
            // Reset form
            document.getElementById('ptoTitle').value = '';
            document.getElementById('ptoStartDate').value = '';
            document.getElementById('ptoEndDate').value = '';
            document.getElementById('ptoStartTime').value = '';
            document.getElementById('ptoEndTime').value = '';
            document.getElementById('ptoDescription').value = '';
            document.getElementById('ptoFullDay').checked = true;
            togglePtoTimes();
        } else {
            const error = await response.json();
            showResponse('ptoResponse', `Failed: ${error.detail}`, 'error');
        }
    } catch (error) {
        showResponse('ptoResponse', `Connection error: ${error.message}`, 'error');
    }
}

export async function loadPTOBlocks() {
    const currentSpecialistId = window.currentSpecialistId;

    if (!currentSpecialistId) return;

    try {
        const response = await fetch(`/specialist/${currentSpecialistId}/pto`, {
            credentials: 'include'
        });

        if (response.ok) {
            const blocks = await response.json();
            displayPTOBlocks(blocks);
        } else if (response.status === 404) {
            // Endpoint not implemented yet, show empty state
            displayPTOBlocks([]);
        }
    } catch (error) {
        console.error('Error loading PTO blocks:', error);
        // Show empty state on error
        displayPTOBlocks([]);
    }
}

function displayPTOBlocks(blocks) {
    const container = document.getElementById('ptoBlocksList');
    if (!container) return;

    if (blocks.length === 0) {
        container.innerHTML = '<p style="color: rgba(212, 175, 55, 0.6); font-style: italic;">No scheduled time off.</p>';
        return;
    }

    container.innerHTML = blocks.map(block => {
        const typeColors = {
            'vacation': '#3b82f6',
            'sick': '#ef4444',
            'personal': '#8b5cf6',
            'holiday': '#10b981',
            'other': '#6b7280'
        };

        return `
            <div class="pto-item">
                <div class="pto-header">
                    <div class="pto-title" style="color: ${typeColors[block.pto_type] || '#D4AF37'}">${block.title}</div>
                    <div class="pto-actions">
                        <button class="btn btn-small btn-danger" onclick="deletePTOBlock(${block.id})">Delete</button>
                    </div>
                </div>
                <div class="pto-info">
                    <div class="info-item">
                        <div class="info-label">Type</div>
                        <div class="info-value">${block.pto_type.charAt(0).toUpperCase() + block.pto_type.slice(1)}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Dates</div>
                        <div class="info-value">${block.start_date}${block.start_date !== block.end_date ? ' - ' + block.end_date : ''}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Duration</div>
                        <div class="info-value">${block.is_full_day ? 'Full Day(s)' : `${block.start_time} - ${block.end_time}`}</div>
                    </div>
                    ${block.description ? `
                        <div class="info-item">
                            <div class="info-label">Notes</div>
                            <div class="info-value">${block.description}</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

export async function deletePTOBlock(blockId) {
    const currentSpecialistId = window.currentSpecialistId;

    if (!confirm('Are you sure you want to delete this PTO block?')) return;

    try {
        const response = await fetch(`/specialist/${currentSpecialistId}/pto/${blockId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            showResponse('ptoResponse', '✅ PTO block deleted successfully!', 'success');
            loadPTOBlocks();
        } else {
            const error = await response.json();
            showResponse('ptoResponse', `Failed: ${error.detail}`, 'error');
        }
    } catch (error) {
        showResponse('ptoResponse', `Connection error: ${error.message}`, 'error');
    }
}

// ========================
// RECURRING SCHEDULES
// ========================

export async function createRecurringSchedule() {
    const currentSpecialistId = window.currentSpecialistId;

    if (!currentSpecialistId) {
        showResponse('recurringResponse', 'Please establish your profile first', 'error');
        return;
    }

    const recurrenceType = document.getElementById('recurrenceType').value;
    const startTime = document.getElementById('recurringStartTime').value;
    const endTime = document.getElementById('recurringEndTime').value;
    const startDate = document.getElementById('recurringStartDate').value;
    const endDate = document.getElementById('recurringEndDate').value;

    if (!startTime || !endTime || !startDate) {
        showResponse('recurringResponse', 'Please fill in all required fields', 'error');
        return;
    }

    let daysOfWeek = null;
    if (recurrenceType === 'weekly') {
        const checkedDays = Array.from(document.querySelectorAll('.day-option input[type="checkbox"]:checked'))
            .map(cb => parseInt(cb.value));
        if (checkedDays.length === 0) {
            showResponse('recurringResponse', 'Please select at least one day for weekly schedule', 'error');
            return;
        }
        daysOfWeek = checkedDays;
    }

    const scheduleData = {
        recurrence_type: recurrenceType,
        days_of_week: daysOfWeek,
        start_time: startTime,
        end_time: endTime,
        start_date: startDate,
        end_date: endDate || null
    };

    try {
        const response = await fetch(`/specialist/${currentSpecialistId}/recurring-schedule`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(scheduleData)
        });

        if (response.ok) {
            const result = await response.json();
            showResponse('recurringResponse', '✅ Recurring schedule created successfully!', 'success');
            loadRecurringSchedules();
            // Reset form
            document.getElementById('recurringStartDate').value = '';
            document.getElementById('recurringEndDate').value = '';
        } else {
            const error = await response.json();
            showResponse('recurringResponse', `Failed: ${error.detail}`, 'error');
        }
    } catch (error) {
        showResponse('recurringResponse', `Connection error: ${error.message}`, 'error');
    }
}

export async function loadRecurringSchedules() {
    const currentSpecialistId = window.currentSpecialistId;

    if (!currentSpecialistId) return;

    try {
        const response = await fetch(`/specialist/${currentSpecialistId}/recurring-schedules`, {
            credentials: 'include'
        });

        if (response.ok) {
            const schedules = await response.json();
            displayRecurringSchedules(schedules);
        }
    } catch (error) {
        console.error('Error loading recurring schedules:', error);
    }
}

function displayRecurringSchedules(schedules) {
    const container = document.getElementById('recurringSchedulesList');
    if (!container) return;

    if (schedules.length === 0) {
        container.innerHTML = '<p style="color: rgba(212, 175, 55, 0.6); font-style: italic;">No recurring schedules set up yet.</p>';
        return;
    }

    container.innerHTML = schedules.map(schedule => {
        // days_of_week is already an array from the API, no need to parse
        const daysOfWeek = schedule.days_of_week || [];
        const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        const selectedDays = daysOfWeek.map(day => dayNames[day]).join(', ');

        return `
            <div class="schedule-item">
                <div class="schedule-header">
                    <div class="schedule-title">${schedule.recurrence_type.charAt(0).toUpperCase() + schedule.recurrence_type.slice(1)} Schedule</div>
                    <div class="schedule-actions">
                        <button class="btn btn-small btn-danger" onclick="deleteRecurringSchedule(${schedule.id})">Delete</button>
                    </div>
                </div>
                <div class="schedule-info">
                    <div class="info-item">
                        <div class="info-label">Time</div>
                        <div class="info-value">${schedule.start_time} - ${schedule.end_time}</div>
                    </div>
                    ${schedule.recurrence_type === 'weekly' ? `
                        <div class="info-item">
                            <div class="info-label">Days</div>
                            <div class="info-value">${selectedDays}</div>
                        </div>
                    ` : ''}
                    <div class="info-item">
                        <div class="info-label">Start Date</div>
                        <div class="info-value">${schedule.start_date}</div>
                    </div>
                    ${schedule.end_date ? `
                        <div class="info-item">
                            <div class="info-label">End Date</div>
                            <div class="info-value">${schedule.end_date}</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

export async function deleteRecurringSchedule(scheduleId) {
    const currentSpecialistId = window.currentSpecialistId;

    if (!confirm('Are you sure you want to delete this recurring schedule?')) return;

    try {
        const response = await fetch(`/specialist/${currentSpecialistId}/recurring-schedule/${scheduleId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            showResponse('recurringResponse', '✅ Recurring schedule deleted successfully!', 'success');
            loadRecurringSchedules();
        } else {
            const error = await response.json();
            showResponse('recurringResponse', `Failed: ${error.detail}`, 'error');
        }
    } catch (error) {
        showResponse('recurringResponse', `Connection error: ${error.message}`, 'error');
    }
}

// ========================
// WEEKLY CALENDAR - INITIALIZATION
// ========================

export function initializeWeeklyCalendar() {
    const calendar = document.getElementById('weeklyCalendar');
    if (!calendar) return;

    // Initialize schedule data for each day (midnight to midnight = 24 hours)
    for (let day = 0; day < 7; day++) {
        weeklyScheduleData[day] = [];
    }

    // Generate initial time labels
    updateCalendarView();

    // Add mouse event listeners to each day column
    for (let day = 0; day < 7; day++) {
        const slotsContainer = calendar.querySelector(`.time-slots[data-day="${day}"]`);

        // Add mouse event listeners
        slotsContainer.addEventListener('mousedown', (e) => startSelection(e, day));
        slotsContainer.addEventListener('mousemove', (e) => updateSelection(e, day));
        slotsContainer.addEventListener('mouseup', (e) => endSelection(e, day));
        slotsContainer.addEventListener('mouseleave', cancelSelection);
    }

    // Set default start date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('recurringStartDate').value = today;
}

export function updateCalendarView() {
    // Get selected time range
    viewStartHour = parseInt(document.getElementById('timeRangeStart').value);
    viewEndHour = parseInt(document.getElementById('timeRangeEnd').value);

    // Validate range
    if (viewEndHour <= viewStartHour) {
        alert('End time must be after start time');
        document.getElementById('timeRangeEnd').value = Math.min(viewStartHour + 8, 24); // Default to 8 hours
        viewEndHour = parseInt(document.getElementById('timeRangeEnd').value);
    }

    // Keep constant height, adjust spacing per hour
    const FIXED_HEIGHT = 680; // Fixed total height in pixels
    const hoursInView = viewEndHour - viewStartHour;
    const heightPerHour = FIXED_HEIGHT / hoursInView;

    console.log('Calendar view update:', {
        viewStartHour,
        viewEndHour,
        hoursInView,
        heightPerHour,
        FIXED_HEIGHT
    });

    // Generate time labels with dynamic height
    const timeColumn = document.getElementById('timeColumn');
    timeColumn.innerHTML = '<div class="time-header"></div>';

    for (let hour = viewStartHour; hour < viewEndHour; hour++) {
        const label = document.createElement('div');
        label.className = 'time-label';
        label.textContent = formatHour(hour);
        label.style.height = heightPerHour + 'px';
        timeColumn.appendChild(label);
    }

    // Set fixed height for time-slots containers
    document.querySelectorAll('.time-slots').forEach(slots => {
        slots.style.height = FIXED_HEIGHT + 'px';
    });

    // Update grid background to match new hour spacing
    updateGridBackground(heightPerHour);

    // Re-render all day schedules with new view
    for (let day = 0; day < 7; day++) {
        renderDaySchedule(day);
    }
}

function updateGridBackground(heightPerHour) {
    // Update the repeating grid to match the hour spacing
    const halfHourHeight = heightPerHour / 2;
    const gridPattern = `
        repeating-linear-gradient(
            to bottom,
            rgba(255, 255, 255, 0.05) 0px,
            rgba(255, 255, 255, 0.05) 1px,
            transparent 1px,
            transparent ${halfHourHeight}px,
            rgba(255, 255, 255, 0.15) ${halfHourHeight}px,
            rgba(255, 255, 255, 0.15) ${halfHourHeight + 1}px,
            transparent ${halfHourHeight + 1}px,
            transparent ${heightPerHour}px
        )
    `;

    document.querySelectorAll('.time-slots').forEach(slots => {
        slots.style.background = gridPattern;
    });
}

export function toggleDayVisibility(day) {
    const checkbox = document.getElementById(`dayToggle${day}`);
    const dayColumn = document.querySelector(`.day-column[data-day="${day}"]`);

    if (dayColumn) {
        dayColumn.style.display = checkbox.checked ? 'flex' : 'none';
    }

    // Recalculate grid layout based on visible days
    updateGridLayout();
}

function updateGridLayout() {
    const calendar = document.getElementById('weeklyCalendar');
    const visibleDays = [];

    // Count visible day columns
    for (let i = 0; i < 7; i++) {
        const checkbox = document.getElementById(`dayToggle${i}`);
        if (checkbox && checkbox.checked) {
            visibleDays.push(i);
        }
    }

    // Update grid-template-columns: 80px for time column + equal columns for visible days
    const numVisibleDays = visibleDays.length;
    if (numVisibleDays > 0) {
        calendar.style.gridTemplateColumns = `80px repeat(${numVisibleDays}, 1fr)`;
    } else {
        // Show at least the time column
        calendar.style.gridTemplateColumns = `80px`;
    }
}

// ========================
// WEEKLY CALENDAR - DRAG & DROP
// ========================

// Helper function to snap time to 5-minute increments
function snapToGranularity(timeInHours) {
    // Convert to minutes, round to nearest 5 minutes, convert back to hours
    const totalMinutes = timeInHours * 60;
    const snappedMinutes = Math.round(totalMinutes / GRANULARITY_MINUTES) * GRANULARITY_MINUTES;
    return snappedMinutes / 60;
}

// Helper function to snap time to 30-minute intervals (on the hour and half-hour)
function snapToHalfHour(timeInHours) {
    // Convert to minutes, round to nearest 30 minutes, convert back to hours
    const totalMinutes = timeInHours * 60;
    const snappedMinutes = Math.round(totalMinutes / 30) * 30;
    return snappedMinutes / 60;
}

// Helper function to format time with minutes
function formatTimeWithMinutes(timeInHours) {
    const hours = Math.floor(timeInHours);
    const minutes = Math.round((timeInHours - hours) * 60);

    if (hours === 24) return '12:00 AM';

    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHour = hours > 12 ? hours - 12 : (hours === 0 ? 12 : hours);
    const displayMinutes = minutes.toString().padStart(2, '0');

    if (minutes === 0) {
        return `${displayHour} ${period}`;
    }
    return `${displayHour}:${displayMinutes} ${period}`;
}

function startSelection(e, day) {
    if (e.target.classList.contains('delete-btn')) return;
    if (e.target.classList.contains('resize-handle')) return;
    if (e.target.classList.contains('time-slot')) {
        // Clicked on existing block - do nothing, let hover show delete button
        return;
    }

    isSelecting = true;
    currentDay = day;

    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const hoursInView = viewEndHour - viewStartHour;
    const rawHour = (y / rect.height) * hoursInView + viewStartHour;
    startHour = snapToHalfHour(rawHour); // Snap to 30-minute intervals

    console.log('Click debug:', {
        y,
        rectHeight: rect.height,
        hoursInView,
        rawHour,
        startHour,
        viewStartHour,
        viewEndHour
    });

    // Create preview element at snapped position
    previewElement = document.createElement('div');
    previewElement.className = 'selection-preview';
    e.currentTarget.appendChild(previewElement);

    // Calculate snapped Y position for preview
    const snappedY = ((startHour - viewStartHour) / hoursInView) * rect.height;
    updatePreview(snappedY, snappedY, e.currentTarget);
}

function startResize(e, day, index, edge) {
    e.stopPropagation();
    e.preventDefault();

    isResizing = true;
    resizingDay = day;
    resizingIndex = index;
    resizingEdge = edge;

    // Add visual feedback
    const blockEl = e.target.closest('.time-slot');
    if (blockEl) {
        blockEl.classList.add('resizing');
    }

    // Add global mouse event listeners
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', endResize);
}

function handleResize(e) {
    if (!isResizing) return;

    const slotsContainer = document.querySelector(`.time-slots[data-day="${resizingDay}"]`);
    const rect = slotsContainer.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const hoursInView = viewEndHour - viewStartHour;
    const rawHour = (y / rect.height) * hoursInView + viewStartHour;

    // Snap to 5-minute increments
    const snappedHour = snapToGranularity(rawHour);

    // Clamp to valid range (0-24)
    const clampedHour = Math.max(0, Math.min(24, snappedHour));

    const block = weeklyScheduleData[resizingDay][resizingIndex];
    const minBlockSize = 0.25; // 15 minutes minimum

    if (resizingEdge === 'top') {
        // Resizing from top - adjust start time
        // Ensure minimum block size
        if (clampedHour < block.end - minBlockSize) {
            block.start = clampedHour;
        }
    } else if (resizingEdge === 'bottom') {
        // Resizing from bottom - adjust end time
        // Ensure minimum block size
        if (clampedHour > block.start + minBlockSize) {
            block.end = clampedHour;
        }
    }

    // Re-render the day to show updated block
    renderDaySchedule(resizingDay);
}

function endResize(e) {
    if (!isResizing) return;

    isResizing = false;

    // Merge overlapping blocks after resize
    if (resizingDay !== null) {
        mergeOverlappingBlocks(resizingDay);
        renderDaySchedule(resizingDay);
    }

    resizingDay = null;
    resizingIndex = null;
    resizingEdge = null;

    // Remove global event listeners
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', endResize);
}

function updateSelection(e, day) {
    if (!isSelecting || currentDay !== day) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const hoursInView = viewEndHour - viewStartHour;

    // Calculate the current mouse position in hours and snap it
    const rawCurrentHour = (y / rect.height) * hoursInView + viewStartHour;
    const currentHour = snapToHalfHour(rawCurrentHour);

    // Convert snapped times to pixel positions
    const startY = ((startHour - viewStartHour) / hoursInView) * rect.height;
    const endY = ((currentHour - viewStartHour) / hoursInView) * rect.height;

    updatePreview(startY, endY, e.currentTarget);
}

function updatePreview(startY, endY, container) {
    if (!previewElement) return;

    const top = Math.min(startY, endY);
    const height = Math.abs(endY - startY);

    previewElement.style.top = top + 'px';
    previewElement.style.height = Math.max(height, 20) + 'px';
    previewElement.style.left = '2px';
    previewElement.style.right = '2px';
}

function endSelection(e, day) {
    if (!isSelecting || currentDay !== day) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const hoursInView = viewEndHour - viewStartHour;
    const rawEndHour = (y / rect.height) * hoursInView + viewStartHour;
    let endHour = snapToHalfHour(rawEndHour); // Snap to 30-minute intervals

    // Ensure at least 15 minute block (0.25 hours)
    const minBlockSize = 0.25;
    if (endHour <= startHour) {
        endHour = startHour + minBlockSize;
    } else if (endHour - startHour < minBlockSize) {
        endHour = startHour + minBlockSize;
    }

    // Clamp to 24-hour range
    endHour = Math.min(endHour, 24);

    // Add to schedule data
    weeklyScheduleData[day].push({
        start: startHour,
        end: endHour
    });

    // Merge overlapping blocks
    mergeOverlappingBlocks(day);

    // Render the block
    renderDaySchedule(day);

    // Clean up
    isSelecting = false;
    currentDay = null;
    startHour = null;
    if (previewElement) {
        previewElement.remove();
        previewElement = null;
    }
}

function cancelSelection() {
    if (previewElement) {
        previewElement.remove();
        previewElement = null;
    }
    isSelecting = false;
    currentDay = null;
    startHour = null;
}

function mergeOverlappingBlocks(day) {
    const blocks = weeklyScheduleData[day];
    if (blocks.length <= 1) return;

    // Sort by start time
    blocks.sort((a, b) => a.start - b.start);

    // Merge overlapping
    const merged = [blocks[0]];
    for (let i = 1; i < blocks.length; i++) {
        const current = blocks[i];
        const last = merged[merged.length - 1];

        if (current.start <= last.end) {
            // Overlapping, merge
            last.end = Math.max(last.end, current.end);
        } else {
            merged.push(current);
        }
    }

    weeklyScheduleData[day] = merged;
}

function renderDaySchedule(day) {
    const slotsContainer = document.querySelector(`.time-slots[data-day="${day}"]`);

    // Clear existing blocks
    slotsContainer.querySelectorAll('.time-slot').forEach(el => el.remove());

    // Get container height - use fixed height to match updateCalendarView
    const FIXED_HEIGHT = 680;
    const totalHeight = parseFloat(slotsContainer.style.height) || FIXED_HEIGHT;
    const hoursInView = viewEndHour - viewStartHour;

    console.log('Render day schedule:', {
        day,
        totalHeight,
        hoursInView,
        viewStartHour,
        viewEndHour,
        heightPerHour: totalHeight / hoursInView
    });

    // Render each block
    weeklyScheduleData[day].forEach((block, index) => {
        // Only show blocks that are at least partially visible in current view
        if (block.end <= viewStartHour || block.start >= viewEndHour) {
            return; // Block is completely outside view
        }

        // Clamp block to visible range for display
        const visibleStart = Math.max(block.start, viewStartHour);
        const visibleEnd = Math.min(block.end, viewEndHour);

        const blockEl = document.createElement('div');
        blockEl.className = 'time-slot';
        blockEl.dataset.day = day;
        blockEl.dataset.index = index;

        const top = ((visibleStart - viewStartHour) / hoursInView) * totalHeight;
        const height = ((visibleEnd - visibleStart) / hoursInView) * totalHeight;

        console.log('Block positioning:', {
            blockStart: block.start,
            blockEnd: block.end,
            visibleStart,
            visibleEnd,
            top,
            height
        });

        blockEl.style.top = top + 'px';
        blockEl.style.height = height + 'px';

        const startTime = formatTimeWithMinutes(block.start);
        const endTime = formatTimeWithMinutes(block.end);

        // Add resize handles
        const topHandle = document.createElement('div');
        topHandle.className = 'resize-handle resize-handle-top';
        topHandle.dataset.edge = 'top';
        topHandle.addEventListener('mousedown', (e) => startResize(e, day, index, 'top'));

        const bottomHandle = document.createElement('div');
        bottomHandle.className = 'resize-handle resize-handle-bottom';
        bottomHandle.dataset.edge = 'bottom';
        bottomHandle.addEventListener('mousedown', (e) => startResize(e, day, index, 'bottom'));

        // Show time label if block is tall enough
        if (height > 30) {
            blockEl.innerHTML = `
                ${startTime} - ${endTime}
                <button class="delete-btn" onclick="deleteTimeBlock(${day}, ${index}); event.stopPropagation();">×</button>
            `;
        } else {
            blockEl.innerHTML = `
                <button class="delete-btn" onclick="deleteTimeBlock(${day}, ${index}); event.stopPropagation();">×</button>
            `;
            blockEl.title = `${startTime} - ${endTime}`;
        }

        blockEl.appendChild(topHandle);
        blockEl.appendChild(bottomHandle);
        slotsContainer.appendChild(blockEl);
    });
}

function formatHour(hour) {
    if (hour === 24) return '12 AM';
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
    return `${displayHour} ${period}`;
}

export function deleteTimeBlock(day, index) {
    weeklyScheduleData[day].splice(index, 1);
    renderDaySchedule(day);
}

export function clearWeeklySchedule() {
    if (!confirm('Clear all availability blocks from the weekly schedule?')) return;

    for (let day = 0; day < 7; day++) {
        weeklyScheduleData[day] = [];
        renderDaySchedule(day);
    }
}

// ========================
// WEEKLY CALENDAR - SAVE & APPLY
// ========================

export function copyDaySchedule() {
    const sourceDay = prompt('Copy FROM which day? (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun)');
    if (sourceDay === null || sourceDay === '') return;

    const sourceDayNum = parseInt(sourceDay);
    if (isNaN(sourceDayNum) || sourceDayNum < 0 || sourceDayNum > 6) {
        alert('Invalid day number. Use 0-6.');
        return;
    }

    const targetDays = prompt('Copy TO which days? (comma-separated, e.g., 1,3,4)');
    if (targetDays === null || targetDays === '') return;

    const targetDayNums = targetDays.split(',').map(d => parseInt(d.trim())).filter(d => !isNaN(d) && d >= 0 && d <= 6);

    if (targetDayNums.length === 0) {
        alert('No valid target days specified.');
        return;
    }

    // Copy schedule
    targetDayNums.forEach(targetDay => {
        weeklyScheduleData[targetDay] = JSON.parse(JSON.stringify(weeklyScheduleData[sourceDayNum]));
        renderDaySchedule(targetDay);
    });

    alert(`Schedule copied to selected days!`);
}

export async function saveWeeklySchedule() {
    const currentSpecialistId = window.currentSpecialistId;

    if (!currentSpecialistId) {
        showResponse('recurringResponse', 'Please establish your profile first', 'error');
        return;
    }

    const startDate = document.getElementById('recurringStartDate').value;
    const endDate = document.getElementById('recurringEndDate').value;

    if (!startDate) {
        showResponse('recurringResponse', 'Please select a start date', 'error');
        return;
    }

    // Check if any days have schedule
    const hasSchedule = Object.values(weeklyScheduleData).some(day => day.length > 0);
    if (!hasSchedule) {
        showResponse('recurringResponse', 'Please add at least one availability block', 'error');
        return;
    }

    // Helper function to convert decimal hours to HH:MM format
    function hoursToTimeString(decimalHours) {
        const hours = Math.floor(decimalHours);
        const minutes = Math.round((decimalHours - hours) * 60);
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    }

    // Convert schedule data to backend format
    const schedules = [];
    for (let day = 0; day < 7; day++) {
        weeklyScheduleData[day].forEach(block => {
            schedules.push({
                recurrence_type: 'weekly',
                days_of_week: [day],
                start_time: hoursToTimeString(block.start),
                end_time: hoursToTimeString(block.end),
                start_date: startDate,
                end_date: endDate || null
            });
        });
    }

    // Save each schedule
    try {
        let successCount = 0;
        for (const schedule of schedules) {
            const response = await fetch(`/specialist/${currentSpecialistId}/recurring-schedule`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(schedule)
            });

            if (response.ok) {
                successCount++;
            }
        }

        if (successCount === schedules.length) {
            showResponse('recurringResponse', `✅ Weekly schedule saved successfully! ${successCount} time blocks created.`, 'success');
            loadRecurringSchedules();
        } else {
            showResponse('recurringResponse', `⚠️ Partially saved: ${successCount}/${schedules.length} blocks created`, 'error');
        }
    } catch (error) {
        showResponse('recurringResponse', `Connection error: ${error.message}`, 'error');
    }
}

export function openApplyWeeksModal() {
    // Check if there's any schedule to apply
    const hasSchedule = Object.values(weeklyScheduleData).some(day => day.length > 0);
    if (!hasSchedule) {
        alert('Please create a weekly schedule first before applying it to upcoming weeks.');
        return;
    }

    // Set default start date to next Monday
    const today = new Date();
    const nextMonday = new Date(today);
    nextMonday.setDate(today.getDate() + ((1 + 7 - today.getDay()) % 7 || 7));
    document.getElementById('applyStartDate').value = nextMonday.toISOString().split('T')[0];

    // Show modal and update preview
    document.getElementById('applyWeeksModal').classList.add('active');
    updateApplyPreview();
}

export function updateApplyPreview() {
    const numberOfWeeks = parseInt(document.getElementById('numberOfWeeks').value);
    const startDate = document.getElementById('applyStartDate').value;
    const previewText = document.getElementById('previewText');

    if (!startDate) {
        previewText.textContent = 'Select a start date to see preview';
        return;
    }

    // Calculate end date
    const start = new Date(startDate);
    const end = new Date(start);
    end.setDate(start.getDate() + (numberOfWeeks * 7) - 1);

    // Format dates nicely
    const startFormatted = start.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
    const endFormatted = end.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });

    // Count total blocks across all days
    let totalBlocks = 0;
    const daysWithSchedule = [];
    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    for (let day = 0; day < 7; day++) {
        if (weeklyScheduleData[day].length > 0) {
            totalBlocks += weeklyScheduleData[day].length;
            daysWithSchedule.push(dayNames[day]);
        }
    }

    // Build preview message
    let message = `This will apply your schedule to ${numberOfWeeks} week${numberOfWeeks > 1 ? 's' : ''} (${startFormatted} - ${endFormatted}).\n\n`;
    message += `📅 Days with availability: ${daysWithSchedule.join(', ')}\n`;
    message += `⏰ Total time blocks per week: ${totalBlocks}\n`;
    message += `✨ Total blocks to create: ${totalBlocks * numberOfWeeks}`;

    previewText.innerHTML = message.replace(/\n/g, '<br>');
}

export function closeApplyWeeksModal() {
    document.getElementById('applyWeeksModal').classList.remove('active');
}

export async function applyToUpcomingWeeks() {
    const currentSpecialistId = window.currentSpecialistId;

    if (!currentSpecialistId) {
        alert('Please establish your profile first');
        closeApplyWeeksModal();
        return;
    }

    const numberOfWeeks = parseInt(document.getElementById('numberOfWeeks').value);
    const startDate = document.getElementById('applyStartDate').value;

    if (!startDate) {
        alert('Please select a start date');
        return;
    }

    // Check if there's any schedule to apply
    const hasSchedule = Object.values(weeklyScheduleData).some(day => day.length > 0);
    if (!hasSchedule) {
        alert('No schedule to apply. Please create a weekly schedule first.');
        closeApplyWeeksModal();
        return;
    }

    // Calculate end date
    const start = new Date(startDate);
    const end = new Date(start);
    end.setDate(start.getDate() + (numberOfWeeks * 7) - 1);

    // Helper function to convert decimal hours to HH:MM format
    function hoursToTimeString(decimalHours) {
        const hours = Math.floor(decimalHours);
        const minutes = Math.round((decimalHours - hours) * 60);
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
    }

    // Convert schedule data to backend format
    const schedules = [];
    for (let day = 0; day < 7; day++) {
        weeklyScheduleData[day].forEach(block => {
            schedules.push({
                recurrence_type: 'weekly',
                days_of_week: [day],
                start_time: hoursToTimeString(block.start),
                end_time: hoursToTimeString(block.end),
                start_date: startDate,
                end_date: end.toISOString().split('T')[0]
            });
        });
    }

    // Save each schedule
    try {
        let successCount = 0;
        for (const schedule of schedules) {
            const response = await fetch(`/specialist/${currentSpecialistId}/recurring-schedule`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(schedule)
            });

            if (response.ok) {
                successCount++;
            } else {
                console.error('Failed to save schedule:', await response.text());
            }
        }

        if (successCount > 0) {
            alert(`✅ Successfully applied schedule to ${numberOfWeeks} week(s)!\n\nCreated ${successCount} recurring availability blocks from ${startDate} to ${end.toISOString().split('T')[0]}`);
            closeApplyWeeksModal();
            loadRecurringSchedules(); // Refresh the recurring schedules list
        } else {
            alert('Failed to apply schedule. Please try again.');
        }
    } catch (error) {
        console.error('Error applying schedule:', error);
        alert('Error applying schedule. Please check your connection and try again.');
    }
}

console.log('Schedule.js module loaded successfully!');
