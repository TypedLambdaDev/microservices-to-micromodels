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
        if self.model is None:
            # Fallback to rule-based classification if model is not available
            return self._rule_based_predict(text)
        
        try:
            # Get prediction from model
            # Suppress warnings by using a try-except block
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                prediction = self.model.predict(text)
            
            # Extract label and confidence
            label = prediction[0][0].replace("__label__", "")
            confidence = float(prediction[1][0])
            
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
        text_lower = text.lower()
        
        # Simple keyword-based classification
        if any(word in text_lower for word in ["create", "add", "register", "new"]):
            return "CREATE", 0.95
        
        elif any(word in text_lower for word in ["show", "list", "get", "display"]):
            return "READ", 0.95
        
        elif any(word in text_lower for word in ["update", "change", "modify", "set"]):
            return "UPDATE", 0.95
        
        elif any(word in text_lower for word in ["delete", "remove", "drop"]):
            return "DELETE", 0.95
        
        elif any(word in text_lower for word in ["find", "search", "query", "where"]):
            return "SEARCH", 0.95
        
        # Default fallback
        return "READ", 0.6

# Create a singleton instance
classifier = IntentClassifier()