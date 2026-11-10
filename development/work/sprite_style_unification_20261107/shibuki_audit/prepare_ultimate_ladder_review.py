"""다음 Ultimate 사다리의 현재 표시와 새 기본 사다리를 원점 그대로 비교."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write

def main():
    o=H/'ultimate_ladder_remaining_review01';need(not o.exists(),'Fresh output');o.mkdir();bp=H/'prepared_dash_base01/PL00_U.ARC';up=H/'prepared_ultimate_dash01/PL02_U.ARC';base=Archive(bp.read_bytes());ult=Archive(up.read_bytes());refs=list(range(143,156))+[183];rows=[];sheets=[]
    for name,arc,mask in(('base_new_reference',base,0),('before_current',ult,15),('after_current',ult,0)):
        items=[]
        idle=arc.composite(0,mask)[0];idle.save(o/f'{name}_idle.png')
        for n in refs:
            im,meta=arc.composite(n,mask);im.save(o/f'{name}_{n:03}.png');items.append((f'{name} {n:03}',im));rows.append({'form':name,'ref':n,'image':str((o/f'{name}_{n:03}.png').relative_to(ROOT)),'rgba_sha256':sha(im.tobytes()),'metrics':metrics(im),'layers':meta})
        for i in range(0,len(refs),6):sheets.append(page(items[i:i+6],idle,o/f'{name}_comparison_{i//6:02}.png',cols=3,scale=3))
    write(o/'manifest.json',{'scope':'현재 Ultimate 사다리14의상쌍과 기존 상세 기본 사다리의 비교·입력준비. 새아트 제작/적용 아님.','source_archives':{bp.relative_to(ROOT).as_posix():sha(bp.read_bytes()),up.relative_to(ROOT).as_posix():sha(up.read_bytes())},'refs':refs,'images':rows,'sheets':sheets,'actually_viewed_sheets':[],'next_art_scope':'원손/발·총구 기준을 유지한 동일자세 Ultimate 의상 전후 편집. 몸 전체 비율과 후면 머리 세부를 대기와 비교.','source_game_or_art_modified':False});print(json.dumps({'out':str(o),'references':len(refs),'form_images':len(rows),'sheets':len(sheets)}))
if __name__=='__main__':main()
