"""
PAR related gubbins
"""

def to_par_file_format(format_version):
    return {
        'id': format_version.pronom_id,
        'localLastModifiedDate': str(format_version.lastmodified),
        'version': format_version.version,
        'name': format_version.slug,
        'description': format_version.description
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
