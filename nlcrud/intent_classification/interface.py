"""
Intent classification interface module.
Provides a unified API for intent classification.
"""
from .classifier import classifier

def predict_intent(text):
    """
    Predict the intent of the given text.
    
    Args:
        text (str): The input text to classify
        
    Returns:
        tuple: (intent, confidence)
    """
    return classifier.predict(text)