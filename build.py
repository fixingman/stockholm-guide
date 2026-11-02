#!/usr/bin/env python3
"""Build and verify one edition. No email sender or recipient configuration exists here."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=BASE / 'guide_data.json')
    parser.add_argument('--asset-base-url', default='https://fixingman.github.io/stockholm-guide/assets')
    parser.add_argument('--output-dir', type=Path, default=BASE / 'build')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'ready_for_delivery': False, 'steps': []}
    # Clear a previous success marker before reading inputs or running commands.
    manifest_path = output / 'build-report.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    try:
        for key, path in [('data', args.data), ('template', BASE / 'template.html.j2'),
                          ('reference', BASE / 'milestone-reference.png')]:
            manifest[key + '_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        manifest['error'] = str(error)
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        print('Build input missing:', error)
        return 1
    commands = [
        ['render.py', '--data', str(args.data.resolve()), '--output', str(output / 'preview.html')],
        ['render.py', '--data', str(args.data.resolve()), '--output', str(output / 'email.html'), '--asset-base-url', args.asset_base_url],
        ['qa.py', '--html', str(output / 'preview.html'), '--data', str(args.data.resolve()), '--output-dir', str(output / 'renders')],
        ['preflight.py', '--html', str(output / 'email.html'), '--data', str(args.data.resolve()), '--report', str(output / 'delivery-report.json')],
    ]
    shutil.copytree(BASE / 'assets', output / 'assets', dirs_exist_ok=True)
    for command in commands:
        result = subprocess.run([sys.executable, str(BASE / command[0]), *command[1:]])
        manifest['steps'].append({'command': command[0], 'exit_code': result.returncode})
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
        if result.returncode:
            print('Build is not ready for delivery; see', manifest_path)
            return result.returncode
    manifest['ready_for_delivery'] = True
    manifest['email_sha256'] = hashlib.sha256((output / 'email.html').read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print('Build and live image checks passed. No email sent.', manifest_path)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
