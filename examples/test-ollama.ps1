param(
  [string]$Backend = "local-ollama-openai",
  [switch]$Send
)

Write-Host "Analyzing prompts..." -ForegroundColor Cyan
uv run vcer analyze --in examples/system.md --user examples/user.md --out parts.json

Write-Host "Visualizing to prompt.mmd..." -ForegroundColor Cyan
uv run vcer visualize --parts parts.json --out prompt.mmd

Write-Host "Optimizing system prompt..." -ForegroundColor Cyan
uv run vcer optimize --parts parts.json --out system.opt.md

Write-Host "Routing to backend: $Backend" -ForegroundColor Cyan
$flags = @()
if ($Send) { $flags += "--send" }
uv run vcer route --system system.opt.md --user examples/user.md --backend $Backend @flags

