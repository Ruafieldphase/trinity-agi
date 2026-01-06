# Task Queue Priority Test Script
# Tests the new priority queue functionality

param(
    [string]$Server = "http://127.0.0.1:8091"
)

$ErrorActionPreference = "Stop"

$ServerUrl = $Server

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-TaskQueuePriority {
    Write-ColorOutput "`n=== Task Queue Priority Test ===" "Cyan"
    Write-ColorOutput "Server: $ServerUrl`n" "Gray"

    # 1. Health Check
    Write-ColorOutput "1. Health Check..." "Yellow"
    try {
        $health = Invoke-RestMethod -Uri "$ServerUrl/api/health" -Method Get -TimeoutSec 5
        Write-ColorOutput "   ✓ Server online" "Green"
        Write-ColorOutput "   Queue sizes: Urgent=$($health.queue_urgent), Normal=$($health.queue_normal), Low=$($health.queue_low)" "Gray"
    }
    catch {
        Write-ColorOutput "   ✗ Server offline. Start with: Task Queue Server (Fresh)" "Red"
        return $false
    }

    # 1.5. Pre-clean any residual inflight/pending tasks
    Write-ColorOutput "`n1.5. Draining any residual tasks..." "Yellow"
    try {
        for ($attempt = 0; $attempt -lt 5; $attempt++) {
            $inflight = Invoke-RestMethod -Uri "$ServerUrl/api/inflight" -Method Get -TimeoutSec 5
            if ($inflight.count -gt 0) {
                foreach ($it in $inflight.inflight) {
                    $drain = @{ success = $true; data = @{ drained = $true } } | ConvertTo-Json
                    Invoke-RestMethod -Uri "$ServerUrl/api/tasks/$($it.task_id)/result" -Method Post -Body $drain -ContentType "application/json" -TimeoutSec 5 | Out-Null
                }
            }
            # Drain pending by fetching until none
            $fetchedAny = $false
            for ($i = 0; $i -lt 10; $i++) {
                Start-Sleep -Milliseconds 100
                $n = Invoke-RestMethod -Uri "$ServerUrl/api/tasks/next" -Method Post -TimeoutSec 5 -Headers @{ 'X-Worker-Name' = 'priority-test-drain' }
                $obj = $null
                if ($null -ne $n.task) { $obj = $n.task }
                elseif ($null -ne $n.task_id) { $obj = $n }
                if ($null -eq $obj) { break }
                $fetchedAny = $true
                $drain = @{ success = $true; data = @{ drained = $true } } | ConvertTo-Json
                Invoke-RestMethod -Uri "$ServerUrl/api/tasks/$($obj.task_id)/result" -Method Post -Body $drain -ContentType "application/json" -TimeoutSec 5 | Out-Null
            }
            if (-not $fetchedAny -and $inflight.count -eq 0) { break }
        }
    }
    catch { Write-ColorOutput "   (Drain step skipped due to transient error)" "DarkGray" }

    # 2. Create tasks with different priorities
    Write-ColorOutput "`n2. Creating tasks with priorities..." "Yellow"
    
    $tasks = @()
    
    # Create low priority task first
    Write-ColorOutput "   Creating LOW priority task..." "Gray"
    $lowTask = @{
        type = "test"
        data = @{ message = "Low priority task" }
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ServerUrl/api/tasks/create?priority=low" `
        -Method Post -Body $lowTask -ContentType "application/json"
    $tasks += @{ id = $response.task_id; priority = "low"; order = 1 }
    Write-ColorOutput "   ✓ Created: $($response.task_id) (priority: low)" "Green"

    # Create normal priority task
    Write-ColorOutput "   Creating NORMAL priority task..." "Gray"
    $normalTask = @{
        type = "test"
        data = @{ message = "Normal priority task" }
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ServerUrl/api/tasks/create?priority=normal" `
        -Method Post -Body $normalTask -ContentType "application/json"
    $tasks += @{ id = $response.task_id; priority = "normal"; order = 2 }
    Write-ColorOutput "   ✓ Created: $($response.task_id) (priority: normal)" "Green"

    # Create urgent priority task last
    Write-ColorOutput "   Creating URGENT priority task..." "Gray"
    $urgentTask = @{
        type = "test"
        data = @{ message = "Urgent priority task" }
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ServerUrl/api/tasks/create?priority=urgent" `
        -Method Post -Body $urgentTask -ContentType "application/json"
    $tasks += @{ id = $response.task_id; priority = "urgent"; order = 3 }
    Write-ColorOutput "   ✓ Created: $($response.task_id) (priority: urgent)" "Green"

    # 3. Check queue stats
    Write-ColorOutput "`n3. Checking queue stats..." "Yellow"
    $stats = Invoke-RestMethod -Uri "$ServerUrl/api/stats" -Method Get
    Write-ColorOutput "   Total pending: $($stats.pending)" "Gray"
    Write-ColorOutput "   Urgent: $($stats.pending_urgent)" "Gray"
    Write-ColorOutput "   Normal: $($stats.pending_normal)" "Gray"
    Write-ColorOutput "   Low: $($stats.pending_low)" "Gray"

    if ($stats.pending -ne 3) {
        Write-ColorOutput "   ✗ Expected 3 pending tasks, got $($stats.pending)" "Red"
        return $false
    }
    Write-ColorOutput "   ✓ Queue contains 3 tasks" "Green"

    # 4. Verify priority order by fetching tasks
    Write-ColorOutput "`n4. Verifying priority order (should be: urgent → normal → low)..." "Yellow"
    
    $expectedOrder = @("urgent", "normal", "low")
    $actualOrder = @()
    
    for ($i = 0; $i -lt 3; $i++) {
        Start-Sleep -Milliseconds 150  # mitigate server flakiness under rapid calls
        $nextTask = Invoke-RestMethod -Uri "$ServerUrl/api/tasks/next" -Method Post -TimeoutSec 5 -Headers @{ 'X-Worker-Name' = 'priority-test' }

        # Server may return either { task: <obj>|$null } or the task object directly
        $taskObj = $null
        if ($null -ne $nextTask.task) {
            $taskObj = $nextTask.task
        }
        elseif ($null -ne $nextTask.task_id) {
            $taskObj = $nextTask
        }

        if ($null -ne $taskObj) {
            $prio = $taskObj.priority
            $actualOrder += $prio
            Write-ColorOutput "   Fetched #$($i+1): $($taskObj.task_id) (priority: $prio)" "Gray"

            # Submit result immediately to clear inflight
            $result = @{
                success = $true
                data    = @{ test = "priority order verification" }
            } | ConvertTo-Json
            Invoke-RestMethod -Uri "$ServerUrl/api/tasks/$($taskObj.task_id)/result" `
                -Method Post -Body $result -ContentType "application/json" -TimeoutSec 5 | Out-Null
            Start-Sleep -Milliseconds 120
        }
    }

    # Verify order
    $orderCorrect = $true
    for ($i = 0; $i -lt 3; $i++) {
        if ($actualOrder[$i] -ne $expectedOrder[$i]) {
            Write-ColorOutput "   ✗ Order mismatch at position $($i+1): expected '$($expectedOrder[$i])', got '$($actualOrder[$i])'" "Red"
            $orderCorrect = $false
        }
    }

    if ($orderCorrect) {
        Write-ColorOutput "   ✓ Priority order correct! (urgent → normal → low)" "Green"
    }
    else {
        Write-ColorOutput "   ✗ Priority order incorrect!" "Red"
        return $false
    }

    # 5. Test invalid priority (should default to normal)
    Write-ColorOutput "`n5. Testing invalid priority handling..." "Yellow"
    $invalidTask = @{
        type = "test"
        data = @{ message = "Invalid priority test" }
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ServerUrl/api/tasks/create?priority=invalid" `
        -Method Post -Body $invalidTask -ContentType "application/json"
    
    if ($response.priority -eq "normal") {
        Write-ColorOutput "   ✓ Invalid priority correctly defaulted to 'normal'" "Green"
    }
    else {
        Write-ColorOutput "   ✗ Invalid priority handling failed" "Red"
        return $false
    }

    # Clean up
    $cleanTask = Invoke-RestMethod -Uri "$ServerUrl/api/tasks/next" -Method Post
    if ($cleanTask.task) {
        $result = @{ success = $true } | ConvertTo-Json
        Invoke-RestMethod -Uri "$ServerUrl/api/tasks/$($cleanTask.task.task_id)/result" `
            -Method Post -Body $result -ContentType "application/json" | Out-Null
    }

    # 6. Test /api/enqueue compatibility endpoint with priority
    Write-ColorOutput "`n6. Testing /api/enqueue compatibility with priority..." "Yellow"
    $compatTask = @{
        task_type = "compat_test"
        params    = @{ message = "Compatibility test" }
        priority  = "urgent"
    } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "$ServerUrl/api/enqueue" `
        -Method Post -Body $compatTask -ContentType "application/json"
    
    if ($response.priority -eq "urgent") {
        Write-ColorOutput "   ✓ /api/enqueue correctly handles priority parameter" "Green"
    }
    else {
        Write-ColorOutput "   ✗ /api/enqueue priority handling failed" "Red"
        return $false
    }

    # Clean up
    $cleanTask = Invoke-RestMethod -Uri "$ServerUrl/api/tasks/next" -Method Post
    if ($cleanTask.task) {
        $result = @{ success = $true } | ConvertTo-Json
        Invoke-RestMethod -Uri "$ServerUrl/api/tasks/$($cleanTask.task.task_id)/result" `
            -Method Post -Body $result -ContentType "application/json" | Out-Null
    }

    Write-ColorOutput "`n=== All Tests Passed! ===" "Green"
    Write-ColorOutput "Priority queue functionality working correctly ✓" "Green"
    return $true
}

# Run test
$success = Test-TaskQueuePriority

if ($success) {
    Write-ColorOutput "`n✅ Priority Queue Test: PASS" "Green"
    exit 0
}
else {
    Write-ColorOutput "`n❌ Priority Queue Test: FAIL" "Red"
    exit 1
}