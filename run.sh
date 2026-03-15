#!/bin/bash

set -e

echo "Installing dependencies..."
pip install -r requirements.txt --quiet
python3 -m spacy download en_core_web_sm --quiet

if [ -f ".env" ]; then
  set -a
  . ./.env
  set +a
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "No ANTHROPIC_API_KEY found; running in debug/mock mode."
  export DEBUG_MODE=1
fi

if [ "$DEBUG_MODE" = "1" ] || [ "$DEBUG_MODE" = "true" ] || [ "$DEBUG_MODE" = "TRUE" ]; then
  echo "Debug mode enabled. Starting without Claude API access."
else
  echo "Using Claude API with provided key."
fi

echo "Starting AI Visibility Analyzer..."
streamlit run dashboard/app.py --server.port 8501
