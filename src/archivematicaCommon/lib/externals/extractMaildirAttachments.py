#!/usr/bin/python -OO
# vim:fileencoding=utf8

#Author Ian Lewis
#http://www.ianlewis.org/en/parsing-email-attachments-python


# Modification
# Author Joseph Perry
# date Aug 10 2010

import email
import sys
# According to the original blogpost, StringIO was chosen over cStringIO because PIL
# required native Python types.
# TODO: Look at using cStringIO instead, as it's faster, and we're not using PIL
from StringIO import StringIO
import uuid

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
from sharedVariablesAcrossModules import sharedVariablesAcrossModules
sharedVariablesAcrossModules.errorCounter = 0


def parse_attachment(message_part, attachments=None):
    """ Extract the attachment and metadata about it from the message.

    Returns the content, content type, size, and create/modification/read dates
    for the attachment.
    """
    params = message_part.get_params(None, 'Content-Disposition')
    if params:
        # If a 'part' has a Content-Disposition, we assume it is an attachment
        try:
            params = dict(params)
            print '\tContent-Disposition (for following email)', params
            if 'attachment' in params:
                # Not sure what's going on here
                # Why get payload with decode, then try again and reparse?
                # See details at
                # http://docs.python.org/2/library/email.message.html#email.message.Message.get_payload
                file_data = message_part.get_payload(decode=True)
                if not file_data:
                    payload = message_part.get_payload()
                    if isinstance(payload, list):
                        for msgobj in payload:
                            # TODO not sure this actually does anything
                            parse2(msgobj, attachments)
                        return None
                    print >>sys.stderr, message_part.get_payload()
                    print >>sys.stderr, message_part.get_content_charset()

                attachment = StringIO(file_data)
                attachment.content_type = message_part.get_content_type()
                attachment.size = params.get('size', len(file_data))
                attachment.create_date = params.get('create-date')
                attachment.mod_date = params.get('modification-date')
                attachment.read_date = params.get('read-date')
                # TODO convert dates to datetime
                
                filename = message_part.get_filename(None)
                if filename:
                    # Filenames may be encoded with =?encoding?...
                    # If so, convert to unicode
                    name, encoding = email.header.decode_header(filename)[0]
                    if encoding:
                        print '\t{filename} encoded with {encoding}, converting to unicode'.format(filename=filename, encoding=encoding)
                        filename = name.decode(encoding)
                else:  # filename not in Content-Disposition
                    print >>sys.stderr, """Warning, no filename found in: [{%s}%s] Content-Disposition: %s or Content-Type""" % (sharedVariablesAcrossModules.sourceFileUUID, sharedVariablesAcrossModules.sourceFilePath, params)
                    filename = unicode(uuid.uuid4())
                    print >>sys.stderr, "Attempting extraction with random filename: %s" % (filename)
                # Remove newlines from filename because that breaks everything
                filename = filename.replace("\r", "").replace("\n", "")

                attachment.name = filename
                return attachment
                            
        except Exception as inst:
            print >>sys.stderr, type(inst)
            print >>sys.stderr, inst.args
            print >>sys.stderr, "Error parsing: file: {%s}%s" % (sharedVariablesAcrossModules.sourceFileUUID, sharedVariablesAcrossModules.sourceFilePath)
            print >>sys.stderr, "Error parsing: Content-Disposition: ", params
            print >>sys.stderr
            sharedVariablesAcrossModules.errorCounter += 1
    return None

def parse(content):
    """
    Eメールのコンテンツを受け取りparse,encodeして返す
    """
    p = email.Parser.Parser()
    msgobj = p.parse(content)
    attachments = []
    return parse2(msgobj, attachments)

def parse2(msgobj, attachments=None):    
    if msgobj['Subject'] is not None:
        decodefrag = email.header.decode_header(msgobj['Subject'])
        subj_fragments = []
        for s, enc in decodefrag:
            if enc:
                s = s.decode(enc)
            subj_fragments.append(s)
        subject = ''.join(subj_fragments)
    else:
        subject = None
    
    if attachments == None:
        attachments = []
    for part in msgobj.walk():
        attachment = parse_attachment(part, attachments=attachments)
        if attachment:
            attachments.append(attachment)
    return {
        'subject' : subject,
        'from' : email.utils.parseaddr(msgobj.get('From'))[1], # 名前は除いてメールアドレスのみ抽出
        'to' : email.utils.parseaddr(msgobj.get('To'))[1], # 名前は除いてメールアドレスのみ抽出
        'attachments': attachments,
        'msgobj': msgobj,
    }
                    
