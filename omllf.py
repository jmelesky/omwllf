#!/usr/bin/env python3

from sys import argv


def parseString(ba):
    i = ba.find(0)
    return ba[:i].decode()

def parseNum(ba):
    return int.from_bytes(ba, 'little')

def parseLEV(rec):
    levrec = {}
    sr = rec['subrecords']

    levrec['type'] = rec['type']
    levrec['name'] = parseString(sr[0]['data'])
    levrec['calcfrom'] = parseNum(sr[1]['data'])
    levrec['chancenone'] = parseNum(sr[2]['data'])

    listcount = parseNum(sr[3]['data'])
    listitems = []

    for i in range(0,listcount*2,2):
        itemid = parseString(sr[4+i]['data'])
        itemlvl = parseNum(sr[5+i]['data'])
        listitems.append((itemid, itemlvl))

    levrec['items'] = listitems

    return levrec


def pullSubs(rec, subtype):
    return [ s for s in rec['subrecords'] if s['type'] == subtype ]

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
    return ( r for r in readRecords(filename) if r['type'] == rectype )


def ppSubRecord(sr):
    if sr['type'] in ['NAME', 'INAM', 'CNAM']:
        print("  %s, length %d, value '%s'" % (sr['type'], sr['length'], parseString(sr['data'])))
    elif sr['type'] in ['DATA', 'NNAM', 'INDX', 'INTV']:
        print("  %s, length %d, value '%s'" % (sr['type'], sr['length'], parseNum(sr['data'])))
    else:
        print("  %s, length %d" % (sr['type'], sr['length']))

def ppRecord(rec):
    print("%s, length %d" % (rec['type'], rec['length']))
    for sr in rec['subrecords']:
        ppSubRecord(sr)

    
def ppLEV(rec):
    if rec['type'] == 'LEVC':
        print("Creature list '%s':" % (rec['name']))
    else:
        print("Item list '%s':" % (rec['name']))

    print("flags: %d, chance of none: %d" % (rec['calcfrom'], rec['chancenone']))

    for (lid, lvl) in rec['items']:
        print("  %2d - %s" % (lvl, lid))



if __name__ == '__main__':
#    for rrec in getRecords(argv[1], 'LEVI'):
#        ppRecord(rrec)

    for filename in argv[1:]:
        for rrec in getRecords(filename, 'LEVI'):
            ppLEV(parseLEV(rrec))
        for rrec in getRecords(filename, 'LEVC'):
            ppLEV(parseLEV(rrec))

