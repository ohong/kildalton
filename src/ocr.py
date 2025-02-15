import os
import base64
from openai import OpenAI
from datetime import datetime
from typing import Dict, Any, Optional

class TradeParser:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

    def parse_screenshot(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract trade information from a Robinhood screenshot using GPT-4V.
        Returns a dictionary with trade details or error message.
        """
        try:
            # Convert image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Ask GPT-4V to extract the information
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract these trade details from the Robinhood screenshot and return them in JSON format:
                            {
                                "trade_type": "buy" or "sell",
                                "ticker": "stock symbol",
                                "quantity": number of shares,
                                "price": price per share,
                                "date": "trade date"
                            }
                            If any field is not visible, leave it as null."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }],
                max_tokens=300
            )
            
            # Get the response text
            result = response.choices[0].message.content
            
            # TODO: Parse the JSON response
            # For now, return a basic structure
            return {
                "success": True,
                "trade_type": None,  # Will be filled by GPT-4V
                "ticker": None,      # Will be filled by GPT-4V
                "quantity": None,    # Will be filled by GPT-4V
                "price": None,       # Will be filled by GPT-4V
                "date": None        # Will be filled by GPT-4V
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
