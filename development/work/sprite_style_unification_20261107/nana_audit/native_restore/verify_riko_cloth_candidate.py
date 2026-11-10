"""제작 함수를 호출하지 않고 동결된 리코 의상18 후보만 독립 읽기 검사."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(Path(__file__).parent)]
from preview_restore import Archive,sha,digest,write,need
from src.psx_player import decode_stream,indexed_atlas,composition_frame,bank_offsets
from scripts.prepare_riko_ui import replace_entry
from PIL import Image
import numpy as np
D=ROOT/'work/sprite_style_unification_20261107/zero_audit'
KEYS={(0,8):(8,0),(0,14):(14,0),**{(0,n):(27,0)for n in range(27,33)},**{(0,n):(133,0)for n in(133,134,246)},**{(1,n):(133,0)for n in(87,91,93)},**{(1,n):(133,-5)for n in(95,96,98,99)}}
PNG_SHA={8:'029fb4961a2ebc0b6f5c42d12979a5ea8791711f32f4453e38a7c6de8e7a797c',14:'ce5ae55ab051133ca719673b541c01f661d3eca0ea1415c6d67c24c0be22bacc',27:'c68a5c88dfd6ac157d5bf773334900185078c3473288aac233573092d17b15cc',133:'30b7cb8e28d7cbeec9d37ac5f401b6ceb4da586a56502730888e049a76862195'}
def main():
    a=Archive((D/'riko_restore/prepared_rear_v1/PL01_U.ARC').read_bytes());b=Archive((D/'riko_restore/prepared_cloth_v1/PL01_U.ARC').read_bytes())
    need(sha(a.data)=='f8f346691709107a4ae774b49f0f46d662941442f75bf92ee0eead97bbf671c8','Source SHA');need(sha(b.data)=='6ebb0239f27253bdd37b16c54b66a5b2044ba8191f41b8cc9f29cfbe15a440dc','Candidate SHA');need(replace_entry(b.data,2,a.g)==a.data,'Non graphics entry changed')
    masters={}
    for n,h in PNG_SHA.items():
        p=D/f'riko_cloth_inputs/registered_candidate_v1/b0_{n:03}_indices.png';need(digest(p)==h,'Source PNG hash');v=np.array(Image.open(p));mask=np.array(Image.open(D/f'riko_cloth_inputs/b0_{n:03}_preserve_head_mask.png'))>0;need(int(mask.sum())==309,'Head mask changed');need(np.array_equal(v[mask],a.layer(n,0,0)[0][mask]),'Head changed');masters[n]=v
    rawchecked=display=nonraw=nondisplay=changed=0
    for gb in(0,1):
        ab,bb=a.banks[gb],b.banks[gb];need((ab['base'],ab['end'])==(bb['base'],bb['end']),'Bank bounds')
        for n,(af,bf)in enumerate(zip(ab['frames'],bb['frames'])):
            need(af['tile_count']==bf['tile_count']<=32,'Tile count');ar=decode_stream(a.g,af['offset'],af['limit'],af['tile_count']*128).data;br=decode_stream(b.g,bf['offset'],bf['limit'],bf['tile_count']*128).data;rawchecked+=1
            if(gb,n)not in KEYS:need(ar==br,'Nonselected raw changed');nonraw+=1
            if gb==1 and 42<=n<=49:continue
            av=a.layer(n,gb*5,gb)[0];bv=b.layer(n,gb*5,gb)[0];display+=1
            if(gb,n)in KEYS:
                key,dx=KEYS[gb,n];target=np.roll(masters[key],dx,axis=1);need(np.array_equal(bv,target),'Registered target differs');changed+=int(np.count_nonzero(av!=bv))
                aa=np.frombuffer(indexed_atlas(ar,af['tile_count'])[0],np.uint8).reshape(-1,256);ba=np.frombuffer(indexed_atlas(br,bf['tile_count'])[0],np.uint8).reshape(-1,256)
                for part in composition_frame(b.c,gb*5,n)['parts']:
                    tile=part['tile'];ty,tx=tile//16*16,tile%16*16
                    if tile%16==0:need(not np.any((aa[ty:ty+16,tx]==0)&(ba[ty:ty+16,tx]>0)),'New first column alpha')
                    if part['flip_y']and tile//16%16==0:need(not np.any((aa[ty,tx:tx+16]==0)&(ba[ty,tx:tx+16]>0)),'New flipY alpha')
            else:need(np.array_equal(av,bv),'Nonselected displayed frame changed');nondisplay+=1
    need(a.c==b.c and a.p==b.p,'Composition/palette changed')
    write(Path(__file__).parent/'riko_cloth_independent.json',{'passed':True,'source_sha256':sha(a.data),'after_sha256':sha(b.data),'raw_references':rawchecked,'displayed_references':display,'non_target_raw_exact':nonraw,'non_target_display_exact':nondisplay,'changed_display_pixels':changed,'accepted_head_pixels_per_master_preserved':309,'selected_references':len(KEYS),'registered_master_png_hashes_and_pixels_exact':True,'composition_palette_audio_other_entries_exact':True,'tile_counts_bank_boundaries_exact':True,'new_gpu_edge_alpha_zero':True,'method':'제작 함수 미호출. 독립된18참조 목록과등록PNG해시를사용하여실제ARC를디코드/재합성.','scope':'당시 prepared_cloth_v1 의상18 후보 한정; 이후리코최종후속ARC/실기미검증','runtime_verified':False})
    print(json.dumps({'passed':True,'raw':rawchecked,'display':display,'nonraw':nonraw,'nondisplay':nondisplay}))
if __name__=='__main__':main()
