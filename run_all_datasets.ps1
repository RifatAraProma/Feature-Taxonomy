# Batch process all 80 precomputed datasets
# Generates 2 plots per metric (z-score + ranking) without --breakdown flag

$datasets = Get-ChildItem -Path "precomputed" -Directory | Select-Object -ExpandProperty Name | Sort-Object

Write-Host "🚀 Processing $($datasets.Count) datasets..." -ForegroundColor Cyan
Write-Host ""

$success = 0
$failed = @()

foreach ($dataset in $datasets) {
    Write-Host "[$($success + $failed.Count + 1)/$($datasets.Count)] Processing: $dataset" -ForegroundColor Yellow
    
    python generate_vegalite_plots.py --dataset $dataset
    
    if ($LASTEXITCODE -eq 0) {
        $success++
        Write-Host "  ✅ Success" -ForegroundColor Green
    } else {
        $failed += $dataset
        Write-Host "  ❌ Failed" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "COMPLETE: $success succeeded, $($failed.Count) failed" -ForegroundColor Cyan
if ($failed.Count -gt 0) {
    Write-Host "Failed datasets:" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}
