Code review
===========

Every new feature and bugfix to a project is expected to go through code review before inclusion.
This applies both to developers at Artefactual and to outside contributors.

Cleaning up commit history
--------------------------

Once code review is finished or nearly finished, and no further development is planned on the branch, the branch's commit history should be cleaned up.
The following few criteria help outline what makes for a clean commit history:

### Commits should be specific and atomic

Any single commit should cover a specific change.
That change might span multiple files, but it shouldn't introduce multiple distinct functional changes unless it's impossible to separate those changes from each other.
It's okay (and normal!) for a branch that makes a lot of changes to consist of many small commits, each of which makes individual small changes.
This makes it easier to revert individual commits from a branch, and also makes it easier to isolate the commit that caused a particular bug with git-blame.

In development, it's common to introduce a change with a commit and then introduce multiple other commits with small fixes for that change.
When getting ready for merging, those commits should all be squashed together.

### Every commit should work

No individual commit should put the software in a broken state.
It's fine for code to go unused (because the feature it's been introduced for isn't there yet), but no new functional issues should be introduced by a given commit.
This ensures that reverting any individual commit from the branch is safe, and that git-bisect stays reliable for tracking down bugs.

### Commit summaries should be concise

The commit summary (the first line of a commit message) should be short and clear.
Usually, the first line of the commit message should be 50 - 80 characters.
Since the summary is just a *summary* of the change, it should be readable at a glance when looking through git history.

A good commit summary makes it clear a) what *part* of the code is changing, and b) what the change is.
For example:

Clear commit summary:
> normalize: fall back to default rule for unidentified files

Unclear commit summaries:
> Fixed some normalization bugs

> Bugfixes

The unclear messages make it hard to tell at a glance what changed, and that makes browsing the commit history harder.

### Commit messages should be as detailed as they need to be

The commit message is the rest of the commit past the first line.
If a commit makes a small and obvious change, it's fine to not even have a commit message past the summary.

The commit message is your place to clarify the justification for a change.
While there's no need to rehash anything that code comments already say, if there's more detail that helps a reader understand *why* a change was made, be as verbose as you need to!
Remember: future-you (or another developer) will read this when going through the commit history to understand why a change was made.
Make their life easier.
