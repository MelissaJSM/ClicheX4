"""PL00 노바 몸체·윤곽·원효과 출처를 제작 함수를 실행하지 않고 읽는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

def outline(v):
    m=v>0;p=np.pad(m,1);edge=(p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:])&~m
    return np.where(edge,6,v).astype(np.uint8)

def main():
    d=H/'nova_strike_base_sources01';need(not d.exists() or not list(d.iterdir()),'새 읽기 경로');d.mkdir(exist_ok=True)
    parent=H/'prepared_nova_base01/PL00_U.ARC';original=H/'chaser_sources01/original_base.ARC'
    hist=ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1';npng=hist/'native04/frame_217.png'
    a,o=Archive(parent.read_bytes()),Archive(original.read_bytes())
    need(sha(a.data)=='619032d0b81ffc50e5f5664ff1e3d0c077f226a7d5a8ccfac081be6a2126c6c5','고정 부모')
    native=np.array(Image.open(npng));need(native.shape==(80,96) and native.ndim==2,'역사 원화 크기')
    body=np.zeros((384,384),np.uint8);body[114:194,112:208]=native
    ring=outline(body);actual=a.layer(217)[0]
    need(np.array_equal(ring,actual),'217 역사 몸+Manhattan1 색6 다름')
    fxmap=np.array([0,1,2,5,4,5,6,7,9,9,10,11,6,14,8,2],np.uint8)
    effects={n:fxmap[o.layer(n)[0]%16]for n in(218,219)}
    for n,z in effects.items():need(np.array_equal(z,a.layer(n)[0]),f'{n} 원 효과 색변환 다름')
    bg=o.layer(220)[0]%16;bg=bg.copy();bg[(bg>0)&~np.isin(bg,[8,12])]=8
    effect220=fxmap[bg];merged=effect220.copy();merged[ring>0]=ring[ring>0]
    current220=a.layer(220)[0];diff220=merged!=current220
    need(not np.any(diff220&(ring==0)),'220 몸 밖 역사 효과 다름')
    prod220=hist/'production14/frame_220.png';prod=np.zeros_like(body);prod[80:240,80:240]=np.array(Image.open(prod220))
    need(np.array_equal(prod,current220),'220 최종 역사 production14 다름')
    rows=[]
    for form,mask in(('base',0),('fourth',15)):
        full=np.array(a.composite(217,mask)[0]);no_ring=full.copy();no_ring[body==0]=0
        Image.fromarray(no_ring).save(d/f'{form}_217_body.png')
        page([('역사 몸체 / 효과 제거',Image.fromarray(no_ring)),('현재217 / 외곽선 포함',Image.fromarray(full)),('현재220 / 효과 합성',a.composite(220,mask)[0])],a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=3,scale=5)
        rows.append({'form':form,'mask':mask,'body_RGBA_sha256':sha(no_ring.tobytes()),'body_metrics':metrics(Image.fromarray(no_ring)),'outer_ring_covered_by_armor_pixels':int(((body==0)&(full[:,:,3]>0)&(np.array(a.rgba(actual))!=full).any(2)).sum())})
    for n,z in[(217,body),(218,effects[218]),(219,effects[219]),(220,current220)]:Image.fromarray(z).save(d/f'{n}_source_indices.png')
    Image.fromarray(effect220).save(d/'220_background_indices.png')
    Image.fromarray(np.where((ring>0)&(body==0),ring,0).astype(np.uint8)).save(d/'217_outline_indices.png')
    imagefiles=[p for p in d.iterdir()if p.suffix=='.png']
    report={'passed':True,'source_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in(parent,original,npng,prod220,hist/'native04/art.json',hist/'assemble04.py',hist/'fix_effect_layout04.py',Path(__file__))},'candidate_sha256':sha(a.data),'217_native_registration':[0,-6],'217_native_body_pixels':int((body>0).sum()),'217_outline_pixels':int(((ring>0)&(body==0)).sum()),'217_full_base_pixels':int((actual>0).sum()),'218_effect_pixels':int((effects[218]>0).sum()),'219_effect_pixels':int((effects[219]>0).sum()),'220_background_pixels':int((effect220>0).sum()),'220_effect_occluded_pixels':int(((effect220>0)&(ring>0)).sum()),'220_body_region_later_historical_differences':int(diff220.sum()),'220_outside_body_background_exact':True,'220_final_production14_exact':True,'217_220_armor_layers_exact':{str(pb):bool(np.array_equal(a.layer(217,pb)[0],a.layer(220,pb)[0]))for pb in(5,6,7,8)},'form_sources':rows,'images':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in imagefiles},'policy':['현재 PL00 217은 역사 native04 몸을 Y−6 등록하고 Manhattan1 색6 외곽선을 합친 것과 exact이며 PL02의840px 옛73 몸체와 별개다.','PL00 218/219는 원US 동일참조의 전체 효과를 역사16색 매핑한 것과 exact. 새그림 대상으로 세지 않으며 임의로 몸체/효과를 삭제하지 않는다.','PL00 220 배경은 원220의 비영8/12 외 값을8로 바꾼 후 역사fxmap을 적용한 배열이며 현재217 몸 영역 밖은 exact다. 몸 안651셀은 이후 역사 production14와 일치하는 별도 색차이가 있으므로 단순217 합성과 같다고 기록하지 않는다.','새몸체를 제작할 때 원220 전체 배경을 출처로 보존하고 새몸·새가림 변화는 별도 정책으로 기록한다. 기존 몸 내부의 옛 색변경을 새머리에 복사하지 않는다.','본 입력은 현재217에서 역사 몸체 알파만 분리했다. Fourth 장식/옷 외곽 중 몸체 밖 표본이 있으면 이 분리판을 새디자인 확정으로 취급하지 않는다.','원화 재작화·원화 수용·패킹·원MIPS/실기는 수행하지 않은 읽기 검사다.'],'new_art_created':False,'source_or_resource_modified':False,'runtime_verified':False}
    write(d/'report.json',report);print(json.dumps({k:v for k,v in report.items()if k not in('images','source_files','policy')},ensure_ascii=False))
if __name__=='__main__':main()
