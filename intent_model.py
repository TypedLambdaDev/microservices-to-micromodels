import fasttext
import os

# Check if model exists, if not, create a placeholder message
model_path = "model/intent.ftz"
if not os.path.exists(model_path):
    print(f"Model file not found at {model_path}. Please run train_intent.py first.")
    model = None
else:
    model = fasttext.load_model(model_path)

def detect_intent(text: str):
    """
    Detect the intent of the given text.
    
    Args:
        text (str): The input text to classify
        
    Returns:
        str: The detected intent (CREATE, READ, UPDATE, DELETE, SEARCH)
        float: The confidence score
    """
    if model is None:
        raise RuntimeError("Model not loaded. Please run train_intent.py first.")
    
    # Get prediction
    prediction = model.predict(text)
    
    # Extract label and confidence
    label = prediction[0][0].replace("__label__", "")
    confidence = float(prediction[1][0])
    
    return label, confidence