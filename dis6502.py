#! /usr/bin/env python
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

import logging

from collections import namedtuple

import atari2600

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
Line = namedtuple('Line', 'label instruction comment')

def dis_instruction(memory, addr):
    from table import TABLE

    try:
        opcode = TABLE[memory[addr]]
    except KeyError:
        raise ValueError('Unknown opcode %02X at addr %04X' % (memory[addr], addr))

    kwargs = {}

    if addr_mode_in(opcode, M_ADDR, M_ABS, M_ABSX, M_ABSY, M_AIND):
        kwargs['addr'] = memory.get_word(addr+1)
    elif addr_mode_in(opcode, M_IMM):
        kwargs['immed'] = memory[addr+1]
    elif addr_mode_in(opcode, M_INDX, M_INDY, M_REL):
        kwargs['offset'] = memory[addr+1]
    elif addr_mode_in(opcode, M_ZERO, M_ZERX, M_ZERY):
        kwargs['addr'] = memory[addr+1]

    return Instruction(opcode=opcode, src=opcode.src(**kwargs), dst=opcode.dst(**kwargs))

def instrs(memory, addr, check_memory_type=False):
    if addr is None:
        addr = memory.start

    while addr < memory.end:
        if check_memory_type and not memory.is_addr_executable(addr):
            break

        instr = dis_instruction(memory, addr)
        yield addr, instr
        addr += instr.opcode.size

def analyze_executable_memory(memory, starts):
    seen_starts = set()

    while starts:
        next_starts = set()

        for start in starts:
            seen_starts.add(start)

            for addr, instr in instrs(memory, start):
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
                    if memory.has_addr(dest_addr) and not dest_addr in seen_starts:
                        next_starts.add(dest_addr)
                elif instr.opcode.dst == M_PC:
                    if instr.opcode.mnemonic == 'JSR':
                        memory.annotate(instr.src.addr, 'J')
                        if memory.has_addr(instr.src.addr) and not instr.src.addr in seen_starts:
                            next_starts.add(instr.src.addr)
                        memory.add_call(addr, instr.src.addr)
                    elif instr.opcode.mnemonic == 'JMP':
                        memory.annotate(addr, 'R')

                        if instr.opcode.src != M_AIND:
                            memory.annotate(addr, 'M')

                            memory.annotate(instr.src.addr, 'J')
                            if memory.has_addr(instr.src.addr) and not instr.src.addr in seen_starts:
                                next_starts.add(instr.src.addr)
                            memory.add_jump(addr, instr.src.addr)

                        break
                    else:
                        if instr.opcode.mnemonic in ('RTS', 'RTI'):
                            memory.annotate(addr, 'R')

                        break

            memory.add_executable_range(start, addr)

        starts = next_starts

def dis(memory):
    addr = memory.start
    while addr < memory.end:
        instr = None
        for addr, instr in instrs(memory, addr, check_memory_type=True):
            if memory.symbols.has_key(addr):
                print '%s' % memory.symbols[addr],
            elif 'T' in memory.annotations[addr] or 'J' in memory.annotations[addr]:
                print 'L%04X ' % addr,
            else:
                print '      ',

            print instr.opcode.mnemonic, '  ',

            try:
                instr.src.to_string
            except AttributeError:
                src = str(instr.src)
            else:
                src = instr.src.to_string(addr, memory)

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
                    dst = instr.dst.to_string(addr, memory)

                print dst,

            print

            if instr.opcode.mnemonic in ('RTS', 'RTI'):
                print

        if instr:
            addr += instr.opcode.size


        bytes_on_current_line = 0
        while addr < memory.end and not memory.is_addr_executable(addr):
            annotations = memory.annotations[addr]

            if '*' in annotations:
                if bytes_on_current_line > 0:
                    bytes_on_current_line = 0
                    print

                print 'L%04X ' % addr, '.wor', memory.addr_label(memory.get_word(addr))
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

            print '$%02X' % memory[addr],

            addr += 1
            bytes_on_current_line += 1

        if bytes_on_current_line > 0:
            print

def smart_int(s):
    if s.startswith('0x'):
        return int(s[2:], 16)

    if s.startswith('$'):
        return int(s[1:], 16)

    return int(s)

def pair(s):
    symbol, value = s.split('=')

    return symbol, smart_int(value)

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Disassemble an Atari 2600 ROM")

    parser.add_argument('romfile', type=argparse.FileType('r'))
    parser.add_argument('--loglevel', default='warn', action='store', choices=('debug', 'info', 'warn'))
    parser.add_argument('--org', default=0xf000, type=smart_int)
    parser.add_argument('--code', type=smart_int, nargs='*')
    parser.add_argument('--code_ref', type=smart_int, nargs='*')
    parser.add_argument('--symbol', type=pair, nargs='*')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--memory_dump', '-m', default=False, action='store_true')
    group.add_argument('--call_graph', '-c', default=False, action='store_true')
    group.add_argument('--disassemble', '-d', default=False, action='store_true')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    logging.basicConfig(level=getattr(logging, args.loglevel.upper()),
                        format='%(levelname)s:%(message)s')

    memory = atari2600.Memory.from_file(args.romfile)

    if args.symbol:
        for symbol, value in args.symbol:
            memory.add_symbol(value, symbol)

    logging.info('Loaded memory %r' % memory)

    code_refs = [memory.end - 4]
    if args.code_ref:
        code_refs.extend(args.code_ref)

    starts = []
    for code_ref in code_refs:
        memory.annotate(code_ref, '*')
        starts.append(memory.get_word(code_ref))

    logging.info('Automatically found and supplied starts are %r' % map(hex, starts))

    if args.code:
        starts.extend(args.code)

    memory.add_symbol(starts[0], 'START')
    for start in starts[1:]:
        memory.add_symbol(start, 'L%04X' % start)

    analyze_executable_memory(memory, starts)

    if args.memory_dump:
        print memory.to_string()

    if args.disassemble:
        for value, symbol in memory.symbols.items():
            if value < memory.start:
                print "%s = $%04X" % (symbol, value)

        print "       * = $%04X" % memory.start
        print

        print '    code'

        dis(memory)

    if args.call_graph:
        memory.call_graph(*starts)
