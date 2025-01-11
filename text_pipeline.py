import unicodedata
from collections import Counter
import requests
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
import spacy
nlp = spacy.load('en_core_web_sm')
# Make sure you have downloaded all necessary data in your environment:
#   nltk.download('punkt')
#   nltk.download('stopwords')
#   nltk.download('wordnet')
#   python -m spacy download en_core_web_sm



def remove_named_entities(text):
    """
    Use spaCy's NER to remove PERSON entities from text.
    Returns a set of person tokens (lowercased).
    """
    doc = nlp(text)
    person_tokens = set()
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Add each token (e.g., multi-word names get split)
            for token in ent:
                person_tokens.add(token.text.lower())
    return person_tokens


def normalize_text(text):
    """
    Normalize characters (accented → unaccented)
    and remove combining marks (e.g., diacritics).
    """
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def clean_and_tokenize(text):
    """
    1. Identify person names (spaCy) in the ORIGINAL text (not lowercased).
    2. Then lowercase, tokenize, remove stopwords, remove person-named tokens.
    """
    # Identify named entities from the original, case-sensitive text
    person_names = remove_named_entities(text)

    # Now do the cleaning on a lowercased version
    text_lower = text.lower()
    tokens = word_tokenize(text_lower)
    tokens = [t for t in tokens if t.isalpha()]

    stop_words = set(stopwords.words('english'))
    tokens = [t for t in tokens if t not in stop_words]

    # Remove detected person names
    tokens = [t for t in tokens if t not in person_names]
    return tokens


def count_word_frequencies(tokens):
    """Return a Counter of word frequencies."""
    return Counter(tokens)


def get_top_n_words(word_freqs, n=20):
    """Return the top n most common words with frequencies."""
    return word_freqs.most_common(n)


def get_word_definition(word):
    """
    Tries dictionaryapi.dev first.
    If no definitions or error, fall back to WordNet.
    Returns a list with a structure similar to dictionaryapi.dev's response:
       [
         {
           "word": <the word>,
           "meanings": [
             {
               "partOfSpeech": <POS>,
               "definitions": [
                 {"definition": <definition_string>}
               ]
             }
           ]
         }
       ]
    """
    # 1. Try dictionaryapi.dev
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        data = response.json()
        # If valid data is returned, it should be a list
        if isinstance(data, list) and len(data) > 0:
            return data
    except requests.RequestException as e:
        print(f"Error fetching definition for {word} from dictionaryapi.dev: {e}")

    # 2. Fallback to WordNet
    synsets = wordnet.synsets(word)
    if synsets:
        # Return the first synset's definition
        definition = synsets[0].definition()
        # Map it to a structure that somewhat resembles dictionaryapi.dev
        return [{
            "word": word,
            "meanings": [
                {
                    "partOfSpeech": synsets[0].pos() or "",
                    "definitions": [{"definition": definition}]
                }
            ]
        }]
    
    # 3. If none found, return empty list
    return []


def get_first_definition(definition_data, max_length=100):
    """
    Returns a short snippet from the first definition if it exists.
    Truncates the snippet to max_length characters for brevity.
    """
    if not definition_data or not isinstance(definition_data, list):
        return None
    
    # The dictionaryapi.dev format is:
    # [
    #   {
    #     "word": ...
    #     "meanings": [
    #       {
    #         "partOfSpeech": ...,
    #         "definitions": [
    #           {"definition": "some text", "example": "..."},
    #           ...
    #         ]
    #       }
    #     ]
    #   }
    # ]
    for entry in definition_data:
        meanings = entry.get("meanings", [])
        for meaning in meanings:
            definitions = meaning.get("definitions", [])
            if definitions:
                snippet = definitions[0].get("definition", "")
                if snippet:
                    return (snippet[:max_length] + "...") if len(snippet) > max_length else snippet
    return None


def process_subtitle_text(raw_text, top_n=20):
    """
    1. Normalize text
    2. Tokenize and remove stopwords (plus remove named entities)
    3. Count word frequencies
    4. Fetch definitions for top n words
    5. Return list of dicts: {word, frequency, definition_data}
    """
    normalized_text = normalize_text(raw_text)
    tokens = clean_and_tokenize(normalized_text)
    freqs = count_word_frequencies(tokens)
    top_words = get_top_n_words(freqs, top_n)

    results = []
    for word, freq in top_words:
        definition_data = get_word_definition(word)
        results.append({
            'word': word,
            'frequency': freq,
            'definition_data': definition_data
        })
    return results

