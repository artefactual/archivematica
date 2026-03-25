# clipboard-field

`clipboard-field` is a frontend feature that registers the
`am-clipboard-field` web component.

The component renders a read-only text input with a copy button and copy status
feedback. It uses light DOM (not Shadow DOM), so existing Bootstrap and Font
Awesome styles apply directly.

## Usage

Load the feature in the Django template:

```django
{% block data_features %}clipboard-field{% endblock %}
```

Then use the component:

```html
<am-clipboard-field value="{{ key }}"></am-clipboard-field>
```

You should see a read-only text field with a copy button.

## Accessibility

The component uses a native button plus ARIA state updates (`aria-label` and a
polite live region) so copy feedback is available to screen readers without
showing visible success text. The status area is kept non-visual (`.sr-only`)
for successful copies, and becomes visible for copy failures so users can see
the manual-copy fallback message.

## Notes

This feature currently uses light DOM intentionally to inherit Bootstrap and
Font Awesome styling from the page. The feature also imports a small
co-located stylesheet (`style.css`) for namespaced component-specific styles
such as the copy-success icon animation.
