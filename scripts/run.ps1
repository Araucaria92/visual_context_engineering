param(
  [Parameter(Mandatory=$true)][string]$Endpoint,
  [string]$Model = "gpt-oss:20b",
  [string]$AuthHeader = "Authorization: Bearer ollama",
  [switch]$Send
)

Write-Host "Routing to $Endpoint with model $Model" -ForegroundColor Cyan
$flags = @()
if ($Send) { $flags += "--send" }
uv run vcer route `
  --backend openai `
  --endpoint $Endpoint `
  --model $Model `
  --header $AuthHeader `
  --system examples/system.md `
  --user examples/user.md `
  @flags

