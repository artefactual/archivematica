# Archivematica transfer browser

Translations
------------

This process has not been wired with Webpack yet.

You need to install `angular-gettext-cli` and `transifex-client`. They are not
application dependencies.

    npm install -g angular-gettext-cli
    pip install transifex-client

Extract messages:

    # Attention, this is going to include the dist file - please remove before you run this command!
    rm app/transfer_browser.js
    angular-gettext-cli --files "./app/**/*.+(js|html)" --dest "./app/locale/extract.pot" --marker-name "i18n"

Push messages to Transifex:

    tx push -s

Pull translations from Transifex:

    tx pull -a

Compile messages:

    angular-gettext-cli --compile --files "app/locale/*.po" --dest "app/locale/translations.json" --format "json" --module "transferBrowse"

The contents of `app/locale` should be tracked in git.
