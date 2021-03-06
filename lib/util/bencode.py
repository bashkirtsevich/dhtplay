# FreeBencode v0.3.1
# 
# This is a simple bencode/bdecode python module that I wrote because
# I wasn't happy with the license of the official bittorrent one.
# There might be a newer version on my site at allanwirth.com.
# 
# Copyright (C) 2011 by Allan Wirth <allanlw@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# Changelog:
# 0.3.1: Minor code cleanup.
# 0.3: Added support for encoding bools as integers.
# 0.2: Added support for type factories and added documentation.
# 0.1: Initial release.
"""FreeBencode: A simple and free python bencode/bdecode library."""

str_factory = str
int_factory = long
list_factory = list
dict_factory = dict

int_types = [int, long, bool]
str_types = [basestring, buffer]
list_types = [list, tuple]
dict_types = [dict]

class BencodeError(StandardError):
  """Bencode Exception class."""
  pass

def bencode(obj):
  """Bencode an object by trying to guess what type to use.

  The module variables int_types, str_types, list_types and dict_types can
  be changed to change the type guessing behavior. They are passed to
  isinstance to determine to proper encoding function to use."""
  if isinstance(obj, tuple(int_types)):
    return bencode_int(obj)
  elif isinstance(obj, tuple(str_types)):
    return bencode_str(obj)
  elif isinstance(obj, tuple(list_types)):
    return bencode_list(obj)
  elif isinstance(obj, tuple(dict_types)):
    return bencode_dict(obj)
  else:
    raise BencodeError("Cannot bencode object: unrecognized type.")

def bencode_int(obj):
  """Bencode an object as a (long) integer and return the result."""
  return "i{0:-d}e".format(long(obj))

def bencode_str(obj):
  """Bencode an object as a string and return the result."""
  return "{0:d}:{1:s}".format(len(obj), str(obj))

def bencode_list(obj):
  """Bencode a sequence object as a list and return the result."""
  return "l{0:s}e".format("".join((bencode(x) for x in obj)))

def bencode_dict(obj):
  """Bencode a mapping object as a dictionary and return the result.

  All keys are cast to strings, per BEP 0001. The object must
  provide a keys method."""
  try:
    keys = [str(k) for k in obj.keys()]
  except AttributeError:
    raise BencodeError("Could not bencode object: no keys method.")
  keys.sort()
  return "d{0:s}e".format("".join(
                              (bencode_str(k)+bencode(obj[k]) for k in keys)))

def bdecode(string):
  """Bdecode a string and return the result and any leftover data.

  The return value is a tuple containing a native python representation of the
  first bencoded object seen and a string containing any leftover data from
  the end. See the functions bdecode_str, bdecode_int, bdecode_list and
  bdecode_dict for information on customizing the types used during
  decoding."""
  if len(string) == 0:
    raise BencodeError("Invalid bencoded object: empty.")
  char = string[0]
  if char == 'i':
    return bdecode_int(string)
  elif char == 'l':
    return bdecode_list(string)
  elif char == 'd':
    return bdecode_dict(string)
  elif char.isdigit():
    return bdecode_str(string)
  else:
    raise BencodeError("Invalid bencoded object: no type indicator.")

def bdecode_int(string, factory=None):
  """Bdecode an integer and return the result and any leftovers.

  The optional factory param is used as a function that takes a string
  and returns an integer. By default it is set to the builtin long(), but
  other useful functionality could be achieved by setting it to something
  else like float() or str(). The default is taken from the module variable
  int_factory."""
  if factory is None:
    factory = int_factory
  if len(string) <= 2 or string[0] != 'i':
    raise BencodeError("Invalid bencoded int: string does not start with i.")
  parts = string.partition("e")
  if not parts[2]:
    raise BencodeError("Invalid bencoded int: string does not terminate.")
  return factory(parts[0][1:]), parts[2]

def bdecode_str(string, factory=None):
  """Bdecode a string and return the result and any leftovers.

  The option factory param is used as a function that takes a string
  and returns a string. By default it is the builtin str function but other
  useful functionality could be achieved by using other functions like
  buffer() or unicode(). The default value is taken from the module variable
  str_factory."""
  if factory is None:
    factory = str_factory
  parts = string.partition(":")
  if not parts[2]:
    raise BencodeError("Invalid bencoded string: string does not contain ':'.")
  try:
    length = int(parts[0])
  except ValueError:
    raise BencodeError("Invalid bencoded string: string length not an integer.")
  if length < 0:
    raise BencodeError("Invalid bencoded string: negative length.")
  elif len(parts[2]) < length :
    raise BencodeError("Invalid bencoded string: Too long length.")
  return factory(parts[2][0:length]), parts[2][length:]

def bdecode_list(string, factory=None):
  """Bdecode a list and return the result and any leftovers.

  The option factory param is used as a function that takes a list and
  returns a list. By default this function is list() but other potentially
  useful functions include set() and tuple(). The default value of this
  function is taken from the module variable list_factory."""
  if factory is None:
    factory = list_factory
  if string[0] != 'l':
    raise BencodeError("Invalid bencoded list: string does not start with 'l'.")
  leftovers = string[1:]
  result = []
  while leftovers and leftovers[0] != 'e':
    res = bdecode(leftovers)
    result.append(res[0])
    leftovers = res[1]
  if not leftovers:
    raise BencodeError("Invalid bencoded list: did not terminate with 'e'.")
  return factory(result), leftovers[1:]

def bdecode_dict(string, factory=None):
  """Bdecode a dict and return the result and any leftover data.

  The optional factory param is used to create the dictionary from a
  dictionary. By default this function is the builtin dict. A user-made
  mapping might be the only useful replacement. The default is taken from the
  dict_factory module variable."""
  if factory is None:
    factory = dict_factory
  if string[0] != 'd':
    raise BencodeError("Invalid bencoded dict: string does not start with 'd'.")
  try:
    items, leftovers = bdecode_list('l'+string[1:])
  except BencodeError as err:
    raise BencodeError(
            "Error while decoding dict items as list:\"{0}\"".format(err))
  result = {}
  if len(items)%2 != 0:
    raise BencodeError("Invalid bencoded dict: odd number of items.")
  for i in range(0, len(items), 2):
    result[items[i]] = items[i+1]
  return factory(result), leftovers
