# Trading Contest Platform

A Streamlit-based web application for organizing and participating in stock trading contests.

## Features

- Create contests with customizable profit targets
- Join contests using unique invite codes
- Upload trade screenshots from Robinhood (iOS)
- Automatic trade detail extraction using GPT-4V
- Real-time leaderboard
- Manual trade entry fallback
- Automated winner payouts via Payman

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
PAYMAN_API_KEY=your_payman_api_key  # Get from app.paymanai.com
```

Note: To enable contest payouts, sign up for an API key at [Payman](https://paymanai.com).

3. Run the application:
```bash
cd src
streamlit run app.py
```

## Project Structure

- `src/`
  - `app.py`: Main Streamlit application
  - `database.py`: Database models and setup
  - `contest.py`: Contest management logic
  - `ocr.py`: Screenshot processing with GPT-4V
- `data/`
  - `screenshots/`: Storage for uploaded trade screenshots
- `tests/`: Unit tests

## Usage

1. Create a contest by setting a name and profit target
2. Share the join code with participants
3. Participants can join using the code
4. Upload screenshots of trades or enter them manually
5. Track progress on the real-time leaderboard

## Development

The project uses SQLite for data storage and OpenAI's GPT-4V for OCR processing of trade screenshots.