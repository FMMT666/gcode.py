#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Stinky little quick and dirty program.
# Far from complete, lots of possible error sources but extremely useful.
# Actually, I have been using it for 17+ years now, so it is not that bad (for me :-)
#
# (c) FMMT666(ASkr) 8/2007, 7/2025


# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#            
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#                            
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


# ToDo:
# - Footer is not implemented:
#   User always has to add "M02" (or other important stuff right after
#   the last "G00 Z<up>" command) manually
# - Tool change commands are not supported (yet); though most of them
#   will not cause any issues (but they are blocked).
# - a lot...


# ASkr, 7/2025; v0.3:
# - revived for Python 3

# ASkr, 9/2007; v0.2:
# - first tests with hp2xx revealed, that hp2xx uses ";" for comments
#   These lines are now changed to parenthesis-comments

# ASkr, 9/2007, v0.1
# - initial version


import sys
from typing import Optional, TextIO


VERSION       = "v0.3"

HEADER_START  = "(*** GS HEADER START)"
HEADER_END    = "(*** GS HEADER END)"
SPLIT_START   = "(*** GS BLK START)"
SPLIT_END     = "(*** GS BLK END)"
SPLIT_POS     = "(*** GS XXXX YYYY NNNN)"  # 4 letters to be replaced by X<num>, Y<num>, N<num> later on
CUT_MARKER    = "(*** GS CUT MARKER LLLL)" # dbg only; 4 letters to be replaced by trace length

STR_NUMBERS   = "01234567890.- "

LVL_MAX_TRACELEN = 5.0   # maximum trace length for auto leveling; assuming mm


#############################################################################
### vecLength
###
#############################################################################
def vecLength(p1,p2=None):
  if p2 is None:
    return ( p1[0]**2.0 + p1[1]**2.0 ) ** 0.5
  else:
    return ( (p2[0]-p1[0])**2.0 + (p2[1]-p1[1])**2.0  ) ** 0.5



###########################################################################
### tGetNumAfterChar
###
###########################################################################
def tGetNumAfterChar(line,ch):
  if line.count(ch) != 1:
    return None
  
  ls = line.find(ch)

  j = 0
  for i in line[ ls + 1: ]:
    if STR_NUMBERS.count(i) == 0:
      break
    j += 1

  if j == 0:
    return None

  tmp = line[ ls + 1 : ls + 1 + j ].strip(" \t")

  try:
    ret = float(tmp)
  except:
    ret = None

  return ret



#############################################################################
### class Blks
###
###
###
#############################################################################
class Blks:

  ###########################################################################
  ###
  ###
  ###########################################################################
  def __init__(self):
    self.BlkLst = []

    
  ###########################################################################
  ###
  ###
  ###########################################################################
  def __exit__(self):
    pass

    
  ###########################################################################
  ###
  ###
  ###########################################################################
  # blknr = int
  # spos  = (x,y)
  # epos  = (x,y)
  # larea = (line of block start, line of block end)
  def add(self,blknr,spos,epos,larea):
    self.BlkLst.append( { 'blknr':blknr, 'arranged':None, 'spos':spos, 'epos':epos, 'larea':larea } )

    # DEBUG
    if blknr == 0:
      print( "SIZE AFTER HEADER: " + str(len(self.BlkLst)) )
    

    
  ###########################################################################
  ###
  ###
  ###########################################################################
  def get(self,blknr):
    if self.BlkLst == []:
      return None
    for i in self.BlkLst:
      if i['blknr'] == blknr:
        return i
    return None


  ###########################################################################
  ###
  ###
  ###########################################################################
  def pop(self,blknr):
    if self.BlkLst == []:
      return None

    index = 0
    for i in self.BlkLst:
      if i['blknr'] == blknr:
        self.BlkLst.pop(index)
        print( "MSG: KILLED " + str(blknr) + " of grand total " + str(len(self.BlkLst)) )
        return 1
      index += 1

    return 0


  ###########################################################################
  ###
  ###
  ###########################################################################
  def count(self):
    return len(self.BlkLst)


  ###########################################################################
  ###
  ###
  ###########################################################################
  def getall(self):
    ret = []
    for i in self.BlkLst:
      ret.append(i)
    return ret


  ###########################################################################
  ###
  ###
  ###########################################################################
  def findNearest(self,pos):

    dist = 99999999.9
    index = 0
    target = -1

    for bl in self.BlkLst:
      # skip the header during search
      if bl['blknr'] != 0:
        i = vecLength( pos, bl['spos'] )
        if i < dist:
          dist = i
          target = index
      index += 1

    if target == -1:
      return None
    
    return self.BlkLst[ target ][ 'blknr' ]



#############################################################################
### class GFile
###
###
###
#############################################################################
class GFile:

  ###########################################################################
  ### __init__
  ###
  ###########################################################################
  def __init__(self):
    print( "MSG: GFile __init__" )
    self.fName: Optional[str]    = None
    self.fI:    Optional[TextIO] = None  # the input file
    self.fO:    Optional[TextIO] = None  # the temporary output file "*.1gs"
    self.fB:    Optional[TextIO] = None  # the final output file     "*.2gs"
    self.fLog:  Optional[TextIO] = None  # the log file
    
    self.Blks = Blks()
    self.newOrder = []

    self.lpos = (None,None)  # last postition
    self.llev = None         # last z level
    
    self.sBlks = 0           # number of start blocks already written
    
    self.tPos = None         # current tool position
    
    self.nLine = ""          # ATTN: dirty hack ahead =)
    

  ###########################################################################
  ### __exit__
  ###
  ###########################################################################
  def __exit__(self):
    print( "MSG: GFile __exit__" )

    try:
      if self.fI is not None:
        self.fI.close()
    except:
      pass

    try:
      if self.fO is not None:
        self.fO.close()
    except:
      pass


  ###########################################################################
  ### fOpen
  ###
  ###########################################################################
  def fOpen(self,FileName):
    """
    Opens the input file and the output files *.1gs, *.2gs and *.log.
    """
    print( "MSG: GFile fOpen" )
    try:
      self.fI = open(FileName,"r+t")
    except:
      self.fI = None
    
    if self.fI is None:
      print( "ERR: ### unable to open input file \"" + FileName + "\"" )
      return -1
    else:
      print( "MSG: opened input file \"" + FileName + "\"" )

    if FileName.count(".") < 1:
      tmp = FileName
    else:
      tmp = FileName[:FileName.rfind(".")]
      
    try:
      self.fO = open( tmp+".1gs", "w+t")
    except:
      self.fO = None
    
    if self.fO is None:
      print( "ERR: ### unable to open output file 1: \"" + tmp + ".1gs" + "\"" )
      return -1
    else:
      print( "MSG: opened output file 1 \"" + tmp + ".1gs" + "\"" )

    try:
      self.fB = open(tmp + ".2gs","w+t")
    except:
      self.fB = None
    
    if self.fB is None:
      print( "ERR: ### unable to open output file 2: \"" + tmp + "\"" )
      return -1
    else:
      print( "MSG: opened output file 2 \"" + tmp + ".2gs" + "\"" )

    if self.fLog is None:
      try:
        self.fLog = open( tmp + ".log", "w+t" )
      except:
        self.fLog = None
    
    return 1


  ###########################################################################
  ### fClose
  ###
  ###########################################################################
  def fClose(self):
    """
    Closes all open files.
    """
    print( "MSG: GFile fClose" )
    try:
      if self.fB is not None:
        self.fB.close()
      if self.fO is not None:
        self.fO.close()
      if self.fI is not None:
        self.fI.close()
      if self.fLog is not None:
        self.fLog.close()
    except:
      pass


  ###########################################################################
  ### fPrint
  ###
  ###########################################################################
  def fPrint(self, msg, logtofile = True):
    """
    Logs a message to the console and optionally to the log file.
    """
    print( msg )
    
    if self.fLog is not None and logtofile:
      try:
        self.fLog.write( msg + "\n" )
        self.fLog.flush()
      except:
        print( "ERR: ### unable to write to log file" )


  ###########################################################################
  ### fAnalyzeLine
  ###
  ### return codes:
  ###  -1 -> error
  ###   0 -> no changes to output
  ###   1 -> Tool down
  ###   2 -> Tool up
  ###   3 -> minor fixes to line (use self.nLine for new output!)
  ###   4 -> line was cut to pieces for auto leveling (use self.nLine)
  ###########################################################################
  def fAnalyzeLine(self, line, linenr, triglev ):
#    print "MSG: GFile fAnalyzeFile"
    tmp = line
    tmp = tmp.upper()
    tmp = tmp.strip(" \t")

    # new in 2025; should be okay [tm]
    tmp = tmp.strip("\r\n ")
    
    # TODO: the return codes should be strings

    if len(tmp) < 1:
      return 0

    # hack for hp2xx, which implements gcode comments via ";"
    if tmp[0] == ";":
      print( "MSG: changed \";\" comment to parenthesis" )
      line = line.rstrip("\r\n")
      self.nLine = "( " + line + " )"
      return 3
    
    if tmp[0] == "(":
      return 0
      
    if tmp[0] == "N":
      print( "ERR: ### program numbers not supported:" )
      print( "     \"" + line + "\"" )
      return -1

    # TESTING WARNING TESTING: temporarily allow tool change commands
    # if tmp.count("T") > 0:
    #   print( "ERR: ### tool change not supported:" )
    #   print( "     \"" + line + "\"" )
    #   return -1
    if tmp.count("T") > 0:
      print( "MSG: ### tool change not officially supported" )
      print( "     \"" + line + "\"" )
      return 0

    if tmp[0]=="G":
      if tmp[1:3]=="91":
        print( "ERR: ### relative mode not supported:" )
        print( "     \"" + line + "\"" )
        return -1
    
      # TODO: could be G2 or G3: check for two numbers after the G (in general)
      if tmp[1:3]=="02" or tmp[1:3]=="03":
        print( "ERR: ### arcs not supported:" )
        print( "     \"" + line + "\"" )
        return -1

      # TODO: same as for G2, G3; but could be corrected to two digits
      if ( LINEARMOVE := ( tmp[1:3] == "01" ) ) or tmp[1:3] == "00":
        tmp2 = tmp[3:]
        tmp2 = tmp2.strip(" \t")
        
        cx = tmp2.count("X")
        cy = tmp2.count("Y")
        cz = tmp2.count("Z")
        

        # NEW 2025: calc deltas
        dx = dy = 0.0

        # X and Y movement
        if cx > 0 or cy > 0:
          if cz > 0:
            print( "ERR: ### moving z at same time as x or y is not supported:" )
            print( "     \""+line+"\"" )
            return -1

          # --- X movement
          if cx > 0:
            i = tGetNumAfterChar(tmp2,"X")
            if i is None:
              print( "ERR: ### G00/01 X number error:" ) 
              print( "     \"" + line + "\"" )
              return -1
            
            if self.lpos[0] is not None:
              dx = i - self.lpos[0]
            self.lpos = ( i, self.lpos[1] )

          # --- Y movement
          if cy > 0:
            i = tGetNumAfterChar(tmp2,"Y")
            if i is None:
              print( "ERR: ### G00/01 Y number error:" )
              print( "     \"" + line + "\"" )
              return -1
            
            if self.lpos[1] is not None:
              dy = i - self.lpos[1]
            self.lpos = ( self.lpos[0], i )

          # --- if auto leveling is enabled; cut traces
          if cx > 0 or cy > 0:
            traceLen = vecLength( (dx,dy) )
            if LINEARMOVE and traceLen > LVL_MAX_TRACELEN:
              self.fPrint( "MAX: \"" + tmp + "\" -> dx=" + f'{dx:.4f}' + ", dy=" + f'{dy:.4f}' + ", traceLen=" + f'{traceLen:.4f}' )
              # TODO: cut the line into pieces; no changes for now
              self.nLine = tmp + "   " + CUT_MARKER.replace("LLLL",f'{traceLen:.4f}')
              return 4


        # only Z movement    
        else:
          if cz > 0:
            i = tGetNumAfterChar(tmp2,"Z")
            if i is None:
              print( "ERR: ### G00/01 Z number error:" )
              print( "     \""+line+"\"" )
              return -1
            self.llev = i
            if i < triglev:
              return 1   # tool down
            else:
              return 2   # tool up
          
          # something we don't know was moved; maybe a rotary axis
          else:
            print( "ERR: ### G00/01 command without X, Y or Z:" )
            print( "     \"" + line + "\"" )
            return -1


    return 0


  ###########################################################################
  ### fSplitIn2Out
  ###
  ###########################################################################
  def fSplitIn2Out(self,TrigLev):
    """
    Splits the G-code into logical blocks based on tool movements and marks these blocks in a new file.
    """

    lnr = 1
    blknr = 0

    if self.fO is None:
      print( "ERR: ### fSplitIn2Out(): output file not open" )
      return -1

    if self.fI is None:
      print( "ERR: ### fSplitIn2Out(): input file not open" )
      return -1

    self.fO.write( "\n" + HEADER_START + "\n\n" )

    while 1:
      tmp = self.fI.readline()
      if not tmp:
        break
        
      # TODO: this methods writes the results to "nLine", which is just baaad; needs fix
      i = self.fAnalyzeLine( tmp, lnr, TrigLev )

      tmp = tmp.rstrip("\r\n")
        
      # --- an error occured
      if i < 0:
        return -1
        
      # --- no important stuff in this line
      if i == 0:
        self.fO.write( tmp + "\n" )

      # --- minor changes to the line
      # TODO: uses the new line "nLine", which was secretly changed in fAnalyzeLine()
      # some minor changes were applied to the (new) line
      if i == 3:
        self.fO.write( self.nLine + "\n" )

      # --- line was cut in smaller segments for auto leveling
      if i == 4: 
        self.fO.write( self.nLine + "\n" )

      # --- tool down
      if i == 1:
        blknr += 1
        
        if blknr == 1:
          self.fO.write( "\n" + HEADER_END + "\n\n" )
        
        print( "MSG: processing Block " + str(blknr) )

        self.fO.write( "\n" + SPLIT_START + "\n" )
        self.fO.write( SPLIT_POS.replace("XXXX","X"+str(self.lpos[0])).replace("YYYY","Y"+str(self.lpos[1])).replace("NNNN","N"+str(blknr)) + "\n"  )

        self.fO.write( "G00 X" + str(self.lpos[0]) + " Y" + str(self.lpos[1]) + "\n" )
        self.fO.write( tmp + "\n")
        self.sBlks += 1
        self.tPos = "down"
        
      # --- tool up
      if i == 2:
        self.fO.write( tmp + "\n" )
        if self.sBlks > 0:
          self.fO.write( SPLIT_END + "\n" )
          self.fO.write( SPLIT_POS.replace("XXXX","X"+str(self.lpos[0])).replace("YYYY","Y"+str(self.lpos[1])).replace("NNNN","N"+str(blknr)) + "\n\n" )

        self.tPos = "up"

    return 0


  ###########################################################################
  ### fAnalyzeBlocks
  ###
  ###########################################################################
  def fAnalyzeBlocks(self):

    if self.fO is None:
      print( "ERR: ### fAnalyzeBlocks(): output file not open" )
      return -1

    if self.fI is None:
      print( "ERR: ### fAnalyzeBlocks(): input file not open" )
      return -1

    tmp = self.fO.name

    try:
      self.fO.close()
      self.fI.close()
    except:
      pass

    try:
      self.fI = open( tmp, "r+t" )
      print( "MSG: re-opened output file 1 (READ)\"" + tmp + "\"" )
    except:
      print( "ERR: ### unable to open output file 1 (READ): \"" + tmp + "\"" )
      return -1
    
    lnr = 0

    while 1:
      tmp = self.fI.readline()
      lnr += 1
      if not tmp:
        break

      # header is treated as block number 0
      if tmp.count( HEADER_END ) > 0:
        print( "DBG: ADDING HEADER" )
        self.Blks.add( 0, (0,0), (0,0), (1,lnr) )
        
        
      if tmp.count(SPLIT_START) > 0:
        lsta = lnr
        tmp = self.fI.readline()
        lnr += 1
        if not tmp:
          print( "ERR: ### EOF after start of block (aka: \"G00 Z<up>\" is missing)" )
          return -1
        
        # tmp now contains coords and block number
        b1 = int( tGetNumAfterChar( tmp, "N" ) )
        x1 = tGetNumAfterChar( tmp, "X" )
        y1 = tGetNumAfterChar( tmp, "Y" )
        
        if b1 is None or x1 is None or y1 is None:
          print( "ERR: ### missing X, Y or N in start of block descriptor:" )
          print( "     \""+tmp+"\"" )
          return -1
        
        while 1:
          tmp = self.fI.readline()
          lnr += 1
          if not tmp:
            print( "ERR: ### EOF after start of block (aka: \"G00 Z<up>\" is missing)" )
            return -1
            
          if tmp.count(SPLIT_START) > 0:
            print( "ERR: ### got second start of block at line No.:"+str(lnr) )
            return -1
          
          if tmp.count(SPLIT_END) > 0:
            lend = lnr
            tmp = self.fI.readline()
            lnr += 1
            if not tmp:
              print( "ERR: ### EOF after end of block" )
              return -1
            
            # tmp now contains coords and block number
            b2 = int( tGetNumAfterChar( tmp, "N" ) )
            x2 = tGetNumAfterChar( tmp, "X" )
            y2 = tGetNumAfterChar( tmp, "Y" )

            if b2 is None or x2 is None or y2 is None:
              print( "ERR: ### missing X, Y or N in end of block descriptor:" )
              print( "     \"" + tmp + "\"" )
              return -1
        
            if b2 != b1:        
              print( "ERR: ### number mismatch start/end of block:" )
              print( "     \"" + str(b1) + " <-> " + str(b2) + "\"" )
              return -1
        
            self.Blks.add( b2, (x1,y1), (x2,y2), (lsta,lend) )
            break

 
    return 0

  ###########################################################################
  ### fRearrangeBlocks
  ###
  ###########################################################################
  def fRearrangeBlocks(self):

    if self.fI is None:
      print( "ERR: ### fRearrangeBlocks(): input file not open" )
      return -1

    try:
      self.fI.seek(0)
    except:
      print( "ERR: ### error rewinding file: \"" + self.fI.name + "\"" )
      return -1
  
    # oops ;)
    blk = Blks()
    # This is only a reference. Deleting (pop) the copy (blk.BlkLst) list
    # will also destroy the original (self.Blks.BlkLst)
#    blk.BlkLst=self.Blks.BlkLst 
    blk.BlkLst=self.Blks.getall()

    # current position
    cpos = ( 0.0, 0.0 )
    
    while 1:
      bnum = blk.findNearest( cpos )
      
      if bnum is None:
        break

      self.newOrder.append( bnum )
      
      bt = blk.get( bnum )
      if bt != None:
        cpos = ( bt['epos'][0], bt['epos'][1] )
        blk.pop( bnum )
      else:
        print( "ERR: ### unable to find block number " + str(bnum) )
        return -1

    return 0


  ###########################################################################
  ### fReadLines
  ###
  ###########################################################################
  def fReadLines(self,fI,larea):

    fI.seek(0)
    sout = []

    if larea[0] < 1:
      print( "ERR: ### illegal line number (fReadLines): " + str(larea) )
      return -1
      
    if larea[1] - larea[0] < 1:
      print( "ERR: ### illegal amount of lines (fReadLines): " + str(larea) )
      return -1

    # this is a custom fseek implementation; lol
    for i in range( 0, larea[0] - 1 ):
      tmp = fI.readline()
      if not tmp:
        print( "ERR: ### end of file (fReadLines): " + str(larea) )
        return -1
      
    #  now we are where we want to be; read the lines
    for i in range( larea[0], larea[1] + 1):
      tmp = fI.readline()
      if not tmp:
        print( "ERR: ### end of file (fReadLines): " + str(larea) )
        return -1
      sout.append(tmp)
    
    return sout
    


  ###########################################################################
  ### fComposeBlocks
  ###
  ###########################################################################
  def fComposeBlocks(self):
    
    if self.fI is None:
      print( "ERR: ### fComposeBlocks(): input file not open" )
      return -1

    if self.fB is None:
      print( "ERR: ### fComposeBlocks(): output file not open" )
      return -1

    try:
      self.fI.seek(0)
    except:
      print( "ERR: ### error rewinding file: \""+self.fI.name+"\"" )
      return -1

    # DEBUG
    print( "DBG: SIZE = " + str(self.Blks.count()) )

    # write the header
    bl = self.Blks.get(0)
    if bl is None:
      print( "ERR: ### oops, we lost the header (Blks.get(0))" )
      return -1
    tmp = self.fReadLines( self.fI, bl['larea'] )
    if tmp == -1:
      print( "ERR: ### error reading header (fReadLines)" )
      return -1
    print( "MSG: writing HEADER" )
    for i in tmp:
      self.fB.write(i)

    # continue with all other blocks
    for i in self.newOrder:
      bl = self.Blks.get(i)
      if bl is None:
        print( "ERR: ### unable to find block number " + str(i) )
        return -1
      tmp = self.fReadLines(self.fI,bl['larea'])
      if tmp == -1:
        print( "ERR: ### error reading block (fReadLines) " + str(i) )
        return -1
      print( "MSG: writing BLOCK " + str(i) )
      for i in tmp:
        self.fB.write(i)

    return 0
  
#############################################################################
### main
###
###
###
#############################################################################
if __name__ == "__main__":

  TrigLev = 0.0

  print( "gsort.py " + VERSION )

  if len(sys.argv) < 2:
    print( "USAGE: gsort.py <filename> [<triggerlevel>]" )
    sys.exit(-1)

  fileName = sys.argv[1]
  
  if len(sys.argv) == 3:
    try:
      TrigLev = float(sys.argv[2])
    except:
      print( "ERR: illegal cut level: " + sys.argv[2] )
      sys.exit(-1)
      
  print( "MSG: main" )
  
  gF = GFile()

  if gF.fOpen( fileName ) < 0:
    gF.fClose()
    sys.exit(-1)

  if gF.fSplitIn2Out( TrigLev ) < 0:
    gF.fClose()
    sys.exit(-1)

  if gF.fAnalyzeBlocks() < 0:
    gF.fClose()
    sys.exit(-1)

  if gF.fRearrangeBlocks() < 0:
    gF.fClose()
    sys.exit(-1)

  if gF.fComposeBlocks() < 0:
    gF.fClose()
    sys.exit(-1)


  sys.exit(0)

