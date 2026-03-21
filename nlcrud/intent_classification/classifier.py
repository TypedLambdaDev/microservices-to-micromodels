import fasttext
import os
import numpy as np

class IntentClassifier:
    """
    Production-ready intent classifier using FastText.
    """
    
    def __init__(self, model_path="model/intent.ftz"):
        """
        Initialize the classifier with a model path.
        
        Args:
            model_path (str): Path to the fasttext model
        """
        self.model_path = model_path
        
        if not os.path.exists(model_path):
            print(f"Model file not found at {model_path}. Please run train_intent.py first.")
            self.model = None
        else:
            try:
                self.model = fasttext.load_model(model_path)
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                self.model = None
    
    def predict(self, text):
        """
        Predict the intent of the given text.
        
        Args:
            text (str): The input text to classify
            
        Returns:
            tuple: (intent, confidence)
        """
        print("\n----- Intent Classification Details -----")
        print(f"Input text for classification: '{text}'")
        
        if self.model is None:
            print("Model not loaded, using rule-based fallback")
            # Fallback to rule-based classification if model is not available
            return self._rule_based_predict(text)
        
        try:
            # Get prediction from model
            print(f"Using FastText model from: {self.model_path}")
            # Suppress warnings by using a try-except block
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                prediction = self.model.predict(text)

            # Extract label and confidence
            label = prediction[0][0].replace("__label__", "")
            confidence = float(prediction[1][0])
            
            print(f"FastText prediction: {label} (confidence: {confidence:.4f})")
            print(f"Raw prediction data: {prediction}")
            
            return label, confidence
        except Exception as e:
            print(f"Error during prediction: {str(e)}. Using rule-based fallback.")
            return self._rule_based_predict(text)
    
    def _rule_based_predict(self, text):
        """
        Rule-based intent classification as a fallback.
        
        Args:
            text (str): The input text to classify
            
        Returns:
            tuple: (intent, confidence)
        """
        print("Using rule-based intent classification")
        text_lower = text.lower()
        
        # Simple keyword-based classification
        create_keywords = ["create", "add", "register", "new"]
        read_keywords = ["show", "list", "get", "display"]
        update_keywords = ["update", "change", "modify", "set"]
        delete_keywords = ["delete", "remove", "drop"]
        search_keywords = ["find", "search", "query", "where"]
        
        print(f"Checking for keywords in: '{text_lower}'")
        
        if any(word in text_lower for word in create_keywords):
            matching_words = [word for word in create_keywords if word in text_lower]
            print(f"Matched CREATE keywords: {matching_words}")
            return "CREATE", 0.95
        
        elif any(word in text_lower for word in read_keywords):
            matching_words = [word for word in read_keywords if word in text_lower]
            print(f"Matched READ keywords: {matching_words}")
            return "READ", 0.95
        
        elif any(word in text_lower for word in update_keywords):
            matching_words = [word for word in update_keywords if word in text_lower]
            print(f"Matched UPDATE keywords: {matching_words}")
            return "UPDATE", 0.95
        
        elif any(word in text_lower for word in delete_keywords):
            matching_words = [word for word in delete_keywords if word in text_lower]
            print(f"Matched DELETE keywords: {matching_words}")
            return "DELETE", 0.95
        
        elif any(word in text_lower for word in search_keywords):
            matching_words = [word for word in search_keywords if word in text_lower]
            print(f"Matched SEARCH keywords: {matching_words}")
            return "SEARCH", 0.95
        
        # Default fallback
        print("No keywords matched, defaulting to READ intent")
        return "READ", 0.6

# Create a singleton instance
classifier = IntentClassifier()