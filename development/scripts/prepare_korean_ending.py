"""Native weapon-get labels and ending prose, preserving original credits."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_korean_ui import label
from scripts.prepare_riko_illustrations import regrid_ui_parts,repack_one_bank
from scripts.inventory_shibuki_ui import background,sheet
from scripts.discover_inputs import sha256
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels,write_tile
from src.psx_static_effect import compose_static

WEAPON={0:'무기 획득',1:'기술 습득',2:'라이트닝',3:'웹',4:'프로스트 타워',5:'소울 보디',6:'라이징 파이어',7:'그라운드',8:'헌터',9:'에이밍 레이저',10:'더블',11:'사이클론',12:'트윈 슬래셔',13:'뇌신격',14:'빙열참',15:'공원무',16:'용염인',17:'비연각',18:'낙봉파',19:'천공패',20:'질풍아'}
NARRATIVE={
38:[(48,96,'…싸움은 끝났다.\n하지만 어째서인지,\n과거의 기억은 여전히\n리코의 마음을 괴롭힌다.'),(48,192,'…헌터로서 이레귤러를\n쫓는 것은 리코의 사명이다.')],
40:[(48,16,'…동시에 언젠가 친구를\n쓰러뜨려야 하는 운명도\n리코는 알고 있다.'),(48,96,'두 사람.\n서로 다른 두 운명.'),(48,160,'언젠가 리코의 선택은\n두 위대한 헌터를\n비극으로 이끌 것이다.'),(48,240,'다가오는 미래…')],
42:[(48,112,'…싸움은 끝났다.\n하지만 시부키의 마음은\n여전히 편치 않다…'),(48,192,'“무엇이 그 로봇들을\n이레귤러로 만든 걸까?”')],
44:[(48,16,'“…언젠가 나에게도\n그런 일이 일어날까?”'),(48,80,'시부키는 비극적인 운명을\n깨달은 것일까?\n이 수수께끼의 답은 언젠가\n스스로 찾아야 할 것이다…'),(48,176,'머지않아…')],
}
ROLES={4:['원작 메가맨 X4','제작진','제작'],6:['기획','프로그래밍'],8:['캐릭터와 오브젝트 디자인'],10:['배경 디자인','타이틀 디자인'],12:['일러스트','음악'],14:['효과음','성우'],16:['애니메이션 제작진'],24:['도움을 주신 분들'],28:['총괄 제작'],30:['제작 총책임'],34:['플레이해 주셔서 감사합니다']}

def extract_screens(raw):
    g=entry(raw,0x10000);mp=np.frombuffer(entry(raw,0),'<u2');info=np.frombuffer(entry(raw,1),'<u4');out={}
    for s in range(len(mp)//256):
        px=np.zeros((256,256),np.uint8);rows=np.zeros((16,16),np.uint8)
        for n,v in enumerate(mp[s*256:(s+1)*256]):
            value=int(info[int(v)&16383]);a=np.frombuffer(tile_pixels(g,value>>16&4095),np.uint8).reshape(16,16)
            if v&0x4000:a=a[:,::-1]
            if v&0x8000:a=a[::-1]
            x,y=n%16,n//16;px[y*16:y*16+16,x*16:x*16+16]=a;rows[y,x]=(value>>8&63)+64
        out[s]=(px,rows)
    return out

def repack_screens(raw,targets):
    original=extract_screens(raw);g=bytearray(entry(raw,0x10000));mp=np.frombuffer(entry(raw,0),'<u2');info=np.frombuffer(entry(raw,1),'<u4')
    protected_ids={int(v)&16383 for i,v in enumerate(mp) if i//256 not in targets}|{0}
    protected_tiles={int(info[i])>>16&4095 for i in protected_ids}
    free_ids=iter(i for i in range(len(info)) if i not in protected_ids);free_tiles=iter(i for i in range(len(g)//128) if i not in protected_tiles)
    patterns={};attrs={};ng=bytearray(g);nm=bytearray(entry(raw,0));ni=bytearray(entry(raw,1))
    for i in sorted(protected_ids):
        value=int(info[i]);tile=value>>16&4095;px=tile_pixels(g,tile);patterns[px]=tile;attrs[(px,(value>>8&63)+64)]=i
    for s,(pixels,rows) in sorted(targets.items()):
        for y in range(16):
            for x in range(16):
                px=pixels[y*16:y*16+16,x*16:x*16+16].tobytes();row=int(rows[y,x]);key=(px,row)
                if not any(px):ident=0
                elif key in attrs:ident=attrs[key]
                else:
                    if px not in patterns:
                        tile=next(free_tiles,None)
                        if tile is None:raise ValueError('Ending texture capacity exceeded')
                        patterns[px]=tile;write_tile(ng,tile,px)
                    ident=next(free_ids,None)
                    if ident is None:raise ValueError('Ending attribute capacity exceeded')
                    struct.pack_into('<I',ni,ident*4,(patterns[px]<<16)|((row-64)<<8));attrs[key]=ident
                struct.pack_into('<H',nm,s*512+y*32+x*2,ident)
    new=replace_entry(replace_entry(replace_entry(raw,0x10000,bytes(ng)),0,bytes(nm)),1,bytes(ni))
    actual=extract_screens(new)
    for s,(px,rows) in actual.items():
        expected=targets.get(s,original[s]);mask=np.repeat(np.repeat(rows,16,0),16,1);er=np.repeat(np.repeat(expected[1],16,0),16,1)
        if not np.array_equal(px,expected[0]) or np.any((px!=0)&(mask!=er)):raise ValueError(f'Ending screen {s} differs')
    return new,{'changed_screens':sorted(targets),'protected_screens':sorted(set(original)-set(targets)),'tile_patterns':len(patterns),'attribute_patterns':len(attrs),'all_48_screens_decoded':True}

def text_at(pixels,rows,x,y,text,palette=80):
    font=ImageFont.truetype('C:/Windows/Fonts/gulim.ttc',16)
    baseline=font.getbbox('가')[1]
    for row,line in enumerate(text.split('\n')):
        yy=(y//16+row)*16;width=len(line)*16
        if x+width>320 or yy+16>256:raise ValueError('Ending text overflow')
        # Align syllables to native 16px tiles, so repeated Hangul reuses tiles
        # rather than consuming a new pattern for every neighboring pair.
        for col,char in enumerate(line):
            if char==' ':continue
            xx=x+col*16
            mask=Image.new('1',(16,16));ImageDraw.Draw(mask).text((0,-baseline),char,font=font,fill=1);m=np.array(mask,bool)
            pixels[yy:yy+16,xx:xx+16][m]=15;rows[yy//16,xx//16]=palette

def main(output):
    output.mkdir(exist_ok=False);files={};checks={}
    for name in ('ST0F_UX.ARC','ST0F_UZ.ARC'):
        raw=(D/'ui_inventory'/name).read_bytes();g=entry(raw,0x10102);p=entry(raw,10);targets={}
        for n,text in WEAPON.items():
            _,size,_,_=compose_static(g,local_composition(aliased_composition(p,0,n)));a=label(text,size,24,14,border=1);targets[n]=(a.tobytes(),size)
        p=regrid_ui_parts(p,0,targets);ng,p,proof=repack_one_bank(g,p,0,targets);new=replace_entry(replace_entry(raw,0x10102,ng),10,p)
        (output/name).write_bytes(new);files[name]={'before':sha256(raw),'after':sha256(new),'size':len(new)};checks[name]=proof
    name='ST0F_U1.ARC';raw=(D/'ui_inventory'/name).read_bytes();screens=extract_screens(raw);targets={};pal=entry((D/'ui_inventory/COL0F_U1.ARC').read_bytes(),5)
    for s in sorted(set(NARRATIVE)|set(ROLES)|{36}):
        pixels=np.concatenate([screens[s][0],screens[s+1][0]],axis=1).copy();rows=np.concatenate([screens[s][1],screens[s+1][1]],axis=1).copy()
        if s in NARRATIVE:
            pixels[:]=0;rows[:]=80
            for x,y,text in NARRATIVE[s]:text_at(pixels,rows,x,y,text)
        if s in ROLES:
            mask=(np.repeat(np.repeat(rows,16,0),16,1)==81)&(pixels>0);ys=np.where(mask.any(1))[0]
            groups=[]
            for y in ys:
                if not groups or y>groups[-1][-1]+2:groups.append([int(y)])
                else:groups[-1].append(int(y))
            if s==34:groups=[list(ys)]  # two-line thank-you is one phrase
            if len(groups)!=len(ROLES[s]):raise ValueError(f'Credits heading count differs {s}: {groups}')
            pixels[np.repeat(np.repeat(rows==81,16,0),16,1)]=0
            for group,text in zip(groups,ROLES[s]):text_at(pixels,rows,32,min(group),text,81)
            if s==28:
                pixels[:32]=0;text_at(pixels,rows,48,8,'그리고 캡콤의 모든 제작진',80)
        if s==36:
            mask=np.repeat(np.repeat(rows==80,16,0),16,1);pixels[mask]=0;text_at(pixels,rows,64,32,'제공',80)
        targets[s]=(pixels[:,:256],rows[:,:16]);targets[s+1]=(pixels[:,256:],rows[:,16:])
    new,proof=repack_screens(raw,targets)
    checked=0;after=extract_screens(new)
    for s in range(4,38):
        a,r=screens[s];z,zr=after[s];rows=np.repeat(np.repeat(r,16,0),16,1);newrows=np.repeat(np.repeat(zr,16,0),16,1);mask=(a>0)&(rows==80)
        if s==28:mask[:32]=False
        if s==36:mask[:64]=False
        if np.any(mask&((a!=z)|(rows!=newrows))):raise ValueError('Original creator name pixels changed')
        checked+=int(mask.sum())
    proof['creator_name_pixels_preserved']=checked
    (output/name).write_bytes(new);files[name]={'before':sha256(raw),'after':sha256(new),'size':len(new)};checks[name]=proof
    # All creator names and company logos outside translated heading regions
    # remain native pixel data, not retranscribed or attributed to this mod.
    items=[]
    for s in sorted(set(NARRATIVE)|set(ROLES)|{36}):
        im=Image.new('RGBA',(320,256));im.alpha_composite(background(new,pal,s));im.alpha_composite(background(new,pal,s+1),(256,0));im.save(output/f'ending_{s}.png');items.append((f'ENDING {s}',im))
    sheet(items,output/'ending_overview.png',3,(330,280))
    (output/'proposal.json').write_text(json.dumps({'kind':'korean_ending_weapon_proposal','bin_applied':False,'files':files,'checks':checks,'original_creator_names_preserved':True},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'files':list(files),'checks':proof}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
