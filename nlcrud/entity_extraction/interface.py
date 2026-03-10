"""
Entity extraction interface module.
Provides a unified API for different entity extraction implementations.
"""
import os
from .regex_extractor import extract_entities as regex_extract_entities
from .spacy_extractor import extract_entities as spacy_extract_entities

def extract_entities(text):
    """
    Extract entities from the given text using the configured extractor.
    
    Args:
        text (str): The input text to extract entities from
        
    Returns:
        dict: A dictionary containing the extracted resource, filters, and data
    """
    # Use environment variable to control which extractor to use
    use_regex = os.environ.get("USE_REGEX_EXTRACTOR", "").lower() in ("true", "1", "yes")
    
    if use_regex:
        return regex_extract_entities(text)
    else:
        try:
            return spacy_extract_entities(text)
        except Exception as e:
            # Fallback to regex extractor if spaCy fails
            print(f"SpaCy extractor failed: {str(e)}. Falling back to regex extractor.")
            return regex_extract_entities(text)

def compare_extractors(text):
    """
    Compare the results of both entity extractors for the same text.
    
    Args:
        text (str): The input text to extract entities from
        
    Returns:
        dict: The results from both extractors
    """
    # Extract entities using both extractors
    regex_entities = regex_extract_entities(text)
    spacy_entities = spacy_extract_entities(text)
    
    return {
        "text": text,
        "regex_extractor": regex_entities,
        "spacy_extractor": spacy_entities
    }