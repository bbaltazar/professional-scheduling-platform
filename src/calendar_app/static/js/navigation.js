// ==================== TAB NAVIGATION & DASHBOARD (TypeScript) ====================
/**
 * Tab switching function - manages UI state and loads tab-specific data
 * @param tabName - Name of tab to switch to
 * @param currentSpecialistId - Currently logged in specialist ID
 */
export function switchTab(tabName, currentSpecialistId) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });
    // Show selected tab content
    const selectedTab = document.getElementById(`tab-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    // Add active class to clicked button
    const clickedButton = event?.target?.closest('.tab-button');
    if (clickedButton) {
        clickedButton.classList.add('active');
    }
    // Load content for specific tabs when opened
    if (tabName === 'bookings' && currentSpecialistId) {
        window.loadBookings();
    }
    else if (tabName === 'schedule' && currentSpecialistId) {
        window.loadWorkplacesForSchedule(); // Load workplaces for the dropdown
        window.loadRecurringSchedules();
        
        // Load PTO blocks if function exists
        if (typeof window.loadPTOBlocks === 'function') {
            window.loadPTOBlocks();
        }
        
        // Initialize unified calendar view in schedule tab
        if (typeof window.initializeUnifiedCalendar === 'function') {
            window.initializeUnifiedCalendar();
        }
    }
    else if (tabName === 'services' && currentSpecialistId) {
        window.loadExistingServices();
    }
    else if (tabName === 'workplaces' && currentSpecialistId) {
        window.loadMyWorkplaces();
    }
    else if (tabName === 'dashboard' && currentSpecialistId) {
        loadDashboardStats(currentSpecialistId);
    }
    else if (tabName === 'clients' && currentSpecialistId) {
        console.log('[NAV] Switching to clients tab');
        console.log('[NAV] clientState:', window.clientState);
        console.log('[NAV] allClients length:', window.clientState ? window.clientState.allClients.length : 'clientState undefined');
        // Only load clients if not already loaded
        if (window.clientState && window.clientState.allClients.length === 0) {
            console.log('[NAV] Clients not loaded yet, calling loadClients...');
            window.loadClients();
        }
        else {
            console.log('[NAV] Clients already loaded, skipping load');
        }
    }
}
/**
 * Load Dashboard Statistics
 * Fetches bookings, services, and workplaces counts
 * @param currentSpecialistId - Specialist ID to load stats for
 */
export async function loadDashboardStats(currentSpecialistId) {
    if (!currentSpecialistId) {
        console.warn('loadDashboardStats: No currentSpecialistId provided');
        return;
    }
    console.log('Loading dashboard stats for specialist:', currentSpecialistId);
    try {
        // Load bookings count
        const bookingsResponse = await fetch(`/bookings/specialist/${currentSpecialistId}`);
        if (bookingsResponse.ok) {
            const bookings = await bookingsResponse.json();
            console.log('Dashboard: Loaded bookings:', bookings.length);
            const totalBookingsEl = document.getElementById('dashTotalBookings');
            if (totalBookingsEl) {
                totalBookingsEl.textContent = bookings.length.toString();
            }
            const confirmed = bookings.filter(b => b.status === 'confirmed').length;
            const confirmedBookingsEl = document.getElementById('dashConfirmedBookings');
            if (confirmedBookingsEl) {
                confirmedBookingsEl.textContent = confirmed.toString();
            }
            console.log('Dashboard: Confirmed bookings:', confirmed);
        }
        else {
            console.error('Dashboard: Failed to load bookings, status:', bookingsResponse.status);
        }
        // Load services count
        const servicesResponse = await fetch(`/specialist/${currentSpecialistId}/services`);
        if (servicesResponse.ok) {
            const services = await servicesResponse.json();
            console.log('Dashboard: Loaded services:', services.length);
            const totalServicesEl = document.getElementById('dashTotalServices');
            if (totalServicesEl) {
                totalServicesEl.textContent = services.length.toString();
            }
        }
        else {
            console.error('Dashboard: Failed to load services, status:', servicesResponse.status);
        }
        // Load workplaces count
        const workplacesResponse = await fetch(`/specialists/${currentSpecialistId}/workplaces`);
        if (workplacesResponse.ok) {
            const workplaces = await workplacesResponse.json();
            console.log('Dashboard: Loaded workplaces:', workplaces.length);
            const totalWorkplacesEl = document.getElementById('dashTotalWorkplaces');
            if (totalWorkplacesEl) {
                totalWorkplacesEl.textContent = workplaces.length.toString();
            }
        }
        else {
            console.error('Dashboard: Failed to load workplaces, status:', workplacesResponse.status);
        }
        console.log('Dashboard stats loading complete');
    }
    catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}
/**
 * Load existing data on page load
 * @param _currentSpecialistId - Specialist ID (unused, kept for API compatibility)
 */
export async function loadExistingData(_currentSpecialistId) {
    try {
        const response = await fetch('/auth/me', {
            method: 'GET',
            credentials: 'include'
        });
        if (response.ok) {
            const data = await response.json();
            // Load existing services
            if (data.services && data.services.length > 0) {
                window.loadExistingServices(data.services);
                window.displayExistingServices(data.services);
            }
            // Load existing availability
            if (data.availability && data.availability.length > 0 && window.loadExistingAvailability) {
                window.loadExistingAvailability(data.availability);
            }
            // Load bookings
            await window.loadBookings();
        }
    }
    catch (error) {
        console.log('Could not load existing data:', error);
    }
}
/**
 * Initialize the application on DOM load
 * Sets up event listeners, default dates, and loads initial data
 * @param currentSpecialistId - Currently logged in specialist ID
 */
function initializeApp(currentSpecialistId) {
    console.log('Initializing app with specialist ID:', currentSpecialistId);
    // Set default dates for various forms
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    const dateInput = document.querySelector('.availability-date');
    if (dateInput) {
        dateInput.value = todayStr;
    }
    // Set default dates for recurring schedule form
    const startDateField = document.getElementById('recurringStartDate');
    if (startDateField) {
        startDateField.value = todayStr;
    }
    // Set default dates for PTO form
    const ptoStartDateField = document.getElementById('ptoStartDate');
    const ptoEndDateField = document.getElementById('ptoEndDate');
    if (ptoStartDateField) {
        ptoStartDateField.value = todayStr;
    }
    if (ptoEndDateField) {
        ptoEndDateField.value = todayStr;
    }
    // Handle recurrence type changes (show/hide days of week)
    const recurrenceType = document.getElementById('recurrenceType');
    const daysGroup = document.getElementById('daysOfWeekGroup');
    if (recurrenceType && daysGroup) {
        recurrenceType.addEventListener('change', function () {
            daysGroup.style.display = this.value === 'weekly' ? 'block' : 'none';
        });
    }
    // Load existing services and availability if user is authenticated
    if (currentSpecialistId) {
        loadExistingData(currentSpecialistId);
        // Load dashboard stats since dashboard is the default tab
        loadDashboardStats(currentSpecialistId);
        // Initialize the weekly calendar for drag-and-drop functionality
        if (typeof window.initializeWeeklyCalendar === 'function') {
            window.initializeWeeklyCalendar();
        }
    }
    // Add Enter key support for login form (email input only)
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        console.log('Login form found, adding submit listener');
        loginForm.addEventListener('submit', function (event) {
            console.log('[NAV] Form submit - calling proceedWithEmail');
            event.preventDefault();
            window.proceedWithEmail();
        });
    }
    else {
        console.log('Login form NOT found');
    }
    // Also add keypress listener directly to email input
    const emailInput = document.getElementById('userEmail');
    if (emailInput) {
        console.log('Email input found, adding keypress listener');
        emailInput.addEventListener('keypress', function (event) {
            console.log('Key pressed:', event.key);
            if (event.key === 'Enter') {
                console.log('Enter key detected, calling proceedWithEmail');
                event.preventDefault();
                window.proceedWithEmail();
            }
        });
    }
    else {
        console.log('Email input NOT found');
    }
    // Note: Verification code Enter key listener is added dynamically in auth.js
    // when the code section becomes visible, not at initialization
}
export { initializeApp };
//# sourceMappingURL=navigation.js.map