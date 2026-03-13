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

if [ "$DEBUG_MODE" = "1" ] || [ "$DEBUG_MODE" = "true" ] || [ "$DEBUG_MODE" = "TRUE" ]; then
  echo "Debug mode enabled. Starting without Claude API access."
else
  echo "Checking API key..."
  if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable not set."
    echo "Set it in .env (copy .env.example) or export it in your shell."
    echo "You can also start in debug mode with: DEBUG_MODE=1 ./run.sh"
    exit 1
  fi
fi

echo "Starting AI Visibility Analyzer..."
streamlit run dashboard/app.py --server.port 8501
