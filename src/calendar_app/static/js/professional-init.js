/* Professional Dashboard Inline Scripts */
/* Minimal initialization code that needs to be inline for template variables */

// This file contains ONLY the code that MUST be inline due to Jinja2 template variables
// All other JavaScript has been modularized in /static/js/

// Set specialist ID from template (needed before module loads)
// Note: This uses Jinja2 templating and cannot be moved to external file
function initializeSpecialistId() {
    // This will be replaced by template rendering
    // {% if authenticated and specialist %}
    // window.currentSpecialistId = {{ specialist.id }};
    // {% else %}
    // window.currentSpecialistId = null;
    // {% endif %}
}

// Create placeholder functions to prevent errors during module loading
// These will be replaced once main.js loads
let retryCount = {};
const MAX_RETRIES = 10;

const placeholderFn = (name) => function (...args) {
    if (!retryCount[name]) retryCount[name] = 0;

    if (retryCount[name] >= MAX_RETRIES) {
        console.error(`${name} failed to load after ${MAX_RETRIES} retries. Check browser console for module loading errors.`);
        return;
    }

    retryCount[name]++;
    console.warn(`${name} called before modules loaded - retry ${retryCount[name]}/${MAX_RETRIES}`);

    setTimeout(() => {
        if (typeof window[name] === 'function' && !window[name].toString().includes('placeholderFn')) {
            // Real function is now loaded, call it
            window[name](...args);
        } else if (retryCount[name] < MAX_RETRIES) {
            // Still not loaded, retry
            window[name](...args);
        }
    }, 200);
};

// Placeholders for onclick handlers (will be overwritten by modules when loaded)
window.switchTab = placeholderFn('switchTab');
window.loadClients = placeholderFn('loadClients');
window.viewClientDetail = placeholderFn('viewClientDetail');
window.updateBookingStatus = placeholderFn('updateBookingStatus');
window.loadBookings = placeholderFn('loadBookings');
window.searchYelpBusinesses = placeholderFn('searchYelpBusinesses');

console.log('[INIT] Placeholder functions created, loading modules...');

// Fallback logout function in case module hasn't loaded yet
if (typeof window.logout === 'undefined') {
    window.logout = async function () {
        try {
            const response = await fetch('/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            window.location.href = '/professional';
        } catch (error) {
            console.error('Logout error:', error);
            window.location.href = '/professional';
        }
    };
    console.log('[FALLBACK] logout function created');
}
