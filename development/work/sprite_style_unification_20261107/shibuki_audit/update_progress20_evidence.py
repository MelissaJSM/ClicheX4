"""검토 문구 정정으로 바뀐 근거 해시와 새 등장1페이지를 장부에 반영한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,write,need
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}

def main():
    p=H/'fullform_ledger20.json';j=json.loads(p.read_text('utf8'));previous=sha(p.read_bytes());names={'root_review_checkpoint108.json','shibuki_fourth_hurt17_summary.json'};changes=[]
    def update(v):
        if isinstance(v,dict):
            if 'path'in v and 'sha256'in v and Path(v['path']).name in names:
                q=ROOT/v['path'];new=sha(q.read_bytes())
                if new!=v['sha256']:changes.append({'path':v['path'],'before':v['sha256'],'after':new});v['sha256']=new
            for x in v.values():update(x)
        elif isinstance(v,list):
            for x in v:update(x)
    update(j);d=H/'ultimate_arrival_inputs01/page01';receipt=json.loads((d/'generation_receipt.json').read_text('utf8'));receipt['original_output']='<LOCAL_PATH>';write(d/'generation_receipt.json',receipt)
    j['next_generation'].update(status='133/135 전후4 첫 원화 생성·fixed96셀 등록·비교2판 실제열람 완료. 공통손/머리·효과 분리·원순서/패킹은 미완료.137/138은 입력만 준비.',generated=True,completed_generated_body_keys=[133,135],generated_source=ev(d/'generated.png'),native_registration=ev(H/'ultimate_arrival_native01/report.json'),packed=False)
    write(p,j);u=H/'unique_art_keys20.json';v=json.loads(u.read_text('utf8'));update(v);v['source_ledger']=ev(p);write(u,v)
    write(H/'progress20_evidence_correction.json',{'previous_ledger_sha256':previous,'current_ledger':ev(p),'changed_external_hashes':changes,'reason':'root108 임시외국어문구를 한국어로 정리.이미지와실기결과 불변이라는 root 전달을 반영.새 등장 첫페이지 진척 추가.','art_candidate_changed':False})
    plates=[H/'ultimate_arrival_native01'/f'{f}_comparison.png'for f in('before','after')]
    write(H/'ultimate_arrival_native01/author_review.json',{'actual_viewed':[ev(x)for x in plates],'observations':['새133/135의 머릿결·금색안경·재킷 칼라/맨팔 구분이 옛 단색머리·소매보다 대기 기준에 가깝다.','깊은133 착지와135 준비자세는 구분되고 네그림 모두 원발바닥23을 유지한다.','135 전후의 손/머리 위치에 작은 차이가 남아 공통관절 정합 전이며 미술·패킹 최종승인 아님.'],'alpha_policy':'원화의 반투명후광은 고정1/8 표본 alpha128 미만으로 제외되며,각몸은1연결성분이다.임의부분삭제/전신확대축소없음.','source':ev(d/'generated.png'),'registration':ev(H/'ultimate_arrival_native01/report.json'),'runtime_verified':False})
    print(json.dumps({'ledger':sha(p.read_bytes()),'external_corrections':len(changes)}))

if __name__=='__main__':main()
