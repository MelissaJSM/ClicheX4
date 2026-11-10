"""시부키 실제PL00/PL02의 노바/호버18참조 원화·효과·공유 읽기."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import composition_frame
PBS=(0,5,6,7,8);REFS=tuple(range(213,231))
def main():
    d=H/'nova_hover_sources01';need(not d.exists(),'새읽기폴더');d.mkdir();sources={'base':H/'prepared_chaser_base01/PL00_U.ARC','ultimate':H/'prepared_standing_fire_ultimate01/PL02_U.ARC','original_base':H/'chaser_sources01/original_base.ARC','original_ultimate':H/'chaser_sources01/original_ultimate.ARC'};report={'sources':{},'frames':{},'pairs':{},'forms':{},'runtime_verified':False,'new_art_generated':False,'source_policy':'Nana의 원화/효과 규칙을 복사하지 않고 시부키 실제부모와원US를 별도읽음.'}
    for key,p in sources.items():
        a=Archive(p.read_bytes());report['sources'][key]={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(a.data)};rows=[];pairs=[];sd=d/key;sd.mkdir()
        for n in REFS:
            layers={}
            for pb in PBS:
                z,m=a.layer(n,pb);rr=records(a.c,pb,n);owners=[j for j in range(composition_frame(a.c,pb,0)['bank_frame_count'])if records(a.c,pb,j)==rr];Image.fromarray(z).save(sd/f'{n:03}_bank{pb}_indices.png')
                layers[str(pb)]={'opaque':int((z>0).sum()),'sha256':sha(z.tobytes()),'parts':m['parts'],'record_owners':owners,'outside_213_230_owners':[v for v in owners if v not in REFS],'all_layer_values':sorted(map(int,np.unique(z)))}
            f=a.banks[0]['frames'][n];rows.append({'ref':n,'tile_count':f['tile_count'],'raw_sha256':a.layer(n,0)[1]['decoded_sha256'],'raw_owners':[v['index']for v in a.banks[0]['frames']if v['offset']==f['offset']],'layers':layers})
        for n in range(213,230,2):pairs.append({'pair':[n,n+1],'different_cells_by_layer':{str(pb):int((a.layer(n,pb)[0]!=a.layer(n+1,pb)[0]).sum())for pb in PBS}})
        report['frames'][key]=rows;report['pairs'][key]=pairs
        forms=[('base',0),('fourth',15)]if 'base'in key else[('before',15),('after',0)]
        for form,mask in forms:
            fr=[]
            for i,ns in enumerate((range(213,217),range(217,221),range(221,227),range(227,231))):
                pics=[]
                for n in ns:
                    im=a.composite(n,mask)[0];im.save(sd/f'{form}_{n:03}.png');pics.append((f'{n} mask{mask}',im));fr.append({'ref':n,'render_mask':mask,'RGBA_sha256':sha(im.tobytes()),'metrics':metrics(im),'same_full_RGBA_refs':[j for j in REFS if a.composite(j,mask)[0].tobytes()==im.tobytes()]})
                page(pics,a.composite(0,mask)[0],d/f'{key}_{form}_{i:02}.png',cols=2,scale=4)
            report['forms'][key+'_'+form]=fr
    meta=ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json';animations=json.loads(meta.read_text('utf8'))['animations'];report['animations_metadata']={'path':meta.relative_to(ROOT).as_posix(),'sha256':sha(meta.read_bytes())};report['tables_using_213_230']=[v for v in animations if any(s['frame']in REFS for s in v['steps'])]
    report['limits']=['모든폼mask0/15를진단용으로저장했다. 실제217..230의강제mask15·CLUT별몸/효과구분은별도원코드/시부키소비검사가필요하다.','서로다른기록을자동FX로취급하지않는다.213/214·215/216동일성은이실제자료의수치에만근거한다.','정적원표메타데이터연결만이며원EXE재실행/실기는아니다.'];write(d/'report.json',report);print(json.dumps({'report_sha256':sha((d/'report.json').read_bytes()),'pairs':report['pairs'],'tables':[v['id']for v in report['tables_using_213_230']]}))
if __name__=='__main__':main()
