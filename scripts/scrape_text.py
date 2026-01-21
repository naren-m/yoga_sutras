#!/usr/bin/env python3
"""
Scrapes Yoga Sutras from multiple reliable sources:
1. Sanskrit text from sanskritdocuments.org (ITX format)
2. English translations from swamij.com

Output: data/yoga_sutras.json with all 196 sutras organized by Pada.
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

# Output configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'yoga_sutras.json')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# Pada structure: name, slug, sutra count
PADAS = [
    {"name": "Samadhi Pada", "slug": "samadhi-pada", "order": 1, "count": 51},
    {"name": "Sadhana Pada", "slug": "sadhana-pada", "order": 2, "count": 55},
    {"name": "Vibhuti Pada", "slug": "vibhuti-pada", "order": 3, "count": 56},
    {"name": "Kaivalya Pada", "slug": "kaivalya-pada", "order": 4, "count": 34},
]


def itx_to_iast(text: str) -> str:
    """
    Convert ITX (ITRANS variant used by sanskritdocuments.org) to IAST transliteration.
    Uses indic-transliteration library for proper conversion.
    """
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate

        # Remove LaTeX-style accent markers from the ITX file
        text = re.sub(r"\\['`]", "", text)
        text = re.sub(r"\\section\{[^}]*\}", "", text)  # Remove LaTeX section markers

        # The sanskritdocuments.org uses ITRANS format
        # Convert ITRANS to IAST
        return transliterate(text, sanscript.ITRANS, sanscript.IAST)
    except ImportError:
        print("Warning: indic-transliteration not installed")
        # Basic fallback cleanup
        text = re.sub(r"\\['`]", "", text)
        return text.lower()


def iast_to_devanagari(text: str) -> str:
    """Convert IAST to Devanagari using indic-transliteration."""
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        return transliterate(text, sanscript.IAST, sanscript.DEVANAGARI)
    except ImportError:
        # Fallback: return IAST if library not available
        print("Warning: indic-transliteration not installed, using IAST")
        return text


def fetch_sanskrit_sutras() -> dict:
    """Fetch Sanskrit sutras from sanskritdocuments.org ITX file."""
    url = "https://sanskritdocuments.org/doc_yoga/yogasuutra.itx"
    print(f"Fetching Sanskrit from {url}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        content = response.text
    except Exception as e:
        print(f"Error fetching Sanskrit: {e}")
        return {}

    sutras = {}
    # Pattern: text || X.Y|| where X is pada number, Y is sutra number
    pattern = r"([^\|]+)\|\|\s*(\d+)\\\.(\d+)\s*\|\|"

    for match in re.finditer(pattern, content):
        sanskrit_itx = match.group(1).strip()
        pada = int(match.group(2))
        sutra_num = int(match.group(3))

        # Clean up the ITX text
        sanskrit_itx = re.sub(r'\s+', ' ', sanskrit_itx)
        sanskrit_itx = sanskrit_itx.strip()
        # Remove LaTeX artifacts like closing braces from section definitions
        sanskrit_itx = re.sub(r'^[}\s]+', '', sanskrit_itx)
        sanskrit_itx = re.sub(r'[}\s]+$', '', sanskrit_itx)

        # Convert to IAST
        iast = itx_to_iast(sanskrit_itx)

        key = f"{pada}.{sutra_num}"
        sutras[key] = {
            "iast": iast,
            "devanagari": iast_to_devanagari(iast)
        }

    print(f"Fetched {len(sutras)} Sanskrit sutras")
    return sutras


def fetch_english_translations() -> dict:
    """Fetch English translations from swamij.com."""
    url = "https://swamij.com/yoga-sutras-list.htm"
    print(f"Fetching translations from {url}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching translations: {e}")
        return {}

    translations = {}

    # Find all text content
    text = soup.get_text()

    # Pattern to match sutra numbers and their translations
    # Format: "1.1 Text here" or "(1.1) Text here"
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        # Match patterns like "1.1 Translation text" or "1.1: Translation text"
        match = re.match(r'^(\d+)\.(\d+)[:\s]+(.+)$', line)
        if match:
            pada = int(match.group(1))
            sutra_num = int(match.group(2))
            translation = match.group(3).strip()

            if translation and len(translation) > 10:  # Skip very short lines
                key = f"{pada}.{sutra_num}"
                translations[key] = translation

    print(f"Fetched {len(translations)} translations")
    return translations


def get_fallback_translations() -> dict:
    """
    Provide key translations as fallback.
    These are well-known, public domain translations.
    """
    return {
        "1.1": "Now begins instruction in yoga.",
        "1.2": "Yoga is the cessation of the modifications of the mind.",
        "1.3": "Then the seer abides in its own nature.",
        "1.4": "Otherwise, there is identification with the modifications of the mind.",
        "1.5": "The modifications of the mind are five, and are painful or not painful.",
        "1.6": "They are: right knowledge, wrong knowledge, imagination, sleep, and memory.",
        "1.7": "Right knowledge comes from perception, inference, and testimony.",
        "1.8": "Wrong knowledge is false understanding not based on the true form of an object.",
        "1.9": "Imagination is based on knowledge of words without any real object.",
        "1.10": "Sleep is a modification based on the absence of content.",
        "1.11": "Memory is the retention of experienced objects.",
        "1.12": "Control over them is achieved through practice and non-attachment.",
        "1.13": "Practice is the effort to remain steady in that state.",
        "1.14": "Practice becomes firmly established when done for a long time, without interruption, and with devotion.",
        "1.15": "Non-attachment is the consciousness of mastery in one who does not thirst for objects seen or heard.",
        "1.16": "The higher non-attachment is freedom from craving for the gunas, arising from knowledge of the Self.",
        "1.17": "Samprajnata samadhi is accompanied by reasoning, reflection, bliss, and I-am-ness.",
        "1.18": "The other samadhi is preceded by practice of cessation and is supported by residual impressions.",
        "1.19": "For the videhas and prakrtilayas, it comes from birth.",
        "1.20": "For others, it is preceded by faith, energy, memory, concentration, and wisdom.",
        "1.21": "Success is near for those with intense practice.",
        "1.22": "There is further distinction according to mild, medium, or intense means.",
        "1.23": "Or by devotion to Ishvara.",
        "1.24": "Ishvara is a special Self untouched by afflictions, actions, results, and latent impressions.",
        "1.25": "In Ishvara is the unsurpassed seed of omniscience.",
        "1.26": "Ishvara is the teacher of even the ancient teachers, being unlimited by time.",
        "1.27": "The word designating Ishvara is pranava (Om).",
        "1.28": "Its repetition is for understanding its meaning.",
        "1.29": "From that comes inner awareness and the removal of obstacles.",
        "1.30": "Disease, dullness, doubt, carelessness, laziness, sensuality, false perception, failure to reach firm ground, and instability are the distractions of the mind, which are obstacles.",
        "1.31": "Pain, despair, trembling, and irregular breathing accompany these distractions.",
        "1.32": "To prevent them, practice on a single principle.",
        "1.33": "By cultivating friendliness toward the happy, compassion toward the suffering, joy toward the virtuous, and indifference toward the non-virtuous, the mind becomes purified.",
        "1.34": "Or by exhalation and retention of breath.",
        "1.35": "Or activity of the higher senses steadies the mind.",
        "1.36": "Or the luminous state free from sorrow.",
        "1.37": "Or the mind taking as its object those who are free from attachment.",
        "1.38": "Or knowledge arising from dream or sleep.",
        "1.39": "Or by meditation on anything of one's inclination.",
        "1.40": "The mastery extends from the smallest to the greatest.",
        "1.41": "When modifications have become weakened, the mind becomes like a transparent crystal, taking the form of whatever object is nearby.",
        "1.42": "Savitarka samapatti is the state mixed with awareness of word, meaning, and knowledge.",
        "1.43": "Nirvitarka is when memory is purified, and the mind shines forth as the object alone.",
        "1.44": "Similarly, savichara and nirvichara samapatti are explained regarding subtle objects.",
        "1.45": "The province of subtle objects extends up to the unmanifest.",
        "1.46": "These are samadhi with seed.",
        "1.47": "On attaining the purity of nirvichara samadhi, there is inner clarity.",
        "1.48": "There, wisdom is truth-bearing.",
        "1.49": "Its scope is different from that of inference and testimony due to its specific purpose.",
        "1.50": "The impression born from it prevents other impressions.",
        "1.51": "With the cessation of even that, all impressions are controlled, and seedless samadhi is attained.",
        # Sadhana Pada (Chapter 2)
        "2.1": "Austerity, self-study, and surrender to Ishvara constitute Kriya Yoga.",
        "2.2": "Its purposes are to cultivate samadhi and to weaken the afflictions.",
        "2.3": "The afflictions are ignorance, egoism, attachment, aversion, and clinging to life.",
        "2.4": "Ignorance is the field for the others, whether dormant, attenuated, interrupted, or active.",
        "2.5": "Ignorance is seeing the impermanent as permanent, the impure as pure, the painful as pleasant, and the non-self as self.",
        "2.6": "Egoism is the identification of the seer with the instrument of seeing.",
        "2.7": "Attachment follows pleasure.",
        "2.8": "Aversion follows pain.",
        "2.9": "Clinging to life flows by its own nature, established even in the wise.",
        "2.10": "These subtle afflictions can be destroyed by tracing them back to their origin.",
        "2.11": "Their modifications can be destroyed by meditation.",
        "2.12": "The store of karma has its root in the afflictions and is experienced in seen and unseen births.",
        "2.13": "As long as the root exists, there is fruition of birth, lifespan, and experience.",
        "2.14": "These have pleasure or pain as their fruits, according to virtue or vice as their cause.",
        "2.15": "To the discerning, all is suffering due to the pain of change, anxiety, and latent impressions.",
        "2.16": "The suffering yet to come can be avoided.",
        "2.17": "The cause of that which is to be avoided is the union of the seer and the seen.",
        "2.18": "The seen consists of the elements and the senses, has the nature of illumination, activity, and inertia, and serves the purpose of experience and liberation.",
        "2.19": "The stages of the gunas are the specific, the non-specific, the differentiated, and the undifferentiated.",
        "2.20": "The seer is pure consciousness only; though pure, it sees through the coloring of the intellect.",
        "2.21": "The nature of the seen exists only for the sake of the seer.",
        "2.22": "Although destroyed for one who has attained liberation, it is not destroyed for others, being common to them.",
        "2.23": "The conjunction of the owner with the owned is the cause of apprehending the nature and powers of both.",
        "2.24": "The cause of this conjunction is ignorance.",
        "2.25": "Without it, there is no conjunction, and the seer attains liberation.",
        "2.26": "Uninterrupted discriminative awareness is the means of liberation.",
        "2.27": "For one with discriminative awareness, there is seven-fold wisdom in the final stage.",
        "2.28": "Through practice of the limbs of yoga, impurities diminish and wisdom shines forth.",
        "2.29": "The eight limbs are: restraint, observance, posture, breath control, sense withdrawal, concentration, meditation, and absorption.",
        "2.30": "The restraints are: non-violence, truthfulness, non-stealing, continence, and non-greed.",
        "2.31": "These are the great vow, universal regardless of class, place, time, or circumstance.",
        "2.32": "The observances are: purity, contentment, austerity, self-study, and surrender to Ishvara.",
        "2.33": "When disturbed by negative thoughts, cultivate the opposite.",
        "2.34": "Negative thoughts are violence, etc., whether done, caused, or approved, whether arising from greed, anger, or delusion, whether mild, medium, or intense. Their fruit is endless suffering and ignorance. Therefore, cultivate the opposite.",
        "2.35": "When non-violence is established, hostility ceases in one's presence.",
        "2.36": "When truthfulness is established, actions and their fruits depend on it.",
        "2.37": "When non-stealing is established, all jewels approach.",
        "2.38": "When continence is established, vigor is gained.",
        "2.39": "When non-greed is established, there comes knowledge of the how and why of birth.",
        "2.40": "Through purity, one becomes disgusted with one's body and avoids contact with others.",
        "2.41": "Also purity of sattva, cheerfulness, one-pointedness, mastery over the senses, and fitness for Self-realization.",
        "2.42": "From contentment comes supreme happiness.",
        "2.43": "Through austerity, impurities are destroyed and perfection of body and senses is attained.",
        "2.44": "Through self-study comes communion with one's chosen deity.",
        "2.45": "Through surrender to Ishvara comes perfection in samadhi.",
        "2.46": "Posture should be steady and comfortable.",
        "2.47": "By relaxation of effort and absorption in the infinite.",
        "2.48": "Then one is not affected by the pairs of opposites.",
        "2.49": "When this is accomplished, pranayama, the regulation of inhalation and exhalation, follows.",
        "2.50": "Its modifications are external, internal, or suspended; regulated by place, time, and number; becoming long and subtle.",
        "2.51": "The fourth pranayama transcends external and internal objects.",
        "2.52": "Thus the covering of light is diminished.",
        "2.53": "And the mind becomes fit for concentration.",
        "2.54": "When the senses withdraw from their objects and imitate the nature of the mind, this is pratyahara.",
        "2.55": "Then follows supreme mastery over the senses.",
        # Vibhuti Pada (Chapter 3) - first few
        "3.1": "Concentration is the binding of the mind to one place.",
        "3.2": "Meditation is the continuous flow of awareness there.",
        "3.3": "Samadhi is when only the object shines forth, as if empty of its own form.",
        "3.4": "The three together constitute samyama.",
        "3.5": "By mastery of samyama comes the light of wisdom.",
        "3.6": "Its application is to successive stages.",
        "3.7": "These three are more internal than the preceding ones.",
        "3.8": "But even these are external to seedless samadhi.",
        "3.9": "The transformation of control is the emergence of control impressions and the subsidence of emergence impressions.",
        "3.10": "Its peaceful flow comes from impression.",
        # Continue with remaining sutras...
        "3.11": "The transformation of samadhi is the decline of scattered attention and the rise of one-pointedness.",
        "3.12": "The transformation of one-pointedness is when subsiding and arising impressions are equal.",
        "3.13": "By this, the transformations of property, character, and condition in elements and senses are explained.",
        "3.14": "The substratum is that which runs through the past, present, and future properties.",
        "3.15": "Difference in sequence is the cause of different transformations.",
        "3.16": "By samyama on the three transformations comes knowledge of past and future.",
        "3.17": "Word, meaning, and idea are normally confused; by samyama on their distinction comes knowledge of all sounds.",
        "3.18": "By bringing latent impressions to consciousness comes knowledge of previous births.",
        "3.19": "From samyama on another's mind comes knowledge of their thoughts.",
        "3.20": "But not of the underlying basis, as that is not the object of samyama.",
        "3.21": "By samyama on the form of the body, when its visibility is suspended, there is invisibility.",
        "3.22": "Similarly, disappearance of sound and other senses.",
        "3.23": "Karma is fast or slow; by samyama on it, or on omens, comes knowledge of death.",
        "3.24": "By samyama on friendliness, etc., those powers arise.",
        "3.25": "By samyama on strength, the strength of an elephant, etc.",
        "3.26": "By directing the light of superphysical perception, knowledge of the subtle, hidden, and distant arises.",
        "3.27": "By samyama on the sun, knowledge of the worlds.",
        "3.28": "On the moon, knowledge of the arrangement of stars.",
        "3.29": "On the pole star, knowledge of their movements.",
        "3.30": "On the navel center, knowledge of the body's arrangement.",
        "3.31": "On the throat pit, cessation of hunger and thirst.",
        "3.32": "On the kurma nadi, steadiness.",
        "3.33": "On the light at the crown of the head, vision of the perfected ones.",
        "3.34": "Or from intuitive illumination, all knowledge.",
        "3.35": "On the heart, understanding of the mind.",
        "3.36": "Experience arises from non-distinction between purusha and sattva, which are absolutely different. By samyama on self-interest vs. interest in the Self, comes knowledge of purusha.",
        "3.37": "From that arise intuitive hearing, touching, seeing, tasting, and smelling.",
        "3.38": "These are obstacles to samadhi but accomplishments in the worldly state.",
        "3.39": "By loosening the cause of bondage and knowing the passages, the mind enters another's body.",
        "3.40": "By mastery over udana, there is non-contact with water, mud, thorns, etc., and rising above.",
        "3.41": "By mastery over samana, blazing radiance.",
        "3.42": "By samyama on the relation between ear and space, divine hearing.",
        "3.43": "By samyama on the relation between body and space, and by absorption in lightness, passage through space.",
        "3.44": "The external, unfancied modification is the great disembodied; from that, the covering of light disappears.",
        "3.45": "By samyama on the gross, essential nature, subtle, interconnection, and purpose of elements, mastery over them.",
        "3.46": "From that comes minuteness, etc., perfection of body, and non-obstruction of its functions.",
        "3.47": "Perfection of body is beauty, grace, strength, and adamantine hardness.",
        "3.48": "By samyama on grasping, essential nature, I-am-ness, interconnection, and purpose, mastery over the senses.",
        "3.49": "From that, swiftness of mind, perception without instruments, and mastery over prakriti.",
        "3.50": "Only from discernment of the difference between sattva and purusha comes sovereignty over all states and omniscience.",
        "3.51": "By non-attachment even to that, the seed of bondage is destroyed, and kaivalya results.",
        "3.52": "There should be no pride or attachment upon invitation by celestials, for undesirable consequences may recur.",
        "3.53": "By samyama on moment and its succession comes wisdom born of discrimination.",
        "3.54": "From that comes discernment of two similar things not distinguishable by class, character, or position.",
        "3.55": "Discriminative wisdom is liberating, encompasses all objects and all times, and is non-sequential.",
        "3.56": "When sattva and purusha are equally pure, there is kaivalya.",
        # Kaivalya Pada (Chapter 4)
        "4.1": "Accomplishments come from birth, herbs, mantras, austerities, or samadhi.",
        "4.2": "Transformation into another state comes from the overflow of natural tendencies.",
        "4.3": "The incidental cause does not move the natural tendencies; it merely removes obstacles, like a farmer.",
        "4.4": "Created minds arise from ego alone.",
        "4.5": "One mind directs the many in their various activities.",
        "4.6": "Of these, the one born of meditation is free from impressions.",
        "4.7": "The karma of a yogi is neither white nor black; of others, it is threefold.",
        "4.8": "From that, only those tendencies manifest for which conditions are favorable.",
        "4.9": "Memory and impressions are of the same form, so there is continuity even when separated by birth, place, and time.",
        "4.10": "They are without beginning, due to the perpetuity of desire.",
        "4.11": "Being held together by cause, result, support, and object, they cease when those cease.",
        "4.12": "Past and future exist in reality, in different forms according to the paths of properties.",
        "4.13": "They are manifest or subtle according to the nature of the gunas.",
        "4.14": "The uniqueness of transformation is due to the unity of change.",
        "4.15": "Due to the difference in minds, the same object is perceived differently.",
        "4.16": "An object is not dependent on one mind; what would happen to it when not cognized by that mind?",
        "4.17": "An object is known or unknown depending on whether the mind is colored by it.",
        "4.18": "The modifications of the mind are always known by its lord, the changeless purusha.",
        "4.19": "The mind is not self-luminous, being an object of perception.",
        "4.20": "And there cannot be cognition of both at the same time.",
        "4.21": "If cognition by another mind were postulated, there would be infinite regress and confusion of memories.",
        "4.22": "When consciousness assumes the form of that which does not move, self-knowledge becomes possible.",
        "4.23": "The mind, colored by both seer and seen, comprehends everything.",
        "4.24": "Though variegated by countless impressions, the mind exists for another, because it acts in association.",
        "4.25": "For one who sees the distinction, reflection on the nature of the self ceases.",
        "4.26": "Then the mind inclines toward discrimination and gravitates toward liberation.",
        "4.27": "In the intervals of that, other thoughts arise from impressions.",
        "4.28": "Their removal is like that of the afflictions, as described.",
        "4.29": "For one who has no interest even in the highest knowledge, constant discriminative discernment brings the samadhi called dharma-megha.",
        "4.30": "From that, afflictions and karma cease.",
        "4.31": "Then, with all coverings and impurities removed, what remains to be known is little, due to the infinity of knowledge.",
        "4.32": "From that, the gunas have fulfilled their purpose, and their sequence of transformation comes to an end.",
        "4.33": "Sequence corresponds to moments, apprehensible at the end of transformation.",
        "4.34": "Kaivalya is the involution of the gunas, no longer serving the purpose of purusha, or the establishment of the power of consciousness in its own nature.",
    }


def build_yoga_sutras_data(sanskrit: dict, translations: dict) -> dict:
    """Build the final structured data combining Sanskrit and translations."""
    fallback = get_fallback_translations()

    data = {
        "slug": "yoga-sutras",
        "title": "Yoga Sutras of Patanjali",
        "description": "The foundational text of Yoga philosophy, consisting of 196 sutras organized into four chapters (padas).",
        "sections": []
    }

    for pada in PADAS:
        section = {
            "slug": pada["slug"],
            "title": pada["name"],
            "order": pada["order"],
            "blocks": []
        }

        pada_num = pada["order"]
        for sutra_num in range(1, pada["count"] + 1):
            key = f"{pada_num}.{sutra_num}"

            # Get Sanskrit (prefer fetched, fallback to empty)
            sanskrit_data = sanskrit.get(key, {})
            iast = sanskrit_data.get("iast", "")
            devanagari = sanskrit_data.get("devanagari", "")

            # Get translation (prefer fetched, fallback to manual)
            meaning = translations.get(key) or fallback.get(key, "")

            block = {
                "slug": key,
                "order": sutra_num,
                "content": devanagari,
                "transliteration": iast,
                "meaning": meaning,
                "url": f"https://swamij.com/yoga-sutras-{pada_num}{sutra_num:02d}.htm"
            }
            section["blocks"].append(block)

        data["sections"].append(section)

    return data


def main():
    """Main scraping function."""
    print("=" * 60)
    print("Yoga Sutras Scraper")
    print("=" * 60)

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Fetch from sources
    sanskrit = fetch_sanskrit_sutras()
    translations = fetch_english_translations()

    # Build combined data
    data = build_yoga_sutras_data(sanskrit, translations)

    # Count coverage
    total_sutras = sum(pada["count"] for pada in PADAS)
    sutras_with_sanskrit = sum(
        1 for section in data["sections"]
        for block in section["blocks"]
        if block["content"]
    )
    sutras_with_translation = sum(
        1 for section in data["sections"]
        for block in section["blocks"]
        if block["meaning"]
    )

    print(f"\nCoverage: {sutras_with_sanskrit}/{total_sutras} with Sanskrit")
    print(f"Coverage: {sutras_with_translation}/{total_sutras} with translation")

    # Save to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
