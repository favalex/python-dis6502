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

import sys

from collections import defaultdict, namedtuple

from operands import *

Opcode = namedtuple('Opcode', 'mnemonic src dst cycles size')

def addr_mode_in(opcode, *modes):
    if isinstance(opcode, dict):
        src = opcode['src']
        dst = opcode['dst']
    else:
        src = opcode.src
        dst = opcode.dst

    return (src in modes) or (dst in modes)

def Op(**kwargs):
    size = 1

    if addr_mode_in(kwargs, M_ADDR, M_ABS, M_ABSX, M_ABSY, M_AIND):
        size += 2
    elif addr_mode_in(kwargs, M_IMM, M_INDX, M_INDY, M_REL, M_ZERO, M_ZERX, M_ZERY):
        size += 1

    kwargs['size'] = size

    return Opcode(**kwargs)

Instruction = namedtuple('Instruction', 'opcode src dst')

class UnknownOpcodeError(Exception):
    def __str__(self):
        return 'unknown opcode ' + self.message

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

    def has_addr(self, addr):
        return addr >= self.start and addr <= self.end

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
            if size == 2:
                return '$%02X' % addr
            elif '*' in self.annotations[addr-1]:
                return '%s+1' % self.addr_label(addr-1)
            elif self.has_addr(addr):
                return 'L%04X' % addr
            else:
                return '$%04X' % addr

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

    def trace_code(self, starts):
        seen_starts = set()

        while starts:
            next_starts = set()

            for start in starts:
                seen_starts.add(start)

                for addr, instr in self.instrs(start):
                    # memory access
                    if instr.opcode.src in (M_ABS, M_ADDR, M_ABSX, M_ABSY):
                        self.annotate(instr.src.addr, 'r')

                    if instr.opcode.dst in (M_ABS, M_ADDR, M_ABSX, M_ABSY):
                        self.annotate(instr.dst.addr, 'w')

                    # jumps and branches
                    if instr.opcode.src == M_REL:  # branches
                        self.annotate(addr, 'B')
                        dest_addr = addr + instr.opcode.size + instr.src.offset
                        self.annotate(dest_addr, 'T')
                        if self.has_addr(dest_addr) and not dest_addr in seen_starts:
                            next_starts.add(dest_addr)
                    elif instr.opcode.dst == M_PC:
                        if instr.opcode.mnemonic == 'JSR':
                            self.annotate(instr.src.addr, 'J')
                            if self.has_addr(instr.src.addr) and not instr.src.addr in seen_starts:
                                next_starts.add(instr.src.addr)
                            self.add_call(addr, instr.src.addr)
                        elif instr.opcode.mnemonic == 'JMP':
                            self.annotate(addr, 'R')

                            if instr.opcode.src != M_AIND:
                                self.annotate(addr, 'M')

                                self.annotate(instr.src.addr, 'J')
                                if self.has_addr(instr.src.addr) and not instr.src.addr in seen_starts:
                                    next_starts.add(instr.src.addr)
                                self.add_jump(addr, instr.src.addr)

                            break
                        else:
                            if instr.opcode.mnemonic in ('RTS', 'RTI'):
                                self.annotate(addr, 'R')

                            break

                self.add_executable_range(start, addr)

            starts = next_starts

    def dis(self):
        addr = self.start
        while addr < self.end:
            instr = None
            for addr, instr in self.instrs(addr, check_memory_type=True):
                if self.symbols.has_key(addr):
                    print '%s' % self.symbols[addr],
                elif 'T' in self.annotations[addr] or 'J' in self.annotations[addr]:
                    print 'L%04X ' % addr,
                else:
                    print '      ',

                print instr.opcode.mnemonic, '  ',

                try:
                    instr.src.to_string
                except AttributeError:
                    src = str(instr.src)
                else:
                    src = instr.src.to_string(addr, self)

                if src:
                    print src,
                else:
                    if instr.opcode.mnemonic in 'ADC AND ASL BIT CMP CPX CPY DEC EOR INC JMP LDA LDX LDY LSR ORA ROL ROR SBC STA STX STY':
                        stringer = repr
                    else:
                        stringer = str

                    try:
                        instr.dst.to_string
                    except AttributeError:
                        dst = stringer(instr.dst)
                        if dst == 'A':
                            dst = ''
                    else:
                        dst = instr.dst.to_string(addr, self)

                    print dst,

                print

                if instr.opcode.mnemonic in ('RTS', 'RTI'):
                    print

            if instr:
                addr += instr.opcode.size


            bytes_on_current_line = 0
            while addr < self.end and not self.is_addr_executable(addr):
                annotations = self.annotations[addr]

                if '*' in annotations:
                    if bytes_on_current_line > 0:
                        bytes_on_current_line = 0
                        print

                    print 'L%04X ' % addr, '.word', self.addr_label(self.get_word(addr))
                    addr += 2

                    continue

                if 'r' in annotations or 'w' in annotations:
                    if bytes_on_current_line > 0:
                        bytes_on_current_line = 0
                        print

                    print 'L%04X  .byt' % addr,
                else:
                    if bytes_on_current_line > 16:
                        print
                        bytes_on_current_line = 0

                    if bytes_on_current_line == 0:
                        print '       .byt',
                    else:
                        print ',',

                print '$%02X' % self[addr],

                addr += 1
                bytes_on_current_line += 1

            if bytes_on_current_line > 0:
                print

    def dis_instruction(self, addr):
        from table import TABLE

        try:
            opcode = TABLE[self[addr]]
        except KeyError:
            raise UnknownOpcodeError('%02X at addr %04X' % (self[addr], addr))

        kwargs = {}

        if addr_mode_in(opcode, M_ADDR, M_ABS, M_ABSX, M_ABSY, M_AIND):
            kwargs['addr'] = self.get_word(addr+1)
        elif addr_mode_in(opcode, M_IMM):
            kwargs['immed'] = self[addr+1]
        elif addr_mode_in(opcode, M_INDX, M_INDY, M_REL):
            kwargs['offset'] = self[addr+1]
        elif addr_mode_in(opcode, M_ZERO, M_ZERX, M_ZERY):
            kwargs['addr'] = self[addr+1]

        return Instruction(opcode=opcode, src=opcode.src(**kwargs), dst=opcode.dst(**kwargs))

    def instrs(self, addr, check_memory_type=False):
        if addr is None:
            addr = self.start

        while addr < self.end:
            if check_memory_type and not self.is_addr_executable(addr):
                break

            instr = self.dis_instruction(addr)
            yield addr, instr
            addr += instr.opcode.size
