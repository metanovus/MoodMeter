from transformers import pipeline


sentiment_pipeline = pipeline("sentiment-analysis",
                              model="blanchefort/rubert-base-cased-sentiment-rurewiews")


def predict_sentiment(message):
    sentiment = sentiment_pipeline(message)[0]
    label = sentiment['label']
    score = sentiment['score']
    return label, score
