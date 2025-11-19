// ========================
// SHARED TYPE DEFINITIONS
// Central location for all TypeScript interfaces used across the application
// ========================

// ========================
// USER & AUTHENTICATION
// ========================

export interface Specialist {
    id: number;
    email: string;
    full_name: string;
    phone?: string;
    bio?: string;
    profile_image_url?: string;
    specialization?: string;
    years_of_experience?: number;
    license_number?: string;
    hourly_rate?: number;
    created_at: string;
    is_active: boolean;
}

export interface Consumer {
    id: number;
    email: string;
    full_name: string;
    phone?: string;
    created_at: string;
}

// ========================
// WORKPLACE
// ========================

export interface Workplace {
    id: number;
    name: string;
    address: string;
    city: string;
    state?: string;
    zip_code?: string;
    phone?: string;
    email?: string;
    website?: string;
    description?: string;
    business_hours?: string;
    created_at: string;
}

export interface WorkplaceWithStatus extends Workplace {
    is_active: boolean;
    joined_at?: string;
}

// ========================
// SERVICE
// ========================

export interface Service {
    id: number;
    specialist_id: number;
    name: string;
    description?: string;
    duration_minutes: number;
    price: number;
    is_active: boolean;
    category?: string;
    created_at: string;
}

export interface ServiceStatistic {
    service_name: string;
    count: number;
    total_revenue: number;
    percentage: number;
}

// ========================
// BOOKING
// ========================

export interface Booking {
    id: number;
    consumer_id: number;
    specialist_id: number;
    service_id: number;
    workplace_id?: number;
    appointment_datetime: string;
    duration_minutes: number;
    status: BookingStatus;
    notes?: string;
    price: number;
    created_at: string;
    updated_at: string;
    consumer?: Consumer;
    service?: Service;
    workplace?: Workplace;
}

export type BookingStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';

// ========================
// RECURRING SCHEDULE
// ========================

export interface RecurringSchedule {
    id: number;
    title: string;
    recurrence_type: 'daily' | 'weekly';
    days_of_week: number[] | null;
    start_time: string;  // Format: "HH:MM" or "HH:MM:SS"
    end_time: string;    // Format: "HH:MM" or "HH:MM:SS"
    start_date: string;  // Format: "YYYY-MM-DD"
    end_date: string | null;  // Format: "YYYY-MM-DD"
    workplace_id: number | null;
    workplace: Workplace | null;
    created_at: string;
}

export interface RecurringScheduleCreate {
    recurrence_type: 'daily' | 'weekly';
    days_of_week?: number[];
    start_time: string;
    end_time: string;
    start_date: string;
    end_date?: string;
    workplace_id?: number;
}

// ========================
// CALENDAR EVENT
// ========================

export interface CalendarEvent {
    id: number;
    specialist_id: number;
    workplace_id?: number;
    title: string;
    description?: string;
    start_datetime: string;
    end_datetime: string;
    is_all_day: boolean;
    timezone: string;
    event_type: EventType;
    category?: string;
    priority: EventPriority;
    is_recurring: boolean;
    recurrence_rule?: string;
    recurring_event_id?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export type EventType = 'availability' | 'booking' | 'pto' | 'other';
export type EventPriority = 'low' | 'normal' | 'high';

// ========================
// PTO (Paid Time Off)
// ========================

export interface PTOBlock {
    id: number;
    specialist_id: number;
    start_date: string;
    end_date: string;
    reason?: string;
    is_all_day: boolean;
    created_at: string;
}

// ========================
// CLIENT (Consumer from Professional's perspective)
// ========================

export interface Client extends Consumer {
    booking_count?: number;
    total_spent?: number;
    last_booking_date?: string;
    upcoming_bookings?: Booking[];
    past_bookings?: Booking[];
}

// ========================
// API RESPONSE WRAPPERS
// ========================

export interface ApiResponse<T> {
    data: T;
    message?: string;
    status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

// ========================
// FORM DATA
// ========================

export interface LoginFormData {
    email: string;
    password: string;
}

export interface RegisterFormData {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
}

export interface ProfileUpdateData {
    full_name?: string;
    phone?: string;
    bio?: string;
    specialization?: string;
    years_of_experience?: number;
    license_number?: string;
    hourly_rate?: number;
}

// ========================
// UI STATE
// ========================

export interface WeeklyScheduleData {
    [day: number]: CalendarEvent[];
}

export interface ModalState {
    isOpen: boolean;
    currentClient?: Client;
    currentBooking?: Booking;
}

// ========================
// UTILITY TYPES
// ========================

export type ResponseMessage = {
    text: string;
    type: 'success' | 'error' | 'info' | 'warning';
};

export type DayOfWeek = 0 | 1 | 2 | 3 | 4 | 5 | 6; // 0 = Monday, 6 = Sunday

export type TimeString = string; // HH:MM format
export type DateString = string; // YYYY-MM-DD format
export type DateTimeString = string; // ISO 8601 format
