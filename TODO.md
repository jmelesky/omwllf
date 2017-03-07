### To-do list

This is brainstorming more than a real plan.

  - Make it faster. Among other things, we're currently loading and parsing each esm/esp/omwaddon file three times.
  - Improve the readability and usefulness of the output, generally
  - Improve the mod description text
  - Add flags for custom output directories, custom mod names.
    - If we do this, we'll have to add in either:
      - mechanically editing the openmw.cfg in-place, or
      - outputting "add this 'data=' line to your ...", etc.
  - GUI version? Should be relatively straightforward with tkinter
  - Wrap the script into a .exe and .app download for windows/osx

Other ideas:

  - Conflict detection is pretty easy, but is it worthwhile for this tool?
