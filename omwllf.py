#!/usr/bin/env python3

from struct import pack, unpack
from datetime import date
import os.path
import argparse
import sys
import re


configFilename = 'openmw.cfg'
configPaths = { 'linux':   '~/.config/openmw',
                'freebsd': '~/.config/openmw',
                'darwin':  '~/Library/Preferences/openmw',
                'win32':   '~\Documents\my games\openmw' }

modPaths = { 'linux':   '~/.local/share/openmw/data',
             'freebsd': '~/.local/share/openmw/data',
             'darwin':  '~/Library/Application Support/openmw/data',
             'win32':   '~\Documents\my games\openmw\data' }
             

def packLong(i):
    # little-endian, "standard" 4-bytes (old 32-bit systems)
    return pack('<l', i)

def packString(s):
    return bytes(s, 'ascii')

def packPaddedString(s, l):
    bs = bytes(s, 'ascii')
    if len(bs) > l:
        # still need to null-terminate
        return bs[:(l-1)] + bytes(1)
    else:
        return bs + bytes(l - len(bs))

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
    levrec['file'] = os.path.basename(f)

    # Apparently, you can have LEV records that end before
    # the INDX subrecord. Found those in Tamriel_Data.esm
    if len(sr) > 3:
        listcount = parseNum(sr[3]['data'])
        listitems = []

        for i in range(0,listcount*2,2):
            itemid = parseString(sr[4+i]['data'])
            itemlvl = parseNum(sr[5+i]['data'])
            listitems.append((itemlvl, itemid))

        levrec['items'] = listitems
    else:
        levrec['items'] = []

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


def packStringSubRecord(lbl, strval):
    str_bs = packString(strval) + bytes(1)
    l = packLong(len(str_bs))
    return packString(lbl) + l + str_bs

def packIntSubRecord(lbl, num, numsize=4):
    # This is interesting. The 'pack' function from struct works fine like this:
    #
    # >>> pack('<l', 200)
    # b'\xc8\x00\x00\x00'
    #
    # but breaks if you make that format string a non-literal:
    #
    # >>> fs = '<l'
    # >>> pack(fs, 200)
    # Traceback (most recent call last):
    #   File "<stdin>", line 1, in <module>
    # struct.error: repeat count given without format specifier
    #
    # This is as of Python 3.5.2

    num_bs = b''
    if numsize == 4:
        # "standard" 4-byte longs, little-endian
        num_bs = pack('<l', num)
    elif numsize == 2:
        num_bs = pack('<h', num)
    elif numsize == 1:
        # don't think endian-ness matters for bytes, but consistency
        num_bs = pack('<b', num)
    elif numsize == 8:
        num_bs = pack('<q', num)

    return packString(lbl) + packLong(numsize) + num_bs

def packLEV(rec):
    start_bs = b''
    id_bs = b''
    if rec['type'] == 'LEVC':
        start_bs += b'LEVC'
        id_bs = 'CNAM'
    else:
        start_bs += b'LEVI'
        id_bs = 'INAM'

    headerflags_bs = bytes(8)
    name_bs = packStringSubRecord('NAME', rec['name'])
    calcfrom_bs = packIntSubRecord('DATA', rec['calcfrom'])
    chance_bs = packIntSubRecord('NNAM', rec['chancenone'], 1)

    subrec_bs = packIntSubRecord('INDX', len(rec['items']))
    for (lvl, lid) in rec['items']:
        subrec_bs += packStringSubRecord(id_bs, lid)
        subrec_bs += packIntSubRecord('INTV', lvl, 2)

    reclen = len(name_bs) + len(calcfrom_bs) + len(chance_bs) + len(subrec_bs)
    reclen_bs = packLong(reclen)

    return start_bs + reclen_bs + headerflags_bs + \
        name_bs + calcfrom_bs + chance_bs + subrec_bs

def packTES3(desc, numrecs, masters):
    start_bs = b'TES3'
    headerflags_bs = bytes(8)

    hedr_bs = b'HEDR' + packLong(300)
    version_bs = pack('<f', 1.0)

    # .esp == 0, .esm == 1, .ess == 32
    # suprisingly, .omwaddon == 0, also -- figured it would have its own
    ftype_bs = bytes(4)

    author_bs = packPaddedString('omwllf, copyright 2017, jmelesky', 32)
    desc_bs = packPaddedString(desc, 256)
    numrecs_bs = packLong(numrecs)

    masters_bs = b''
    for (m, s) in masters:
        masters_bs += packStringSubRecord('MAST', m)
        masters_bs += packIntSubRecord('DATA', s, 8)

    reclen = len(hedr_bs) + len(version_bs) + len(ftype_bs) + len(author_bs) +\
             len(desc_bs) + len(numrecs_bs) + len(masters_bs)
    reclen_bs = packLong(reclen)

    return start_bs + reclen_bs + headerflags_bs + \
        hedr_bs + version_bs + ftype_bs + author_bs + \
        desc_bs + numrecs_bs + masters_bs

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
        print("Item list '%s' from '%s':" % (rec['name'], rec['file']))

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


def readCfg(cfg):
    # first, open the file and pull all 'data' and 'content' lines, in order

    data_dirs = []
    mods = []
    with open(cfg, 'r') as f:
        for l in f.readlines():
            # match of form "blah=blahblah"
            m = re.search(r'^(.*)=(.*)$', l)
            if m:
                varname = m.group(1).strip()
                # get rid of not only whitespace, but also surrounding quotes
                varvalue = m.group(2).strip().strip('\'"')
                if varname == 'data':
                    data_dirs.append(varvalue)
                elif varname == 'content':
                    mods.append(varvalue)

    # we've got the basenames of the mods, but not the full paths
    # and we have to search through the data_dirs to find them
    fp_mods = []
    for m in mods:
        for p in data_dirs:
            full_path = os.path.join(p, m)
            if os.path.exists(full_path):
                fp_mods.append(full_path)
                break

    print("Config file parsed...")

    return fp_mods

def dumplists(cfg):
    llists = []
    fp_mods = readCfg(cfg)
    for f in fp_mods:
        [ ppTES3(parseTES3(x)) for x in getRecords(f, 'TES3') ]

    for f in fp_mods:
        llists += [ parseLEV(f, x) for x in getRecords(f, 'LEVI') ]

    for f in fp_mods:
        llists += [ parseLEV(f, x) for x in getRecords(f, 'LEVC') ]

    for l in llists:
        ppLEV(l)


def main(cfg, outmod):
    fp_mods = readCfg(cfg)

    # first thing, we need a list of master files required by
    # all our mods

    tes3list = []
    for f in fp_mods:
        print("Pulling master file info from '%s'" % f)
        tes3list += [ parseTES3(x) for x in getRecords(f, 'TES3') ]

    masters = {}
    for t in tes3list:
        for m in t['masters']:
            masters[m[0]] = m[1]

    master_list = [ (k,v) for (k,v) in masters.items() ]

    # okay, now we have the full list of esp, esm, and omwaddon
    # files, so let's read them, pull out all the leveled lists,
    # and generate some merged ones

    levc = [] # creature lists
    levi = [] # item lists

    ilist = []
    for f in fp_mods:
        print("Pulling creature lists from '%s'" % f)
        ilist += [ parseLEV(f, x) for x in getRecords(f, 'LEVC') ]

    levc = mergeAllLists(ilist)

    ilist = []
    for f in fp_mods:
        print("Pulling item lists from '%s'" % f)
        ilist += [ parseLEV(f, x) for x in getRecords(f, 'LEVI') ]

    levi = mergeAllLists(ilist)

    llist_bc = b''
    pluginlist = []
    for x in levi + levc:
        # ppLEV(x)
        llist_bc += packLEV(x)
        pluginlist += x['files']
    plugins = set(pluginlist)
    moddesc = "Merged leveled lists from: %s" % ', '.join(plugins)

    with open(outmod, 'wb') as f:
        f.write(packTES3(moddesc, len(levi + levc), master_list))
        f.write(llist_bc)

    modShortName = os.path.basename(outmod)
    print("\n\n****************************************")
    print(" Great! I think that worked. When you next start the OpenMW Launcher, look for a module named %s. Make sure of the following things:" % modShortName)
    print("    1. %s is at the bottom of the list. Drag it to the bottom if it's not. It needs to load last." % modShortName)
    print("    2. %s is checked (enabled)" % modShortName)
    print("    3. Any other OMWLLF mods are *un*checked. Loading them might not cause problems, but probably will")
    print("\n")
    print(" Then, go ahead and start the game! Your leveled lists should include adjustmemts from all relevants enabled mods")
    print("\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--conffile', type = str, default = None,
                        action = 'store', required = False,
                        help = 'Conf file to use. Optional. By default, attempts to use the default conf file location.')

    parser.add_argument('-d', '--dumplists', default = False,
                        action = 'store_true', required = False,
                        help = 'Instead of generating merged lists, dump all leveled lists in the conf mods. Used for debugging')

    p = parser.parse_args()

    confFile = ''
    baseModDir = ''
    if p.conffile:
        confFile = p.conffile
    else:
        pl = sys.platform
        if pl in configPaths:
            baseDir = os.path.expanduser(configPaths[pl])
            baseModDir = os.path.expanduser(modPaths[pl])
            confFile = os.path.join(baseDir, configFilename)
        else:
            print("Sorry, I don't recognize the platform '%s'. You can try specifying the conf file using the '-c' flag." % p)
            sys.exit(1)

    if not os.path.exists(confFile):
        print("Sorry, the conf file '%s' doesn't seem to exist." % confFile)
        sys.exit(1)

    modName = 'OMWLLF Mod - %s.omwaddon' % date.today().strftime('%Y-%m-%d')
    modFullPath = os.path.join(baseModDir, modName)

    if p.dumplists:
        dumplists(confFile)
    else:
        main(confFile, modFullPath)


