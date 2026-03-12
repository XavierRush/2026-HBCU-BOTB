$ErrorActionPreference = "Stop"

Write-Host "Installing dependencies..."
python -m pip install -r requirements.txt --quiet
python -m spacy download en_core_web_sm --quiet

$debugEnabled = $env:DEBUG_MODE -eq "1" -or $env:DEBUG_MODE -eq "true" -or $env:DEBUG_MODE -eq "TRUE"

if ($debugEnabled) {
    Write-Host "Debug mode enabled. Starting without Claude API access."
}
else {
    Write-Host "Checking API key..."
    if ([string]::IsNullOrWhiteSpace($env:ANTHROPIC_API_KEY)) {
        Write-Host "ERROR: ANTHROPIC_API_KEY environment variable not set."
        Write-Host "Run with a key, or start in debug mode with: `$env:DEBUG_MODE='1'; .\run.ps1"
        exit 1
    }
}

Write-Host "Starting AI Visibility Analyzer..."
python -m streamlit run dashboard/app.py --server.port 8501
