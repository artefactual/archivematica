# tab

`tab` is a frontend feature that rewrites the behavior of Bootstrap 3's
`tab.js` (`v3.4.1`) in TypeScript without jQuery.

## Context

This feature provides a compatibility-oriented reproduction of the Bootstrap 3
Tab data API patterns used in Archivematica templates (for example archival
storage views), while integrating with our core feature loader.

## Usage

Load the feature in the Django template:

```django
{% block data_features %}tab{% endblock %}
```

Use Bootstrap-style tab markup inside an `.am-tabs-pane` container:

```html
<section class="am-tabs-pane">
  <ul class="nav nav-tabs" data-active-tab="details">
    <li class="active"><a href="#tab-summary">Summary</a></li>
    <li><a href="#tab-details">Details</a></li>
  </ul>

  <div class="tab-content">
    <div class="tab-pane active" id="tab-summary">...</div>
    <div class="tab-pane" id="tab-details">...</div>
  </div>
</section>
```

`data-active-tab` accepts either a bare suffix (`details` -> `#tab-details`) or
an explicit fragment (`#tab-details`).

## Behavior

The feature initializes matching tab containers in the document and supports:

- click activation for tab links using `href="#..."` or `data-target="#..."`
- optional initial tab activation via `data-active-tab`
- Bootstrap-style classes (`active`, and `in` for fade panes)

## Notes

This is a focused rewrite for Archivematica templates, not a full Bootstrap
jQuery plugin port. Programmatic use is available through `initTabs()` and the
returned controller (`activate(tabSelector)`).

Bootstrap-style jQuery plugin APIs and `*.bs.tab` custom event hooks are not
exposed by this rewrite. We removed them because there are no in-repo
consumers and they add unused compatibility behavior.
