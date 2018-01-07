"""
Macro definitions for the Brainfuck Assembly Language (BFAL)

Macros are simple functions to generate or manipulate brainfuck commands.
They are highly dependent on each other, generate more complex functionality.

The MacroContext is used to keep track of the memory pointer's position.
It provides the following neat syntax:

with macros.MacroContext(startPos) as mc:
  mc.atTemp(mc.printText('Hello World!')

  endPos = mc.getCurPos()


Marius Lambacher, 2017
"""


from . import memoryLayout
from .errors import *


class MacroContext():
  def __init__(self, startPos=0, cells=None, temps=None):
    self._curPos = startPos

    if cells is None: self.CELLS = memoryLayout.CELLS
    else: self.CELLS = cells

    if temps is None: self.TEMPS = memoryLayout.TEMPS
    else: self.TEMPS = temps


  def __enter__(self):
    return self

  def __exit__(self, *exc):
    return False

  def getCurPos(self):
    return self._curPos


  def repeat(self, cmds, repeats):
    """
    Takes a command and repeats it
    The commands can be either a string of bf code, or another macro

    :param cmds: command to be repeated
    :param repeats: number of repeats
    :return: bf command
    """

    cmdsOrg = cmds
    if not callable(cmds): cmds = lambda s: cmdsOrg

    if repeats < 0: raise RepeatMacroRepeatsError(repeats)
    else:
      bf = ''
      for i in range(repeats):
        bf += cmds(self)

      return bf



  def moveToPos(self, pos):
    """
    Moves the head to given pos; relative to its current position

    :param pos: position to move to (int)
    :return: brainfuck commands to move the head
    """

    dist = pos - self._curPos
    self._curPos = pos

    if dist < 0: cmdString = '<'
    else: cmdString = '>'

    return self.repeat(cmdString, abs(dist))


  def moveToCell(self, cell):
    """
    Moves the head to given cell by indexing it in CELLS and using moveToPos

    :param cell: cell to move the head to
    :return: brainfuck commands to move the head
    """

    pos = self.CELLS.index(cell)
    return self.moveToPos(pos)


  def atCell(self, cell, cmds):
    """
    Short for moveToCell(cell) + cmds
    The commands can be either a string of bf code, or another macro

    :param cell: cell to execute commands at
    :param cmds: cmds to execute
    :return: brainfuck commands
    """

    cmdsOrg = cmds
    if not callable(cmds): cmds = lambda s: cmdsOrg

    return self.moveToCell(cell) + cmds(self)


  def findTemp(self, cell, direction=1, omit=None):
    """
    Find the temporary cell closest to cell.
    If direction >= 0; it will be the closest temp cell to the right; else to the left.
    omit is a list of cells to be omitted; useful if one needs more temporary cells -> omit the ones already in use

    :param cell: cell to which to find the closest temporary cell
    :param direction: direction in which the cells are searched
    :param omit: list of cells to omit in search
    :return: temporary cell if found, None if none is found
    """

    if not omit: omit = []

    if direction >= 0:
      step = 1
      stop = len(self.CELLS)

    else:
      step = -1
      stop = 0

    index = next((i for i in range(self.CELLS.index(cell)+step, stop, step) if (self.CELLS[i] in self.TEMPS and not self.CELLS[i] in omit)), None)

    if index: return self.CELLS[index]
    else: return None


  def getClosestTemp(self, cell=None, directionCell=None, omit=None):
    """
    Convenience call to findTemp()
    Finds a closest temp cell; closest to cell if given, else to current head position
    If directionCell is given, the temp cell will be searched in its direction; this can reduce the number of head movements
    DirectionCell will be appended to the omits, so one can search in direction of temp cell without further consideration
    If findTemp() does not yield a result, it will search in the reverse direction

    :param cell: cell to which to find the closest temporary cell
    :param directionCell: cell to determine the direction in which the temp cell should be searched for
    :param omit: list of cells to omit in search
    :return: temporary cell if found, else None
    """

    if not cell:
      c = self._curPos
      cell = self.CELLS[c]

    else: c = self.CELLS.index(cell)

    if not directionCell:
      d = c+1
      directionCell = self.CELLS[d]

    else:  d = self.CELLS.index(directionCell)

    direction = d-c

    if not omit: omit = []

    temp = self.findTemp(cell, direction, omit=[directionCell] + omit)
    if not temp: temp = self.findTemp(cell, -direction, omit=[directionCell] + omit)

    return temp


  def moveToTemp(self, **kwargs):
    """
    Move to closest temp cell from current position
    :param kwargs: omit
    :return: brainfuck commands
    """

    return self.moveToCell(self.getClosestTemp(**kwargs))

  def atTemp(self, cmds, **kwargs):
    """
    Will move to closest temp and add cmds
    The commands can be either a string of bf code, or another macro

    :param cmds: commands to execute at temp cell
    :param kwargs: omit
    :return: brainfuck commands
    """
    
    cmdsOrg = cmds
    if not callable(cmds): cmds = lambda s: cmdsOrg

    return self.moveToTemp(**kwargs) + cmds(self)


  def setFromTo(self, fromVal, toVal, dest=None):
    """
    Sets a cell (or current position) from a given value to another; using increment or decrement operations

    :param fromVal: current value of cell
    :param toVal: goal value of cell
    :param dest: cell to set
    :return: brainfuck commands
    """

    diff = toVal - fromVal

    if diff == 0: return ''
    elif diff > 128: diff -= 256
    elif diff < -128: diff += 256

    if diff > 0: return self.inc(dest=dest, val=diff)
    elif diff < 0: return self.dec(dest=dest, val=abs(diff))


  def set(self, dest=None, val=0):
    """
    Set given cell (or current) to val

    :param dest: cell to set
    :param val: value to set the cell to
    :return: brainfuck commands
    """

    if not dest: return '[-]' + self.setFromTo(0, val)
    return self.atCell(cell=dest, cmds='[-]' + self.setFromTo(0, val))


  def inc(self, dest=None, val=1):
    """
    Increment given cell by val
    If no cell is given, increment at current position

    :param dest: cell to incerement
    :param val: value to increment by
    :return: brainfuck commands
    """

    cmds = self.repeat('+', val)

    if not dest: return cmds
    else: return self.atCell(dest, cmds)


  def dec(self, dest=None, val=1):
    """
    Decrement given cell by val
    If no cell is given, increment at current position

    :param dest: cell to decerement
    :param val: value to decrement by
    :return: brainfuck commands
    """

    cmds = self.repeat('-', val)
    if not dest: return cmds
    else: return self.atCell(dest, cmds)


  def loop(self, cmds):
    """
    Enclose cmds by loop start and end
    The commands can be either a string of bf code, or another macro
    
    :param cmds: cmds to enclose
    :return: brainfuck commands
    """
    
    if callable(cmds): cmds = cmds(self)
    return '[{}]'.format(cmds)

  

  def doCellTimes(self, count, cmds, dest=None, destructive=False, **kwargs):
    """
    Repeat cmds at dest as often as determined by the contents of cell count.
    The commands can be either a string of bf code, or another macro

    :param count: cell which contains the number of repeats
    :param cmds: cmds to be repeated
    :param dest: destination to run the commands at (allows for better temp cell search)
    :param destructive: if True, count will be set to 0 (faster, no temps required)
    :param kwargs: omit
    :return: brainfuck commands
    """
    
    
    cmdsOrg = cmds
    if dest is not None: cmds = lambda s: self.atCell(dest, cmdsOrg)
    elif not callable(cmds): cmds = lambda s: cmdsOrg
    
    if destructive:
      bf = self.moveToCell(count) + self.loop('-' + cmds(self) + self.moveToCell(count))

    else:
      if dest is None: temp = self.getClosestTemp(count, **kwargs)
      else: temp = self.getClosestTemp(dest, count, **kwargs)

      bf = self.moveToCell(count) + self.loop('-' + self.atCell(temp, '+') + self.atCell(dest, cmds(self)) + self.moveToCell(count))
      bf += self.moveToCell(temp) + self.loop('-' + self.atCell(count, '+') + self.moveToCell(temp))

    return bf


  def addCell(self, dest, source, **kwargs):
    """
    Add contents of source to dest.

    :param dest: destination to be added to
    :param source: cell to be added to dest
    :param kwargs: omit, destructive
    :return: brainfuck commands
    """

    return self.doCellTimes(source, self.inc(), dest=dest, **kwargs)


  def subCell(self, dest, source, **kwargs):
    """
    Subtract contents of source from dest.

    :param dest: destination to be subtracted from
    :param source: cell to be subtracted from dest
    :param kwargs: omit, destructive
    :return: brainfuck commands
    """

    return self.doCellTimes(source, self.dec(), dest=dest, **kwargs)

  def mulCell(self, dest, a, b, **kwargs):
    """
    Multiply a and b, wirte result into dest

    :param dest: destination to be subtracted from
    :param a: factor 1
    :param b: factor 2
    :param kwargs: omit, destructive
    :return: brainfuck commands
    """

    t = self.getClosestTemp(dest, b)

    if 'omit' in kwargs.keys():
      omit = kwargs['omit']
      omit.append(t)
    else: omit = [t,]

    bf = self.addCell(t, a, omit=omit, destructive=False)
    bf += self.set(dest, 0)
    bf += self.doCellTimes(t, lambda s: s.addCell(dest, b, omit=omit), destructive=True)

    return bf


  def copyCell(self, dest, source, **kwargs):
    """
    Copies content of source to dest

    :param dest: cell to be copied to
    :param source: cell to be copied
    :param kwargs: omit, destructive
    :return: brainfuck commands
    """

    if dest == source: return ''
    else: return self.atCell(dest, '[-]') + self.addCell(dest, source, **kwargs)


  def printText(self, text):
    """
    Prints given text by converting its characters to unicode literals, setting a temp cell to each of them and calling the out command

    :param text: text to be printed
    :return: brainfuck commands
    """

    bf = ''
    cur = 0
    for nxt in bytearray(text.encode('Latin-1').decode('unicode-escape'), 'Latin-1'):
      bf += self.setFromTo(cur, nxt) + '.'
      cur = nxt

    bf += '[-]'

    return bf
  
  def comparison(self, compType, a, b, mode, **kwargs):
    """
    Perform a comparison of given registers
    Mode has to be in ('LT', 'LE', 'GT', 'GE)
    
    :param a: first register to compare
    :param b: second register or value to compare
    :param compType: type of comparison, either 'RR' or 'RV'
    :param mode: comparison mode
    :param kwargs: omit, destructive
    :return: brainfuck commands
    """

    if compType == 'RR' and a == b:   # predetermined if registers are equal
      if mode in ('LT', 'GT'): return self.set('RC', 0)
      if mode in ('LE', 'GE'): return self.set('RC', 1)

    bf = self.set('RC', 1)

    if mode[0] == 'L':
      destA = 'CA'
      destB = 'CB'

    else:                     # switching registers for greater comparisons
      mode = 'L' + mode[1]
      destA = 'CB'
      destB = 'CA'

    bf += self.addCell(destA, a, **kwargs)
    if   compType == 'RR': bf += self.addCell(destB, b, **kwargs)
    elif compType == 'RV': bf += self.inc(destB, b)
    else: raise ComparisonMacroTypeError(compType)

    if mode[1] == 'T': bf += self.inc('CA')   # the test is for CA <= CB; for CA < CB, add 1 to CA

    bf += self.moveToCell('CA') + '\n'
    bf += self.doCellTimes('CA', lambda s: s.ifCB(lambda s: s.inc('RC')) + s.dec('RC') + s.dec('CB'), dest='CB', destructive=True)

    bf += self.set('CB', 0)

    return bf


  def ifCB(self, cmds):
    """
    Execute cmds if CB is not 0

    :param cmds: cmds to be executed
    :return: brainfuck commands
    """

    bf = self.moveToCell('CB')
    if callable(cmds): cmds = cmds(self)

    bf += '[{}]<<[<]'.format(cmds + self.moveToCell('C2'))   # note: this has an undefined position in it
    self._curPos = self.CELLS.index('C0')

    return bf

