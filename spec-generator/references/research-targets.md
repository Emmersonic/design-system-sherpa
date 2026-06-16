# Research Targets by Component Class

Reference this file when Phase 4 research needs more specific direction based on the type of component being documented.

---

## Priority search order (all component classes)

Always start here before going to component-specific sources:

1. **W3C APG pattern** — `w3.org/WAI/ARIA/apg/patterns/[pattern-name]` — authoritative for keyboard and ARIA
2. **Radix UI** — `radix-ui.com/primitives/docs/components/[name]` — anatomy, API conventions, composition
3. **Adobe Spectrum** — `spectrum.adobe.com/page/[component-name]` — states, accessibility depth
4. **IBM Carbon** — `carbondesignsystem.com/components/[name]/usage` — anatomy, usage guidelines
5. **Shopify Polaris** — `polaris.shopify.com/components/[name]` — content guidelines, usage rules
6. **GitHub Primer** — `primer.style/components/[name]` — API and composability
7. **Material Design 3** — `m3.material.io/components/[name]` — state and motion specs

---

## Component class → APG pattern mapping

| Component | APG Pattern URL slug |
|---|---|
| Accordion | `accordion` |
| Alert / Banner | `alert` |
| Breadcrumb | `breadcrumb` |
| Button | `button` |
| Checkbox | `checkbox` |
| Combobox / Autocomplete | `combobox` |
| Date Picker | `dialog-modal` + `spinbutton` |
| Dialog / Modal | `dialog-modal` |
| Disclosure | `disclosure` |
| Drawer / Side panel | `dialog-modal` |
| Dropdown Menu | `menu-button` |
| Feed | `feed` |
| File upload | No APG pattern — use Carbon + Spectrum |
| Form / Form field | No single APG pattern — use `alertdialog` for errors |
| Listbox | `listbox` |
| Menu | `menu-and-menubar` |
| Navigation Menu | `disclosure-navigation-listbox` |
| Pagination | No APG pattern — use Carbon + Polaris |
| Popover | `dialog-modal` (non-modal) |
| Progress | No APG pattern — use ARIA `progressbar` role |
| Radio Group | `radio-group` |
| Select | `listbox` |
| Slider | `slider` |
| Spinner / Loading | No APG pattern — use ARIA `status` role |
| Switch / Toggle | `switch` |
| Table / Data grid | `grid` |
| Tabs | `tabs` |
| Tag / Chip | No APG pattern — use `button` role |
| Text Input / Text Field | No APG pattern — use ARIA `textbox` role |
| Textarea | No APG pattern — use ARIA `textbox` with `aria-multiline` |
| Toast / Notification | `alert` |
| Toggle Button | `button` with `aria-pressed` |
| Tooltip | `tooltip` |
| Tree View | `treeview` |

---

## Component classes with no APG pattern

For these, rely on research across Spectrum, Carbon, and Polaris. Note in the spec that no APG pattern exists.

- Avatar
- Badge / Pill
- Calendar (standalone display)
- Card
- Carousel / Slideshow
- Chip / Tag (non-interactive)
- Color Picker
- Data Table (non-interactive)
- Divider / Separator
- Empty State
- File Upload
- Image
- Pagination
- Progress Steps / Stepper
- Skeleton / Loading placeholder
- Spinner

---

## Research notes by component class

### Inputs (text, number, search, password)
- ARIA role is implicit (`textbox`) — no explicit role needed on `<input>`
- APG does not have a dedicated text input pattern; use the `combobox` pattern for inputs with suggestions
- Key research gaps usually found in: validation timing, mobile `inputMode`, autofill suppression, RTL icon mirroring

### Select / Listbox / Combobox
- These three are commonly confused — clarify which pattern this component is closest to before researching
- APG patterns differ significantly between `listbox` (no text filter) and `combobox` (with text filter)
- Keyboard interaction tables from APG are the most reliable artifact for these component classes

### Overlay components (Dialog, Popover, Tooltip, Drawer)
- Focus trap is required for modal dialogs, optional for non-modal popovers
- Dismissal behavior (Escape, click-outside) varies — document which triggers dismiss vs. which don't
- Always check if the component has a `role="dialog"` vs. `role="tooltip"` implication — they have different keyboard models

### Navigation (Tabs, Breadcrumb, Menu)
- APG specifies two keyboard models for Tabs: "follows focus" (arrow keys activate) and "manual activation" (Enter activates)
- Document which model this component implements — this is a common spec gap
- For Menu: distinguish between menubar (always visible, horizontal) and menu (popup, triggered)

### Disclosure / Accordion
- Single-expand vs. multi-expand is a key variant that changes the ARIA model
- APG specifies `aria-expanded` on the trigger, not the panel

### Form composition (FormField, FormGroup, FieldSet)
- No APG pattern — research Carbon's "Form" and Polaris's "Form layout" patterns
- Key questions: who owns the `<label>` association, how are grouped fields labeled, where does error summary live

---

## Token research targets

When token files aren't present in the provided code, search in this order:

1. Same repo: `tokens/`, `design-tokens/`, `theme/`, `src/tokens/`, `src/styles/`
2. Package dependencies: look for `@[org]/tokens`, `@[org]/design-tokens`, `@[org]/theme` in `package.json`
3. CSS custom property declarations: grep for `--` prefixed variables in any global CSS file
4. Figma variables export: if a Figma link is provided, extract tokens from published variables
5. Style Dictionary output: look for `tokens.json`, `variables.json`, or `_variables.scss`
