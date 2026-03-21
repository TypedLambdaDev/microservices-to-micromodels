import fasttext
import os
import warnings
from typing import Tuple, Optional, Any

from nlcrud.logger import get_logger
from nlcrud.exceptions import ModelNotFoundError, IntentClassificationError
from nlcrud.intent_classification.interface import IntentClassifier

logger = get_logger("intent_classification")


class FastTextIntentClassifier(IntentClassifier):
    """Production-ready intent classifier using FastText."""

    def __init__(self, model_path: str = "model/intent.ftz") -> None:
        """Initialize the classifier with a model path.

        Args:
            model_path: Path to the fasttext model

        Raises:
            ModelNotFoundError: If model file not found
        """
        self.model_path: str = model_path
        self.model: Optional[Any] = None

        if not os.path.exists(model_path):
            logger.error(f"Model file not found at {model_path}")
            raise ModelNotFoundError(
                f"Intent model not found at {model_path}. "
                f"Please run 'python -m nlcrud.intent_classification.train' first."
            )

        try:
            logger.info(f"Loading FastText model from: {model_path}")
            self.model = fasttext.load_model(model_path)
            logger.info("FastText model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load FastText model: {e}")
            raise ModelNotFoundError(f"Could not load model: {e}") from e

    def predict(self, text: str) -> Tuple[str, float]:
        """Predict the intent of the given text.

        Args:
            text: The input text to classify

        Returns:
            Tuple of (intent, confidence)

        Raises:
            IntentClassificationError: If classification fails
        """
        logger.debug(f"Classifying text: '{text}'")

        if self.model is None:
            logger.warning("Model is None, using rule-based fallback")
            return self._rule_based_predict(text)

        try:
            logger.debug(f"Using FastText model from: {self.model_path}")
            # Suppress numpy deprecation warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                prediction = self.model.predict(text)

            # Extract label and confidence
            label = prediction[0][0].replace("__label__", "")
            confidence = float(prediction[1][0])

            logger.info(f"Intent: {label} (confidence: {confidence:.4f})")
            logger.debug(f"Raw prediction: {prediction}")

            return label, confidence
        except Exception as e:
            logger.error(f"FastText prediction failed: {e}. Using fallback.")
            return self._rule_based_predict(text)
    
    def _rule_based_predict(self, text: str) -> Tuple[str, float]:
        """Rule-based intent classification as a fallback.

        Args:
            text: The input text to classify

        Returns:
            Tuple of (intent, confidence)
        """
        logger.info("Using rule-based intent classification fallback")
        text_lower = text.lower()

        # Simple keyword-based classification
        create_keywords = ["create", "add", "register", "new"]
        read_keywords = ["show", "list", "get", "display"]
        update_keywords = ["update", "change", "modify", "set"]
        delete_keywords = ["delete", "remove", "drop"]
        search_keywords = ["find", "search", "query", "where"]

        logger.debug(f"Checking for keywords in: '{text_lower}'")
        
        if any(word in text_lower for word in create_keywords):
            matching_words = [word for word in create_keywords if word in text_lower]
            logger.debug(f"Matched CREATE keywords: {matching_words}")
            return "CREATE", 0.95

        elif any(word in text_lower for word in read_keywords):
            matching_words = [word for word in read_keywords if word in text_lower]
            logger.debug(f"Matched READ keywords: {matching_words}")
            return "READ", 0.95

        elif any(word in text_lower for word in update_keywords):
            matching_words = [word for word in update_keywords if word in text_lower]
            logger.debug(f"Matched UPDATE keywords: {matching_words}")
            return "UPDATE", 0.95

        elif any(word in text_lower for word in delete_keywords):
            matching_words = [word for word in delete_keywords if word in text_lower]
            logger.debug(f"Matched DELETE keywords: {matching_words}")
            return "DELETE", 0.95

        elif any(word in text_lower for word in search_keywords):
            matching_words = [word for word in search_keywords if word in text_lower]
            logger.debug(f"Matched SEARCH keywords: {matching_words}")
            return "SEARCH", 0.95

        # Default fallback
        logger.warning("No keywords matched, defaulting to READ intent")
        return "READ", 0.6

# Create a singleton instance
classifier = FastTextIntentClassifier()