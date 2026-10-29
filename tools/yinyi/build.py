# -*- coding: utf-8 -*-
"""Build the 音译 (transliteration) variant of the 亚共版 Chinese localization.

Sources
-------
* sources/yinyi/*.json  : the human-made transliteration corpus
                           (extracted from the Steam Workshop mod
                           "TerrariaTransliteratedEdition" by HoCha113)
* backup_en/en-US*.json : the English original, used as the key universe and
                           as the input for machine transliteration
* zh-Hans*.json         : the current 亚共版 translation, used as the key
                           universe (it also carries a few keys the English
                           files no longer have)

Every key covered by the corpus is copied verbatim. Keys the corpus does not
cover are transliterated with tools/yinyi/translit.py, reusing the corpus as a
word/phrase memory so that the machine output stays consistent with the human
output (e.g. "Adamantite" always becomes 阿戴慢泰特).
"""

from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOURCES = os.path.join(ROOT, "sources", "yinyi")
sys.path.insert(0, HERE)

from translit import Transliterator, TOKEN_RE, HAS_LATIN  # noqa: E402

PAIRS = [
    ("zh-Hans.json", "Main.json", "en-US.json"),
    ("zh-Hans.Items.json", "Items.json", "en-US.Items.json"),
    ("zh-Hans.Game.json", "Game.json", "en-US.Game.json"),
    ("zh-Hans.NPCs.json", "NPCs.json", "en-US.NPCs.json"),
    ("zh-Hans.Projectiles.json", "Projectiles.json", "en-US.Projectiles.json"),
    ("zh-Hans.Town.json", "Town.json", "en-US.Town.json"),
    ("zh-Hans.Legacy.json", "Legacy.json", "en-US.Legacy.json"),
    ("zh-Hans.Mobile.json", None, "en-US.Mobile.json"),
    ("zh-Hans.PS4.json", None, "en-US.PS4.json"),
    ("zh-Hans.Switch.json", None, "en-US.Switch.json"),
    ("zh-Hans.XBO.json", None, "en-US.XBO.json"),
]

TRAILING_COMMA = re.compile(r",\s*([}\]])")
HANZI = re.compile(r"[\u4e00-\u9fff]")
WORD_ONLY = re.compile(r"^[A-Za-z][A-Za-z'\-]*$")


def load_json(path: str):
    raw = open(path, "rb").read().decode("utf-8-sig")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(TRAILING_COMMA.sub(r"\1", raw))


def walk(node, path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, path + (k,))
    else:
        yield path, node


def set_path(tree, path, value):
    node = tree
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value


def build_memory(corpus_pairs):
    """Learn word-level and phrase-level transliterations from the corpus."""
    word_counts = {}
    phrase = {}
    total = 0
    for en_tree, zy_tree in corpus_pairs:
        for path, zh in walk(zy_tree):
            if not isinstance(zh, str) or not zh:
                continue
            en = en_tree
            for key in path:
                if not isinstance(en, dict) or key not in en:
                    en = None
                    break
                en = en[key]
            if not isinstance(en, str) or not en:
                continue
            total += 1
            if HAS_LATIN.search(zh):
                continue
            key = en.strip().lower()
            if WORD_ONLY.match(key) and len(zh) <= 12:
                word_counts.setdefault(key, {}).setdefault(zh, 0)
                word_counts[key][zh] += 1
            elif len(key) <= 120 and "{" not in key and "[" not in key:
                phrase.setdefault(key, {}).setdefault(zh, 0)
                phrase[key][zh] += 1
    word_memory = {k: max(v.items(), key=lambda kv: kv[1])[0] for k, v in word_counts.items()}
    phrase_memory = {k: max(v.items(), key=lambda kv: kv[1])[0] for k, v in phrase.items()}
    return word_memory, phrase_memory, total


SPACE_FIX = [
    (re.compile(r"[ \t]{2,}"), " "),
    (re.compile(r"\s+([,.;:!?，。；：！？、])"), r"\1"),
    (re.compile(r"([（(])\s+"), r"\1"),
]


def polish(text: str) -> str:
    for pattern, repl in SPACE_FIX:
        text = pattern.sub(repl, text)
    return text.strip() if text.strip() else text


def tokens(text: str):
    return sorted(m.group(0) for m in TOKEN_RE.finditer(text))


def restore_tokens(zh_ref: str, value: str) -> str:
    """Re-insert rich-text tags (icons, {$Keys}) the source text dropped.

    The 亚共版 Chinese references the icons; the transliteration starts from the
    English, which has none.  Each missing tag is parked right after the tag
    that precedes it in the Chinese, so "{0}[i:58]" stays together.
    """
    ref = [(m.start(), m.end(), m.group(0)) for m in TOKEN_RE.finditer(zh_ref)]
    cur = [(m.start(), m.end(), m.group(0)) for m in TOKEN_RE.finditer(value)]
    if not ref:
        return value
    have, need = {}, {}
    for _, _, t in cur:
        have[t] = have.get(t, 0) + 1
    for _, _, t in ref:
        need[t] = need.get(t, 0) + 1
    missing = {t: n - have.get(t, 0) for t, n in need.items() if n > have.get(t, 0)}
    if not missing:
        return value

    pos_by_token = {}
    for start, end, t in cur:
        pos_by_token.setdefault(t, []).append((start, end))

    inserts, seen, prev = [], {}, None
    for _, _, t in ref:
        seen[t] = seen.get(t, 0) + 1
        if missing.get(t, 0) > 0:
            if prev is not None and prev in pos_by_token:
                k = min(seen.get(prev, 1), len(pos_by_token[prev]))
                inserts.append((pos_by_token[prev][k - 1][1], t))
                missing[t] -= 1
            # tags with no anchor are dropped: guessing a position reads worse
            # than a missing icon
        prev = t

    result = value
    for pos, tok in reversed(sorted(inserts, key=lambda item: item[0])):
        result = result[:pos] + tok + result[pos:]
    return result


HAN_ONLY = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")


def _icon_fragment(line: str) -> str:
    """Keep the icons/placeholders of a line, drop its Chinese words.

    Only icon-dense lines survive: a line whose Chinese carries the meaning
    would read as half-translated garbage once the words are removed.
    """
    frag = HAN_ONLY.sub("", line)
    frag = frag.replace("()", "").replace("（）", "").replace("[]", "")
    frag = re.sub(r"\s{2,}", " ", frag).strip()
    if "[" not in frag and "{" not in frag:
        return ""
    dense = len(re.sub(r"\s", "", frag))
    total = len(re.sub(r"\s", "", line))
    if total and dense / total < 0.55:
        return ""
    return frag


def restore_tokens_by_line(zh_ref: str, value: str) -> str:
    """Restore tags line by line, keeping 亚共版-only icon rows at the end."""
    if "\n" not in zh_ref and "\n" not in value:
        return restore_tokens(zh_ref, value)

    zh_lines, out_lines = zh_ref.split("\n"), value.split("\n")
    if len(zh_lines) == len(out_lines):
        return "\n".join(restore_tokens(a, b) for a, b in zip(zh_lines, out_lines))

    if len(zh_lines) > len(out_lines):
        restored = [
            restore_tokens(zh, out) if out.strip() else out
            for zh, out in zip(zh_lines, out_lines)
        ]
        extra = [frag for frag in (_icon_fragment(line) for line in zh_lines[len(out_lines):]) if frag]
        if extra:
            restored.extend(extra)
        return "\n".join(restored)
    return value


LANGUAGE_LABEL = "音译版（整活）"
LANGUAGE_LABEL_EN = "Yinyi (Meme)"
EXTRA_DIR = os.path.join(ROOT, "yinyi-extra")

LABEL_RE = re.compile(r'("Japanese"\s*:\s*)"(?:[^"\\]|\\.)*"')


def label_backup_languages() -> None:
    """Rename the hijacked culture in every language file the pipeline injects."""
    main_file = os.path.join(ROOT, "zh-Hans.json")
    if os.path.exists(main_file):
        raw = open(main_file, "rb").read().decode("utf-8-sig")
        patched, count = LABEL_RE.subn(
            lambda m: m.group(1) + json.dumps(LANGUAGE_LABEL, ensure_ascii=False), raw, count=1
        )
        if count and patched != raw:
            with open(main_file, "w", encoding="utf-8", newline="") as fh:
                fh.write(patched)

    for folder in ("backup_en", "backup_else"):
        directory = os.path.join(ROOT, folder)
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            if not name.endswith(".json"):
                continue
            path = os.path.join(directory, name)
            raw = open(path, "rb").read().decode("utf-8-sig")
            if '"Japanese"' not in raw:
                continue
            label = LANGUAGE_LABEL if name.startswith("zh-Hans") else LANGUAGE_LABEL_EN
            patched, count = LABEL_RE.subn(lambda m: m.group(1) + json.dumps(label, ensure_ascii=False), raw, count=1)
            if count and patched != raw:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(patched)


def main():
    corpus_pairs = []
    for _, mod_name, _ in PAIRS:
        if not mod_name:
            continue
        path = os.path.join(SOURCES, mod_name)
        if os.path.exists(path):
            corpus_pairs.append(load_json(path))

    source_pairs = []
    for repo_name, mod_name, en_name in PAIRS:
        en_path = os.path.join(ROOT, "backup_en", en_name)
        en_tree = load_json(en_path) if os.path.exists(en_path) else {}
        mod_tree = {}
        if mod_name and os.path.exists(os.path.join(SOURCES, mod_name)):
            mod_tree = load_json(os.path.join(SOURCES, mod_name))
        source_pairs.append((repo_name, en_tree, mod_tree))

    word_memory, phrase_memory, learned = build_memory(
        [(en, mod) for _, en, mod in source_pairs if mod]
    )
    labels_path = os.path.join(HERE, "language-labels.json")
    language_labels = load_json(labels_path) if os.path.exists(labels_path) else None

    overrides_path = os.path.join(HERE, "overrides.json")
    overrides = load_json(overrides_path) if os.path.exists(overrides_path) else {}
    tr = Transliterator(
        phrase_memory=phrase_memory, word_memory=word_memory, overrides=overrides
    )

    stats = {
        "learned": learned,
        "words": len(word_memory),
        "phrases": len(phrase_memory),
        "overrides": len(overrides),
    }
    total_corpus = total_generated = total_kept = total_restored = token_issues = 0
    samples = []

    os.makedirs(EXTRA_DIR, exist_ok=True)
    written = {}
    for repo_name, en_tree, mod_tree in source_pairs:
        target_path = os.path.join(ROOT, repo_name)
        zh_tree = load_json(target_path)
        out = {}
        for path, zh in walk(zh_tree):
            en = en_tree
            for key in path:
                en = en[key] if isinstance(en, dict) and key in en else None
                if en is None:
                    break

            mod_value = mod_tree
            for key in path:
                mod_value = mod_value[key] if isinstance(mod_value, dict) and key in mod_value else None
                if mod_value is None:
                    break

            if isinstance(mod_value, str) and mod_value:
                if (
                    isinstance(en, str)
                    and en
                    and HAS_LATIN.search(en)
                    and tokens(en)
                    and tokens(en) != tokens(mod_value)
                ):
                    # the corpus dropped/rewrote rich-text tags (icons, {$Keys}):
                    # rebuild the line word by word so the tags survive
                    value = polish(tr(en, phrase=False))
                    total_restored += 1
                else:
                    value = mod_value
                    total_corpus += 1
            elif isinstance(en, str) and en and HAS_LATIN.search(en):
                value = polish(tr(en))
                total_generated += 1
                if len(samples) < 400:
                    samples.append([repo_name, ".".join(path), en, value])
            elif isinstance(zh, str) and HAS_LATIN.search(zh) and not HANZI.search(zh):
                # no English source (credits, custom keys): transliterate what is there
                value = polish(tr(zh))
                total_generated += 1
                if len(samples) < 400:
                    samples.append([repo_name, ".".join(path), zh, value])
            else:
                value = zh
                total_kept += 1

            if isinstance(en, str) and isinstance(value, str) and value != zh:
                if tokens(en) != tokens(value) and tokens(value):
                    token_issues += 1
            if isinstance(zh, str) and isinstance(value, str) and value != zh:
                value = restore_tokens_by_line(zh, value)
            set_path(out, path, value)

        if repo_name == "zh-Hans.json" and language_labels:
            # keep the 亚共版 language-picker text exactly as CSFT ships it
            out["Language"] = dict(language_labels)
        text = json.dumps(out, ensure_ascii=False, indent="\t")
        text = text.replace("\n", "\r\n") + "\r\n"
        extra_name = repo_name.replace("zh-Hans", "de-DE", 1)
        with open(os.path.join(EXTRA_DIR, extra_name), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        written[extra_name] = text


    stats.update(
        corpus=total_corpus,
        restored=total_restored,
        generated=total_generated,
        kept=total_kept,
        token_issues=token_issues,
        samples=len(samples),
    )
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    with open(os.path.join(HERE, "last-build-report.json"), "w", encoding="utf-8") as fh:
        json.dump({"stats": stats, "samples": samples}, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
