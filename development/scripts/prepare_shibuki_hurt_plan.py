"""미국판 X 피격 몸과 공유 효과/아머를 읽기 전용으로 조사한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko');args=p.parse_args();character='nana' if args.project=='ver_rin_nana' else 'shibuki'
 source=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';inv=json.loads((source/'inventory.json').read_text());parts=(source/'composition_entry.bin').read_bytes()
 assert sha256((source/'original.arc').read_bytes())==inv['archive']['sha256']
 out=ROOT/'work'/args.project/(character+'_art')/'hurt_v1';out.mkdir(parents=True,exist_ok=True);records=[]
 groups={106:[106,107,108],109:[109],110:[110,111],112:[112],113:[113],114:[114]}
 for n,aliases in groups.items():
  r=inv['base_frames'][n];assert inv['stream_sharing'][str(r['offset'])]==[[0,q] for q in aliases]
  body={q['tile'] for q in r['composition']['parts']};armor={q['tile'] for b in range(5,9) for a in aliases for q in composition_frame(parts,b,a)['parts']}
  assert not body&armor
  records.append({'frame':n,'aliases':aliases,'budget':r['compressed_end']-r['offset'],'tile_count':r['tile_count'],'part_count':len(r['composition']['parts']),'writable':sorted(body),'armor_tiles':sorted(armor),'effect_clut':r['composition']['parts'][0]['clut'],'bounds':r['bounds']})
 plan={'task':'x_shibuki','frames':list(range(106,115)),'groups':records,'animations':{str(n):inv['animations'][n] for n in (33,34,36,37)},'deferred_special_hurt':{'animation':35,'frames':[233,234,235,236],'reason':'별도 특수 피격 몸과 팔레트. 일반/강한 피격 완료에 자동 포함하지 않음.'},'source_inventory':str((source/'inventory.json').relative_to(ROOT)),'runtime_verified':False}
 plan['task']='x_'+character
 (out/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(records))
if __name__=='__main__':main()
