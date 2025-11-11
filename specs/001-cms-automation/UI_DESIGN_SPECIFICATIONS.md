# UI Design Specifications - CMS Automation System

**Version**: 1.0.0
**Date**: 2025-10-27
**Design Tool**: Figma / Sketch / Adobe XD Compatible
**Target Platforms**: Web (Desktop + Tablet + Mobile)

---

## 📐 Document Overview

This document provides complete UI/UX design specifications for implementing the CMS Automation frontend. It is designed to be used with design tools like Figma, Sketch, or Adobe XD.

**Audience**:
- UI/UX Designers creating mockups and prototypes
- Frontend Engineers implementing components
- Product Managers reviewing designs

**Related Documents**:
- [UI Gaps Analysis](../../docs/UI_GAPS_ANALYSIS.md) - Functional requirements
- [UI Implementation Tasks](./UI_IMPLEMENTATION_TASKS.md) - Technical implementation
- [spec.md FR-046 to FR-070](./spec.md) - Formal requirements

---

## 🎨 Part 1: Design System

### 1.1 Color Palette

#### Primary Colors

```
Primary-50:  #EEF2FF  (Lightest)
Primary-100: #E0E7FF
Primary-200: #C7D2FE
Primary-300: #A5B4FC
Primary-400: #818CF8
Primary-500: #6366F1  ⭐ Main Brand Color
Primary-600: #4F46E5  (Hover State)
Primary-700: #4338CA
Primary-800: #3730A3
Primary-900: #312E81  (Darkest)
```

**Usage**:
- Primary-500: Main CTA buttons, active states, links
- Primary-600: Button hover states
- Primary-50: Subtle backgrounds for highlighted content

#### Neutral Colors (Grays)

```
Gray-50:  #F9FAFB  (Page Background)
Gray-100: #F3F4F6  (Card Background)
Gray-200: #E5E7EB  (Borders)
Gray-300: #D1D5DB  (Disabled States)
Gray-400: #9CA3AF  (Placeholder Text)
Gray-500: #6B7280  (Secondary Text)
Gray-600: #4B5563  (Body Text)
Gray-700: #374151
Gray-800: #1F2937  (Headings)
Gray-900: #111827  (Darkest Text)
```

#### Semantic Colors

**Success (Green)**:
```
Success-50:  #F0FDF4
Success-500: #22C55E  ⭐ Success States
Success-600: #16A34A  (Hover)
Success-700: #15803D
```

**Warning (Yellow)**:
```
Warning-50:  #FFFBEB
Warning-500: #F59E0B  ⭐ Warning States
Warning-600: #D97706  (Hover)
```

**Error (Red)**:
```
Error-50:  #FEF2F2
Error-500: #EF4444  ⭐ Error States
Error-600: #DC2626  (Hover)
Error-700: #B91C1C
```

**Info (Blue)**:
```
Info-50:  #EFF6FF
Info-500: #3B82F6  ⭐ Info States
Info-600: #2563EB  (Hover)
```

---

### 1.2 Typography

**Font Family**:
```
Primary: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
Monospace: "Fira Code", "Courier New", monospace (for code)
```

**Font Sizes & Line Heights**:

| Name | Size | Line Height | Weight | Usage |
|------|------|-------------|--------|-------|
| **Display** | 48px | 56px | 700 (Bold) | Hero Headings |
| **Heading 1** | 36px | 44px | 700 | Page Titles |
| **Heading 2** | 30px | 38px | 600 (Semibold) | Section Titles |
| **Heading 3** | 24px | 32px | 600 | Subsection Titles |
| **Heading 4** | 20px | 28px | 600 | Card Titles |
| **Body Large** | 18px | 28px | 400 (Regular) | Important Body Text |
| **Body** | 16px | 24px | 400 | Default Body Text |
| **Body Small** | 14px | 20px | 400 | Secondary Text |
| **Caption** | 12px | 16px | 400 | Labels, Hints |
| **Overline** | 12px | 16px | 700 | ALL CAPS LABELS |

**Font Weights**:
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

---

### 1.3 Spacing System (8px Grid)

**Base Unit**: 8px

```
Space-0:  0px
Space-1:  4px   (0.5 × base)
Space-2:  8px   (1 × base)  ⭐ Most Common
Space-3:  12px  (1.5 × base)
Space-4:  16px  (2 × base)  ⭐ Most Common
Space-5:  20px  (2.5 × base)
Space-6:  24px  (3 × base)
Space-8:  32px  (4 × base)
Space-10: 40px  (5 × base)
Space-12: 48px  (6 × base)
Space-16: 64px  (8 × base)
Space-20: 80px  (10 × base)
Space-24: 96px  (12 × base)
```

**Usage Guidelines**:
- **Component Padding**: Space-4 (16px) or Space-6 (24px)
- **Component Margins**: Space-4 (16px) or Space-6 (24px)
- **Section Spacing**: Space-8 (32px) or Space-12 (48px)
- **Icon Spacing**: Space-2 (8px) or Space-3 (12px)

---

### 1.4 Border Radius

```
Radius-None: 0px
Radius-SM:   4px   (Buttons, Inputs)
Radius-MD:   8px   (Cards, Modals)
Radius-LG:   12px  (Large Cards)
Radius-XL:   16px  (Hero Cards)
Radius-Full: 9999px (Pills, Avatars)
```

---

### 1.5 Shadows

**Elevation System**:

```css
/* Shadow-SM: Small components (Dropdown menus) */
box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);

/* Shadow-MD: Cards, Buttons on hover */
box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06);

/* Shadow-LG: Modals, Popovers */
box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
            0 4px 6px -2px rgba(0, 0, 0, 0.05);

/* Shadow-XL: Drawers, Full-screen overlays */
box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1),
            0 10px 10px -5px rgba(0, 0, 0, 0.04);

/* Shadow-2XL: Hero sections */
box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
```

---

### 1.6 Animation & Transitions

**Duration**:
```
Fast:   150ms  (Hover effects, small changes)
Normal: 200ms  (Default transitions)
Slow:   300ms  (Modal open/close, page transitions)
```

**Easing Functions**:
```
Ease-In:     cubic-bezier(0.4, 0, 1, 1)
Ease-Out:    cubic-bezier(0, 0, 0.2, 1)  ⭐ Recommended
Ease-In-Out: cubic-bezier(0.4, 0, 0.2, 1)
```

---

## 🧩 Part 2: Component Library Specifications

### 2.1 Buttons

#### 2.1.1 Button Variants

**Primary Button** (Main CTAs)
```
Default State:
  - Background: Primary-500 (#6366F1)
  - Text: White
  - Height: 40px
  - Padding: 0 16px
  - Border Radius: 4px
  - Font: Body (16px), Weight 500

Hover State:
  - Background: Primary-600 (#4F46E5)
  - Shadow: Shadow-MD
  - Transition: 200ms ease-out

Active State:
  - Background: Primary-700
  - Transform: scale(0.98)

Disabled State:
  - Background: Gray-300
  - Text: Gray-500
  - Cursor: not-allowed
  - Opacity: 0.6
```

**Secondary Button** (Alternative actions)
```
Default State:
  - Background: White
  - Text: Primary-600
  - Border: 1px solid Gray-300
  - Height: 40px
  - Padding: 0 16px

Hover State:
  - Background: Gray-50
  - Border: Primary-500
```

**Success Button** (Positive actions)
```
Default State:
  - Background: Success-500 (#22C55E)
  - Text: White
  - Height: 40px
  - Padding: 0 16px
  - Border Radius: 4px
  - Font: Body (16px), Weight 500

Hover State:
  - Background: Success-600 (#16A34A)
  - Shadow: Shadow-MD
  - Transition: 200ms ease-out

Active State:
  - Background: Success-700
  - Transform: scale(0.98)

Disabled State:
  - Background: Gray-300
  - Text: Gray-500
  - Cursor: not-allowed
  - Opacity: 0.6

Usage: Publish actions, approve actions, complete actions
```

**Destructive Button** (Delete actions)
```
Default State:
  - Background: Error-500 (#EF4444)
  - Text: White
  - Height: 40px

Hover State:
  - Background: Error-600
```

**Ghost Button** (Tertiary actions)
```
Default State:
  - Background: Transparent
  - Text: Gray-600
  - Height: 40px

Hover State:
  - Background: Gray-100
```

#### 2.1.2 Button Sizes

| Size | Height | Padding | Font Size | Icon Size | Usage |
|------|--------|---------|-----------|-----------|-------|
| **SM** | 32px | 0 12px | 14px | 16px | Compact areas, tables |
| **MD** | 40px | 0 16px | 16px | 20px | ⭐ Default |
| **LG** | 48px | 0 24px | 18px | 24px | Hero sections, important CTAs |

#### 2.1.3 Button with Icons

```
[Icon] Text Button:
  - Icon Position: Left
  - Icon-Text Gap: Space-2 (8px)
  - Icon Size: 20px (MD button)

Text [Icon] Button:
  - Icon Position: Right
  - Icon-Text Gap: Space-2 (8px)

Icon Only Button:
  - Width: 40px (MD)
  - Height: 40px
  - Icon: Centered, 20px
```

---

### 2.2 Form Inputs

#### 2.2.1 Text Input

**Default State**:
```
Size:
  - Height: 40px
  - Width: 100% (fluid)
  - Padding: 0 12px

Border:
  - Width: 1px
  - Color: Gray-300
  - Radius: 4px

Text:
  - Font: Body (16px)
  - Color: Gray-900
  - Placeholder Color: Gray-400

Background: White
```

**Focus State**:
```
Border:
  - Width: 2px
  - Color: Primary-500
  - Shadow: 0 0 0 3px rgba(99, 102, 241, 0.1)

Transition: border-color 200ms ease-out
```

**Error State**:
```
Border:
  - Width: 2px
  - Color: Error-500

Error Message:
  - Font: Body Small (14px)
  - Color: Error-600
  - Margin-Top: Space-2 (8px)
  - Icon: AlertCircle (16px)
```

**Disabled State**:
```
Background: Gray-100
Border: Gray-200
Text: Gray-400
Cursor: not-allowed
```

#### 2.2.2 Input with Label

```
Layout (Vertical):
┌─────────────────────────┐
│ Label *                 │  ← Font: Body (16px), Weight 500, Color: Gray-700
│ (Margin-Bottom: 8px)    │
├─────────────────────────┤
│ [Input Field]           │  ← Height: 40px
├─────────────────────────┤
│ Hint text or error      │  ← Font: Body Small (14px), Color: Gray-500
└─────────────────────────┘

Required Indicator (*):
  - Color: Error-500
  - Position: After label text
```

#### 2.2.3 Textarea

```
Same as Text Input, but:
  - Height: 120px (default)
  - Padding: 12px
  - Resize: Vertical only
  - Max Height: 400px
```

---

### 2.3 Rich Text Editor (TipTap)

#### 2.3.1 Editor Container

```
Container:
  - Border: 1px solid Gray-300
  - Border Radius: 8px
  - Background: White
  - Min Height: 400px

Toolbar:
  - Height: 48px
  - Background: Gray-50
  - Border-Bottom: 1px solid Gray-200
  - Padding: 0 12px
  - Display: Flex, Align: Center, Gap: 8px

Editor Content Area:
  - Padding: 16px
  - Min Height: 352px
  - Font: Body (16px), Line Height: 24px
  - Color: Gray-900
```

#### 2.3.2 Toolbar Buttons

```
Button Style:
  - Size: 32px × 32px
  - Background: Transparent
  - Border: None
  - Border Radius: 4px
  - Icon: 20px, Color: Gray-600

Hover State:
  - Background: Gray-200
  - Icon Color: Gray-900

Active State (when formatting applied):
  - Background: Primary-100
  - Icon Color: Primary-600
```

#### 2.3.3 Toolbar Icons

| Icon | Format | Tooltip |
|------|--------|---------|
| **B** | Bold | Bold (Ctrl+B) |
| _I_ | Italic | Italic (Ctrl+I) |
| U̲ | Underline | Underline (Ctrl+U) |
| H1 | Heading 1 | Heading 1 |
| H2 | Heading 2 | Heading 2 |
| H3 | Heading 3 | Heading 3 |
| • | Bullet List | Bullet List |
| 1. | Numbered List | Numbered List |
| 🔗 | Link | Insert Link (Ctrl+K) |
| 🖼️ | Image | Insert Image |
| `</>` | Code Block | Code Block |

---

### 2.4 Character Counter

**Visual Design**:

```
Layout:
┌──────────────────────────────────────┐
│ [Input Field]                        │
│                                      │
└──────────────────────────────────────┘
                           50/60 chars ← Counter

Counter Position:
  - Align: Right
  - Margin-Top: Space-2 (8px)
  - Font: Caption (12px)

Color States:
  - Valid (within range): Gray-500
  - Warning (near limit): Warning-500
  - Error (exceeds limit): Error-500

Example:
  Meta Title (50-60 chars):
    - 0-49 chars: Gray-500 "45/60 chars (too short)"
    - 50-60 chars: Success-500 "55/60 chars ✓"
    - 61+ chars: Error-500 "65/60 chars (too long)"
```

---

### 2.5 Drag & Drop Zone

**Default State**:
```
Container:
  - Border: 2px dashed Gray-300
  - Border Radius: 8px
  - Background: Gray-50
  - Padding: 48px 24px
  - Text Align: Center
  - Cursor: pointer

Content:
  - Icon: UploadCloud (48px), Color: Gray-400
  - Title: Body Large (18px), Weight 500, Color: Gray-700
    "拖拽 CSV 文件到此处，或点击选择文件"
  - Subtitle: Body Small (14px), Color: Gray-500
    "最多 500 篇文章，文件大小不超过 10MB"
```

**Hover State**:
```
Border: 2px dashed Primary-500
Background: Primary-50
Icon Color: Primary-500
Transition: all 200ms ease-out
```

**Drag Over State** (file being dragged over):
```
Border: 2px solid Primary-500
Background: Primary-100
Icon Color: Primary-600
Title: "释放文件以上传"
```

**Error State**:
```
Border: 2px dashed Error-500
Background: Error-50
Icon: AlertCircle (48px), Color: Error-500
Title Color: Error-600
```

---

### 2.6 Progress Bar

**Linear Progress Bar**:

```
Container:
  - Height: 8px
  - Width: 100%
  - Background: Gray-200
  - Border Radius: 4px
  - Overflow: Hidden

Progress Fill:
  - Height: 8px
  - Background: Primary-500
  - Border Radius: 4px
  - Transition: width 300ms ease-out

Label (Above):
  - Font: Body Small (14px)
  - Color: Gray-600
  - Margin-Bottom: Space-2 (8px)
  - Display: Flex, Justify: Space-Between
    Left: "正在处理..."
    Right: "60/100 篇"

States:
  - Default: Primary-500
  - Success: Success-500 (when 100% complete)
  - Error: Error-500 (when failed)
```

**Circular Progress (Spinner)**:

```
Size: 40px (default)
Border: 4px
Color: Primary-500
Animation: Rotate 1s linear infinite

Usage: Loading states, indefinite progress
```

---

### 2.7 Cards

**Default Card**:
```
Container:
  - Background: White
  - Border: 1px solid Gray-200
  - Border Radius: 8px
  - Padding: 24px
  - Shadow: Shadow-SM

Hover State (for clickable cards):
  - Border: 1px solid Gray-300
  - Shadow: Shadow-MD
  - Cursor: pointer
  - Transition: all 200ms ease-out
```

**Card with Header**:
```
┌────────────────────────────────────┐
│ Card Title                    [X]  │  ← Header: 56px height
├────────────────────────────────────┤    Border-Bottom: 1px Gray-200
│                                    │
│ Card Content                       │  ← Body: Padding 24px
│                                    │
│                                    │
└────────────────────────────────────┘

Header:
  - Padding: 16px 24px
  - Display: Flex, Justify: Space-Between, Align: Center
  - Title: Heading 4 (20px), Weight 600, Color: Gray-900
  - Action: Button (Ghost variant, SM size)
```

---

### 2.8 Worklist Status Badge ⭐

**Worklist Status Badge (with Icon)**:

The Worklist uses a 9-state workflow system with icon-based status badges for improved visual clarity.

```
Container:
  - Display: Inline-Flex, Align: Center, Gap: 8px
  - Height: 28px
  - Padding: 0 12px
  - Border Radius: 14px (Radius-Full)
  - Font: Caption (12px), Weight 500

Icon:
  - Size: 16px × 16px
  - Position: Left of text
  - Color: Matches text color

Text:
  - Font: Body Small (14px)
  - Color: Semantic color (matches icon)
```

**9 Worklist Status States**:

| Status | Icon | Text Color | Background | Pulse | Label (i18n key) |
|--------|------|------------|------------|-------|------------------|
| **pending** | Clock | Gray-700 | Gray-100 | No | worklist.status.pending |
| **parsing** | Loader | Blue-700 | Blue-100 | Yes | worklist.status.parsing |
| **parsing_review** | ClipboardCheck | Orange-700 | Orange-100 | No | worklist.status.parsing_review |
| **proofreading** | Loader | Blue-700 | Blue-100 | Yes | worklist.status.proofreading |
| **proofreading_review** | ClipboardCheck | Orange-700 | Orange-100 | No | worklist.status.proofreading_review |
| **ready_to_publish** | ClipboardCheck | Orange-700 | Orange-100 | No | worklist.status.ready_to_publish |
| **publishing** | Loader | Blue-700 | Blue-100 | Yes | worklist.status.publishing |
| **published** | Check | Green-700 | Green-100 | No | worklist.status.published |
| **failed** | X | Red-700 | Red-100 | No | worklist.status.failed |

**Icon Set (from Lucide React)**:
- Clock: `lucide-react/Clock`
- Loader: `lucide-react/Loader` (with rotation animation)
- ClipboardCheck: `lucide-react/ClipboardCheck`
- Check: `lucide-react/Check`
- X: `lucide-react/X`

**Pulse Animation (for in-progress states)**:
```css
@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

.pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

**Semantic Color Mapping**:
- **Gray (Pending)**: Neutral state, awaiting action
- **Blue (In Progress)**: Active processing states (parsing, proofreading, publishing)
- **Orange (Review Required)**: User action needed (parsing_review, proofreading_review, ready_to_publish)
- **Green (Success)**: Completed successfully (published)
- **Red (Error)**: Failed state, requires attention (failed)

**Usage in Worklist Table**:
- Display in "Status" column
- Icon + text on desktop (width ≥ 768px)
- Icon only on mobile (width < 768px), with tooltip showing full text
- Sort by status priority: failed → review required → in progress → pending → published

**Accessibility**:
- Icon must have `aria-hidden="true"` (decorative)
- Status text must be visible or provided via `aria-label`
- Color is not the only indicator (icon shape also differs)
- Minimum contrast ratio 4.5:1 maintained

---

### 2.9 Tables

**Table Container**:
```
Container:
  - Border: 1px solid Gray-200
  - Border Radius: 8px
  - Overflow: Hidden (for rounded corners)
  - Background: White
```

**Table Header**:
```
Background: Gray-50
Height: 48px
Padding: 0 16px
Border-Bottom: 1px solid Gray-200
Font: Body Small (14px), Weight 600, Color: Gray-700
Text Transform: Uppercase
```

**Table Row**:
```
Default:
  - Height: 64px (default)
  - Padding: 0 16px
  - Border-Bottom: 1px solid Gray-200
  - Font: Body (16px), Color: Gray-900

Hover:
  - Background: Gray-50
  - Cursor: pointer (if clickable)

Selected:
  - Background: Primary-50
  - Border-Left: 4px solid Primary-500
```

**Table Cell**:
```
Padding: 16px
Vertical Align: Middle

Cell Types:
  1. Text: Default body text
  2. Badge: Status indicators
  3. Actions: Button group (Ghost variant, SM size)
```

**Empty State**:
```
Container:
  - Padding: 64px 24px
  - Text Align: Center
  - Border: 1px solid Gray-200
  - Border Radius: 8px

Content:
  - Icon: Inbox (64px), Color: Gray-400
  - Title: Heading 4 (20px), Color: Gray-900
    "暂无数据"
  - Description: Body Small (14px), Color: Gray-500
    "开始导入文章以查看列表"
```

---

### 2.10 Modal / Dialog

**Overlay**:
```
Background: rgba(0, 0, 0, 0.5)
Position: Fixed, Full Screen
Display: Flex, Center Aligned
Z-Index: 1000
Animation: Fade In (200ms)
```

**Modal Container**:
```
Size:
  - Width: 600px (default)
  - Max Width: 90vw
  - Max Height: 90vh

Background: White
Border Radius: 12px
Shadow: Shadow-2XL
Animation: Scale + Fade In (200ms)
  From: scale(0.95), opacity(0)
  To: scale(1), opacity(1)
```

**Modal Header**:
```
Height: 64px
Padding: 0 24px
Border-Bottom: 1px solid Gray-200
Display: Flex, Justify: Space-Between, Align: Center

Title:
  - Font: Heading 3 (24px), Weight 600, Color: Gray-900

Close Button:
  - Size: 32px × 32px
  - Icon: X (20px), Color: Gray-500
  - Hover: Background: Gray-100
```

**Modal Body**:
```
Padding: 24px
Max Height: calc(90vh - 64px - 72px)
Overflow-Y: Auto
```

**Modal Footer**:
```
Height: 72px
Padding: 16px 24px
Border-Top: 1px solid Gray-200
Display: Flex, Justify: Flex-End, Gap: 12px

Buttons: Right-aligned
  - Cancel (Secondary)
  - Confirm (Primary)
```

---

### 2.11 Drawer (Side Panel)

**Overlay**: Same as Modal

**Drawer Container**:
```
Position: Fixed, Right: 0
Width: 480px (default)
Height: 100vh
Background: White
Shadow: Shadow-2XL
Animation: Slide In from Right (300ms)

Sizes:
  - SM: 320px
  - MD: 480px ⭐ Default
  - LG: 640px
```

**Drawer Header**:
```
Height: 64px
Padding: 0 24px
Border-Bottom: 1px solid Gray-200
Display: Flex, Justify: Space-Between, Align: Center
```

**Drawer Body**:
```
Padding: 24px
Height: calc(100vh - 64px)
Overflow-Y: Auto
```

---

### 2.12 Proofreading Suggestion Card ⭐新增

```
┌───────────────────────────────┐
│ [Rule Badge]  [Severity Tag]  │  ← Header (56px)
│ Issue summary (single line)   │
├───────────────────────────────┤
│ Original: 「……」               │  ← Body (Stacked)
│ Suggestion: 「……」             │
│ Confidence: 0.85 (Claude)      │
├───────────────────────────────┤
│ [接受建議] [保留原文] [部分採用] │  ← Action Row (SM buttons)
└───────────────────────────────┘
```

**Header**
- Rule Badge：使用 `Badge Primary` 展示 `A1-001` 等编号。
- Severity Tag：沿用 `Status Badge`（Error/Warning/Primary/Default）。
- 来源标签：Script → Code icon + Gray-700；AI → Sparkles icon + Primary-500；Merged → Merge icon + Primary-700。

**Body**
- 文本使用 `Body Small 14px`，原文/建议对齐左侧，行距 20px。
- 过长时折叠，显示 “展开全文” 链接，点击后展开 + “收起”。
- 差异高亮：
  - 添加 → 背景 `Success-100`，文字 `Success-700`。
  - 删除 → 背景 `Error-100`，文字 `Error-700` + 删除线。
  - 替换 → 两侧同时高亮并在 hover tooltip 中显示 “旧值 → 新值”。
- 置信度信息位于底部：ShieldCheck icon + `Confidence: 0.85 (Claude)`，颜色 `Info-600`。

**Action Row**
- 按钮顺序：Primary「接受建議」、Secondary「保留原文」、Ghost「部分採用」。
- 按钮尺寸：SM（32px 高），间距 12px。
- 移动端改为垂直堆叠（Flex Column + Gap 12px）。
- 再次点击已选决策时，按钮进入 `loading` 状态并禁用其它按钮。

**Card 状态**
| 状态 | Border | 背景 | Header 角标 |
|------|--------|------|-------------|
| Pending | 1px Gray-200 | White | 无 |
| Accepted | 2px Success-500 | Success-50 | `已接受 ✓` + Success badge |
| Rejected | 2px Error-500 | Error-50 | `保留原文 ✕` + Error badge |
| Modified | 2px Warning-500 | Warning-50 | `部分採用 ✎` + Warning badge |

**辅助信息**
- Tooltip：Hover rule badge 显示“规则说明 + 示例”。
- 快捷键：桌面端可使用 `A`（接受）、`K`（保留原文）、`P`（部分采用）。
- Toast：操作成功后显示顶部右侧 Toast，文案如“已保留原文（3s 后自动消失）”。

---

### 2.13 Feedback Modal / Drawer ⭐新增

> 触发场景：点击“保留原文”或“部分採用”按钮。

**结构**
```
Header: 標題 + Close 按鈕
Body:
  1. 建議摘要 (可折疊)
  2. 決策選擇 (Radio)
  3. 反饋原因 (Checkbox，多選)
  4. 最終文本編輯區 (僅部分採用時顯示)
  5. 可選備註 Textarea
Footer: [取消] [確認提交]
```

**詳細規則**
1. **建議摘要卡片**  
   - 預設展開，顯示原文/建議/置信度。  
   - 右上角提供 “查看差異” → 開啟 Diff Viewer Overlay。  
   - 折疊後僅顯示規則 + 單行摘要。
2. **決策選擇 (Radio Group)**  
   - 選項：接受建議 / 保留原文 / 部分採用。  
   - 預設鎖定為觸發來源（如點擊「保留原文」則預選該項）。  
   - 切換為“接受建議”時，隱藏下方反饋區域，只需確認即可。
3. **反饋原因 (Checkbox Group)**  
   - 列表（至多兩列，最多 6 項）：  
     - 建議理解錯誤  
     - 與風格指南不符  
     - 語義/事實不準確  
     - 上下文不完整  
     - AI 建議過於激進  
     - 其他（顯示額外輸入框）  
   - 未選擇時，在確認按鈕左側顯示提醒 `建議選擇原因，幫助我們改進`（不阻止提交）。
4. **最終文本編輯區**  
   - 僅在「部分採用」展示。  
   - 使用 `Textarea` + `Character Counter` + `Diff Toggle`。  
   - 校驗：不可為空；若與原文完全一致則提示 `確認是否直接保留原文？`。  
   - 提供 `套用 AI 建議` 按鈕快速填充。  
5. **備註 Textarea**  
   - 佔位：“可記錄更詳細的調整說明（僅內部可見）”。  
   - 限制 500 字符，顯示字數計數。

**Footer 按鈕**
- Cancel：Secondary，點擊後關閉並重置。  
- Confirm：Primary，Loading 狀態顯示 Spinner + `提交中…`。  
- 當必填校驗失敗時，阻止關閉並聚焦第一個錯誤欄位。

---

### 2.14 Diff Viewer ⭐新增

**檢視模式**
1. **並排模式 (Desktop Default)**  
   - 左側原文，右側最終文本。  
   - 標題行：`原文` / `最終文本`，右側提供 `切換為行內模式` 按鈕。  
   - 滾動同步，頂部顯示 `同步滾動` 切換開關。
2. **行內模式 (Mobile Default)**  
   - 使用 Inline Diff，新增以 `Success-100/700` 標示，刪除以 `Error-100/700` 標示。  
   - 列表下方提供 “僅顯示差異” Toggle。

**工具列**
- `複製最終文本`（Primary Ghost Icon Button）  
- `下載 Diff（.txt）`  
- `上一處差異 / 下一處差異`（Chevron 按鈕）

---

### 2.15 Feedback Status Chip ⭐新增

| 狀態 | 背景 | 文字 | Icon |
|------|------|------|------|
| pending | Gray-100 | Gray-700 | Clock |
| in_progress | Info-100 | Info-700 | Loader (旋轉動畫) |
| completed | Success-100 | Success-700 | CheckCircle |
| failed | Error-100 | Error-700 | AlertCircle |

- 高度 24px，Padding 0 12px，Icon 16px。
- 在卡片／表格／儀表盤中統一使用。

---

### 2.16 Decisions Bulk Toolbar ⭐新增

```
┌────────────────────────────────────────────┐
│ [Checkbox 全選] 已選 3 項                 │
│  [標記待處理]  [導出 CSV]  [批量保留原文] │
└────────────────────────────────────────────┘
```

- 背景 Gray-50，Border-Bottom Gray-200，Padding 0 24px，高度 56px。
- 顯示於多選模式，從畫面頂部滑入（Slide Down 200ms ease-out）。
- 右側操作按鈕全部為 Secondary/Primary SM，最右側保留原文按鈕觸發二次確認。
- 提供 “取消選擇” 連結（放置在左側 Checkbox 旁），觸發後恢復列表狀態。

---

## 📱 Part 3: Page Layouts & Wireframes

### 3.1 Article Import Page

**Layout Structure**:

```
┌─────────────────────────────────────────────────────────────┐
│ Header Navigation (64px height)                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Page Title Section (120px height)                           │
│   H1: 导入文章                                               │
│   Description: 支持 CSV/JSON 批量导入或手动输入单篇文章     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Tabs (48px height)                                          │
│   [ CSV 导入 ] [ JSON 导入 ] [ 手动输入 ]                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                                                              │
│ Tab Content Area (Dynamic Height)                           │
│                                                              │
│   [Drag & Drop Zone] or [Manual Form] or [JSON Form]        │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Import History Section                                      │
│   H2: 导入历史                                               │
│   [Table: Recent 10 imports]                                 │
└─────────────────────────────────────────────────────────────┘
```

**Responsive Breakpoints**:
- Desktop: 1280px+ (Full layout)
- Tablet: 768px - 1279px (Stack sections)
- Mobile: < 768px (Single column, tabs as dropdown)

---

### 3.2 Article Detail Page (with SEO Panel)

**Layout Structure** (2-Column):

```
┌──────────────────────┬──────────────────────────────────────┐
│ Left Sidebar (360px) │ Main Content Area (Fluid)            │
│                      │                                      │
│ ┌──────────────────┐ │ ┌──────────────────────────────────┐ │
│ │ Article Metadata │ │ │ Article Title & Content          │ │
│ │                  │ │ │                                  │ │
│ │ - Status Badge   │ │ │ H1: Article Title                │ │
│ │ - Created Date   │ │ │                                  │ │
│ │ - Source         │ │ │ [Rich Text Content Preview]      │ │
│ │ - Featured Image │ │ │                                  │ │
│ └──────────────────┘ │ └──────────────────────────────────┘ │
│                      │                                      │
│ ┌──────────────────┐ │ ┌──────────────────────────────────┐ │
│ │ Quick Actions    │ │ │ SEO Optimizer Panel              │ │
│ │                  │ │ │                                  │ │
│ │ [Analyze SEO]    │ │ │ ┌──────────────────────────────┐ │ │
│ │ [Publish]        │ │ │ │ Meta Title (Character Count) │ │ │
│ │ [Edit]           │ │ │ └──────────────────────────────┘ │ │
│ │ [Delete]         │ │ │                                  │ │
│ └──────────────────┘ │ │ ┌──────────────────────────────┐ │ │
│                      │ │ │ Meta Description             │ │ │
│                      │ │ └──────────────────────────────┘ │ │
│                      │ │                                  │ │
│                      │ │ ┌──────────────────────────────┐ │ │
│                      │ │ │ Keywords (Tags)              │ │ │
│                      │ │ └──────────────────────────────┘ │ │
│                      │ │                                  │ │
│                      │ │ ┌──────────────────────────────┐ │ │
│                      │ │ │ Keyword Density Chart        │ │ │
│                      │ │ └──────────────────────────────┘ │ │
│                      │ │                                  │ │
│                      │ │ ┌──────────────────────────────┐ │ │
│                      │ │ │ Readability Score Gauge      │ │ │
│                      │ │ └──────────────────────────────┘ │ │
│                      │ │                                  │ │
│                      │ │ [Save Changes] [Re-analyze SEO]  │ │
│                      │ └──────────────────────────────────┘ │
└──────────────────────┴──────────────────────────────────────┘
```

**Responsive**:
- Tablet/Mobile: Stack sidebar on top of main content

---

### 3.3 Publish Tasks Monitoring Page

**Layout Structure**:

```
┌─────────────────────────────────────────────────────────────┐
│ Page Header (120px)                                          │
│   H1: 发布任务监控                                           │
│   [Filters] [Refresh Button]                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Filters Row (56px)                                           │
│   [ Status: All ▼ ] [ Provider: All ▼ ] [ Clear Filters ]   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                                                              │
│ Task List Table                                              │
│                                                              │
│ ┌────┬───────────┬─────────┬────────┬──────┬──────┬──────┐ │
│ │ ID │ Article   │ Provider│ Status │ Time │ Cost │ Action│ │
│ ├────┼───────────┼─────────┼────────┼──────┼──────┼──────┤ │
│ │ 1  │ Title...  │ [PW]    │ ✓ Done │ 90s  │ $0.02│ View │ │
│ │ 2  │ Title...  │ [AI]    │ ⏳ Run │ 180s │ $1.50│ View │ │
│ │ 3  │ Title...  │ [GEM]   │ ✗ Fail │ 45s  │ $0.50│ View │ │
│ └────┴───────────┴─────────┴────────┴──────┴──────┴──────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Pagination (56px)                                            │
│   ← Previous | Page 1 of 5 | Next →                         │
└─────────────────────────────────────────────────────────────┘
```

**Provider Icons**:
- [PW] = Playwright (Green badge)
- [AI] = Anthropic (Blue badge)
- [GEM] = Gemini (Orange badge)

---

### 3.4 Provider Comparison Dashboard

**Layout Structure** (Grid Layout):

```
┌─────────────────────────────────────────────────────────────┐
│ Page Header (120px)                                          │
│   H1: Provider 性能对比                                      │
│   Description: 数据驱动的 Provider 选择建议                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬──────────────────────────┐
│ Metrics Table (Left, 50%)        │ Recommendation Card      │
│                                  │ (Right, 50%)             │
│ ┌────────────┬───────┬─────┬───┐ │                          │
│ │ Provider   │ Rate  │ Time│ $ │ │ ⭐ 推荐使用 Playwright   │
│ ├────────────┼───────┼─────┼───┤ │                          │
│ │ Playwright │ 98% ✓ │ 90s │$0 │ │ - 成功率 98%             │
│ │ Anthropic  │ 95%   │210s │$1 │ │ - 完全免费               │
│ │ Gemini     │ 93%   │180s │$1 │ │ - 速度最快               │
│ └────────────┴───────┴─────┴───┘ │                          │
└──────────────────────────────────┴──────────────────────────┘

┌──────────────────────────────────┬──────────────────────────┐
│ Success Rate Over Time (Line)   │ Cost Comparison (Bar)    │
│                                  │                          │
│ [Line Chart: 30 days trend]      │ [Bar Chart: Cost/Article]│
└──────────────────────────────────┴──────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Task Distribution (Pie Chart)                                │
│                                                              │
│ [Pie Chart: % of tasks by provider]                         │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.5 Worklist Page ⭐

**Layout Structure** (Phase 1 Enhanced Design):

```
┌─────────────────────────────────────────────────────────────┐
│ Page Header (120px)                                          │
│   H1: 工作清单                                               │
│   Description: 管理文章从解析到发布的完整流程                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Statistics Row (96px)                                        │
│ ┌───────────┬───────────┬───────────┬───────────┬─────────┐ │
│ │ [Icon] 9  │ [Icon] 12 │ [Icon] 45 │ [Icon] 3  │ [Icon]  │ │
│ │ Total     │ Pending   │ Published │ Failed    │ 152 ⭐  │ │
│ └───────────┴───────────┴───────────┴───────────┴─────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Quick Filters Row (56px) ⭐NEW                              │
│ [🔔 需要我处理 (3)] [⏳ 进行中 (2)] [✅ 已完成 (45)] [⚠️ 有问题 (1)] │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Filters Card (Collapsible) (80px when collapsed)            │
│   [Status: All ▼] [Search: ________] [Clear Filters]        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                                                              │
│ Worklist Table ⭐ENHANCED                                   │
│                                                              │
│ ┌─────┬──────────┬────────────┬──────────────┬──────────┐  │
│ │ ID  │ Title    │ Status     │ Operations   │ Updated  │  │
│ ├─────┼──────────┼────────────┼──────────────┼──────────┤  │
│ │ #1  │ Article1 │ [📋 Review]│ [View] [Pub] │ 2h ago   │  │
│ │ #2  │ Article2 │ [⏳ Parsing]│ [View]       │ 5h ago   │  │
│ │ #3  │ Article3 │ [✅ Done]   │ [View]       │ 1d ago   │  │
│ └─────┴──────────┴────────────┴──────────────┴──────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Pagination (56px)                                            │
│   ← Previous | Page 1 of 3 | Next →                         │
└─────────────────────────────────────────────────────────────┘
```

**Component Specifications**:

**1. Statistics Cards** (Grid: 5 columns)
```
Each Card:
  - Size: Auto-width, Height 96px
  - Padding: 16px
  - Background: White
  - Border: 1px solid Gray-200
  - Border Radius: 8px
  - Hover: Shadow-MD

Content Layout:
  - Icon: Top, 24px, Semantic color
  - Number: H2 (30px), Weight 600, Gray-900
  - Label: Body Small (14px), Gray-500
  - Gap: 8px between elements

Responsive:
  - Desktop (≥1024px): 5 columns
  - Tablet (768-1023px): 3 columns (2 rows)
  - Mobile (<768px): 2 columns, stacked
```

**2. Quick Filters Row** ⭐NEW
```
Container:
  - Height: 56px
  - Padding: 0 24px
  - Background: White
  - Border: 1px solid Gray-200
  - Border Radius: 8px
  - Display: Flex, Gap: 12px
  - Overflow-X: Auto (mobile)

Filter Button:
  - Height: 40px
  - Padding: 0 16px
  - Border Radius: 20px (Pill)
  - Font: Body (16px), Weight 500
  - Display: Flex, Align: Center, Gap: 8px
  - Transition: all 200ms ease-out

Button States:
  Default:
    - Background: Gray-100
    - Text: Gray-700
    - Border: 1px solid Gray-200

  Hover:
    - Background: Gray-200
    - Border: Gray-300

  Active (selected):
    - Background: Primary-100
    - Text: Primary-700
    - Border: Primary-500

Icon:
  - Size: 20px
  - Position: Left
  - Color: Matches text

Badge (count):
  - Size: 20px × 20px
  - Border Radius: 10px
  - Font: Caption (12px), Weight 600
  - Background: Semantic color
  - Position: Right of text

Filter Types:
  1. 需要我处理 (Bell icon, Orange badge)
     - States: parsing_review, proofreading_review, ready_to_publish

  2. 进行中 (Loader icon, Blue badge)
     - States: parsing, proofreading, publishing

  3. 已完成 (Check icon, Green badge)
     - States: published

  4. 有问题 (AlertTriangle icon, Red badge)
     - States: failed

Keyboard:
  - Tab navigation
  - Enter/Space to activate
  - Arrow keys to move between filters
```

**3. Enhanced Worklist Table** ⭐ENHANCED
```
Columns:
  1. ID (80px):
     - Format: #12345
     - Font: Monospace, Gray-600

  2. Title (Flex, min 200px):
     - Font: Body (16px), Weight 500, Gray-900
     - Max Lines: 2, Ellipsis
     - Hover: Underline, Cursor pointer

  3. Status (180px): ⭐ENHANCED
     - Uses Worklist Status Badge (Section 2.8)
     - Icon + text (desktop)
     - Icon only (mobile with tooltip)

  4. Operations (200px): ⭐NEW
     - Button Group, Gap: 8px
     - All SM size (32px height)

     Buttons shown per status:
     - parsing_review: [View] [Approve] [Reject]
     - proofreading_review: [View] [Approve] [Reject]
     - ready_to_publish: [View] [Publish]
     - published: [View] [Open URL]
     - failed: [View] [Retry]
     - Default: [View]

     Button Variants:
     - View: Ghost, Eye icon
     - Approve: Primary, Check icon
     - Reject: Secondary, X icon
     - Publish: Success, Send icon
     - Open URL: Ghost, ExternalLink icon
     - Retry: Primary, RotateCcw icon

  5. Updated (120px):
     - Format: Relative time (2h ago, 1d ago)
     - Font: Body Small (14px), Gray-500

Row States:
  Default:
    - Background: White
    - Height: 64px

  Hover:
    - Background: Gray-50

  Needs Attention (review states):
    - Border-Left: 4px solid Orange-500
    - Background: Orange-50 (hover)

  Failed:
    - Border-Left: 4px solid Red-500
    - Background: Red-50 (hover)

Empty State:
  - Icon: Inbox (64px), Gray-400
  - Title: "暂无工作清单"
  - Description: "导入文章后，它们会出现在这里"
  - Action: [导入文章] button (Primary)
```

**Responsive Breakpoints**:
- Desktop (≥1024px): Full layout, all columns visible
- Tablet (768-1023px): Hide "Updated" column, compact operations
- Mobile (<768px): Card-based layout
  ```
  ┌────────────────────────────┐
  │ #1 · Article Title         │
  │ [Status Badge]             │
  │ [View] [Publish]           │
  │ Updated: 2h ago            │
  └────────────────────────────┘
  ```

**Interaction Details**:

1. **Quick Filter Click**:
   - Filter activates (Primary style)
   - Table updates instantly (client-side filtering if ≤100 items)
   - URL updates: `/worklist?filter=needs_attention`
   - Badge count updates
   - Smooth transition (200ms)

2. **Operation Button Click**:
   - View: Opens detail drawer (right side, 480px)
   - Publish: Shows publish confirmation modal
   - Approve/Reject: Shows review modal with feedback form
   - Open URL: Opens in new tab
   - Retry: Shows retry confirmation with provider selection

3. **Row Click** (outside buttons):
   - Opens detail drawer
   - Highlights row (Primary-50 background)

4. **Status Badge Hover**:
   - Tooltip shows full status text + description
   - Example: "Parsing Review - AI 解析完成，请审核内容"

**Performance Optimizations**:
- Virtual scrolling for >100 rows
- Lazy load images in detail drawer
- Debounce search (300ms)
- Optimistic UI updates for operations
- Skeleton loading states

**Accessibility**:
- All buttons have aria-labels
- Status badges use aria-live="polite" for updates
- Table has proper ARIA table structure
- Keyboard navigation: Tab through filters → table → operations
- Screen reader announces filter changes

---

## 🔄 Part 4: Interaction Flows

### 4.1 Article Import Flow (CSV)

```
User Journey:
1. Navigate to Import Page
   ↓
2. Click "CSV 导入" tab
   ↓
3. Drag & Drop CSV file OR Click to select
   ↓
4. File validation starts
   ├─ Valid: Show file info, "开始导入" button enabled
   └─ Invalid: Show error message, retry
   ↓
5. Click "开始导入"
   ↓
6. Progress bar animates (0% → 100%)
   Show: "正在处理... 60/100 篇"
   ↓
7. Import complete
   ├─ Success: Show summary (95 imported, 5 failed)
   │   Action: "查看文章列表" button
   │   ↓
   │   Redirect to Article List
   │
   └─ Partial success: Show error list
       Action: "下载错误报告" + "查看成功导入的文章"
```

**Interaction States**:
1. **Idle**: Drag & drop zone visible, no file
2. **File Selected**: File info shown, button enabled
3. **Uploading**: Progress bar animating, cancel button
4. **Processing**: Spinner + "X/Y 篇" counter
5. **Success**: Success icon + summary + CTA
6. **Error**: Error icon + error list + retry button

---

### 4.2 SEO Analysis & Edit Flow

```
User Journey:
1. Navigate to Article Detail Page
   ↓
2. Click "Analyze SEO" button (if no SEO data)
   ↓
3. Loading modal appears
   Show: "正在分析 SEO..." + spinner
   Poll: /v1/seo/analyze/{id}/status every 2s
   ↓
4. Analysis complete (30s)
   Modal updates: "分析完成 ✓"
   ↓
5. Modal closes, SEO panel populates with data
   ↓
6. User reviews AI-generated metadata
   ├─ Satisfied: Click "保存修改"
   │   ↓
   │   Success toast: "SEO 元数据已保存"
   │
   └─ Not satisfied: Edit fields manually
       ↓
       Make changes to Meta Title, Keywords, etc.
       ↓
       Click "保存修改"
       ↓
       Success toast + "manual_overrides" tracked
```

**Character Counter States**:
```
Meta Title (50-60 chars):
  - 0-49: Gray "45/60 (需要再添加 5+ 字符)" ⚠️
  - 50-60: Green "55/60 ✓" ✅
  - 61+: Red "65/60 (超出 5 字符)" ❌
```

---

### 4.3 Multi-Provider Publishing Flow

```
User Journey:
1. On Article Detail Page (SEO data exists)
   ↓
2. Click "发布到 WordPress" dropdown
   ↓
3. Select Provider:
   [ ] Playwright (推荐) - 免费, 1-2 分钟
   [ ] Anthropic Computer Use - $1.50, 3-5 分钟
   [ ] Gemini Computer Use - $1.00, 2-4 分钟
   ↓
4. Confirmation dialog appears
   "确认发布文章到 WordPress？"
   - Provider: Playwright
   - 预估时间: 1-2 分钟
   - 预估成本: 免费
   [取消] [确认发布]
   ↓
5. Click "确认发布"
   ↓
6. Publish Progress Modal opens (full screen overlay)
   ┌────────────────────────────────────┐
   │ 正在发布文章...                    │
   │                                    │
   │ [Progress Bar: 62%]                │
   │ 5/8 步骤完成                       │
   │                                    │
   │ [Spinner] Configuring Yoast SEO... │
   │                                    │
   │ 已用时间: 45秒                     │
   │ 预计剩余: 30秒                     │
   └────────────────────────────────────┘

   Poll: /v1/publish/tasks/{task_id}/status every 2s
   ↓
7. Publishing complete (90s)
   ├─ Success:
   │   Modal updates:
   │   ┌────────────────────────────────────┐
   │   │ ✅ 发布成功！                      │
   │   │                                    │
   │   │ 文章已发布到 WordPress             │
   │   │ URL: https://example.com/post/123  │
   │   │                                    │
   │   │ 耗时: 90 秒                        │
   │   │ 截图: 8 张                         │
   │   │                                    │
   │   │ [查看文章] [查看截图] [关闭]      │
   │   └────────────────────────────────────┘
   │
   └─ Failed:
       Modal updates:
       ┌────────────────────────────────────┐
       │ ❌ 发布失败                        │
       │                                    │
       │ 错误: Login failed - invalid creds │
       │                                    │
       │ [查看错误截图] [重试] [关闭]      │
       └────────────────────────────────────┘
```

**Modal States**:
1. **Publishing**: Progress bar + current step + timer
2. **Success**: Success icon + URL + actions
3. **Failed**: Error icon + error message + retry

---

### 4.4 Task Monitoring Flow

```
User Journey:
1. Navigate to "发布任务" page
   ↓
2. View task list table
   ├─ Filter by Status: [All ▼] → Select "Running"
   │   ↓
   │   Table updates to show only running tasks
   │
   └─ Click "View Details" on a task
       ↓
       Drawer opens from right (480px wide)
       ┌─────────────────────────────────┐
       │ 任务详情                         │
       │                                 │
       │ Task ID: #12345                 │
       │ Article: 文章标题               │
       │ Provider: Playwright            │
       │ Status: ✓ Completed             │
       │ Duration: 90 seconds            │
       │ Cost: $0.02                     │
       │                                 │
       │ ──────────────────────────────  │
       │                                 │
       │ 执行日志 (8 steps):             │
       │ 1. ✓ Login to WordPress         │
       │ 2. ✓ Create new post            │
       │ 3. ✓ Fill title and content     │
       │ 4. ✓ Upload images              │
       │ 5. ✓ Configure Yoast SEO        │
       │ 6. ✓ Set categories             │
       │ 7. ✓ Publish article            │
       │ 8. ✓ Verify publication         │
       │                                 │
       │ ──────────────────────────────  │
       │                                 │
       │ 截图 (8 张):                    │
       │ [Screenshot Gallery Grid]       │
       │ [img] [img] [img]               │
       │ [img] [img] [img]               │
       │ [img] [img]                     │
       │                                 │
       │ Click any screenshot → Lightbox │
       └─────────────────────────────────┘
```

---

## ♿ Part 5: Accessibility (WCAG 2.1 AA)

### 5.1 Color Contrast

**Requirements**:
- Normal text (16px): Minimum contrast ratio 4.5:1
- Large text (24px+): Minimum contrast ratio 3:1
- UI components: Minimum contrast ratio 3:1

**Validation**:
```
✅ Gray-900 on White: 15.8:1 (Excellent)
✅ Gray-600 on White: 7.2:1 (Good)
✅ Primary-500 on White: 4.6:1 (Pass)
✅ Error-500 on White: 4.8:1 (Pass)
❌ Gray-400 on White: 2.8:1 (Fail - Placeholder only)
```

### 5.2 Keyboard Navigation

**Requirements**:
- All interactive elements must be keyboard accessible
- Focus indicators must be visible (2px outline)
- Tab order must be logical

**Focus Styles**:
```
Default Focus:
  - Outline: 2px solid Primary-500
  - Outline Offset: 2px
  - Box Shadow: 0 0 0 3px rgba(99, 102, 241, 0.1)

Skip Focus (e.g., cards):
  - tabindex="-1" for non-interactive elements
```

### 5.3 Screen Reader Support

**ARIA Labels**:
```html
<!-- Buttons with icons only -->
<button aria-label="Close dialog">
  <XIcon />
</button>

<!-- Form inputs -->
<label for="article-title">Article Title</label>
<input id="article-title" aria-required="true" />

<!-- Status indicators -->
<span role="status" aria-live="polite">
  Article published successfully
</span>

<!-- Progress bars -->
<div role="progressbar" aria-valuenow="60" aria-valuemin="0" aria-valuemax="100">
  60/100 articles processed
</div>
```

### 5.4 Alternative Text

**Images**:
```html
<!-- Featured image -->
<img src="..." alt="Article featured image showing..." />

<!-- Icons (decorative) -->
<svg aria-hidden="true"><path d="..." /></svg>

<!-- Icons (informative) -->
<svg role="img" aria-label="Success"><path d="..." /></svg>
```

---

## 📱 Part 6: Responsive Design

### 6.1 Breakpoints

| Name | Min Width | Max Width | Layout |
|------|-----------|-----------|--------|
| **Mobile** | 0px | 767px | Single column, stack all |
| **Tablet** | 768px | 1023px | 2 columns where possible |
| **Desktop** | 1024px | 1279px | Full layout |
| **Large Desktop** | 1280px | ∞ | Max width 1280px, centered |

### 6.2 Mobile Adaptations

**Navigation**:
- Desktop: Horizontal nav bar
- Mobile: Hamburger menu + drawer

**Tables**:
- Desktop: Full table
- Tablet: Scrollable table (horizontal scroll)
- Mobile: Card-based list (each row = card)

**Modals**:
- Desktop: 600px width, centered
- Mobile: Full screen (100vw, 100vh)

**Forms**:
- Desktop: 2-column grid (where applicable)
- Mobile: Single column

---

## 🎨 Part 7: Design Tool Export Specifications

### 7.1 For Figma

**Component Structure**:
```
📁 CMS Automation Design System
  ├─ 🎨 Styles
  │   ├─ Colors (All color tokens)
  │   ├─ Text Styles (All typography)
  │   ├─ Effects (Shadows)
  │   └─ Grids (8px grid system)
  │
  ├─ 🧩 Components
  │   ├─ Buttons (All variants + sizes)
  │   ├─ Form Inputs (Text, Textarea, Select, etc.)
  │   ├─ Cards
  │   ├─ Badges
  │   ├─ Tables
  │   ├─ Modals
  │   ├─ Drawers
  │   └─ Progress Indicators
  │
  └─ 📄 Pages
      ├─ Article Import Page
      ├─ Article Detail Page
      ├─ SEO Optimizer Panel
      ├─ Publish Tasks Page
      └─ Provider Comparison Dashboard
```

**Auto Layout Settings**:
- Direction: Horizontal / Vertical
- Spacing: 8px, 16px, 24px (from spacing system)
- Padding: Match component specs
- Resizing: Fill container / Hug contents

### 7.2 For Sketch

**Libraries**:
- Create shared library: "CMS Automation System"
- Use Symbols for reusable components
- Use Shared Styles for colors and typography

### 7.3 For Adobe XD

**Components**:
- Use Component States for hover/active/disabled
- Use Stacks for auto layout
- Use Repeat Grid for tables and lists

---

## 📝 Part 8: Design Handoff Checklist

### 8.1 For Designers

Before handing off to developers:
- [ ] All components have hover and focus states
- [ ] Error states designed for all forms
- [ ] Empty states designed for lists and tables
- [ ] Loading states (spinners, skeletons)
- [ ] Success/error feedback (toasts, alerts)
- [ ] Mobile layouts designed for all pages
- [ ] Accessibility annotations added (ARIA labels, contrast ratios)
- [ ] All text is actual content (not Lorem Ipsum)
- [ ] All icons are from consistent icon set (e.g., Heroicons)
- [ ] Design tokens documented (colors, spacing, typography)

### 8.2 For Developers

Development checklist:
- [ ] Design system implemented (colors, typography, spacing)
- [ ] All components built and tested in Storybook
- [ ] Responsive breakpoints tested on real devices
- [ ] Keyboard navigation working for all interactive elements
- [ ] Screen reader compatibility tested
- [ ] Form validation working with proper error messages
- [ ] Loading and empty states implemented
- [ ] Hover and focus states match design
- [ ] Animations smooth and performant (60fps)
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)

---

## 🔗 Appendix: Design Resources

### Icon Library

**Recommended**: [Heroicons](https://heroicons.com/) (MIT License)
- Outline style: 24px stroke, 1.5px width
- Solid style: 24px filled
- Mini style: 20px filled

**Common Icons Needed**:
| Icon | Usage | Heroicon Name |
|------|-------|---------------|
| ✓ | Success states | CheckIcon |
| ✗ | Error states | XCircleIcon |
| ⚠️ | Warning states | ExclamationTriangleIcon |
| ℹ️ | Info states | InformationCircleIcon |
| ↑ | Upload | ArrowUpTrayIcon |
| 🗑️ | Delete | TrashIcon |
| ✏️ | Edit | PencilIcon |
| 👁️ | View | EyeIcon |
| ⚙️ | Settings | CogIcon |
| 📊 | Dashboard | ChartBarIcon |
| 📝 | Article | DocumentTextIcon |
| 🚀 | Publish | RocketLaunchIcon |

### Illustration Style (Optional)

If using illustrations:
- Style: Flat, 2.5D, or Line art
- Colors: Match brand colors (Primary-500, Success-500, etc.)
- Size: Max 400px × 400px for empty states
- Format: SVG (scalable, small file size)

### Image Guidelines

**Article Images**:
- Aspect Ratio: 16:9 (recommended)
- Min Size: 1200px × 675px
- Max Size: 5MB
- Formats: JPG, PNG, WebP

**Thumbnails**:
- Size: 300px × 169px (16:9)
- Quality: 80% (optimized)

---

## ✅ Next Steps

### For Designers

1. **Import Design System** into Figma/Sketch/XD
   - Create color palette (Section 1.1)
   - Create text styles (Section 1.2)
   - Create effects (Section 1.5)

2. **Build Component Library** (Section 2)
   - Start with atomic components (buttons, inputs)
   - Then build composite components (cards, modals)

3. **Design Pages** (Section 3)
   - Use wireframes as starting point
   - Apply design system consistently

4. **Add Interaction States**
   - Hover, active, disabled for all components
   - Loading, empty, error states for pages

5. **Create Prototype**
   - Link pages together
   - Add transitions (200ms ease-out)
   - Test user flows

### For Developers

1. **Review Design Specs** (this document)
   - Understand design system
   - Note any technical constraints

2. **Set Up Frontend**
   - Install TailwindCSS with custom config
   - Create design token files (colors, spacing, etc.)

3. **Build Component Library**
   - Follow specs in Section 2
   - Create Storybook stories
   - Test in isolation

4. **Implement Pages**
   - Follow layouts in Section 3
   - Follow interaction flows in Section 4

5. **Test & Refine**
   - Responsive testing
   - Accessibility testing
   - Cross-browser testing

---

**Document Created**: 2025-10-27
**Created by**: Claude (AI Assistant)
**Status**: ✅ Ready for Design Tool Implementation
**Version**: 1.0.0

**This document is designed to be imported into Figma, Sketch, or Adobe XD for creating high-fidelity mockups and prototypes.**
