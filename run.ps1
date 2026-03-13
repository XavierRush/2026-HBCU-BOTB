$ErrorActionPreference = "Stop"

Write-Host "Installing dependencies..."
python -m pip install -r requirements.txt --quiet
python -m spacy download en_core_web_sm --quiet

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        $line = $_.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
            return
        }
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $name = $parts[0].Trim()
            $value = $parts[1].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

$debugEnabled = $env:DEBUG_MODE -eq "1" -or $env:DEBUG_MODE -eq "true" -or $env:DEBUG_MODE -eq "TRUE"

if ($debugEnabled) {
    Write-Host "Debug mode enabled. Starting without Claude API access."
}
else {
    Write-Host "Checking API key..."
    if ([string]::IsNullOrWhiteSpace($env:ANTHROPIC_API_KEY)) {
        Write-Host "ERROR: ANTHROPIC_API_KEY environment variable not set."
        Write-Host "Set it in .env (copy .env.example) or in your shell env."
        Write-Host "You can also start in debug mode with: `$env:DEBUG_MODE='1'; .\run.ps1"
        exit 1
    }
}

Write-Host "Starting AI Visibility Analyzer..."
python -m streamlit run dashboard/app.py --server.port 8501
