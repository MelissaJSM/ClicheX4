"""수용본의 PL02 구조와 설정화·기준 도트를 읽기 전용으로 조사한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256,psx_arc
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from scripts.verify_shibuki_save_icon import rgba
PARENT=ROOT/'out/ver_rin_nana/nana_fourth_ui_20261030T122936152482Z'
PARENT_SHA='c7fc576c68a4c4bc2f55090bfccf47d4e03a11489fa49c9b824399cbcab11d8a'
REF=ROOT/'character/ver_rin_nana/nana(ultimate armor).webp'
SOURCE_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'

def render_ultimate(arc,n):
    g,c,pal=[entry(arc,k) for k in (2,3,9)];f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;words=np.zeros((160,160),np.uint16)
    for bank in (0,8,5,7,6):
        cp=composition_frame(c,bank,n)
        for p in cp['parts']:
            v=canvas_from_parts(raw,f['tile_count'],local_composition({**cp,'parts':[p]}));colors=np.array(struct.unpack_from('<16H',pal,((0 if bank==0 else 1)+p['clut'])*32),np.uint16);words=np.where(v,colors[v],words)
    return rgba(words)

def main(out):
    out=out.resolve();require(out.is_relative_to(ROOT/'work/ver_rin_nana/nana_ultimate_armor') and not out.exists(),'Fresh analysis output required')
    require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(ROOT/'MegaMan X4.bin')==SOURCE_SHA,'Unsupported game input')
    protected=json.loads((PARENT/'preservation.json').read_text('utf8'))
    for q in protected['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed')
    out.mkdir(parents=True);arcs={};records={}
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,(PARENT/'rin_nana.bin').stat().st_size);iso={q['name']:q for q in d.inspect()['files']}
        for name in ('PL00_U.ARC','PL02_U.ARC','MOJIPAT.ARC','LOAD_U.ARC'):
            q=iso[name+';1'];a=d.read(q['lba'],q['size']);arcs[name]=a;records[name]={**q,'sha256':sha256(a)};(out/name).write_bytes(a)
    require(arcs['PL00_U.ARC']==(PARENT/'modified.arc').read_bytes() and arcs['PL02_U.ARC']==(PARENT/'PL02_U.ARC').read_bytes(),'Disc extraction differs')
    with (ROOT/'MegaMan X4.bin').open('rb') as f:
        d=DiscReader(f,(ROOT/'MegaMan X4.bin').stat().st_size);q=records['PL02_U.ARC'];original=d.read(q['lba'],q['size'])
    (out/'original_PL02_U.ARC').write_bytes(original)
    arc=arcs['PL02_U.ARC'];g,c,pal=[entry(arc,k) for k in (2,3,9)];frames=[];same_base=[];different_base=[];not_comparable=[]
    for fr in graphics_bank(g,0,allow_bank_aliases=True)['frames']:
        n=fr['index'];raw=decode_stream(g,fr['offset'],fr['limit'],fr['tile_count']*128);layers=[]
        for bi in (0,8,5,7,6):
            cp=composition_frame(c,bi,n)
            try:v=canvas_from_parts(raw.data,fr['tile_count'],local_composition(cp));valid=True;error=None
            except ValueError as exc:v=None;valid=False;error=str(exc)
            layers.append({'bank':bi,'parts':len(cp['parts']),'tiles':sorted({p['tile'] for p in cp['parts']}),'cluts':sorted({p['clut'] for p in cp['parts']}),'renderable':valid,'error':error,'visible_pixels':int(np.count_nonzero(v)) if valid else None})
            if bi==0:
                try:_,nv,_,_=render(arcs['PL00_U.ARC'],n);require(valid,'Current PL02 not renderable');(same_base if np.array_equal(v,nv) else different_base).append(n)
                except ValueError:not_comparable.append(n)
        frames.append({'frame':n,'descriptor':fr,'encoded_bytes':raw.end-fr['offset'],'slot_bytes':fr['limit']-fr['offset'],'layers':layers})
    previews={}
    for n in (0,85):
        for key,a,full in [('accepted_base',arcs['PL00_U.ARC'],False),('accepted_fourth',arcs['PL00_U.ARC'],True),('current_ultimate',arc,True),('original_ultimate',original,True)]:
            im=render_ultimate(a,n) if key.endswith('ultimate') else render(a,n,full)[0];im.save(out/f'{key}_{n:03}.png');previews[key,n]=im
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
    board=Image.new('RGB',(1280,620),'#252c3c');draw=ImageDraw.Draw(board)
    for i,(key,label) in enumerate([('original_ultimate','원작 얼티밋'),('current_ultimate','현재 PL02'),('accepted_base','수용 나나 기본형'),('accepted_fourth','수용 포스아머')]):
        draw.text((i*320+8,8),label,font=font,fill='white')
        for row,n in enumerate((0,85)):
            im=previews[key,n].crop((40,48,120,112)).resize((320,256),Image.Resampling.NEAREST);board.paste(im,(i*320,38+row*280),im)
    board.save(out/'native_comparison_4x.png')
    # 이미지 생성에는 수용 도트만 참고 시트로 전달한다. ROM 데이터는 전달하지 않는다.
    board=Image.new('RGBA',(960,440),(0,0,0,0))
    for i,(key,n) in enumerate([('accepted_base',0),('accepted_base',85)]):
        im=previews[key,n].crop((40,48,120,112)).resize((480,384),Image.Resampling.NEAREST);board.alpha_composite(im,(i*480,28))
    board.save(out/'accepted_nana_pose_reference.png')
    details={}
    for n in (0,85):
        im=previews['accepted_base',n];a=np.array(im);y,x=np.nonzero(a[:,:,3]);details[n]={'bbox':list(im.getbbox()),'height':int(y.max()-y.min()+1),'sole_y':int(y.max()),'opaque_pixels':len(x)}
    p=struct.unpack_from('<I',arcs['MOJIPAT.ARC'],4)[0];report={'task':'ultimate_armor_nana','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,'original_sha256':SOURCE_SHA,'reference':REF.relative_to(ROOT).as_posix(),'reference_sha256':digest(REF),'resources':records,'graphics_refs':sum(len(graphics_bank(g,b,allow_bank_aliases=True)['frames']) for b in range(len(bank_offsets(g,allow_aliases=True)))),'base_frame_count':len(frames),'base_index_pixels_equal_to_nana_pl00':same_base,'base_index_pixels_differ_from_nana_pl00':different_base,'not_comparable':not_comparable,'frames':frames,'accepted_landmarks':details,'save_frame52':composition_frame(arcs['MOJIPAT.ARC'],2,52),'save_palette_rows':{r:arcs['MOJIPAT.ARC'][p+r*32:p+(r+1)*32].hex() for r in (8,9,10,11,30,31)},'game_modified':False,'runtime_verified':False}
    write(out/'analysis.json',report);write(out/'preservation.json',{'files':protected['files'],'parent_sha256':PARENT_SHA,'reference_sha256':digest(REF),'unchanged':True})
    for q in protected['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed')
    print(json.dumps({k:report[k] for k in ('graphics_refs','base_frame_count','reference_sha256','accepted_landmarks','not_comparable')}));print(json.dumps({'base_equal':len(same_base),'base_different':len(different_base),'output':str(out)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
