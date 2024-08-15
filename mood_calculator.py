import json


def calculate_weighted_sentiment(new_message_category, new_message_score):
    if new_message_category == 'POSITIVE':
        default_weighted_score = new_message_score
    elif new_message_category == 'NEUTRAL':
        default_weighted_score = 0.5 * new_message_score
    else:
        default_weighted_score = -1 * new_message_score

    try:
        with open('messages.json', 'r') as f:
            messages = json.load(f)

            total_weighted_score = default_weighted_score
            total_score = new_message_score

            for message in messages:
                label = message['label']
                score = message['score']
                weight = -1

                if label == 'POSITIVE':
                    weight = 1
                elif label == 'NEUTRAL':
                    weight = 0.5

                weighted_score = weight * score

                total_weighted_score += weighted_score
                total_score += score

            if total_score != 0:
                weighted_sentiment = total_weighted_score / total_score
            else:
                weighted_sentiment = 0

        return (weighted_sentiment + 1) * 2.5
    except json.JSONDecodeError:
        return (default_weighted_score + 1) * 2.5


def save_message(chat_id, label, score, mood, date):
    data = {
        "chat_name": chat_id,
        "label": label,
        "score": score,
        "mood": mood,
        "date": date.isoformat()
    }
    with open('test_messages.json', 'a') as f:
        json.dump(data, f)
        f.write('\n')