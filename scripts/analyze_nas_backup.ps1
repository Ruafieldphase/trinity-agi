#Requires -Version 5.1
<#
.SYNOPSIS
    D:\nas_backup Complete Structure and Content Analysis
.DESCRIPTION
    Performs comprehensive analysis including directory structure, file statistics,
    document classification, and code analysis to generate a complete knowledge map.
#>

[CmdletBinding()]
param(
    [string]$SourcePath = "D:\nas_backup",
    [string]$OutputPath = "C:\workspace\agi\outputs",
    [switch]$SkipLargeFiles,
    [int]$MaxDepth = 10
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

# Create output directory
$analysisDir = Join-Path $OutputPath "nas_backup_analysis"
if (-not (Test-Path $analysisDir)) {
    New-Item -ItemType Directory -Path $analysisDir -Force | Out-Null
}

Write-Host "[INFO] Starting comprehensive analysis of D:\nas_backup..." -ForegroundColor Cyan
Write-Host "       Output path: $analysisDir" -ForegroundColor Gray

# =============================================================================
# 1. 디렉터리 구조 매핑
# =============================================================================
Write-Host "`n📁 [1/8] 디렉터리 구조 매핑 중..." -ForegroundColor Yellow

$dirStructure = @()
$dirStats = @{}

Get-ChildItem -Path $SourcePath -Recurse -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $dir = $_
    $depth = ($dir.FullName -replace [regex]::Escape($SourcePath), "").Split('\').Count - 1
    
    if ($depth -le $MaxDepth) {
        $files = Get-ChildItem -Path $dir.FullName -File -ErrorAction SilentlyContinue
        $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
        
        $dirStats[$dir.FullName] = @{
            Path         = $dir.FullName
            RelativePath = $dir.FullName -replace [regex]::Escape($SourcePath), ""
            FileCount    = $files.Count
            TotalSize    = $totalSize
            Depth        = $depth
            LastModified = $dir.LastWriteTime
        }
        
        $dirStructure += [PSCustomObject]@{
            Path     = $dir.FullName -replace [regex]::Escape($SourcePath), ""
            Depth    = $depth
            Files    = $files.Count
            SizeMB   = [math]::Round($totalSize / 1MB, 2)
            Modified = $dir.LastWriteTime.ToString("yyyy-MM-dd")
        }
    }
}

$dirStructure | Export-Csv -Path (Join-Path $analysisDir "directory_structure.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 디렉터리 구조 저장됨: directory_structure.csv" -ForegroundColor Green

# =============================================================================
# 2. 파일 분류 및 통계
# =============================================================================
Write-Host "`n📊 [2/8] 파일 분류 및 통계 생성 중..." -ForegroundColor Yellow

$allFiles = Get-ChildItem -Path $SourcePath -Recurse -File -ErrorAction SilentlyContinue
Write-Host "   총 파일 수: $($allFiles.Count)" -ForegroundColor Gray

# 확장자별 통계
$extensionStats = $allFiles | Group-Object Extension | ForEach-Object {
    $ext = if ($_.Name) { $_.Name } else { "(no extension)" }
    $files = $_.Group
    $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
    
    [PSCustomObject]@{
        Extension     = $ext
        Count         = $files.Count
        TotalSizeMB   = [math]::Round($totalSize / 1MB, 2)
        AvgSizeMB     = [math]::Round(($totalSize / $files.Count) / 1MB, 4)
        LargestFileMB = [math]::Round(($files | Sort-Object Length -Descending | Select-Object -First 1).Length / 1MB, 2)
    }
} | Sort-Object TotalSizeMB -Descending

$extensionStats | Export-Csv -Path (Join-Path $analysisDir "file_extensions_stats.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 확장자별 통계 저장됨: file_extensions_stats.csv" -ForegroundColor Green

# 크기별 분포
$sizeDistribution = @{
    "< 1KB" = 0; "1KB-10KB" = 0; "10KB-100KB" = 0
    "100KB-1MB" = 0; "1MB-10MB" = 0; "10MB-100MB" = 0; "> 100MB" = 0
}

$allFiles | ForEach-Object {
    $sizeMB = $_.Length / 1MB
    if ($sizeMB -lt 0.001) { $sizeDistribution["< 1KB"]++ }
    elseif ($sizeMB -lt 0.01) { $sizeDistribution["1KB-10KB"]++ }
    elseif ($sizeMB -lt 0.1) { $sizeDistribution["10KB-100KB"]++ }
    elseif ($sizeMB -lt 1) { $sizeDistribution["100KB-1MB"]++ }
    elseif ($sizeMB -lt 10) { $sizeDistribution["1MB-10MB"]++ }
    elseif ($sizeMB -lt 100) { $sizeDistribution["10MB-100MB"]++ }
    else { $sizeDistribution["> 100MB"]++ }
}

$sizeDistribution.GetEnumerator() | ForEach-Object {
    [PSCustomObject]@{ Range = $_.Key; Count = $_.Value }
} | Export-Csv -Path (Join-Path $analysisDir "file_size_distribution.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 크기 분포 저장됨: file_size_distribution.csv" -ForegroundColor Green

# 대용량 파일 (>10MB)
$largeFiles = $allFiles | Where-Object { $_.Length -gt 10MB } | ForEach-Object {
    [PSCustomObject]@{
        Path      = $_.FullName -replace [regex]::Escape($SourcePath), ""
        SizeMB    = [math]::Round($_.Length / 1MB, 2)
        Extension = $_.Extension
        Modified  = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm")
    }
} | Sort-Object SizeMB -Descending

$largeFiles | Export-Csv -Path (Join-Path $analysisDir "large_files.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 대용량 파일 목록 저장됨: large_files.csv ($($largeFiles.Count) files)" -ForegroundColor Green

# =============================================================================
# 3. 문서 인벤토리
# =============================================================================
Write-Host "`n📝 [3/8] 문서 인벤토리 작성 중..." -ForegroundColor Yellow

$docExtensions = @('.md', '.txt', '.pdf', '.docx', '.doc')
$documents = $allFiles | Where-Object { $docExtensions -contains $_.Extension } | ForEach-Object {
    $content = ""
    if ($_.Extension -eq '.md' -or $_.Extension -eq '.txt') {
        try {
            # 첫 20줄만 읽어서 제목/요약 추출
            $content = (Get-Content $_.FullName -Head 20 -ErrorAction SilentlyContinue) -join " "
            $content = $content -replace '\s+', ' '
            if ($content.Length -gt 200) { $content = $content.Substring(0, 200) + "..." }
        }
        catch {}
    }
    
    [PSCustomObject]@{
        Path      = $_.FullName -replace [regex]::Escape($SourcePath), ""
        FileName  = $_.Name
        Extension = $_.Extension
        SizeKB    = [math]::Round($_.Length / 1KB, 2)
        Modified  = $_.LastWriteTime.ToString("yyyy-MM-dd")
        Preview   = $content
        Category  = switch -Regex ($_.Name) {
            'AGI|agi' { 'AGI' }
            'BQI|bqi' { 'BQI' }
            'PHASE|phase' { 'Phase Planning' }
            'portfolio' { 'Portfolio' }
            'lubit|Lubit' { 'Lubit' }
            'lumen|Lumen' { 'Lumen' }
            'README' { 'Documentation' }
            'REPORT|report' { 'Report' }
            'GUIDE|guide' { 'Guide' }
            default { 'General' }
        }
    }
}

$documents | Export-Csv -Path (Join-Path $analysisDir "document_inventory.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 문서 목록 저장됨: document_inventory.csv ($($documents.Count) documents)" -ForegroundColor Green

# 카테고리별 문서 수
$docCategories = $documents | Group-Object Category | ForEach-Object {
    [PSCustomObject]@{ Category = $_.Name; Count = $_.Count }
} | Sort-Object Count -Descending
$docCategories | Export-Csv -Path (Join-Path $analysisDir "document_categories.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 카테고리별 통계 저장됨: document_categories.csv" -ForegroundColor Green

# =============================================================================
# 4. 스크립트 및 자동화
# =============================================================================
Write-Host "`n🔧 [4/8] 스크립트 분석 중..." -ForegroundColor Yellow

$scriptExtensions = @('.ps1', '.py', '.sh', '.bat', '.cmd')
$scripts = $allFiles | Where-Object { $scriptExtensions -contains $_.Extension } | ForEach-Object {
    $imports = @()
    $functions = @()
    
    if ($_.Extension -eq '.py') {
        try {
            $content = Get-Content $_.FullName -ErrorAction SilentlyContinue
            $imports = ($content | Select-String -Pattern '^\s*(import|from)\s+(\S+)' -AllMatches).Matches | 
            ForEach-Object { $_.Groups[2].Value } | Select-Object -Unique
            $functions = ($content | Select-String -Pattern '^\s*def\s+(\w+)' -AllMatches).Matches | 
            ForEach-Object { $_.Groups[1].Value }
        }
        catch {}
    }
    elseif ($_.Extension -eq '.ps1') {
        try {
            $content = Get-Content $_.FullName -ErrorAction SilentlyContinue
            $functions = ($content | Select-String -Pattern '^\s*function\s+(\S+)' -AllMatches).Matches | 
            ForEach-Object { $_.Groups[1].Value }
        }
        catch {}
    }
    
    [PSCustomObject]@{
        Path          = $_.FullName -replace [regex]::Escape($SourcePath), ""
        FileName      = $_.Name
        Type          = $_.Extension
        SizeKB        = [math]::Round($_.Length / 1KB, 2)
        Modified      = $_.LastWriteTime.ToString("yyyy-MM-dd")
        FunctionCount = $functions.Count
        ImportCount   = $imports.Count
        Functions     = ($functions | Select-Object -First 5) -join ', '
        Imports       = ($imports | Select-Object -First 5) -join ', '
    }
}

$scripts | Export-Csv -Path (Join-Path $analysisDir "script_inventory.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 스크립트 목록 저장됨: script_inventory.csv ($($scripts.Count) scripts)" -ForegroundColor Green

# =============================================================================
# 5. 데이터 자산 분석
# =============================================================================
Write-Host "`n💾 [5/8] 데이터 자산 분석 중..." -ForegroundColor Yellow

$dataExtensions = @('.json', '.jsonl', '.csv', '.xml', '.yaml', '.yml', '.db', '.sqlite')
$dataFiles = $allFiles | Where-Object { $dataExtensions -contains $_.Extension } | ForEach-Object {
    $lineCount = 0
    if ($_.Extension -eq '.jsonl' -or $_.Extension -eq '.csv' -or $_.Extension -eq '.txt') {
        try {
            $lineCount = (Get-Content $_.FullName -ErrorAction SilentlyContinue).Count
        }
        catch {}
    }
    
    [PSCustomObject]@{
        Path      = $_.FullName -replace [regex]::Escape($SourcePath), ""
        FileName  = $_.Name
        Format    = $_.Extension
        SizeMB    = [math]::Round($_.Length / 1MB, 2)
        LineCount = $lineCount
        Modified  = $_.LastWriteTime.ToString("yyyy-MM-dd")
        Location  = switch -Regex ($_.DirectoryName) {
            'outputs' { 'Outputs' }
            'memory' { 'Memory' }
            'knowledge_base' { 'Knowledge Base' }
            'config' { 'Config' }
            default { 'Other' }
        }
    }
}

$dataFiles | Export-Csv -Path (Join-Path $analysisDir "data_assets.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 데이터 자산 목록 저장됨: data_assets.csv ($($dataFiles.Count) files)" -ForegroundColor Green

# =============================================================================
# 6. 설정 파일 분석
# =============================================================================
Write-Host "`n⚙️ [6/8] 설정 파일 분석 중..." -ForegroundColor Yellow

$configExtensions = @('.yaml', '.yml', '.json', '.toml', '.ini', '.conf', '.config')
$configFiles = $allFiles | Where-Object { 
    ($configExtensions -contains $_.Extension) -and 
    ($_.DirectoryName -match 'config|conf|settings|\.vscode')
} | ForEach-Object {
    [PSCustomObject]@{
        Path     = $_.FullName -replace [regex]::Escape($SourcePath), ""
        FileName = $_.Name
        Type     = $_.Extension
        SizeKB   = [math]::Round($_.Length / 1KB, 2)
        Modified = $_.LastWriteTime.ToString("yyyy-MM-dd")
        Purpose  = switch -Regex ($_.Name) {
            'persona' { 'Persona Configuration' }
            'phase.*controller' { 'Phase Controller' }
            'orchestrat' { 'Orchestration' }
            'task' { 'Task Configuration' }
            'settings' { 'Settings' }
            default { 'Configuration' }
        }
    }
}

$configFiles | Export-Csv -Path (Join-Path $analysisDir "config_files.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 설정 파일 목록 저장됨: config_files.csv ($($configFiles.Count) files)" -ForegroundColor Green

# =============================================================================
# 7. Python 코드베이스 분석
# =============================================================================
Write-Host "`n🧩 [7/8] Python 코드베이스 분석 중..." -ForegroundColor Yellow

$pythonFiles = $allFiles | Where-Object { $_.Extension -eq '.py' }
$pythonModules = @()

foreach ($pyFile in $pythonFiles) {
    try {
        $content = Get-Content $pyFile.FullName -ErrorAction SilentlyContinue
        $classes = ($content | Select-String -Pattern '^\s*class\s+(\w+)' -AllMatches).Matches | 
        ForEach-Object { $_.Groups[1].Value }
        $functions = ($content | Select-String -Pattern '^\s*def\s+(\w+)' -AllMatches).Matches | 
        ForEach-Object { $_.Groups[1].Value }
        $imports = ($content | Select-String -Pattern '^\s*(import|from)\s+(\S+)' -AllMatches).Matches | 
        ForEach-Object { $_.Groups[2].Value } | Select-Object -Unique
        
        $pythonModules += [PSCustomObject]@{
            Path          = $pyFile.FullName -replace [regex]::Escape($SourcePath), ""
            FileName      = $pyFile.Name
            ClassCount    = $classes.Count
            FunctionCount = $functions.Count
            ImportCount   = $imports.Count
            LOC           = $content.Count
            Modified      = $pyFile.LastWriteTime.ToString("yyyy-MM-dd")
            Classes       = ($classes | Select-Object -First 3) -join ', '
            TopFunctions  = ($functions | Select-Object -First 3) -join ', '
        }
    }
    catch {}
}

$pythonModules | Export-Csv -Path (Join-Path $analysisDir "python_modules.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ Python 모듈 분석 저장됨: python_modules.csv ($($pythonModules.Count) modules)" -ForegroundColor Green

# =============================================================================
# 8. 시계열 분석
# =============================================================================
Write-Host "`n📈 [8/8] 시계열 분석 중..." -ForegroundColor Yellow

$timeline = $allFiles | ForEach-Object {
    [PSCustomObject]@{
        Date      = $_.LastWriteTime.ToString("yyyy-MM-dd")
        Month     = $_.LastWriteTime.ToString("yyyy-MM")
        FileName  = $_.Name
        Extension = $_.Extension
        SizeMB    = [math]::Round($_.Length / 1MB, 2)
        Path      = ($_.FullName -replace [regex]::Escape($SourcePath), "").Split([char]0x5C)[0]
    }
} | Group-Object Date | ForEach-Object {
    [PSCustomObject]@{
        Date         = $_.Name
        FileCount    = $_.Count
        TotalSizeMB  = [math]::Round(($_.Group | Measure-Object -Property SizeMB -Sum).Sum, 2)
        TopExtension = ($_.Group | Group-Object Extension | Sort-Object Count -Descending | Select-Object -First 1).Name
    }
} | Sort-Object Date

$timeline | Export-Csv -Path (Join-Path $analysisDir "timeline.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 타임라인 저장됨: timeline.csv" -ForegroundColor Green

# 월별 활동
$monthlyActivity = $allFiles | ForEach-Object {
    [PSCustomObject]@{
        Month  = $_.LastWriteTime.ToString("yyyy-MM")
        Files  = 1
        SizeMB = $_.Length / 1MB
    }
} | Group-Object Month | ForEach-Object {
    [PSCustomObject]@{
        Month       = $_.Name
        FileCount   = $_.Count
        TotalSizeMB = [math]::Round(($_.Group | Measure-Object -Property SizeMB -Sum).Sum, 2)
    }
} | Sort-Object Month

$monthlyActivity | Export-Csv -Path (Join-Path $analysisDir "monthly_activity.csv") -NoTypeInformation -Encoding UTF8
Write-Host "   ✓ 월별 활동 저장됨: monthly_activity.csv" -ForegroundColor Green

# =============================================================================
# 최종 요약
# =============================================================================
Write-Host "`n✨ 분석 완료!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$summary = @{
    TotalFiles        = $allFiles.Count
    TotalDirectories  = $dirStructure.Count
    TotalSizeGB       = [math]::Round(($allFiles | Measure-Object -Property Length -Sum).Sum / 1GB, 2)
    Documents         = $documents.Count
    Scripts           = $scripts.Count
    DataFiles         = $dataFiles.Count
    ConfigFiles       = $configFiles.Count
    PythonModules     = $pythonModules.Count
    UniqueExtensions  = ($extensionStats | Measure-Object).Count
    AnalysisTimestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
}

$summary | ConvertTo-Json | Out-File (Join-Path $analysisDir "summary.json") -Encoding UTF8

Write-Host "`n📊 전체 요약:" -ForegroundColor Cyan
Write-Host "   총 파일: $($summary.TotalFiles)" -ForegroundColor White
Write-Host "   총 디렉터리: $($summary.TotalDirectories)" -ForegroundColor White
Write-Host "   총 크기: $($summary.TotalSizeGB) GB" -ForegroundColor White
Write-Host "   문서: $($summary.Documents)" -ForegroundColor White
Write-Host "   스크립트: $($summary.Scripts)" -ForegroundColor White
Write-Host "   데이터 파일: $($summary.DataFiles)" -ForegroundColor White
Write-Host "   설정 파일: $($summary.ConfigFiles)" -ForegroundColor White
Write-Host "   Python 모듈: $($summary.PythonModules)" -ForegroundColor White

Write-Host "`n📁 결과 파일 위치: $analysisDir" -ForegroundColor Yellow
Write-Host "   - directory_structure.csv" -ForegroundColor Gray
Write-Host "   - file_extensions_stats.csv" -ForegroundColor Gray
Write-Host "   - file_size_distribution.csv" -ForegroundColor Gray
Write-Host "   - large_files.csv" -ForegroundColor Gray
Write-Host "   - document_inventory.csv" -ForegroundColor Gray
Write-Host "   - script_inventory.csv" -ForegroundColor Gray
Write-Host "   - data_assets.csv" -ForegroundColor Gray
Write-Host "   - config_files.csv" -ForegroundColor Gray
Write-Host "   - python_modules.csv" -ForegroundColor Gray
Write-Host "   - timeline.csv" -ForegroundColor Gray
Write-Host "   - monthly_activity.csv" -ForegroundColor Gray
Write-Host "   - summary.json" -ForegroundColor Gray

Write-Host "`n✅ 다음 단계: KNOWLEDGE_MAP.md 생성 스크립트 실행" -ForegroundColor Green
