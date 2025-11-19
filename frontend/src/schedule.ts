// ========================
// SCHEDULE MODULE (TypeScript Version)
// Handles weekly calendar, recurring schedules, availability, and PTO management
// ========================

// NOTE: showResponse will be imported from compiled utils.js
// For now, we'll declare it to satisfy TypeScript
declare function showResponse(elementId: string, message: string, type: 'success' | 'error' | 'info'): void;

import type {
    RecurringSchedule,
    WorkplaceWithStatus,
    DayOfWeek
} from './types.js';

console.log('Loading schedule.ts module...');

// ========================
// WORKPLACE LOADING
// ========================

export async function loadWorkplacesForSchedule(): Promise<void> {
    const currentSpecialistId = (window as any).currentSpecialistId as number | undefined;
    if (!currentSpecialistId) return;

    try {
        const response = await fetch(`/specialists/${currentSpecialistId}/workplaces`, {
            credentials: 'include'
        });

        if (response.ok) {
            const workplaces: WorkplaceWithStatus[] = await response.json();
            const selectElement = document.getElementById('recurringWorkplaceId') as HTMLSelectElement | null;

            if (selectElement) {
                // Clear existing options except "Personal"
                selectElement.innerHTML = '<option value="">Personal</option>';

                // Add workplace options
                workplaces.forEach((wp: WorkplaceWithStatus) => {
                    const option = document.createElement('option');
                    option.value = wp.id.toString();
                    option.textContent = `${wp.name} - ${wp.city}`;
                    selectElement.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading workplaces for schedule:', error);
    }
}

// ========================
// RECURRING SCHEDULES
// ========================

export async function loadRecurringSchedules(): Promise<void> {
    const currentSpecialistId = (window as any).currentSpecialistId as number | undefined;

    if (!currentSpecialistId) {
        return;
    }

    try {
        const response = await fetch(`/specialist/${currentSpecialistId}/recurring-schedules`, {
            credentials: 'include'
        });

        if (response.ok) {
            const schedules: RecurringSchedule[] = await response.json();
            displayRecurringSchedules(schedules);
        } else {
            console.error('Failed to load recurring schedules, status:', response.status);
        }
    } catch (error) {
        console.error('Error loading recurring schedules:', error);
    }
}

function displayRecurringSchedules(schedules: RecurringSchedule[]): void {
    // Store schedules globally for calendar rendering
    (window as any).recurringSchedulesData = schedules;

    // Render the calendar view
    updateRecurringSchedulesCalendar();
}

// New function to render recurring schedules as a visual calendar
export function updateRecurringSchedulesCalendar(): void {
    const container = document.getElementById('recurringSchedulesCalendar');
    if (!container) {
        console.error('recurringSchedulesCalendar container not found!');
        return;
    }

    const schedules: RecurringSchedule[] = (window as any).recurringSchedulesData || [];
    console.log(`Rendering calendar with ${schedules.length} schedules`);

    // Get time range from selectors
    const startHourElement = document.getElementById('scheduleViewTimeStart') as HTMLSelectElement | null;
    const endHourElement = document.getElementById('scheduleViewTimeEnd') as HTMLSelectElement | null;
    const startHour = parseInt(startHourElement?.value || '8');
    const endHour = parseInt(endHourElement?.value || '18');

    // Get current week dates
    const today = new Date();
    const currentDayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, etc.
    const mondayOffset = currentDayOfWeek === 0 ? -6 : 1 - currentDayOfWeek; // Calculate days to Monday

    const monday = new Date(today);
    monday.setDate(today.getDate() + mondayOffset);

    // Generate week dates
    const weekDates: Date[] = [];
    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    for (let i = 0; i < 7; i++) {
        const date = new Date(monday);
        date.setDate(monday.getDate() + i);
        weekDates.push(date);
    }

    // Always show the calendar grid (even when empty)
    let html = '<div style="display: grid; grid-template-columns: 60px repeat(7, 1fr); gap: 1px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; overflow: hidden;">';

    // Header row with actual dates
    html += '<div style="background: rgba(212, 175, 55, 0.15); padding: 12px 8px; text-align: center; font-weight: 600; font-size: 0.75rem; color: var(--color-text-tertiary);">Time</div>';
    weekDates.forEach((date, index) => {
        const isToday = date.toDateString() === today.toDateString();
        const dayName = dayNames[index];
        const dateStr = `${monthNames[date.getMonth()]} ${date.getDate()}`;

        html += `
            <div style="
                background: ${isToday ? 'rgba(212, 175, 55, 0.25)' : 'rgba(212, 175, 55, 0.15)'};
                padding: 8px 4px;
                text-align: center;
                border: ${isToday ? '2px solid var(--color-accent)' : 'none'};
            ">
                <div style="font-weight: 600; font-size: 0.85rem; color: ${isToday ? 'var(--color-accent)' : 'var(--color-accent)'};">
                    ${dayName}
                </div>
                <div style="font-size: 0.7rem; color: var(--color-text-tertiary); margin-top: 2px;">
                    ${dateStr}
                </div>
                ${isToday ? '<div style="font-size: 0.65rem; color: var(--color-accent); margin-top: 2px;">TODAY</div>' : ''}
            </div>
        `;
    });

    // Time rows
    for (let hour = startHour; hour < endHour; hour++) {
        // Format hour for display
        const displayHour = hour === 0 ? '12 AM' :
            hour < 12 ? `${hour} AM` :
                hour === 12 ? '12 PM' :
                    `${hour - 12} PM`;

        html += `<div style="background: rgba(255, 255, 255, 0.02); padding: 8px 4px; text-align: right; font-size: 0.7rem; color: var(--color-text-tertiary); border-right: 1px solid rgba(255, 255, 255, 0.05);">${displayHour}</div>`;

        // For each day
        for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
            const date = weekDates[dayIndex];
            const isToday = date.toDateString() === today.toDateString();

            // Find schedules for this day and hour
            const daySchedules = schedules.filter((schedule: RecurringSchedule) => {
                if (schedule.recurrence_type === 'weekly') {
                    return schedule.days_of_week && schedule.days_of_week.includes(dayIndex as DayOfWeek);
                } else if (schedule.recurrence_type === 'daily') {
                    return true; // Daily applies to all days
                }
                return false;
            });

            // Check if any schedule overlaps this hour
            let cellContent = '';
            const baseStyle = isToday
                ? 'background: rgba(212, 175, 55, 0.03); border-left: 1px solid rgba(212, 175, 55, 0.2);'
                : 'background: rgba(255, 255, 255, 0.02);';
            let cellStyle = `${baseStyle} padding: 4px; min-height: 40px; position: relative; border-bottom: 1px solid rgba(255, 255, 255, 0.05);`;

            daySchedules.forEach((schedule: RecurringSchedule) => {
                // Parse time strings (e.g., "09:00:00" or "09:00")
                const startParts = schedule.start_time.split(':');
                const endParts = schedule.end_time.split(':');
                const scheduleStartHour = parseInt(startParts[0]);
                const scheduleEndHour = parseInt(endParts[0]);
                const scheduleEndMin = parseInt(endParts[1] || '0');

                // Check if this hour is within the schedule
                if (hour >= scheduleStartHour && hour < scheduleEndHour ||
                    (hour === scheduleEndHour && scheduleEndMin === 0)) {

                    // Determine workplace display
                    const workplaceIcon = schedule.workplace ? '📍' : '🏠';
                    const workplaceName = schedule.workplace ? schedule.workplace.name : 'Personal';

                    // Only show label on the starting hour
                    if (hour === scheduleStartHour) {
                        cellContent += `
                            <div style="
                                background: linear-gradient(135deg, rgba(212, 175, 55, 0.3), rgba(212, 175, 55, 0.2));
                                border-left: 3px solid var(--color-accent);
                                padding: 6px 8px;
                                border-radius: 4px;
                                margin-bottom: 2px;
                                position: relative;
                            ">
                                <div style="font-size: 0.75rem; font-weight: 600; color: var(--color-accent); margin-bottom: 2px;">
                                    ${schedule.start_time.substring(0, 5)} - ${schedule.end_time.substring(0, 5)}
                                </div>
                                <div style="font-size: 0.7rem; color: var(--color-text-secondary);">
                                    ${workplaceIcon} ${workplaceName}
                                </div>
                                <button onclick="deleteRecurringSchedule(${schedule.id})" 
                                    style="position: absolute; top: 4px; right: 4px; background: rgba(220, 38, 38, 0.8); border: none; color: white; border-radius: 3px; padding: 2px 6px; font-size: 0.65rem; cursor: pointer; opacity: 0.7; transition: opacity 0.2s;"
                                    onmouseover="this.style.opacity='1'" 
                                    onmouseout="this.style.opacity='0.7'">✕</button>
                            </div>
                        `;
                    } else {
                        // Continuation of the block - show subtle highlight
                        cellStyle = `${baseStyle} background: linear-gradient(135deg, rgba(212, 175, 55, 0.15), rgba(212, 175, 55, 0.08)); border-left: 3px solid rgba(212, 175, 55, 0.5); padding: 4px; min-height: 40px; border-bottom: 1px solid rgba(255, 255, 255, 0.05);`;
                    }
                }
            });

            html += `<div style="${cellStyle}">${cellContent}</div>`;
        }
    }

    html += '</div>';

    // Add helpful message if no schedules
    if (schedules.length === 0) {
        html += `
            <div style="margin-top: 20px; padding: 24px; background: rgba(212, 175, 55, 0.05); border: 1px dashed rgba(212, 175, 55, 0.3); border-radius: 8px; text-align: center;">
                <div style="font-size: 1.2rem; margin-bottom: 8px;">📅</div>
                <div style="color: var(--color-text-secondary); font-size: 0.95rem; margin-bottom: 6px;">No recurring schedules yet</div>
                <div style="color: var(--color-text-tertiary); font-size: 0.8rem;">Use the drag-and-drop calendar above to create your weekly availability schedule</div>
            </div>
        `;
    }

    container.innerHTML = html;
}

export async function deleteRecurringSchedule(scheduleId: number): Promise<void> {
    const currentSpecialistId = (window as any).currentSpecialistId as number | undefined;

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
        showResponse('recurringResponse', `Connection error: ${(error as Error).message}`, 'error');
    }
}

console.log('Schedule.ts module loaded successfully!');
