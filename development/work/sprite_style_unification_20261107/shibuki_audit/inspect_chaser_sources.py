"""시부키 실제 부모와 원US의 탑승13 관계를 읽기 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
from scripts.prepare_shibuki_ultimate_production import records

PBS=(0,5,6,7,8);KEYS=(162,166,170,174)
def shifted(z,dy):
    a=np.zeros_like(z)
    if dy>=0:a[dy:]=z[:z.shape[0]-dy]
    else:a[:dy]=z[-dy:]
    return a
def main():
    d=H/'chaser_sources01';need(not d.exists(),'새 조사 출력 필요');d.mkdir()
    paths={'current_base':H/'prepared_standing_fire_base01/PL00_U.ARC','current_ultimate':H/'prepared_standing_fire_ultimate01/PL02_U.ARC'}
    hashes={'current_base':'4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175','current_ultimate':'1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad'}
    arcs={}
    for k,p in paths.items():need(sha(p.read_bytes())==hashes[k],'부모 변경');arcs[k]=Archive(p.read_bytes())
    original=ROOT/'MegaMan X4.bin';blobs=read_disc(original,('PL00_U.ARC','PL02_U.ARC'))[0]
    for k,n in [('original_base','PL00_U.ARC'),('original_ultimate','PL02_U.ARC')]:
        p=d/f'{k}.ARC';p.write_bytes(blobs[n]);paths[k]=p;hashes[k]=sha(blobs[n]);arcs[k]=Archive(blobs[n])
    report={'sources':{},'frames':{},'forms':{},'original_relation_assumed_from_other_character':False,'new_art_or_arc_candidate_created':False,'runtime_verified':False}
    for k,a in arcs.items():
        report['sources'][k]={'path':paths[k].relative_to(ROOT).as_posix(),'sha256':hashes[k]};rows=[]
        for n in range(162,175):
            group=max(v for v in KEYS if v<=n);layers={}
            for pb in PBS:
                z,meta=a.layer(n,pb);base=a.layer(group,pb)[0];rr=records(a.c,pb,n)
                owner=[i for i in range(composition_frame(a.c,pb,0)['bank_frame_count'])if records(a.c,pb,i)==rr]
                layers[str(pb)]={'indexed_sha256':sha(z.tobytes()),'opaque':int(np.count_nonzero(z)),
                    'exact_dy_from_key':[dy for dy in range(-4,5)if np.array_equal(z,shifted(base,dy))],
                    'records':meta['parts'],'same_record_bytes_owners':owner,'external_owners':[i for i in owner if i not in range(162,175)]}
            f=a.banks[0]['frames'][n]
            rows.append({'ref':n,'source_key':group,'tile_count':f['tile_count'],'raw_offset':f['offset'],
                'raw_owners':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']], 'layers':layers})
        report['frames'][k]=rows
        for form,mask in [('base'if 'base'in k else'after',0),('fourth'if 'base'in k else'before',15)]:
            key=k+'_'+form;fr=[]
            for n in range(162,175):
                group=max(v for v in KEYS if v<=n);z=np.asarray(a.composite(n,mask)[0]);base=np.asarray(a.composite(group,mask)[0])
                fr.append({'ref':n,'source_key':group,'rgba_sha256':sha(z.tobytes()),'metrics':metrics(a.composite(n,mask)[0]),
                    'exact_dy_from_key':[dy for dy in range(-4,5)if np.array_equal(z,shifted(base,dy))]})
            report['forms'][key]=fr
            page([(str(n),a.composite(n,mask)[0])for n in KEYS],a.composite(0,mask)[0],d/f'{key}_keys.png',cols=2,scale=4)
    meta=ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json'
    animations=json.loads(meta.read_text('utf8'))['animations'];report['animation_metadata']={'path':meta.relative_to(ROOT).as_posix(),'sha256':sha(meta.read_bytes())}
    report['tables_using_chaser']=[a for a in animations if any(162<=s['frame']<=174 for s in a['steps'])]
    report['limits']=['현재 원표 메타데이터만 연결한 읽기 조사다. 실제 EXE 바이트 확인과 순서 재생은 새 패킹 뒤 별도 수행한다.','다른 캐릭터의 별칭 규칙을 가정하지 않고 원US와 시부키 부모의 각 층/완성RGBA를 직접 대조했다.']
    write(d/'report.json',report)
    print(json.dumps({'report_sha256':sha((d/'report.json').read_bytes()),'forms':{k:{r['ref']:r['exact_dy_from_key']for r in v}for k,v in report['forms'].items()},'tables':[a['id']for a in report['tables_using_chaser']]}))
if __name__=='__main__':main()
