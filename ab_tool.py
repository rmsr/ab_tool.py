#! /usr/bin/env python

"""
This code is based on the file format documentation found at

http://nelenkov.blogspot.com/2012/06/unpacking-android-backups.html

Encrypted archives are not yet handled.
"""

USAGE = """
Usage: ab_tool.py CMD FILE [ DIR ]

Packs, inspects, and unpacks Android backup files.

DIR defaults to the current directory.

Commands:
    p, pack: packs the contents of DIR into FILE
    l, list: lists out the contents of the backup
    u, unpack: extracts the contents of FILE into DIR
""".strip()

import sys
import os
import zlib
import tarfile

def do_list(arch, _):
    parser = parse_file(arch)
    def tarinfo_gen(parser):
        next = True
        while next:
            next = parser.next()
            if next:
                yield next

    for info in tarinfo_gen(parser):
        if info.isdir():
            print '[dir]'.rjust(9), info.name
        else:
            size = int(round(info.size / 1024.0 + 0.5))
            print str(size).rjust(8) + 'k', info.name

def do_unpack(arch, dest):
    parser = parse_file(arch)
    fatal("unpack cmd not yet implemented")

def do_pack(arch, src):
    fatal("pack cmd not yet implemented")

cmd_map = {
        'p': do_pack,
        'l': do_list,
        'u': do_unpack,
    }

def parse_header(fobj):
    magic = "ANDROID BACKUP\n"
    if fobj.read(len(magic)) != magic:
        fatal("file does not appear to be a backup file")
    version = fobj.read(2)[:1]
    if version not in ('1', '2', '3'):
        fatal("unsupported backup version '%s'", version)
    comp_flag = fobj.read(2)
    if comp_flag == '1\n':
        comp_flag = True
    elif comp_flag == '0\n':
        comp_flag = False
    else:
        fatal("bad compression flag value")
    encrypt_flag = fobj.read(5)
    if encrypt_flag != 'none\n':
        encrypt_flag += fobj.read(3)
        if encrypt_flag != 'AES-256':
            fatal("unkown encryption algorithm")
        fatal("encrypted backups not yet supported")
    return comp_flag

def parse_file(path):
    """ returns a TarFile object """
    fobj = open(path)
    comp_flag = parse_header(fobj)
    if comp_flag:
        fobj = ZlibReader(fobj)
    return tarfile.open(mode='r:', fileobj=fobj)

class ZlibReader(object):
    def __init__(self, fobj):
        self.fobj = fobj
        self.zipobj = zlib.decompressobj()
        self.offset = 0
        self.data = ""

    def __fill(self, size):
        if not self.zipobj:
            return
        while not size or len(self.data) < size:
            data = self.fobj.read(16384)
            if not data:
                self.data += self.zipobj.flush()
                self.zipobj = None
                break
            self.data += self.zipobj.decompress(data)

    def seek(self, offset, whence=0):
        if whence == 0:
            position = offset
        elif whence == 1:
            position = self.offset + offset
        else:
            raise IOError("Illegal seek direction")
        if position < self.offset:
            raise IOError("Cannot seek backwards")
        
        while position > self.offset:
            if not self.read(min(position - self.offset, 16384)):
                break

    def tell(self):
        return self.offset

    def read(self, size=0):
        self.__fill(size)
        if size:
            data = self.data[:size]
            self.data = self.data[size:]
        else:
            data = self.data
            self.data = ""
        self.offset += len(data)
        return data

def main(args):
    if len(args) < 1:
        fatal("must specify a command")
    if len(args) < 2:
        fatal("must specify a file to process")
    if len(args) > 3:
        fatal("too many arguments")
    if len(args) == 3:
        cmd, arch, path = args
    else:
        cmd, arch = args
        path = '.'
    try:
        cmd_map[cmd](arch, path)
    except KeyError:
        fatal("unknown command '%s'", cmd)

def fatal(msg, *fmt):
    print >> sys.stderr, "FATAL:", msg % fmt
    sys.exit(1)

if __name__ == "__main__":
    main(sys.argv[1:])
