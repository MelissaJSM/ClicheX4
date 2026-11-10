from pathlib import Path
import hashlib,json
import capstone
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;O=D/'shibuki_nova_hover_relations01'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
p=O/'report.json';r=json.loads(p.read_text('utf8'));assert sha(p.read_bytes())=='14da197c66b67c5efdc0384f66517ec4f5b4c442dc1197efd6dfeba327920f4a'
for q in r['readback_sheets']:assert sha((ROOT/q['path']).read_bytes())==q['sha256']
cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
codefiles=[]
for q in r['US_equal_code_ranges']+[{'name':'renderer','start':0x800257bc,'bytes':r['renderer']['code_hex'],'sha256':r['renderer']['sha256']}]:
 b=bytes.fromhex(q['bytes']);assert sha(b)==q['sha256'];p=O/(q['name']+'_mips.txt');assert not p.exists();p.write_text('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}'for i in cs.disasm(b,q['start']))+'\n','utf8');codefiles.append({'path':rel(p),'sha256':sha(p.read_bytes())})
v={
 'scope':'시부키 원준비·Nova/호버 11판 실제 열람과 제작 보호 조건',
 'report':rel(O/'report.json'),'report_sha256':sha((O/'report.json').read_bytes()),
 'actually_viewed':r['readback_sheets'],'disassembly':codefiles,
 'findings':[
  '원US PL00/PL02 모두 213/214와215/216은 별도 그림이다. 현재 두 자원의 5층이 같은 것은 이전 Shibuki 제작 정책이다. 원US214의 팔 주변 변형과216의 상체/팔 자세 변화까지 복원됐다고 하지 않는다.',
  '준비213/215 현재 재추출에서 기본·포스·Ultimate 전후 의상 모두 구별된다. Ultimate는 engine+37가 켜져 있으면 engine+47 ownership0에서mask15, 획득후에는mask0을 사용한다. 일시 player+ A7가0이더라도 이를 곧 후폼이라고 해석하지 않는다.',
  '실제217..230은 ownership과 무관 mask15다. 현재217의 흰 재킷은5층 overlay가 아니라0층840px몸체 안에 있다. 역사 Shibuki73의 최대성분840px를(-3,-7) 옮긴 것과 현재몸이 exact다. after 의상으로 새Nova몸을 통일하려면 이 몸체를 새로 제작하는 정책으로 기록해야 하며 renderer 변경이나 나나의 몸체 복사를 전제로 하지 않는다.',
  '218의5층은 현재 어두운3px만 남는다. 역사몸팽창1(1184셀)을 제거한 기존 규칙과 정확히 같고 나나의 큰 녹색 에너지면과 다르다. 세 점의 좌표·색을 출처로 기록하고 임의로 잡티 삭제하거나 나나와 같은 채움으로 확장하지 않는다.',
  '219는840px몸체의Manhattan2팽창,몸index6/테두리7이다. 220은0층의같은몸+5층황금효과2541px이며 역사규칙의395셀메움과외부형상보호를 정확재현했다. 새몸을 대입할 때 새실루엣·몸가림만 별도검토하고 전체FXbyteexact라고 쓰지 않는다.',
  '호버5짝은0층에옛공중39/37/45/47/41 및사격짝상체,5층에각원호버하체를 합친 현재정책과exact다. 절단행은worldY5/6/5/7/5이며6/7/8은빈층이다.5층을재킷이나불꽃으로취급하면다리가없어진다. 짝끼리5층하체는exact고0층의팔/총부분만다르다.',
  '호버추진불꽃은별도visual0x21/조립bank12/static0x10206·CLUT0x7802이며player원점/facing을쓴다. 15위상30파트와실소비6전체타일504..509는원US양자원/현재Shibuki양자원모두exact다. 새다리정합은불꽃을움직이지않고해당원점의위상별접점을따로검토한다.',
  '새원화입력에는현재5짝의원총구좌표를기준으로분리하되그림끝과탄환원점의일치를추측하지않는다. 실제원테이블direction0좌표는222(-27,-9),224(-29,-8),226(-20,-10),228(-17,-10),230(-24,-11)이고반대방향X만반전한다.',
  'PL02 213/214 빈6/7/8 조립레코드는115..118과공유한다.220 빈6/7/8은105/119/160/161과공유한다. 이빈층을변경해야하면원레코드수정으로공유소비자를오염시키지말고분기하며비대상을보호한다. 나머지217..230의raw공유는준비2짝·호버5짝과Nova4단독이고목표밖raw공유는없다.'
 ],
 'original_state_constraints':[
  '원 player_check_nova_strike는 shot_cooldown0, armor_parts bit2, weapon_energy[0]==0x30, air_action0, 진행방향벽충돌없음, GIGA새입력을 요구하고원표106을설정한다. 이조건은복장표시함수와별개다. 코드만으로모든캡슐전상태에서발동가능하다고보장하지않는다.',
  '발동시air_action5/spike면역/Nova활성/timer24를설정한다. engine+37이0인경우만에너지를0으로소모하며Ultimate표시는원체크를유지한다.',
  '원표106의213→215→216→214 준비 뒤 event80 전환,217 event40 충돌취소와event20 돌진발동으로이어진다. 발동에서visual/weapon0x16과팔레트0x49,속도±8을설정하며끝에서timer/벽조건으로복귀한다. 이읽기에서는원속도·상태·효과발생코드를변경하지않았다.'
 ],
 'producer_functions_called':False,'new_MIPS_executed':False,'runtime_verified':False,'new_art_accepted':False,'overall_complete':False,
 'limits':['현재그림과역사정책의관계를분류한읽기보고다. 새그림의미술수용/원화재구성/패킹/실기근거를대체하지않는다.','원코드는BR26에서실제추출한바이트와US원본을비교했다. disassembly를작성했지만새CPU실행은수행하지않았다.']
}
p=O/'conclusions.json';assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
inputs=dict(r['inputs'])
for q in [O/'report.json',p,Path(__file__),D/'audit_shibuki_nova_hover_relations01.py',D/'verify_shibuki_ultimate_hurt13_independent.py']+[ROOT/q['path']for q in r['readback_sheets']+codefiles]:inputs[rel(q)]=sha(q.read_bytes())
for name,h in inputs.items():assert sha((ROOT/name).read_bytes())==h,name
p=O/'READER_LOCK.json';assert not p.exists();p.write_text(json.dumps({'count':len(inputs),'inputs':inputs,'producer_functions_called':False,'source_writes':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'conclusions_sha256':sha((O/'conclusions.json').read_bytes()),'lock_sha256':sha(p.read_bytes()),'input_count':len(inputs)}))
