"""그림 생성 없이 현재 네이티브 후보 입력들의 해시를 고정한다."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    d=H/'air_targets_probe02';p=d/'LOCK.json'
    if p.exists():raise ValueError('Existing lock must remain immutable')
    files={f'{n:03}_bank{b}_indices.png':sha(d/f'{n:03}_bank{b}_indices.png')for n in range(33,55)for b in(0,5,6,7,8)}
    paths=['air_detail_inputs01/generated.png','air_detail_inputs02/generated.png','air_detail_inputs03/generated.png','air_detail_inputs04/generated.png','air_shot_inputs02/page01/generated.png','air_shot_extra_hand_retry01/generated.png','air_shot_inputs02/page03/generated.png','air_shot_inputs02/page04/generated.png']
    q={'source_parent_sha256':'78b329a07d888682c24b440386cb365f826572402346b3ee6620216ce951617e','target_manifest_sha256':sha(d/'targets.json'),'files':files,'accepted_generation_inputs':{str(x):sha(H/x)for x in paths},'status':'네이티브 후보 입력 동결. 실제 게임 적용/최종 미술 수용과는 구분한다.'}
    p.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
if __name__=='__main__':main()
