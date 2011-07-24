# Copyright (c) 2011, Gabriele Favalessa
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

from collections import defaultdict

import sys

class Ranges(object):
    def __init__(self):
        self.ranges = []

    def __iter__(self):
        return iter(self.ranges)

    def add(self, start, end):
        for i, (s, e) in enumerate(self.ranges):
            if start >= s and start <= e:
                if end <= e:
                    return
                else:
                    self.ranges[i] = s, end
                    return
            elif end >= s and end <= e:
                self.ranges[i] = start, e
                return

        self.ranges.append((start, end))

    def contains(self, addr):
        for start, end in self.ranges:
            if addr >= start and addr <= end:
                return True

        return False

    def size(self, page_size=4096):
        "Rounded to page size"

        min_ = sys.maxint
        max_ = 0

        for s, e in self.ranges:
            min_ = min(min_, s)
            max_ = max(max_, e)

        pages, rem = divmod(max_ - min_, page_size)

        if rem:
            pages += 1

        return pages*page_size

    def to_ppm(self, file_name, width=64):
        size = self.size()

        f = open(file_name, 'wb')

        f.write('P6\n')
        f.write('%s %s\n' % (width, size/width))
        f.write('255\n')

        addr = 0xf000
        offset = 0

        while offset <= size:
            f.write(chr(255 if self.contains(addr+offset) else 0))
            offset += 1

        f.close()

class Memory(object):
    def __init__(self, memory, org):
        self.memory = memory
        self.start = org
        self.end = self.start + len(memory)

        self.executable_ranges = Ranges()
        self.annotations = defaultdict(set)
        self.symbols = {
            0x00: 'VSYNC',
            0x01: 'VBLANK',
            0x02: 'WSYNC',
            0x09: 'COLUBK',
            0x0a: 'CTRLPF',
            0x12: 'RESM0',
            0x16: 'AUDC1',
            0x18: 'AUDF1',
            0x1a: 'AUDV1',
            0x2c: 'CXCLR',
        }

    @classmethod
    def from_file(cls, file_name, org):
        return cls(open(file_name).read(), org)

    def __getitem__(self, addr):
        return ord(self.memory[addr-self.start])

    def get_word(self, addr):
        return (self[addr+1] << 8) + self[addr]

    def add_executable_range(self, start, end):
        self.executable_ranges.add(start, end)

    def is_addr_executable(self, addr):
        return self.executable_ranges.contains(addr)

    def annotate(self, addr, kind):
        self.annotations[addr].add(kind)

    def to_string(self, width=128):
        addr = self.start
        result = ''
        while addr <= self.end:
            marker = '.' if self.executable_ranges.contains(addr) else ' '

            ann = self.annotations[addr]
            if 'J' in ann: # jumped to
                marker = '['
            elif 'R' in ann: # end of execution (RTS or JMP)
                marker = 'T' if 'T' in ann else ']'
            elif 'B' in ann: # branched from
                marker = '/'
            elif 'T' in ann: # branched to
                marker = '\\'
            elif 'r' in ann and 'w' in ann: # read from and written to
                marker = '*'
            elif 'r' in ann: # read from
                marker = 'r'
            elif 'w' in ann: # written to
                marker = 'w'

            # a pound to highlight code ending in data without a JMP or RTS
            # most likely a problem in our tracing algorithm
            if marker == ' ' and result[-1] not in (']', 'T', ' '):
                marker = '#'

            offset = addr - self.start
            if offset and not offset % width:
                result += '\n'

            result += marker

            addr += 1

        return result
