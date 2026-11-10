from pathlib import Path
D=Path(__file__).resolve().parent;S=D.parent/'root_nana_shot85'
s=(S/'register.py').read_text('utf8')
for a,b in [('d22a7b65432bd2b04bd2a934937a1787d420a69fbde0d3342a558a140aec5083','523729648a683362fe713ce7705084247cdbff0083613f9ef2c65010688ad661'),('standing shot','settling pose')]:
 assert a in s;s=s.replace(a,b)
p=D/'register.py';assert not p.exists();p.write_text(s,'utf8')
