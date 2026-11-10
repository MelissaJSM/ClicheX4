from pathlib import Path
import hashlib,json
D=Path(__file__).parent
for folder in ('nana_arrival_endpoint_audit01','shibuki_standing02_layer_audit01'):
    p=D/folder/'report.json';r=json.loads(p.read_text('utf8'));r['comparison_actually_viewed']=True
    if folder.startswith('nana'):
        r['visual_finding']='층 단독과 현재/11월5일 합성 25셀을 실제 열람했다. 재킷의 분홍 소매/앞섶 차이는 존재하지만 133/135는 맨팔·허리 면이 크게 보여 대기의 재킷보다 의상 식별성이 약하다. 기존 원화의 미술 보완 후보이며 현재 마스크 반전이나 최근 등록 소실로 설명할 수 없다.'
    else:
        r['visual_finding']='층 분리판과 기본/포스 실제 후보를 열람했다. 왼쪽 무릎 외측 작은 조각은 내린 옛 소매/손끝이다. layer8 기술 소유를 무릎 의미로 해석한 보호 조건 때문에 남는다.'
        r['ownership_evidence']={'layer8_record_offset':23412,'tile':10,'window_world':[-14,11,2,27],
            'duplicate_arm7_leg8_row':'world y11 x-14..-10 색인2,2,10,4,1 동일',
            'not_all_roi_is_arm':'x-9 인접 무릎 포함하므로 ROI19점 전체 삭제는 금지',
            'recommendation':'새 원화의 alpha/외곽으로 옛 소매·손끝 의미영역만 교체하고 실제 무릎/다리는 보존. old layer8 전체opaque를 보호하는 규칙은 이 ref0에 적용 불가.'}
    p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
    print(folder,hashlib.sha256(p.read_bytes()).hexdigest())
