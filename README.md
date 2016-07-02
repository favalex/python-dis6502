Disassembler for 6502 ROMs. Currently targeting Atari 2600, but can be extended to support other similar machines.

It works by tracing the code from some supplied entry points, trying to figure out if a memory location contains code or data. 

# Usage

You can pass what you already know about the layout of the ROM using command line parameters:

## --org ORG

Address of the ROM.

## --code [CODE [CODE ...]]

Address of entry point(s). dis6502 will trace the code starting from those addresses.

## --code_ref [CODE_REF [CODE_REF ...]]

Indirect address of entry point(s).

## --symbol [SYMBOL [SYMBOL ...]]

Label for an address. E.g. `--symbol BEEP=$f100`.

It has four output modes:

## ASCII memory map of the ROM

char | meaning
------------------------------
 [   | start of routine
 ]   | end of routine
 /   | branch instruction
 \   | destination of a branch
 .   | code
 r   | data, read from
 w   | data, written to
 *   | data, read and written


````
$ ./dis6502.py --org 0xf000 --memory_map Combat.bin
F000: ....................[..........................]  [................................][.......\../................\../...../......
F080: ...[......................................................../.............]  \.................\............/.../.\.\...........
F100: ......../...\./.....\............/.../.\.\.../.............\...../....................][.../................../.\......./...../.
F180: ..\...../...../...\..../.../.\./...[.\.............../.../.\............/.../...\............/...................T[.\...........
F200: ................./.][./.../.\.\...........\.............../..\.../..............\/.][................/......../...../.....\.[...
F280: ........../.../.\./.../.\.../...\.../...T[............./...\........../....\\.../...\../.][..../...../............../....\./....
F300: [..........T\.........\./...\...................../.../.\./.\............\./........../.\..................\............/.]\../.
F380: [./.../.....\./........./.../.../.\./.../.../.[.....\.]\./.../.\..]  \..]  [./........]  \....[.../.../.../.../.\.\./.\.........
F400: .............]  [./.............]\................\/.../.\.........][.[./.../...../.\................................]\./.]  \./
F480: ...../.....\./.....]  \./.../.................../...T  \./..././...]  \.[....]  \...[.[./.../.\.../....\.../.\./..././.\.\......
F500: .[/.]  T[......[....................][..................../.../.../.\.\.\...../.......\..........................][.../...\.....
F580: ................................./.....\...\............../.][.\../.]r                                                 r        
F600:                                        r               r                                                                        
F680:                                                                                                                                 
F700:                r  r                                r  r  r                                   rr      r                          
F780:                                                                       r  r  r   r   r   r                                     r 
F800:  
````

## Call graph

The output can be feed into [dot](https://en.wikipedia.org/wiki/DOT_(graph_description_language)) to generate an actual picture (e.g. `dot -T png Combat.dot >Combat.png`).


````
$ ./dis6502.py --org 0xf000 --call_graph Combat.bin
digraph G {
  START -> LF5BD ;
  START -> LF1A3 ;
  START -> LF032 ;
  START -> LF157 ;
  START -> LF572 ;
  START -> LF2DA ;
…
````

## Information about a specific memory address

````
$ ./dis6502.py --org 0xf000 --addr_info 0xf083 Combat.bin
0xf083 LF083 set(['J', 'r'])
````

## Disassembly

The output can be reassembled e.g. by [xa](http://www.floodgap.com/retrotech/xa/)

````
$ ./dis6502.py --org 0xf000 --disassemble Combat.bin
…
TIM1T = $0294
TIM8T = $0295
       * = $F000

    code
START SEI    
       CLD    
       LDX    #$FF
       TXS    
       LDX    #$5D
       JSR    LF5BD
       LDA    #$10
       STA    $0283
       STA    $88
       JSR    LF1A3
LF014  JSR    LF032
       JSR    LF157
…
````
