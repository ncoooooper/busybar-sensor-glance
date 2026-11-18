"""Read timestamped wearable measurements from selected Home Assistant entities."""
import os,json,time
from datetime import datetime,timezone
from urllib.parse import quote
from urllib.request import Request,urlopen
from serve import page
INTERVAL=5
METRICS={"hr":("HEART RATE","bpm",60),"stress":("STRESS","",300),"spo2":("OXYGEN","%",300),"vo2":("VO2 MAX","",2592000)}
def snapshot(o,m):
    pages=[]
    if o.get("bluetooth_name"):
        from broadcast import reading
        pages.append(reading(o["bluetooth_name"],m))
    for key,eid in o.get("entities",{}).items():
        title,unit,limit=METRICS[key]
        try:
            url=o["home_assistant"].rstrip("/")+"/api/states/"+quote(eid,safe="")
            with urlopen(Request(url,headers={"Authorization":"Bearer "+os.environ["HA_TOKEN"]}),timeout=6) as r:d=json.load(r)
            value=float(d["state"]);t=datetime.fromisoformat(d["last_updated"].replace("Z","+00:00"));age=(datetime.now(timezone.utc)-t).total_seconds()
            old=age>o.get("max_age_seconds",{}).get(key,limit)
            source_unit=d.get("attributes",{}).get("unit_of_measurement") or unit
            pages.append(page(title,"Stale" if old else f"{value:g}"+unit,f"{value:g} {source_unit}",t.strftime("%Y-%m-%d %H:%M UTC"),"Last estimate" if key=="vo2" else "Sensor observation"))
        except (KeyError,ValueError,OSError):pages.append(page(title,"No data",eid,"Check sensor and pairing"))
    return dict(state="Wearable measurements",key=str([(p["caption"],p["value"]) for p in pages]),pages=pages)
