gsort.py
========

A little G-code sorter to speed up the PCB milling process with [PCB-GCode][1] for [Eagle][2].

For a little more info, including a binary distribution, follow [this link][3]. 

Although it might have it's issues, like the currently still missing M02 command at the end of the
file (read the readme), I milled hundreds of PCB with it.

Yep, it works quite fine, but please notice that this code is (yet) from 2007 and might not
be compatible with newer PCB-GCode (or Eagle) releases.

Has to be tested, that's while it's now (4/2014) here, on Github.


----------------------------------------------------------------------------------------------

Originally tested with:

 - pcb-gcode with EMC (EMC2, LinuxCNC) post processor
 - hp2xx

 Also working, but not required (for sorting):

 - CopperCAM in LinuxCNC mode


---
## TODO
    - 2025 support tool changes
    - 2025 support tool changes file splitting (file_T1, file_T2, etc.)
    - 2025 auto LeVeLlLlLing <3


---
## NEWS

### CHANGES 2025/07/XX:
    - v0.3
    - revived for Python 3
    - some code formatting and notes
    - new .gitignore
    - now tested with CopperCAM (not required though; already sorted)
    - added log file (almost)
    - added length calc & cut marker


### CHANGES 2007/09/XX:
    - v0.2
    - first tests with hp2xx revealed, that hp2xx uses ";" for comments
      These lines are now changed to parenthesis-comments


### CHANGES 2007/09/XX:
    - v0.1
    - initial version



---
Have fun  
FMMT666(ASkr)  


[1]: http://www.pcbgcode.org/
[2]: http://www.cadsoft.de
[3]: http://www.askrprojects.net/software/gsort.html
