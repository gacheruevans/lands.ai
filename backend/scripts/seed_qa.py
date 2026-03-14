
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("backend/src"))

from lands_ai_backend.schemas.knowledge import IngestDocumentRequest
from lands_ai_backend.services.knowledge_ingestion import KnowledgeIngestionService
from lands_ai_backend.core.db import initialize_database

COMMON_QA = [
    {
        "question": "Can foreigners buy land in Kenya?",
        "answer": "Yes, foreigners can buy land in Kenya, but with restrictions. Under the Constitution and the Land Act, non-citizens can only hold land on a leasehold basis for a maximum period of 99 years. They cannot own freehold land or agricultural land (unless specifically exempted by the President).",
        "topics": ["foreign-ownership", "leasehold", "legality"]
    },
    {
        "question": "How much is stamp duty in Nairobi?",
        "answer": "For property within municipalities (including Nairobi), the stamp duty is typically 4% of the property's valuation. For properties in rural areas, the rate is usually 2%. Stamp duty is paid to the Kenya Revenue Authority (KRA) during the property transfer process.",
        "topics": ["stamp-duty", "nairobi", "valuation"]
    },
    {
        "question": "How do I verify land ownership?",
        "answer": "To verify land ownership in Kenya, you should conduct an official search at the relevant land registry. You will need a copy of the title deed and the owner's ID. The search will reveal the registered owner, any encumbrances (like charges or caveats), and the type of land tenure.",
        "topics": ["ownership", "title-search", "registration"]
    },
    {
        "question": "What documents are needed before buying land?",
        "answer": "Essential documents include: an official search report, the original title deed, Land Control Board consent (if agricultural), KRA PINs for both buyer and seller, and a duly signed transfer instrument. You should also verify the land rates payment status.",
        "topics": ["registration", "documentation", "checklist"]
    },
    {
        "question": "How do I get a building permit in Kiambu?",
        "answer": "Building permits in Kiambu are handled by the County Government of Kiambu. You must submit architectural and structural plans through their online portal (e-development system), pay the requisite fees, and wait for approval from the sub-county planning office. Ensuring compliance with zoning regulations is critical.",
        "topics": ["county-rates", "registration", "approvals"]
    }
]

def seed():
    # Ensure tables exist
    print("Ensuring database is initialized...")
    initialize_database()
    
    service = KnowledgeIngestionService()
    print(f"Seeding {len(COMMON_QA)} Q&A pairs...")
    
    for i, qa in enumerate(COMMON_QA):
        source_id = f"faq:common-qa:{i}"
        payload = IngestDocumentRequest(
            source_id=source_id,
            title=qa["question"],
            text=qa["answer"],
            jurisdiction="KE",
            source_type="faq",
            topics=qa["topics"]
        )
        try:
            res = service.ingest(payload)
            print(f"Ingested: {qa['question']} -> {res.chunks_created} chunks")
        except Exception as e:
            print(f"Failed to ingest '{qa['question']}': {e}")

if __name__ == "__main__":
    seed()
