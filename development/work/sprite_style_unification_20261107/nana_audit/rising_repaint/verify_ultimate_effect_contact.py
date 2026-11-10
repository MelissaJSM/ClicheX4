"""완성 ARC 권총과 순정 초기 불꽃의 양방향 공간 대조. 실제 색/실기 아님."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,write,need,sha,helper
from prepare_body_contacts import translate,merged

def main():
    p=D/'packed_ultimate_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9','후보')
    out=D/'ultimate_effect_contact_v1';out.mkdir(exist_ok=False)
    npth=D/'native_contacts_v1/manifest.json';need(digest(npth)=='87644d2f6e4734ae982cdcce649dee09cdb8d54716841e66d44cc2036a606f09','원초기화 증거')
    native=json.loads(npth.read_text('utf8'));rows=[];records=[]
    for st,n in((1,104),(0,232)):
        for form,mask,start in(('before',15,16),('after',0,0)):
            body=merged(a,n,mask);case=np.array(Image.open(D/f'ultimate_weapon_probe_v1/before_{231 if n==232 else n:03}_case.png'));panels=[]
            for facing in(0,64):
                q=next(c for c in native['native_initializers']if not c['charged']and c['subtype']==st and c['facing']==facing)
                fx=np.array(Image.open(D/f'native_contacts_v1/effect_anim{q["animation"]}_{q["initial_ref"]:03}.png'))
                need(np.array_equal(a.layer(q['initial_ref'],13,5)[0],fx),'원효과 실제ARC')
                effect=translate(fx,*q['spawn_world'],q['flip_x']);vis=translate(body,0,0,bool(facing));weapon=translate(case,0,0,bool(facing));im=a.rgba(vis,start)
                cyan=np.zeros((384,384,4),np.uint8);cyan[effect>0]=[25,205,220,155];overlay=im.copy();overlay.alpha_composite(Image.fromarray(cyan))
                panels.extend([(f'{form} {facing} ARC',im),(f'{facing} native initial occupancy',overlay)])
                dist=distance_transform_edt(effect==0);records.append({'ref':n,'form':form,'facing':facing,'native_initializer':q,'weapon_min_distance_to_initial_effect':float(dist[weapon>0].min()),'weapon_pixels_overlapping_effect':int(((weapon>0)&(effect>0)).sum()),'weapon_pixels':int((weapon>0).sum())})
            rows.append((f'Ultimate {n} {form}',panels))
    for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
    write(out/'report.json',{'passed':True,'candidate_sha256':sha(a.data),'initializer_manifest_sha256':digest(npth),'cases':records,'scope':'원초기화 MIPS의 좌우 생성점/반전과 원효과 첫프레임을 현재 ARC 권총에 겹친 정적 진단. 청록은 점유 영역이며 실제 효과색/물리/전시간표/실기 아니다.','runtime_verified':False})
    print(json.dumps({'cases':len(records),'distances':[q['weapon_min_distance_to_initial_effect']for q in records]}))
if __name__=='__main__':main()
