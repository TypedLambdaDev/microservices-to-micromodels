import fasttext
import os

class FastTextWrapper:
    """
    A wrapper around fasttext to handle compatibility issues with numpy.
    """
    
    def __init__(self, model_path="model/intent.ftz"):
        """
        Initialize the wrapper with a model path.
        
        Args:
            model_path (str): Path to the fasttext model
        """
        self.model_path = model_path
        
        if not os.path.exists(model_path):
            print(f"Model file not found at {model_path}. Please run train_intent.py first.")
            self.model = None
        else:
            self.model = fasttext.load_model(model_path)
    
    def predict(self, text):
        """
        Predict the intent of the given text.
        
        Args:
            text (str): The input text to classify
            
        Returns:
            tuple: (intent, confidence)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Please run train_intent.py first.")
        
        # Get raw prediction
        raw_prediction = self.model.predict(text)
        
        # Extract label and confidence safely
        label = raw_prediction[0][0].replace("__label__", "")
        confidence = float(raw_prediction[1][0])
        
        return label, confidence

# Create a singleton instance
model = FastTextWrapper()