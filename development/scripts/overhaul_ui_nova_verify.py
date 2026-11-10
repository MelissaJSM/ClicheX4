"""노바·종아리 교정의 byte 병합, GPU 열 경계, 부분 아머를 확인한다."""
import json,struct,sys,tempfile,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_ui_nova_pack import patch,image,FRAMES,SIZE
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import sha,rgba
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from scripts.discover_inputs import psx_arc
import scripts.overhaul_ui_nova_pack as packer
D=ROOT/'work/overhaul_20261105/ui/nana_fourth_nova_v1'

def main():
    old=(ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL00_U.ARC').read_bytes()
    nova=(D/'PL00_U.ARC').read_bytes();legs=(ROOT/'work/overhaul_20261105/ui/nana_legs_v1/PL00_U.ARC').read_bytes()
    fresh,proof,base,full,layers=patch(old)
    assert fresh==nova==(D.with_name('nana_fourth_nova_repro_v1')/'PL00_U.ARC').read_bytes()
    a=np.frombuffer(old,np.uint8);n=np.frombuffer(nova,np.uint8);l=np.frombuffer(legs,np.uint8)
    nm=a!=n;lm=a!=l;overlap=nm&lm
    assert not overlap.any()
    merged=np.where(nm,n,l).astype(np.uint8).tobytes()
    ng,lg,mg=entry(nova,2),entry(legs,2),entry(merged,2)
    refs=0
    for k in range(1,33):
        lf=graphics_bank(lg,0,allow_bank_aliases=True)['frames'][k];mf=graphics_bank(mg,0,allow_bank_aliases=True)['frames'][k]
        assert decode_stream(lg,lf['offset'],lf['limit'],lf['tile_count']*128).data==decode_stream(mg,mf['offset'],mf['limit'],mf['tile_count']*128).data
        for b in(0,5,6,7,8):assert np.array_equal(image(merged,b,k),image(legs,b,k));refs+=1
    for k in range(213,221):
        for b in(0,5,6,7,8):assert np.array_equal(image(merged,b,k),image(nova,b,k));refs+=1
    seam=[]
    for k in FRAMES:
        f=graphics_bank(ng,0,allow_bank_aliases=True)['frames'][k];raw=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data
        atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
        for b in(0,5,6,7,8):
            for p in composition_frame(entry(nova,3),b,k)['parts']:
                if p['tile']%16==0:
                    assert not atlas[p['tile']//16*16:p['tile']//16*16+16,0].any()
                    assert not p['flip_x']
                    seam.append({'frame':k,'bank':b,'tile':p['tile'],'transparent_first_column':True,'flip_x':False})
    for e in psx_arc(old):
        k=int(e['type'],16)
        if k not in(2,3):assert entry(old,k)==entry(nova,k)
    rejected=[];art=packer.D
    before_hashes={p.name:sha(p.read_bytes())for p in art.iterdir()if p.is_file()}
    with tempfile.TemporaryDirectory(prefix='nova_verify_',dir=D.parent)as name:
        temp=Path(name).resolve();assert temp.is_relative_to(ROOT.resolve())
        needed=['prepared.json','generated.png']+[f'{kind}_{k}.png'for kind in('base','fourth')for k in(213,215,217)]
        for case in('source_sha','palette','indexed_sha','dimensions','mode','index16'):
            for file in needed:shutil.copyfile(art/file,temp/file)
            meta=json.loads((temp/'prepared.json').read_text('utf8'))
            if case=='source_sha':meta['source_sha256']='0'*64
            elif case=='palette':meta['palette_words'][1]^=1
            elif case=='indexed_sha':meta['images']['base_213.png']='0'*64
            else:
                p=temp/'base_213.png';im=Image.open(p)
                if case=='dimensions':im=im.crop((0,0,1,1))
                elif case=='mode':im=im.convert('RGBA')
                else:im.putpixel((0,0),16)
                im.save(p);meta['images'][p.name]=sha(p.read_bytes())
            (temp/'prepared.json').write_text(json.dumps(meta),'utf8')
            packer.D=temp
            try:packer.targets(old)
            except ValueError:rejected.append(case)
            else:raise AssertionError('Invalid artwork accepted: '+case)
            finally:packer.D=art
    assert len(rejected)==6
    assert {p.name:sha(p.read_bytes())for p in art.iterdir()if p.is_file()}==before_hashes
    words=struct.unpack_from('<64H',entry(merged,9));masks=(2,3,6,10,7,11,14,15)
    board=Image.new('RGB',(8*240,2*280),(28,34,45));draw=ImageDraw.Draw(board)
    for row,k in enumerate((213,217)):
        for col,mask in enumerate(masks):
            actual=rgba(image(merged,0,k),words)
            for bit,b in((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:actual.alpha_composite(rgba(image(merged,b,k),words[16:32]))
            cut=actual.crop((40,40,120,120)).resize((240,240),Image.Resampling.NEAREST)
            board.paste(cut,(col*240,row*280+28),cut);draw.text((col*240+4,row*280+4),f'{k} parts={mask}',fill='white')
    board.save(D/'partial_armor_review.png')
    report={'nova_arc_sha256':sha(nova),'legs_arc_sha256':sha(legs),'merged_arc_sha256':sha(merged),
        'byte_changes_nova':int(nm.sum()),'byte_changes_legs':int(lm.sum()),'overlapping_changed_bytes':int(overlap.sum()),
        'legs32_all_layers_and_decoded_streams_preserved':True,'nova8_all_layers_preserved':True,'layer_comparisons':refs,
        'reproduced_identical':True,'UV_edge_checks':seam,'only_entries2_3_changed':True,
        'partial_outfit_assignment':{'head':'모자','body':'드레스 상체','arm':'소매와 앞쪽 장식','leg':'구두와 흰 치맛단 및 뒤 베일'},
        'partial_masks_displayed':list(masks),'runtime_verified':False}
    report['invalid_art_cases_rejected']=rejected
    report['source_artifacts_unchanged']=True
    (D/'merge_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    proposal=json.loads((D/'proposal.json').read_text('utf8'));proposal['checks']=proof;proposal['additional_verification']=report
    (D/'proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n','utf8')
    (D/'verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
