# Batch process all 80 precomputed datasets
# Generates 2 plots per metric (z-score + ranking) without --breakdown flag
# Use --csv-only flag to regenerate only CSV files (quartiles and rankings)

param(
    [switch]$CsvOnly
)

$datasets = Get-ChildItem -Path "precomputed" -Directory | Select-Object -ExpandProperty Name | Sort-Object

$modeText = if ($CsvOnly) { "CSV-ONLY mode" } else { "full plot generation" }
Write-Host "🚀 Processing $($datasets.Count) datasets ($modeText)..." -ForegroundColor Cyan
Write-Host ""

$success = 0
$failed = @()
$startTime = Get-Date

foreach ($dataset in $datasets) {
    Write-Host "[$($success + $failed.Count + 1)/$($datasets.Count)] Processing: $dataset" -ForegroundColor Yellow
    
    $command = if ($CsvOnly) {
        "python generate_vegalite_plots.py --dataset $dataset --csv-only"
    } else {
        "python generate_vegalite_plots.py --dataset $dataset"
    }
    
    Invoke-Expression $command | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $success++
        Write-Host "  ✅ Success" -ForegroundColor Green
    } else {
        $failed += $dataset
        Write-Host "  ❌ Failed" -ForegroundColor Red
    }
    
    # Progress update every 10 datasets
    if (($success + $failed.Count) % 10 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        $avgTime = $elapsed.TotalSeconds / ($success + $failed.Count)
        $remaining = ($datasets.Count - ($success + $failed.Count)) * $avgTime / 60
        Write-Host "  ⏱️  Elapsed: $([math]::Round($elapsed.TotalMinutes, 1))min | Est. remaining: $([math]::Round($remaining, 1))min" -ForegroundColor Cyan
    }
    
    Write-Host ""
}

$totalTime = (Get-Date) - $startTime

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "COMPLETE: $success succeeded, $($failed.Count) failed" -ForegroundColor Cyan
Write-Host "Total time: $([math]::Round($totalTime.TotalMinutes, 1)) minutes" -ForegroundColor Cyan
if ($failed.Count -gt 0) {
    Write-Host "Failed datasets:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}
Write-Host "=" * 80 -ForegroundColor Cyan
