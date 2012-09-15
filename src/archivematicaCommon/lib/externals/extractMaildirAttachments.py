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
from rfc6266 import parse_headers #TODO: add notes

class NotSupportedMailFormat(Exception):
    pass

def parse_attachment(message_part, attachments=None):
    content_disposition = message_part.get("Content-Disposition", None)
    if content_disposition:
        try:
            cd = parse_headers(content_disposition, relaxed=True)
            if cd.disposition.lower() == "attachment":
                if not cd.assocs.has_key("filename"):
                    #print error or warning?
                    return None
                else:
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
                    attachment.name = cd.assocs['filename']
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
            print >>sys.stderr, "content_disposition:", content_disposition
            raise
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
    return {
        'subject' : subject,
        'body' : body,
        'html' : html,
        'from' : parseaddr(msgobj.get('From'))[1], # 名前は除いてメールアドレスのみ抽出
        'to' : parseaddr(msgobj.get('To'))[1], # 名前は除いてメールアドレスのみ抽出
        'attachments': attachments,
        'msgobj': msgobj,
    }
                    
