import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.metadata import extract_metadata, ALLOWED_VERBS

load_dotenv()

DUMMY_TEXT = """
Welcome to the podcast. Today I'm speaking with Sam Altman, CEO of OpenAI.
We discuss the future of AGI, AI safety concerns, and what Microsoft's partnership
with OpenAI means for the industry. Sam co-founded OpenAI with Elon Musk, though Elon
later left the board. Sam believes we need to move carefully and advocates strongly
for AI safety research. He has also warned against rushing deployment without proper alignment.
"""

def test_metadata_extraction():
    print("Testing Tiered Relationship Extraction...")

    if not os.getenv("MOONSHOT_API_KEY"):
        print("FAIL: MOONSHOT_API_KEY not set.")
        return False

    data = extract_metadata(DUMMY_TEXT)
    print(f"\nEntities:")
    print(f"  Guests:    {data.get('guests')}")
    print(f"  Topics:    {data.get('topics')}")
    print(f"  Companies: {data.get('companies')}")
    print(f"\nRelationships ({len(data.get('relationships', []))}):")
    for r in data.get('relationships', []):
        print(f"  {r['subject']} --[{r['verb']}]--> {r['object']}")

    # Validations
    if 'relationships' not in data:
        print("\nFAIL: No 'relationships' key in response.")
        return False

    # Check all verbs are from allowed list
    bad_verbs = [r['verb'] for r in data['relationships'] if r['verb'] not in ALLOWED_VERBS]
    if bad_verbs:
        print(f"\nFAIL: Disallowed verbs found: {bad_verbs}")
        return False

    # Expect at least some relationships
    if len(data['relationships']) == 0:
        print("\nWARNING: No relationships extracted. Prompt may need tuning.")
    else:
        print("\nSUCCESS: Relationships extracted with valid verbs.")

    return True

if __name__ == "__main__":
    test_metadata_extraction()
