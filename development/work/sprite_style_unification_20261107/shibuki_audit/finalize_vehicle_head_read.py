"""작은머리 역사원화 직접대조와 현재 실제열람 의견을 결속한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def main():
    d=H/'vehicle_head_accessory_read01';need(not(d/'conclusions.json').exists(),'기존근거보호');rp=d/'report.json';r=json.loads(rp.read_text('utf8'));a=Archive((ROOT/r['parents']['base']['path']).read_bytes());hist=ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1/production14';matches=[]
    for n in range(184,204):
        p=hist/f'frame_{n:03}.png';z=np.array(Image.open(p));need(np.array_equal(z,a.layer(n,0)[0][80:240,80:240]),'역사원화와현재base 다름');matches.append({'ref':n,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'indexed160_world_exact':True})
    gold=[222,172,57,255];goldcounts={}
    for form in r['forms']:
        q=np.array(Image.open(d/f'{form["form"]}_small184.png'));yy,xx=np.nonzero((q==gold).all(2));goldcounts[form['form']]={'count':int(len(xx)),'crop_coordinates':[[int(x),int(y)]for y,x in zip(yy,xx)]}
    plate=d/'four_forms_existing_head.png';write(d/'conclusions.json',{'scope':'기존작은머리 유지조건의 확인.새원화 제작/수용/패킹 아님.','report':rp.relative_to(ROOT).as_posix(),'report_sha256':sha(rp.read_bytes()),'actually_viewed':[{'path':plate.relative_to(ROOT).as_posix(),'sha256':sha(plate.read_bytes())}],'historical_base20_world_exact':matches,'history_metadata':{'path':(hist/'art.json').relative_to(ROOT).as_posix(),'sha256':sha((hist/'art.json').read_bytes()),'head_slot_constraint':'one tile16x16;현재144불투명/13x15머리,몸체없음정상'},'gold_RGBA':gold,'small_gold_positions':goldcounts,'findings':['현작은머리는각폼19참조에서동일13×15·144불투명이며198은빈참조다. 전체높이나얼굴을늘릴 근거가 없다.','기본층20은2026-10월remaining_v1/production14 원화색인과exact다. 후속전신재작화의상세머리원화가이작은머리까지교체된것은아니다.','기본/포스의귀·홍채·옆장식은읽힌다. 작은표시라는제약을고려해전신대기와같은세부픽셀수를강요하지않는다.','Ultimate대기의눈위금색고글은작은머리에서보이지않고금색1셀은아래홍채다. 기존13×15안에서고글식별성과큰연보라면의국소머릿결보완을검토할근거가있다.','빈6/7/8은일부타참조와공유하므로수정하지않는다. 같은최종머리여도raw그룹은PL00/02마다다르므로전체19·부분·공유검사가필요하다.'],'decision':'Ultimate작은머리장식은 국소신규원화 후보, 기본/포스는 현작은영역의읽힘으로우선보존 검토. 실제라이드아머조종석실기·새미술수용은별도.','new_art_generated':False,'new_resources_written':False,'runtime_verified':False})
    print(json.dumps({'conclusions':sha((d/'conclusions.json').read_bytes()),'gold':goldcounts}))
if __name__=='__main__':main()
