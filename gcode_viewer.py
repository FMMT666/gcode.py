#!/usr/bin/env python
# -*- coding: utf-8 -*-

# gsplit.py
# Wrapper for gsort.py's file G-Code view functionality.
#
# (c) FMMT666(ASkr) 8/2007, 7/2025


import gprobe_viewer as gv
import numpy as np
import sys


Z_THRESHOLD = 0.0  # TODO: only coordinates below this value will be plotted


def usage():
    print("---\nUsage: python gcode_viewer <nc-file>")
    print("...")


def load( fname ):
    try:
        fin = open(fname, 'r')
    except:
        print( f"Error loading from {fname}.")
        return None

    data = []
    lastX = lastY = lastZ = None
    codeLetters = "XYZFM"
    lineNo = 0

    for line in fin:
        line = line.upper().strip()

        lineNo += 1

        x = y = z = None

        # ----- remove comments
        if '(' in line and ')' in line:
            line = line.split('(')[0].strip()

        # ----- correct "G0" and "G1" to "G00" and "G01" if possible
        # This is far from complete, there are tons of other possibilities, like
        # G0X, G0Y, G0Z, G0F, etc ...
        if not 'G00' in line:
            if 'G0 ' in line:
                line = line.replace('G0', 'G00 ')
        if not 'G01' in line:
            if 'G1 ' in line:
                line = line.replace('G1', 'G01 ')

        # ----- only lines with G00 or G01 commands
        if 'G00' in line or 'G01' in line:
            # create some spaces for str to float conversion
            for ch in codeLetters:
                line = line.replace( ch, " " + ch)

            # TODO: try/except and error checks if conversion fails


            # ----- X
            if 'X' in line:
                try:
                    x = float( line.split('X')[1].split()[0] )
                except:
                    print( f"Error parsing X coordinate in line no {lineNo}:\n{line}\n" + str(line.split('X')[1].split()[0]) )
                lastX = x
            else:
                if lastX is not None:
                    x = lastX

            # ----- Y
            if 'Y' in line:
                try:
                    y = float( line.split('Y')[1].split()[0] )
                except:
                    print( f"Error parsing Y coordinate in line no {lineNo}:\n{line}\n" + str(line.split('Y')[1].split()[0]) )
                lastY = y
            else:
                if lastY is not None:
                    y = lastY

            # ----- Z
            if 'Z' in line:
                try:
                    z = float( line.split('Z')[1].split()[0] )
                except:
                    print( f"Error parsing Z coordinate in line no {lineNo}:\n{line}\n" + str(line.split('Z')[1].split()[0]) )
                lastZ = z
            else:
                if lastZ is not None:
                    z = lastZ

        # -----

        if x is not None and y is not None and z is not None:
            data.append( [x, y, z] )

    return np.array( data )



if __name__ == "__main__":

    if len(sys.argv) > 1:
        fname = sys.argv[1]
    else:
        usage()
        print("Continuing with demo data ...")
        fname = "gcode_demo_adjusted.ngc"

    data = load( fname )

    if data is not None:

        gv.plot( data, only_verts = True )

