#!/usr/bin/python -OO
import hashlib

#Borrowed from http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python
def md5_for_file(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(2**10 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


#Modification of above borrowed function
def sha_for_file(filename):
    sha = hashlib.sha256()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(2**10 * sha.block_size), b''):
            sha.update(chunk)
    return sha.hexdigest()


if __name__ == '__main__':
    import sys
    theFile = sys.argv[1]
    print "md5:", md5_for_file(theFile)
    print "sha256:", sha_for_file(theFile)
