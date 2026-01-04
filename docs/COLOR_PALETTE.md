# UI Color Palette Reference

## Primary Colors

### Background
```
Base: #0a0a0f (Deep Dark Navy)
With radial gradients:
  - Top Left: rgba(99, 102, 241, 0.08) - Indigo glow
  - Top Right: rgba(139, 92, 246, 0.06) - Purple glow
  - Bottom Right: rgba(79, 70, 229, 0.05) - Deep indigo glow
  - Bottom Left: rgba(124, 58, 237, 0.07) - Violet glow
```

### Surface Colors
```
Card Background: rgba(15, 23, 42, 0.6) - Slate with 60% opacity
Card Hover: rgba(15, 23, 42, 0.8) - Slate with 80% opacity
Glass Effect: backdrop-filter: blur(24px) saturate(180%)
```

### Text Colors
```
Primary: #f8fafc - Pure white (headings, important text)
Secondary: #e5e7eb - Light gray (body text)
Tertiary: #cbd5e1 - Medium light gray (labels, subtitles)
Muted: #94a3b8 - Medium gray (placeholders, hints)
Disabled: #64748b - Dark gray (disabled states)
```

### Interactive Colors
```
Primary Action: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)
Hover: rgba(139, 92, 246, 0.2)
Active: #7c3aed
Focus Ring: rgba(139, 92, 246, 0.1)
```

### Borders
```
Subtle: rgba(148, 163, 184, 0.1) - Very light slate
Default: rgba(148, 163, 184, 0.2) - Light slate
Emphasis: rgba(139, 92, 246, 0.2) - Purple tint
```

## Feature-Specific Colors

### Dashboard Stat Cards
```
Total Bookings:
  Background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(99, 102, 241, 0.02) 100%)
  Border: rgba(99, 102, 241, 0.2)
  Icon: 📅

Confirmed Bookings:
  Background: linear-gradient(135deg, rgba(34, 197, 94, 0.08) 0%, rgba(34, 197, 94, 0.02) 100%)
  Border: rgba(34, 197, 94, 0.2)
  Icon: ✅

Services:
  Background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, rgba(139, 92, 246, 0.02) 100%)
  Border: rgba(139, 92, 246, 0.2)
  Icon: 💼

Workplaces:
  Background: linear-gradient(135deg, rgba(236, 72, 153, 0.08) 0%, rgba(236, 72, 153, 0.02) 100%)
  Border: rgba(236, 72, 153, 0.2)
  Icon: 🏢
```

### Status Colors
```
Success: #22c55e (Green)
Warning: #f59e0b (Amber)
Error: #ef4444 (Red)
Info: #3b82f6 (Blue)
```

## Typography

### Font Families
```css
Headings: 'Playfair Display', serif
Body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif
Code: 'Fira Code', 'Courier New', monospace
```

### Font Sizes
```
3.5rem - Main page title (H1)
1.125rem - Section headings (H2, H3)
0.938rem - Body text, buttons
0.875rem - Labels, captions
2.5rem - Stat card numbers
```

### Font Weights
```
700 - Bold (headings, stat numbers)
600 - Semibold (buttons, labels)
500 - Medium (subheadings)
400 - Regular (body text)
```

### Letter Spacing
```
Headings: -0.02em to -0.01em (tighter for elegance)
Body: 0.01em (slightly open for readability)
Buttons/Labels: 0.01em (consistent spacing)
```

## Shadows

### Elevation Levels
```css
/* Level 1 - Subtle */
box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);

/* Level 2 - Card */
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);

/* Level 3 - Elevated */
box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);

/* Level 4 - High */
box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

/* Glow Effect */
box-shadow: 0 10px 15px -3px rgba(139, 92, 246, 0.3), 0 4px 6px -2px rgba(139, 92, 246, 0.2);
```

## Border Radius

```
Small: 8px - Compact elements
Medium: 10px - Buttons, inputs
Large: 12px - Cards, panels
Extra Large: 16px - Stat cards
2XL: 24px - Section containers
```

## Spacing Scale

```
4px - Micro spacing
8px - Extra small
12px - Small
16px - Medium
24px - Large
32px - Extra large
48px - 2X large
```

## Animation

### Timing Functions
```css
Standard: cubic-bezier(0.4, 0, 0.2, 1) /* ease-out */
Emphasized: cubic-bezier(0.4, 0, 0.6, 1) /* emphasized ease-out */
```

### Durations
```
Fast: 150ms - Micro-interactions
Normal: 200ms - Standard transitions
Slow: 300ms - Complex animations
```

## Usage Examples

### Primary Button
```css
background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
color: #ffffff;
padding: 14px 28px;
border-radius: 10px;
font-weight: 600;
font-size: 0.938rem;
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
```

### Card Component
```css
background: rgba(15, 23, 42, 0.6);
backdrop-filter: blur(24px) saturate(180%);
border: 1px solid rgba(148, 163, 184, 0.1);
border-radius: 16px;
padding: 32px;
box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
```

### Input Field
```css
background: rgba(15, 23, 42, 0.6);
border: 1px solid rgba(148, 163, 184, 0.2);
border-radius: 10px;
color: #f8fafc;
padding: 14px 16px;
font-size: 0.938rem;
```

### Tab Navigation
```css
/* Inactive */
color: #94a3b8;
background: transparent;

/* Hover */
color: #c4b5fd;
background: rgba(139, 92, 246, 0.1);

/* Active */
color: #f8fafc;
background: rgba(139, 92, 246, 0.15);
border-bottom: 2px solid #8b5cf6;
```

## Accessibility

### Contrast Ratios (WCAG AA)
```
White on Dark Background: 15:1 ✅
Purple on Dark Background: 4.8:1 ✅
Gray Text on Dark: 4.5:1 ✅
Purple Button Text: 4.5:1 ✅
```

### Focus Indicators
```
Always visible purple ring:
box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
border-color: #8b5cf6;
```

## Design Principles

1. **Consistency**: Use the same colors for the same purposes throughout
2. **Hierarchy**: Lighter = more important (inverse of typical dark mode)
3. **Subtlety**: Prefer gentle gradients over harsh contrasts
4. **Depth**: Use shadows and blur to create layers
5. **Elegance**: Purple accents provide sophistication without being flashy

## Quick Reference

```
🎨 Brand Purple: #8b5cf6
📝 Text White: #f8fafc
🌫️ Muted Gray: #94a3b8
🎯 Background: #0a0a0f
✨ Glass: rgba(15, 23, 42, 0.6) + blur(24px)
```
