#!/usr/bin/env python3
"""Read-only delivery readiness checks. This module cannot send email."""
import argparse
import hashlib
import io
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from PIL import Image

BASE = Path(__file__).resolve().parent

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == 'img':
            self.urls.append(fields.get('src', ''))
        if fields.get('background'):
            self.urls.append(fields['background'])

def check_image(url, opener=urlopen):
    if urlparse(url).scheme != 'https' or not urlparse(url).netloc:
        return {'url': url, 'ok': False, 'error': 'Email image URL must be absolute HTTPS'}
    try:
        with opener(Request(url, headers={'User-Agent': 'StockholmGuide-Preflight/1.0'}), timeout=25) as response:
            status = response.status
            mime = response.headers.get_content_type()
            content = response.read(12_000_001)
        if status != 200 or not mime.startswith('image/'):
            raise ValueError(f'Expected HTTP 200 image response, got {status} {mime}')
        if len(content) > 12_000_000:
            raise ValueError('Image exceeds 12 MB')
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
        return {'url': url, 'ok': True, 'status': status, 'mime': mime,
                'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest()}
    except Exception as error:
        return {'url': url, 'ok': False, 'error': str(error)}

def inspect(html, data, image_checker=check_image):
    images = Images()
    images.feed(html)
    results = [image_checker(url) for url in dict.fromkeys(images.urls)]
    unresolved = [{'section': section, 'title': item['title']}
                  for section in ('top3', 'new_discoveries') for item in data[section]
                  if not item.get('image_url') or item.get('image_verified') is not True]
    failures = []
    by_url = {result['url']: result for result in results}
    by_name = {Path(urlparse(result['url']).path).name: result for result in results}
    for section in ('top3', 'new_discoveries'):
        for item in data[section]:
            filename = item.get('image_cache_file')
            source_hash = item.get('image_source_sha256')
            if source_hash and not filename:
                actual_source = by_url.get(item['image_url'])
                if not actual_source or actual_source.get('sha256') != source_hash:
                    failures.append(f"Official image missing or changed since identity review: {item['title']}")
            if item.get('image_verified') is True and filename:
                actual = by_name.get(filename)
                if not actual or actual.get('sha256') != item.get('image_cache_sha256'):
                    failures.append(f"Published verified image missing or bytes differ: {item['title']}")
    if unresolved:
        failures.append(f'{len(unresolved)} visible event image slots still lack verified photographs')
    if not images.urls:
        failures.append('No image elements in email HTML')
    if any(not result['ok'] for result in results):
        failures.append('One or more production image URLs failed a live HTTP/decode check')
    if len(html.encode('utf-8')) >= 100_000:
        failures.append('HTML is too close to Gmail clipping size')
    # A passing browser run alone cannot attest to a reference that was never supplied.
    reference = BASE / 'milestone-reference.png'
    if not reference.is_file():
        failures.append('Approved milestone image has not been captured in the repository')
    else:
        spec = json.loads((BASE / 'layout-spec.json').read_text())
        if hashlib.sha256(reference.read_bytes()).hexdigest() != spec['reference_sha256']:
            failures.append('Milestone reference differs from the recorded layout specification')
    return {'ready_for_delivery': not failures, 'failures': failures,
            'unresolved_event_image_slots': unresolved, 'images': results,
            'html_bytes': len(html.encode('utf-8')),
            'note': 'Live HTTP/decode checks, not Gmail rendering certification. No email sent.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, default=BASE / 'email.html')
    parser.add_argument('--data', type=Path, default=BASE / 'guide_data.json')
    parser.add_argument('--report', type=Path, default=BASE / 'delivery-report.json')
    args = parser.parse_args()
    report = inspect(args.html.read_text(), json.loads(args.data.read_text()))
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'ready_for_delivery': report['ready_for_delivery'], 'failures': report['failures']}))
    return 0 if report['ready_for_delivery'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
