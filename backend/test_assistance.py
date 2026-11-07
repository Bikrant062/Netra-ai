from assistant import answer_question, parse_question

# Detections from your own photo (what detector.py + spatial.py produce).
detections = [
    {"name": "laptop", "confidence": 0.92, "box": [152, 87, 1223, 1156],
     "position": "center", "regions": ["left", "center"]},
    {"name": "clock", "confidence": 0.52, "box": [7, 859, 289, 1125],
     "position": "left", "regions": ["left"]},
    {"name": "bottle", "confidence": 0.50, "box": [1136, 24, 1590, 1128],
     "position": "right", "regions": ["right"]},
]

# 1) Does the code understand the questions? (exact checks)
parse_cases = [
    ("What is on my left?", "left", None),
    ("What is on my right?", "right", None),
    ("What is in front of me?", "center", None),
    ("Is there a chair in front of me?", "center", "chair"),
    ("Is there a person on my left?", "left", "person"),
    ("What objects are around me?", None, None),
    ("मेरो बायाँतिर के छ?", "left", None),
    ("मेरो दायाँतिर के छ?", "right", None),
    ("मेरो अगाडि के छ?", "center", None),
    ("मेरो अगाडि कुर्सी छ?", "center", "chair"),
    ("मेरो अगाडि के बसेको छ?", "center", None),  # 'बसेको' (sitting) must NOT mean bus
]
all_ok = True
for question, want_dir, want_obj in parse_cases:
    got = parse_question(question)
    ok = got["direction"] == want_dir and got["object"] == want_obj
    all_ok = all_ok and ok
    print(f"{'PASS' if ok else 'FAIL'}  {question!r} -> {got}")
print("\nParsing: all passed.\n" if all_ok else "\nParsing: some FAILED.\n")

# 2) What does it say? (read these and judge the wording)
questions = [
    "What is in front of me?",
    "What is on my left?",
    "What is on my right?",
    "What objects are around me?",
    "Is there a laptop in front of me?",
    "Is there a chair in front of me?",
    "Is there a bottle on my left?",
    "मेरो बायाँतिर के छ?",
    "मेरो अगाडि के छ?",
    "मेरो अगाडि ल्यापटप छ?",
    "मेरो अगाडि कुर्सी छ?",
]
for lang in ("en", "ne"):
    print(f"===== language = {lang} =====")
    for q in questions:
        print(f"Q: {q}\nA: {answer_question(q, lang, detections)}\n")

print("===== nothing detected =====")
print(answer_question("What is in front of me?", "en", []))
print(answer_question("मेरो अगाडि के छ?", "ne", []))