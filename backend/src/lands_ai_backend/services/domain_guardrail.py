from lands_ai_backend.services.text_processing import TOPIC_KEYWORDS, tokenize_query_terms

class DomainGuardrail:
    """Service to ensure queries remain within the Kenyan land/property law domain."""

    @staticmethod
    def is_in_domain(question: str) -> bool:
        # 1. Check against our defined topic keywords
        question_lower = question.lower()
        for keywords in TOPIC_KEYWORDS.values():
            if any(keyword in question_lower for keyword in keywords):
                return True
        
        # 2. Check for general legal/land terms even if not in specific topic buckets
        tokens = set(tokenize_query_terms(question))
        domain_terms = {
            "kenya", "kenyan", "land", "property", "plot", "title", "deed", 
            "registry", "survey", "boundary", "duty", "tax", "fee", "permit",
            "building", "construction", "owner", "buyer", "seller", "lease",
            "rent", "rates", "valuation", "law", "legal", "advocate", "process"
        }
        
        if tokens.intersection(domain_terms):
            return True
            
        return False
