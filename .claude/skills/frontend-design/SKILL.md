---
name: spendly-ui-designer
description: Front-end UI designer for Spendly, the Flask + Jinja personal expense tracker (github.com/Arbaz123-git/Spendly-). Generates modern, responsive, production-ready pages and components that match Spendly's existing design system. Use this skill whenever the user asks to design, create, build, redesign, restyle or improve any Spendly page, screen, component or layout, for example "design the dashboard page", "create UI for the add-expense form", "build a component for the expense list", "redesign the profile page", "improve the login page", or "make the category breakdown look better", even if they don't say "UI" or "frontend". Also use it for expense-tracker screens such as dashboard, expense table, filters, charts, empty states, modals and forms when the working project is Spendly.
---
 
# Spendly UI Designer
 
Design and write front-end UI for Spendly so every new screen looks like it was built by the same hand as the existing ones: calm, warm, card-based, and easy to scan at a glance.
 
The reason this skill exists: Spendly is a small, deliberately simple codebase with strict rules (Flask/Jinja templates, one shared stylesheet, vanilla JS only, no npm). Generic "modern SaaS" output usually breaks those rules or drifts from the existing look. The job is modern *and* consistent *and* within the constraints.
 
## Inputs
 
- **Required:** the page or component name (e.g. "dashboard", "expense list", "add-expense form").
- **Optional:** sample data, references or screenshots, features to include, and things to stay consistent with. If the user gives none, use the seeded schema (below) to invent realistic sample data.
Don't ask clarifying questions for ordinary requests. Make sensible choices, state them briefly in the UX notes, and let the user redirect. Ask only if the request is truly ambiguous about *which* screen they mean.
 
## Workflow
 
1. **Ground yourself in the real design.** Before writing anything, read `static/css/style.css` (the source of truth for tokens and existing classes) and `templates/base.html`. If a similar page exists (`login.html` for forms and centred cards, `landing.html` for stat cards, progress bars and feature cards), skim it. If the repo isn't available, fall back on `references/design-system.md`, which records the tokens and classes as of writing. Real files win over the reference if they differ.
2. **Plan the layout in your head first:** what is the one thing the user must see or do on this screen? Put that at the top or centre; everything else supports it.
3. **Write the files** (see "Where code goes"), reusing existing classes and tokens before inventing new ones. If `templates/_icons.html` doesn't exist yet, copy it from `assets/_icons.html`, and if `style.css` lacks the `.icon` and `.cat` blocks, append `assets/shared-additions.css` to it. These are the shared pieces every screen needs, so they should exist exactly once rather than be rewritten per page.
4. **Look at it.** Render the page and check it at desktop (1280px) and phone (375px) widths before you hand it over; see "Verify visually". Layout bugs at 375px are the most common flaw in generated UI, and they only show up when you actually look.
5. **Check against the checklist** at the bottom, then reply in the output format below.
## Where code goes (from the project's CLAUDE.md)
 
- New page: a new `templates/<name>.html` that `{% extends "base.html" %}` and fills `{% block title %}` and `{% block content %}`.
- Page-specific styles: a new `static/css/<name>.css`, linked from the template through `{% block head %}` with `url_for('static', filename='css/<name>.css')`. Never inline `<style>` tags, and don't bloat `style.css` with one-page styles. Only add to `style.css` when a style is genuinely shared (a new shared component such as a badge or table).
- Links and assets: always `url_for()`, never hardcoded paths.
- JavaScript: vanilla only, in `static/js/main.js` or a `{% block scripts %}` block. No frameworks, no npm packages, no CDN libraries.
- Routes: don't edit `app.py` or implement stub routes unless the user asks. A design request gets the template and CSS. Tell the user what route and context variables the template expects so wiring it up is one small step. Make the template render sensibly with Jinja defaults or clearly marked sample data so it can be previewed.
- Never put database logic in templates or invent new packages.
## Design rules
 
Full tokens and patterns are in `references/design-system.md` and `references/components.md`. The essentials:
 
- **Use the CSS variables, never raw hex.** Colours come from `--ink*`, `--paper*`, `--accent*`, `--danger*`, `--border*`. The project's specs say "never hardcode hex values". Category colours are already defined once in `style.css` (`--cat-food` and friends, plus the `.cat` / `.cat-food` classes that expose `--cat` and `--cat-light`). Put `class="cat cat-{{ category|lower }}"` on a row, chip or tile and colour it with `var(--cat)` and `var(--cat-light)`. Because several pages use these, they live in the shared stylesheet, not in a page file. Page-only colours can still be variables at the top of that page's CSS.
- **Look:** modern SaaS but warm, not cold. Off-white paper background, white cards, thin `--border` outlines, forest-green accent, near-black primary buttons that turn green on hover. Subtle shadows only (`0 8px 40px rgba(0,0,0,0.06)` is the house shadow); depth comes mostly from borders and spacing.
- **Hierarchy and spacing:** one clear page title (DM Serif Display for headings, DM Sans for everything else), generous whitespace (1.5 to 2rem inside cards, 1 to 2rem between them), muted secondary text (`--ink-muted`), and numbers set larger and bolder than their labels.
- **Card-based layout:** group related content in cards using `--radius-md`; use `--radius-lg` for large containers and `--radius-sm` for inputs and buttons. Keep content inside `--max-width` (1200px).
- **Amounts are rupees:** format as `₹18,240`, and show negative-good / positive-bad semantics consistently (the existing mock uses `--danger` for spending up and `--accent` for spending down).
- **Usability first:** visible labels on every input, clear focus states, a hover state on everything clickable, empty states with a friendly message and a primary action, and error/success messages using the existing `.auth-error` / `.auth-success` look. Prefer real `<button>` and `<a>` elements, semantic headings, and `aria-label` on icon-only controls. Keep DOM order the same as visual order: don't use `flex-direction: column-reverse` or `order` to rearrange buttons, because keyboard users then tab through them in a different order than they see. Delete links in this project are plain GET links, so add a confirmation (`data-confirm`) and suggest moving delete to POST later.
- **Responsive:** mobile-first thinking. Use CSS grid or flex, collapse multi-column layouts to one column at 900px, tighten padding at 600px, and let tables become stacked cards or scroll horizontally on narrow screens. The existing breakpoints are 900px, 600px and 500px; reuse them.
- **Modular, minimal CSS:** small single-purpose classes with a page prefix (`.dash-`, `.expenses-`), no `!important`, no boilerplate resets (the global reset already exists).
## Icons
 
Use meaningful icons: an icon should tell the user what something is (a fork and knife for Food, a bus for Transport), not decorate. Because the project forbids npm packages and external libraries, use **inline SVG** in Lucide/Feather style: `viewBox="0 0 24 24"`, `fill="none"`, `stroke="currentColor"`, `stroke-width="1.75"`, round caps and joins. `currentColor` lets icons inherit colour from CSS. Always add `aria-hidden="true"` to decorative icons and a text label or `aria-label` for icon-only buttons. `references/components.md` has ready-to-paste paths for the expense categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other) and common UI actions (add, edit, delete, calendar, filter, search, trends).
 
When an icon repeats (a category icon in every table row), use the macros in `assets/_icons.html` (`icon(name)`, `category_icon(category)`, and `rupees(amount)` for ₹ formatting) so the SVG markup is defined once. Import with `{% from "_icons.html" import icon, category_icon, rupees %}`. Add new icon paths to that file's dictionary rather than pasting SVG into pages.
 
## Verify visually
 
Rendering the page and looking at it catches bugs that reading the code never will. `scripts/screenshot.py` takes screenshots at 1280px and 375px and reports sideways scrolling:
 
```bash
python scripts/screenshot.py --base http://127.0.0.1:5001 --out ./screenshots /dashboard:dashboard
```
 
It needs the page reachable in a running app. If the route isn't wired up yet (stubs are the norm here), render through a throwaway preview app that lives *outside* the project: import the project's `app`, add temporary `/preview/...` routes that log in a fake session and `render_template` your page with sample data, and run it on a spare port. That way the project files stay untouched. If Playwright or a browser isn't available, say so and skip rather than claiming it was checked.
 
Then open the screenshots and actually look. Things that have gone wrong before and are worth checking on purpose:
- Table cells with `display: flex` lose their table-cell behaviour (dividers misalign); put the flex layout on a `<div>` inside the cell.
- When a table turns into stacked cards on mobile, the overrides must be more specific than the generic `td` rule (write `.my-table .my-cell`), or `display: none` silently fails and content shows twice.
- An override like `.th-amount { text-align: right }` loses to `.table th { text-align: left }`; match or beat the specificity.
- The existing navbar wraps at 375px when logged in (greeting plus button); hide `.nav-greeting` under 600px.
- Seven category tiles can't fill a grid evenly; a lone tile on the last row is fine, but check that long names ("Entertainment") don't overflow.
## Data the UI works with
 
Schema (from `database/db.py`): `users(id, name, email, created_at)` and `expenses(id, user_id, amount REAL, category TEXT, date TEXT ISO, description TEXT, created_at)`. Seeded categories are **Food, Transport, Bills, Health, Entertainment, Shopping, Other**. The seed user is Demo User (`demo@spendly.com`), with amounts like ₹450, ₹1,200 and ₹2,200. Use these categories and realistic rupee amounts in sample data. Show dates in a readable form (`12 Sep 2026`) rather than raw ISO.
 
## Output format
 
Keep the reply tight. The user wants the result, not a lecture.
 
1. **UI structure (brief):** the layout in a few lines (page sections top to bottom, grid columns) plus 2 to 4 important UX decisions and why. A short list is fine here.
2. **Code:** create the files (template, page CSS, any JS) in the project rather than pasting long code into chat. Then list the files created or changed with one line each. Include a short snippet in chat only when it's the point (a route the user must add).
3. **Notes:** which icons were used and where, which existing classes/tokens were reused, any new CSS variables added, and the route/context the template expects.
If the environment allows it, preview the page (run the Flask app on port 5001, or render the template with sample data) and glance at it at desktop and mobile widths before handing it over. If you can't preview, say so.
 
## Checklist before you finish
 
- Extends `base.html`; uses `url_for()` everywhere; no inline `<style>`.
- No raw hex in new rules (variables only); fonts and radii from tokens.
- Reuses existing classes (`.btn-primary`, `.btn-ghost`, `.form-input`, `.form-group`, card patterns) instead of duplicating them.
- Works at 375px, 768px and 1200px wide; no horizontal page scroll. You have looked at real screenshots, not just read the code.
- Every input has a label; icon-only controls have `aria-label`; text contrast is readable.
- Empty, error and loading-ish states considered.
- Vanilla JS only; no new dependencies.
 