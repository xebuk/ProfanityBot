import re

vowels = "аеёиоуыэюя"
consonants = "бвгджзйклмнпрстфхцчшщ"
special_chars = "ъь"

profanity_ngrams = ["бля", "ху", "пиз", "пез", "еб",
                    "гонд", "ганд", "сук", "cуч", "пид",
                    "блан", "своло", "убл", "мраз", "пед",
                    "дроч"]

def extract_features_from_word(word):
    return {
        "length": len(word),
        "vowel_count": sum(word.count(c) for c in vowels),
        "consonant_count": sum(word.count(c) for c in consonants),
        "special_char_count": sum(word.count(c) for c in special_chars),
        "consonant_clusters": len(re.findall(rf"[{consonants}]{3,}", word)),
        "vowel_clusters": len(re.findall(rf"[{vowels}]{3,}", word)),
        "starts_with_consonant": int(word[0] in consonants) if word else 0,
        "ends_with_vowel": int(word[-1] in vowels) if word else 0,
        "ends_with_special_char": int(word[-1] in special_chars) if word else 0,
        "contains_common_profanity_ngrams": int(any(ngram in word for ngram in profanity_ngrams))
    }