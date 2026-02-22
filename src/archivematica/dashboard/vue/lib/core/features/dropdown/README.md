# dropdown

`dropdown` is a frontend feature that rewrites the behavior of Bootstrap 3's
`dropdown.js` (`v3.4.1`) in TypeScript without jQuery.

Archivematica loads this feature by default from `layout.html` via the core
feature bootstrapping (`data-features="dropdown ..."`).

## Context

This implementation is a compatibility-oriented reproduction of the Bootstrap 3
Dropdown data API used by Archivematica templates, with Archivematica-specific
feature loading (`data-features`) but Bootstrap-style dropdown activation
selectors (`data-toggle="dropdown"`).

## Usage

Minimal markup:

```html
<li class="dropdown">
  <a class="dropdown-toggle" data-toggle="dropdown" aria-expanded="false">
    Menu
  </a>
  <ul class="dropdown-menu" aria-labelledby="menu-id">
    <li><a href="/profile">Profile</a></li>
    <li>
      <form method="post">
        <button type="submit">Log out</button>
      </form>
    </li>
  </ul>
</li>
```

Optional explicit root targeting is supported with `data-target`:

```html
<a data-toggle="dropdown" data-target="#my-dropdown">Open</a>
<div id="my-dropdown" class="dropdown">...</div>
```

## Behavior

The feature reproduces the Bootstrap 3-style interactions used in the legacy UI:

- click to open/close
- `ArrowDown`/`ArrowUp` keyboard navigation between menu links
- `Escape` closes the dropdown and returns focus to the toggle
- form clicks inside dropdown menus do not close the menu

## Notes

This is a DOM/event rewrite, not a full Bootstrap JS plugin port. It preserves
Archivematica behavior while avoiding jQuery plugin registration and Bootstrap's
mobile backdrop helper.

Bootstrap-style jQuery plugin APIs and `*.bs.dropdown` custom event hooks are
not exposed by this rewrite. We removed them because there are no in-repo
consumers and they add compatibility surface we are not using.
