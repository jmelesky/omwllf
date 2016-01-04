#!/usr/bin/env python3

from sys import argv



def readHeader(ba):
    header = {}
    header['type'] = ba[0:4].decode()
    header['length'] = int.from_bytes(ba[4:8], 'little')
    return header

def readSubRecord(ba):
    sr = {}
    sr['type'] = ba[0:4].decode()
    sr['length'] = int.from_bytes(ba[4:8], 'little')
    endbyte = 8 + sr['length']
    sr['data'] = ba[8:endbyte]
    return (sr, ba[endbyte:])


def readRecord(fh):
    record = {}

    header = readHeader(fh.read(16))

    remains = fh.read(header['length'])

    record['type'] = header['type']
    record['length'] = header['length']
    record['subrecords'] = []

    while len(remains) > 0:
        (subrecord, restofbytes) = readSubRecord(remains)
        record['subrecords'].append(subrecord)
        remains = restofbytes

    return record

def ppSubRecord(sr):
    print("  %s, length %d" % (sr['type'], sr['length']))

def ppRecord(rec):
    print("%s, length %d" % (rec['type'], rec['length']))
    for sr in rec['subrecords']:
        ppSubRecord(sr)

    


if __name__ == '__main__':
    filename = argv[1]

    fh = open(filename, 'rb')
    
    ppRecord(readRecord(fh))
