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

import memory

SYMBOLS = {
    0x00: 'VSYNC',
    0x01: 'VBLANK',
    0x02: 'WSYNC',
    0x04: 'NUSIZ0',
    0x05: 'NUSIZ1',
    0x06: 'COLUP0',
    0x07: 'COLUP1',
    0x09: 'COLUBK',
    0x0A: 'CTRLPF',
    0x0B: 'REFP0',
    0x0D: 'PF0',
    0x0E: 'PF1',
    0x10: 'RESP0',
    0x11: 'RESP1',
    0x12: 'RESM0',
    0x13: 'RESM1',
    0x14: 'RESBL',
    0x15: 'AUDC0',
    0x16: 'AUDC1',
    0x17: 'AUDF0',
    0x18: 'AUDF1',
    0x19: 'AUDV0',
    0x1A: 'AUDV1',
    0x1B: 'GRP0',
    0x1C: 'GRP1',
    0x1D: 'ENAM0',
    0x1E: 'ENAM1',
    0x1F: 'ENABL',
    0x20: 'HMP0',
    0x21: 'HMP1',
    0x22: 'HMM0',
    0x23: 'HMM1',
    0x24: 'HMBL',
    0x25: 'VDELP0',
    0x26: 'VDELP1',
    0x2A: 'HMOVE',
    0x2C: 'CXCLR',
    0x30: 'CXM0P',
    0x31: 'CXM1P',
    0x33: 'CXP1FB',
    0x34: 'CXM0FB',
    0x35: 'CXM1FB',
    0x37: 'CXPPMM',
    0x3C: 'INPT4',
    0x0280: 'SWCHA',
    0x0282: 'SWCHB',
    0x0284: 'INTIM',
    0x0294: 'TIM1T',
    0x0295: 'TIM8T',
    0x0296: 'TIM64T',
}

class Memory(memory.Memory):
    @classmethod
    def from_file(cls, file_, org=None, symbols=None):
        memory = file_.read()

        if len(memory) != 4096:
            raise ValueError('Expected ROM size of 4096 bytes, found %d bytes' % len(memory))

        if org is None:
            org = 0xf000 & ((ord(memory[-3]) << 8) + ord(memory[-4]))

        syms = SYMBOLS

        if symbols:
            syms.update(symbols)

        return cls(memory, org, symbols=syms)
