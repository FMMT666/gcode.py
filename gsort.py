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
# - Tool change commands are not supported (yet)
# - a lot...


# ASkr, 7/2025:
# - revived for Python 3

# ASkr, 9/2007; v0.2:
# - first tests with hp2xx revealed, that hp2xx uses ";" for comments
#   These lines are now changed to parenthesis-comments

# ASkr, 9/2007, v0.1
# - initial version


import sys
from typing import Optional, TextIO


sVersion ="v0.3"

sHeadSta  = "(*** GS HEADER START)"
sHeadEnd  = "(*** GS HEADER END)"
sSplitSta = "(*** GS BLK START)"
sSplitEnd = "(*** GS BLK END)"

sNumbers  = "01234567890.- "


#############################################################################
### vecLength
###
#############################################################################
def vecLength(p1,p2=None):
  if p2 == None:
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
    if sNumbers.count(i) == 0:
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
    self.BlkLst=[]

    
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
    self.fI:    Optional[TextIO] = None
    self.fO:    Optional[TextIO] = None
    self.fB:    Optional[TextIO] = None
    
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
    print( "MSG: GFile fOpen" )
    try:
      self.fI=open(FileName,"r+t")
    except:
      self.fI=None
    
    if self.fI == None:
      print( "ERR: ### unable to open input file \""+FileName+"\"" )
      return -1
    else:
      print( "MSG: opened input file \""+FileName+"\"" )

    if FileName.count(".") < 1:
      tmp=FileName
    else:
      tmp=FileName[:FileName.rfind(".")]
      
    try:
      self.fO=open(tmp+".1gs","w+t")
    except:
      self.fO=None
    
    if self.fO == None:
      print( "ERR: ### unable to open output file 1: \""+tmp+".1gs"+"\"" )
      return -1
    else:
      print( "MSG: opened output file 1 \""+tmp+".1gs"+"\"" )

    try:
      self.fB=open(tmp+".2gs","w+t")
    except:
      self.fB=None
    
    if self.fB == None:
      print( "ERR: ### unable to open output file 2: \""+tmp+"\"" )
      return -1
    else:
      print( "MSG: opened output file 2 \""+tmp+".2gs"+"\"" )
    
    return 1


  ###########################################################################
  ### fClose
  ###
  ###########################################################################
  def fClose(self):
    print( "MSG: GFile fClose" )
    try:
      if self.fB is not None:
        self.fB.close()
      if self.fO is not None:
        self.fO.close()
      if self.fI is not None:
        self.fI.close()
    except:
      pass


  ###########################################################################
  ### fAnalyzeLine
  ###
  ### return codes:
  ###  -1 -> error
  ###   0 -> no changes to output
  ###   1 -> Tool down
  ###   2 -> Tool up
  ###   3 -> minor fixes to line (use self.nLine for new output!)
  ###########################################################################
  def fAnalyzeLine(self, line, linenr, triglev ):
#    print "MSG: GFile fAnalyzeFile"
    tmp = line
    tmp = tmp.upper()
    tmp = tmp.strip(" \t")
    
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
      print( "     \""+line+"\"" )
      return -1


    # TESTING WARNING TESTING: temporarily allow tool change commands
    # if tmp.count("T") > 0:
    #   print( "ERR: ### tool change not supported:" )
    #   print( "     \""+line+"\"" )
    #   return -1
    if tmp.count("T") > 0:
      print( "MSG: ### tool change not officially supported" )
      print( "     \""+line+"\"" )
      return 0



    if tmp[0]=="G":
      if tmp[1:3]=="91":
        print( "ERR: ### relative mode not supported:" )
        print( "     \""+line+"\"" )
        return -1
    
      # TODO: could be G2 or G3: check for two numbers after the G (in general)
      if tmp[1:3]=="02" or tmp[1:3]=="03":
        print( "ERR: ### arcs not supported:" )
        print( "     \""+line+"\"" )
        return -1

      # TODO: same as for G2, G3; but could be corrected to two digits
      if tmp[1:3] == "00" or tmp[1:3] == "01":
        tmp2 = tmp[3:]
        tmp2 = tmp2.strip(" \t")
        
        cx = tmp2.count("X")
        cy = tmp2.count("Y")
        cz = tmp2.count("Z")
        
        if cx > 0 or cy > 0:
          if cz > 0:
            print( "ERR: ### moving z at same time as x or y is not supported:" )
            print( "     \""+line+"\"" )
            return -1
            
          if cx > 0:
            i = tGetNumAfterChar(tmp2,"X")
            if i == None:
              print( "ERR: ### G00/01 X number error:" ) 
              print( "     \""+line+"\"" )
              return -1
            self.lpos=(i,self.lpos[1])

          if cy > 0:
            i = tGetNumAfterChar(tmp2,"Y")
            if i == None:
              print( "ERR: ### G00/01 Y number error:" )
              print( "     \""+line+"\"" )
              return -1
            self.lpos=(self.lpos[0],i)
        else:
          if cz > 0:
            i = tGetNumAfterChar(tmp2,"Z")
            if i == None:
              print( "ERR: ### G00/01 Z number error:" )
              print( "     \""+line+"\"" )
              return -1
            self.llev = i
            if i < triglev:
              return 1   # tool down
            else:
              return 2   # tool up
          
          else:
            print( "ERR: ### G00/01 command without X, Y or Z:" )
            print( "     \""+line+"\"" )
            return -1

    return 0


  ###########################################################################
  ### fSplitIn2Out
  ###
  ###########################################################################
  def fSplitIn2Out(self,TrigLev):

    lnr=1
    blknr=0

    if self.fO is None:
      print( "ERR: ### fSplitIn2Out(): output file not open" )
      return -1

    if self.fI is None:
      print( "ERR: ### fSplitIn2Out(): input file not open" )
      return -1

    self.fO.write("\n"+sHeadSta+"\n\n")

    while 1:
      tmp = self.fI.readline()
      if not tmp:
        break
        
      # TODO: this methods writes the results to "nLine", which is just baaad; needs fix
      i = self.fAnalyzeLine( tmp, lnr, TrigLev )

      tmp = tmp.rstrip("\r\n")
        
      # an error occured
      if i < 0:
        return -1
        
      # no important stuff in this line
      if i == 0:
        self.fO.write(tmp+"\n")

      # TODO: uses the new line "nLine", which was secretly changed in fAnalyzeLine()
      # some minor changes were applied to the (new) line
      if i == 3:
        self.fO.write( self.nLine + "\n" )
        
      # tool down
      if i == 1:
        blknr += 1
        
        if blknr == 1:
          self.fO.write( "\n" + sHeadEnd + "\n\n" )
        
        print( "MSG: processing Block " + str(blknr) )

        self.fO.write( "\n" + sSplitSta + "\n" )
        self.fO.write( "(*** X" + str(self.lpos[0]) + "  Y" + str(self.lpos[1]) + " N" + str(blknr) + ")" + "\n" )
        self.fO.write( "G00 X" + str(self.lpos[0]) + " Y" + str(self.lpos[1]) + "\n" )
        self.fO.write( tmp + "\n")
        self.sBlks += 1
        self.tPos = "down"
        
      # tool up
      if i == 2:
        self.fO.write( tmp + "\n" )
        if self.sBlks > 0:
          self.fO.write( sSplitEnd + "\n" )
          self.fO.write( "(*** X" + str(self.lpos[0]) + "  Y" + str(self.lpos[1]) + " N" + str(blknr) + ")" + "\n\n" )
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
      if tmp.count( sHeadEnd ) > 0:
        print( "DBG: ADDING HEADER" )
        self.Blks.add( 0, (0,0), (0,0), (1,lnr) )
        
        
      if tmp.count(sSplitSta) > 0:
        lsta = lnr
        tmp = self.fI.readline()
        lnr += 1
        if not tmp:
          print( "ERR: ### EOF after start of block (aka: \"G00 Z<up>\" is missing)" )
          return -1
        
        # tmp now contains coords and block number
        b1 = tGetNumAfterChar( tmp, "N" )
        x1 = tGetNumAfterChar( tmp, "X" )
        y1 = tGetNumAfterChar( tmp, "Y" )
        
        if b1 == None or x1 == None or y1 == None:
          print( "ERR: ### missing X, Y or N in start of block descriptor:" )
          print( "     \""+tmp+"\"" )
          return -1
        
        while 1:
          tmp = self.fI.readline()
          lnr += 1
          if not tmp:
            print( "ERR: ### EOF after start of block (aka: \"G00 Z<up>\" is missing)" )
            return -1
            
          if tmp.count(sSplitSta) > 0:
            print( "ERR: ### got second start of block at line No.:"+str(lnr) )
            return -1
          
          if tmp.count(sSplitEnd) > 0:
            lend = lnr
            tmp = self.fI.readline()
            lnr += 1
            if not tmp:
              print( "ERR: ### EOF after end of block" )
              return -1
            
            # tmp now contains coords and block number
            b2 = tGetNumAfterChar( tmp, "N" )
            x2 = tGetNumAfterChar( tmp, "X" )
            y2 = tGetNumAfterChar( tmp, "Y" )

            if b2 == None or x2 == None or y2 == None:
              print( "ERR: ### missing X, Y or N in end of block descriptor:" )
              print( "     \""+tmp+"\"" )
              return -1
        
            if b2 != b1:        
              print( "ERR: ### number mismatch start/end of block:" )
              print( "     \""+str(b1)+" <-> "+str(b2)+"\"" )
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
      
      if bnum == None:
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
    sout=[]

    if larea[0]<1:
      print( "ERR: ### illegal line number (fReadLines): "+str(larea) )
      return -1
      
    if larea[1]-larea[0] < 1:
      print( "ERR: ### illegal amount of lines (fReadLines): "+str(larea) )
      return -1

    for i in range(0,larea[0]-1):
      tmp=fI.readline()
      if not tmp:
        print( "ERR: ### end of file (fReadLines): "+str(larea) )
        return -1
      
    for i in range(larea[0],larea[1]+1):
      tmp=fI.readline()
      if not tmp:
        print( "ERR: ### end of file (fReadLines): "+str(larea) )
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
    if bl == None:
      print( "ERR: ### ups, we lost the header (Blks.get(0))" )
      return -1
    tmp=self.fReadLines(self.fI,bl['larea'])
    if tmp == -1:
      print( "ERR: ### error reading header (fReadLines)" )
      return -1
    print( "MSG: writing HEADER" )
    for i in tmp:
      self.fB.write(i)

    # continue with all other blocks
    for i in self.newOrder:
      bl = self.Blks.get(i)
      if bl == None:
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

  print( "gsort " + sVersion )

  if len(sys.argv) < 2:
    print( "USAGE: gsort <filename> [<trigger-level>]" )
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

