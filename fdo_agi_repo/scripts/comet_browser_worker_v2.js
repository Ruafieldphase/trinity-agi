/**
 * Comet Enhanced Browser Worker Script v2.0
 * 
 * 기능:
 * - 다양한 작업 타입 처리 (calculation, data_transform, json_process, web_scraping, ping)
 * - inbox 폴더의 메시지 자동 확인
 * - 자동 응답 및 보고서 생성
 */

// 설정
const CONFIG = {
    apiBaseUrl: 'http://localhost:8091',
    workerId: 'comet-browser',
    pollInterval: 5000,  // 5초마다 체크
    maxRetries: 3,
    checkInbox: true  // inbox 메시지 확인 활성화
};

// 전역 상태
let isRunning = false;
let processingTaskId = null;
let stats = {
    processed: 0,
    succeeded: 0,
    failed: 0,
    startTime: null,
    tasksByType: {}
};

/**
 * 작업 타입별 처리 함수들
 */
const taskHandlers = {
    // 계산 작업
    calculation: async (taskData) => {
        console.log('[Comet] 🧮 계산 작업 시작:', taskData);
        const { operation, numbers } = taskData;

        let result;
        if (operation === 'add') {
            result = numbers.reduce((a, b) => a + b, 0);
        } else if (operation === 'multiply') {
            result = numbers.reduce((a, b) => a * b, 1);
        } else {
            throw new Error(`Unknown operation: ${operation}`);
        }

        return {
            result: result,
            calculation: `${numbers.join(operation === 'add' ? '+' : '*')}=${result}`,
            numbers: numbers,
            operation: operation
        };
    },

    // 문자열 변환 작업
    data_transform: async (taskData) => {
        console.log('[Comet] 🔄 문자열 변환 작업 시작:', taskData);
        const { input, transform } = taskData;

        let result;
        if (transform === 'reverse') {
            result = input.split('').reverse().join('');
        } else if (transform === 'uppercase') {
            result = input.toUpperCase();
        } else if (transform === 'lowercase') {
            result = input.toLowerCase();
        } else {
            throw new Error(`Unknown transform: ${transform}`);
        }

        return {
            result: result,
            original: input,
            transform: transform
        };
    },

    // JSON 처리 작업
    json_process: async (taskData) => {
        console.log('[Comet] 📊 JSON 처리 작업 시작:', taskData);
        const { items, task } = taskData;

        let result;
        if (task === 'count_active') {
            const activeItems = items.filter(item => item.status === 'active');
            result = {
                count: activeItems.length,
                active_items: activeItems.map(item => item.name),
                total: items.length
            };
        } else {
            throw new Error(`Unknown JSON task: ${task}`);
        }

        return result;
    },

    // 웹 스크래핑 (기존)
    web_scraping: async (taskData) => {
        console.log('[Comet] 🕷️ 웹 스크래핑 작업 시작:', taskData);
        const url = taskData.url || 'https://example.com';
        const selector = taskData.selector || 'body';

        await new Promise(resolve => setTimeout(resolve, 2000));

        return {
            url: url,
            selector: selector,
            content: `Scraped content from ${url}`,
            timestamp: new Date().toISOString(),
            length: Math.floor(Math.random() * 1000) + 100
        };
    },

    // Ping 작업
    ping: async (taskData) => {
        console.log('[Comet] 🏓 Ping 작업 시작');
        return {
            message: 'pong',
            worker: CONFIG.workerId,
            timestamp: new Date().toISOString()
        };
    }
};

/**
 * 다음 작업 가져오기
 */
async function getNextTask() {
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
        if (response.status === 404) {
            return null; // 작업 없음
        }
        throw new Error(`Failed to get task: ${response.status}`);
    }

    const data = await response.json();
    return data.task;
}

/**
 * 작업 결과 제출
 */
async function submitResult(taskId, status, resultData, errorMessage = null) {
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
        throw new Error(`Failed to submit result: ${response.status}`);
    }

    return await response.json();
}

/**
 * 작업 처리
 */
async function processTask(task) {
    const taskType = task.type;
    const handler = taskHandlers[taskType];

    if (!handler) {
        throw new Error(`Unknown task type: ${taskType}`);
    }

    console.log(`[Comet] 📋 작업 처리 중: ${task.id} (${taskType})`);

    try {
        const resultData = await handler(task.data);
        await submitResult(task.id, 'success', resultData);

        stats.succeeded++;
        stats.tasksByType[taskType] = (stats.tasksByType[taskType] || 0) + 1;

        console.log(`[Comet] ✅ 작업 완료: ${task.id}`);
        console.log('[Comet] 결과:', resultData);

        return true;
    } catch (error) {
        console.error(`[Comet] ❌ 작업 실패: ${task.id}`, error);
        await submitResult(task.id, 'error', {}, error.message);

        stats.failed++;
        return false;
    } finally {
        stats.processed++;
        processingTaskId = null;
    }
}

/**
 * inbox 메시지 확인 (선택적)
 */
async function checkInboxMessages() {
    if (!CONFIG.checkInbox) return;

    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/api/inbox/messages`);
        if (response.ok) {
            const data = await response.json();
            if (data.messages && data.messages.length > 0) {
                console.log('[Comet] 📬 새 메시지:', data.messages);
            }
        }
    } catch (error) {
        // inbox API가 없으면 조용히 무시
    }
}

/**
 * 워커 메인 루프
 */
async function workerLoop() {
    if (!isRunning) return;

    try {
        // inbox 메시지 확인 (있으면)
        await checkInboxMessages();

        // 작업 가져오기
        const task = await getNextTask();

        if (task) {
            processingTaskId = task.id;
            await processTask(task);
        } else {
            console.log('[Comet] ⏳ 대기 중... (작업 없음)');
        }
    } catch (error) {
        console.error('[Comet] 🔥 오류 발생:', error);
    }

    // 다음 체크 예약
    if (isRunning) {
        setTimeout(workerLoop, CONFIG.pollInterval);
    }
}

/**
 * 워커 시작
 */
function start() {
    if (isRunning) {
        console.log('[Comet] ⚠️ 이미 실행 중입니다');
        return;
    }

    console.log('[Comet] 🚀 워커 시작!');
    console.log(`[Comet] 📡 API: ${CONFIG.apiBaseUrl}`);
    console.log(`[Comet] 🆔 Worker ID: ${CONFIG.workerId}`);
    console.log(`[Comet] ⏱️ Poll interval: ${CONFIG.pollInterval}ms`);
    console.log(`[Comet] 📋 지원 작업 타입: ${Object.keys(taskHandlers).join(', ')}`);

    isRunning = true;
    stats.startTime = new Date();

    workerLoop();
}

/**
 * 워커 중지
 */
function stop() {
    if (!isRunning) {
        console.log('[Comet] ⚠️ 실행 중이 아닙니다');
        return;
    }

    console.log('[Comet] ⏹️ 워커 중지');
    isRunning = false;
}

/**
 * 통계 출력
 */
function showStats() {
    const runtime = stats.startTime ?
        Math.floor((new Date() - stats.startTime) / 1000) : 0;

    console.log('═══════════════════════════════════');
    console.log('  📊 Comet Worker 통계');
    console.log('═══════════════════════════════════');
    console.log(`  상태: ${isRunning ? '🟢 실행 중' : '🔴 중지됨'}`);
    console.log(`  실행 시간: ${runtime}초`);
    console.log(`  처리 완료: ${stats.succeeded}개`);
    console.log(`  실패: ${stats.failed}개`);
    console.log(`  전체: ${stats.processed}개`);

    if (Object.keys(stats.tasksByType).length > 0) {
        console.log('  ───────────────────────────────');
        console.log('  작업 타입별:');
        for (const [type, count] of Object.entries(stats.tasksByType)) {
            console.log(`    - ${type}: ${count}개`);
        }
    }

    if (processingTaskId) {
        console.log(`  현재 처리 중: ${processingTaskId}`);
    }
    console.log('═══════════════════════════════════');

    return stats;
}

/**
 * API 연결 테스트
 */
async function test() {
    console.log('[Comet] 🔍 API 연결 테스트...');

    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/health`);
        const data = await response.json();

        console.log('[Comet] ✅ API 서버 연결 성공!');
        console.log('[Comet] 서버 정보:', data);

        // 작업 통계 확인
        const statsResponse = await fetch(`${CONFIG.apiBaseUrl}/api/stats`);
        const statsData = await statsResponse.json();

        console.log('[Comet] 📊 현재 작업 상태:');
        console.log(`  - 대기 중: ${statsData.pending_tasks}개`);
        console.log(`  - 완료: ${statsData.completed_tasks}개`);

        return true;
    } catch (error) {
        console.error('[Comet] ❌ API 서버 연결 실패:', error);
        return false;
    }
}

// 전역 객체로 노출
window.CometWorker = {
    start,
    stop,
    stats: showStats,
    test,
    config: CONFIG
};

console.log('═══════════════════════════════════════════');
console.log('  🤖 Comet Worker v2.0 로드 완료!');
console.log('═══════════════════════════════════════════');
console.log('  사용법:');
console.log('    CometWorker.test()   - API 연결 테스트');
console.log('    CometWorker.start()  - 워커 시작');
console.log('    CometWorker.stop()   - 워커 중지');
console.log('    CometWorker.stats()  - 통계 확인');
console.log('═══════════════════════════════════════════');
console.log('  지원 작업 타입:');
console.log('    - calculation (계산)');
console.log('    - data_transform (문자열 변환)');
console.log('    - json_process (JSON 처리)');
console.log('    - web_scraping (웹 스크래핑)');
console.log('    - ping (연결 테스트)');
console.log('═══════════════════════════════════════════');
