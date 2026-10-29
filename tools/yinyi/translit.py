# -*- coding: utf-8 -*-
"""English -> Chinese syllable transliteration (音译) engine.

The point is phonetic, not semantic: an English word is turned into Chinese
syllables that sound like the English original, so reading it aloud
reproduces the English pronunciation while the meaning is gone (谐音梗).

Terraria rich-text tokens ({0}, [i:123], {$Key}, <interact>, URLs) are
protected and passed through untouched.
"""

from __future__ import annotations

import re

TOKEN_RE = re.compile(
    r"(\{[^{}]*\}"
    r"|\[[^\[\]]*\]"
    r"|<[^<>\n]{1,40}>"
    r"|https?://[^\s]+)"
)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
HAS_LATIN = re.compile(r"[A-Za-z]")

VOWELS = "aeiouy"

VOWEL_GROUP = {
    "a": "阿", "e": "埃", "i": "伊", "o": "奥", "u": "乌", "y": "伊",
    "ai": "艾", "ay": "艾", "au": "奥", "aw": "奥",
    "ea": "伊", "ee": "伊", "ei": "埃", "ey": "埃", "eu": "优", "ew": "优",
    "ie": "艾", "io": "伊奥", "ia": "伊阿", "iu": "优",
    "oa": "欧", "oi": "奥伊", "oo": "乌", "ou": "欧", "ow": "奥", "oy": "奥伊",
    "ue": "优", "ui": "威", "uo": "沃",
    "eye": "艾", "ye": "耶", "you": "尤", "eau": "欧", "iew": "优",
}

CONSONANT = {
    "b": "布", "c": "克", "d": "德", "f": "弗", "g": "格", "h": "赫",
    "j": "吉", "k": "克", "l": "勒", "m": "姆", "n": "恩", "p": "普",
    "q": "克", "r": "尔", "s": "斯", "t": "特", "v": "弗", "w": "沃",
    "x": "克斯", "y": "伊", "z": "兹",
}

CV = {
    "ba": "巴", "be": "贝", "bi": "比", "bo": "博", "bu": "布", "by": "比",
    "ca": "卡", "ce": "塞", "ci": "西", "co": "科", "cu": "库", "cy": "西",
    "da": "达", "de": "德", "di": "迪", "do": "多", "du": "杜", "dy": "迪",
    "fa": "法", "fe": "费", "fi": "菲", "fo": "福", "fu": "福", "fy": "菲",
    "ga": "加", "ge": "格", "gi": "吉", "go": "戈", "gu": "古", "gy": "吉",
    "ha": "哈", "he": "赫", "hi": "希", "ho": "霍", "hu": "胡", "hy": "希",
    "ja": "贾", "je": "杰", "ji": "吉", "jo": "乔", "ju": "朱", "jy": "吉",
    "ka": "卡", "ke": "克", "ki": "基", "ko": "科", "ku": "库", "ky": "基",
    "la": "拉", "le": "勒", "li": "利", "lo": "洛", "lu": "卢", "ly": "利",
    "ma": "马", "me": "梅", "mi": "米", "mo": "莫", "mu": "穆", "my": "米",
    "na": "纳", "ne": "内", "ni": "尼", "no": "诺", "nu": "努", "ny": "尼",
    "pa": "帕", "pe": "佩", "pi": "皮", "po": "波", "pu": "普", "py": "皮",
    "qa": "夸", "qe": "奎", "qi": "奎", "qo": "阔", "qu": "库", "qy": "奎",
    "ra": "拉", "re": "瑞", "ri": "里", "ro": "罗", "ru": "鲁", "ry": "里",
    "sa": "萨", "se": "塞", "si": "斯", "so": "索", "su": "苏", "sy": "西",
    "ta": "塔", "te": "特", "ti": "蒂", "to": "托", "tu": "图", "ty": "蒂",
    "va": "瓦", "ve": "维", "vi": "维", "vo": "沃", "vu": "武", "vy": "维",
    "wa": "瓦", "we": "韦", "wi": "威", "wo": "沃", "wu": "武", "wy": "威",
    "xa": "扎", "xe": "泽", "xi": "西", "xo": "佐", "xu": "祖", "xy": "西",
    "ya": "亚", "ye": "耶", "yi": "伊", "yo": "约", "yu": "尤", "yy": "伊",
    "za": "扎", "ze": "泽", "zi": "齐", "zo": "佐", "zu": "祖", "zy": "齐",
    "cha": "查", "che": "切", "chi": "奇", "cho": "乔", "chu": "楚", "chy": "奇",
    "sha": "沙", "she": "舍", "shi": "希", "sho": "肖", "shu": "舒", "shy": "希",
    "tha": "萨", "the": "泽", "thi": "西", "tho": "索", "thu": "苏", "thy": "西",
    "pha": "法", "phe": "菲", "phi": "菲", "pho": "福", "phu": "弗", "phy": "菲",
    "wha": "瓦", "whe": "韦", "whi": "威", "who": "胡", "whu": "武", "why": "威",
    "qua": "夸", "que": "奎", "qui": "奎", "quo": "阔", "quy": "奎",
    "kna": "纳", "kne": "内", "kni": "尼", "kno": "诺", "knu": "努",
    "wra": "拉", "wre": "雷", "wri": "里", "wro": "罗", "wru": "鲁",
    "bai": "拜", "bei": "贝", "boo": "布", "bou": "波", "bee": "比", "bea": "比",
    "cai": "凯", "cee": "西", "coo": "库", "cou": "库", "cea": "西", "cau": "考",
    "dai": "戴", "dee": "迪", "dou": "多", "doo": "杜", "dea": "迪", "dau": "道",
    "fai": "法", "fee": "菲", "foo": "福", "fou": "福", "fea": "菲",
    "gai": "盖", "gee": "吉", "goo": "古", "gou": "古", "gea": "吉",
    "hai": "海", "hee": "希", "hoo": "胡", "hou": "豪", "hea": "希",
    "jai": "杰", "jee": "吉", "joo": "朱", "jou": "乔",
    "kai": "凯", "kee": "基", "koo": "库", "kou": "考",
    "lai": "莱", "lee": "利", "loo": "卢", "lou": "卢", "lea": "利", "lau": "劳",
    "mai": "迈", "mee": "米", "moo": "穆", "mou": "莫", "mea": "米", "mau": "毛",
    "nai": "奈", "nee": "尼", "noo": "努", "nou": "诺", "nea": "尼",
    "pai": "派", "pee": "皮", "poo": "普", "pou": "波", "pea": "皮",
    "rai": "雷", "ree": "瑞", "roo": "鲁", "rou": "罗", "rea": "瑞", "rau": "劳",
    "sai": "赛", "see": "西", "soo": "苏", "sou": "索", "sea": "西", "sau": "索",
    "tai": "泰", "tee": "蒂", "too": "图", "tou": "托", "tea": "蒂", "tau": "陶",
    "vai": "维", "vee": "维", "voo": "武", "vea": "维",
    "wai": "怀", "wee": "威", "woo": "沃",
    "yai": "亚", "yee": "伊",
    "zai": "泽", "zee": "齐", "zoo": "祖",
}

CODA = {
    "ng": "恩", "nk": "恩克", "nt": "恩特", "nd": "恩德", "mp": "姆普",
    "mb": "姆", "ck": "克", "ght": "特", "dge": "吉", "tch": "奇",
    "ss": "斯", "ll": "尔", "tt": "特", "dd": "德", "ff": "弗",
    "pp": "普", "nn": "恩", "mm": "姆", "zz": "兹", "rr": "尔",
    "sh": "什", "ch": "奇", "th": "斯", "ph": "弗", "ce": "斯", "se": "斯",
    "ze": "兹", "ge": "吉", "que": "克",
}

SUFFIX = {
    "tion": "申", "sion": "惹恩", "tious": "舍斯", "cious": "舍斯",
    "ing": "英", "ings": "英斯", "ment": "门特", "ments": "门茨",
    "ness": "尼斯", "less": "莱斯", "ful": "福尔", "ously": "厄斯利",
    "ous": "厄斯", "ious": "伊厄斯", "able": "额波", "ible": "伊波",
    "ical": "伊扣", "ically": "伊扣利", "ity": "伊提", "ety": "伊提",
    "ive": "伊夫", "ate": "埃特", "age": "诶吉", "ance": "恩斯",
    "ence": "恩斯", "ant": "恩特", "ent": "恩特", "ism": "伊泽姆",
    "ist": "伊斯特", "ize": "爱兹", "ise": "爱兹",
    "ture": "彻", "sure": "烁", "ly": "利", "er": "尔", "or": "奥",
    "ar": "尔", "ir": "尔", "ur": "尔", "le": "尔", "el": "尔",
}

DIGRAPHS = ("ch", "sh", "th", "ph", "wh", "qu", "kn", "wr", "ck", "gh", "dg", "ps")

# Characters that carry no meaning on their own; neighbouring duplicates read badly.
EPENTHETIC_CHARS = set("".join(CONSONANT.values()) + "".join(CODA.values()))

CLUSTER = {
    "sch": "斯克", "scr": "斯克", "shr": "什", "thr": "斯罗",
    "spr": "斯普", "spl": "斯普", "squ": "斯克", "chr": "克", "phr": "弗",
}


def _units(onset: str):
    """Split an onset cluster into pronounceable units (digraphs stay whole)."""
    out = []
    while onset:
        if onset[:2] in DIGRAPHS:
            out.append(onset[:2])
            onset = onset[2:]
        else:
            out.append(onset[0])
            onset = onset[1:]
    return out


def _unit_epenthetic(unit: str) -> str:
    if unit in CLUSTER:
        return CLUSTER[unit]
    if len(unit) == 2:
        return CONSONANT.get(unit[0], "") + CONSONANT.get(unit[1], "")
    return CONSONANT.get(unit, "")


def _vowel_zh(vowel: str) -> str:
    """Map a vowel group to Chinese, degrading gracefully for odd spellings."""
    if not vowel:
        return ""
    if vowel in VOWEL_GROUP:
        return VOWEL_GROUP[vowel]
    for size in (2, 1):
        if vowel[:size] in VOWEL_GROUP:
            return VOWEL_GROUP[vowel[:size]] + _vowel_zh(vowel[size:])
    return VOWEL_GROUP.get(vowel[0], "")


def _syllable(onset: str, vowel: str) -> str:
    units = _units(onset)
    if not units:
        return _vowel_zh(vowel)
    prefix = "".join(_unit_epenthetic(u) for u in units[:-1])
    last = units[-1]
    for size in (3, 2):
        key = (last + vowel)[:size] if len(last + vowel) >= size else ""
        if key and key in CV and key.startswith(last):
            rest = (last + vowel)[size:]
            return prefix + CV[key] + _vowel_zh(rest)
    return prefix + CONSONANT.get(last, "") + _vowel_zh(vowel)


def _coda(coda: str) -> str:
    out = []
    while coda:
        for size in (3, 2):
            chunk = coda[:size]
            if chunk in CODA:
                out.append(CODA[chunk])
                coda = coda[size:]
                break
        else:
            ch = coda[0]
            if ch != "e":
                out.append(CONSONANT.get(ch, ""))
            coda = coda[1:]
    return "".join(out)


def _split_syllables(word: str):
    spans = []
    i = 0
    while i < len(word):
        if word[i] in VOWELS:
            j = i
            while j < len(word) and word[j] in VOWELS:
                j += 1
            spans.append((i, j))
            i = j
        else:
            i += 1
    if not spans:
        return []
    sylls = []
    prev_end = 0
    for idx, (s, e) in enumerate(spans):
        onset = word[prev_end:s]
        if idx + 1 < len(spans):
            nxt_start = spans[idx + 1][0]
            cons = word[e:nxt_start]
            if len(cons) <= 1:
                coda, next_onset = "", cons
            elif cons in ("str", "spr", "scr", "thr", "spl", "squ"):
                coda, next_onset = "", cons
            elif len(cons) == 2 and cons[0] in "rlmn":
                coda, next_onset = cons[0], cons[1]
            else:
                coda, next_onset = cons[0], cons[1:]
            sylls.append((onset, word[s:e], coda))
            prev_end = nxt_start - len(next_onset)
        else:
            sylls.append((onset, word[s:e], word[e:]))
    return sylls


ACCENTS = str.maketrans(
    "áàâäãåéèêëíìîïóòôöõúùûüñçýÿßæø",
    "aaaaaaeeeeiiiiooooouuuuncyysao",
)


def word_to_syllables(word: str) -> str:
    w = word.lower().translate(ACCENTS).replace("'", "").replace("-", "")
    if not w:
        return word
    for suf, zh in SUFFIX.items():
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return word_to_syllables(w[: -len(suf)]) + zh
    sylls = _split_syllables(w)
    if not sylls:
        return "".join(CONSONANT.get(c, c) for c in w)
    out = []
    for onset, vowel, coda in sylls:
        head = _syllable(onset, vowel)
        tail = _coda(coda)
        # avoid "克克/斯斯" when a coda and the next onset produce the same character
        if out and out[-1] and head and out[-1][-1] == head[0] and head[0] in EPENTHETIC_CHARS:
            head = head[1:]
        if out and out[-1] and tail and out[-1][-1] == tail[0] and tail[0] in EPENTHETIC_CHARS:
            tail = tail[1:]
        out.append(head + tail)
    joined = "".join(out)
    while "克克克" in joined:
        joined = joined.replace("克克克", "克克")
    return joined


class Transliterator:
    """Transliterate strings with a phrase/word memory plus G2P fallback."""

    def __init__(self, phrase_memory=None, word_memory=None, overrides=None):
        self.phrase_memory = phrase_memory or {}
        self.word_memory = word_memory or {}
        self.overrides = overrides or {}

    def word(self, word: str) -> str:
        key = word.lower().strip("'-")
        if not key:
            return word
        if key in self.overrides:
            return self.overrides[key]
        if key in self.word_memory:
            return self.word_memory[key]
        return word_to_syllables(key)

    def _text(self, chunk: str) -> str:
        out = []
        last = 0
        for m in WORD_RE.finditer(chunk):
            out.append(chunk[last:m.start()])
            out.append(self.word(m.group(0)))
            last = m.end()
        out.append(chunk[last:])
        return "".join(out)

    def __call__(self, text: str, phrase: bool = True) -> str:
        if not isinstance(text, str) or not HAS_LATIN.search(text):
            return text
        key = text.strip().lower()
        if phrase and key in self.phrase_memory:
            return self.phrase_memory[key]
        parts = []
        last = 0
        for m in TOKEN_RE.finditer(text):
            parts.append((True, text[last:m.start()]))
            parts.append((False, m.group(0)))
            last = m.end()
        parts.append((True, text[last:]))
        out = []
        for is_text, chunk in parts:
            out.append(self._text(chunk) if is_text else chunk)
        return "".join(out)
