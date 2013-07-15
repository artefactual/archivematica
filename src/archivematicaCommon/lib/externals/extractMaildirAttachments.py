#!/usr/bin/python -OO
# vim:fileencoding=utf8

#Author Ian Lewis
#http://www.ianlewis.org/en/parsing-email-attachments-python

#additional:
#http://blog.magiksys.net/parsing-email-using-python-content

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
import urllib2

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

def get_filename(part):
    """Many mail user agents send attachments with the filename in 
    the 'name' parameter of the 'content-type' header instead 
    of in the 'filename' parameter of the 'content-disposition' header.
    """
    ##http://blog.magiksys.net/parsing-email-using-python-content
    filename=part.get_param('filename', None, 'content-disposition')
    if not filename:
        filename=part.get_param('name', None) # default is 'content-type'
        
    if filename:
        # RFC 2231 must be used to encode parameters inside MIME header
        filename=email.Utils.collapse_rfc2231_value(filename).strip()

    if filename and isinstance(filename, str):
        # But a lot of MUA erroneously use RFC 2047 instead of RFC 2231
        # in fact anybody miss use RFC2047 here !!!
        filename=getmailheader(filename)
        
    if filename:
        filename = filename.replace('\r', "").replace("\n", "")
        
    return filename

def getmailheader(header_text, default="ascii"):
    """Decode header_text if needed"""
    ##http://blog.magiksys.net/parsing-email-using-python-content
    try:
        headers=email.Header.decode_header(header_text)
    except email.Errors.HeaderParseError:
        # This already append in email.base64mime.decode()
        # instead return a sanitized ascii string
        # this faile '=?UTF-8?B?15HXmdeh15jXqNeVINeY15DXpteUINeTJ9eV16jXlSDXkdeg15XXldeUINem15PXpywg15TXptei16bXldei15nXnSDXqdecINek15zXmdeZ?==?UTF-8?B?157XldeR15nXnCwg157Xldek16Ig157Xl9eV15wg15HXodeV15bXnyDXk9ec15DXnCDXldeh15gg157Xl9eR16rXldeqINep15wg15HXmdeQ?==?UTF-8?B?15zXmNeZ?='
        return header_text.encode('ascii', 'replace').decode('ascii')
    else:
        for i, (text, charset) in enumerate(headers):
            try:
                headers[i]=unicode(text, charset or default, errors='replace')
            except LookupError:
                # if the charset is unknown, force default 
                headers[i]=unicode(text, default, errors='replace')
        return u"".join(headers)


def parse_attachment(message_part, attachments=None):
    content_disposition = message_part.get("Content-Disposition", None)
    if content_disposition:
        try:
            if content_disposition:
                dispositions = content_disposition.strip().split(";")
                if content_disposition and (dispositions[0].lower() == "attachment" or dispositions[0].lower() == "inline"):
                    file_data = message_part.get_payload(decode=True)
                    attachment = StringIO(file_data)
                    attachment.content_type = message_part.get_content_type()
                    attachment.size = len(file_data)
                    attachment.name = None
                    attachment.create_date = None
                    attachment.mod_date = None
                    attachment.read_date = None
                    
                    attachment.name = get_filename(message_part)
                    for param in dispositions[1:]:
                        i = param.find("=")
                        if i == -1:
                            continue
                        name = param[:i]
                        value = param[i+1:]
                        name = name.lower()
        
                        if name == "create-date":
                            attachment.create_date = value  #TODO: datetime
                        elif name == "modification-date":
                            attachment.mod_date = value #TODO: datetime
                        elif name == "read-date":
                            attachment.read_date = value #TODO: datetime
                    return attachment                            
        except Exception as inst:
            print >>sys.stderr, type(inst)
            print >>sys.stderr, inst.args
            print >>sys.stderr, "Error parsing file: {%s}%s" % (sharedVariablesAcrossModules.sourceFileUUID, sharedVariablesAcrossModules.sourceFilePath)
            print >>sys.stderr, "Error parsing:", dispositions
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
                    
