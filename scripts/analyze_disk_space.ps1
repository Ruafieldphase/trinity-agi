# 디스크 공간 분석 스크립트
# 워크스페이스의 폴더 크기와 큰 파일을 분석합니다

param(
    [string]$RootPath = "D:\",
    [int]$TopFolders = 20,
    [int]$TopFiles = 20,
    [int]$MinFileSizeMB = 100,
    [string]$OutputReport = "disk_space_report.txt"
)

Write-Host "=== 디스크 공간 분석 시작 ===" -ForegroundColor Cyan
Write-Host "분석 경로: $RootPath" -ForegroundColor Yellow
Write-Host ""

# 1. 전체 드라이브 상태
Write-Host "1. 드라이브 상태" -ForegroundColor Green
$drive = Get-PSDrive D
$usedGB = [math]::Round($drive.Used / 1GB, 2)
$freeGB = [math]::Round($drive.Free / 1GB, 2)
$totalGB = $usedGB + $freeGB
$usedPercent = [math]::Round(($usedGB / $totalGB) * 100, 1)

Write-Host "   사용 중: $usedGB GB ($usedPercent%)" -ForegroundColor Yellow
Write-Host "   남은 공간: $freeGB GB" -ForegroundColor Green
Write-Host "   전체 용량: $totalGB GB" -ForegroundColor Cyan
Write-Host ""

# 2. 최상위 폴더별 크기 분석
Write-Host "2. 최상위 폴더 크기 분석 (상위 $TopFolders 개)" -ForegroundColor Green
Write-Host "   분석 중... (시간이 소요될 수 있습니다)" -ForegroundColor Gray

$folderSizes = Get-ChildItem $RootPath -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $folder = $_
    Write-Progress -Activity "폴더 크기 계산 중" -Status $folder.Name
    
    try {
        $size = (Get-ChildItem $folder.FullName -Recurse -File -ErrorAction SilentlyContinue | 
            Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
        
        [PSCustomObject]@{
            Folder = $folder.Name
            Path   = $folder.FullName
            SizeGB = [math]::Round($size / 1GB, 2)
            SizeMB = [math]::Round($size / 1MB, 2)
            Files  = (Get-ChildItem $folder.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
        }
    }
    catch {
        [PSCustomObject]@{
            Folder = $folder.Name
            Path   = $folder.FullName
            SizeGB = 0
            SizeMB = 0
            Files  = 0
        }
    }
}

Write-Progress -Activity "폴더 크기 계산 중" -Completed

$topFolders = $folderSizes | Sort-Object SizeGB -Descending | Select-Object -First $TopFolders
$topFolders | Format-Table -AutoSize

# 3. 큰 파일 찾기
Write-Host "3. 큰 파일 분석 (${MinFileSizeMB}MB 이상, 상위 $TopFiles 개)" -ForegroundColor Green
Write-Host "   검색 중... (시간이 소요될 수 있습니다)" -ForegroundColor Gray

$largeFiles = Get-ChildItem $RootPath -Recurse -File -ErrorAction SilentlyContinue | 
Where-Object { $_.Length -gt ($MinFileSizeMB * 1MB) } | 
Sort-Object Length -Descending | 
Select-Object -First $TopFiles |
Select-Object FullName, 
@{N = 'SizeGB'; E = { [math]::Round($_.Length / 1GB, 2) } },
@{N = 'SizeMB'; E = { [math]::Round($_.Length / 1MB, 2) } },
LastWriteTime

$largeFiles | Format-Table -AutoSize

# 4. 파일 타입별 통계
Write-Host "4. 주요 파일 타입별 공간 사용" -ForegroundColor Green

$fileTypes = Get-ChildItem $RootPath -Recurse -File -ErrorAction SilentlyContinue | 
Group-Object Extension | 
ForEach-Object {
    $totalSize = ($_.Group | Measure-Object -Property Length -Sum).Sum
    [PSCustomObject]@{
        Extension = if ($_.Name) { $_.Name } else { "(확장자 없음)" }
        Count     = $_.Count
        TotalGB   = [math]::Round($totalSize / 1GB, 2)
        TotalMB   = [math]::Round($totalSize / 1MB, 2)
    }
} | Sort-Object TotalGB -Descending | Select-Object -First 15

$fileTypes | Format-Table -AutoSize

# 5. 잠재적 정리 대상 식별
Write-Host "5. 잠재적 정리 대상" -ForegroundColor Green

$cleanupTargets = @()

# node_modules 폴더
$nodeModules = Get-ChildItem $RootPath -Recurse -Directory -Filter "node_modules" -ErrorAction SilentlyContinue | 
Select-Object -First 10 |
ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | 
        Measure-Object -Property Length -Sum).Sum
    [PSCustomObject]@{
        Type   = "node_modules"
        Path   = $_.FullName
        SizeMB = [math]::Round($size / 1MB, 2)
    }
}

# __pycache__ 폴더
$pycache = Get-ChildItem $RootPath -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | 
Select-Object -First 10 |
ForEach-Object {
    $size = (Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | 
        Measure-Object -Property Length -Sum).Sum
    [PSCustomObject]@{
        Type   = "__pycache__"
        Path   = $_.FullName
        SizeMB = [math]::Round($size / 1MB, 2)
    }
}

# .log 파일
$logFiles = Get-ChildItem $RootPath -Recurse -File -Filter "*.log" -ErrorAction SilentlyContinue | 
Where-Object { $_.Length -gt 10MB } |
Select-Object -First 10 |
ForEach-Object {
    [PSCustomObject]@{
        Type   = "log 파일"
        Path   = $_.FullName
        SizeMB = [math]::Round($_.Length / 1MB, 2)
    }
}

$cleanupTargets = @($nodeModules) + @($pycache) + @($logFiles)
$cleanupTargets | Sort-Object SizeMB -Descending | Format-Table -AutoSize

# 6. 보고서 저장
Write-Host ""
Write-Host "=== 보고서 저장 중 ===" -ForegroundColor Cyan

$reportPath = Join-Path $RootPath $OutputReport
$report = @"
디스크 공간 분석 보고서
생성 시간: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
분석 경로: $RootPath

=== 1. 드라이브 상태 ===
사용 중: $usedGB GB ($usedPercent%)
남은 공간: $freeGB GB
전체 용량: $totalGB GB

=== 2. 최상위 폴더 크기 (상위 $TopFolders) ===
$($topFolders | Format-Table -AutoSize | Out-String)

=== 3. 큰 파일 (${MinFileSizeMB}MB 이상, 상위 $TopFiles) ===
$($largeFiles | Format-Table -AutoSize | Out-String)

=== 4. 파일 타입별 공간 사용 (상위 15) ===
$($fileTypes | Format-Table -AutoSize | Out-String)

=== 5. 잠재적 정리 대상 ===
$($cleanupTargets | Sort-Object SizeMB -Descending | Format-Table -AutoSize | Out-String)

=== 권장 조치 ===
1. node_modules 폴더: 사용하지 않는 프로젝트의 node_modules는 삭제 가능 (npm install로 복구 가능)
2. __pycache__ 폴더: 안전하게 삭제 가능 (Python이 자동으로 재생성)
3. 큰 로그 파일: 오래된 로그는 압축 또는 삭제
4. 중복 백업: backup 폴더 내 중복 파일 검토
5. 빌드 산출물: dist/, build/ 폴더는 재빌드 가능하므로 삭제 고려

=== 다음 단계 ===
1. 위 정리 대상을 검토하고 불필요한 파일 삭제
2. 중요 데이터는 클라우드 또는 외부 백업
3. 정기적인 디스크 정리 스케줄 설정 (예: 월 1회)

"@

$report | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "보고서 저장 완료: $reportPath" -ForegroundColor Green
Write-Host ""

# 7. 요약
Write-Host "=== 분석 완료 ===" -ForegroundColor Cyan
Write-Host "총 분석 폴더 수: $($folderSizes.Count)" -ForegroundColor Yellow
Write-Host "총 큰 파일 수: $($largeFiles.Count)" -ForegroundColor Yellow
Write-Host "잠재적 정리 대상: $($cleanupTargets.Count)개 항목" -ForegroundColor Yellow
Write-Host ""
Write-Host "상세 보고서: $reportPath" -ForegroundColor Green
