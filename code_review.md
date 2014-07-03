Code review
===========

Every new feature and bugfix to a project is expected to go through code review before inclusion.
This applies both to developers at Artefactual and to outside contributors.

Here's an outline of the code review process:

1. Fork the Artefactual project on GitHub, and commit your changes to a branch.
2. Open a pull request.
3. Back and forth discussion with developers on the branch.
4. Make any changes suggested by reviewers.
5. Repeat 3 and 4 as necessary.
6. Clean up commit history, if necessary.
7. Your branch will be merged!

Getting started
---------------

So you have something to contribute to an Artefactual project. Great!

Artefactual uses [GitHub](https://github.com/)'s pull request feature for code review.
Every change being submitted to an Artefactual project should be submitted as a pull request to the appropriate repository.
A branch being submitted for code review should contain commits covering a related section of code.
Try not to bundle unrelated changes together in one branch; it makes review harder.

If you're not familiar with forking repositories and creating branches in GitHub, consult their [guide](https://help.github.com/articles/fork-a-repo).

When to submit code for review?
-------------------------------

Your code doesn't have to be ready yet to submit for code review!
You should submit a branch for code review as soon as you want to get feedback on it.
Sometimes, that means submitting a feature-complete branch, but sometimes that means submitting an early WIP n order to get feedback on direction.
Don't be shy about submitting early.

Opening the pull request
------------------------

GitHub has an [excellent](https://help.github.com/articles/using-pull-requests) guide on using the pull request feature.

Discussion
----------

Discussion on pull requests is usually a back and forth process.
Don't feel like you have to make every change the reviewer suggests; the pull request is a great place to have in-depth conversation on the issue.

Do make use of GitHub's line comment feature!

![Line comment](http://i.imgur.com/FsWppGN.png)

By viewing the "Files changed", you can leave a comment on any line of the diff.
This is a great way to scope discussion to a particular part of a diff.
Any discussion you have in a specific part of the diff will also be automatically hidden once a change is pushed that addresses it, which helps keep the pull request page clear and readable.

When leaving line comments, make sure you leave them on the *diff* - not on the page for an individual commit.
Any comments left on the commit will disappear from the pull request page as soon as that commit is no longer in the branch, even if a newer revision of that commit is.

Anyone can participate in code review discussions.
Feel free to jump in if you have something to contribute on another pull request, even if you're not the one who opened it.

Cleaning up commit history
--------------------------

Once code review is finished or nearly finished, and no further development is planned on the branch, the branch's commit history should be cleaned up.
You can alter the commit history of a branch using git's powerful [interactive rebase feature](http://www.git-scm.com/book/en/Git-Tools-Rewriting-History).
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

### Commit messages should be as detailed as they need to be (and no more)

The commit message is the rest of the commit past the first line.
If a commit makes a small and obvious change, it's fine to not even have a commit message past the summary.

The commit message is your place to clarify the justification for a change.
While there's no need to rehash anything that code comments already say, if there's more detail that helps a reader understand *why* a change was made, be as verbose as you need to!
Remember: future-you (or another developer) will read this when going through the commit history to understand why a change was made.
Make their life easier.
