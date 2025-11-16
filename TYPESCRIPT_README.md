# TypeScript Setup

This project uses TypeScript for type-safe JavaScript development.

## Directory Structure

```
calendar_app/
├── typescript/              # TypeScript source files (.ts)
│   ├── types.ts            # Shared type definitions
│   ├── schedule.ts         # Schedule module (TypeScript version)
│   └── ...                 # Other modules (to be converted)
├── src/calendar_app/static/js/  # Compiled JavaScript output
│   ├── schedule.js         # Compiled from typescript/schedule.ts
│   ├── schedule.js.map     # Source map for debugging
│   └── ...                 # Other JS files (vanilla or compiled)
└── tsconfig.json           # TypeScript compiler configuration
```

## Workflow

### Development

1. **Edit TypeScript files** in `typescript/` directory
2. **Run watch mode** to auto-compile on save:
   ```bash
   npm run watch
   ```
3. **Compiled JavaScript** appears in `src/calendar_app/static/js/`
4. **Refresh browser** to see changes

### One-time Build

```bash
npm run build
```

### Type Checking Only (no compilation)

```bash
npm run type-check
```

## Migration Strategy

We're gradually migrating from JavaScript to TypeScript:

### ✅ Completed
- [x] `typescript/types.ts` - All shared type definitions
- [x] `typescript/schedule.ts` - Schedule module (example)

### 🔄 In Progress
- [ ] Convert other modules as needed

### Current State
- JavaScript files in `src/calendar_app/static/js/` still work
- TypeScript files compile to the same directory
- Both can coexist during migration

## Type Definitions

All shared types are defined in `typescript/types.ts`:
- User types (Specialist, Consumer, Client)
- Workplace types
- Service types
- Booking types
- Recurring schedule types
- Calendar event types
- Form data types
- API response types

Import types in your TypeScript files:
```typescript
import type { RecurringSchedule, Workplace } from './types.js';
```

## Benefits

1. **Autocomplete** - Editor suggests properties and methods
2. **Type safety** - Catch errors before runtime
3. **Refactoring** - Rename safely across files
4. **Documentation** - Types serve as inline docs
5. **Better debugging** - Source maps link compiled code to TypeScript

## Tips

- Keep `.js` extension in imports even for `.ts` files (ES modules requirement)
- Use `type` keyword for type-only imports
- Run `npm run watch` in a separate terminal while developing
- Check `schedule.ts` as an example of converted module
