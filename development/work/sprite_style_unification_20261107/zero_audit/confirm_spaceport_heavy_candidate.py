"""Bind static US heavy contact candidate to RN18, without running the game."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
D=Path(__file__).parent; O=D/'nana_hurt_triggers01'
sha=lambda b:hashlib.sha256(b).hexdigest()
current=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v18/rin_nana.bin'
with current.open('rb')as f: bh=hashlib.file_digest(f,'sha256').hexdigest()
assert bh=='0f40463b883e00a7e3acf268fd45052b905d0454440d8c5436ce24fe80f58c95'
us,_=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61',));rn,_=read_disc(current,('SLUS_005.61',))
u=us['SLUS_005.61'];r=rn['SLUS_005.61']; base=struct.unpack_from('<I',u,24)[0]
at=lambda e,a,n:e[a-base+2048:a-base+2048+n]
ranges=[('dash_gunner_init_and_update',0x800586f0,0x80059d00),('main_allocator',0x8002ab74,0x8002ac50),('contact_damage',0x8002d9bc,0x8002dd04),('hurt_init',0x80033d54,0x80033ec0),('stage10_records',0x800f81ec,0x800f81ec+62*8),('dispatch',0x800f24a4+0x1b*4,0x800f24a4+0x1b*4+4)]
checks=[]
for name,start,end in ranges:
    a=at(u,start,end-start);assert a==at(r,start,end-start)
    checks.append({'name':name,'start':hex(start),'end':hex(end),'sha256':sha(a),'RN18_exact':True})
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
init=list(md.disasm(at(u,0x80058700,0x80058ab0-0x80058700),0x80058700))
subtype_stores=[{'pc':hex(i.address),'mnemonic':i.mnemonic,'operands':i.op_str}for i in init if i.mnemonic=='sb'and ', 2('in i.op_str]
assert not subtype_stores
records=[]
for i in range(62):
    rec=at(u,0x800f81ec+i*8,8)
    area,kind,subtype,flag,x,y=struct.unpack('<BBBBHH',rec)
    if area==0xff:break
    if kind==0x1b:records.append({'index':i,'address':hex(0x800f81ec+i*8),'bytes':rec.hex(),'area':area,'kind':kind,'subtype':subtype,'flags':flag,'x':x,'y':y})
assert records[:2]==[dict(records[0],x=2216,y=2176,subtype=8),dict(records[1],x=2168,y=2224,subtype=8)]
ins=[{'pc':hex(i.address),'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}for i in md.disasm(at(u,0x800589d0,0x7c),0x800589d0)]
report={'scope':'원US 우주항 강한 일반 접촉피격 후보의 코드·배치와 RN18 동일성 읽기. 실기/자동조작 없음.',
 'bin':{'path':current.relative_to(ROOT).as_posix(),'sha256':bh,'exe_sha256':sha(r)},'original_exe_sha256':sha(u),
 'ranges':checks,'stage10_dash_gunner_records':records,'damage_initializer_instructions':ins,
 'subtype_is_preserved_by_initializer':not subtype_stores,
 'candidate':{'object_id':27,'symbol':'dash_gunner_update','closest_by_x':{'x':2168,'y':2224,'subtype':8},'other_nearby':{'x':2216,'y':2176,'subtype':8},'contact_damage':6,'hurt_kind':0,'basic_without_body_armor':{'hurt_type':2,'animation':34,'references':[106,110,111,112,113,114]},'with_body_armor':{'hurt_type':4,'animation':35}},
 'evidence':['초기화가 subtype0..3 또는8..11에 +0x60=6을 쓴다(0x800589D0..589F4). 그 밖 subtype은7이다.','main allocator의 +0x62=0 초기값과 dash_gunner 함수 구간에 +0x62 쓰기가 없음을 앞 native_read/heavy_native_read에서 확인했다.','충돌 본체는 0x80058BDC/58BF0에서 원 contact damage를 호출한다. 투사체 피해를 이 값으로 간주하지 않는다.'],
 'prior_evidence':[{'path':(O/n).relative_to(ROOT).as_posix(),'sha256':sha((O/n).read_bytes())}for n in('native_read.json','trigger_plan.json','heavy_native_read.json')],
 'limits':['최소 x 배치에 근거한 다음 지상 후보이며 실제 이동 경로·발판·스크롤 생성 시각·안전 통과는 미검증이다.','실제 충돌·무적 종료·HP 유지 등 런타임 조건은 부모 실기에서 확인해야 한다.','몸통아머 type0 접촉은 원피해6이어도 type4 우선이므로 포스110..114의 재현 후보로 확대하지 않는다.']}
p=O/'heavy_candidate_RN18.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p.read_bytes()))
