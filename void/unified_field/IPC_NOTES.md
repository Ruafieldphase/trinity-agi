# IPC Notes (v1.6)
- Future option: adapter/enricher communicate via Unix domain socket at /data/lumen_v16.sock
- Helm mounts /data from PVC or emptyDir; processes can share the socket path if scheduled on same pod (sidecar pattern) or same node with hostPath (not default).
- For now, CSV/JSON files remain the contract.
