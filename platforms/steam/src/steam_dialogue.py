import struct

def runtime_patches():
    # All addresses are in the verified, normally loaded RXC1 X4 engine.
    # No on-disk executable changes, executable loader changes, or new threads.
    start = 0x98312c
    old = bytes.fromhex('8bcdc644b00400e8687c01008bcf0fbff0e86ed900008bcd668bd8e834c3feff8bcd885cb005')
    new = bytearray()
    def emit(hexbytes):
        new.extend(bytes.fromhex(hexbytes))
    def call(address):
        new.extend(b'\xe8'+struct.pack('<i', address-(start+len(new)+5)))
    # ESI already contains the visible glyph index. Omit its redundant getter
    # to fit page+tile stores into the original 38-byte block.
    emit('8bcf'); call(0x990ab0)       # current encoded word
    emit('668bd88bcd'); call(0x96f480) # BX=word, EAX=quad array
    emit('885cb005')                  # low 8 bits -> tile
    emit('8bd3c1ea0880e2038854b004')    # page=(word>>8)&3, no control bits
    emit('8bcd')                      # same ECX for the next native getter
    if len(new) > len(old):
        raise ValueError('Inline dialogue change exceeds its original block')
    new.extend(b'\x90'*(len(old)-len(new)))
    return [
        ('dialogue_space_mask_initial', 0x982f9f, bytes.fromhex('bbff010000'), bytes.fromhex('bbff030000')),
        ('dialogue_space_mask_loop', 0x9831b5, bytes.fromhex('bbff010000'), bytes.fromhex('bbff030000')),
        ('dialogue_glyph_page_and_tile', start, old, bytes(new)),
        ('dialogue_korean_advance', 0x98320e,
         bytes.fromhex('488bcff7d81bc083e0fc83c010'),
         bytes.fromhex('8bcfb80c000000909090909090')),
    ]
