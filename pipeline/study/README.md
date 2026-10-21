# Study paths

Each file here is one study path for the Study section (web/study.js). `python pipeline/study_build.py` checks them
and writes `web/data/study.json`, adding the atlas regions each path's drills draw from (`SCOPE` in the script).

```json
{ "id": "bourgogne", "title": "Burgundy", "level": "WSET 3 to Diploma", "summary": "…",
  "lessons": [ { "id": "bourgogne-overview", "title": "…", "minutes": 6, "intro": "…",
    "sections": [ { "h": "…", "p": ["…"], "places": ["fr-inao-a162"] } ],
    "key": ["…"],
    "questions": [ { "id": "q1", "q": "…", "options": ["…", "…", "…", "…"], "answer": 2, "explain": "…", "place": "fr-inao-a162" } ],
    "cards": [ { "f": "Front: a question or a term", "b": "Back: the answer, 220 characters at most", "place": "fr-inao-a162" } ] } ] }
```

Flashcards (`cards`, about 20 per lesson) make a deck per lesson and per path; `place` is optional and adds a link
that flies to it on the map. A card is known in the review by its lesson and its front text, so editing a front
starts that card afresh. A path with no `SCOPE` in `study_build.py` (foundations, vine-wine, sparkling-sweet-fortified)
is theory only: lessons, quizzes, cards and the mock exam, no map drills.

Rules: place ids from the atlas only; four distinct options with one right answer that the lesson teaches; stable,
checkable facts (geography, grapes, classifications, legal rules); plain short sentences and no long dashes.
Every path was drafted and then fact-checked separately against official specifications and standard references
in October 2026. Rules change: when an appellation's specification changes, update the lesson and its questions.
Lesson texts are CC BY 4.0, Open Wine Atlas contributors.

The first lesson of each path is free (its reading, quiz and cards); the others, more than 10 answers a day and the
full mock exam (30 questions) are for members. Everyone can take a sample exam of 10 questions per path (web/study.js).
