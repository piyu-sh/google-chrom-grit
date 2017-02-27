#!/usr/bin/env python
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''This file contains item formatters for resource_map_header and
resource_map_source files.  A resource map is a mapping between resource names
(string) and the internal resource ID.'''

import os
from functools import partial

from grit import util


def GetFormatter(type):
  if type == 'resource_map_header':
    return _FormatHeader
  if type == 'resource_map_source':
    return partial(_FormatSource, _GetItemName)
  if type == 'resource_file_map_source':
    return partial(_FormatSource, _GetItemPath)


def GetMapName(root):
  '''Get the name of the resource map based on the header file name.  E.g.,
  if our header filename is theme_resources.h, we name our resource map
  kThemeResourcesMap.

  |root| is the grd file root.'''
  outputs = root.GetOutputFiles()
  rc_header_file = None
  for output in outputs:
    if 'rc_header' == output.GetType():
      rc_header_file = output.GetFilename()
  if not rc_header_file:
    raise Exception('unable to find resource header filename')
  filename = os.path.splitext(os.path.split(rc_header_file)[1])[0]
  filename = filename[0].upper() + filename[1:]
  while True:
    pos = filename.find('_')
    if pos == -1 or pos >= len(filename):
      break
    filename = filename[:pos] + filename[pos + 1].upper() + filename[pos + 2:]
  return 'k' + filename


def _FormatHeader(root, lang='en', output_dir='.'):
  '''Create the header file for the resource mapping.  This file just declares
  an array of name/value pairs.'''
  return '''\
// This file is automatically generated by GRIT.  Do not edit.

#include <stddef.h>

#ifndef GRIT_RESOURCE_MAP_STRUCT_
#define GRIT_RESOURCE_MAP_STRUCT_
struct GritResourceMap {
  const char* name;
  int value;
};
#endif // GRIT_RESOURCE_MAP_STRUCT_

extern const GritResourceMap %(map_name)s[];
extern const size_t %(map_name)sSize;
''' % { 'map_name': GetMapName(root) }


def _FormatSourceHeader(root):
  '''Create the header of the C++ source file for the resource mapping.'''
  rc_header_file = None
  map_header_file = None
  for output in root.GetOutputFiles():
    if 'rc_header' == output.GetType():
      rc_header_file = output.GetFilename()
    elif 'resource_map_header' == output.GetType():
      map_header_file = output.GetFilename()
  if not rc_header_file or not map_header_file:
    raise Exception('resource_map_source output type requires '
        'resource_map_header and rc_header outputs')
  return '''\
// This file is automatically generated by GRIT.  Do not edit.

#include "%(map_header_file)s"

#include <stddef.h>

#include "base/macros.h"

#include "%(rc_header_file)s"

const GritResourceMap %(map_name)s[] = {
''' % { 'map_header_file': map_header_file,
        'rc_header_file': rc_header_file,
        'map_name': GetMapName(root),
      }


def _FormatSourceFooter(root):
  # Return the footer text.
  return '''\
};

const size_t %(map_name)sSize = arraysize(%(map_name)s);
''' % { 'map_name': GetMapName(root) }


def _FormatSource(get_key, root, lang, output_dir):
  from grit.format import rc_header
  from grit.node import include, structure, message
  yield _FormatSourceHeader(root)
  tids = rc_header.GetIds(root)
  seen = set()
  active_descendants = [item for item in root.ActiveDescendants()]
  output_all_resource_defines = root.ShouldOutputAllResourceDefines()
  for item in root:
    if not item.IsResourceMapSource():
      continue
    key = get_key(item)
    tid = item.attrs['name']
    if tid not in tids or key in seen:
      continue
    if item.GeneratesResourceMapEntry(output_all_resource_defines,
                                      item in active_descendants):
      seen.add(key)
      yield '  {"%s", %s},\n' % (key, tid)
  yield _FormatSourceFooter(root)


def _GetItemName(item):
  return item.attrs['name']


def _GetItemPath(item):
  return item.GetInputPath().replace("\\", "/")
