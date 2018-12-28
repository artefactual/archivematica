#!/bin/bash

###############################################################################
# TODO:
#
# Q. Do we need the log file output?
# Q. Do we want to include SHA512 because we can? Blake2?
# Q, Do we want additional failure states? FAIL, INVALID?
#
# Remove: archivematicaCheckMD5NoGUI.sh script
#
# dateArgs previously used for log file output....
# dateArgs="-u +%Y%m%dT%H%M%SZ"  # 20170605T220452Z (UTC ISO8601)
#
# Rename: script, and client module
# Merge: After i18n work so that we don't have any additional migrations.
#
# Create: new mcp-client base image for Docker
#
# Delete: this TODO
###############################################################################

# Script to run the various coreutils checksum utilities suite. Commands
# include sha1sum, sha256sum etc. Easily extensible to the other algorithms in
# the same suite, for example, b2sum for Blake2 hash comparison.
#
# The script can be run standalone outside of Archivematica using a transfer
# style layout e.g.
#
#       transfer/
#       ├── metadata
#       │   ├── checksum.md5
#       │   ├── checksum.sha1
#       │   ├── checksum.sha256
#       │   └── checksum.sha512
#       └── objects
#           ├── file1.dat
#           ├── file1.dat
#           ├── file3.dat
#           └── file4.dat
#
# And the following commands:
#
# ./{script_name}.sh "absolute path to trnasfer" {date, e.g. 20170605T220452Z}\
#       {uuid} {uuid}
#
# And the output will be send to stdout and stderr.
#
# For debugging users are recommended to use the `set -eux` flags following the
# bash shebang. `set -u` is used by default.
#
# Dependencies (coreutils (sha1sum, sha256sum, head, etc.); ack)

set -u

# Variables provided on execution by Archivematica.
target="$1";
date="$2";
eventID="$3";
transferUUID="$4";

# Cumulative exit_code variable. Assumption being that we won't simply exit if
# there is a comparison issue. We'll attempt to run a comparison for each
# hash file a user provides. If three files have errors, exit_code will be '3'.
# If no files have errors, the exit code will be '0'.
exit_code=0;

metadata_folder="${target}metadata/";
objects_folder="${target}objects";

# TOOLMAP for our hash files and command variables. Can be easily extended
# for all algorithms provided with coreutils: https://perma.cc/BC92-PUX5
declare -A TOOLMAP;
TOOLMAP["${metadata_folder}checksum.md5"]="md5sum";
TOOLMAP["${metadata_folder}checksum.sha1"]="sha1sum";
TOOLMAP["${metadata_folder}checksum.sha256"]="sha256sum";
TOOLMAP["${metadata_folder}checksum.sha512"]="sha512sum";

echo "Transfer metadata folder:" "${metadata_folder}";
echo "Transfer objects folder:" "${objects_folder}";

# Store current working directory to reset at the end of the script and then
# change to the transfer directory.
tmp_pwd=$(pwd);
cd "${target}";

# Count the number of lines in the given hash file and the number of objects
# in the objects/ folder.
#
# ARG1 ($1): Checksum file
# ARG2 ARG ($2): Objects folder
#
# Return: True if the object count and checksum line count match.
#         False if there is a discrepancy.
#
function count_and_compare_lines()
{
    local checksum_lines=$(cat "${1}" | wc -l);
    local file_count=$(find "${2}" -type f | wc -l);
    if [ "${checksum_lines}" -eq "${file_count}" ];
    then
        echo true;
    else
        msg="${3}"": Comparison failed with %d checksum lines and %d transfer files\n";
        printf "${msg}" \
            "${checksum_lines}" "${file_count}" >&2;
        echo false;
    fi
}

# Retrieve the file extension to prettify the output of the script. If the
# second argument passed to the function is false, then don't output the
# extension, output the filename on its own (minus its path structure).
#
# ARG1 ($1): File path
# ARG2 ($2): true for ext, false for filename e.g. checksum.sha256
#
# Return: The file extension retrieved from the checksum.{ext} filename.
#
function get_file_extension()
{
    local filename=$(basename -- "${1}");
    if [ "${2}" == false ];
    then
        echo "${filename}";
    else
        local extension="${filename##*.}";
        echo $extension;
    fi;
}

# Output the version information from the hash command currently being called.
# The version is the first line output from the command's --version flag.
#
# ARG1 ($1): Command name
#
# Return: First line of the --version information returned by the command.
#
function output_hashsum_version()
{
    # $(head -n 1) will close the pipe when it has read enough and the hash
    # command will inconsistently interpret this as an error state resulting
    # in: {command}: write error.
    #
    # Avoid the hash command's sensitivity to a closed pipe, or unwritable
    # source e.g. $(sha1sum --version > /dev/full) by letting it write its
    # entire output to a variable and then manipulating the variable instead.
    version=$("${1}" --version);
    echo "${version}" | head -n 1;
}

# Write out PREMIS information about the comparison happening here.
function write_premis()
{
    >&2 echo "Writing PREMIS event for:" "${transferUUID}";
    hashsum_version=$(output_hashsum_version "${1}");
    "`dirname $0`/createEventsForGroup.py" \
        --eventIdentifierUUID "${eventID}" \
        --groupUUID "${transferUUID}" \
        --groupType "transfer_id" \
        --eventType "fixity check" \
        --eventDateTime "$date" \
        --eventOutcome "${2}" \
        --eventDetail "${hashsum_version}";
    >&2 echo "PREMIS written";
}

# Retrieve an error string from a given array and output information about what
# we find to stderr.
#
# ARG1 ($1): Array: An array of strings output from the previous hash command.
# ARG2 ($2): String: String, e.g. "FAILED" to search for.
# ARG3 ($2): String: The hash algorithm currently being checked against.
#
# Return: The current globally scoped exit_code.
#
function retrieve_error()
{
    echo "${3}"":" "${1}" | >&2 ack -w "${2}";
    local err=$?;
    exit_code=$(increment_exit_code "${err}" 0);
    echo $exit_code;
}

# Increment the exit code per error found running the hash commands.
#
# ARG1 ($1): Integer, ideally an $? value
# ARG2 ($2): Integer, comparison value to increment counter if -eq true
#
# Return: The current or updated globally scoped exit_code.
#
function increment_exit_code()
{
    if [ "${1}" -eq "${2}" ];
    then
        local updated_exit_code=$(( "${exit_code}" + 1 ));
        echo "${updated_exit_code}";
    else
        echo "${exit_code}";
    fi
}

# Loop through keys and values the associative array TOOLMAP.
for K in "${!TOOLMAP[@]}";
do
    ext=$(get_file_extension "${K}" true);
    if [ -f "${K}" ];
    then
        >&2 printf "Comparing transfer checksums with the %s file\n" "${ext}";
        ret=$(count_and_compare_lines "${K}" "${objects_folder}" "${ext}");
        if [ "${ret}" == false ];
        then
            exit_code=$(increment_exit_code 0 0);
        else
            current_exit_code=$exit_code;
            # Store our multi-line hash command results in an array.
            declare out=$( "${TOOLMAP[$K]}" -c --strict "${K}" 2>&1);
            exit_code=$(retrieve_error "${out}" "FAILED" "${ext}");
            exit_code=$(retrieve_error "${out}" "improperly formatted" "${ext}");
            exit_code=$(retrieve_error "${out}" "no properly formatted" "${ext}");
            # Write 'Pass' to PREMIS. PREMIS only written to METS if this
            # script doesn't fail.
            write_premis "${TOOLMAP[$K]}" "Pass";
            if [ ! $current_exit_code -lt $exit_code ];
            then
                echo "${ext} comparison was OK";
            fi;
        fi
    else
        printf "Nothing to do for %s: File '%s' not provided \n" \
            "${ext}" $(get_file_extension "${K}" false);
    fi;
done

# Reset to the original working directory and handle script exit.
cd "${tmp_pwd}";
>&2 printf "Exiting with code: %d\n" "${exit_code}";
if [ "${exit_code}" -eq 0 ];
then
    echo "Script exiting without error. Any checksum comparisons made were OK";
fi;
exit "${exit_code}";
