# Documentation Research Targets by Component Class

Reference this file when Phase 2 research needs more specific direction. Focus on Usage / Guidelines tabs — not Code or API tabs.

---

## Priority search order (all component classes)

1. **Shopify Polaris** — `polaris.shopify.com/components/[name]` — content guidelines, real do/don'ts, best rationale
2. **IBM Carbon** — `carbondesignsystem.com/components/[name]/usage` — deep usage guidance, decision tables
3. **Atlassian Design System** — `atlassian.design/components/[name]/usage` — decision frameworks, clear when/when-not
4. **Material Design 3** — `m3.material.io/components/[name]/guidelines` — semantic distinctions, motion/behavior
5. **Apple HIG** — `developer.apple.com/design/human-interface-guidelines/[name]` — behavioral principles, mobile
6. **Adobe Spectrum** — `spectrum.adobe.com/page/[name]` — accessibility for designers, usage nuance
7. **GitHub Primer** — `primer.style/components/[name]` — context-specific usage, compositional guidance

---

## Component class → documentation focus notes

### Button / Action

- **Best rationale sources:** Polaris (label writing, semantic hierarchy), Carbon (button types decision grid)
- **Key do/don'ts for designers:** multiple primary actions in one section, danger button misuse, button vs. link decision
- **Semantic distinctions to document:** primary / secondary / tertiary hierarchy; destructive/danger meaning; ghost vs. plain
- **Common designer mistakes:** using primary button for every action on a page; using danger for routine deletes; icon-only buttons without visible labels
- **Polaris:** `polaris.shopify.com/components/actions/button`
- **Carbon:** `carbondesignsystem.com/components/button/usage`
- **Material:** `m3.material.io/components/buttons/guidelines`

### Input / Text Field

- **Best rationale sources:** Nielsen Norman Group (label placement), Carbon (helper text vs. tooltip), Polaris (placeholder anti-pattern)
- **Key do/don'ts for designers:** placeholder as label (inaccessible), helper text vs. tooltip, label position
- **Common designer mistakes:** using placeholder text as the only label; omitting helper text for complex inputs; unclear error state placement
- **Polaris:** `polaris.shopify.com/components/selection-and-input/text-field`
- **Carbon:** `carbondesignsystem.com/components/text-input/usage`

### Select / Dropdown

- **Key do/don'ts for designers:** using select for fewer than 5 options (use radio instead), using select for actions (use a menu instead)
- **Semantic distinctions:** select (form value) vs. dropdown menu (actions) vs. combobox (filtered search)
- **Carbon:** `carbondesignsystem.com/components/select/usage`
- **Material:** `m3.material.io/components/menus/guidelines`

### Modal / Dialog

- **Best rationale sources:** Nielsen Norman (interruption cost), Polaris (modal overuse), HIG (sheets vs. dialogs)
- **Key do/don'ts for designers:** using modals for complex workflows, nesting modals, modal without a clear dismissal path
- **Common designer mistakes:** putting forms with many fields in a modal; stacking modals; using confirmation modals for non-destructive actions
- **Polaris:** `polaris.shopify.com/components/overlays/modal`
- **Carbon:** `carbondesignsystem.com/components/modal/usage`
- **HIG:** `developer.apple.com/design/human-interface-guidelines/sheets`

### Tooltip

- **Best rationale sources:** Nielsen Norman (tooltip discoverability), Polaris (tooltip content rules)
- **Key do/don'ts for designers:** using tooltip for essential information, tooltip on disabled elements
- **Common designer mistakes:** putting critical info in a tooltip; using tooltip as a replacement for a visible label; triggering on focus for complex content
- **Polaris:** `polaris.shopify.com/components/overlays/tooltip`

### Toast / Notification / Banner

- **Best rationale sources:** Carbon (notification types decision), Polaris (when not to use toast)
- **Semantic distinctions:** toast (transient, system-initiated) vs. banner (persistent, page-level) vs. inline message (contextual, field-level)
- **Key do/don'ts for designers:** using toast for errors that require action, stacking multiple toasts
- **Carbon:** `carbondesignsystem.com/components/notification/usage`
- **Polaris:** `polaris.shopify.com/components/feedback-indicators/toast`

### Tabs

- **Best rationale sources:** Nielsen Norman (tabs vs. accordion), Carbon (tabs vs. navigation)
- **Key do/don'ts for designers:** using tabs for sequential steps (use stepper), exceeding ~6 tabs, nesting tabs
- **Semantic distinctions:** tabs (parallel views of same content type) vs. steps (sequential, ordered) vs. navigation (cross-page)
- **Carbon:** `carbondesignsystem.com/components/tabs/usage`
- **Material:** `m3.material.io/components/tabs/guidelines`

### Checkbox / Radio / Switch

- **Best rationale sources:** Nielsen Norman (checkbox vs. radio), Polaris (switch vs. checkbox timing)
- **Semantic distinctions:** checkbox (multi-select, form value, requires save) vs. radio (single-select, mutually exclusive) vs. switch (immediate effect, no save needed)
- **Key do/don'ts for designers:** using switch for multi-option groups, using checkbox for single on/off with immediate effect
- **Carbon:** `carbondesignsystem.com/components/checkbox/usage` and `carbondesignsystem.com/components/toggle/usage`
- **Polaris:** `polaris.shopify.com/components/selection-and-input/checkbox`

### Badge / Tag / Chip

- **Best rationale sources:** Carbon (status vs. label), Material (chip types)
- **Semantic distinctions:** badge (status indicator, system-generated) vs. tag (categorization, user-applied) vs. chip (interactive filter or selection)
- **Key do/don'ts for designers:** using badge color without text label, using interactive chips where non-interactive tags are correct
- **Material:** `m3.material.io/components/chips/guidelines`
- **Carbon:** `carbondesignsystem.com/components/tag/usage`

### Empty State

- **Best rationale sources:** Polaris (empty state types), Google Material (three types: first-use, cleared, zero-results)
- **Key do/don'ts for designers:** using the same empty state for all three scenarios, omitting a CTA when first-use empty state is the trigger
- **Common designer mistakes:** writing generic "no data" copy; missing the opportunity for a first-use CTA; using error imagery for zero-results
- **Material:** `m3.material.io/foundations/empty-states`
- **Polaris:** `polaris.shopify.com/patterns/empty-states`

### Form Layout

- **Best rationale sources:** Nielsen Norman (form design), Carbon (form structure), Polaris (form patterns)
- **Key do/don'ts for designers:** multi-column forms reducing completion rates, ambiguous required/optional field conventions, unclear error recovery
- **Common designer mistakes:** using multiple columns without reason; omitting inline validation; mixing required/optional without convention
- **Carbon:** `carbondesignsystem.com/patterns/forms-pattern`
- **Polaris:** `polaris.shopify.com/patterns/form-layout`

### Navigation (primary nav, side nav, breadcrumb)

- **Best rationale sources:** Nielsen Norman (navigation design), Carbon (navigation patterns), HIG (navigation hierarchy)
- **Semantic distinctions:** primary nav (destination) vs. breadcrumb (wayfinding) vs. tabs (parallel views) vs. sidebar (utility/context)
- **Key do/don'ts for designers:** using breadcrumb for shallow hierarchies (≤2 levels), mixing navigation patterns that imply different mental models
- **Carbon:** `carbondesignsystem.com/patterns/navigation-pattern`

---

## Patterns with no direct component equivalent

For these, research focuses on product design best practices across systems rather than a specific component:

- Empty state (multi-component composition)
- Onboarding / progressive disclosure
- Data table / list layout patterns
- Search results / filtering patterns
- Loading and skeleton patterns
- Confirmation and destructive action patterns
- Error recovery patterns
- Settings / preference flows

For these, prioritise: Polaris patterns section, Carbon patterns section, Nielsen Norman Group articles, and Baymard Institute (for e-commerce and form patterns).

---

## What to extract from each system's Usage tab

Focus on extracting these specific things — not the component props or code:

| Extract | Where to find it | Notes |
|---|---|---|
| When to use / not use | "Usage" or "Overview" section | Capture the alternatives named |
| Variant semantic meanings | "Variants" or "Types" section | Why does each variant exist — what does it *communicate*? |
| Do/Don't examples | "Best practices" or "Do/Don't" sections | Only keep things designers could actually do wrong |
| Content/copy rules | "Content" or "Writing" section | Label conventions, length limits, tone |
| Accessibility notes for designers | "Accessibility" section | What the designer ensures, not what code to write |
| Research citations | Inline or footnote references | Cite these in the output if present |
