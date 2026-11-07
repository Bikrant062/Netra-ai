import re

from detector import COCO_CLASSES

SURE_THRESHOLD = 0.6  # below this, answers are hedged ("something that looks like...")

# ---------- English wording ----------
PLACE_EN = {"left": "on the left", "center": "in front", "right": "on the right"}
SIDE_EN = {"left": "left side", "center": "middle", "right": "right side"}

DISPLAY_EN = {
    "cell phone": "phone", "dining table": "table", "potted plant": "plant",
    "tv": "TV", "hair drier": "hair dryer", "sports ball": "ball",
    "scissors": "pair of scissors", "skis": "pair of skis",
}
IRREGULAR_PLURALS = {
    "person": "people", "knife": "knives", "sheep": "sheep",
    "pair of scissors": "pairs of scissors", "pair of skis": "pairs of skis",
}

# ---------- Nepali wording ----------
PLACE_NE = {"left": "तपाईंको बायाँतिर", "center": "तपाईंको अगाडि", "right": "तपाईंको दायाँतिर"}
SIDE_NE = {"left": "बायाँतिर", "center": "बीचमा", "right": "दायाँतिर"}

OBJECT_NAMES_NE = {
    "person": "मान्छे", "chair": "कुर्सी", "couch": "सोफा", "bed": "ओछ्यान",
    "dining table": "टेबल", "bottle": "बोतल", "cup": "कप", "laptop": "ल्यापटप",
    "cell phone": "मोबाइल फोन", "tv": "टेलिभिजन", "book": "किताब", "clock": "घडी",
    "keyboard": "किबोर्ड", "mouse": "माउस", "backpack": "झोला", "umbrella": "छाता",
    "bowl": "कचौरा", "potted plant": "बिरुवा", "cat": "बिरालो", "dog": "कुकुर",
    "car": "कार", "motorcycle": "मोटरसाइकल", "bicycle": "साइकल", "bus": "बस",
    "remote": "रिमोट", "scissors": "कैंची", "vase": "फूलदानी",
    "refrigerator": "फ्रिज", "microwave": "माइक्रोवेभ", "sink": "सिंक",
    "toilet": "शौचालय", "bench": "बेन्च", "suitcase": "सुटकेस",
    "handbag": "ह्यान्डब्याग", "knife": "चक्कु", "spoon": "चम्चा",
    "fork": "काँटा", "wine glass": "गिलास",
}

# Words in a question that point to a direction (Nepali words are matched as substrings).
DIRECTION_WORDS = {
    "left": ["left", "बाया", "बाँया"],
    "right": ["right", "दाया", "दाँया", "दाहिने"],
    "center": ["front", "ahead", "straight", "center", "centre", "middle", "forward",
               "अगाडि", "अघि", "सामुन्ने", "सिधा", "बीच"],
}

# Other words people use for the same object.
EN_SYNONYMS = {
    "table": "dining table", "phone": "cell phone", "mobile": "cell phone",
    "smartphone": "cell phone", "sofa": "couch", "plant": "potted plant",
    "television": "tv", "people": "person", "man": "person", "woman": "person",
    "human": "person", "bike": "bicycle", "motorbike": "motorcycle",
    "fridge": "refrigerator",
}
NE_TERMS = {ne: en for en, ne in OBJECT_NAMES_NE.items() if " " not in ne}
NE_TERMS.update({
    "मोबाइल": "cell phone", "फोन": "cell phone", "मानिस": "person",
    "व्यक्ति": "person", "टेबुल": "dining table", "गमला": "potted plant",
})
# Endings that can follow a Nepali noun (कुर्सीमा, बोतललाई ...).
NE_SUFFIXES = {"", "हरू", "हरु", "मा", "लाई", "को", "ले", "बाट", "हरूमा",
               "हरूलाई", "हरूको", "छ", "छन्"}


# ---------- Understanding the question ----------
def _contains(text, term):
    if term.isascii():
        return re.search(r"\b" + re.escape(term) + r"\b", text) is not None
    return term in text


def _find_object(q):
    """Return the COCO class name the question asks about, or None."""
    best = None  # (position in question, class name)
    terms = {name: name for name in COCO_CLASSES}
    terms.update(EN_SYNONYMS)
    for term, cls in terms.items():
        m = re.search(r"\b" + re.escape(term) + r"(?:s|es)?\b", q)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), cls)
    if best:
        return best[1]

    for token in (t.strip("?।,.!\"'") for t in q.split()):
        for term, cls in NE_TERMS.items():
            if token.startswith(term) and token[len(term):] in NE_SUFFIXES:
                return cls
    return None


def parse_question(question):
    q = question.lower().strip()
    found = [d for d, words in DIRECTION_WORDS.items()
             if any(_contains(q, w) for w in words)]
    direction = found[0] if len(found) == 1 else None  # two directions -> overview
    return {"direction": direction, "object": _find_object(q)}


# ---------- English phrases ----------
def _cap(text):
    return text[0].upper() + text[1:]


def _display_en(name):
    return DISPLAY_EN.get(name, name)


def _plural_en(word):
    if word in IRREGULAR_PLURALS:
        return IRREGULAR_PLURALS[word]
    if word.endswith(("s", "x", "ch", "sh")):
        return word + "es"
    return word + "s"


def _article_en(word):
    return "an" if word[0].lower() in "aeiou" else "a"


def _phrase_en(name, sure, count):
    word = _display_en(name)
    if sure:
        return f"{_article_en(word)} {word}" if count == 1 else f"{count} {_plural_en(word)}"
    if count == 1:
        return f"something that looks like {_article_en(word)} {word}"
    return f"{count} things that look like {_plural_en(word)}"


def _join_en(items):
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


# ---------- Nepali phrases ----------
def _name_ne(name):
    return OBJECT_NAMES_NE.get(name, _display_en(name))


def _phrase_ne(name, sure, count):
    word = _name_ne(name)
    if sure:
        return f"एउटा {word}" if count == 1 else f"{count} वटा {word}"
    if count == 1:
        return f"{word} जस्तो देखिने केही"
    return f"{word} जस्ता {count} वटा वस्तु"


def _join_ne(items):
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " र " + items[-1]


# ---------- Building sentences ----------
def _group(dets):
    """Count objects by (name, sure?). Confident ones come first."""
    counts = {}
    for d in dets:
        key = (d["name"], d["confidence"] >= SURE_THRESHOLD)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: not kv[0][1]))


def _list_en(dets):
    counts = _group(dets)
    items = [_phrase_en(n, sure, c) for (n, sure), c in counts.items()]
    return _join_en(items), sum(counts.values())


def _list_ne(dets):
    counts = _group(dets)
    items = [_phrase_ne(n, sure, c) for (n, sure), c in counts.items()]
    return _join_ne(items), sum(counts.values())


def _sentence(lang, place, dets):
    """'On the left, there is a chair.'"""
    if lang == "ne":
        text, total = _list_ne(dets)
        return f"{PLACE_NE[place]} {text} {'छ' if total == 1 else 'छन्'}।"
    text, total = _list_en(dets)
    return f"{_cap(PLACE_EN[place])}, there {'is' if total == 1 else 'are'} {text}."


def _extends(lang, direction, dets):
    """'A laptop also extends into the left side of the view.'"""
    if lang == "ne":
        text, total = _list_ne(dets)
        verb = "फैलिएको छ" if total == 1 else "फैलिएका छन्"
        return f"{text} {SIDE_NE[direction]} पनि {verb}।"
    text, total = _list_en(dets)
    verb = "extends" if total == 1 else "extend"
    return f"{_cap(text)} also {verb} into the {SIDE_EN[direction]} of the view."


# ---------- The three kinds of answer ----------
def _answer_overview(lang, detections):
    if not detections:
        if lang == "ne":
            return "क्यामेराको दृश्यमा मैले कुनै वस्तु चिन्न सकिनँ। यसको अर्थ त्यहाँ केही छैन भन्ने होइन।"
        return "I could not recognize any objects in the camera view. That does not mean nothing is there."
    parts = []
    for place in ("left", "center", "right"):
        here = [d for d in detections if d["position"] == place]
        if here:
            parts.append(_sentence(lang, place, here))
    return " ".join(parts)


def _answer_direction(lang, direction, detections):
    main = [d for d in detections if d["position"] == direction]
    extra = [d for d in detections
             if d["position"] != direction and direction in d["regions"]]
    if not main and not extra:
        if lang == "ne":
            return f"{PLACE_NE[direction]} मैले कुनै वस्तु चिन्न सकिनँ। यसको अर्थ केही छैन भन्ने होइन।"
        return f"I could not recognize any objects {PLACE_EN[direction]}. That does not mean nothing is there."
    parts = []
    if main:
        parts.append(_sentence(lang, direction, main))
    if extra:
        parts.append(_extends(lang, direction, extra))
    return " ".join(parts)


def _answer_object(lang, name, direction, detections):
    same = [d for d in detections if d["name"] == name]
    main = [d for d in same if direction is None or d["position"] == direction]
    where_en = f" {PLACE_EN[direction]}" if direction else ""
    where_ne = PLACE_NE[direction] if direction else ""

    if main:
        sure = any(d["confidence"] >= SURE_THRESHOLD for d in main)
        if lang == "ne":
            text, _ = _list_ne(main)
            msg = (f"हो, {where_ne} {text} देखिन्छ।" if sure
                   else f"पक्का छैन, तर {where_ne} {text} हुन सक्छ।")
            return " ".join(msg.split())
        text, _ = _list_en(main)
        if sure:
            return f"Yes, I can see {text}{where_en}."
        return f"I'm not sure, but I may see {text}{where_en}."

    extra = [d for d in same if direction and direction in d["regions"]]
    if extra:
        return _extends(lang, direction, extra)

    if lang == "ne":
        msg = f"{where_ne} मैले {_name_ne(name)} देखिनँ, तर मैले केही छुटाएको हुन सक्छ।"
        return " ".join(msg.split())
    word = _display_en(name)
    return f"I can't see {_article_en(word)} {word}{where_en}, but I may miss things."


def answer_question(question, language, detections):
    """detections: the list from detector.py after spatial.add_positions()."""
    lang = "ne" if language == "ne" else "en"
    parsed = parse_question(question)
    direction, wanted = parsed["direction"], parsed["object"]
    if wanted:
        return _answer_object(lang, wanted, direction, detections)
    if direction:
        return _answer_direction(lang, direction, detections)
    return _answer_overview(lang, detections)