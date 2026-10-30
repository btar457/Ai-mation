import re
L=[l.split(': ') for l in open('sil.txt')]
starts=[float(v) for k,v in L if k=='silence_start']; ends=[float(v) for k,v in L if k=='silence_end']
segs=[]; s=0.0
for a,b in zip(starts,ends):
    if a-s>0.05: segs.append((s,a))
    s=b
segs.append((s,73.95))
P=open('phrases.txt',encoding='utf-8').read().strip().split('\n')
n,m=len(P),len(segs)
w=[len(re.sub(r"[\s\u064B-\u0652،.:؟]","",p.replace("1916","الفوتسعمئةوستةعشر").replace("1926","الفوتسعمئةوستةوعشرين")))+1 for p in P]
_=[len(re.sub(r'[\sً-ْ،.:؟]','',p))+1 for p in P]
tot=sum(e-s for s,e in segs); rate=tot/sum(w)
INF=1e18
dp=[[INF]*(m+1) for _ in range(n+1)]; bk=[[0]*(m+1) for _ in range(n+1)]
dp[0][0]=0
for i in range(1,n+1):
  for j in range(1,m+1):
    for k in range(i-1,j):
      if dp[i-1][k]==INF: continue
      d=sum(e-s for s,e in segs[k:j])
      c=dp[i-1][k]+(d-w[i-1]*rate)**2
      if c<dp[i][j]: dp[i][j]=c; bk[i][j]=k
j=m; res=[]
for i in range(n,0,-1):
  k=bk[i][j]; res.append((segs[k][0],segs[j-1][1])); j=k
res.reverse()
import json
out=[{'t':P[i],'s':round(a,2),'e':round(b,2)} for i,(a,b) in enumerate(res)]
for o in out: print(o['s'],o['e'],o['t'])
json.dump(out,open('src/subs.json','w',encoding='utf-8'),ensure_ascii=False)
