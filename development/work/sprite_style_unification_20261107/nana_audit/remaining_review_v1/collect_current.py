"""현재 후보 ARC를 직접 복원하는 읽기 전용 미술 재검토. 새 아트 없음."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]
N=Path(__file__).resolve().parent.parent;OUT=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(N)]
from collect import helper
from scripts.export_x_consistency import Archive,GROUPS,metrics

def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):return sha(p.read_bytes())
def write(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n','utf8')

def main():
    paths={'PL00':N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC',
           'PL02':N/'native_restore/nova_sync_v1/PL02_U.ARC'}
    expected={'PL00':'cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa',
              'PL02':'bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45'}
    for k,p in paths.items():assert digest(p)==expected[k]
    arcs={k:Archive(p.read_bytes())for k,p in paths.items()}
    forms=[('base','기본','PL00',0),('fourth','포스','PL00',15),
           ('ultimate_before','얼티밋 전 재킷','PL02',15),('ultimate_after','얼티밋 후 수영복','PL02',0)]
    images={};frames=[];sheets=[];placeholder={105,*range(175,183)}
    for form,label,key,mask in forms:
        for n in range(237):
            effective=15 if form=='ultimate_after'and 217<=n<=230 else mask
            try:im,_=arcs[key].composite(n,effective,2)
            except(ValueError,IndexError):
                assert n in placeholder;im=Image.new('RGBA',(384,384))
            images[form,n]=im
            frames.append({'form':form,'ref':n,'mask':effective,'rgba_sha256':sha(im.tobytes()),**metrics(im)})
    for group,refs in GROUPS.items():
        if group=='reserved_or_empty':continue
        for start in range(0,len(refs),12):
            sub=refs[start:start+12];p=OUT/f'{group}_{start//12:02}.png'
            r=helper.grid([(label,[('idle 0',images[form,0])]+[(str(n),images[form,n])for n in sub])for form,label,_,_ in forms],p,2)
            r.update(group=group,refs=sub,sha256=digest(p));sheets.append(r)
    focus={
      'ultimate_run':[0,1,7,15,25,31],
      'ultimate_air_wall':[0,33,39,47,55,63],
      'weapons':[0,85,95,98,100,231],
      'hurt_low':[0,106,108,120,124,233],
      'arrival':[0,133,135,137,141,142],
      'ladder':[0,143,146,150,153,183],
      'victory':[0,156,161,204,206,207],
      'flight_vehicle':[0,162,184,217,223,229]}
    for group,refs in focus.items():
        p=OUT/f'focus_{group}.png'
        r=helper.grid([(label,[(str(n),images[form,n])for n in refs])for form,label,_,_ in forms],p,4)
        r.update(group=group,refs=refs,sha256=digest(p));sheets.append(r)
    write(OUT/'manifest.json',{'arcs':{k:{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for k,p in paths.items()},'frames':frames,'sheets':sheets,'origin':[160,160],
      'scope':'bank0 237 refs × 4 full forms; not all partial masks, save/select, or capsule/effect banks.',
      'gameplay_verified':False,'visual_review_is_separate':True,'new_art_created':False,
      'caveats':['213..230 기본형과 캡슐 전 일부 기술은 실제 도달하지 않는 저장 참조다.','184..203은 탑승 머리뿐이며 전신 체형 결함으로 판단하지 않는다.','피격 CLUT 순환과 이펙트 배경 혼합을 정적 시트로 판정하지 않는다.']})
    print(json.dumps({'sheets':len(sheets),'frames':len(frames)}))
if __name__=='__main__':main()
