import os
import csv
import re

_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_THIS_DIR)
_PROJECT_DIR = os.path.dirname(_BACKEND_DIR)

_CSV_SEARCH_PATHS = [
    os.path.join(_PROJECT_DIR,  'data', 'raw_data', 'crop_diseases.csv'),
    os.path.join(_BACKEND_DIR,  'data', 'raw_data', 'crop_diseases.csv'),
    os.path.join(_PROJECT_DIR,  'data', 'crop_diseases.csv'),
    os.path.join(_BACKEND_DIR,  'data', 'crop_diseases.csv'),
]

_STOPWORDS = {
    'the','a','an','is','are','on','in','of','with','and','or','my','i',
    'have','has','its','it','this','that','what','how','to','do','can',
    'please','help','tell','me','about','plant','crop','leaf','leaves',
    'showing','shows','there','affected','problem','issue','seems','look',
    'looks','like','some','getting','see','seen','notice','noticed','found',
}

_VISUAL_WORDS = {
    'yellow','brown','black','white','orange','gray','grey','purple','silver',
    'dark','pale','lesion','spot','spots','ring','rings','curl','curling',
    'wilt','wilting','blight','rust','mold','mould','powder','powdery',
    'blotch','necrosis','necrotic','scorch','burn','stippling','bronze',
    'mosaic','mottle','distortion','stunted','gall','ooze','pustule',
    'canker','shot','hole','holes','stripe','streaks','water','soaked',
    'angular','concentric','target','tattered','skeleton','webbing',
}

_CAUSE_SYNONYMS = {
    'fungus':             ['fungal','mold','mould','rust','blight','mildew','rot','spore','powdery'],
    'bacteria':           ['bacterial','bacterium','ooze','canker','streak','slime'],
    'virus':              ['viral','mosaic','curl','mottle','ringspot','yellowing','stunt'],
    'pest':               ['insect','mite','aphid','thrip','whitefly','beetle','worm',
                           'bug','fly','larva','larvae','caterpillar','spider','scale'],
    'nutrient deficiency':['deficiency','chlorosis','yellowing','pale','purple','stunted',
                           'interveinal','necrosis','scorch','nitrogen','phosphorus',
                           'potassium','iron','zinc','magnesium','calcium'],
    'abiotic':            ['drought','salt','heat','frost','wind','burn','stress','injury'],
}


def _find_csv():
    for path in _CSV_SEARCH_PATHS:
        if os.path.exists(path):
            return path
    return None


def _tokenise(text: str) -> set:
    tokens = re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 2}


class DiseaseMatcher:
    def __init__(self, csv_path: str = None):
        self.csv_path = csv_path or _find_csv()
        self.records  = []
        self._loaded  = False
        self._load()

    def _load(self):
        if not self.csv_path or not os.path.exists(self.csv_path):
            return

        with open(self.csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['_crop_tokens']    = _tokenise(row.get('crop', ''))
                row['_symptom_tokens'] = _tokenise(row.get('symptom_description', ''))
                row['_disease_tokens'] = _tokenise(row.get('possible_disease', ''))
                row['_cause_lower']    = row.get('cause', '').lower().strip()
                self.records.append(row)

        self._loaded = True

    def _score(self, query_tokens: set, query_lower: str, record: dict) -> float:
        score = 0.0

        crop_lower = record.get('crop', '').lower()
        if crop_lower and crop_lower in query_lower:
            score += 30
        else:
            shared_crop = query_tokens & record['_crop_tokens']
            score += len(shared_crop) * 12

        shared_sym = query_tokens & record['_symptom_tokens']
        score += min(len(shared_sym) * 5, 40)

        bonus_sym = query_tokens & _VISUAL_WORDS & record['_symptom_tokens']
        score += min(len(bonus_sym) * 3, 15)

        cause = record['_cause_lower']
        for canonical, synonyms in _CAUSE_SYNONYMS.items():
            if canonical in cause:
                if canonical.split()[0] in query_lower:
                    score += 10
                    break
                for syn in synonyms:
                    if syn in query_lower:
                        score += 7
                        break

        shared_dis = query_tokens & record['_disease_tokens']
        score += min(len(shared_dis) * 10, 20)

        return score

    def match(self, query: str):
        results = self.match_top_n(query, n=1)
        return results[0] if results else None

    def match_top_n(self, query: str, n: int = 3) -> list:
        if not self._loaded or not self.records:
            return []

        query_lower  = query.lower()
        query_tokens = _tokenise(query)

        if not query_tokens:
            return []

        scored = []
        for record in self.records:
            s = self._score(query_tokens, query_lower, record)
            if s > 0:
                scored.append((s, record))

        scored.sort(key=lambda x: x[0], reverse=True)

        MIN_SCORE = 10
        return [
            {**rec, '_score': sc}
            for sc, rec in scored[:n]
            if sc >= MIN_SCORE
        ]

    def format_response(self, record: dict, confidence_pct: float = None) -> str:
        crop    = record.get('crop', 'Unknown crop').title()
        disease = record.get('possible_disease', 'Unknown disease')
        cause   = record.get('cause', 'Unknown')
        detail  = record.get('detailed_explanation', '')
        treat   = record.get('treatment_solution', 'Consult your local agricultural officer.')

        cause_emoji = {
            'fungus':             '🍄',
            'bacteria':           '🦠',
            'virus':              '🧬',
            'pest':               '🐛',
            'nutrient deficiency':'🌿',
            'abiotic':            '☀️',
        }.get(cause.lower(), '🔬')

        conf_line = f"\n📊 **Match confidence:** {min(confidence_pct, 100):.0f}%" \
                    if confidence_pct is not None else ""

        return (
            f"🔍 **Disease Identified: {disease}**{conf_line}\n\n"
            f"🌾 **Crop:** {crop}\n"
            f"{cause_emoji} **Cause:** {cause}\n\n"
            f"📋 **Details:**\n{detail}\n\n"
            f"💊 **Treatment:**\n{treat}"
        )

    def format_multi_response(self, records: list) -> str:
        if not records:
            return (
                "I couldn't identify a specific disease from your description.\n\n"
                "Please try:\n"
                "• Mentioning the **crop name** (e.g. tomato, wheat, potato)\n"
                "• Describing **symptoms** more specifically "
                "(e.g. 'yellow spots on leaves', 'brown lesions with rings')\n"
                "• Uploading a **photo** or **video** of the affected plant"
            )

        if len(records) == 1:
            return self.format_response(records[0],
                                        confidence_pct=min(records[0].get('_score', 0), 100))

        lines = ["🔍 **Possible diseases matching your description:**\n"]
        for i, rec in enumerate(records, 1):
            disease = rec.get('possible_disease', 'Unknown')
            crop    = rec.get('crop', '').title()
            cause   = rec.get('cause', '')
            treat   = rec.get('treatment_solution', '')
            conf    = min(rec.get('_score', 0), 100)
            short_treat = treat.split(';')[0].strip() if treat else ''
            lines.append(
                f"**{i}. {disease}** ({crop}) — {cause} | {conf:.0f}% match\n"
                f"   💊 {short_treat}\n"
            )

        lines.append(
            "\n*For a definitive diagnosis, upload a photo or video of your plant.*"
        )
        return "\n".join(lines)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_crops(self) -> list:
        return sorted({r.get('crop', '') for r in self.records if r.get('crop')})