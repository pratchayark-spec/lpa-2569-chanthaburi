import pandas as pd, numpy as np, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"
OUT=ROOT/"index.html"

def norm(s):
    if pd.isna(s): return ""
    return re.sub(r"\s+","",str(s).replace("\t","").replace("\n","")).strip()

def parse_lpa(path, year):
    d=pd.read_excel(path,header=None).iloc[14:,:24].copy()
    d=d[pd.to_numeric(d.iloc[:,0],errors="coerce").notna()].copy()
    d.columns=["rank","region","province","district","type","name","d1_full","d1_score","d1_pct","d2_full","d2_score","d2_pct","d3_full","d3_score","d3_pct","d4_full","d4_score","d4_pct","d5_full","d5_score","d5_pct","total_full","total_score","total_pct"]
    for c in ["region","province","district","type","name"]:
        d[c]=d[c].fillna("").astype(str).str.replace("\t","",regex=False).str.strip()
    d["key"]=d["name"].map(norm)
    return d

def parse_hpa(path):
    d=pd.read_excel(path,header=None).iloc[14:,:12].copy()
    d=d[pd.to_numeric(d.iloc[:,0],errors="coerce").notna()].copy()
    d.columns=["rank","region","province","district","type","name","full","score","pct","total_full","total_score","total_pct"]
    for c in ["region","province","district","type","name"]:
        d[c]=d[c].fillna("").astype(str).str.replace("\t","",regex=False).str.strip()
    d["key"]=d["name"].map(norm)
    return d

def parse_confirm(path):
    d=pd.read_excel(path,sheet_name="Sheet1",header=None).iloc[5:,:7].copy()
    d=d[pd.to_numeric(d.iloc[:,0],errors="coerce").notna()].copy()
    d.columns=["rank","province","district","name","confirmed","progress","note"]
    d["key"]=d["name"].map(norm)
    return d

def findrow(df,key):
    z=df[df.key==key]
    return z.iloc[0] if len(z) else None

def val(x):
    if x is None or pd.isna(x): return None
    try: return float(x)
    except: return str(x)

l68=parse_lpa(DATA/"LPA 2568.xlsx",2568)
l69=parse_lpa(DATA/"LPA 2569.xlsx",2569)
h68=parse_hpa(DATA/"HPA 2568.xlsx")
h69=parse_hpa(DATA/"HPA 2569.xlsx")
c68=parse_confirm(DATA/"ยืนยันข้อมูล 2568.xlsx")
c69=parse_confirm(DATA/"ยืนยันข้อมูล 2569.xlsx")

records=[]
for _,r in l69.iterrows():
    key=r.key; old=findrow(l68,key); oh=findrow(h68,key); nh=findrow(h69,key); oc=findrow(c68,key); nc=findrow(c69,key)
    def conf(q):
        if q is None: return "pending"
        if pd.notna(q.confirmed) and str(q.confirmed).strip() not in ("","0","nan"): return "confirmed"
        if pd.notna(q.progress) and str(q.progress).strip() not in ("","0","nan"): return "progress"
        return "pending"
    records.append({
      "rank":int(r["rank"]),"district":r["district"],"type":r["type"],"name":r["name"],"province":r["province"],
      "year68":{**{k:val(old[k+"_pct"]) if old is not None else None for k in ["d1","d2","d3","d4","d5"]},"total":val(old.total_pct) if old is not None else None},
      "year69":{**{k:val(r[k+"_pct"]) for k in ["d1","d2","d3","d4","d5"]},"total":val(r.total_pct)},
      "hpa68":val(oh.pct) if oh is not None else None,"hpa69":val(nh.pct) if nh is not None else None,
      "confirm68":conf(oc),"confirm69":conf(nc),
      "note68":val(oc.note) if oc is not None else None,"note69":val(nc.note) if nc is not None else None
    })

# Replace the data payload in index.html. The dashboard code is kept as the UI template.
text=OUT.read_text(encoding="utf-8")
payload=json.dumps(records,ensure_ascii=False,separators=(",",":"))
marker=re.compile(r"const DATA=\[.*?\];",re.S)
if marker.search(text):
    text=marker.sub("const DATA="+payload+";",text,count=1)
else:
    # fallback: append data object if a custom template is used
    text=text.replace("</body>","<script>const DATA="+payload+";</script></body>")
OUT.write_text(text,encoding="utf-8")
print("Updated",len(records),"organizations")
