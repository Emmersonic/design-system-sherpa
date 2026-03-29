# Naming Examples by Category

Reference for the `token-foundation` skill. Use these as concrete examples when explaining the naming convention to a designer.

---

## Color

### Primitives
```
color/neutral/0      → #FFFFFF
color/neutral/50     → #F9FAFB
color/neutral/100    → #F3F4F6
color/neutral/200    → #E5E7EB
color/neutral/500    → #6B7280
color/neutral/900    → #111827

color/blue/100       → #DBEAFE
color/blue/500       → #3B82F6
color/blue/600       → #2563EB
color/blue/700       → #1D4ED8

color/red/100        → #FEE2E2
color/red/500        → #EF4444
color/red/700        → #B91C1C

color/green/100      → #D1FAE5
color/green/500      → #10B981
color/green/700      → #047857
```

### Semantic — surface
```
color/surface/default        → color/neutral/0      (light) / color/neutral/900 (dark)
color/surface/secondary      → color/neutral/50     (light) / color/neutral/800 (dark)
color/surface/brand          → color/blue/500       (light) / color/blue/600    (dark)
color/surface/brand-subtle   → color/blue/100       (light) / color/blue/900    (dark)
color/surface/danger         → color/red/100        (light) / color/red/900     (dark)
color/surface/success        → color/green/100      (light) / color/green/900   (dark)
```

### Semantic — text
```
color/text/primary           → color/neutral/900    (light) / color/neutral/50  (dark)
color/text/secondary         → color/neutral/500    (light) / color/neutral/400 (dark)
color/text/disabled          → color/neutral/300    (light) / color/neutral/600 (dark)
color/text/on-brand          → color/neutral/0      (both modes — white on blue)
color/text/danger            → color/red/700        (light) / color/red/300     (dark)
color/text/success           → color/green/700      (light) / color/green/300   (dark)
```

### Semantic — border
```
color/border/default         → color/neutral/200    (light) / color/neutral/700 (dark)
color/border/strong          → color/neutral/400    (light) / color/neutral/500 (dark)
color/border/focus           → color/blue/500       (both modes)
color/border/danger          → color/red/500        (both modes)
```

### Component — button
```
button/background/primary/default    → color/surface/brand
button/background/primary/hover      → color/blue/600   (direct primitive — slightly darker)
button/background/primary/disabled   → color/surface/brand-subtle
button/text/primary/default          → color/text/on-brand
button/text/primary/disabled         → color/text/disabled
button/border/primary/focus          → color/border/focus

button/background/secondary/default  → color/surface/default
button/background/secondary/hover    → color/surface/secondary
button/border/secondary/default      → color/border/default
button/text/secondary/default        → color/text/primary
```

---

## Spacing

### Primitives
```
spacing/0    → 0px
spacing/1    → 4px
spacing/2    → 8px
spacing/3    → 12px
spacing/4    → 16px
spacing/5    → 20px
spacing/6    → 24px
spacing/8    → 32px
spacing/10   → 40px
spacing/12   → 48px
spacing/16   → 64px
```

### Semantic (optional — only if spacing has meaningful named roles)
```
spacing/component/xs   → spacing/1  (4px)
spacing/component/sm   → spacing/2  (8px)
spacing/component/md   → spacing/4  (16px)
spacing/component/lg   → spacing/6  (24px)

spacing/layout/sm      → spacing/8  (32px)
spacing/layout/md      → spacing/12 (48px)
spacing/layout/lg      → spacing/16 (64px)
```

---

## Typography

### Primitives
```
font-family/sans     → "Inter", system-ui, sans-serif
font-family/mono     → "JetBrains Mono", monospace

font-size/12         → 12px
font-size/14         → 14px
font-size/16         → 16px
font-size/18         → 18px
font-size/20         → 20px
font-size/24         → 24px
font-size/32         → 32px

font-weight/regular  → 400
font-weight/medium   → 500
font-weight/semibold → 600
font-weight/bold     → 700

line-height/tight    → 1.25
line-height/normal   → 1.5
line-height/relaxed  → 1.75
```

### Semantic (usually Figma text styles, not variables)
```
text-style/display-lg    → font-size/32, font-weight/bold,   line-height/tight
text-style/heading-lg    → font-size/24, font-weight/semibold, line-height/tight
text-style/heading-md    → font-size/20, font-weight/semibold, line-height/tight
text-style/body-lg       → font-size/16, font-weight/regular, line-height/normal
text-style/body-md       → font-size/14, font-weight/regular, line-height/normal
text-style/label-md      → font-size/14, font-weight/medium,  line-height/normal
text-style/caption       → font-size/12, font-weight/regular, line-height/normal
text-style/code          → font-family/mono, font-size/14, line-height/relaxed
```

---

## Border Radius

### Primitives
```
border-radius/none   → 0px
border-radius/sm     → 4px
border-radius/md     → 8px
border-radius/lg     → 12px
border-radius/xl     → 16px
border-radius/2xl    → 24px
border-radius/full   → 9999px
```

### Semantic (optional)
```
border-radius/component/button  → border-radius/md
border-radius/component/input   → border-radius/md
border-radius/component/card    → border-radius/lg
border-radius/component/badge   → border-radius/full
border-radius/layout/panel      → border-radius/xl
```

---

## Elevation / Shadow

### Primitives (defined as Figma effect styles, not variables)
```
elevation/0    → no shadow
elevation/1    → 0 1px 2px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.10)
elevation/2    → 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)
elevation/3    → 0 10px 15px rgba(0,0,0,0.10), 0 4px 6px rgba(0,0,0,0.05)
elevation/4    → 0 20px 25px rgba(0,0,0,0.10), 0 10px 10px rgba(0,0,0,0.04)
```

---

## Motion / Duration

### Primitives
```
motion/duration/instant    → 0ms
motion/duration/fast       → 100ms
motion/duration/normal     → 200ms
motion/duration/slow       → 300ms
motion/duration/slower     → 500ms

motion/easing/linear       → cubic-bezier(0, 0, 1, 1)
motion/easing/ease-in      → cubic-bezier(0.4, 0, 1, 1)
motion/easing/ease-out     → cubic-bezier(0, 0, 0.2, 1)
motion/easing/ease-in-out  → cubic-bezier(0.4, 0, 0.2, 1)
motion/easing/spring       → cubic-bezier(0.34, 1.56, 0.64, 1)
```
