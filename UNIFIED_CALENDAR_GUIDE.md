# 📅 Unified Calendar Feature - User Guide

## What Changed?

Your calendar system has been consolidated from **two separate views** into **one unified calendar** that shows both your recurring availability and actual bookings together.

### Before
- **Bookings Tab** → List view of bookings
- **Schedule Tab** → Recurring availability calendar (separate)
- Had to switch between tabs to see the full picture

### After  
- **Calendar Tab** → Unified weekly view showing:
  - ⬜ Availability blocks (from recurring schedule)
  - 🟦 Confirmed bookings
  - 🟩 Completed bookings  
  - 🟥 Cancelled bookings (optional)

---

## How to Use the Unified Calendar

### 📍 Navigation

**Week Controls**
- `◀ Previous Week` / `Next Week ▶` - Navigate through weeks
- `📍 Today` button - Jump back to current week  
- Week display shows: "Week of Dec 2-8, 2025"

### 🎛️ Filter Toggles

Toggle visibility for each layer independently:

- **⬜ Availability Blocks** - Your recurring weekly availability (gray blocks)
- **🟦 Confirmed Bookings** - Scheduled appointments (blue blocks)  
- **🟩 Completed** - Past appointments (green blocks)
- **🟥 Cancelled** - Cancelled bookings (red blocks, off by default)

**Pro Tip:** Uncheck layers you don't need to reduce visual clutter!

### ✏️ Edit Mode

**View Mode (Default)**
- Click on bookings → See booking details  
- Click on availability → See time range
- Read-only, safe for browsing

**Edit Mode**  
- Click `✏️ Edit Availability` button
- Click on availability blocks → Edit/delete them
- Drag on empty space → Create new availability (future feature)

### 📊 Quick Stats

Bottom of calendar shows real-time metrics:

- **Available Hours** - Total recurring availability hours
- **Confirmed This Week** - Number of confirmed bookings
- **Completed This Week** - Number of completed sessions
- **Utilization Rate** - How much of your availability is booked (%)

---

## Visual Design

### Layer System

The calendar uses a **z-index layering system**:

```
┌─────────────────────────────┐
│  🟦 Bookings (foreground)  │ ← Always on top, solid colors
│  ⬜ Availability (background) │ ← Semi-transparent, dashed border
└─────────────────────────────┘
```

### Color Coding

| Type | Color | Meaning |
|------|-------|---------|
| ⬜ Availability | Light gray, dashed | You're available to book |
| 🟦 Confirmed | Solid blue | Client has a confirmed appointment |
| 🟩 Completed | Solid green | Session already completed |
| 🟥 Cancelled | Faded red | Booking was cancelled |

### Block Content

**Availability Blocks** show:
- Start - End time
- "Available" label

**Booking Blocks** show:
- Client name (bold)
- Service name
- Start - End time

---

## Managing Recurring Availability

### How It Works

1. Your **recurring weekly schedule** defines when you're generally available
2. These blocks appear as **light gray availability** on the calendar
3. When clients book, those specific times become **solid booking blocks**

### Editing Your Schedule

Click the button at bottom of calendar:
```
⚙️ Manage Recurring Availability
```

This reveals the full schedule editor where you can:
- Drag to create availability blocks
- Resize blocks by dragging edges
- Delete blocks
- Copy blocks from one day to another
- Set view hours (6 AM - 10 PM, etc.)

**When done editing:**
- Click `💾 Save Weekly Schedule`
- Click `← Back to Calendar` to return to unified view

Changes to recurring availability immediately update the unified calendar!

---

## Workflow Examples

### 📅 Planning Your Week

1. Navigate to the week you want to plan
2. **Turn off** "Completed" to reduce noise
3. See gaps between confirmed bookings
4. Note: Gray blocks = still available for booking

### 🔍 Reviewing Past Performance

1. Navigate to a past week
2. **Turn off** "Availability" (you only care about what happened)
3. **Turn on** "Completed" 
4. Review utilization rate at bottom

### ⚡ Quick Check Before Calling Client

1. Use `📍 Today` to go to current week
2. See today's bookings at a glance
3. Click on specific booking to see full details

---

## Technical Details

### Data Sources

- **Availability Blocks** - Loaded from `/specialist/{id}/recurring-schedules`
- **Bookings** - Loaded from `/specialist/{id}/bookings`, filtered to current week

### Performance

- Only loads ±1 week of bookings at a time
- Recurring patterns cached (they don't change often)
- Smooth 60fps animations
- Lazy-loads booking details on click

### Browser Compatibility

- Works on all modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile responsive (but best on desktop/tablet)
- No external dependencies

---

## Frequently Asked Questions

**Q: Can I still see a list view of bookings?**  
A: The old Bookings tab has been removed. The unified calendar provides better visualization. If you need a list, export to CSV (future feature).

**Q: What if I have overlapping availability and bookings?**  
A: Bookings always appear on top of availability (higher z-index). This is intentional - you can see both what's available and what's booked.

**Q: How do I add one-time availability for a specific date?**  
A: Currently, all availability is recurring. One-time exceptions are on the roadmap.

**Q: Can I print this calendar?**  
A: Browser print works! Use Ctrl/Cmd+P. Pro tip: Turn off "Cancelled" layer first for cleaner printout.

**Q: The calendar doesn't show past midnight. What about late-night availability?**  
A: Default view is 6 AM - 10 PM. In the recurring schedule editor, you can adjust the time range to show midnight-6 AM if needed.

---

## Tips & Tricks

### 🎯 Maximize Bookings
- Check utilization rate weekly
- If it's low, consider:
  - Adjusting your pricing
  - Marketing to fill gaps
  - Reducing availability blocks you rarely fill

### 🧹 Keep It Clean  
- Use filters! You rarely need all 4 layers visible
- Default to: Availability + Confirmed only
- Turn on Completed when reviewing past weeks

### ⌨️ Keyboard Shortcuts (Future)
- Left/Right arrows - Navigate weeks
- T - Go to Today
- E - Toggle edit mode
- 1-4 - Toggle layers

---

## Future Enhancements

Planned features for future releases:

- [ ] Drag-and-drop to create availability in calendar view
- [ ] Booking details modal (currently shows alert)
- [ ] Color customization for block types
- [ ] Export calendar to PDF/CSV
- [ ] Month view option
- [ ] One-time availability exceptions
- [ ] Client timezone display
- [ ] Drag to reschedule bookings
- [ ] Multi-week view (2-4 weeks at once)

---

## Troubleshooting

**Calendar not loading?**
- Check browser console for errors
- Ensure `window.currentSpecialistId` is set
- Try clicking `🔄 Refresh` button

**Blocks positioned incorrectly?**
- This usually means time zone issues
- Check that all times are in same timezone
- Report if blocks consistently overlap wrong

**Stats showing "NaN" or "--"?**
- Data hasn't loaded yet
- Click refresh or wait a few seconds
- Check network tab for failed API calls

**Edit mode not working?**
- Make sure you clicked "✏️ Edit Availability"
- Button should turn green: "✓ View Mode"  
- If still broken, refresh page

---

## Feedback

This is a brand new feature! Please report:
- Bugs or unexpected behavior  
- UI/UX confusion
- Feature requests
- Performance issues

Contact: [your email/support system]

---

**Happy Scheduling! 🎉**
