// ==================== UTILITY FUNCTIONS (TypeScript) ====================

// Type definitions for phone validation result
export interface PhoneValidationResult {
    valid: boolean;
    normalized: string | null;
    error?: string;
}

// Type for formatted phone display result
export interface FormattedPhoneDisplay {
    formatted: string;
    isInvalid?: boolean;
    error?: string;
}

// Message types for showResponse
export type MessageType = 'success' | 'error' | 'info' | 'warning';

// ==================== PHONE UTILITIES ====================

/**
 * Normalize phone number to 10 digits
 * Removes all non-digit characters and country code
 * @param phone - Raw phone number string
 * @returns Normalized 10-digit string or null if invalid
 */
export function normalizePhone(phone: string | null | undefined): string | null {
    if (!phone) return null;

    // Remove all non-digit characters (parentheses, dashes, spaces, etc.)
    const digits = phone.replace(/\D/g, '');

    // Remove leading 1 if present (country code)
    const normalized = digits.startsWith('1') && digits.length === 11 ? digits.slice(1) : digits;

    // Return null if not exactly 10 digits
    return normalized.length === 10 ? normalized : null;
}

/**
 * Validate phone number with comprehensive checks
 * @param phone - Phone number to validate
 * @returns Validation result with normalized number and error if invalid
 */
export function validatePhone(phone: string | null | undefined): PhoneValidationResult {
    if (!phone) return { valid: true, normalized: null }; // Optional field

    const normalized = normalizePhone(phone);

    if (!normalized) {
        return {
            valid: false,
            normalized: null,
            error: 'Phone number must be exactly 10 digits'
        };
    }

    // Extract area code and exchange
    const areaCode = normalized.slice(0, 3);
    const exchange = normalized.slice(3, 6);

    // Reject invalid area codes (cannot start with 0 or 1)
    if (areaCode[0] === '0' || areaCode[0] === '1') {
        return {
            valid: false,
            normalized: null,
            error: 'Invalid area code (cannot start with 0 or 1)'
        };
    }

    // Reject 555 area code (directory assistance)
    if (areaCode === '555') {
        return {
            valid: false,
            normalized: null,
            error: 'Invalid area code (555 is reserved)'
        };
    }

    // Reject fake exchange codes (555-XXXX pattern)
    if (exchange === '555') {
        return {
            valid: false,
            normalized: null,
            error: 'Invalid phone number (555 exchange is reserved for fictional use)'
        };
    }

    // Reject all same digit (e.g., 1111111111)
    if (new Set(normalized).size === 1) {
        return {
            valid: false,
            normalized: null,
            error: 'Invalid phone number (repeating digits)'
        };
    }

    // Reject sequential digits
    if (normalized === '1234567890' || normalized === '0123456789') {
        return {
            valid: false,
            normalized: null,
            error: 'Invalid phone number (sequential digits)'
        };
    }

    // Reject common test numbers
    if (normalized === '0000000000' || normalized === '9999999999') {
        return {
            valid: false,
            normalized: null,
            error: 'Invalid phone number (test number)'
        };
    }

    // Reject if area code and exchange are the same
    if (areaCode === exchange) {
        return {
            valid: false,
            normalized: null,
            error: 'Invalid phone number (area code and exchange cannot match)'
        };
    }

    return { valid: true, normalized: normalized };
}

/**
 * Format phone for display as (555) 555-5555
 * @param phone - Phone number to format
 * @returns Formatted phone string
 */
export function formatPhone(phone: string | null | undefined): string {
    const normalized = normalizePhone(phone);
    if (!normalized) return phone || '';

    return `(${normalized.slice(0, 3)}) ${normalized.slice(3, 6)}-${normalized.slice(6)}`;
}

/**
 * Format phone for display in table with validation check
 * @param phone - Phone number to format and validate
 * @returns Formatted string or object with error info if invalid
 */
export function formatPhoneForDisplay(phone: string | null | undefined): string | FormattedPhoneDisplay {
    if (!phone) return '-';

    const validation = validatePhone(phone);
    if (validation.valid && validation.normalized) {
        // Valid phone - format it nicely
        return `(${validation.normalized.slice(0, 3)}) ${validation.normalized.slice(3, 6)}-${validation.normalized.slice(6)}`;
    } else {
        // Invalid phone - return original with error indicator
        return { formatted: phone, isInvalid: true, error: validation.error || 'Invalid format' };
    }
}

// ==================== TIME & DATE UTILITIES ====================

/**
 * Format time string for display (24h to 12h with AM/PM)
 * @param timeString - Time in HH:MM or HH:MM:SS format
 * @returns Formatted time like "2:30 PM"
 */
export function formatTime(timeString: string | null | undefined): string {
    if (!timeString) return '';
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
}

/**
 * Calculate and format duration between two times
 * @param startTime - Start time in HH:MM format
 * @param endTime - End time in HH:MM format
 * @returns Formatted duration like "2h 30m" or "45m"
 */
export function formatDuration(startTime: string, endTime: string): string {
    const start = new Date(`2000-01-01T${startTime}`);
    const end = new Date(`2000-01-01T${endTime}`);
    const diff = (end.getTime() - start.getTime()) / 1000 / 60; // minutes
    const hours = Math.floor(diff / 60);
    const minutes = diff % 60;

    if (hours > 0 && minutes > 0) {
        return `${hours}h ${minutes}m`;
    } else if (hours > 0) {
        return `${hours}h`;
    } else {
        return `${minutes}m`;
    }
}

// ==================== UI UTILITIES ====================

/**
 * Show response message with auto-hide
 * @param elementId - ID of element to show message in
 * @param message - Message text to display
 * @param type - Message type (success, error, info, warning)
 */
export function showResponse(elementId: string, message: string, type: MessageType): void {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = message;
    element.className = type === 'success' ? 'success-message' : 'error-message';
    element.style.display = 'block';

    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

// ==================== DOM UTILITIES ====================

/**
 * Safely get input value from element
 * @param elementId - ID of input element
 * @returns Input value or empty string if not found
 */
export function getInputValue(elementId: string): string {
    const element = document.getElementById(elementId) as HTMLInputElement | null;
    return element?.value || '';
}

/**
 * Safely set input value
 * @param elementId - ID of input element
 * @param value - Value to set
 */
export function setInputValue(elementId: string, value: string): void {
    const element = document.getElementById(elementId) as HTMLInputElement | null;
    if (element) {
        element.value = value;
    }
}

/**
 * Safely get select value
 * @param elementId - ID of select element
 * @returns Selected value or empty string if not found
 */
export function getSelectValue(elementId: string): string {
    const element = document.getElementById(elementId) as HTMLSelectElement | null;
    return element?.value || '';
}

/**
 * Check if element is checked (checkbox/radio)
 * @param elementId - ID of checkbox/radio element
 * @returns True if checked, false otherwise
 */
export function isChecked(elementId: string): boolean {
    const element = document.getElementById(elementId) as HTMLInputElement | null;
    return element?.checked || false;
}
