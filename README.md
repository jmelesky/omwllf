# OMWLLF has been archived

I'm so glad this tool was useful for as long as it was, but ultimately it was a stopgap until more sophisticated stuff came along. The [Delta Plugin](https://gitlab.com/bmwinger/delta-plugin) tool handles leveled list merging extremely well, and I recommend using it instead of `omwllf`. Thanks, @bmwinger, for writing an excellent tool.

The readme remains below, and the `omwllf` code will remain available, but this repository is now archived and there will be no further changes. Thanks to all of you who used it!


# OMWLLF - OpenMW Leveled List Fixer - v1.0

This is a utility written specifically for [OpenMW](http://openmw.org/) users who want to use lots of mods, and don't want to wrestle with using MW Classic tools to merge their leveled lists.

## How to use this

First, make sure you have python (version 3.3 or higher) installed on your system and reachable.

Second, make sure the script itself (`omwllf.py`) is downloaded and available. You can download it from github at https://github.com/jmelesky/omwllf

Then, [install your mods in the OpenMW way](https://wiki.openmw.org/index.php?title=Mod_installation), adding `data` lines to your `openmw.cfg`.

Make sure to start the launcher and enable all the appropriate `.esm`, `.esp`, and `.omwaddon` files. Drag them around to the appropriate load order.

Then, run `omwllf.py` from a command line (Terminal in OS X, Command Prompt in Windows, etc). This should create a new `.omwaddon` module, and give you instructions on how to enable it.

Open the Launcher, drag the new module to the bottom (it should be loaded last), and enable it.

Finally, start OpenMW with your new, merged leveled lists.

## Advanced usage

Having everything automatic is darn handy, but some of us have multiple config files and setups. OpenMW can handle that, so `omwllf` should be able to, too.

There are some useful command-line arguments:

  - `-c` (or `--configfile`), which allows you to specify a specific config file to use
  - `-d` (or `--moddir`), where you can set the directory in which to put the new mod
  - `-m` (or `--modname`), which lets you set the name of the new mod (I like the default of `OMW Mod - <today's date>.omwaddon`, but to each their own)

All of those are optional (obviously), but when you need them, you need them.

## HELP!

Are you having a problem? I can only fix it if I know about it. You can [file an issue](https://github.com/jmelesky/omwllf/issues) on the github project. I'm also trying to be available on the [OpenMW General Discussion forum](https://forum.openmw.org/viewforum.php?f=2), and sometimes on the [#openmw irc channel](https://webchat.freenode.net/?channels=openmw&uio=OT10cnVlde).

## Thanks

  * Resources for understanding MW file formats:
    * http://www.mwmythicmods.com/argent/tech/tute.html
    * http://www.mwmythicmods.com/tutorials/MorrowindESPFormat.html
  * The much-more-fully-functioning tool for classic TES3:
    * https://github.com/john-moonsugar/tes3cmd

