STATUS_DELETE_REQUESTED = "DEL_REQ"
STATUS_DELETED = "DELETED"
STATUS_UPLOADED = "UPLOADED"
STATUS_BACKLOG = "backlog"

AIPS_INDEX = "aips"
AIP_FILES_INDEX = "aipfiles"
TRANSFERS_INDEX = "transfers"
TRANSFER_FILES_INDEX = "transferfiles"

ES_FIELD_AICID = "AICID"
ES_FIELD_ACCESSION_IDS = "accessionids"
ES_FIELD_AICCOUNT = "countAIPsinAIC"
ES_FIELD_CREATED = "created"
ES_FIELD_ENCRYPTED = "encrypted"
ES_FIELD_FILECOUNT = "file_count"
ES_FIELD_LOCATION = "location"
ES_FIELD_NAME = "name"
ES_FIELD_SIZE = "size"
ES_FIELD_STATUS = "status"
ES_FIELD_UUID = "uuid"

# Additional Elasticsearch field names
ES_FIELD_AIPUUID = "AIPUUID"
ES_FIELD_FILEUUID = "FILEUUID"
ES_FIELD_SIPUUID = "sipuuid"
ES_FIELD_FILEUUID_LOWER = "fileuuid"

DEFAULT_TIMEOUT = 10
# Known indexes. This indexes may be enabled or not based on the SEARCH_ENABLED
# setting. To add a new index, make sure it's related to the setting values in
# the setup functions below, add its name to the following array and create a
# function declaring the index settings and mapping. For example, for an index
# called `tests` the function must be called `_get_tests_index_body`. See the
# functions related to the current known indexes for examples.
INDEXES = [AIPS_INDEX, AIP_FILES_INDEX, TRANSFERS_INDEX, TRANSFER_FILES_INDEX]
# Maximun ES result window. Use the scroll API for a better way to get all
# results or change `index.max_result_window` on each index settings.
MAX_QUERY_SIZE = 10000
# Maximun amount of fields per index (increased from the ES default of 1000).
TOTAL_FIELDS_LIMIT = 10000
# Maximum index depth (increased from the ES default of 20). The way the
# `structMap` element from the METS file is parsed may create a big depth
# in documents for AIPs with a big directories hierarchy.
DEPTH_LIMIT = 1000
