import logging
import time
from abc import ABC
from abc import abstractmethod
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any
from typing import Literal
from typing import Optional
from typing import TypedDict
from typing import Union

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.exceptions import RequestError
from elasticsearch.helpers import bulk

from archivematica.search.constants import AIP_FILES_INDEX
from archivematica.search.constants import AIPS_INDEX
from archivematica.search.constants import DEFAULT_TIMEOUT
from archivematica.search.constants import DEPTH_LIMIT
from archivematica.search.constants import ES_FIELD_ACCESSION_IDS
from archivematica.search.constants import ES_FIELD_AICCOUNT
from archivematica.search.constants import ES_FIELD_AICID
from archivematica.search.constants import ES_FIELD_AIPUUID
from archivematica.search.constants import ES_FIELD_CREATED
from archivematica.search.constants import ES_FIELD_ENCRYPTED
from archivematica.search.constants import ES_FIELD_FILECOUNT
from archivematica.search.constants import ES_FIELD_FILEUUID
from archivematica.search.constants import ES_FIELD_LOCATION
from archivematica.search.constants import ES_FIELD_NAME
from archivematica.search.constants import ES_FIELD_SIZE
from archivematica.search.constants import ES_FIELD_STATUS
from archivematica.search.constants import ES_FIELD_UUID
from archivematica.search.constants import STATUS_DELETE_REQUESTED
from archivematica.search.constants import STATUS_UPLOADED
from archivematica.search.constants import TOTAL_FIELDS_LIMIT

logger = logging.getLogger("archivematica.search")


_search_service_instance: Optional["SearchService"] = None


@dataclass
class SearchBackendInfo:
    """Information about the search backend connection."""

    name: str
    version: str
    cluster_name: Optional[str] = None
    raw_info: Optional[dict[str, Any]] = None


@dataclass
class SortSpec:
    """Represents search sort specification with field name and order."""

    field: str
    order: Literal["asc", "desc"] = "asc"


class SearchServiceError(Exception):
    """Base exception for search service operations."""

    pass


class AIPNotFoundError(SearchServiceError):
    """Raised when an AIP cannot be found by UUID."""

    pass


class AIPFileNotFoundError(SearchServiceError):
    """Raised when an AIP file cannot be found by UUID."""

    pass


class MultipleResultsError(SearchServiceError):
    """Raised when a search expected to return a single result returns multiple."""

    pass


class SearchService(ABC):
    """Abstract base class for search services."""

    @abstractmethod
    def delete_aip(self, aip_uuid: str) -> None:
        """Delete AIP from the search index.

        :param str aip_uuid: AIP UUID to delete
        """
        pass

    @abstractmethod
    def delete_aip_files(self, aip_uuid: str) -> None:
        """Delete AIP files from the search index.

        :param str aip_uuid: AIP UUID to delete files for
        """
        pass

    @abstractmethod
    def mark_aip_for_deletion(self, aip_uuid: str, refresh: bool = False) -> None:
        """Mark AIP for deletion in the search index.

        :param str aip_uuid: AIP UUID to mark for deletion
        :param bool refresh: Whether to refresh affected indexes immediately
        """
        pass

    @abstractmethod
    def unmark_aip_for_deletion(self, aip_uuid: str, refresh: bool = False) -> None:
        """Unmark AIP for deletion in the search index.

        :param str aip_uuid: AIP UUID to unmark for deletion
        :param bool refresh: Whether to refresh affected indexes immediately
        """
        pass

    @abstractmethod
    def ensure_indexes_exist(self, indexes: list[str]) -> None:
        """Ensure the specified search indexes exist.

        Creates any missing indexes with their appropriate settings and mappings.

        :param list[str] indexes: List of index names to ensure exist
        """
        pass

    @abstractmethod
    def delete_indexes(self, indexes: list[str]) -> None:
        """Delete the specified search indexes.

        :param list[str] indexes: List of index names to delete
        """
        pass

    @abstractmethod
    def update_index_mappings(self, index: str, mappings: dict[str, Any]) -> None:
        """Update mappings for a specific index.

        :param str index: Index name to update
        :param dict[str, Any] mappings: Mapping properties to apply
        """
        pass

    @abstractmethod
    def reindex_from_remote(
        self, remote_config: dict[str, Any], index_mappings: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Reindex data from a remote search cluster.

        :param dict[str, Any] remote_config: Remote cluster configuration
        :param list[dict[str, str]] index_mappings: Source to destination index mappings
        :return: Results of reindex operations
        """
        pass

    @abstractmethod
    def update_all_documents(self, index: str) -> dict[str, Any]:
        """Update all documents in an index.

        Useful for populating new mapping fields after schema changes.

        :param str index: Index name to update
        :return: Update operation results
        """
        pass

    @abstractmethod
    def get_aip_data(
        self, uuid: str, fields: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Get AIP data by UUID.

        :param str uuid: AIP UUID to retrieve
        :param Optional[list[str]] fields: Optional list of fields to return
        :return: AIP document data
        """
        pass

    @abstractmethod
    def get_aipfile_data(
        self, uuid: str, fields: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Get AIP file data by file UUID.

        :param str uuid: File UUID to retrieve
        :param Optional[list[str]] fields: Optional list of fields to return
        :return: AIP file document data
        """
        pass

    @abstractmethod
    def get_aipfile_by_document_id(self, document_id: str) -> dict[str, Any]:
        """Get AIP file document by document ID.

        :param str document_id: Document ID
        :return: Complete document data including metadata
        :raises AIPFileNotFoundError: When document is not found
        """
        pass

    @abstractmethod
    def search_aips(
        self,
        query: dict[str, Any],
        size: Optional[int] = None,
        from_: Optional[int] = None,
        sort: Optional[SortSpec] = None,
        fields: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Search AIPs with optional parameters.

        :param dict[str, Any] query: Search query body
        :param Optional[int] size: Optional size limit for results, defaults to max_query_size
        :param Optional[int] from_: Optional start index for pagination
        :param Optional[SortSpec] sort: Optional sort specification with field and order
        :param Optional[list[str]] fields: Optional list of fields to return
        :return: Raw search results
        """
        pass

    @abstractmethod
    def search_aip_files(
        self,
        query: dict[str, Any],
        size: Optional[int] = None,
        from_: Optional[int] = None,
        sort: Optional[SortSpec] = None,
        fields: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Search AIP files with optional parameters.

        :param dict[str, Any] query: Search query body
        :param Optional[int] size: Optional size limit for results, defaults to max_query_size
        :param Optional[int] from_: Optional start index for pagination
        :param Optional[SortSpec] sort: Optional sort specification with field and order
        :param Optional[list[str]] fields: Optional list of fields to return
        :return: Raw search results
        """
        pass

    @abstractmethod
    def count_aip_files(self, query: dict[str, Any]) -> int:
        """Count AIP files matching the given query.

        :param dict[str, Any] query: Search query body
        :return: Number of AIP files matching the query
        """
        pass

    @abstractmethod
    def get_cluster_info(self) -> SearchBackendInfo:
        """Get search backend cluster information.

        :return: SearchBackendInfo containing cluster information and backend details
        :raises SearchServiceError: When unable to connect to search backend
        """
        pass

    @abstractmethod
    def index_aip(
        self,
        uuid: str,
        aip_stored_path: str,
        parser: Any,
        name: str,
        aip_size: int,
        am_version: str,
        indexed_at: str,
        identifiers: list[dict[str, str]],
        aips_in_aic: Optional[int] = None,
        encrypted: bool = False,
        location: str = "",
        dashboard_uuid: str = "",
    ) -> int:
        """Index AIP and AIP files.

        :param str uuid: UUID of the AIP to index
        :param str aip_stored_path: Path on disk where the AIP is located
        :param Any parser: AIPMETSParser instance
        :param str name: AIP name
        :param int aip_size: AIP size in bytes
        :param str am_version: Archivematica version
        :param str indexed_at: Timestamp when indexing occurred
        :param list[dict[str, str]] identifiers: Additional identifiers (MODS, Islandora, etc.)
        :param Optional[int] aips_in_aic: Number of AIPs stored in AIC
        :param bool encrypted: Whether AIP is encrypted
        :param str location: AIP location
        :param str dashboard_uuid: Pipeline UUID
        :return: 0 if succeeded, 1 otherwise
        """
        pass


class TermQuery(TypedDict):
    term: dict[str, str]


class TermsQuery(TypedDict):
    terms: dict[str, list[str]]


class DeleteByQueryBody(TypedDict):
    query: Union[TermQuery, TermsQuery]


class ScriptDict(TypedDict):
    source: str
    params: dict[str, Union[str, bool, list[str]]]


class UpdateByQueryBody(TypedDict):
    script: ScriptDict
    query: TermQuery


class ElasticsearchSearchService(SearchService):
    """Elasticsearch implementation of SearchService."""

    def __init__(
        self,
        client: Elasticsearch,
        aip_files_index: str = "aipfiles",
        aips_index: str = "aips",
        max_query_size: int = 10000,
    ) -> None:
        """Initialize with Elasticsearch client and configuration.

        :param Elasticsearch client: Elasticsearch client instance
        :param str aip_files_index: Name of the AIP files index
        :param str aips_index: Name of the AIPs index
        :param int max_query_size: Maximum size for Elasticsearch queries
        """
        self.client = client
        self.aip_files_index = aip_files_index
        self.aips_index = aips_index
        self.max_query_size = max_query_size

    def _escape_slashes(self, value: str) -> str:
        """Escape forward slashes for Elasticsearch queries.

        :param str value: value to escape
        :return: value with forward slashes escaped
        """
        return str(value).replace("/", "\\/")

    def _delete_by_field(
        self, index: str, field: str, value: Union[str, set[str]]
    ) -> None:
        """Delete documents from Elasticsearch index by field value(s).

        :param str index: Elasticsearch index name
        :param str field: Field name to query on
        :param Union[str, set[str]] value: Single value or set of values to match
        """
        if not value:
            return

        query: DeleteByQueryBody
        if isinstance(value, str):
            query = {"query": {"term": {field: self._escape_slashes(value)}}}
        else:
            escaped_value = [self._escape_slashes(v) for v in value]
            query = {"query": {"terms": {field: escaped_value}}}

        self.client.delete_by_query(index=index, body=query)

    def _update_by_field(
        self,
        index: str,
        field: str,
        value: str,
        update_field: str,
        update_value: Union[str, bool, list[str]],
        refresh: bool = False,
    ) -> None:
        """Update documents in Elasticsearch index by field value.

        :param str index: Elasticsearch index name
        :param str field: Field name to query on
        :param str value: Value to match in query field
        :param str update_field: Field to update
        :param Union[str, bool, list[str]] update_value: Value to set in update field
        :param bool refresh: Whether to refresh index after update
        """
        escaped_value = self._escape_slashes(value)
        query = self._build_update_query(
            field, escaped_value, update_field, update_value
        )
        self.client.update_by_query(index=index, body=query, refresh=refresh)

    def _build_update_query(
        self,
        query_field: str,
        query_value: str,
        update_field: str,
        update_value: Union[str, bool, list[str]],
    ) -> UpdateByQueryBody:
        """Build an update_by_query body for Elasticsearch.

        :param str query_field: Field to query on
        :param str query_value: Value to match in query field
        :param str update_field: Field to update
        :param Union[str, bool, list[str]] update_value: Value to set in update field
        :return: Dictionary representing the update query body
        """
        return {
            "script": {
                "source": f"ctx._source.{update_field} = params.value",
                "params": {"value": update_value},
            },
            "query": {"term": {query_field: query_value}},
        }

    def _update_field_for_package_and_files(
        self,
        package_index: str,
        files_index: str,
        package_uuid_field: str,
        package_uuid: str,
        field: str,
        value: Union[str, bool],
        refresh: bool = False,
    ) -> None:
        """Update field for a package and its related files using bulk operations.

        :param str package_index: Name of package index to update
        :param str files_index: Name of files index to update
        :param str package_uuid_field: Name of ES field for package UUID in files index
        :param str package_uuid: UUID of package to update
        :param str field: Field in indices to update
        :param Union[str, bool] value: Value to set in updated field
        :param bool refresh: Whether to refresh affected indexes after updates
        """
        self._update_by_field(
            package_index, ES_FIELD_UUID, package_uuid, field, value, refresh=refresh
        )
        self._update_by_field(
            files_index,
            package_uuid_field,
            package_uuid,
            field,
            value,
            refresh=refresh,
        )

    def _update_aip_pending_deletion(
        self, aip_uuid: str, pending: bool, refresh: bool = False
    ) -> None:
        """Update status field for an AIP and its files based on pending deletion.

        :param str aip_uuid: AIP UUID to update
        :param bool pending: Whether AIP is pending deletion
        :param bool refresh: Whether to refresh affected indexes after updates
        """
        status_value = STATUS_DELETE_REQUESTED if pending else STATUS_UPLOADED
        self._update_field_for_package_and_files(
            self.aips_index,
            self.aip_files_index,
            ES_FIELD_AIPUUID,
            aip_uuid,
            ES_FIELD_STATUS,
            status_value,
            refresh=refresh,
        )

    def delete_aip(self, aip_uuid: str) -> None:
        """Delete AIP from the Elasticsearch index.

        :param str aip_uuid: AIP UUID to delete
        """
        self._delete_by_field(self.aips_index, ES_FIELD_UUID, aip_uuid)

    def delete_aip_files(self, aip_uuid: str) -> None:
        """Delete AIP files from the Elasticsearch index.

        :param str aip_uuid: AIP UUID to delete files for
        """
        self._delete_by_field(self.aip_files_index, ES_FIELD_AIPUUID, aip_uuid)

    def mark_aip_for_deletion(self, aip_uuid: str, refresh: bool = False) -> None:
        """Mark AIP for deletion in the Elasticsearch index.

        :param str aip_uuid: AIP UUID to mark for deletion
        :param bool refresh: Whether to refresh affected indexes immediately
        """
        self._update_aip_pending_deletion(aip_uuid, True, refresh=refresh)

    def unmark_aip_for_deletion(self, aip_uuid: str, refresh: bool = False) -> None:
        """Unmark AIP for deletion in the Elasticsearch index.

        :param str aip_uuid: AIP UUID to unmark for deletion
        :param bool refresh: Whether to refresh affected indexes immediately
        """
        self._update_aip_pending_deletion(aip_uuid, False, refresh=refresh)

    def ensure_indexes_exist(self, indexes: list[str]) -> None:
        """Ensure the specified search indexes exist.

        Creates any missing indexes with their appropriate settings and mappings.

        :param list[str] indexes: List of index names to ensure exist
        """
        if not indexes or self.client.indices.exists(index=indexes):
            return

        valid_indexes = {
            self.aips_index,
            self.aip_files_index,
        }

        for index in indexes:
            if index not in valid_indexes:
                continue

            self._create_index(index)

    def _create_index(self, index: str) -> None:
        """Create an Elasticsearch index with settings and mappings.

        :param str index: Name of the index to create
        """
        settings = self._get_index_settings_for_index(index)
        mappings = self._get_index_mappings_for_index(index)

        try:
            self.client.indices.create(
                index=index,
                body={"settings": settings, "mappings": mappings},
            )
        except RequestError as e:
            if not e.error == "resource_already_exists_exception":
                raise

    def _get_index_settings_for_index(self, index: str) -> dict[str, Any]:
        """Get the settings for a specific index.

        :param str index: Name of the index
        :return: Dictionary containing settings
        """
        return self._get_index_settings()

    def _get_index_mappings_for_index(self, index: str) -> dict[str, Any]:
        """Get the mapping properties for a specific index.

        :param str index: Name of the index
        :return: Dictionary containing mapping properties for the index
        """
        if index == self.aips_index:
            return self._get_aips_index_mappings()
        elif index == self.aip_files_index:
            return self._get_aipfiles_index_mappings()
        else:
            raise ValueError(f"Unknown index: {index}")

    def _get_index_settings(self) -> dict[str, Any]:
        """Return common settings applied to all Elasticsearch indexes."""
        return {
            "index": {
                "mapping": {
                    "total_fields": {"limit": TOTAL_FIELDS_LIMIT},
                    "depth": {"limit": DEPTH_LIMIT},
                },
                "analysis": {
                    "analyzer": {
                        "file_path_and_name": {
                            "tokenizer": "char_tokenizer",
                            "filter": ["lowercase"],
                        }
                    },
                    "tokenizer": {
                        "char_tokenizer": {
                            "type": "char_group",
                            "tokenize_on_chars": ["-", "_", ".", "/", "\\"],
                        }
                    },
                },
            }
        }

    def _get_aips_index_mappings(self) -> dict[str, Any]:
        """Return field mappings for the AIPs index."""
        return {
            "date_detection": False,
            "properties": {
                ES_FIELD_NAME: {
                    "type": "text",
                    "fields": {"raw": {"type": "keyword"}},
                    "analyzer": "file_path_and_name",
                },
                ES_FIELD_SIZE: {"type": "double"},
                ES_FIELD_UUID: {"type": "keyword"},
                ES_FIELD_ACCESSION_IDS: {"type": "keyword"},
                ES_FIELD_STATUS: {"type": "keyword"},
                ES_FIELD_FILECOUNT: {"type": "integer"},
                ES_FIELD_LOCATION: {"type": "keyword"},
            },
        }

    def _get_aipfiles_index_mappings(self) -> dict[str, Any]:
        """Return field mappings for the AIP files index."""
        return {
            "date_detection": False,
            "properties": {
                "sipName": {
                    "type": "text",
                    "fields": {"raw": {"type": "keyword"}},
                    "analyzer": "file_path_and_name",
                },
                ES_FIELD_AIPUUID: {"type": "keyword"},
                ES_FIELD_FILEUUID: {"type": "keyword"},
                "isPartOf": {"type": "keyword"},
                ES_FIELD_AICID: {"type": "keyword"},
                "indexedAt": {"type": "double"},
                "filePath": {
                    "type": "text",
                    "fields": {"raw": {"type": "keyword"}},
                    "analyzer": "file_path_and_name",
                },
                "fileExtension": {"type": "text"},
                "origin": {"type": "text"},
                "identifiers": {"type": "keyword"},
                "accessionid": {"type": "keyword"},
                ES_FIELD_STATUS: {"type": "keyword"},
            },
        }

    def delete_indexes(self, indexes: list[str]) -> None:
        """Delete the specified search indexes.

        :param list[str] indexes: List of index names to delete
        """
        if not indexes:
            return

        try:
            self.client.indices.delete(index=indexes)
        except NotFoundError:
            pass

    def update_index_mappings(self, index: str, mappings: dict[str, Any]) -> None:
        """Update mappings for a specific index.

        :param str index: Index name to update
        :param dict[str, Any] mappings: Mapping properties to apply
        """
        self.client.indices.put_mapping(index=index, body=mappings)

    def reindex_from_remote(
        self, remote_config: dict[str, Any], index_mappings: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Reindex data from a remote Elasticsearch cluster.

        :param dict[str, Any] remote_config: Remote cluster configuration
        :param list[dict[str, str]] index_mappings: Source to destination index mappings
        :return: Results of reindex operations
        """
        results: dict[str, list[dict[str, Any]]] = {"successful": [], "failed": []}

        for mapping in index_mappings:
            body = {
                "source": {
                    "remote": remote_config,
                    "index": mapping["source_index"],
                    "size": remote_config.get("size", 10),
                },
                "dest": {"index": mapping["dest_index"]},
            }

            try:
                response = self.client.reindex(body=body)
                results["successful"].append(
                    {
                        "index": mapping["dest_index"],
                        "response": response,
                    }
                )
            except Exception as exc:
                results["failed"].append(
                    {
                        "index": mapping["dest_index"],
                        "error": str(exc),
                    }
                )

        return results

    def update_all_documents(self, index: str) -> dict[str, Any]:
        """Update all documents in an index using update_by_query.

        Useful for populating new mapping fields after schema changes.

        :param str index: Index name to update
        :return: Update operation results
        """
        return dict(self.client.update_by_query(index=index))

    def _search_by_term(
        self,
        index: str,
        field: str,
        value: str,
        fields: Optional[list[str]] = None,
        size: Optional[int] = None,
    ) -> dict[str, Any]:
        """Execute a term search query.

        :param str index: Elasticsearch index to search
        :param str field: Field name to query on
        :param str value: Value to search for
        :param Optional[list[str]] fields: Optional list of fields to return
        :param Optional[int] size: Optional size limit for results
        :return: Raw search results from Elasticsearch
        """
        query = {"query": {"term": {field: value}}}
        return self._search_index(index, query, size=size, fields=fields)

    def _get_single_document_by_field(
        self,
        index: str,
        field: str,
        value: str,
        fields: Optional[list[str]] = None,
        not_found_exception_class: type[SearchServiceError] = SearchServiceError,
        error_context: str = "document",
    ) -> dict[str, Any]:
        """Get a single document by field value with error handling.

        :param str index: Elasticsearch index to search
        :param str field: Field name to query on
        :param str value: Value to search for
        :param Optional[list[str]] fields: Optional list of fields to return
        :param type[SearchServiceError] not_found_exception_class: Exception class to raise when not found
        :param str error_context: Context description for error messages
        :return: Document data
        :raises SearchServiceError: When no document is found or multiple documents are found
        """
        results = self._search_by_term(index, field, value, fields=fields)

        count = results["hits"]["total"]["value"]
        if count == 0:
            raise not_found_exception_class(
                f"No {error_context} found with {field} {value}"
            )
        if count > 1:
            raise MultipleResultsError(
                f"{count} {error_context}s found with {field} {value}; unable to fetch a single result"
            )

        return dict(results["hits"]["hits"][0])

    def get_aip_data(
        self, uuid: str, fields: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Get AIP data by UUID.

        :param str uuid: AIP UUID to retrieve
        :param Optional[list[str]] fields: Optional list of fields to return
        :return: AIP document data
        :raises AIPNotFoundError: When no AIP is found with the given UUID
        :raises MultipleResultsError: When multiple AIPs are found with the same UUID
        """
        return self._get_single_document_by_field(
            index=self.aips_index,
            field=ES_FIELD_UUID,
            value=uuid,
            fields=fields,
            not_found_exception_class=AIPNotFoundError,
            error_context="AIP",
        )

    def get_aipfile_data(
        self, uuid: str, fields: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Get AIP file data by file UUID.

        :param str uuid: File UUID to retrieve
        :param Optional[list[str]] fields: Optional list of fields to return
        :return: AIP file document data
        :raises AIPFileNotFoundError: When no file is found with the given UUID
        :raises MultipleResultsError: When multiple files are found with the same UUID
        """
        return self._get_single_document_by_field(
            index=self.aip_files_index,
            field=ES_FIELD_FILEUUID,
            value=uuid,
            fields=fields,
            not_found_exception_class=AIPFileNotFoundError,
            error_context="AIP file",
        )

    def get_aipfile_by_document_id(self, document_id: str) -> dict[str, Any]:
        """Get AIP file document by Elasticsearch document ID.

        :param str document_id: Elasticsearch document ID
        :return: Complete document data including metadata
        :raises AIPFileNotFoundError: When document is not found
        """
        try:
            return dict(self.client.get(index=self.aip_files_index, id=document_id))
        except Exception as e:
            raise AIPFileNotFoundError(
                f"AIP file document {document_id} not found: {e}"
            )

    def _search_index(
        self,
        index: str,
        query: dict[str, Any],
        size: Optional[int] = None,
        from_: Optional[int] = None,
        sort: Optional[SortSpec] = None,
        fields: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Search an index with optional parameters.

        :param str index: Elasticsearch index name to search
        :param dict[str, Any] query: Elasticsearch query body
        :param Optional[int] size: Optional size limit for results
        :param Optional[int] from_: Optional start index for pagination
        :param Optional[SortSpec] sort: Optional sort specification with field and order
        :param Optional[list[str]] fields: Optional list of fields to return
        :return: Raw search results from Elasticsearch
        """
        search_params: dict[str, Any] = {"index": index}

        # Treat the provided query dict as the full search body and map supported keys
        # onto the typed client parameters so we avoid combining `body` with other args.
        for key, value in query.items():
            if key == "from":
                search_params["from_"] = value
            else:
                search_params[key] = value

        # Explicit parameters take precedence over values supplied in the query dict.
        if size is not None:
            search_params["size"] = size
        if from_ is not None:
            search_params["from_"] = from_
        if sort is not None:
            search_params["sort"] = [{sort.field: {"order": sort.order}}]
        if fields is not None:
            search_params["_source"] = fields

        return dict(self.client.search(**search_params))

    def search_aips(
        self,
        query: dict[str, Any],
        size: Optional[int] = None,
        from_: Optional[int] = None,
        sort: Optional[SortSpec] = None,
        fields: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Search AIPs with optional parameters.

        :param dict[str, Any] query: Elasticsearch query body
        :param Optional[int] size: Optional size limit for results, defaults to max_query_size
        :param Optional[int] from_: Optional start index for pagination
        :param Optional[SortSpec] sort: Optional sort specification with field and order
        :param Optional[list[str]] fields: Optional list of fields to return
        :return: Raw search results from Elasticsearch
        """
        if size is None:
            size = self.max_query_size
        return self._search_index(self.aips_index, query, size, from_, sort, fields)

    def search_aip_files(
        self,
        query: dict[str, Any],
        size: Optional[int] = None,
        from_: Optional[int] = None,
        sort: Optional[SortSpec] = None,
        fields: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Search AIP files with optional parameters.

        :param dict[str, Any] query: Elasticsearch query body
        :param Optional[int] size: Optional size limit for results, defaults to max_query_size
        :param Optional[int] from_: Optional start index for pagination
        :param Optional[SortSpec] sort: Optional sort specification with field and order
        :param Optional[list[str]] fields: Optional list of fields to return
        :return: Raw search results from Elasticsearch
        """
        if size is None:
            size = self.max_query_size
        return self._search_index(
            self.aip_files_index, query, size, from_, sort, fields
        )

    def count_aip_files(self, query: dict[str, Any]) -> int:
        """Count AIP files matching the given query.

        :param dict[str, Any] query: Elasticsearch query body
        :return: Number of AIP files matching the query
        """
        try:
            result = self.client.count(index=self.aip_files_index, body=query)
            return int(result["count"])
        except Exception:
            return 0

    def get_cluster_info(self) -> SearchBackendInfo:
        """Get Elasticsearch cluster information.

        :return: SearchBackendInfo containing Elasticsearch cluster information
        :raises SearchServiceError: When unable to connect to Elasticsearch
        """
        try:
            es_info = dict(self.client.info())
            return SearchBackendInfo(
                name=es_info["name"],
                version=es_info["version"]["number"],
                cluster_name=es_info.get("cluster_name"),
                raw_info=es_info,
            )
        except Exception as err:
            raise SearchServiceError(f"Unable to connect to Elasticsearch: {err}")

    def _wait_for_cluster_yellow_status(
        self, wait_between_tries: int = 10, max_tries: int = 10
    ) -> None:
        """Wait for Elasticsearch cluster to reach yellow status.

        :param int wait_between_tries: Seconds to wait between health checks
        :param int max_tries: Maximum number of tries before giving up
        """
        health: dict[str, Any] = {}
        health["status"] = None
        tries = 0

        while (
            health["status"] != "yellow"
            and health["status"] != "green"
            and tries < max_tries
        ):
            tries = tries + 1

            try:
                health = self.client.cluster.health()
            except Exception:
                health["status"] = None

            if health["status"] != "yellow" and health["status"] != "green":
                time.sleep(wait_between_tries)

    def _try_to_index(
        self,
        data: dict[str, Any],
        index: str,
        wait_between_tries: int = 10,
        max_tries: int = 10,
        printfn: Any = print,
    ) -> None:
        """Try to index data in Elasticsearch with retry logic.

        :param dict[str, Any] data: Data to index
        :param str index: Index name to store the document
        :param int wait_between_tries: Seconds to wait between retries
        :param int max_tries: Maximum number of attempts
        :param printfn: Print function for output messages
        """
        exception = None
        if max_tries < 1:
            raise ValueError("max_tries must be 1 or greater")
        for _ in range(0, max_tries):
            try:
                self.client.index(index=index, body=data)
                return
            except Exception as e:
                exception = e
                printfn("ERROR: error trying to index.")
                printfn(e)
                time.sleep(wait_between_tries)

        if exception:
            raise exception

    def _bulk_index(
        self, generator: Generator[dict[str, Any], None, None], chunk_size: int = 50
    ) -> tuple[int, list[dict[str, Any]]]:
        """Perform bulk indexing operation using elasticsearch helpers.

        :param Generator[dict[str, Any], None, None] generator: Generator yielding documents to index
        :param int chunk_size: Number of documents to process in each batch
        :return: Tuple of (number of documents indexed, list of failed documents)
        """
        success, errors = bulk(
            self.client, generator, chunk_size=chunk_size, stats_only=False
        )
        return success, errors

    def _index_aip_files(
        self,
        uuid: str,
        name: str,
        am_version: str,
        indexed_at: str,
        identifiers: list[dict[str, str]],
        dashboard_uuid: str = "",
        parser: Any = None,
    ) -> tuple[int, list[str]]:
        """Index AIP files from AIP with UUID `uuid`.

        :param str uuid: UUID of the AIP being indexed
        :param str name: AIP name
        :param str am_version: Archivematica version
        :param str indexed_at: Timestamp when indexing occurred
        :param list[dict[str, str]] identifiers: Additional identifiers
        :param str dashboard_uuid: Pipeline UUID
        :param Any parser: AIPMETSParser instance
        :return: Tuple of (number of files indexed, list of accession numbers)
        """
        accession_ids = set()

        def _generator() -> Generator[dict[str, Any], None, None]:
            for file_data, file_accession_ids in parser.files():
                file_data.update(
                    {
                        "archivematicaVersion": am_version,
                        "AIPUUID": uuid,
                        "sipName": name,
                        "indexedAt": indexed_at,
                        "isPartOf": parser.is_part_of,
                        ES_FIELD_AICID: parser.aic_identifier,
                        "origin": dashboard_uuid,
                        ES_FIELD_STATUS: STATUS_UPLOADED,
                    }
                )
                file_data["transferMetadata"] = (
                    parser.aip_metadata + file_data["transferMetadata"]
                )
                file_data["identifiers"] = identifiers + file_data["identifiers"]
                accession_ids.update(file_accession_ids)

                yield {
                    "_op_type": "index",
                    "_index": self.aip_files_index,
                    "_source": file_data,
                }

        file_count, _ = self._bulk_index(_generator(), chunk_size=50)
        return file_count, list(accession_ids)

    def index_aip(
        self,
        uuid: str,
        aip_stored_path: str,
        parser: Any,
        name: str,
        aip_size: int,
        am_version: str,
        indexed_at: str,
        identifiers: list[dict[str, str]],
        aips_in_aic: Optional[int] = None,
        encrypted: bool = False,
        location: str = "",
        dashboard_uuid: str = "",
    ) -> int:
        """Index AIP and AIP files.

        :param str uuid: UUID of the AIP to index
        :param str aip_stored_path: Path on disk where the AIP is located
        :param Any parser: AIPMETSParser instance
        :param str name: AIP name
        :param int aip_size: AIP size in bytes
        :param str am_version: Archivematica version
        :param str indexed_at: Timestamp when indexing occurred
        :param list[dict[str, str]] identifiers: Additional identifiers
        :param Optional[int] aips_in_aic: Number of AIPs stored in AIC
        :param bool encrypted: Whether AIP is encrypted
        :param str location: AIP location
        :param str dashboard_uuid: Pipeline UUID
        :return: 0 if succeeded, 1 otherwise
        """
        try:
            files_indexed, accession_ids = self._index_aip_files(
                uuid=uuid,
                name=name,
                am_version=am_version,
                indexed_at=indexed_at,
                identifiers=identifiers,
                dashboard_uuid=dashboard_uuid,
                parser=parser,
            )

            print(f"Files indexed: {files_indexed}")
            print("Indexing AIP ...")

            aip_data = {
                ES_FIELD_UUID: uuid,
                ES_FIELD_NAME: name,
                "filePath": aip_stored_path,
                ES_FIELD_SIZE: int(aip_size) / (1024 * 1024),
                ES_FIELD_FILECOUNT: files_indexed,
                "origin": dashboard_uuid,
                ES_FIELD_CREATED: parser.created,
                ES_FIELD_AICID: parser.aic_identifier,
                "isPartOf": parser.is_part_of,
                ES_FIELD_AICCOUNT: aips_in_aic,
                "identifiers": identifiers,
                "transferMetadata": parser.aip_metadata,
                ES_FIELD_ENCRYPTED: encrypted,
                ES_FIELD_ACCESSION_IDS: accession_ids,
                ES_FIELD_STATUS: STATUS_UPLOADED,
                ES_FIELD_LOCATION: location,
            }

            self._wait_for_cluster_yellow_status()
            self._try_to_index(aip_data, self.aips_index)

            return 0
        except Exception as e:
            logger.error(f"Failed to index AIP {uuid}: {e}")
            return 1


def _create_elasticsearch_client(
    hosts: Union[str, list[str], tuple[str, ...]], timeout: int = DEFAULT_TIMEOUT
) -> Elasticsearch:
    """Create configured Elasticsearch client.

    :param hosts: Elasticsearch hosts (string, list or tuple)
    :param timeout: Connection timeout in seconds
    :return: Configured Elasticsearch client
    """
    return Elasticsearch(**{"hosts": hosts, "request_timeout": timeout})


def setup_search_service(
    hosts: Union[str, list[str], tuple[str, ...]],
    timeout: int = DEFAULT_TIMEOUT,
    enabled: tuple[str, ...] = (AIPS_INDEX,),
) -> SearchService:
    """Initialize and return the search service with Elasticsearch client.

    Also creates the required indexes if they don't exist based on the enabled parameter.

    :param hosts: Elasticsearch hosts (string, list or tuple)
    :param timeout: Connection timeout in seconds
    :param enabled: Enabled indexes tuple
    :return: Configured SearchService instance
    """
    global _search_service_instance

    client = _create_elasticsearch_client(hosts, timeout)
    _search_service_instance = ElasticsearchSearchService(client)

    indexes = []
    if AIPS_INDEX in enabled:
        indexes.extend([AIPS_INDEX, AIP_FILES_INDEX])

    if indexes:
        _search_service_instance.ensure_indexes_exist(indexes)
    else:
        logger.warning("Setting up the search service without enabled indexes.")

    return _search_service_instance


def setup_search_service_from_conf(settings: Any) -> SearchService:
    """Initialize search service using Django settings.

    :param settings: Django settings object
    :return: Configured SearchService instance
    """
    return setup_search_service(
        settings.ELASTICSEARCH_SERVER,
        settings.ELASTICSEARCH_TIMEOUT,
        settings.SEARCH_ENABLED,
    )


def get_search_service_instance() -> Optional["SearchService"]:
    """Get the current search service instance if initialized.

    :return: SearchService instance or None if not initialized
    """
    return _search_service_instance
