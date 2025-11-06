from transformers import pipeline

# Load summarizer model once at import
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")


def create_ai_summary(text, max_length=80, min_length=20):
    """
    Creates an AI summary from full article text.
    Falls back to a truncated version if text is very short.

    Args:
        text (str): Full article content
        max_length (int): Max tokens in summary
        min_length (int): Min tokens in summary
    Returns:
        str: Summary
    """
    if not text or len(text.split()) < 5:
        return "No summary available."

    try:
        summary = summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        return summary[0]['summary_text']
    except Exception as e:
        print(f"[WARN] Summarization failed: {e}")
        # fallback to simple truncation
        return text[:200] + "..."
