# This file must be used with "source hack/activate.fish" *from fish*
# (https://fishshell.com/). You cannot run it directly.

function deactivate -d "Exit virtual environment and return to normal shell environment"
    if test -n "$_OLD_VIRTUAL_PATH"
        set -gx PATH $_OLD_VIRTUAL_PATH
        set -e _OLD_VIRTUAL_PATH
    end

    if test -n "$_OLD_FISH_PROMPT_OVERRIDE"
        set -e _OLD_FISH_PROMPT_OVERRIDE
        # prevents error when using nested fish instances (Issue #93858)
        if functions -q _old_fish_prompt
            functions -e fish_prompt
            functions -c _old_fish_prompt fish_prompt
            functions -e _old_fish_prompt
        end
    end

    set -e VIRTUAL_ENV
    set -e VIRTUAL_ENV_PROMPT
    if test "$argv[1]" != "nondestructive"
        # Self-destruct!
        functions -e deactivate
    end
end

# Unset irrelevant variables.
deactivate nondestructive

set -gx VIRTUAL_ENV "$HOME/.cache/ccp/Linux/x86_64/bin"

set -gx _OLD_VIRTUAL_PATH $PATH
set -gx PATH "$VIRTUAL_ENV" $PATH

if test -z "$VIRTUAL_ENV_DISABLE_PROMPT"
    functions -c fish_prompt _old_fish_prompt
    function fish_prompt
        set -l old_status $status
        printf "%s%s%s" (set_color 4B8BBE) "(.venv) " (set_color normal)
        echo "exit $old_status" | .
        _old_fish_prompt
    end
    set -gx _OLD_FISH_PROMPT_OVERRIDE "$VIRTUAL_ENV"
    set -gx VIRTUAL_ENV_PROMPT "(.venv) "
end


