from bitcoin.main import *
from bitcoin.bci import *
from bitcoin.transaction import *
from bitcoin.pyspecials import safe_hexlify, safe_unhexlify, st, by

import re
from pprint import pprint as pp

def ishex(s):
    return set(s).issubset(set('0123456789abcdefABCDEF'))

def isbin(s):
    if not (is_python2 or isinstance(s, bytes)):
        return False
    if len(s)%2 == 1:
        return True
    try: 
        unhexed = safe_unhexlify(s)
    except TypeError: 
        return True
    return True

def satoshi_to_btc(val):
    return (float(val) / 1e8)

def btc_to_satoshi(val):
    return int(val*1e8 + 0.5)

# Return the address and btc_amount from the parsed uri_string.
# If either of address or amount is not found that particular
# return value is None.
def parse_bitcoin_uri(uri_string):
    import urlparse
    parsed = urlparse.urlparse(uri_string)
    if parsed.scheme != 'bitcoin':
        return None, None
    elif parsed.scheme == 'bitcoin':
        addr = parsed.path
        queries = urlparse.parse_qs(parsed.query)
        if 'amount' not in queries:       btc_amount = None
        elif len(queries['amount']) == 1: btc_amount = float(queries['amount'][0])
        else:                             btc_amount = None
        return addr, btc_amount


OPCODE_LIST = [
  ("OP_0", 0),
  ("OP_PUSHDATA1", 76),
  ("OP_PUSHDATA2", 77),
  ("OP_PUSHDATA4", 78),
  ("OP_1NEGATE", 79),
  ("OP_RESERVED", 80),
  ("OP_1", 81),
  ("OP_2", 82),
  ("OP_3", 83),
  ("OP_4", 84),
  ("OP_5", 85),
  ("OP_6", 86),
  ("OP_7", 87),
  ("OP_8", 88),
  ("OP_9", 89),
  ("OP_10", 90),
  ("OP_11", 91),
  ("OP_12", 92),
  ("OP_13", 93),
  ("OP_14", 94),
  ("OP_15", 95),
  ("OP_16", 96),
  ("OP_NOP", 97),
  ("OP_VER", 98),
  ("OP_IF", 99),
  ("OP_NOTIF", 100),
  ("OP_VERIF", 101),
  ("OP_VERNOTIF", 102),
  ("OP_ELSE", 103),
  ("OP_ENDIF", 104),
  ("OP_VERIFY", 105),
  ("OP_RETURN", 106),
  ("OP_TOALTSTACK", 107),
  ("OP_FROMALTSTACK", 108),
  ("OP_2DROP", 109),
  ("OP_2DUP", 110),
  ("OP_3DUP", 111),
  ("OP_2OVER", 112),
  ("OP_2ROT", 113),
  ("OP_2SWAP", 114),
  ("OP_IFDUP", 115),
  ("OP_DEPTH", 116),
  ("OP_DROP", 117),
  ("OP_DUP", 118),
  ("OP_NIP", 119),
  ("OP_OVER", 120),
  ("OP_PICK", 121),
  ("OP_ROLL", 122),
  ("OP_ROT", 123),
  ("OP_SWAP", 124),
  ("OP_TUCK", 125),
  ("OP_CAT", 126),
  ("OP_SUBSTR", 127),
  ("OP_LEFT", 128),
  ("OP_RIGHT", 129),
  ("OP_SIZE", 130),
  ("OP_INVERT", 131),
  ("OP_AND", 132),
  ("OP_OR", 133),
  ("OP_XOR", 134),
  ("OP_EQUAL", 135),
  ("OP_EQUALVERIFY", 136),
  ("OP_RESERVED1", 137),
  ("OP_RESERVED2", 138),
  ("OP_1ADD", 139),
  ("OP_1SUB", 140),
  ("OP_2MUL", 141),
  ("OP_2DIV", 142),
  ("OP_NEGATE", 143),
  ("OP_ABS", 144),
  ("OP_NOT", 145),
  ("OP_0NOTEQUAL", 146),
  ("OP_ADD", 147),
  ("OP_SUB", 148),
  ("OP_MUL", 149),
  ("OP_DIV", 150),
  ("OP_MOD", 151),
  ("OP_LSHIFT", 152),
  ("OP_RSHIFT", 153),
  ("OP_BOOLAND", 154),
  ("OP_BOOLOR", 155),
  ("OP_NUMEQUAL", 156),
  ("OP_NUMEQUALVERIFY", 157),
  ("OP_NUMNOTEQUAL", 158),
  ("OP_LESSTHAN", 159),
  ("OP_GREATERTHAN", 160),
  ("OP_LESSTHANOREQUAL", 161),
  ("OP_GREATERTHANOREQUAL", 162),
  ("OP_MIN", 163),
  ("OP_MAX", 164),
  ("OP_WITHIN", 165),
  ("OP_RIPEMD160", 166),
  ("OP_SHA1", 167),
  ("OP_SHA256", 168),
  ("OP_HASH160", 169),
  ("OP_HASH256", 170),
  ("OP_CODESEPARATOR", 171),
  ("OP_CHECKSIG", 172),
  ("OP_CHECKSIGVERIFY", 173),
  ("OP_CHECKMULTISIG", 174),
  ("OP_CHECKMULTISIGVERIFY", 175),
  ("OP_NOP1", 176),
  ("OP_NOP2", 177),
  ("OP_NOP3", 178),
  ("OP_NOP4", 179),
  ("OP_NOP5", 180),
  ("OP_NOP6", 181),
  ("OP_NOP7", 182),
  ("OP_NOP8", 183),
  ("OP_NOP9", 184),
  ("OP_NOP10", 185),
  ("OP_PUBKEYHASH", 253),
  ("OP_PUBKEY", 254),
  ("OP_INVALIDOPCODE", 255),
]

OP_ALIASES = [
    ("OP_CHECKLOCKTIMEVERIFY", 177),
    ("OP_TRUE", 81),
    ("OP_FALSE", 0)
]

# SUBSETS
#OPCODES_PUSHDATA = set(xrange(0, 96+1))
#OPCODES_INTEGERS = set(xrange(0x51, 0x60+1))
#OPCODES_CRYPTO = set([166, 167, 168, 169, 170])
#OPCODES_LOGIC = set([99, 100, 101, 102, 103, 104])
#OPCODES_ARITHMETIC = set(xrange(139, 152))
#OPCODES_SIGCHECKS = 


#REGEX_PATTERNS = {
#        'P2PKH': re.compile('OP_DUP OP_HASH160 [abcdef0123456789]+ OP_EQUALVERIFY OP_CHECKSIG'),
#        'P2SH': re.compile('OP_HASH160 .* OP_EQUAL'),
#        'Multisig': re.compile('(OP_FALSE|OP_0|OP_TRUE) ([abcdef0123456789]+ )+(OP_1|OP_2|OP_3|OP_4|OP_5) OP_CHECKMULTISIG'),
#        'Pubkey': re.compile('[abcdef0123456789]+ OP_CHECKSIG'),
#        'Null Data': re.compile('OP_RETURN [abcdef0123456789]+'),
#}

OPname = dict([(k[3:], v) for k, v in OPCODE_LIST + OP_ALIASES]);OPname.update(dict([(k,v) for k,v in OPCODE_LIST + OP_ALIASES]))
OPint = dict([(v,k) for k,v in OPCODE_LIST])
OPhex = dict([(encode(k, 16, 2), v) for v,k in OPCODE_LIST])
getop = lambda o: OPname.get(o.upper() if not o.startswith("OP_") else upper(o[2:]), 0)

def get_op(s):
    """Returns OP_CODE for integer, or integer for OP_CODE"""
    if isinstance(s, int):
        return OPint.get(s, '')
    elif isinstance(s, basestring):
        return getop(s)

def parse_script(script):
    if isinstance(script, list):
        script = ' '.join(script)
    scriptarr = script.split()
    SCR = []
    for v in scriptarr:
        if isinstance(v, basestring):
            if str(v).startswith('0x'):
                if int(v[2:], 16) < 0x4c:
                    continue
                else:
                    SCR.append(v[2:])
            elif len(v) in (1, 2):
                SCR.append(int(v, 0))
            elif v.startswith('OP_'):
                SCR.append(get_op(v[3:]))
            else:
                SCR.append(v)
    return serialize_script(SCR)

#addr="n1hjyVvYQPQtejJcANd5ZJM5rmxHCCgWL7"

#SIG64="G8kH/WEgiATGXSy78yToe36IF9AUlluY3bMdkDFD1XyyDciIbXkfiZxk/qmjGdMeP6/BQJ/C5U/pbQUZv1HGkn8="

tpriv = priv = sha256("mrbubby"*3+"!")
tpub = pub = privtopub(priv)
taddr = addr = privtoaddr(priv, 111)
pkh = mk_pubkey_script(addr)[6:-4]

masterpriv = sha256("master"*42)
masterpub = compress(privtopub(masterpriv))
masteraddr = pubtoaddr(masterpub, 111)

ops = [
       OPname['IF'], 
       masterpub, 
       OPname['CHECKSIGVERIFY'], 
       OPname['ELSE'],
       '80bf07', #safe_hexlify(from_int_to_le_bytes(507776)), # '80bf07'
       OPname['NOP2'], 
       OPname['DROP'], 
       OPname['ENDIF'], 
       pub, 
       OPname['CHECKSIG']
       ]

myscript = "63210330ed33784ee1891122bc608b89da2da45194efaca68564051e5a7be9bee7f63fad670380bf07" \
           "b1756841042daa93315eebbe2cb9b5c3505df4c6fb6caca8b756786098567550d4820c09db988fe999" \
           "7d049d687292f815ccd6e7fb5c1b1a91137999818d17c73d0f80aef9ac"

msaddr = "2NBrWPN37wvZhMYb66h23v5rScuVRDDFNsR"

pushedtx_txid = "2e7f518ce5ab61c1c959d25e396bc9d3d684d22ea86dc477b1a90329c6ca354f"

raw = mktx(
    ["2e7f518ce5ab61c1c959d25e396bc9d3d684d22ea86dc477b1a90329c6ca354f:1"],
    [{'value': 84480000, 'script': '76a914dd6cce9f255a8cc17bda8ba0373df8e861cb866e88ac'}])

#signing_tx = signature_form(tx, i, '<utxo_scriptPubKey>', hashcode)
signing_tx = signature_form(raw, 0, myscript)

sig1 = multisign(signing_tx, 0, myscript, masterpriv)
sig2 = multisign(signing_tx, 0, myscript, priv)
signed1 = apply_multisignatures(raw, 0, myscript, sig1, sig2)

txh = txh23b = "0100000001b14bdcbc3e01bdaad36cc08e81e69c82e1060bc14e518db2b49aa43ad90ba26000000000" \
               "490047304402203f16c6f40162ab686621ef3000b04e75418a0c0cb2d8aebeac894ae360ac1e780220" \
               "ddc15ecdfc3507ac48e1681a33eb60996631bf6bf5bc0a0682c4db743ce7ca2b01ffffffff0140420f" \
               "00000000001976a914660d4ef3a743e3e696ad990364e555c271ad504b88ac00000000"

txo = txo23b = deserialize(txh23b)