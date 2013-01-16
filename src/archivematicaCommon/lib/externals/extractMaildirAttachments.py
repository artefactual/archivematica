#!/usr/bin/python -OO
# vim:fileencoding=utf8

#Author Ian Lewis
#http://www.ianlewis.org/en/parsing-email-attachments-python


# Modification
# Author Joseph Perry
# date Aug 10 2010
# Using rfc6266 library

from email.Header import decode_header
import email
from base64 import b64decode
import sys
from email.Parser import Parser as EmailParser
from email.utils import parseaddr
# cStringIOはダメ
from StringIO import StringIO
import uuid
import re
import rfc6266 #TODO: add notes

#http://tools.ietf.org/html/rfc2183
#http://tools.ietf.org/html/rfc6266
#http://en.wikipedia.org/wiki/MIME#Content-Disposition

import sys
sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from sharedVariablesAcrossModules import sharedVariablesAcrossModules
sharedVariablesAcrossModules.errorCounter = 0

class NotSupportedMailFormat(Exception):
    pass

def tweakContentDisposition(content_disposition):
    #filename*=utf-8''=Name -> filename*=utf-8''Name
    #content_disposition = content_disposition.replace("filename*=utf-8''=", "filename*=utf-8''Name")
    
    content_disposition = content_disposition.replace("\r", "")
    content_disposition = content_disposition.replace("\n", "")
    p = re.compile('attachment;\s*filename')
    content_disposition = p.sub('attachment; filename', content_disposition, count=1)
    return content_disposition 

#
#>>> c = "attachment; filename*=utf-8''%20Southern%20Roots%20of%20of%20Modern%20Philanthropy.pptx"
#>>> parse_headers(c)
#ContentDisposition(u'attachment', {u'filename*': LangTagged(string=u' Southern Roots of of Modern Philanthropy.pptx', langtag=None)}, None)


def parse_attachment(message_part, attachments=None):
    content_disposition = message_part.get("Content-Disposition", None)
    if content_disposition:
        try:
            try:
                content_disposition = tweakContentDisposition(content_disposition)
                cd = rfc6266.parse_headers(content_disposition, relaxed=True)
            except Exception as inst:
                print type(inst)
                print inst.args
                print >>sys.stderr, "Error parsing file: {%s}%s" % (sharedVariablesAcrossModules.sourceFileUUID, sharedVariablesAcrossModules.sourceFilePath)
                print >>sys.stderr, "Error parsing the content_disposition:", content_disposition
                if "attachment" in content_disposition.lower() and "filename" in content_disposition.lower():  
                    try:
                        filename = uuid.uuid4.__str__()
                        print >>sys.stderr, "Attempting extraction with random filename."
                        print >>sys.stderr
                        content_disposition = "attachment; filename=%s;" % (filename)
                        cd = parse_headers(content_disposition, relaxed=True)
                    except:
                        print >>sys.stderr, "Failed"
                        print >>sys.stderr
                        return None
                else:
                    print >>sys.stderr
                    return None
            if cd.disposition.lower() == "attachment":
                filename = ""
                if cd.assocs.has_key("filename"):
                    filename = cd.assocs["filename"]
                elif cd.assocs.has_key("filename*"):
                    filename = cd.assocs["filename*"]
                else:
                    print >>sys.stderr, """Warning, no filename found in: [{%s}%s]%s""" % (sharedVariablesAcrossModules.sourceFileUUID, sharedVariablesAcrossModules.sourceFilePath, content_disposition)
                    filename = uuid.uuid4.__str__()
                    print >>sys.stderr, "Attempting extraction with random filename: %s" % (filename)
                    print >>sys.stderr
                if isinstance(filename, rfc6266.LangTagged):
                    filename = filename.string
                else:
                    print >>sys.stderr, type(fileName)
                file_data = message_part.get_payload(decode=True)
                if not file_data:
                    payload = message_part.get_payload()
                    if isinstance(payload, list):
                        for msgobj in payload:
                            parse2(msgobj, attachments)
                        return None
                    print >>sys.stderr, message_part.get_payload()
                    print >>sys.stderr, message_part.get_content_charset()
                attachment = StringIO(file_data)
                attachment.content_type = message_part.get_content_type()
                attachment.size = len(file_data)
                attachment.name = filename
                attachment.create_date = None
                attachment.mod_date = None
                attachment.read_date = None 
                
                for name, value in cd.assocs.iteritems():
                    if name == "create-date":
                        attachment.create_date = value  #TODO: datetime
                    elif name == "modification-date":
                        attachment.mod_date = value #TODO: datetime
                    elif name == "read-date":
                        attachment.read_date = value #TODO: datetime
                
                return attachment
                            
        except:
            print >>sys.stderr, "Error parsing file: {%s}%s" % (sharedVariablesAcrossModules.sourceFileUUID, sharedVariablesAcrossModules.sourceFilePath)
            print >>sys.stderr, "Error parsing:", filename
            print >>sys.stderr
            sharedVariablesAcrossModules.errorCounter += 1
    return None

def parse(content):
    """
    Eメールのコンテンツを受け取りparse,encodeして返す
    """
    p = EmailParser()
    msgobj = p.parse(content)
    attachments = []
    return parse2(msgobj, attachments)

def parse2(msgobj, attachments=None):    
    if msgobj['Subject'] is not None:
        decodefrag = decode_header(msgobj['Subject'])
        subj_fragments = []
        for s , enc in decodefrag:
            if enc:
                s = s.decode(enc)
            subj_fragments.append(s)
        subject = ''.join(subj_fragments)
    else:
        subject = None
    
    if attachments == None:
        attachments = []
    body = None
    html = None
    for part in msgobj.walk():
        attachment = parse_attachment(part, attachments=attachments)
        if attachment:
            attachments.append(attachment)
        disabledBodyAndHTMLParsingCode = """
        elif part.get_content_type() == "text/plain":
            if body is None:
                body = ""
            payload = part.get_payload()
            encoding = part.get_content_charset()
            if encoding:
                encoding = encoding.replace("windows-874", "cp874")
                payload = payload.decode(encoding, 'replace')
            body += payload 
        elif part.get_content_type() == "text/html":
            if html is None:
                html = ""
            payload = part.get_payload()
            encoding = part.get_content_charset()
            if encoding:
                encoding = encoding.replace("windows-874", "cp874")
                payload = payload.decode(encoding, 'replace')
            html += payload
        """
    return {
        'subject' : subject,
        'body' : body,
        'html' : html,
        'from' : parseaddr(msgobj.get('From'))[1], # 名前は除いてメールアドレスのみ抽出
        'to' : parseaddr(msgobj.get('To'))[1], # 名前は除いてメールアドレスのみ抽出
        'attachments': attachments,
        'msgobj': msgobj,
    }
                    
