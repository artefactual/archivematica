from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


@dataclass
class ArchivematicaInstance:
    dashboard_url: str
    storage_service_url: str
    dashboard_username: str
    dashboard_password: str
    dashboard_api_key: str
    storage_service_username: str
    storage_service_password: str
    storage_service_api_key: str
    sample_data_root: Path
    transfer_source_root: Path
    poll_interval: float
    timeout_seconds: float


@dataclass
class TransferRun:
    transfer_type: str
    sample_transfer_path: str
    transfer_name: str
    transfer_source_path: Path
    transfer_uuid: str
    processing_config: str = "default"
    sip_uuid: str | None = None
    aip_path: Path | None = None
    extracted_aip_dir: Path | None = None
    aip_mets_location: Path | None = None
    metadata_csv_files: list[dict[str, Any]] = field(default_factory=list)
    source_metadata_files: list[dict[str, Any]] = field(default_factory=list)
    reingest_type: str | None = None
    reingest_processing_config: str | None = None
    reingest_uuid: str | None = None
    reingest_aip_path: Path | None = None
    reingest_extracted_aip_dir: Path | None = None
    reingest_aip_mets_location: Path | None = None
    reingest_metadata_csv_files: list[dict[str, Any]] = field(default_factory=list)
    reingest_source_metadata_files: list[dict[str, Any]] = field(default_factory=list)
    dip_path: Path | None = None
    extracted_dip_dir: Path | None = None
    dip_mets_location: Path | None = None
    aip_pointer_path: Path | None = None
    master_aip_uuid: str | None = None
    replica_aip_uuid: str | None = None
    master_aip_pointer_path: Path | None = None
    replica_aip_pointer_path: Path | None = None
    master_aip_download_path: Path | None = None
    replica_aip_download_path: Path | None = None


@dataclass
class ScenarioState:
    aip_search_results: list[dict[str, Any]] = field(default_factory=list)
    latest_job_details: dict[str, Any] | None = None
    remote_dir_subfolders: list[str] = field(default_factory=list)
    remote_dir_files: list[str] = field(default_factory=list)
    remote_dir_empty_subfolders: list[str] = field(default_factory=list)
    pointer_event_uuids: dict[str, str] = field(default_factory=dict)
    standard_gpg_space_uuid: str | None = None
    standard_gpg_location_uuid: str | None = None
    standard_gpg_replicator_location_uuid: str | None = None
    default_gpg_key_fingerprint: str | None = None
    default_gpg_key_id: str | None = None
    imported_gpg_key_fingerprint: str | None = None
    imported_gpg_key_id: str | None = None
    new_key_name: str | None = None
    new_key_email: str | None = None
    new_key_fingerprint: str | None = None
    new_key_id: str | None = None
    import_gpg_key_result: str | None = None
    delete_gpg_key_success: bool | None = None
    delete_gpg_key_msg: str | None = None
    aip_deletion_request_id: int | None = None
