#!/usr/bin/env python
# -*- coding: utf-8 -*-

# gsplit.py
# Wrapper for gsort.py's file G-Code view functionality.
#
# (c) FMMT666(ASkr) 8/2007, 7/2025


import gprobe_viewer as gv
import numpy as np
import sys


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

    for line in fin:
        line = line.upper().strip()

        x = y = z = None

        # -----
        if 'G00' in line or 'G01' in line:
            # create some spaces for str to float conversion
            for ch in codeLetters:
                line = line.replace( ch, " " + ch)

            # TODO: try/except and error checks if conversion fails


            if 'X' in line:
                x = float( line.split('X')[1].split()[0] )
                lastX = x
            else:
                if lastX is not None:
                    x = lastX

            if 'Y' in line:
                y = float( line.split('Y')[1].split()[0] )
                lastY = y
            else:
                if lastY is not None:
                    y = lastY

            if 'Z' in line:
                z = float( line.split('Z')[1].split()[0] )
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
        fname = "gcode_demo.ngc"

    data = load( fname )

    if data is not None:

        gv.plot( data, only_verts = True )

