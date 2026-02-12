param(
  [string]$BaseUrl = "",
  [string]$ApiKey = "",
  [int]$TimeoutSeconds = 20
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
  $BaseUrl = $env:DELOPAY_BASE_URL
}
if ([string]::IsNullOrWhiteSpace($BaseUrl)) {
  $BaseUrl = "https://sandbox-delopay.deloxity.com"
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  $ApiKey = $env:DELOPAY_API_KEY
}
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  $ApiKey = $env:DELOPAY_STAGING_API_KEY
}
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
  throw "Missing API key. Pass -ApiKey or set DELOPAY_API_KEY/DELOPAY_STAGING_API_KEY."
}

$normalizedBaseUrl = $BaseUrl.TrimEnd("/")
$results = [System.Collections.Generic.List[object]]::new()

function New-EncodedPathSegment {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Value
  )

  return [System.Uri]::EscapeDataString($Value)
}

function New-RequestUri {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [hashtable]$Query = $null
  )

  $uri = "$normalizedBaseUrl/$($Path.TrimStart('/'))"
  if ($null -eq $Query -or $Query.Count -eq 0) {
    return $uri
  }

  $queryParts = @()
  foreach ($key in $Query.Keys) {
    $encodedKey = [System.Uri]::EscapeDataString([string]$key)
    $encodedValue = [System.Uri]::EscapeDataString([string]$Query[$key])
    $queryParts += "$encodedKey=$encodedValue"
  }

  return "$uri?$($queryParts -join '&')"
}

function Invoke-SmokeCheck {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Name,
    [Parameter(Mandatory = $true)]
    [string]$Method,
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [hashtable]$Query = $null,
    [Parameter(Mandatory = $true)]
    [int[]]$ExpectedStatusCodes,
    [bool]$UseAuth = $true
  )

  $uri = New-RequestUri -Path $Path -Query $Query
  $headers = @{
    Accept = "application/json"
  }
  if ($UseAuth) {
    $headers.Authorization = "Bearer $ApiKey"
  }

  $requestArgs = @{
    Method = $Method
    Uri = $uri
    Headers = $headers
    TimeoutSec = $TimeoutSeconds
    SkipHttpErrorCheck = $true
  }

  $response = Invoke-WebRequest @requestArgs
  $status = [int]$response.StatusCode

  $results.Add([pscustomobject]@{
      Check = $Name
      Status = $status
      Method = $Method
      Uri = $uri
    })

  $bodyPreview = ""
  if (-not [string]::IsNullOrWhiteSpace($response.Content)) {
    $bodyPreview = $response.Content.Trim()
    if ($bodyPreview.Length -gt 220) {
      $bodyPreview = $bodyPreview.Substring(0, 220) + "..."
    }
  }

  if ($status -ge 500) {
    throw "Smoke check '$Name' failed with server error $status. Uri: $uri. Body: $bodyPreview"
  }

  if ($ExpectedStatusCodes -notcontains $status) {
    $expected = $ExpectedStatusCodes -join ", "
    throw "Smoke check '$Name' returned unexpected status $status (expected: $expected). Uri: $uri. Body: $bodyPreview"
  }
}

$encodedPaymentId = New-EncodedPathSegment -Value "pay smoke/test#id"
$encodedOrderId = New-EncodedPathSegment -Value "order#smoke/test"
$encodedProviderId = New-EncodedPathSegment -Value "provider/test#smoke"

Invoke-SmokeCheck `
  -Name "providers-list" `
  -Method "GET" `
  -Path "/api/providers" `
  -ExpectedStatusCodes @(200) `
  -UseAuth $false

Invoke-SmokeCheck `
  -Name "stripe-payment-methods" `
  -Method "GET" `
  -Path "/api/providers/stripe/payment-methods" `
  -Query @{
    merchantCountry = "DE"
    customerCountry = "DE"
    currency = "EUR"
  } `
  -ExpectedStatusCodes @(200)

Invoke-SmokeCheck `
  -Name "provider-config-special-chars" `
  -Method "GET" `
  -Path "/api/providers/$encodedProviderId/client-config" `
  -ExpectedStatusCodes @(200, 400, 401, 403, 404)

Invoke-SmokeCheck `
  -Name "payment-get-special-chars" `
  -Method "GET" `
  -Path "/api/payments/$encodedPaymentId" `
  -ExpectedStatusCodes @(200, 400, 401, 403, 404, 422)

Invoke-SmokeCheck `
  -Name "payment-by-order-special-chars" `
  -Method "GET" `
  -Path "/api/payments/by-order/$encodedOrderId" `
  -ExpectedStatusCodes @(200, 400, 401, 403, 404, 422)

Write-Host ""
$results | Format-Table -AutoSize | Out-String | Write-Host
Write-Host "Smoke checks passed against $normalizedBaseUrl."
