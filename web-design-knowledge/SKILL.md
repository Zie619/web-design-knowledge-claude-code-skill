---
name: web-design-knowledge
description: Provides expert web design guidance backed by a curated library of 23 professional design books covering color theory, typography, layout, UI/UX patterns, responsive design, and CSS techniques. Use this skill when users are building web interfaces, creating designs, need color/typography/layout advice, or want UX best practices.
license: Complete terms in LICENSE.txt
---

# Web Design Knowledge Skill

This skill provides access to a comprehensive web design knowledge base built from 23 curated design books. It enables Claude to provide expert, book-backed guidance on all aspects of web design.

## When to Use This Skill

This skill should be activated when:

1. **Creating new interfaces** - Landing pages, dashboards, forms, settings pages
2. **Choosing colors** - Palette selection, color harmony, accessibility compliance
3. **Typography decisions** - Font pairing, type hierarchy, readability
4. **Layout design** - Grid systems, spacing, responsive breakpoints
5. **UX improvements** - User flows, interaction patterns, usability
6. **CSS implementation** - Modern techniques, animations, best practices
7. **Visual hierarchy** - Emphasis, contrast, attention flow
8. **Branding consistency** - Design systems, style guides

## Available MCP Tools

The `web_design_mcp` server provides four specialized query tools:

### 1. `web_design_query`

General-purpose query for any web design question.

**Parameters:**
- `query` (required): Natural language question about web design
- `topics` (optional): Filter by topics (color_theory, typography, layout, ux_principles, ui_patterns, responsive, css_techniques, visual_hierarchy, branding, navigation, forms_inputs, performance)
- `n_results` (optional): Number of passages to retrieve (default: 5, max: 15)
- `response_format` (optional): "markdown" or "json"

**Use for:** Open-ended design questions, exploring concepts, research

### 2. `web_design_color_advice`

Specialized color palette and harmony guidance.

**Parameters:**
- `context` (required): Design context (e.g., "healthcare app", "fashion e-commerce")
- `mood` (optional): Desired tone (professional, playful, calm, energetic, luxurious, trustworthy, modern, minimalist, bold, warm)
- `constraints` (optional): Color requirements (e.g., "must include brand blue #0066CC")
- `include_accessibility` (optional): Include WCAG guidance (default: true)

**Use for:** Choosing color palettes, understanding color psychology, ensuring accessibility

### 3. `web_design_layout_patterns`

Layout patterns and structural recommendations.

**Parameters:**
- `page_type` (required): landing_page, dashboard, blog, portfolio, ecommerce, settings, profile, search_results, form_page, documentation
- `device_target` (optional): responsive, mobile, tablet, desktop
- `content_density` (optional): low, medium, high
- `key_elements` (optional): Elements to include

**Use for:** Structuring pages, choosing grid systems, responsive layouts

### 4. `web_design_ux_review`

UX best practices for specific features.

**Parameters:**
- `feature` (required): Feature or flow to review (e.g., "checkout flow", "user onboarding")
- `current_approach` (optional): Current implementation description
- `user_context` (optional): Target user context

**Use for:** Improving usability, reviewing flows, applying UX principles

## Integration Guidelines

When using the design knowledge tools:

1. **Synthesize multiple sources** - Combine insights from different passages to provide comprehensive guidance
2. **Adapt to context** - Apply general principles to the specific constraints of the project
3. **Prioritize actionable advice** - Focus on practical steps the user can implement
4. **Consider trade-offs** - Different sources may suggest different approaches; explain when each is appropriate
5. **Cite appropriately** - Reference which book or principle informed decisions when relevant

## Knowledge Coverage

The knowledge base covers content from authoritative design books including:

| Topic | Key Sources |
|-------|------------|
| **Color Theory** | Web Design Basics: Color Choices, The Principles of Beautiful Web Design |
| **Typography** | Learning Web Design 6E, Handcrafted CSS |
| **Layout** | Principles of Web Design, CSS Portfolio App Design |
| **UX Principles** | Roots of UI/UX Design, UX and UI Strategy |
| **UI Patterns** | Ultimate UI/UX Design for Professionals, Designing Apps for Success |
| **Responsive** | Responsive Web Design (Ethan Marcotte), Responsive Web Design in Practice |
| **CSS Techniques** | Learning Web Design 6E, Handcrafted CSS |
| **Visual Hierarchy** | The Principles of Beautiful Web Design, Architectural Approach to Level Design |
| **Branding** | Design Culture, Ultimate Figma for UI/UX Design |

## Example Queries

```
# Color palette for a healthcare startup
web_design_color_advice(
    context="healthcare startup for elderly patients",
    mood="trustworthy",
    include_accessibility=true
)

# Dashboard layout patterns
web_design_layout_patterns(
    page_type="dashboard",
    content_density="high",
    key_elements="metrics cards, activity feed, quick actions"
)

# General typography question
web_design_query(
    query="How do I create an effective type hierarchy for a content-heavy website?",
    topics=["typography", "visual_hierarchy"]
)

# UX review for checkout
web_design_ux_review(
    feature="checkout flow",
    current_approach="multi-step wizard with progress bar",
    user_context="mobile users"
)
```

## Topic Reference

For detailed topic descriptions and example queries, see [references/design_topics.md](./references/design_topics.md).
