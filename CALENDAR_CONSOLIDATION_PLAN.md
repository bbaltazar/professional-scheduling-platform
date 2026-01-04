# Calendar Consolidation Plan

## Current State
- **Schedule Tab**: Weekly recurring availability calendar (editable time blocks)
- **Bookings Tab**: List view of all bookings with filters

## Proposed Unified Design

### Visual Hierarchy
```
┌─────────────────────────────────────────────────────────┐
│  📅 Unified Calendar View                                │
│  [◀ Previous Week] [📅 Week of Dec 2-8, 2025] [Next ▶]  │
│                                                          │
│  Filters: [✓ Availability] [✓ Bookings] [✓ Completed]   │
│  Legend: [⬜ Available] [🟦 Booked] [🟩 Completed]       │
├─────────────────────────────────────────────────────────┤
│  MON   TUE   WED   THU   FRI   SAT   SUN                │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐            │
│  │░░░│ │░░░│ │░░░│ │░░░│ │░░░│ │░░░│ │░░░│ ← Avail    │
│  │███│ │   │ │███│ │   │ │███│ │   │ │   │ ← Booked   │
│  │░░░│ │░░░│ │▓▓▓│ │░░░│ │░░░│ │░░░│ │░░░│ ← Comp.    │
│  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘            │
└─────────────────────────────────────────────────────────┘
```

### Implementation Details

#### 1. Layer System
- **Layer 1 (Background)**: Recurring availability blocks (semi-transparent black)
- **Layer 2 (Foreground)**: Actual bookings (solid colors with client info)
- **Z-index management**: Bookings always on top

#### 2. Color Coding
- **Availability**: `rgba(26, 26, 26, 0.2)` - Light gray blocks
- **Confirmed Bookings**: `#3b82f6` - Blue with client name
- **Completed Bookings**: `#22c55e` - Green
- **Cancelled**: `rgba(239, 68, 68, 0.3)` - Faded red (optional visibility)

#### 3. Interaction Patterns
- **Click availability block** → Edit/delete recurring schedule
- **Click booking block** → Show booking details modal
- **Drag on empty space** → Create new availability (edit mode)
- **Hover** → Show tooltip with details

#### 4. Smart Filters
- Toggle buttons to show/hide layers independently
- "Edit Mode" to enable drag-create on availability
- "View Mode" (default) - click to see details only

#### 5. Week Navigation
- Arrow buttons for prev/next week
- Date picker to jump to any week
- "Today" button to return to current week
- Display "Week of [Start Date] - [End Date]"

## Technical Implementation

### Data Structure
```javascript
{
  availability: [
    { day: 0, start: '09:00', end: '12:00', recurring: true }
  ],
  bookings: [
    { 
      date: '2025-12-02', 
      start: '10:00', 
      end: '11:00', 
      client: 'John Doe',
      service: 'Haircut',
      status: 'confirmed'
    }
  ]
}
```

### Rendering Logic
1. Load current week's date range
2. Fetch recurring availability patterns
3. Fetch bookings for that week
4. Render availability layer (background)
5. Overlay booking layer (foreground)
6. Apply filters based on toggle states

### Performance Optimization
- Only load ±4 weeks of bookings
- Cache recurring patterns (they don't change often)
- Lazy load booking details on click
- Debounce filter toggles

## User Benefits
✅ See full week at a glance
✅ Understand when you're available vs. booked
✅ Quickly identify gaps in schedule
✅ Less navigation between tabs
✅ More intuitive than separate views
✅ Professional calendar feel (like Google Calendar)

## Migration Path
1. Create new unified calendar component
2. Add toggle to switch between "Classic List View" and "Calendar View"
3. Collect user feedback
4. Eventually deprecate separate views

