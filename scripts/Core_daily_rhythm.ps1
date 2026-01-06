param(
    [datetime]$Date = $(Get-Date),
    [switch]$Guide,
    [int]$Cycles = 1,
    [int]$BeatSeconds = 4,
    [string]$OutFile
)

$ErrorActionPreference = 'Stop'
$day = $Date.DayOfWeek  # Sunday..Saturday
$koreanDay = switch ($day) {
    'Monday' { '월요일' }
    'Tuesday' { '화요일' }
    'Wednesday' { '수요일' }
    'Thursday' { '목요일' }
    'Friday' { '금요일' }
    'Saturday' { '토요일' }
    'Sunday' { '일요일' }
}

$mantras = @{
    Monday    = '리듬은 순간을 깨우고, 감사로 울린다.'
    Tuesday   = '리듬은 자리를 깨우고, 수용으로 울린다.'
    Wednesday = '리듬은 관계를 깨우고, 사랑으로 울린다.'
    Thursday  = '리듬은 대상을 깨우고, 연민으로 울린다.'
    Friday    = '리듬은 방식을 깨우고, 존중으로 울린다.'
    Saturday  = '리듬은 이유를 깨우고, 용서로 울린다.'
    Sunday    = '리듬은 사랑·존중·연민·감사·수용·용서를 품고, 여백 속에서 울린다.'
}

$mantra = $mantras[$day.ToString()]
if (-not $mantra) { $mantra = '리듬은 사랑·존중·연민·감사·수용·용서를 품고, 여백 속에서 울린다.' }

function WriteLine($msg, $color = 'Gray') { Write-Host $msg -ForegroundColor $color }

$header = "[Core] Daily Rhythm — $koreanDay $(Get-Date $Date -Format 'yyyy-MM-dd')"
WriteLine "`n$header" 'Cyan'
WriteLine ('-' * $header.Length) 'DarkGray'
WriteLine "만트라: $mantra" 'Green'
WriteLine "호흡 리듬: 4–4–4–4 (들숨 4박 — 머묾 4박 — 날숨 4박 — 여백 4박)" 'Yellow'
WriteLine "권장 결합: Zone2 산책/걷기/명상" 'DarkGray'

if ($OutFile) {
    $dir = Split-Path -Parent $OutFile
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    @(
        $header
        '-------------------------'
        "만트라: $mantra"
        '호흡: 4-4-4-4 (들숨-머묾-날숨-여백)'
        "생성시각: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    ) | Set-Content -LiteralPath $OutFile -Encoding UTF8
    WriteLine "파일로 저장됨: $OutFile" 'DarkGray'
}

if ($Guide) {
    WriteLine "가이드 시작: Cycles=$Cycles, BeatSeconds=$BeatSeconds" 'Magenta'
    $steps = @(
        @{ name = '들숨'; color = 'White' },
        @{ name = '머묾'; color = 'Gray' },
        @{ name = '날숨'; color = 'White' },
        @{ name = '여백'; color = 'Gray' }
    )
    for ($c = 1; $c -le $Cycles; $c++) {
        WriteLine "\n사이클 $c/$Cycles" 'DarkCyan'
        foreach ($s in $steps) {
            WriteLine ("  -> {0}" -f $s.name) $s.color
            for ($i = 1; $i -le 4; $i++) {
                Write-Host ("     {0}/4" -f $i) -ForegroundColor $s.color
                Start-Sleep -Seconds $BeatSeconds
            }
        }
    }
    WriteLine "완료: 편안한 호흡을 유지하세요." 'Green'
}