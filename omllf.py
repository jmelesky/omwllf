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
        listitems.append((itemlvl, itemid))

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

    for (lvl, lid) in rec['items']:
        print("  %2d - %s" % (lvl, lid))



def mergeableLists(alllists):
    candidates = {}
    for l in alllists:
        lid = l['name']
        if lid in candidates:
            candidates[lid].append(l)
        else:
            candidates[lid] = [l]

    mergeables = {}
    for k in candidates:
        if len(candidates[k]) > 1:
            mergeables[k] = candidates[k]

    return mergeables


def mergeLists(lls):
    # last one gets priority for list-level attributes
    last = lls[-1]
    newLev = { 'type': last['type'],
               'name': last['name'],
               'calcfrom': last['calcfrom'],
               'chancenone': last['chancenone'] }

    allItems = []
    for l in lls:
        allItems += l['items']

    # This ends up being a bit tricky, but it prevents us
    # from overloading lists with the same stuff.
    #
    # This is needed, because the original leveled lists
    # contain multiple entries for some creatures/items, and
    # that gets reproduced in many plugins. 
    #
    # If we just added and sorted, then the more plugins you
    # have, the less often you'd see plugin content. This
    # method prevents the core game content from overwhelming
    # plugin contents.

    allUniques = [ x for x in set(allItems) ]
    allUniques.sort()

    newList = []

    for i in allUniques:
        newCount = max([ x['items'].count(i) for x in lls ])
        newList += [i] * newCount

    newLev['items'] = newList

    return newLev


def mergeAllLists(alllists):
    mergeables = mergeableLists(alllists)

    merged = []

    for k in mergeables:
        merged.append(mergeLists(mergeables[k]))

    return merged


def writeHeader():
    pass


def writeList():
    pass



if __name__ == '__main__':
    for t in ['LEVC', 'LEVI']:
        ilist = []
        for filename in argv[1:]:
            ilist += [ parseLEV(x) for x in getRecords(filename, t) ]

        for rec in mergeAllLists(ilist):
            ppLEV(rec)

