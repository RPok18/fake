
import sys
import logging
from app import comprehensive_verification_api

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

test_text = "The moon landing was faked by NASA in a studio."
print(f"Testing verifcation with text: {test_text}")

try:
    result = comprehensive_verification_api(test_text)
    print("Result:", result)
except Exception as e:
    print("Error:", e)
