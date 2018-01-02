'''
Utilities used in the package

Marius Lambacher, 2017
'''

def litStrToInt(s):
  '''
  String to int conversion. Accepts literals '0b' for binary, '0x' for hexadecimal and '0o' for octal (and none for decimal).

  :param s: string to convert
  :return: converted int
  '''

  try:
    if s[:2].lower() == '0b': i = int(s[2:], 2)
    elif s[:2].lower() == '0x': i = int(s[2:], 16)
    elif s[:2].lower() == '0o': i = int(s[2:], 8)
    else: i = int(s)

    return i

  except ValueError: raise ValueError('Cannot parse to int: {}'.format(s))

