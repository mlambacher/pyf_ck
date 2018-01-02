'''
Brainfuck interpreter implemented in Python3.

Based on language description as found in https://esolangs.org/wiki/Brainfuck (9/2017)
As for the key implementation details mentioned there:
  - memory consists of 8bit cells
  - memory cells wrap on under- and overflow
  - negative memory addresses do not exist
  - user input consists either of the first typed character, or the line is buffered (and ended with \x0A)
  - input consisting of an empty line will be interpreted as EOF (\x00)
Marius Lambacher, 2017
'''

import numpy as np

class Interpreter():
  def __init__(self, memorySize=30000, bufferInput=True):
    """
    Creates a new brainfuck interpreter

    :param dataSize: size of the memory field
    :param bufferInput: If True, a line of input is buffered and then delivered to bf character-wise.
                        If the buffer is empty, a new line of input is requested
    """

    self.memorySize = memorySize
    self.bufferInput = bufferInput

    self.debugging = False
    self.running = False

    self.cmdCodes = ('>', '<', '+', '-', '.', ',', '[', ']')      # recognised bf codes

    self.cmds = np.array([], 'U1')                                # contains the current commands to be run
    self.cmdPtr = 0                                               # index of current command

    self.jmps = np.zeros(0, dtype='u4')                           # jumps to be made when encountering parentheses '[...]'
    self.memory = np.zeros(self.memorySize, dtype='u1')           # memory cells
    self.memoryPtr = 0                                            # pointer to current memory cell

    self.bufferedLine = iter([])


  def setDebugging(self, debugging=True):
    self.debugging = debugging

  def init(self):
    """
    Initialises the interpreter; called before running code.

    :return:
    """
    self.cmdPtr = 0                                               # index of current command

    self.jmps = np.zeros(self.cmds.size, dtype='u4')              # jumps to be made when encountering parentheses '[...]'
    addrs = []
    for i, cmd in enumerate(self.cmds):
      if cmd == '[': addrs.append(i)
      elif cmd == ']':
        if len(addrs) == 0: raise SyntaxError('Parentheses in source do not match (too many ]\'s)')
        addr = addrs.pop()
        self.jmps[i] = addr + 1
        self.jmps[addr] = i + 1

    if len(addrs) != 0: raise SyntaxError('Parentheses in source do not match (too many [\'s)')

    self.memory = np.zeros(self.memorySize, dtype='u1')         # memory cells
    self.memoryPtr = 0                                            # pointer to current memory cell

    self.bufferedLine = iter([])


  def load(self, source):
    """
    Load a string containing bf commands to be run.

    :param source: string containing bf commands
    :return:
    """

    cmdStr = ''
    for c in source:
      if c in self.cmdCodes: cmdStr += c

    cmdStr = cmdStr.replace('[-]', '0')
    cmdStr = cmdStr.replace('[+]', '0')

    self.cmds = np.array(list(cmdStr), dtype='U1')
    self.init()


  def run(self):
    """
    Starts the interpreter.
    If debugging mode is active, this will only set running to True

    :return:
    """

    self.init()
    self.running = True

    if not self.debugging:
      while self.running: self._step()


  def step(self):
    """
    If the debugger is running and debugging mode is active, this will perform a single step (command).

    :return:
    """

    if self.running and self.debugging: self._step()

  def _step(self):
    if self.cmdPtr < self.cmds.size:
      cmd = self.cmds[self.cmdPtr]                  # fetching and executing the command

      if   cmd == '[' and self.memory[self.memoryPtr] == 0: self.cmdPtr = self.jmps[self.cmdPtr]
      elif cmd == ']' and self.memory[self.memoryPtr] != 0: self.cmdPtr = self.jmps[self.cmdPtr]

      else:
        if   cmd == '>': self.memoryPtr += 1
        elif cmd == '<': self.memoryPtr -= 1

        elif cmd == '0': self.memory[self.memoryPtr]  = 0
        elif cmd == '+': self.memory[self.memoryPtr] += 1
        elif cmd == '-': self.memory[self.memoryPtr] -= 1

        elif cmd == '.': print(chr(self.memory[self.memoryPtr]), end='')

        elif cmd == ',':
          if not self.bufferInput:
            s = bytearray(input(), 'Latin-1')
            if len(s) > 0: self.memory[self.memoryPtr] = s[0]
            else: self.memory[self.memoryPtr] = 0

          else:
            c = next(self.bufferedLine, None)
            if not c:
              l = bytearray(input(), 'Latin-1')
              if not l: self.bufferedLine = iter(b'\x00')
              else: self.bufferedLine = iter(l + b'\x0A')
              c = next(self.bufferedLine)

            self.memory[self.memoryPtr] = c

        self.cmdPtr += 1                     # will be only increased if not jumping

      # handling exceptions (out of bounds memory, cell wraparound)

      if self.memoryPtr < 0: raise MemoryError('Forbidden memory access: address < 0')
      if self.memoryPtr >= self.memorySize: raise MemoryError('Forbidden memory access: address > memorySize ({}).'.format(self.memorySize))


    else: self.running = False



