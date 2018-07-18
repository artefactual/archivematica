"""
PAR related gubbins
"""

def parse_offset_and_limit(request):
    offset = request.GET.get('offset')
    limit = request.GET.get('limit')
    if offset != None and limit != None: limit = int(offset) + int(limit)
    return offset, limit

def to_par_file_format(format_version):
    return {
        'id': format_version.pronom_id,
        'localLastModifiedDate': str(format_version.lastmodified),
        'version': format_version.version,
        'name': format_version.slug,
        'description': format_version.description,
        'types': [format_version.format.group.description],
        }

def to_fpr_format_version(file_format):
    return {
        'version': file_format.get('version'),
        'pronom_id': file_format.get('id'),
        'description': file_format.get('description'),
        }

def to_fpr_format_group(group):
    return {
        'description': group,
        }

def to_fpr_format(format):
    return {
        'description': format,
        }

def to_par_tool(tool):
    return {
        'toolId': tool.slug,
        'toolVersion': tool.version,
        'toolName': tool.description,
        }

def to_fpr_tool(tool):
    return {
        'description': tool.get('toolName'),
        'version': tool.get('toolVersion'),
        }

def to_par_preservation_action_type(type):
    return {
        'id': type,
        'label': type,
        }

def to_par_io_file(name):
    return {
        'type': 'File',
        'name': name,
        }

def to_par_preservation_action(rule):
    return {
        'id': rule.uuid,
        'description': rule.command.description,
        'type': to_par_preservation_action_type(rule.purpose),
        'inputs': [to_par_io_file(rule.format.description)],
        'outputs': [to_par_io_file(rule.command.output_format.description)],
        'tool': to_par_tool(rule.command.tool),
        }
