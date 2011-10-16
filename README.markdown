## Introduction

The python-dis6502 project provides tools to analyse and disassemble binaries
for the 6502 CPU.

The 6502 is the 8 bit CPU used by many early home computers (e.g. Commodore 64,
Apple ][) and game consoles (e.g. Atari 2600, Nintendo NES).

With the help of python-dis6502 you can:

  - have an high level overview of the content of the ROM: which part are code
    and which are data? Who calls who?

  - disassemble the ROM, generating a listing that can then be studied,
    modified and reassembled back to binary form using one of the supported
    assemblers

## License

python-dis6502 is licensed under the GPLv3.

## Example

    $ dis6502.py -m Dk.bin

## Requirements and installation

python-dis6502 was developed and tested with python 2.7.

## Command line arguments

 - `-h`, `--help`

 - `--loglevel {debug,info,warn}`

### Annotating the addresses and populating the symbol table

 - `--org ORG`

   Set ORG as the address of the first byte of the ROM.  On most architectures
   this address is fixed so you don't need to provide it.

 - `--code [ADDR [ADDR ...]]`

   Annotate one or more addresses as containing executable code.  The tracing
   algorithm will start its job from these addresses.

 - `--code_ref [ADDR [ADDR ...]]`

   Annotate one or more addresses as containing the address of executable code.

 - `--symbol [SYMBOL=VALUE [SYMBOL=VALUE ...]]`

   Add one or more symbols to the symbol table

### Output control

 A few mutually exclusive command line argurments control which kind of output
 will be generated.

 - `--memory_map`, `-m`

   Output an ASCII representation of the content of the ROM.

   Each byte in the ROM is represented by a character, following this table:

   - `.` the address contains code
   - `[` is the destination of a JSR instruction
   - `]` the instruction is an RTS
   - `T` the instruction is a JMP
   - `/` contains branch instruction
   - `\` is the destination of a branch instruction
   - ` ` contains data
   - `r` is read from (i.e. is the source of a load instruction)
   - `w` is written to (i.e. is the destination of a store instruction)
   - `*` is both written to and read from

 - `--call_graph`, `-c`

   Generate the call graph in [dot]() format.

 - `--disassemble`, `-d`

   Generate the disassembly of the ROM

 - `--addr_info ADDR`, `-a ADDR`

   Output what the tracing algorithm has discovered about an address

## Supported architectures

Currently only the atari 2600 is supported. A collection of ROMs for the atari
2600 is available at []()

### Atari 2600

ROMs of 2KB and 4KB are supported.  Symbols for the hardware registers are
preloaded.

ROM origin is set automatically at 0x10000 - sizeof(ROM) i.e. 0xf000 for 2KB
ROMs and 0xe000 for 4KB ROMs.

Code tracing starts at the address contained at 0xfffc (the reset vector).

## Related projects

 - [stella]() -- an atari 2600 emulator
 - [distella]() -- a disassembler for atari 2600 ROMs
 - [Ophis]() -- an assembler for the 6502 CPU
