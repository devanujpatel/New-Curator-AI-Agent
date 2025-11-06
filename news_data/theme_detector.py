from transformers import pipeline

# Predefined candidate themes
candidate_labels = [
    "Mergers & Acquisitions",
    "Startups",
    "Venture Capital & Funding",
    "Stock Market & Investing",
    "Corporate Earnings & Financial Reports",
    "Regulation & Antitrust",
    "Banking & Fintech",
    "Global Trade & Economy",
    "Artificial Intelligence & Machine Learning",
    "Cloud Computing & Infrastructure",
    "Cybersecurity & Data Privacy",
    "Semiconductors & Chips",
    "Quantum Computing",
    "Blockchain & Cryptocurrencies",
    "Big Tech Companies",
    "E-commerce & Retail Tech",
    "Gaming & Esports",
    "Enterprise Software & SaaS",
    "Climate Tech & Sustainability",
    "Healthcare Technology",
    "Automotive & Electric Vehicles",
    "Space Industry & Satellites",
    "Government Tech & Policy",
    "Workplace & Future of Work",
    "Media & Streaming Services",
    "Robotics & Automation",
    "Emerging Technology, Markets or Industries",
]

zero_shot_classifier = pipeline(
    "zero-shot-classification",
    model="valhalla/distilbart-mnli-12-1"  # "facebook/bart-large-mnli"
)


def detect_themes_zeroshot(input_str):
    # print("detect_themes_zeroshot called")
    result = zero_shot_classifier(input_str, candidate_labels=candidate_labels, multi_label=True)
    return sorted(
        [(label, round(score, 2)) for label, score in zip(result["labels"], result["scores"]) if score > 0.4])[:3]
