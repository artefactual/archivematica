"""
PAR related gubbins
"""

def to_file_format(format_version):
    return {
        'id': format_version.pronom_id,
        'localLastModifiedDate': str(format_version.lastmodified),
        'version': format_version.version,
        'name': format_version.slug,
        'description': format_version.description
        }
