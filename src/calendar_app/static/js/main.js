// ==================== MAIN COORDINATOR ====================
// This file imports all modules and exposes functions to window object for onclick handlers

console.log('====================================');
console.log('[MAIN] ⚡ main.js FILE IS EXECUTING ⚡');
console.log('====================================');

console.log('[MAIN] Loading main.js module...');

import * as utils from './utils.js';
console.log('[MAIN] utils.js loaded');
import * as auth from './auth.js';
console.log('[MAIN] auth.js loaded');
import * as clients from './clients.js';
console.log('[MAIN] clients.js loaded');
import * as navigation from './navigation.js';
console.log('[MAIN] navigation.js loaded');
import * as bookings from './bookings.js';
console.log('[MAIN] bookings.js loaded');
import * as schedule from './schedule.js';
console.log('[MAIN] schedule.js loaded');
import * as services from './services.js';
console.log('[MAIN] services.js loaded');
import * as workplaces from './workplaces.js';
console.log('[MAIN] workplaces.js loaded');
import * as clientDetail from './client-detail.js';
console.log('[MAIN] client-detail.js loaded');

console.log('[MAIN] All modules imported successfully');

// Expose currentSpecialistId globally (set by template)
// window.currentSpecialistId is set in the HTML template

// ==================== EXPOSE FUNCTIONS TO WINDOW ====================
// These are needed for onclick handlers in the HTML

// Utility functions
window.formatTime = utils.formatTime;
// NOTE: formatDuration is NOT exposed here because professional.html has its own version
// that handles datetime strings. The utils.formatDuration handles time-only strings.
window.formatPhone = utils.formatPhone;
window.formatPhoneForDisplay = utils.formatPhoneForDisplay;
window.validatePhone = utils.validatePhone;
window.normalizePhone = utils.normalizePhone;
window.showResponse = utils.showResponse;

console.log('Utility functions exposed to window');

// Client management functions
window.loadClients = () => clients.loadClients(window.currentSpecialistId);
window.sortClients = clients.sortClients;
window.filterClients = clients.filterClients;
window.toggleFavorite = (consumerId, isFavorite) => 
    clients.toggleFavorite(consumerId, isFavorite, window.currentSpecialistId);
window.dismissInvalidLegend = clients.dismissInvalidLegend;
window.displayClients = clients.displayClients;
window.updateClientStats = clients.updateClientStats;

console.log('[MAIN] Checking clients module:', clients);
console.log('[MAIN] Checking clientState:', clients.clientState);

// Expose clientState directly - this is a reference to the module's state object
// so mutations will work correctly
if (!clients.clientState) {
    console.error('[MAIN] ERROR: clients.clientState is undefined! Creating fallback...');
    window.clientState = {
        allClients: [],
        currentClientDetail: null,
        editModeActive: false,
        currentSortColumn: 'name',
        currentSortDirection: 'asc'
    };
} else {
    window.clientState = clients.clientState;
}

console.log('[MAIN] Client state exposed:', window.clientState);

// Navigation functions
window.switchTab = (tabName) => navigation.switchTab(tabName, window.currentSpecialistId);
window.loadDashboardStats = () => navigation.loadDashboardStats(window.currentSpecialistId);
window.loadExistingData = () => navigation.loadExistingData(window.currentSpecialistId);

console.log('[MAIN] Navigation functions exposed, switchTab available:', typeof window.switchTab);

// Booking management functions
window.loadBookings = bookings.loadBookings;
window.filterBookings = bookings.filterBookings;
window.updateBookingStatus = bookings.updateBookingStatus;
window.startAppointment = bookings.startAppointment;
window.finishAppointment = bookings.finishAppointment;
window.closeCompleteAppointmentModal = bookings.closeCompleteAppointmentModal;
window.confirmCompleteAppointment = bookings.confirmCompleteAppointment;
window.resetCompleteConfirmationPreference = bookings.resetCompleteConfirmationPreference;
window.openClientProfile = bookings.openClientProfile;

// Schedule management functions
window.togglePtoTimes = schedule.togglePtoTimes;
window.createPTOBlock = schedule.createPTOBlock;
window.loadPTOBlocks = schedule.loadPTOBlocks;
window.deletePTOBlock = schedule.deletePTOBlock;
window.createRecurringSchedule = schedule.createRecurringSchedule;
window.loadRecurringSchedules = schedule.loadRecurringSchedules;
window.deleteRecurringSchedule = schedule.deleteRecurringSchedule;
window.initializeWeeklyCalendar = schedule.initializeWeeklyCalendar;
window.updateCalendarView = schedule.updateCalendarView;
window.toggleDayVisibility = schedule.toggleDayVisibility;
window.deleteTimeBlock = schedule.deleteTimeBlock;
window.clearWeeklySchedule = schedule.clearWeeklySchedule;
window.copyDaySchedule = schedule.copyDaySchedule;
window.saveWeeklySchedule = schedule.saveWeeklySchedule;
window.openApplyWeeksModal = schedule.openApplyWeeksModal;
window.updateApplyPreview = schedule.updateApplyPreview;
window.closeApplyWeeksModal = schedule.closeApplyWeeksModal;
window.applyToUpcomingWeeks = schedule.applyToUpcomingWeeks;

// Service management functions
window.displayExistingServices = services.displayExistingServices;
window.editService = services.editService;
window.cancelEdit = services.cancelEdit;
window.saveServiceEdit = services.saveServiceEdit;
window.confirmDeleteService = services.confirmDeleteService;
window.deleteService = services.deleteService;
window.loadExistingServices = services.loadExistingServices;
window.addServiceField = services.addServiceField;
window.saveServices = services.saveServices;

// Workplace management functions
window.searchYelpBusinesses = workplaces.searchYelpBusinesses;
window.addWorkplaceFromYelp = workplaces.addWorkplaceFromYelp;
window.createCustomWorkplace = workplaces.createCustomWorkplace;
window.loadMyWorkplaces = workplaces.loadMyWorkplaces;
window.toggleWorkplaceStatus = workplaces.toggleWorkplaceStatus;
window.removeWorkplace = workplaces.removeWorkplace;

// Client detail modal functions
window.viewClientDetail = clientDetail.viewClientDetail;
window.updateManualBookingServiceInfo = clientDetail.updateManualBookingServiceInfo;
window.loadManualBookingTimeSlots = clientDetail.loadManualBookingTimeSlots;
window.selectAlternativeDate = clientDetail.selectAlternativeDate;
window.submitManualBooking = clientDetail.submitManualBooking;
window.closeClientModal = clientDetail.closeClientModal;
window.saveClientProfile = clientDetail.saveClientProfile;
window.addAppointmentNote = clientDetail.addAppointmentNote;
window.toggleAppointmentNoteEditor = clientDetail.toggleAppointmentNoteEditor;
window.saveAppointmentNote = clientDetail.saveAppointmentNote;
window.toggleChangelog = clientDetail.toggleChangelog;
window.confirmDeleteClient = clientDetail.confirmDeleteClient;
window.closeDeleteConfirmModal = clientDetail.closeDeleteConfirmModal;
window.deleteClient = clientDetail.deleteClient;

// Authentication functions (auth.js already exposes these to window, but we reference them here for completeness)
console.log('[MAIN] Authentication functions available:', {
    proceedWithEmail: typeof window.proceedWithEmail,
    showSignUp: typeof window.showSignUp,
    registerUser: typeof window.registerUser,
    verifyCode: typeof window.verifyCode
});

console.log('[MAIN] All functions exposed to window - modules ready!');

// Initialize app on DOM load
document.addEventListener('DOMContentLoaded', () => {
    navigation.initializeApp(window.currentSpecialistId);
});

// Export for use in other modules
export { utils, clients, navigation, bookings, schedule, services, workplaces, clientDetail };
