class SuggestionService:
    @staticmethod
    def get_suggestions() -> list[str]:
        # These could be dynamically fetched from KB or audit logs in the future.
        # For now, we return high-quality common questions.
        return [
            "Can foreigners buy land in Kenya?",
            "How much is stamp duty in Nairobi?",
            "How do I verify land ownership?",
            "What documents are needed before buying land?",
            "How do I get a building permit in Kiambu?",
            "What is the process of land registration in Kenya?",
            "What is conveyancing law in Kenya?"
        ]
