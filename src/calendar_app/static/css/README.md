# Using Shared CSS in Templates

## Quick Start

To use the shared CSS in your templates, add this to the `<head>` section:

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Page Title</title>
    
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Shared CSS -->
    <link rel="stylesheet" href="/static/css/shared.css">
    
    <!-- Page-specific CSS (if needed) -->
    <style>
        /* Your custom styles here */
    </style>
</head>
```

## Available CSS Classes

### Layout
- `.container` - Main content container with max-width and padding
- `.card` - Card component with hover effects
- `.glass-panel` - Glassmorphism panel effect

### Typography
- `.page-title` - Main page heading with gradient
- `.section-title` - Section headings
- `.service-title` - Service/product titles
- `.specialist-name` - Professional names

### Buttons
- `.btn-primary` - Primary action button (gold gradient)
- `.btn-secondary` - Secondary action button (glass effect)

### Forms
- `.form-group` - Form field container
- `.form-label` - Form labels
- `.form-input` - Text inputs
- `.form-textarea` - Textarea inputs
- `.form-select` - Select dropdowns

### Time Slots
- `.time-slots` - Grid container for time slots
- `.time-slot` - Individual time slot button
- `.time-slot.selected` - Selected time slot
- `.time-slot.unavailable` - Disabled time slot

### Navigation
- `.back-link` - Fixed back navigation button

### Messages
- `.error-message` - Error alert
- `.success-message` - Success alert
- `.loading` - Loading state

### Utilities
- `.text-center` - Center text
- `.mb-1`, `.mb-2`, `.mb-3`, `.mb-4` - Bottom margins
- `.mt-1`, `.mt-2`, `.mt-3`, `.mt-4` - Top margins
- `.hidden` - Hide element

## Migration Guide

When converting existing templates:

1. **Add the shared CSS link** in the `<head>` section
2. **Remove duplicated base styles** (`*`, `body`, common fonts)
3. **Replace inline styles** with CSS classes where possible
4. **Keep page-specific styles** in `<style>` tags for unique elements

### Example Before:
```html
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #6464a0ff 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    .my-button {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        padding: 15px 40px;
        /* ... */
    }
</style>
```

### Example After:
```html
<link rel="stylesheet" href="/static/css/shared.css">
<style>
    /* Only page-specific styles */
    .unique-element {
        /* your custom styles */
    }
</style>

<!-- In HTML -->
<button class="btn-primary">Click Me</button>
```

## Benefits

- ✅ Reduced file sizes (templates ~50% smaller)
- ✅ Consistent styling across pages
- ✅ Faster page loads (CSS cached by browser)
- ✅ Easier maintenance (change once, apply everywhere)
- ✅ Better performance (less duplicate CSS parsing)

## Notes

- The shared CSS is already responsive (mobile-friendly)
- Font imports are still in each template (so pages work independently)
- You can override shared styles with page-specific CSS
- All colors use the luxury gold theme (#FFD700, #FFA500)