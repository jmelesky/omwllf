#!/usr/bin/env python3

from sys import argv
from os.path import basename
from struct import unpack

def parseString(ba):
    i = ba.find(0)
    return ba[:i].decode()

def parseNum(ba):
    return int.from_bytes(ba, 'little')

def parseFloat(ba):
    return unpack('f', ba)[0]

def parseLEV(f, rec):
    levrec = {}
    sr = rec['subrecords']

    levrec['type'] = rec['type']
    levrec['name'] = parseString(sr[0]['data'])
    levrec['calcfrom'] = parseNum(sr[1]['data'])
    levrec['chancenone'] = parseNum(sr[2]['data'])
    levrec['file'] = basename(f)

    listcount = parseNum(sr[3]['data'])
    listitems = []

    for i in range(0,listcount*2,2):
        itemid = parseString(sr[4+i]['data'])
        itemlvl = parseNum(sr[5+i]['data'])
        listitems.append((itemlvl, itemid))

    levrec['items'] = listitems

    return levrec

def parseTES3(rec):
    tesrec = {}
    sr = rec['subrecords']
    tesrec['version'] = parseFloat(sr[0]['data'][0:4])
    tesrec['filetype'] = parseNum(sr[0]['data'][4:8])
    tesrec['author'] = parseString(sr[0]['data'][8:40])
    tesrec['desc'] = parseString(sr[0]['data'][40:296])
    tesrec['numrecords'] = parseNum(sr[0]['data'][296:300])

    masters = []
    for i in range(1, len(sr), 2):
        mastfile = parseString(sr[i]['data'])
        mastsize = parseNum(sr[i+1]['data'])
        masters.append((mastfile, mastsize))

    tesrec['masters'] = masters
    return tesrec

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
        print("Creature list '%s' from '%s':" % (rec['name'], rec['file']))
    else:
        print("Item list '%s':" % (rec['name']))

    print("flags: %d, chance of none: %d" % (rec['calcfrom'], rec['chancenone']))

    for (lvl, lid) in rec['items']:
        print("  %2d - %s" % (lvl, lid))

def ppTES3(rec):
    print("TES3 record, type %d, version %f" % (rec['filetype'], rec['version']))
    print("author: %s" % rec['author'])
    print("description: %s" % rec['desc'])

    for (mfile, msize) in rec['masters']:
        print("  master %s, size %d" % (mfile, msize))

    print()


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

    newLev['files'] = [ x['file'] for x in lls ]
    newLev['file'] = ', '.join(newLev['files'])


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
    levc = []
    levi = []

    ilist = []
    for f in argv[1:]:
        ilist += [ parseLEV(f, x) for x in getRecords(f, 'LEVC') ]

    levc = mergeAllLists(ilist)

    ilist = []
    for f in argv[1:]:
        ilist += [ parseLEV(f, x) for x in getRecords(f, 'LEVI') ]

    levi = mergeAllLists(ilist)

    modauthor = 'OpenMW Leveled List Fixer'
    pluginlist = []
    for x in levi + levc:
        pluginlist += x['files']
    plugins = set(pluginlist)
    moddesc = "Merged leveled lists from: %s" % ', '.join(plugins)


