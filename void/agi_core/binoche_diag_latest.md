# Binoche_Observer Diagnostic Report (2025-11-03T09:48:44.007121Z)

- server: http://127.0.0.1:8091
- health: ok
- queue_size: None
- inflight: 0
- results_count: 26

## quick look
- issues: worker_absent

## proposed fixes (Binoche_Observer)
- 워커가 보이지 않습니다. 백그라운드 워커를 시작하세요.

## processes: worker
```

```

## processes: server
```

```

## netstat 8091
```
LocalAddress LocalPort       State OwningProcess

------------ ---------       ----- -------------

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091 Established         40720

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091 Established         40720

127.0.0.1         8091 Established         40720

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091 Established         40720

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091    FinWait2         40720

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091    FinWait2         40720

127.0.0.1         8091 Established         40720

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091    TimeWait             0

127.0.0.1         8091      Listen         40720
```