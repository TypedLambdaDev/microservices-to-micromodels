import spacy
import re
from nlcrud.db.schema import SCHEMA

class SpacyEntityExtractor:
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
        entities = {
            "resource": None,
            "filters": {},
            "data": {}
        }
        
        # Process the text with spaCy
        doc = self.nlp(text)
        
        # Extract resource type using spaCy entities
        for ent in doc.ents:
            if ent.label_ == "RESOURCE":
                # Remove trailing 's' if plural
                resource = ent.text.lower()
                if resource.endswith('s') and resource[:-1] in SCHEMA:
                    resource = resource[:-1]
                
                if resource in SCHEMA:
                    entities["resource"] = resource
                    break
        
        # Fallback to basic word matching if spaCy didn't find a resource
        if entities["resource"] is None:
            text_lower = text.lower()
            words = text_lower.split()
            
            # Extract resource type (user, order, etc.)
            for resource in SCHEMA:
                if resource in words:
                    entities["resource"] = resource
                    break
            
            # If we're showing "all users" or similar, set the resource
            if "users" in words and entities["resource"] is None:
                entities["resource"] = "user"
            
            if "orders" in words and entities["resource"] is None:
                entities["resource"] = "order"
        
        # Extract numeric entities (IDs, age, amount)
        self._extract_numeric_entities(text, doc, entities)
        
        # Extract name entities
        self._extract_name_entities(doc, entities)
        
        # Extract email entities
        self._extract_email_entities(text, entities)
        
        # Handle search queries
        self._handle_search_queries(text, entities)
        
        return entities
    
    def _extract_numeric_entities(self, text, doc, entities):
        """Extract numeric entities like IDs, age, and amount."""
        # Use spaCy's numeric entity recognition
        for token in doc:
            # Check for ID patterns
            if token.text.lower() == "id" and token.i + 1 < len(doc) and doc[token.i + 1].is_digit:
                entities["filters"]["id"] = int(doc[token.i + 1].text)
            
            # Check for age patterns
            if token.text.lower() == "age" and token.i + 1 < len(doc) and doc[token.i + 1].is_digit:
                entities["data"]["age"] = int(doc[token.i + 1].text)
            
            # Check for user_id patterns
            if (token.text.lower() == "user_id" or (token.text.lower() == "user" and 
                token.i + 1 < len(doc) and doc[token.i + 1].text.lower() == "id")) and \
                token.i + 2 < len(doc) and doc[token.i + 2].is_digit:
                entities["data"]["user_id"] = int(doc[token.i + 2].text)
        
        # Fallback to regex for more complex patterns
        # Extract ID filter
        id_match = re.search(r"id\s*(\d+)", text.lower())
        if id_match and "id" not in entities["filters"]:
            entities["filters"]["id"] = int(id_match.group(1))
        
        # Extract age with various patterns
        age_match = re.search(r"age\s*(\d+)", text.lower())
        if age_match and "age" not in entities["data"]:
            entities["data"]["age"] = int(age_match.group(1))
        
        # Alternative age pattern: "change age of user with id X to Y"
        alt_age_match = re.search(r"change\s+age\s+.*\s+to\s+(\d+)", text.lower())
        if alt_age_match and "age" not in entities["data"]:
            entities["data"]["age"] = int(alt_age_match.group(1))
            
        # Pattern for "X years old"
        years_old_match = re.search(r"(\d+)\s+years?\s+old", text.lower())
        if years_old_match and "age" not in entities["data"]:
            entities["data"]["age"] = int(years_old_match.group(1))
        
        # Extract amount (for orders)
        amount_match = re.search(r"amount\s*(\d+(?:\.\d+)?)", text.lower())
        if amount_match:
            entities["data"]["amount"] = float(amount_match.group(1))
        
        # Extract user_id (for orders)
        user_id_match = re.search(r"user[_\s]*id\s*(\d+)", text.lower())
        if user_id_match and "user_id" not in entities["data"]:
            entities["data"]["user_id"] = int(user_id_match.group(1))
    
    def _extract_name_entities(self, doc, entities):
        """Extract name entities using spaCy's named entity recognition."""
        # Look for PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON" and "name" not in entities["data"]:
                entities["data"]["name"] = ent.text
                break
        
        # Fallback to pattern matching if no PERSON entity found
        if "name" not in entities["data"]:
            for token_idx, token in enumerate(doc):
                if token.text.lower() == "name" and token_idx + 1 < len(doc):
                    # Get the next token as the name
                    name_token = doc[token_idx + 1]
                    if name_token.is_alpha:
                        entities["data"]["name"] = name_token.text
                        break
    
    def _extract_email_entities(self, text, entities):
        """Extract email entities."""
        # Use regex for email extraction as it's more reliable than spaCy for this
        email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
        if email_match:
            entities["data"]["email"] = email_match.group(0)
    
    def _handle_search_queries(self, text, entities):
        """Handle search queries by moving data to filters if appropriate."""
        text_lower = text.lower()
        words = text_lower.split()
        
        if "find" in words or "search" in words:
            if entities["resource"] is None:
                # Try to infer resource from context
                if "user" in words or "users" in words:
                    entities["resource"] = "user"
                elif "order" in words or "orders" in words:
                    entities["resource"] = "order"
            
            # Move data to filters for search
            for key, value in list(entities["data"].items()):
                if key not in entities["filters"]:
                    entities["filters"][key] = value

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