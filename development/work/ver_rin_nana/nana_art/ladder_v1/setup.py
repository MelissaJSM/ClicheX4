from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[4]
p=ROOT/'work/ver_buki_riko/shibuki_art/ladder_v1/optimize04b.py'
s=p.read_text('utf8').replace('import json,sys,random,math,itertools','import argparse,json,sys,random,math,itertools').replace('ROOT=Path(__file__).resolve().parents[4]','ROOT=Path(__file__).resolve().parents[1]')
old="d=Path(__file__).parent;a=d/'production04';parent=ROOT/'out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z';"
new="p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--steps',type=int,default=12000);args=p.parse_args();a=args.art.resolve();d=a.parent;parent=args.parent.resolve()\nif not a.is_relative_to(ROOT/'work/ver_rin_nana/nana_art/ladder_v1') or not parent.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Isolated Nana paths required')\n"
assert old in s;s=s.replace(old,new).replace('range(240000)','range(args.steps)');dest=ROOT/'scripts/optimize_nana_ladder.py'
assert not dest.exists();dest.write_text(s,'utf8')
p=ROOT/'projects/ver_rin_nana/project.json';j=json.loads(p.read_text('utf8'));j['nana_fall_leg_revision'].update(user_accepted=True,user_quote='좋아 다음 작업으로 진행해도 괜찮아',date='2026-10-30');j['active_substage']='NANA_LADDER_PRODUCTION';p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
p=ROOT/'out/ver_rin_nana/nana_fall_legs_20261029T230758381002Z/manifest.json';j=json.loads(p.read_text('utf8'));j.update(new_animation_user_accepted=True,user_acceptance={'date':'2026-10-30','quote':'좋아 다음 작업으로 진행해도 괜찮아','scope':'falling leg revision only'});p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
p=ROOT/'docs/NANA_FALL_LEGS.md';p.write_text(p.read_text('utf8')+'\n2026-10-30 사용자 “좋아 다음 작업으로 진행해도 괜찮아”로 하강 다리 수정 수용. 자동 전수 검사 미완료 사실은 유지한다.\n','utf8')
p=ROOT/'docs/DECISIONS.md';p.write_text('# 2026-10-30 나나 하강 수정 수용·사다리 제작\n\n사용자 “좋아 다음 작업으로 진행해도 괜찮아”를 하강 다리 수정 수용과 다음 기본형 모션 진행 승인으로 기록한다. 사다리14참조를 제작하며 피격 전체 미술 수용으로 확대하지 않는다. 중단 후 “다시 이어서” 지시에 따라 같은 작업을 재개했다.\n\n'+p.read_text('utf8'),'utf8')
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8').replace('다음은 사다리 제작이며 현재 수정 미술 사용자 수용 전이다.','하강 다리 수정은 사용자 수용했으며 사다리14참조 제작 중이다.');p.write_text(s,'utf8')
