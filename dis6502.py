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

from collections import namedtuple

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

    if addr_mode_in(kwargs, M_ADDR, M_ABS, M_ABSX, M_ABSY):
        size += 2
    elif addr_mode_in(kwargs, M_IMM, M_INDX, M_INDY, M_REL, M_ZERO, M_ZERX, M_ZERY):
        size += 1

    kwargs['size'] = size

    return Opcode(**kwargs)

Instruction = namedtuple('Instruction', 'opcode src dst')
Line = namedtuple('Line', 'label instruction comment')

def dis_instruction(opcode, bytes_, ip=0):
    kwargs = {}

    if addr_mode_in(opcode, M_ADDR, M_ABS, M_ABSX, M_ABSY):
        kwargs['addr'] = (ord(bytes_[ip+2]) << 8) + ord(bytes_[ip+1])
    elif addr_mode_in(opcode, M_IMM):
        kwargs['immed'] = ord(bytes_[ip+1])
    elif addr_mode_in(opcode, M_INDX, M_INDY, M_REL):
        kwargs['offset'] = ord(bytes_[ip+1])
    elif addr_mode_in(opcode, M_ZERO, M_ZERX, M_ZERY):
        kwargs['addr'] = ord(bytes_[ip+1])

    return Instruction(opcode=opcode, src=opcode.src(**kwargs), dst=opcode.dst(**kwargs))

def dump(bytes_):
    return ' '.join(hex(ord(byte)) for byte in bytes_)

def instrs(bytes_, org=0xf000, start=None):
    from table import TABLE

    if start is None:
        start = org

    offset = start - org
    while offset < len(bytes_):
        opcode = TABLE[ord(bytes_[offset])]
        yield org+offset, dis_instruction(opcode, bytes_, offset)
        offset += opcode.size

class Ranges(object):
    def __init__(self):
        self.ranges = []

    def __iter__(self):
        return iter(self.ranges)

    def add(self, start, end):
        self.ranges.append((start, end))  # FIXME merge

    def contains(self, addr):
        for start, end in self.ranges:
            if addr >= start and addr <= end:
                return True

        return False

# TODO encapsulate bytes in a class bytes+org, and accessors with addr instead of/together with offsets
# TODO class to hold ranges
# operations add a range (performs merge)
#            operator in
def follow_execution_path(bytes_, org=0xf000, start=0xf000, executable_ranges=None):
    if executable_ranges is None:
        executable_ranges = Ranges()

    to_be_explored = []

    # TODO mark addresses as jump destinations

    for addr, instr in instrs(bytes_, org=org, start=start):
        if instr.opcode.src == M_REL:  # branches
            to_be_explored.append(addr + instr.opcode.size + instr.src.offset)
        elif instr.opcode.dst == M_PC:
            if instr.opcode.mnemonic == 'JSR':
                to_be_explored.append(instr.src.addr)
            elif instr.opcode.mnemonic == 'JMP':
                to_be_explored.append(instr.src.addr)
                break
            else:
                break

    executable_ranges.add(start, addr)

    # print instr.opcode.mnemonic, hex(instr.src.addr), executable_ranges.contains(instr.src.addr)

    for dest_addr in to_be_explored:
        if not executable_ranges.contains(dest_addr):
            follow_execution_path(bytes_, org=org, start=dest_addr, executable_ranges=executable_ranges)

    return executable_ranges

def dis(bytes_, org=0xf000):
    for addr, instr in instrs(bytes_, org=org):
        offset = addr - org
        bs = bytes_[offset:offset+instr.opcode.size] # FIXME avoid copying
        yield addr, bs, instr

if __name__ == '__main__':
    import sys

    for range_ in follow_execution_path(open(sys.argv[1]).read()):
        print map(hex, range_)

    # for addr, bytes_, instr in dis(open(sys.argv[1]).read(101)):
    #     print hex(addr), dump(bytes_), instr
