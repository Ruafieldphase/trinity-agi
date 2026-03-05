# Slack Message Format (Alertmanager Slack Config)

Alertmanager `slack_configs` supports `title` and `text`.  
추천 포맷:
- `title`: `"[{severity}] {{ .CommonLabels.alertname }} ({{ .CommonLabels.domain }})"`
- `text`: 
  ```
  {{ range .Alerts -}}
  • *{{ .Labels.severity }}* {{ .Annotations.summary }}
    - {{ .Annotations.description }}
    - starts: {{ .StartsAt }}
  {{ end }}
  ```

> Alertmanager의 Slack "blocks"는 공식 템플릿 필드가 아니므로, 범용 호환을 위해 `title/text` 조합을 권장.
