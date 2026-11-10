"""새98 한 자세를 원래99 x+1 관계로 공유 패킹하는 기본/포스 후보."""
from pathlib import Path
import sys,json,struct,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
import numpy as np
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import decode_stream,bank_offsets,composition_frame,indexed_atlas
from native_pose_pack import need,sha,write,crop
from prepare_lowhp_final import compose
LOCK_SHA='a8bb418252d28b5f6a1e81c2a2baa9a87c4ef721db9cb39b4fcc53cc47dc678a'
def validate_inputs(data,d,read=lambda p:p.read_bytes()):
    need(sha(data)=='c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be','Wrong parent')
    raw=read(d/'LOCK.json');need(sha(raw)==LOCK_SHA,'Wrong art lock');q=json.loads(raw)
    for name,digest in q['files'].items():need(sha(read(d/name))==digest,'Changed native source: '+name)
    for name,digest in q['source_files'].items():need(sha(read(H/name))==digest,'Changed generation/registration: '+name)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--layers',default='double_cyclone_layers_probe01');ap.add_argument('--out',default='double_cyclone_base_pack01');args=ap.parse_args()
    need(args.layers in('double_cyclone_layers_probe01','double_cyclone_layers_probe02'),'Unsupported layers');o=(H/args.out).resolve();need(o.is_relative_to(H.resolve())and o!=H.resolve(),'Output outside owned work');need(not o.exists(),'Fresh output required');o.mkdir();source=H/'prepared_air01/PL00_U.ARC';data=source.read_bytes();need(sha(data)=='c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be','Wrong parent');a=Archive(data);d=H/args.layers;banks=(0,5,6,7,8);layers={b:np.array(Image.open(d/f'098_bank{b}_indices.png'))for b in banks}
    if args.layers.endswith('02'):validate_inputs(data,d)
    need(a.banks[0]['frames'][98]['offset']==a.banks[0]['frames'][99]['offset'],'Native sharing changed')
    f=a.banks[0]['frames'][98];group=[p['index']for p in a.banks[0]['frames']if p['offset']==f['offset']];need(group==[98,99],'Unexpected raw alias')
    raw,parts=pack_many_patterns(bytes(4096),32,[crop(layers[b])for b in banks],set(range(1,32)),[24]*5);replacements={}
    for bank,rr in zip(banks,parts):
        replacements[bank]={n:b''.join(struct.pack('<BBbb',flags,t,x-80+(n-98),y-80)for t,x,y,flags in rr)for n in(98,99)}
    nc=a.c;slack={}
    for bank,rr in replacements.items():nc,slack[bank]=repack_parts(nc,bank,rr)
    ng,graphics=repack_variable(a.g,{98:raw,99:raw},{98:32,99:32});out=replace_entry(replace_entry(data,2,ng),3,nc);b=Archive(out);need(bank_offsets(a.c)==bank_offsets(b.c),'Parts boundaries changed');need(b.p==a.p,'Palette changed');parts_checked=0
    for bank in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,bank,0)['bank_frame_count']):
            if bank in banks and n in(98,99):continue
            need(records(a.c,bank,n)==records(b.c,bank,n),'Nontarget parts changed');parts_checked+=1
    nonraw=0;allraw=0
    for bi,ab in enumerate(a.banks):
        bb=b.banks[bi];need((ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames'])),'Graphics boundaries changed')
        for p,q in zip(ab['frames'],bb['frames']):
            old=decode_stream(a.g,p['offset'],p['limit'],p['tile_count']*128).data;new=decode_stream(b.g,q['offset'],q['limit'],q['tile_count']*128).data;allraw+=1
            if bi==0 and p['index']in(98,99):need(new==raw,'Target raw differs')
            else:need(new==old,'Nontarget raw changed');nonraw+=1
    conditions=0;gpu=0
    atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
    for n in(98,99):
        ll={bank:np.roll(v,n-98,axis=1)for bank,v in layers.items()}
        for bank,v in ll.items():
            need(np.array_equal(b.layer(n,bank)[0],v),'New source layer differs')
            for part in composition_frame(b.c,bank,n)['parts']:
                t=part['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];gpu+=1
                if t%16==0:need(not tile[:,0].any(),'GPU first-column underflow risk')
                if part['flip_y']:need(not tile[0].any(),'GPU flipped row risk')
        for mask in range(16):
            for arm in(1,2):need(b.composite(n,mask,arm)[0].tobytes()==compose(a,ll,mask,arm).tobytes(),'Partial readback mismatch');conditions+=1
        for form,mask in(('base',0),('fourth',15)):
            b.composite(n,mask)[0].save(o/f'{form}_{n:03}.png')
    for form,mask in(('base',0),('fourth',15)):
        page([(f'{n} old',a.composite(n,mask)[0])for n in(98,99)]+[(f'{n} actual candidate',b.composite(n,mask)[0])for n in(98,99)],a.composite(0,mask)[0],o/f'{form}_readback.png',cols=2,scale=5)
    page([(f'98 mask{m:X}',b.composite(98,m)[0])for m in range(16)],a.composite(0,15)[0],o/'partial_readback.png',cols=4,scale=4)
    (o/'PL00_U.ARC').write_bytes(out)
    write(o/'report.json',{'passed':True,'parent_sha256':sha(data),'candidate_sha256':sha(out),'target_refs':[98,99],'target_layers_exact':10,'raw_count':allraw,'non_target_raw_exact':nonraw,'non_target_parts_exact':parts_checked,'partial_conditions':conditions,'gpu_parts':gpu,'parts_slack':slack,'graphics':graphics,'native99_is_new98_x_plus1':True,'all_palette_bytes_exact':True,'hand_contact_delta_from_parent_pixels':{'left':[1,1],'right':([0,0]if args.layers.endswith('02')else[-1,1])},'right_new_hand_registration':args.layers.endswith('02'),'left_shoe_tip_delta_pixels':[1,0],'sole_y_exact':22,'body_source_recolored_contour_pixels':54,'source_generation':{'page01':sha((H/'double_cyclone_inputs02/page01/generated.png').read_bytes())},'actual_gameplay':False,'native_mips_gpu_pending':True,'root_art_review_pending':True,'resource_not_frozen':True})
    print(json.dumps({'sha':sha(out),'slack':slack,'parts':parts_checked,'nonraw':nonraw,'partial':conditions}))
if __name__=='__main__':main()
