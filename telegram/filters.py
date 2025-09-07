
KEYWORDS = ["job", "hiring", "opening", "shortlist", "shortlisted", "interview", "vacancy", "walk-in", "requirement"]

def is_job_related(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(k in lower for k in KEYWORDS)
