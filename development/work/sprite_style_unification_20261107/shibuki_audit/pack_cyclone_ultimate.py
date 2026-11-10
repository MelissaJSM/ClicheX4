"""현재 Ultimate 누적본에98·99 새 전후 의상을 같은32타일로 등록한다."""
from pathlib import Path
import sys,struct,json,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from native_pose_pack import need,sha,write,crop,lossless_pack,same_rgba
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame,decode_stream,indexed_atlas
LOCK_SHA='9330f6af35a2fb457768af3d4f41935571554dcad8b108c9f2522787aa42581c'
def validate_inputs(data,d,read=lambda p:p.read_bytes()):
    need(sha(data)=='c851fb17b2369281667970c414be63eb31fb1f02fe5641ad667bfb4b5c8507cf','Wrong parent')
    raw=read(d/'LOCK.json');need(sha(raw)==LOCK_SHA,'Wrong art lock');q=json.loads(raw)
    for name,digest in q['files'].items():need(sha(read(d/name))==digest,'Changed target: '+name)
    for name,digest in q['source_files'].items():need(sha(read(H/name))==digest,'Changed source: '+name)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='double_cyclone_ultimate_pack01');args=ap.parse_args();out=(H/args.out).resolve();need(out.is_relative_to(H.resolve())and out!=H.resolve(),'Output outside work');need(not out.exists(),'Fresh output required');p=H/'prepared_ultimate_wall01/PL02_U.ARC';data=p.read_bytes();a=Archive(data);d=H/'double_cyclone_ultimate_shared01';validate_inputs(data,d);before=np.array(Image.open(d/'before_098_indices.png'));after=np.array(Image.open(d/'after_098_indices.png'));need(not np.any((after>0)&(before==0)),'Cannot erase base with transparent overlay');out.mkdir()
    group=[f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][98]['offset']];need(group==[98,99],'Unexpected alias group')
    layers={0:after,5:np.where(same_rgba(a,before,after),0,before).astype(np.uint8)};raw,parts,method=lossless_pack([crop(layers[0]),crop(layers[5])]);newc=a.c;slack={};targets={}
    for b,rr in zip((0,5),parts):
        repl={n:b''.join(struct.pack('<BBbb',flags,t,x-80+n-98,y-80)for t,x,y,flags in rr)for n in(98,99)};newc,slack[b]=repack_parts(newc,b,repl)
        for n in(98,99):targets[n,b]=np.roll(layers[b],n-98,1)
    for n in(98,99):
        for b in(6,7,8):need(not a.layer(n,b)[0].any(),'Unexpected separate Ultimate part')
    newg,gmeta=repack_variable(a.g,{98:raw,99:raw},{98:32,99:32});candidate=replace_entry(replace_entry(data,2,newg),3,newc);b=Archive(candidate)
    need(bank_offsets(a.c)==bank_offsets(b.c),'Composition boundaries moved');need(a.p==b.p,'Palette changed');rawcount=0;rawkept=0
    for gb,bb in enumerate(a.banks):
        nb=b.banks[gb];need((bb['base'],bb['end'],len(bb['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics boundary moved')
        for f,q in zip(bb['frames'],nb['frames']):
            v=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;w=decode_stream(b.g,q['offset'],q['limit'],q['tile_count']*128).data;rawcount+=1
            if gb==0 and f['index']in(98,99):need(w==raw,'New raw differs')
            else:need(w==v,'Non-target raw changed');rawkept+=1
    keptparts=0
    for bank in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,bank,0)['bank_frame_count']):
            if(n,bank)in targets:continue
            need(records(a.c,bank,n)==records(b.c,bank,n),'Non-target composition changed');keptparts+=1
    for key,v in targets.items():need(np.array_equal(b.layer(*key)[0],v),'New layer differs')
    rawatlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256);gp=0
    for n,bank in targets:
        for part in composition_frame(b.c,bank,n)['parts']:
            gp+=1;t=part['tile'];tile=rawatlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
            if t%16==0:need(not tile[:,0].any(),'GPU first column hazard')
            if part['flip_y']:need(not tile[0].any(),'GPU flipped top hazard')
    keptdisplay=0
    for n in range(237):
        if n in{105,*range(175,183)}:continue
        for mask,arr in((0,after),(15,before)):
            im=b.composite(n,mask)[0]
            if n in(98,99):need(im.tobytes()==a.rgba(np.roll(arr,n-98,1),16 if mask else 0).tobytes(),'New costume composite differs')
            else:need(im.tobytes()==a.composite(n,mask)[0].tobytes(),'Non-target costume display changed');keptdisplay+=1
    allowed=np.zeros(len(data),bool)
    for typ in(2,3):
        e=next(e for e in psx_arc(data)if e['type']==hex(typ));allowed[e['offset']:e['offset']+e['size']]=True
    need(len(candidate)==len(data),'ARC grew');delta=np.frombuffer(data,np.uint8)!=np.frombuffer(candidate,np.uint8);need(not np.any(delta&~allowed),'Outside graphics/parts changed')
    (out/'PL02_U.ARC').write_bytes(candidate)
    for form,mask in(('before',15),('after',0)):
        page([(f'{n} parent',a.composite(n,mask)[0])for n in(98,99)]+[(f'{n} packed',b.composite(n,mask)[0])for n in(98,99)],a.composite(0,mask)[0],out/f'{form}_readback.png',cols=2,scale=5)
        for n in(98,99):b.composite(n,mask)[0].save(out/f'{form}_{n:03}.png')
    write(out/'report.json',{'passed':True,'parent_sha256':sha(data),'candidate_sha256':sha(candidate),'target_refs':[98,99],'new_layers':len(targets),'new_costume_displays':4,'non_target_display_exact':keptdisplay,'all_raw':rawcount,'non_target_raw_exact':rawkept,'non_target_parts_exact':keptparts,'gpu_parts_safe':gp,'parts_slack':slack,'graphics':gmeta,'packing_method':method,'pixel_loss':False,'shared99_is98_x_plus1':True,'whole_arc_outside_2_3_exact_bytes':int((~allowed).sum()),'source_art':json.loads((d/'report.json').read_text('utf8')),'root_review_pending':True,'independent_pending':True,'runtime_verified':False})
    print(json.dumps({'sha':sha(candidate),'slack':slack,'raw':rawcount,'nonraw':rawkept,'display':keptdisplay,'parts':keptparts}))
if __name__=='__main__':main()
