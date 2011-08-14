BEGIN { FS=","; print "from memory import Op"; print "from operands import *"; print "TABLE = {" }
END { print "}" }
# addr_mode=$3
{ printf "    0x%s: Op(mnemonic=\"%s\", src=%s, dst=%s, cycles=%s),\n", $1, $2, $4, $5, $6 }
