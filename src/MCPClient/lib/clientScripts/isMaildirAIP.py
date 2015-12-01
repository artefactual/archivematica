#!/usr/bin/env python2

import os
import sys
import mailbox
exitCodes = {None: 0, 'maildir': 179}

def isMaildir(path):
    maildir = path + "objects/Maildir/"
    if not os.path.isdir(maildir):
        return False
    if not os.path.isdir(os.path.join(path, "objects", "attachments")):
        return False
    try:
        for maildirsub2 in os.listdir(maildir):
            maildirsub = os.path.join(maildir, maildirsub2)
            md = mailbox.Maildir(maildirsub, None)
    except:
        return False
    return True


if __name__ == '__main__':
    path = sys.argv[1]
    if isMaildir(path):
        exit(exitCodes['maildir'])
        
    exit(exitCodes[None])
