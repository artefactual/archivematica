# popover

`popover` is a frontend feature that rewrites the behavior Archivematica needs
from Bootstrap 3's `popover.js` (`v3.4.1`) as a small TypeScript module without
jQuery.

## Context

Bootstrap 3's `popover.js` extends `tooltip.js`. This feature reproduces the
popover interactions used by Archivematica templates (not the full Bootstrap
plugin surface), using a shared DOM popover element and delegated page-level
handlers.

## Usage

Load the feature in the Django template:

```django
{% block data_features %}popover{% endblock %}
```

Annotate targets with `data-toggle="popover"`, a title, and `data-content`:

```html
<a data-toggle="popover" href="#" title="Location" data-content="/path/to/file">
  Example
</a>
```

## Behavior

The feature provides Bootstrap 3-style popover interactions for Archivematica's
legacy tables and links:

- shows on hover and focus
- hides on mouse leave, blur, or outside click
- repositions on scroll/resize
- prevents navigation for `href="#"` popover links

Content and title are inserted as plain text (`textContent`), not HTML.

## Notes

This implementation intentionally favors predictable text-only rendering for the
current Archivematica use cases. It also strips `%...%` tokens from
`data-content` before display to avoid leaking formatting placeholders from the
source strings used in some reports.
