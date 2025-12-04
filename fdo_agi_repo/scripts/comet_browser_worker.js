/**
 * Comet Browser Worker Script
 * 
 * 이 스크립트를 Chrome DevTools Console에 붙여넣기하여 실행하세요.
 * API 서버가 http://localhost:8091에서 실행 중이어야 합니다.
 */

// 설정
const CONFIG = {
    apiBaseUrl: 'http://localhost:8091',
    workerId: 'comet-browser',
    pollInterval: 5000,  // 5초마다 체크
    maxRetries: 3
};

// 전역 상태
let isRunning = false;
let processingTaskId = null;
let stats = {
    processed: 0,
    succeeded: 0,
    failed: 0,
    startTime: null
};

/**
 * 웹 스크래핑 시뮬레이션
 */
async function simulateWebScraping(taskData) {
    const url = taskData.url || 'https://example.com';
    const selector = taskData.selector || 'body';

    console.log(`[Comet] Scraping ${url} with selector: ${selector}`);

    // 실제로는 여기서 DOM 조작이나 fetch를 사용할 수 있습니다
    // 지금은 시뮬레이션만 수행
    await new Promise(resolve => setTimeout(resolve, 2000));

    return {
        url: url,
        selector: selector,
        content: `Scraped content from ${url}`,
        timestamp: new Date().toISOString(),
        length: Math.floor(Math.random() * 1000) + 100
    };
}

/**
 * 다음 작업 가져오기
 */
async function getNextTask() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/api/tasks/next`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                worker_id: CONFIG.workerId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data.task;
    } catch (error) {
        console.error('[Comet] Failed to get task:', error.message);
        return null;
    }
}

/**
 * 작업 결과 제출
 */
async function submitResult(taskId, status, resultData, errorMessage = null) {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/api/tasks/${taskId}/result`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                worker_id: CONFIG.workerId,
                status: status,
                data: resultData,
                error_message: errorMessage
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log(`[Comet] Result submitted for task ${taskId}:`, data.message);
        return true;
    } catch (error) {
        console.error('[Comet] Failed to submit result:', error.message);
        return false;
    }
}

/**
 * 작업 처리
 */
async function processTask(task) {
    const taskId = task.id;
    const taskType = task.type;
    const taskData = task.data;

    console.log(`[Comet] Processing task ${taskId} (${taskType})...`);
    processingTaskId = taskId;

    try {
        let result;

        switch (taskType) {
            case 'web_scraping':
                result = await simulateWebScraping(taskData);
                break;

            case 'ping':
                result = {
                    message: 'pong',
                    worker: CONFIG.workerId,
                    timestamp: new Date().toISOString()
                };
                break;

            default:
                throw new Error(`Unknown task type: ${taskType}`);
        }

        // 결과 제출
        const success = await submitResult(taskId, 'success', result);

        if (success) {
            stats.succeeded++;
            console.log(`[Comet] ✅ Task ${taskId} completed successfully`);
        } else {
            stats.failed++;
            console.log(`[Comet] ⚠️ Task ${taskId} completed but failed to submit result`);
        }

    } catch (error) {
        console.error(`[Comet] ❌ Task ${taskId} failed:`, error.message);
        await submitResult(taskId, 'failed', {}, error.message);
        stats.failed++;
    } finally {
        processingTaskId = null;
        stats.processed++;
    }
}

/**
 * 워커 루프
 */
async function workerLoop() {
    while (isRunning) {
        try {
            const task = await getNextTask();

            if (task) {
                await processTask(task);
            } else {
                // 대기 중인 작업이 없으면 잠시 대기
                console.log('[Comet] No tasks available, waiting...');
                await new Promise(resolve => setTimeout(resolve, CONFIG.pollInterval));
            }
        } catch (error) {
            console.error('[Comet] Worker loop error:', error.message);
            await new Promise(resolve => setTimeout(resolve, CONFIG.pollInterval));
        }
    }
}

/**
 * 워커 시작
 */
function startWorker() {
    if (isRunning) {
        console.log('[Comet] Worker is already running');
        return;
    }

    console.log('='.repeat(60));
    console.log('Comet Browser Worker Starting');
    console.log('='.repeat(60));
    console.log(`Worker ID: ${CONFIG.workerId}`);
    console.log(`API Server: ${CONFIG.apiBaseUrl}`);
    console.log(`Poll Interval: ${CONFIG.pollInterval}ms`);
    console.log('='.repeat(60));

    isRunning = true;
    stats.startTime = new Date();
    stats.processed = 0;
    stats.succeeded = 0;
    stats.failed = 0;

    workerLoop();

    console.log('[Comet] ✅ Worker started successfully');
    console.log('[Comet] Use stopWorker() to stop, showStats() to see statistics');
}

/**
 * 워커 중지
 */
function stopWorker() {
    if (!isRunning) {
        console.log('[Comet] Worker is not running');
        return;
    }

    isRunning = false;
    console.log('[Comet] ⏹️ Worker stopped');
    showStats();
}

/**
 * 통계 표시
 */
function showStats() {
    const runtime = stats.startTime
        ? Math.floor((new Date() - stats.startTime) / 1000)
        : 0;

    console.log('='.repeat(60));
    console.log('Comet Worker Statistics');
    console.log('='.repeat(60));
    console.log(`Runtime: ${runtime}s`);
    console.log(`Total Processed: ${stats.processed}`);
    console.log(`  - Succeeded: ${stats.succeeded}`);
    console.log(`  - Failed: ${stats.failed}`);
    if (stats.processed > 0) {
        const successRate = ((stats.succeeded / stats.processed) * 100).toFixed(1);
        console.log(`Success Rate: ${successRate}%`);
    }
    console.log(`Currently Processing: ${processingTaskId || 'None'}`);
    console.log(`Worker Status: ${isRunning ? '🟢 Running' : '🔴 Stopped'}`);
    console.log('='.repeat(60));
}

/**
 * API 서버 연결 테스트
 */
async function testConnection() {
    console.log('[Comet] Testing API server connection...');

    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/health`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('[Comet] ✅ API server is healthy:', data);
        return true;
    } catch (error) {
        console.error('[Comet] ❌ API server connection failed:', error.message);
        console.error('[Comet] Make sure the server is running on', CONFIG.apiBaseUrl);
        return false;
    }
}

// 전역 스코프에 함수 노출
window.CometWorker = {
    start: startWorker,
    stop: stopWorker,
    stats: showStats,
    test: testConnection,
    config: CONFIG
};

console.log('='.repeat(60));
console.log('Comet Browser Worker Loaded');
console.log('='.repeat(60));
console.log('Available commands:');
console.log('  CometWorker.test()  - Test API server connection');
console.log('  CometWorker.start() - Start processing tasks');
console.log('  CometWorker.stop()  - Stop worker');
console.log('  CometWorker.stats() - Show statistics');
console.log('='.repeat(60));
console.log('');
console.log('Quick start:');
console.log('  1. CometWorker.test()   // API 서버 연결 확인');
console.log('  2. CometWorker.start()  // 워커 시작');
console.log('  3. CometWorker.stats()  // 통계 확인');
console.log('  4. CometWorker.stop()   // 워커 중지');
console.log('');
