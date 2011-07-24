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

import unittest

from dis6502 import *

class TestDisassembler(unittest.TestCase):
    def test_nop(self):
        self.assertEqual([Instruction(opcode='NOP', src=M_NONE(), dst=M_NONE())], dis('\xea'))

    def test_two_nops(self):
        nop = Instruction(opcode='NOP', src=M_NONE(), dst=M_NONE())
        self.assertEqual([nop, nop], dis('\xea\xea'))

    def test_addr_mode_accumulator(self):
        self.assertEqual([Instruction(opcode='LSR', src=M_AC(), dst=M_AC())], dis('\x4a'))

if __name__ == '__main__':
    unittest.main()
