$ErrorActionPreference = "Stop"

if (-not (Test-Path Cert:\CurrentUser\My)) {
    throw "Certificate provider is unavailable: Cert:\CurrentUser\My"
}

$c = "CrossHud_Permanent_Cert"
$f = "dist\CrossHud\CrossHud.exe"
$e = "dist\CrossHudCert.cer"

if (-not (Test-Path $f)) {
    throw "Executable not found: $f"
}

$s = Get-ChildItem Cert:\CurrentUser\My | Where-Object { $_.Subject -match $c } | Select-Object -First 1
if (-not $s) {
    $s = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=$c" -CertStoreLocation Cert:\CurrentUser\My -NotAfter (Get-Date).AddYears(100)
}

$r = New-Object System.Security.Cryptography.X509Certificates.X509Store "Root", "CurrentUser"
$r.Open("ReadWrite")
$r.Add($s)
$r.Close()

$p = New-Object System.Security.Cryptography.X509Certificates.X509Store "TrustedPublisher", "CurrentUser"
$p.Open("ReadWrite")
$p.Add($s)
$p.Close()

$signature = Set-AuthenticodeSignature -Certificate $s -FilePath $f -TimestampServer "http://timestamp.digicert.com"
if ($signature.Status -ne "Valid") {
    throw "Signing failed: $($signature.Status) $($signature.StatusMessage)"
}

$verify = Get-AuthenticodeSignature -FilePath $f
if ($verify.Status -ne "Valid") {
    throw "Signature verification failed: $($verify.Status) $($verify.StatusMessage)"
}

Export-Certificate -Cert $s -FilePath $e -Type CERT | Out-Null
if (-not (Test-Path $e)) {
    throw "Certificate export failed: $e"
}
