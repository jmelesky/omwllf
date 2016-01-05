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

def readRecords(filename):
    fh = open(filename, 'rb')
    while True:
        headerba = fh.read(16)
        if headerba is None or len(headerba) < 16:
            return None

        record = {}
        header = readHeader(headerba)
        record['type'] = header['type']
        record['length'] = header['length']
        record['subrecords'] = []

        remains = fh.read(header['length'])

        while len(remains) > 0:
            (subrecord, restofbytes) = readSubRecord(remains)
            record['subrecords'].append(subrecord)
            remains = restofbytes

        yield record


def getRecords(filename, rectype):
    return [ r for r in readRecords(filename) if r['type'] == rectype ]


def ppSubRecord(sr):
    print("  %s, length %d" % (sr['type'], sr['length']))

def ppRecord(rec):
    print("%s, length %d" % (rec['type'], rec['length']))
    for sr in rec['subrecords']:
        ppSubRecord(sr)

    


if __name__ == '__main__':
    filename = argv[1]

    for rec in getRecords(filename, 'LEVI'):
        ppRecord(rec)
