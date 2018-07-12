"""
PAR related gubbins
"""

import re
import shlex


PRESERVATION_ACTION_TYPES = {
    "access": "da68a236-9231-433f-b1df-ea89b12f2aa6",
    "characterization": "4db7ea62-afdb-405f-8075-df851f382b00",
    "characterize": "66ab85e6-2af1-41ac-a415-9cf1d9a4435d",
    "default_access": "9cb398cc-3706-4537-b144-ebb82ccb0fcd",
    "default_characterization": "032e97c6-29d9-4b9c-bebf-7a571f004d6a",
    "default_thumbnail": "2df2676d-74c4-4e57-a81c-2b08a5786732",
    "extract": "a73fdd1c-6865-4b13-a0d1-93a7a4355979",
    "policy_check": "4b3f414b-9c6e-4df9-8da2-67a34379fc3a",
    "preservation": "d8a67ca5-aa32-4884-9967-06a6506cb4f7",
    "thumbnail": "b6cdb762-ec50-44f2-ade5-e0583dd0897a",
    "transcription": "01deb8e8-1d50-41a2-835b-001c64b79f09",
    "validation": "a4449466-8388-424b-9d59-04a914a9c662",
}


def parse_offset_and_limit(request):
    offset = request.GET.get("offset")
    limit = request.GET.get("limit")
    if offset != None and limit != None:
        limit = int(offset) + int(limit)
    return offset, limit


def to_par_id(id, uuid):
    return {"guid": uuid, "name": id}


def to_par_file_format(format_version):
    return {
        "id": to_par_id(format_version.pronom_id, format_version.format.uuid),
        "localLastModifiedDate": str(format_version.lastmodified),
        "version": format_version.version,
        "name": format_version.slug,
        "description": format_version.description,
        "types": [format_version.format.group.description],
    }


def to_fpr_format_version(file_format):
    return {
        "version": file_format.get("version"),
        "pronom_id": file_format.get("id"),
        "description": file_format.get("description"),
    }


def to_fpr_format_group(group):
    return {"description": group}


def to_fpr_format(format):
    return {"description": format}


def to_par_tool(tool):
    return {
        "toolId": tool.uuid,
        "toolVersion": tool.version,
        "toolName": tool.description,
    }


def to_fpr_tool(tool):
    return {"description": tool.get("toolName"), "version": tool.get("toolVersion")}


def to_par_preservation_action_type(type):
    uuid = PRESERVATION_ACTION_TYPES[type]
    label_bits = type.split("_")
    label = " ".join(bit.title() for bit in label_bits)

    return {"id": to_par_id(type, uuid), "label": label}


def to_par_io_file(name):
    return {"type": {"file": {"filepath": ""}}, "name": name, "description": name}


def to_par_input_items(rule):
    file_type_re = ""

    if rule.command.script_type == "command":
        result = []
        i = 0
        for arg in shlex.split(rule.command.command):
            item = {"name": arg, "description": arg}

            if "directory" in arg.lower() or "file" in arg.lower():
                item["type"] = {"file": {"filepath": ""}}
            else:
                item["type"] = {
                    "parProperty": {
                        "class": "other",
                        "id": {"guid": "none"},
                        "type": "string",
                    }
                }

            result.append(item)

            i = i + 1

        return result
    else:
        return [to_par_io_file(rule.format.description)]


def to_par_output_items(rule):
    try:
        return [to_par_io_file(rule.command.output_format.description)]
    except AttributeError:
        return []


def to_par_preservation_action(rule):
    return {
        "id": to_par_id(rule.uuid, rule.uuid),
        "description": rule.command.description,
        "type": to_par_preservation_action_type(rule.purpose),
        "inputs": to_par_input_items(rule),
        "outputs": to_par_output_items(rule),
        "tool": to_par_tool(rule.command.tool),
    }


def to_fpr_rule(preservation_action):
    return {}
