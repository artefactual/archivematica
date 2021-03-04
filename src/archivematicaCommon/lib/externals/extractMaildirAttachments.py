# -*- coding: utf-8 -*-
# vim:fileencoding=utf8

# Author Ian Lewis
# http://www.ianlewis.org/en/parsing-email-attachments-python


# Modification
# Author Joseph Perry
# date Aug 10 2010
from __future__ import absolute_import, print_function

import email
import sys
import uuid

import six
from six import StringIO


def parse_attachment(message_part, state, attachments=None):
    """Extract the attachment and metadata about it from the message.

    Returns the content, content type, size, and create/modification/read dates
    for the attachment.
    """
    params = message_part.get_params(None, "Content-Disposition")
    if params:
        # If a 'part' has a Content-Disposition, we assume it is an attachment
        try:
            params = dict(params)
            print("\tContent-Disposition (for following email)", params)
            if "attachment" in params:
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
                            parse2(msgobj, state, attachments)
                        return None
                    print(message_part.get_payload(), file=sys.stderr)
                    print(message_part.get_content_charset(), file=sys.stderr)

                attachment = StringIO(file_data)
                attachment.content_type = message_part.get_content_type()
                attachment.size = params.get("size", len(file_data))
                attachment.create_date = params.get("create-date")
                attachment.mod_date = params.get("modification-date")
                attachment.read_date = params.get("read-date")
                # TODO convert dates to datetime

                filename = message_part.get_filename(None)
                if filename:
                    # Filenames may be encoded with =?encoding?...
                    # If so, convert to unicode
                    name, encoding = email.header.decode_header(filename)[0]
                    if encoding:
                        print(
                            "\t{filename} encoded with {encoding}, converting to unicode".format(
                                filename=filename, encoding=encoding
                            )
                        )
                        filename = name.decode(encoding)
                else:  # filename not in Content-Disposition
                    print(
                        """Warning, no filename found in: [{%s}%s] Content-Disposition: %s or Content-Type"""
                        % (state.sourceFileUUID, state.sourceFilePath, params),
                        file=sys.stderr,
                    )
                    filename = six.text_type(uuid.uuid4())
                    print(
                        "Attempting extraction with random filename: %s" % (filename),
                        file=sys.stderr,
                    )
                # Remove newlines from filename because that breaks everything
                filename = filename.replace("\r", "").replace("\n", "")

                attachment.name = filename
                return attachment

        except Exception as inst:
            print(type(inst), file=sys.stderr)
            print(inst.args, file=sys.stderr)
            print(
                "Error parsing: file: {%s}%s"
                % (state.sourceFileUUID, state.sourceFilePath),
                file=sys.stderr,
            )
            print("Error parsing: Content-Disposition: ", params, file=sys.stderr)
            print(file=sys.stderr)
            state.error_count += 1
    return None


def parse(content, state):
    """
    Eメールのコンテンツを受け取りparse,encodeして返す
    """
    state.error_count = 0
    p = email.Parser.Parser()
    msgobj = p.parse(content)
    attachments = []
    return parse2(msgobj, state, attachments)


def parse2(msgobj, state, attachments=None):
    if msgobj["Subject"] is not None:
        decodefrag = email.header.decode_header(msgobj["Subject"])
        subj_fragments = []
        for s, enc in decodefrag:
            if enc:
                s = s.decode(enc)
            subj_fragments.append(s)
        subject = "".join(subj_fragments)
    else:
        subject = None

    if attachments is None:
        attachments = []
    for part in msgobj.walk():
        attachment = parse_attachment(part, state, attachments=attachments)
        if attachment:
            attachments.append(attachment)
    return {
        "subject": subject,
        "from": email.utils.parseaddr(msgobj.get("From"))[1],  # 名前は除いてメールアドレスのみ抽出
        "to": email.utils.parseaddr(msgobj.get("To"))[1],  # 名前は除いてメールアドレスのみ抽出
        "attachments": attachments,
        "msgobj": msgobj,
    }
