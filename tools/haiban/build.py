# -*- coding: utf-8 -*-
"""Build the 害人汉化 (troll text) variant by overlaying sources/haiban onto the CSFT Chinese."""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOURCES = os.path.join(ROOT, 'sources', 'haiban')
OUT = os.path.join(ROOT, 'haiban-extra')
LABELS = json.load(open(os.path.join(ROOT, 'tools', 'yinyi', 'language-labels.json'), encoding='utf-8'))

MAP = [('Main.json', ''), ('Items.json', '.Items'), ('Game.json', '.Game'),
       ('NPCs.json', '.NPCs'), ('Legacy.json', '.Legacy'), ('Projectiles.json', '.Projectiles')]
COPY = ['.Mobile', '.PS4', '.Switch', '.Town', '.XBO']


def load(path):
    text = open(path, 'rb').read().decode('utf-8-sig')
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(re.sub(r',\s*([}\]])', r'\1', text))


def dump(data):
    return json.dumps(data, ensure_ascii=False, indent='\t').replace('\n', '\r\n') + '\r\n'


def main():
    os.makedirs(OUT, exist_ok=True)
    applied = skipped = 0
    for name, suffix in MAP:
        pack = load(os.path.join(SOURCES, name))
        base = load(os.path.join(ROOT, 'zh-Hans' + suffix + '.json'))
        for category, values in pack.items():
            if category == 'Language' or not isinstance(values, dict):
                continue
            target = base.get(category)
            if not isinstance(target, dict):
                continue
            for key, value in values.items():
                if key in target:
                    target[key] = value
                    applied += 1
                else:
                    skipped += 1
        base['Language'] = dict(LABELS)
        with open(os.path.join(OUT, 'it-IT' + suffix + '.json'), 'w', encoding='utf-8', newline='') as fh:
            fh.write(dump(base))
    for suffix in COPY:
        src = os.path.join(ROOT, 'zh-Hans' + suffix + '.json')
        if not os.path.exists(src):
            continue
        data = load(src)
        data['Language'] = dict(LABELS)
        with open(os.path.join(OUT, 'it-IT' + suffix + '.json'), 'w', encoding='utf-8', newline='') as fh:
            fh.write(dump(data))
    print('applied=%d skipped=%d' % (applied, skipped))


if __name__ == '__main__':
    main()