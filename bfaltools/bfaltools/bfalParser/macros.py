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


from .memoryLayout import CELLS, TEMPS
from .errors import *
#from contextlib import ContextDecorator


class MacroContext():#ContextDecorator):
  def __init__(self, startPos):
    self._curPos = startPos

  def __enter__(self):
    return self

  def __exit__(self, *exc):
    return False

  def getCurPos(self):
    return self._curPos


  def repeat(self, cmds, repeats):
    """
    Takes a command and repeats it

    :param cmds: command to be repeated
    :param repeats: number of repeats
    :return: bf command
    """

    if repeats < 0: raise RuntimeError('Internal error, trying to repeat a negative number of times')
    else: return cmds * repeats



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

    pos = CELLS.index(cell)
    return self.moveToPos(pos)


  def atCell(self, cell, cmds=''):
    """
    Short for moveToCell(cell) + cmds

    :param cell: cell to execute commands at
    :param cmds: cmds to execute
    :return: brainfuck commands
    """

    return self.moveToCell(cell) + cmds


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
      stop = len(CELLS)

    else:
      step = -1
      stop = 0

    index = next((i for i in range(CELLS.index(cell)+step, stop, step) if (CELLS[i] in TEMPS and not CELLS[i] in omit)), None)

    if index: return CELLS[index]
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
      cell = CELLS[c]

    else: c = CELLS.index(cell)

    if not directionCell:
      d = c+1
      directionCell = CELLS[d]

    else:  d = CELLS.index(directionCell)

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

  def atTemp(self, cmds='', **kwargs):
    """
    Will move to closest temp and add cmds

    :param cmds: commands to execute at temp cell
    :param kwargs: omit
    :return: brainfuck commands
    """

    return self.moveToTemp(**kwargs) + cmds


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





  def loop(self, cmds=''):
    """
    Enclose cmds by loop start and end
    :param cmds: cmds to enclose
    :return: brainfuck commands
    """

    return '[{}]'.format(cmds)

  

  def doCellTimes(self, count, dest, cmds='', destructive=False, **kwargs):
    """
    Repeat cmds at dest as often as determined by the contents of cell count.

    :param count: cell which contains the number of repeats
    :param dest: cell to run the commands at
    :param cmds: cmds to be repeated
    :param destructive: if True, count will be set to 0 (faster, no temps required)
    :param kwargs: omit
    :return: brainfuck commands
    """

    if destructive:
      bf = self.moveToCell(count) + self.loop('-' + self.atCell(dest, cmds) + self.moveToCell(count))

    else:
      temp = self.getClosestTemp(dest, count, **kwargs)

      bf = self.moveToCell(count) + self.loop('-' + self.atCell(temp, '+') + self.atCell(dest, cmds) + self.moveToCell(count))
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

    return self.doCellTimes(source, dest, self.inc(), **kwargs)


  def subCell(self, dest, source, **kwargs):
    """
    Subtractcontents of source from dest.

    :param dest: destination to be subtracted from
    :param source: cell to be subtracted from dest
    :param kwargs: omit, destructive
    :return: brainfuck commands
    """

    return self.doCellTimes(source, dest, self.dec(), **kwargs)


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

    cmds = ''
    cur = 0
    for nxt in bytearray(text.encode('Latin-1').decode('unicode-escape'), 'Latin-1'):
      cmds += self.setFromTo(cur, nxt) + '.'
      cur = nxt

    cmds += '[-]'

    return cmds
  
  def comparison(self, compType, a, b, mode, **kwargs):
    """
    Perform a comparison of given registers
    Mode has to be in ('LT', 'LE', 'GT', 'GE)
    
    :param a: first register to compare
    :param b: second register or value to compare
    :param compType: type of comparison, either 'RR' or 'RV'
    :param mode: comparison mode
    :param kwargs: omit, destructive
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

    bf += self.moveToCell('CA')
    bf += '[ <[<<<<+>>>] << [<] <->>>>->-]'  # pure magic! - not, but has an undefined position in it...
    # here, the pointer is at CA again - as before, therefore the magic bit is transparent to the MacroContext

    bf += self.set('CB', 0)

    return bf


    
    
