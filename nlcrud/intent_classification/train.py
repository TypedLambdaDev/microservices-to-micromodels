import fasttext

from nlcrud.logger import get_logger

logger = get_logger("intent_classification.train")

# Train the model
model = fasttext.train_supervised(
    input="data/intent_train.txt",
    epoch=50,
    lr=1.0,
    wordNgrams=2
)

# Save the model
model.save_model("model/intent.ftz")

logger.info("Model trained and saved successfully.")