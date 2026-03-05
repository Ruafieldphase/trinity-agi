# LUON Deploy — Docker & Ansible

## Docker Compose (quick start)
```bash
cd ops/docker
docker compose build
docker compose up -d
# Exporter on :9108, Scheduler following Day/Night policy
```

## Ansible (VM/server)
```bash
cd ops/ansible
ansible-playbook -i inventory.yml playbook.yml
# Edit inventory.yml (ansible_host) and group_vars.yml as needed
```

## Secrets
- Put Slack webhook etc. into `ops/secrets/.env.alerts` (never commit real secrets)
- For Alertmanager, render env vars into `ops/monitoring/alertmanager.yml`

## Hardening
See `ops/HARDENING_Checklist.md`
