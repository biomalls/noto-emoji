#!/usr/bin/env python
#
# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import glob
import os
from os import path
import sys

"""Create aliases in target directory.

The target files should not contain the emoji variation selector
codepoint in their names."""

DATA_ROOT = path.dirname(path.abspath(__file__))

def str_to_seq(seq_str):
  return tuple([int(s, 16) for s in seq_str.split('_')])


def seq_to_str(seq):
  return '_'.join('%04x' % cp for cp in seq)


def read_emoji_aliases():
  result = {}

  with open(path.join(DATA_ROOT, 'emoji_aliases.txt'), 'r') as f:
    for line in f:
      ix = line.find('#')
      if (ix > -1):
        line = line[:ix]
      line = line.strip()
      if not line:
        continue
      als, trg = (s.strip() for s in line.split(';'))
      als_seq = tuple([int(x, 16) for x in als.split('_')])
      try:
        trg_seq = tuple([int(x, 16) for x in trg.split('_')])
      except:
        print 'cannot process alias %s -> %s' % (als, trg)
        continue
      result[als_seq] = trg_seq
  return result


def add_aliases(filedir, prefix, ext, replace=False, dry_run=False):
  if not path.isdir(filedir):
    print >> sys.stderr, '%s is not a directory' % filedir
    return

  prefix_len = len(prefix)
  suffix_len = len(ext) + 1
  filenames = [path.basename(f)
               for f in glob.glob(path.join(filedir, '%s*.%s' % (prefix, ext)))]
  seq_to_file = {
      str_to_seq(name[prefix_len:-suffix_len]) : name
      for name in filenames}

  aliases = read_emoji_aliases()
  aliases_to_create = {}
  aliases_to_replace = []
  for als,trg in sorted(aliases.items()):
    if trg not in seq_to_file:
      print >> sys.stderr, 'target %s for %s does not exist' % (
          seq_to_str(trg), seq_to_str(als))
      continue
    if als in seq_to_file:
      if replace:
        aliases_to_replace.append(seq_to_file[als])
      else:
        print >> sys.stderr, 'alias %s exists' % seq_to_str(als)
        continue
    target_file = seq_to_file[trg]
    alias_name = '%s%s.%s' % (prefix, seq_to_str(als), ext)
    aliases_to_create[alias_name] = target_file

  if replace:
    if not dry_run:
      for k in sorted(aliases_to_replace):
        os.remove(path.join(filedir, k))
    print 'replacing %d files' % len(aliases_to_replace)

  for k, v in sorted(aliases_to_create.items()):
    if dry_run:
      msg = 'replace ' if k in aliases_to_replace else ''
      print '%s%s -> %s' % (msg, k, v)
    else:
      try:
        os.symlink(v, path.join(filedir, k))
      except:
        print >> sys.stderr, 'failed to create %s -> %s' % (k, v)
        raise Exception('oops')
  print 'created %d symlinks' % len(aliases_to_create)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-d', '--filedir', help='directory containing files to alias',
      required=True, metavar='dir')
  parser.add_argument(
      '-p', '--prefix', help='file name prefix (default emoji_u)',
      metavar='pfx', default='emoji_u')
  parser.add_argument(
      '-e', '--ext', help='file name extension (default png)',
      choices=['ai', 'png', 'sgv'], default='png')
  parser.add_argument(
      '-r', '--replace', help='replace existing files/aliases',
      action='store_true')
  parser.add_argument(
      '-n', '--dry_run', help='print out aliases to create only',
      action='store_true')
  args = parser.parse_args()

  add_aliases(args.filedir, args.prefix, args.ext, args.replace, args.dry_run)


if __name__ == '__main__':
  main()
