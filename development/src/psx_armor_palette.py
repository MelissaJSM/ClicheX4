"""X 몸/효과 행을 보존하는 별도 아머 CLUT 변환."""
import struct


def replace_armor_palette_rows(source, words, body_rows, flashes, *, weapon_rows=()):
    if len(source)%32 or len(words)!=16 or words[0]!=0 or any(type(w) is not int or not 0<w<=65535 for w in words[1:]):
        raise ValueError('Invalid palette data')
    if len(set(body_rows))!=len(body_rows) or any(type(r) is not int or r<0 for r in body_rows):
        raise ValueError('Invalid body row selection')
    if len(set(weapon_rows))!=len(weapon_rows) or any(type(r) is not int or r<0 for r in weapon_rows):raise ValueError('Invalid weapon rows')
    if set(weapon_rows)&set(body_rows):raise ValueError('Weapon and single-row modes overlap')
    # player_set_palette copies 16 body words then 32 armor words;
    # player_reset_palette(weapon) copies 32 body/effect words then 32 armor words.
    groups={r:(r+1,r+2) for r in body_rows}
    groups.update({r:(r+2,r+3) for r in weapon_rows})
    all_targets=[row for rows in groups.values() for row in rows];targets=set(all_targets)
    protected=set(body_rows)|{r+i for r in weapon_rows for i in (0,1)}
    if len(targets)!=len(all_targets) or targets&protected or any(r*32+32>len(source) for r in targets):
        raise ValueError('Armor rows overlap bodies or exceed entry')
    if not set(flashes)<=set(body_rows):raise ValueError('Flash row outside selection')
    result=bytearray(source)
    for body,armor_rows in groups.items():
        transformed=list(words)
        if body in flashes:
            rgb,weight=flashes[body]
            if len(rgb)!=3 or not 0<=weight<=1 or any(not 0<=c<=31 for c in rgb):raise ValueError('Invalid flash')
            for i,w in enumerate(words[1:],1):
                colors=[round(((w>>s)&31)*(1-weight)+target*weight) for s,target in zip((0,5,10),rgb)]
                transformed[i]=sum(c<<s for c,s in zip(colors,(0,5,10)))
        for row in armor_rows:
            old=struct.unpack_from('<16H',source,row*32)
            if old[0]!=0:raise ValueError('Armor transparency differs')
            new=[0]+[(transformed[i]&0x7fff)|(old[i]&0x8000) for i in range(1,16)]
            if any(w&0x7fff==0 for w in new[1:]):raise ValueError('Opaque color became transparent black')
            struct.pack_into('<16H',result,row*32,*new)
    return bytes(result),sorted(targets)
