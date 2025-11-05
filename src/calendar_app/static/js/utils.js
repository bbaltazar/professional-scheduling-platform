// ==================== UTILITY FUNCTIONS ====================

// Normalize phone number to 10 digits
export function normalizePhone(phone) {
    if (!phone) return null;

    // Remove all non-digit characters (parentheses, dashes, spaces, etc.)
    const digits = phone.replace(/\D/g, '');

    // Remove leading 1 if present (country code)
    const normalized = digits.startsWith('1') && digits.length === 11 ? digits.slice(1) : digits;

    // Return null if not exactly 10 digits
    return normalized.length === 10 ? normalized : null;
}

// Validate phone number
export function validatePhone(phone) {
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

// Format phone for display (optional - formats as (555) 555-5555)
export function formatPhone(phone) {
    const normalized = normalizePhone(phone);
    if (!normalized) return phone;

    return `(${normalized.slice(0, 3)}) ${normalized.slice(3, 6)}-${normalized.slice(6)}`;
}

// Format phone for display in table with validation check
export function formatPhoneForDisplay(phone) {
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

// Format time for display
export function formatTime(timeString) {
    if (!timeString) return '';
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
}

// Format duration
export function formatDuration(startTime, endTime) {
    const start = new Date(`2000-01-01T${startTime}`);
    const end = new Date(`2000-01-01T${endTime}`);
    const diff = (end - start) / 1000 / 60; // minutes
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

// Show response message
export function showResponse(elementId, message, type) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = message;
    element.className = type === 'success' ? 'success-message' : 'error-message';
    element.style.display = 'block';

    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}
