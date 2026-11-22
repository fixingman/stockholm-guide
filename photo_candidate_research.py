"""No-send organizer photo research; suggestions are NOT identity approvals."""
import json
import base64
from io import BytesIO
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image

SOURCES = [
 {"title":"CHIMERA / EVOLVER","url":"https://fylkingen.se/en/events/chimera-evolver"},
 {"title":"Träden + Homegrown","url":"https://stadsgardsterminalen.com/event/traden-homegrown/"},
 {"title":"Changing Landscape","url":"https://fylkingen.se/en/events/changing-landscape-evolving-experiences"},
 {"title":"Pepparkakshus 2026","url":"https://arkdes.se/utstallningar/pepparkakshus-2026/"},
]
HEADERS={"User-Agent":"Mozilla/5.0 StockholmGuide-EditorialResearch/1.0"}
def get(url):
    response=requests.get(url,headers=HEADERS,timeout=20)
    response.raise_for_status()
    return response
def candidates(page):
    soup=BeautifulSoup(get(page).text,"html.parser")
    pool=[]
    for tag in soup.select('meta[property="og:image"],meta[name="twitter:image"],meta[name="twitter:image:src"]'):
        if tag.get("content"):pool.append(("meta",urljoin(page,tag["content"])))
    for tag in soup.find_all("img"):
        addr=tag.get("src") or tag.get("data-src")
        if addr:pool.append((tag.get("alt","")[:80],urljoin(page,addr)))
    for tag in soup.find_all("a"):
        caption=tag.get_text(" ",strip=True)
        if "CHIMERA" in caption.upper() and "EVOLVER" in caption.upper():
            url=urljoin(page,tag.get("href",""))
            if urlparse(url).hostname==urlparse(page).hostname and url!=page:
                print("EXACT_CHIMERA_PAGE",url,flush=True)
    unique={}
    for alt,url in pool:
        if url.startswith("https://") and url not in unique:
            unique[url]=alt
    return [{"url":url,"label":alt} for url,alt in list(unique.items())[:12]]
def inspect(item):
    result={"title":item["title"],"source":item["url"],"images":[]}
    try:
        found=candidates(item["url"])
    except Exception as exc:
        result["page_error"]=str(exc)[:220]
        return result
    for idx,c in enumerate(found):
        try:
            response=get(c["url"])
            img=Image.open(BytesIO(response.content))
            img.load()
            if idx == 0 and img.width>=500 and img.height>=300:
                preview=img.convert("RGB");preview.thumbnail((360,260))
                out=BytesIO();preview.save(out,"JPEG",quality=68)
                print("REVIEW_IMAGE",item["title"].replace(" ","_"),base64.b64encode(out.getvalue()).decode("ascii"),flush=True)
            if img.width>=500 and img.height>=300:
                result["images"].append({**c,"bytes":len(response.content),"size":[img.width,img.height],"format":img.format,"redirect":response.url})
        except Exception as exc:
            result["images"].append({**c,"error":str(exc)[:120]})
    return result
def main():
    out=[inspect(item) for item in SOURCES]
    print("CANDIDATES_JSON_START",flush=True)
    print(json.dumps(out,ensure_ascii=False,indent=2),flush=True)
    print("CANDIDATES_JSON_END",flush=True)
    with open("photo-candidates.json","w") as f:json.dump(out,f,ensure_ascii=False,indent=2)
if __name__=="__main__":main()
