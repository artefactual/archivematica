from django.http import HttpResponse
from contrib.mcp.client import MCPClient
from lxml import etree

def execute(request):
    result = ''
    if 'uuid' in request.REQUEST:
        client = MCPClient()
        uuid   = request.REQUEST.get('uuid', '')
        choice = request.REQUEST.get('choice', '')
        uid    = request.REQUEST.get('uid', '')
        result = client.execute(uuid, choice, uid)
    return HttpResponse(result, content_type='text/plain')

def list(request):
    client = MCPClient()
    jobs = etree.XML(client.list())
    response = ''
    if 0 < len(jobs):
        for job in jobs:
            response += etree.tostring(job)
    response = '<MCP>%s</MCP>' % response
    return HttpResponse(response, content_type='text/xml')
