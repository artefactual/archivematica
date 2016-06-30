#!/bin/bash

current_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

db_name=$1
if [ -z "${db_name}" ]; then
    db_name="MCP"
fi

db_password=""
if [ -n "${2}" ]; then
    db_password="--password=${2}"
fi

db_host=$3
if [ -z "${db_host}" ]; then
    db_host="localhost"
fi

db_user=$4
if [ -z "${db_user}" ]; then
    db_user="root"
fi

db_seed=$5
if [ -n "${db_seed}" ]; then
    db_seed="/vagrant/src/archivematica/src/MCPServer/share/mysql"
    mysql --host="${db_host}" --user="${db_user}" ${db_password} --execute="DROP DATABASE ${db_name};"
    mysql --host="${db_host}" --user="${db_user}" ${db_password} --execute="CREATE DATABASE ${db_name};"
    mysql --host="${db_host}" --user="${db_user}" ${db_password} "${db_name}" < "${db_seed}"
fi

migrations=(
  mysql_dev_7464_processing_directory.sql
  mysql_dev_7478_processing_directory.sql
  mysql_dev_7603_metadata_identification.sql
  mysql_dev_7606_atk_whitespace.sql
  mysql_dev_6488_aip_reingest.sql
  mysql_dev_7137_models.sql
  mysql_dev_7424_identifiers_in_es.sql
  mysql_dev_7714_transfer_mets.sql
  mysql_dev_7690_recursive_extraction.sql
  mysql_dev_7239_contentdm.sql
  mysql_dev_8825_checksum_failure.sql
  mysql_dev_8019_dspace_at_fixes.sql
  mysql_dev_7922_index_aips.sql
  mysql_dev_8287_siegfried.sql
  mysql_dev_7321_dip_processing_xml.sql
  mysql_dev_8415_checksum.sql
  mysql_dev_8423_extract_logging.sql
  mysql_dev_4757_sounds.sql
  mysql_dev_8252_fpr_update.sql
  mysql_dev_7595_archivesspace_upload.sql
  mysql_dev_6488_aip_reingest2.sql
  mysql_dev_hierarchical_dip_upload.sql
  mysql_dev_8609_automate_matching_gui.sql
  mysql_dev_8896_checksum_algorithms.sql
  mysql_dev_9265_index_after_processing_decision.sql
  mysql_dev_8974_migrations.sql
  mysql_dev_delete_links.sql
  mysql_dev_delete_views.sql
  mysql_dev_update_args_email_report.sql
  mysql_dev_dip_storage_after_upload.sql
  mysql_dev_9647_archivesspace_inherit_notes.sql
  mysql_dev_9478_integrate_mediaarea_tools.sql
)

failed=()

for item in "${migrations[@]}"; do
    echo "Loading migration ${item}... "
    mysql --host="${db_host}" --user="${db_user}" ${db_password} "${db_name}" < "${current_dir}/${item}"
    if [ $? -ne 0 ]; then
        failed+=($item)
    fi
done

if [ "${#failed[@]}" -gt "0" ]; then
  >&2 echo "-------------------------------------"
  >&2 echo "The following migrations have failed:"
  for item in "${failed[@]}"; do
    >&2 echo " - ${item}"
  done
  >&2 echo "See more details above."
fi

touch "${current_dir}/mysql_dev.complete"
