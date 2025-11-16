# 🚀 TypeScript Quick Start Guide

## What Just Happened?

TypeScript is now set up in your project! Here's what was added:

### New Files
- ✅ `tsconfig.json` - TypeScript configuration
- ✅ `package.json` - Node.js package configuration
- ✅ `typescript/types.ts` - All type definitions (200+ lines!)
- ✅ `typescript/schedule.ts` - Example converted module
- ✅ `TYPESCRIPT_README.md` - Full documentation

### What TypeScript Gives You

**Before (JavaScript):**
```javascript
function displayRecurringSchedules(schedules) {
    // What's in schedules? 🤷‍♂️
    schedules.forEach(s => {
        console.log(s.workplace.name); // Could crash!
    });
}
```

**After (TypeScript):**
```typescript
function displayRecurringSchedules(schedules: RecurringSchedule[]): void {
    // TypeScript KNOWS what's in schedules! ✅
    schedules.forEach(s => {
        // Editor autocomplete shows: id, title, workplace, etc.
        console.log(s.workplace?.name); // Safe with optional chaining!
    });
}
```

## How to Use It

### Option 1: Start TypeScript watch mode (Recommended)

Open a **new terminal** and run:
```bash
cd /Users/brianabaltazar/SoftwareEngineering/apps/calendar_app
npm run watch
```

This will:
- ✅ Watch your TypeScript files
- ✅ Auto-compile when you save
- ✅ Show type errors immediately
- ✅ Keep running in background

### Option 2: Manual build

```bash
npm run build
```

### Option 3: Type check only (no compilation)

```bash
npm run type-check
```

## Converting Your JavaScript to TypeScript

### Step-by-step process:

1. **Pick a JavaScript file** (e.g., `clients.js`)
2. **Copy it** to `typescript/clients.ts`
3. **Add type annotations** gradually:
   ```typescript
   // Add parameter types
   function loadClients(specialistId: number): Promise<void> {
       // Add return type ↑
   }
   
   // Type API responses
   const clients: Client[] = await response.json();
   ```
4. **Run `npm run watch`** - see errors in real-time
5. **Fix errors** one by one (or use `any` as temporary fix)
6. **Save** - TypeScript compiles to `src/calendar_app/static/js/clients.js`
7. **Test in browser** - it should work the same!

### Example: Converting `utils.js`

**Current (JavaScript):**
```javascript
export function formatTime(timeString) {
    // Convert "14:30:00" to "2:30 PM"
    const [hours, minutes] = timeString.split(':');
    // ...
}
```

**TypeScript version:**
```typescript
export function formatTime(timeString: string): string {
    // Convert "14:30:00" to "2:30 PM"
    const [hours, minutes] = timeString.split(':');
    // TypeScript knows hours and minutes are strings!
    // ...
}
```

## Tips & Tricks

### 1. Use `type` for imports
```typescript
import type { RecurringSchedule } from './types.js';  // ✅ Correct
import { RecurringSchedule } from './types.js';        // ❌ Runtime error
```

### 2. Keep `.js` extension in imports
```typescript
import { showResponse } from './utils.js';  // ✅ Even if it's utils.ts!
```

### 3. Start with loose types
```typescript
// Strict (ideal)
function processBooking(booking: Booking): void { }

// Loose (temporary)
function processBooking(booking: any): void { }
```

### 4. Use optional chaining for safety
```typescript
// Old way (could crash)
const name = schedule.workplace.name;

// TypeScript way (safe)
const name = schedule.workplace?.name;  // undefined if no workplace
```

### 5. Type DOM elements
```typescript
const input = document.getElementById('email') as HTMLInputElement;
const value = input.value;  // TypeScript knows inputs have .value!
```

## Common Type Patterns

### API Responses
```typescript
async function loadBookings(): Promise<void> {
    const response = await fetch('/bookings');
    const bookings: Booking[] = await response.json();
    // bookings is typed!
}
```

### Event Handlers
```typescript
function handleClick(event: MouseEvent): void {
    event.preventDefault();
    // TypeScript knows about .preventDefault()!
}
```

### Form Data
```typescript
const formData: LoginFormData = {
    email: emailInput.value,
    password: passwordInput.value
};
```

## What's Already Done

✅ **Type definitions created** - 200+ lines covering:
- Specialist, Consumer, Client
- Workplace, Service, Booking
- RecurringSchedule, CalendarEvent, PTOBlock
- Form data, API responses, UI state

✅ **Example module converted** - `typescript/schedule.ts` shows the pattern

✅ **Build system configured** - Just run `npm run watch`

## Next Steps

1. **Start watch mode**: `npm run watch`
2. **Convert one module**: Try `clients.js` → `typescript/clients.ts`
3. **See the magic**: Autocomplete, error checking, refactoring
4. **Keep building**: New files can start as `.ts` from day one!

## Questions?

- Check `TYPESCRIPT_README.md` for full docs
- Look at `typescript/schedule.ts` for examples
- VS Code will show type errors inline
- Run `npm run type-check` to see all errors

---

**You now have TypeScript! 🎉** Start small, convert gradually, enjoy the safety net!
