'''
Utilities used in the package

Marius Lambacher, 2017
'''

def litStrToInt(s):
  '''
  String to int conversion. Accepts literals '0b' for binary and '0x' for hexadecimal (and none for decimal).

  :param s: string to convert
  :return: converted int
  '''

  try:
    if s[:2] == '0b':
      i = int(s[2:], 2)
    elif s[:2] == '0x':
      i = int(s[2:], 16)
    else:
      i = int(s)

    return i

  except ValueError:
    raise ValueError('Cannot parse to int: {}'.format(s))

