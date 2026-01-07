# Regenerate fc_scores_quartiles.csv for all datasets with new per-metric format
# Run this after updating generate_vegalite_plots.py

Write-Host "=" * 80
Write-Host "REGENERATING FC SCORE QUARTILES FOR ALL DATASETS"
Write-Host "=" * 80
Write-Host ""

# Get all dataset directories from data/ folder
$dataFolders = Get-ChildItem "data" -Directory

$datasets = @()
foreach ($folder in $dataFolders) {
    # Get all JSON files in each data folder (each file is a dataset)
    $jsonFiles = Get-ChildItem -Path $folder.FullName -Filter "*.json"
    foreach ($file in $jsonFiles) {
        # Extract dataset name from filename (remove .json extension)
        $datasetName = $file.BaseName
        $datasets += $datasetName
    }
}

Write-Host "Found $($datasets.Count) datasets to process"
Write-Host ""

$successful = 0
$failed = 0
$startTime = Get-Date

foreach ($i in 0..($datasets.Count - 1)) {
    $dataset = $datasets[$i]
    $num = $i + 1
    
    Write-Host "[$num/$($datasets.Count)] Processing: $dataset"
    
    try {
        # Run generate_vegalite_plots.py with --csv-only flag
        python generate_vegalite_plots.py --dataset $dataset --csv-only 2>&1 | Out-Null
        
        # Check if quartile file was created
        $quartileFile = "plots/$dataset/ranking/fc_scores_quartiles.csv"
        if (Test-Path $quartileFile) {
            # Verify it has the correct format (should have multiple rows, not just 3)
            $content = Get-Content $quartileFile
            if ($content.Count -gt 10) {  # Should have ~23 rows + header
                Write-Host "  ✅ Success ($($content.Count - 1) metrics)" -ForegroundColor Green
                $successful++
            } else {
                Write-Host "  ⚠️  Warning: Only $($content.Count - 1) rows (expected ~23)" -ForegroundColor Yellow
                $successful++
            }
        } else {
            Write-Host "  ❌ Failed: Quartile file not created" -ForegroundColor Red
            $failed++
        }
    }
    catch {
        Write-Host "  ❌ Error: $_" -ForegroundColor Red
        $failed++
    }
    
    # Progress update every 10 datasets
    if ($num % 10 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        $avgTimePerDataset = $elapsed.TotalSeconds / $num
        $remaining = ($datasets.Count - $num) * $avgTimePerDataset
        Write-Host ""
        Write-Host "  Progress: $num/$($datasets.Count) completed"
        Write-Host "  Elapsed: $([math]::Round($elapsed.TotalMinutes, 1)) minutes"
        Write-Host "  Estimated remaining: $([math]::Round($remaining / 60, 1)) minutes"
        Write-Host ""
    }
}

$endTime = Get-Date
$totalTime = $endTime - $startTime

Write-Host ""
Write-Host "=" * 80
Write-Host "REGENERATION COMPLETE"
Write-Host "=" * 80
Write-Host "Successful: $successful" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "Total time: $([math]::Round($totalTime.TotalMinutes, 1)) minutes"
Write-Host "=" * 80
