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
        # merge the new range with existing ones, if possible
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

class Memory(object):
    def __init__(self, memory, org, symbols=None):
        self.memory = memory
        self.start = org
        self.end = self.start + len(memory)

        self.executable_ranges = Ranges()
        self.annotations = defaultdict(set)
        self.calls = {}
        self.jumps = {}

        if symbols is None:
            self.symbols = {}
        else:
            self.symbols = symbols.copy()

    @classmethod
    def from_file(cls, file_, org, symbols=None):
        return cls(file_.read(), org, symbols=symbols)

    def __repr__(self):
        return '<Memory start=%X end=%X, symbols=%d>' % (self.start, self.end, len(self.symbols))

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

    def addr_is(self, addr, *kind):
        return set(kind) & self.annotations[addr]

    def add_symbol(self, addr, symbol):
        self.symbols[addr] = symbol

    def add_call(self, from_addr, to_addr):
        self.calls[from_addr] = to_addr

    def add_jump(self, from_addr, to_addr):
        self.jumps[from_addr] = to_addr

    def addr_label(self, addr, size=4):
        try:
            return self.symbols[addr]
        except KeyError:
            annotations = self.annotations[addr]
            fmt = '%%0%dX' % size
            if 'J' in  annotations or 'T' in annotations:
                return 'L' + (fmt % addr)
            else:
                return '$' + (fmt % addr)

    def to_string(self, width=128):
        addr = self.start
        result = '%4X: ' % addr
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
            if result and marker == ' ' and result[-1] not in (']', 'T', ' ', 'r', 'w'):
                marker = '#'

            offset = addr - self.start
            if offset and not offset % width:
                result += '\n'
                result += '%04X: ' % addr

            result += marker

            addr += 1

        return result

    def routine_of_addr(self, addr):
        while addr >= self.start:
            if self.addr_label(addr) == 'START':
                return 'START'

            if self.addr_is(addr, 'J'):
                return self.addr_label(addr)

            addr -= 1

        return 'UNKNOWN'

    def call_graph(self, *starts):
        print 'digraph G {'

        seen_starts = set()

        while starts:
            next_starts = set()

            for start in starts:
                seen_starts.add(start)

                start_label = self.addr_label(start)
                addr = start
                while not self.addr_is(addr, 'R'):
                    if self.calls.has_key(addr):
                        dest_addr = self.calls[addr]
                        if not dest_addr in seen_starts:
                            next_starts.add(dest_addr)
                        print ' ', start_label, '->', self.addr_label(dest_addr), ';'

                    addr += 1

                if self.addr_is(addr, 'M'):
                    dest_addr = self.jumps[addr]
                    if not dest_addr in seen_starts:
                        next_starts.add(dest_addr)
                    print ' ', start_label, '->', self.addr_label(dest_addr), ';'

            starts = next_starts

        print '}'
