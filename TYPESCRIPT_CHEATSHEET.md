# 📋 TypeScript Quick Reference

## 🚀 Commands

```bash
# Start watch mode (recommended for development)
npm run watch

# Build once
npm run build

# Type check only (no compilation)
npm run type-check
```

## 📝 Common Type Patterns

### Import Types
```typescript
import type { Booking, Service, Client } from './types.js';
```

### Function with Types
```typescript
async function loadBookings(specialistId: number): Promise<void> {
    const response = await fetch(`/bookings/${specialistId}`);
    const bookings: Booking[] = await response.json();
    // ...
}
```

### DOM Element Types
```typescript
// Input element
const input = document.getElementById('email') as HTMLInputElement;
const value = input.value;  // TypeScript knows inputs have .value

// Select element
const select = document.getElementById('service') as HTMLSelectElement;
const selected = select.value;

// Button element
const button = document.getElementById('submit') as HTMLButtonElement;
button.disabled = true;

// Generic element (when type is unknown)
const element = document.getElementById('something') as HTMLElement | null;
```

### Optional Properties
```typescript
interface Client {
    id: number;
    name: string;
    phone?: string;  // Optional (can be undefined)
}

// Safe access with optional chaining
console.log(client.phone?.substring(0, 3));
```

### Array Types
```typescript
const bookings: Booking[] = [];
const ids: number[] = [1, 2, 3];
const names: string[] = ['Alice', 'Bob'];
```

### Union Types
```typescript
type Status = 'pending' | 'confirmed' | 'cancelled';
let status: Status = 'pending';  // ✅ OK
status = 'active';  // ❌ Error: not in union
```

### Async Functions
```typescript
async function fetchData(): Promise<Booking[]> {
    const response = await fetch('/api/bookings');
    return await response.json();
}
```

### Event Handlers
```typescript
button.addEventListener('click', (event: MouseEvent) => {
    event.preventDefault();
    // ...
});

input.addEventListener('keypress', (event: KeyboardEvent) => {
    if (event.key === 'Enter') {
        // ...
    }
});
```

### Null Checks
```typescript
// Before
if (booking && booking.consumer && booking.consumer.name) {
    console.log(booking.consumer.name);
}

// After (with optional chaining)
console.log(booking?.consumer?.name);
```

### Type Assertions
```typescript
// When you know better than TypeScript
const element = document.getElementById('myId') as HTMLInputElement;

// Alternative syntax (not recommended in .tsx files)
const element = <HTMLInputElement>document.getElementById('myId');
```

## 🎯 Available Types

### User Types
- `Specialist` - Professional user
- `Consumer` - Customer
- `Client` - Consumer from professional's view

### Business Types
- `Workplace` - Business location
- `Service` - Service offering
- `Booking` - Appointment booking
- `BookingStatus` - Status enum

### Schedule Types
- `RecurringSchedule` - Recurring availability
- `CalendarEvent` - Calendar event
- `PTOBlock` - Time off
- `DayOfWeek` - 0-6 (Monday-Sunday)

### Form Types
- `LoginFormData`
- `RegisterFormData`
- `ProfileUpdateData`
- `RecurringScheduleCreate`

### API Types
- `ApiResponse<T>` - Wrapped response
- `PaginatedResponse<T>` - Paginated data

### Utility Types
- `MessageType` - 'success' | 'error' | 'info' | 'warning'
- `PhoneValidationResult` - Phone validation
- `TimeString` - "HH:MM" format
- `DateString` - "YYYY-MM-DD" format

## ⚡ Quick Tips

### 1. Use `type` for imports
```typescript
import type { Booking } from './types.js';  // ✅ Correct
import { Booking } from './types.js';        // ❌ Runtime error
```

### 2. Keep `.js` extension
```typescript
import { foo } from './utils.js';  // ✅ Even for .ts files
import { foo } from './utils';     // ❌ Won't work
```

### 3. Handle null/undefined
```typescript
// Use optional chaining
booking?.consumer?.name

// Or explicit check
if (booking && booking.consumer) {
    console.log(booking.consumer.name);
}

// Or nullish coalescing
const name = booking?.consumer?.name ?? 'Unknown';
```

### 4. Type function parameters
```typescript
function process(id: number, name: string, optional?: boolean) {
    // ...
}
```

### 5. Use JSDoc for documentation
```typescript
/**
 * Load bookings for a specialist
 * @param specialistId - ID of the specialist
 * @returns Promise that resolves when loaded
 */
async function loadBookings(specialistId: number): Promise<void> {
    // ...
}
```

## 🐛 Common Errors & Fixes

### Error: "Cannot find module"
```typescript
// ❌ Wrong
import { foo } from './utils';

// ✅ Correct
import { foo } from './utils.js';
```

### Error: "Property X does not exist"
```typescript
// ❌ Wrong - typo
booking.servis.name

// ✅ Correct
booking.service.name
```

### Error: "Type X is not assignable to type Y"
```typescript
// ❌ Wrong type
const id: number = "123";

// ✅ Correct type
const id: number = 123;

// ✅ Or parse
const id: number = parseInt("123");
```

### Error: "Object is possibly null"
```typescript
// ❌ Unsafe
const value = document.getElementById('id').value;

// ✅ Safe with optional chaining
const value = (document.getElementById('id') as HTMLInputElement | null)?.value;

// ✅ Or null check
const element = document.getElementById('id') as HTMLInputElement | null;
if (element) {
    const value = element.value;
}
```

### Error: "Parameter X is declared but never used"
```typescript
// ❌ Unused parameter
function foo(unusedParam: string) { }

// ✅ Prefix with underscore
function foo(_unusedParam: string) { }

// ✅ Or remove it
function foo() { }
```

## 📚 Resources

- **Types**: See all in `typescript/types.ts`
- **Examples**: Check converted modules
  - `typescript/utils.ts` - Utility patterns
  - `typescript/navigation.ts` - DOM & events
  - `typescript/schedule.ts` - Complex logic

- **Docs**:
  - `TYPESCRIPT_QUICKSTART.md` - Get started
  - `TYPESCRIPT_README.md` - Full guide
  - `TYPESCRIPT_PROGRESS.md` - What's converted

## ✅ Checklist for Converting a Module

1. [ ] Copy `.js` file to `typescript/` as `.ts`
2. [ ] Add type imports at top
3. [ ] Add parameter types to functions
4. [ ] Add return types to functions
5. [ ] Type variables and constants
6. [ ] Handle null/undefined safely
7. [ ] Run `npm run build` to check
8. [ ] Fix any errors shown
9. [ ] Test in browser
10. [ ] Commit changes

---

**Start Here**: `npm run watch` → Edit a `.ts` file → Save → See it compile! 🎉
