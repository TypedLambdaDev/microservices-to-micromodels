import spacy
import re
from typing import Dict, Any

from nlcrud.db.schema import SCHEMA
from nlcrud.entity_extraction.interface import EntityExtractor
from nlcrud.logger import get_logger

logger = get_logger("entity_extraction.spacy")


class SpacyEntityExtractor(EntityExtractor):
    """
    Entity extractor using spaCy NLP capabilities for more accurate entity recognition.
    """
    
    def __init__(self, model_name="en_core_web_sm"):
        """
        Initialize the SpaCy entity extractor with a language model.
        
        Args:
            model_name (str): Name of the spaCy model to use
        """
        self.nlp = spacy.load(model_name)
        
        # Add custom pipeline components for domain-specific entities
        self._add_custom_components()
    
    def _add_custom_components(self):
        """Add custom pipeline components for domain-specific entity recognition."""
        # Add custom patterns for resource types
        resource_patterns = []
        for resource in SCHEMA:
            # Add patterns for singular and plural forms
            resource_patterns.append({"label": "RESOURCE", "pattern": resource})
            resource_patterns.append({"label": "RESOURCE", "pattern": f"{resource}s"})
        
        # Add entity ruler if we have patterns
        if resource_patterns:
            # Check if entity ruler already exists
            if "entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
                ruler.add_patterns(resource_patterns)
            else:
                # Get existing ruler and add patterns
                ruler = self.nlp.get_pipe("entity_ruler")
                ruler.add_patterns(resource_patterns)
    
    def extract_entities(self, text):
        """
        Extract entities from the given text using spaCy NLP.
        
        Args:
            text (str): The input text to extract entities from
            
        Returns:
            dict: A dictionary containing the extracted resource, filters, and data
        """
        logger.debug("===== SpaCy Entity Extraction =====")

        logger.debug(f"Input text for entity extraction: '{text}'")
        logger.debug(f"Using spaCy model: {self.nlp.meta['name']}")
        logger.debug(f"Pipeline components: {self.nlp.pipe_names}")
        
        entities = {
            "resource": None,
            "filters": {},
            "data": {}
        }
        
        # Process the text with spaCy
        logger.debug("Processing text with spaCy...")
        doc = self.nlp(text)
        logger.debug(f"Tokens: {[token.text for token in doc]}")
        logger.debug(f"Named entities recognized by spaCy: {[(ent.text, ent.label_) for ent in doc.ents]}")
        
        # Extract resource type using spaCy entities
        logger.debug("\nExtracting resource type...")
        for ent in doc.ents:
            if ent.label_ == "RESOURCE":
                logger.debug(f"Found RESOURCE entity: {ent.text}")
                # Remove trailing 's' if plural
                resource = ent.text.lower()
                if resource.endswith('s') and resource[:-1] in SCHEMA:
                    resource = resource[:-1]
                    logger.debug(f"Removing plural 's' from '{ent.text}' -> '{resource}'")
                
                if resource in SCHEMA:
                    entities["resource"] = resource
                    logger.debug(f"Resource type set to: {resource}")
                    break
        
        # Fallback to basic word matching if spaCy didn't find a resource
        if entities["resource"] is None:
            logger.debug("No resource found via spaCy entities, falling back to word matching")
            text_lower = text.lower()
            words = text_lower.split()
            logger.debug(f"Words in text: {words}")
            
            # Extract resource type (user, order, etc.)
            for resource in SCHEMA:
                if resource in words:
                    entities["resource"] = resource
                    logger.debug(f"Found resource '{resource}' in words")
                    break
            
            # If we're showing "all users" or similar, set the resource
            if "users" in words and entities["resource"] is None:
                entities["resource"] = "user"
                logger.debug("Found 'users' in text, setting resource to 'user'")
            
            if "orders" in words and entities["resource"] is None:
                entities["resource"] = "order"
                logger.debug("Found 'orders' in text, setting resource to 'order'")
        
        # Extract numeric entities (IDs, age, amount)
        self._extract_numeric_entities(text, doc, entities)
        
        # Extract name entities
        self._extract_name_entities(doc, entities)
        
        # Extract email entities
        self._extract_email_entities(text, entities)
        
        # Handle search queries
        self._handle_search_queries(text, entities)
        
        logger.debug("\n----- Entity Extraction Results -----")
        logger.debug(f"Final extracted entities: {entities}")
        
        return entities
    
    def _extract_numeric_entities(self, text, doc, entities):
        """Extract numeric entities like IDs, age, and amount."""
        logger.debug("\nExtracting numeric entities...")
        
        # Use spaCy's numeric entity recognition
        for token in doc:
            # Check for ID patterns
            if token.text.lower() == "id" and token.i + 1 < len(doc) and doc[token.i + 1].is_digit:
                entities["filters"]["id"] = int(doc[token.i + 1].text)
                logger.debug(f"Found ID: {entities['filters']['id']} (token-based)")
            
            # Check for age patterns
            if token.text.lower() == "age" and token.i + 1 < len(doc) and doc[token.i + 1].is_digit:
                entities["data"]["age"] = int(doc[token.i + 1].text)
                logger.debug(f"Found age: {entities['data']['age']} (token-based)")
            
            # Check for user_id patterns
            if (token.text.lower() == "user_id" or (token.text.lower() == "user" and
                token.i + 1 < len(doc) and doc[token.i + 1].text.lower() == "id")) and \
                token.i + 2 < len(doc) and doc[token.i + 2].is_digit:
                entities["data"]["user_id"] = int(doc[token.i + 2].text)
                logger.debug(f"Found user_id: {entities['data']['user_id']} (token-based)")
        
        # Fallback to regex for more complex patterns
        logger.debug("Applying regex patterns for entity extraction...")
        
        # Extract ID filter
        id_match = re.search(r"id\s*(\d+)", text.lower())
        if id_match and "id" not in entities["filters"]:
            entities["filters"]["id"] = int(id_match.group(1))
            logger.debug(f"Found ID: {entities['filters']['id']} (regex-based)")
        
        # Extract age with various patterns
        age_match = re.search(r"age\s*(\d+)", text.lower())
        if age_match and "age" not in entities["data"]:
            entities["data"]["age"] = int(age_match.group(1))
            logger.debug(f"Found age: {entities['data']['age']} (regex pattern: 'age\\s*(\\d+)')")
        
        # Alternative age pattern: "change age of user with id X to Y"
        alt_age_match = re.search(r"change\s+age\s+.*\s+to\s+(\d+)", text.lower())
        if alt_age_match and "age" not in entities["data"]:
            entities["data"]["age"] = int(alt_age_match.group(1))
            logger.debug(f"Found age: {entities['data']['age']} (regex pattern: 'change\\s+age\\s+.*\\s+to\\s+(\\d+)')")
            
        # Pattern for "X years old"
        years_old_match = re.search(r"(\d+)\s+years?\s+old", text.lower())
        if years_old_match and "age" not in entities["data"]:
            entities["data"]["age"] = int(years_old_match.group(1))
            logger.debug(f"Found age: {entities['data']['age']} (regex pattern: '(\\d+)\\s+years?\\s+old')")
        
        # Extract amount (for orders)
        amount_match = re.search(r"amount\s*(\d+(?:\.\d+)?)", text.lower())
        if amount_match:
            entities["data"]["amount"] = float(amount_match.group(1))
            logger.debug(f"Found amount: {entities['data']['amount']} (regex-based)")
        
        # Extract user_id (for orders)
        user_id_match = re.search(r"user[_\s]*id\s*(\d+)", text.lower())
        if user_id_match and "user_id" not in entities["data"]:
            entities["data"]["user_id"] = int(user_id_match.group(1))
            logger.debug(f"Found user_id: {entities['data']['user_id']} (regex-based)")
    
    def _extract_name_entities(self, doc, entities):
        """Extract name entities using spaCy's named entity recognition."""
        logger.debug("\nExtracting name entities...")
        
        # Look for PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON" and "name" not in entities["data"]:
                entities["data"]["name"] = ent.text
                logger.debug(f"Found name: {entities['data']['name']} (spaCy PERSON entity)")
                break
        
        # Fallback to pattern matching if no PERSON entity found
        if "name" not in entities["data"]:
            logger.debug("No PERSON entity found, trying pattern matching for name")
            for token_idx, token in enumerate(doc):
                if token.text.lower() == "name" and token_idx + 1 < len(doc):
                    # Get the next token as the name
                    name_token = doc[token_idx + 1]
                    if name_token.is_alpha:
                        entities["data"]["name"] = name_token.text
                        logger.debug(f"Found name: {entities['data']['name']} (pattern matching)")
                        break
    
    def _extract_email_entities(self, text, entities):
        """Extract email entities."""
        logger.debug("\nExtracting email entities...")
        
        # Use regex for email extraction as it's more reliable than spaCy for this
        email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
        if email_match:
            entities["data"]["email"] = email_match.group(0)
            logger.debug(f"Found email: {entities['data']['email']} (regex-based)")
    
    def _handle_search_queries(self, text, entities):
        """Handle search queries by moving data to filters if appropriate."""
        logger.debug("\nHandling search queries...")
        
        text_lower = text.lower()
        words = text_lower.split()
        
        if "find" in words or "search" in words:
            logger.debug("Detected search query based on keywords: 'find' or 'search'")
            
            if entities["resource"] is None:
                logger.debug("Resource not yet determined, trying to infer from context")
                # Try to infer resource from context
                if "user" in words or "users" in words:
                    entities["resource"] = "user"
                    logger.debug("Inferred resource: 'user'")
                elif "order" in words or "orders" in words:
                    entities["resource"] = "order"
                    logger.debug("Inferred resource: 'order'")
            
            # Move data to filters for search
            if entities["data"]:
                logger.debug("Moving data to filters for search query:")
                for key, value in list(entities["data"].items()):
                    if key not in entities["filters"]:
                        entities["filters"][key] = value
                        logger.debug(f"  - Moved '{key}': {value} from data to filters")

# Create a singleton instance for easy import
extractor = SpacyEntityExtractor()

def extract_entities(text):
    """
    Extract entities from the given text using the SpacyEntityExtractor.
    This function maintains the same interface as the original extract_entities function.
    
    Args:
        text (str): The input text to extract entities from
        
    Returns:
        dict: A dictionary containing the extracted resource, filters, and data
    """
    return extractor.extract_entities(text)