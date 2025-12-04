import json

# Load steps
with open('outputs/steps/3c-iBn73dDE_steps.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    steps = data['steps']

# Filter Docker/Install related steps
docker_steps = [
    s for s in steps 
    if 'docker' in s['description'].lower() 
    or 'install' in s['description'].lower()
]

print(f'\n🐳 Docker/Install related steps: {len(docker_steps)}/{len(steps)}\n')
print('='*70)

# Show first 10 Docker-related steps
for s in docker_steps[:10]:
    print(f"\nStep {s['order']}: {s['action'].upper()}")
    if s.get('target'):
        print(f"  Target: {s['target']}")
    print(f"  Time: {s['timestamp']:.1f}s ({s['timestamp']//60:.0f}m {s['timestamp']%60:.0f}s)")
    print(f"  Confidence: {s['confidence']:.2f}")
    desc = s['description'][:100] + '...' if len(s['description']) > 100 else s['description']
    print(f"  Description: {desc}")

print('\n' + '='*70)
print(f'\n✅ Total steps extracted: {len(steps)}')
print(f'🎯 Docker-related steps: {len(docker_steps)}')
