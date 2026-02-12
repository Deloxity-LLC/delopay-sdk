param(
  [string]$BaseUrl = "",
  [string]$ApiKey = "",
  [int]$Iterations = 5,
  [int]$IntervalSeconds = 15,
  [int]$TimeoutSeconds = 20,
  [double]$Max4xxRate = 0.0,
  [double]$Max5xxRate = 0.0
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

if ($Iterations -lt 1) {
  throw "Iterations must be >= 1."
}
if ($IntervalSeconds -lt 0) {
  throw "IntervalSeconds must be >= 0."
}

$normalizedBaseUrl = $BaseUrl.TrimEnd("/")
$samples = [System.Collections.Generic.List[object]]::new()

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

function Invoke-CanaryRequest {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Method,
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [hashtable]$Query = $null,
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
  return [pscustomobject]@{
    Uri = $uri
    Status = [int]$response.StatusCode
  }
}

$checks = @(
  [pscustomobject]@{
    Name = "providers-list"
    Method = "GET"
    Path = "/api/providers"
    Query = $null
    UseAuth = $false
  },
  [pscustomobject]@{
    Name = "stripe-payment-methods"
    Method = "GET"
    Path = "/api/providers/stripe/payment-methods"
    Query = @{
      merchantCountry = "DE"
      customerCountry = "DE"
      currency = "EUR"
    }
    UseAuth = $true
  }
)

for ($iteration = 1; $iteration -le $Iterations; $iteration++) {
  foreach ($check in $checks) {
    $requestUri = New-RequestUri -Path $check.Path -Query $check.Query
    try {
      $response = Invoke-CanaryRequest `
        -Method $check.Method `
        -Path $check.Path `
        -Query $check.Query `
        -UseAuth $check.UseAuth

      $status = [int]$response.Status
      $category = if ($status -ge 500) {
        "5xx"
      } elseif ($status -ge 400) {
        "4xx"
      } elseif ($status -ge 200 -and $status -lt 300) {
        "2xx"
      } else {
        "other"
      }

      $samples.Add([pscustomobject]@{
          Iteration = $iteration
          Check = $check.Name
          Status = $status
          Category = $category
          Uri = $response.Uri
          Error = ""
        })
    } catch {
      $samples.Add([pscustomobject]@{
          Iteration = $iteration
          Check = $check.Name
          Status = 0
          Category = "network"
          Uri = $requestUri
          Error = $_.Exception.Message
        })
    }
  }

  if ($iteration -lt $Iterations -and $IntervalSeconds -gt 0) {
    Start-Sleep -Seconds $IntervalSeconds
  }
}

$total = $samples.Count
$count2xx = ($samples | Where-Object { $_.Category -eq "2xx" }).Count
$count4xx = ($samples | Where-Object { $_.Category -eq "4xx" }).Count
$count5xx = ($samples | Where-Object { $_.Category -eq "5xx" }).Count
$countNetwork = ($samples | Where-Object { $_.Category -eq "network" }).Count
$countOther = ($samples | Where-Object { $_.Category -eq "other" }).Count

$rate4xx = if ($total -gt 0) { [double]$count4xx / [double]$total } else { 0.0 }
$rate5xx = if ($total -gt 0) { [double]$count5xx / [double]$total } else { 0.0 }

Write-Host ""
$samples | Select-Object Iteration, Check, Status, Category | Format-Table -AutoSize | Out-String | Write-Host
Write-Host ("Summary: total={0}, 2xx={1}, 4xx={2}, 5xx={3}, network={4}, other={5}" -f $total, $count2xx, $count4xx, $count5xx, $countNetwork, $countOther)
Write-Host ("Rates: 4xx={0:P2}, 5xx={1:P2}" -f $rate4xx, $rate5xx)

if ($countNetwork -gt 0) {
  throw "Canary failed: network errors detected ($countNetwork)."
}
if ($countOther -gt 0) {
  throw "Canary failed: unexpected non-2xx/4xx/5xx statuses detected ($countOther)."
}
if ($rate5xx -gt $Max5xxRate) {
  throw ("Canary failed: 5xx rate {0:P2} exceeded threshold {1:P2}." -f $rate5xx, $Max5xxRate)
}
if ($rate4xx -gt $Max4xxRate) {
  throw ("Canary failed: 4xx rate {0:P2} exceeded threshold {1:P2}." -f $rate4xx, $Max4xxRate)
}

Write-Host "Canary checks passed against $normalizedBaseUrl."
