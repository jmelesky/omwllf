# omwllf
OpenMW leveled list fixer

## The Goal

Realistically, this is what I'd like this tool to do. It's not there yet.

1. Auto-detect the location of the `openmw.cfg` and `launcher.cfg` (based on the [Paths](https://wiki.openmw.org/index.php?title=Paths) docs). Allow a different path to be assigned via command-line argument.
1. Read the `openmw.cfg` and pull all `data` lines defining data and mod directories.
1. Read the `launcher.cfg` and pull all `.esm`, `.esp`, and `.omwaddon` files for `currentprofile`.
1. Process all the identified files, pulling out all leveled lists.
1. Generate a new `.omwaddon` with intelligently-merged leveled lists. Description of the mod should include all the mods with lists that got merged.
1. Output:
  1. The new `data` line to add to `openmw.cfg`
  1. Instructions to find and enable it in the launcher


If I do all that, then the documentation should be something like:

## How to use this

First, this is not yet in a usable state, and I'm writing this documentation as a basic set of requirements.

First, make sure you have python3 installed on your system and reachable.

Second, make sure this script itself (`omwllf.py`) is downloaded and available.

Then, [install your mods in the OpenMW way](https://wiki.openmw.org/index.php?title=Mod_installation), adding `data` lines to your `openmw.cfg`.

Make sure to start the launcher and enable all the appropriate `.esm`, `.esp`, and `.omwaddon` files. Drag them around to the appropriate load order.

Then, run `omwllf.py` from a command line (Terminal in OS X, Command Prompt in Windows, etc). This should create a new `.omwaddon` module, and give you instructions on how to enable it.

Add it to your `openmw.cfg` file as indicated.

Open the Launcher, drag the new module to the bottom (it should be loaded last), and enable it.

Finally, start OpenMW with your new, merged leveled lists.

