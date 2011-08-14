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
import sys

import atari2600

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
    parser.add_argument('--org', default=None, type=smart_int)
    parser.add_argument('--code', type=smart_int, nargs='*')
    parser.add_argument('--code_ref', type=smart_int, nargs='*')
    parser.add_argument('--symbol', type=pair, nargs='*')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--memory_map', '-m', default=False, action='store_true')
    group.add_argument('--call_graph', '-c', default=False, action='store_true')
    group.add_argument('--disassemble', '-d', default=False, action='store_true')
    group.add_argument('--addr_info', '-a', default=None, type=smart_int)

    return parser.parse_args()

def main():
    args = parse_args()

    logging.basicConfig(level=getattr(logging, args.loglevel.upper()),
                        format='%(levelname)s:%(message)s')

    memory = atari2600.Memory.from_file(args.romfile, args.org)

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

    memory.trace_code(starts)

    if args.memory_map:
        print memory.to_string()

    if args.disassemble:
        for value, symbol in memory.symbols.items():
            if value < memory.start:
                print "%s = $%04X" % (symbol, value)

        print "       * = $%04X" % memory.start
        print

        print '    code'

        memory.dis()

    if args.call_graph:
        memory.call_graph(*starts)

    if args.addr_info:
        addr = args.addr_info
        print hex(addr), memory.addr_label(addr), memory.annotations[addr]

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print e
        sys.exit(1)
    else:
        sys.exit(0)
