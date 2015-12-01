from .common import *

DEBUG = True
TEMPLATE_DEBUG = True
FPR_URL = 'https://fpr-qa.archivematica.org/fpr/api/v2/'
FPR_VERIFY_CERT = False

FIXTURE_DIRS = (
    'tests/fixtures/',
    '../archivematicaCommon/tests/fixtures/'
)
