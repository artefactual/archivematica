#!/usr/bin/python -OO

import os
import sys
import shutil

def main(src, dst):
    """
    Moves a file/directory to a new location, or moves two directories.

    If dst doesn't exist, acts like mv: src is moved to the same path as dst.
    If dst does exist and is a directory, the two directories are merged by
    moving src's contents into dst.
    """
    if os.path.exists(dst):
        for item in os.listdir(src):
            shutil.move(os.path.join(src, item), dst)
        shutil.rmtree(src)
    else:
        shutil.move(src, dst)

    return 0

if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2]
    try:
        sys.exit(main(src, dst))
    except Exception as e:
        sys.exit(e)
