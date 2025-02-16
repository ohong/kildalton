import os
import json
import base64
from openai import OpenAI
from datetime import datetime
from typing import Dict, Any, Optional

class TradeParser:
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))

    def parse_screenshot(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extract trade information from a Robinhood screenshot using OpenAI's gpt-4o-mini.
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
                            "text": """You are a JSON extractor. Your task is to extract trade details from a Robinhood screenshot and output ONLY a JSON object with this structure:
{
    "trade_type": "buy" or "sell",
    "ticker": "stock symbol",
    "quantity": number,
    "price": number,
    "date": "YYYY-MM-DD"
}
Use null for any missing values. Output ONLY the JSON object, no other text or explanation."""
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
            
            # Get the response text and parse JSON
            raw_result = response.choices[0].message.content.strip()
            print(f"Raw GPT response: {raw_result}")  # Debug output
            
            try:
                # Try to clean the response if it contains markdown code blocks
                if "```json" in raw_result:
                    raw_result = raw_result.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_result:
                    raw_result = raw_result.split("```")[1].strip()
                
                parsed_data = json.loads(raw_result)
                return {
                    "success": True,
                    "trade_type": parsed_data.get("trade_type"),
                    "ticker": parsed_data.get("ticker"),
                    "quantity": parsed_data.get("quantity"),
                    "price": parsed_data.get("price"),
                    "date": parsed_data.get("date")
                }
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Failed to parse GPT response as JSON. Raw response: {raw_result}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
