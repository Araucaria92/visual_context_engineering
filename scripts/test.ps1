param(
  [string]$Endpoint = "http://localhost:11434/v1/chat/completions",
  [string]$Model = "gpt-oss:20b",
  [string]$AuthHeader = "Authorization: Bearer ollama",
  [switch]$Send
)

Write-Host "Analyzing prompts..." -ForegroundColor Cyan
uv run vcer analyze --in examples/system.md --user examples/user.md --out parts.json

Write-Host "Routing test to $Endpoint" -ForegroundColor Cyan
if ($Send) {
  & $PSScriptRoot/run.ps1 -Endpoint $Endpoint -Model $Model -AuthHeader $AuthHeader -Send
} else {
  & $PSScriptRoot/run.ps1 -Endpoint $Endpoint -Model $Model -AuthHeader $AuthHeader
}
