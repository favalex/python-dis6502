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

from memory import Memory
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

def dis_instruction(memory, addr):
    from table import TABLE

    opcode = TABLE[memory[addr]]

    kwargs = {}

    if addr_mode_in(opcode, M_ADDR, M_ABS, M_ABSX, M_ABSY):
        kwargs['addr'] = memory.get_word(addr+1)
    elif addr_mode_in(opcode, M_IMM):
        kwargs['immed'] = memory[addr+1]
    elif addr_mode_in(opcode, M_INDX, M_INDY, M_REL):
        kwargs['offset'] = memory[addr+1]
    elif addr_mode_in(opcode, M_ZERO, M_ZERX, M_ZERY):
        kwargs['addr'] = memory[addr+1]

    return Instruction(opcode=opcode, src=opcode.src(**kwargs), dst=opcode.dst(**kwargs))

def dump(bytes_):
    return ' '.join(hex(ord(byte)) for byte in bytes_)

def instrs(memory, addr, check_memory_type=False):
    if addr is None:
        addr = memory.start

    while addr < memory.end:
        if check_memory_type and not memory.is_addr_executable(addr):
            break

        instr = dis_instruction(memory, addr)
        yield addr, instr
        addr += instr.opcode.size

def analyze_executable_memory(memory, start_addr):
    to_be_explored = []

    for addr, instr in instrs(memory, start_addr):
        # memory access
        if instr.opcode.src in (M_ADDR, M_ABSX, M_ABSY):
            memory.annotate(instr.src.addr, 'r')

        if instr.opcode.dst in (M_ADDR, M_ABSX, M_ABSY):
            memory.annotate(instr.dst.addr, 'w')

        # jumps and branches
        if instr.opcode.src == M_REL:  # branches
            memory.annotate(addr, 'B')
            dest_addr = addr + instr.opcode.size + instr.src.offset
            memory.annotate(dest_addr, 'T')
            to_be_explored.append(dest_addr)
        elif instr.opcode.dst == M_PC:
            if instr.opcode.mnemonic == 'JSR':
                memory.annotate(instr.src.addr, 'J')
                to_be_explored.append(instr.src.addr)
            elif instr.opcode.mnemonic == 'JMP':
                memory.annotate(addr, 'R')
                memory.annotate(instr.src.addr, 'J')
                to_be_explored.append(instr.src.addr)
                break
            else:
                if instr.opcode.mnemonic in ('RTS', 'RTI'):
                    memory.annotate(addr, 'R')

                break

    memory.add_executable_range(start_addr, addr)

    for dest_addr in to_be_explored:
        if not memory.is_addr_executable(dest_addr):
            analyze_executable_memory(memory, dest_addr)

def dis(memory, addr):
    for addr, instr in instrs(memory, addr, check_memory_type=True):
        if 'T' in memory.annotations[addr] or 'J' in memory.annotations[addr]:
            print 'L%s:' % hex(addr)[2:].upper(),
        else:
            print '      ',

        print instr.opcode.mnemonic, '  ',

        src = str(instr.src)
        if src:
            print src,

        print instr.dst,

        print

        if instr.opcode.mnemonic in ('RTS', 'RTI'):
            print

if __name__ == '__main__':
    import sys

    memory = Memory.from_file(sys.argv[1], 0xf000)
    analyze_executable_memory(memory, 0xf000)

    print memory.to_string()

    dis(memory, 0xf000)
