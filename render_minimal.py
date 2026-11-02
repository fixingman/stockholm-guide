#!/usr/bin/env python3
"""Render the alternate minimal design from the same factual data. Never sends email."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parent
def render(data_path, output_path, asset_base_url):
    guide = json.loads(Path(data_path).read_text(encoding="utf-8"))
    for section in ("top3", "new_discoveries", "worth_reconsidering", "unavailable"):
        assert guide.get(section), f"Missing section: {section}"
        for i, item in enumerate(guide[section]):
            fields = ("title", "dates", "url", "price", "booking") if section=="unavailable" else ("title","dates","url","price","booking","description","venue")
            assert all(item.get(key) for key in fields), f"Missing event data: {section}[{i}]"
            assert urlparse(item["url"]).scheme == "https", f"Invalid event link: {section}[{i}]"
    assert len(guide["top3"]) == 3, "Exactly three featured picks required"
    assert asset_base_url.startswith("https://") or asset_base_url == "../assets", "Asset host must be HTTPS or a local preview path"
    env=Environment(loader=FileSystemLoader(ROOT),undefined=StrictUndefined,autoescape=select_autoescape(default=True))
    result=env.get_template("minimal_template.html.j2").render(guide=guide,asset_base_url=asset_base_url.rstrip("/"))
    Path(output_path).parent.mkdir(parents=True,exist_ok=True)
    Path(output_path).write_text(result,encoding="utf-8")
    return guide,result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",default=str(ROOT/"guide_data.json"))
    parser.add_argument("--output",default=str(ROOT/"minimal-preview.html"))
    parser.add_argument("--asset-base-url",default="https://fixingman.github.io/stockholm-guide/assets")
    args=parser.parse_args()
    guide,result=render(args.data,args.output,args.asset_base_url)
    print(f"Rendered {sum(len(guide[k]) for k in ('top3','new_discoveries','worth_reconsidering','unavailable'))} entries, {len(result.encode())} bytes to {args.output}")

if __name__=="__main__":
    main()
