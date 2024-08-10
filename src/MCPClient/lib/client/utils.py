import shlex
from typing import List

from django.conf import settings
from django.utils import timezone


def parse_command_line(s: str) -> List[str]:
    return [_shlex_unescape(x) for x in shlex.split(s)]


# If we're looking at an escaped backtick, drop the escape
# character.  Shlex doesn't do this but bash unescaping does, and we
# want to remain compatible.
def _shlex_unescape(s: str) -> str:
    return "".join(c1 for c1, c2 in zip(s, s[1:] + ".") if (c1, c2) != ("\\", "`"))


def replace_task_arguments(
    arguments: str, task_uuid: str, task_created_date: str
) -> str:
    replacements = {
        r"%sharedPath%": settings.SHARED_DIRECTORY,
        r"%clientAssetsDirectory%": settings.CLIENT_ASSETS_DIRECTORY,
        r"%date%": timezone.now().isoformat(),
        r"%taskUUID%": task_uuid,
        r"%jobCreatedDate%": task_created_date,
    }
    for key, val in replacements.items():
        arguments = arguments.replace(key, val)

    return arguments
