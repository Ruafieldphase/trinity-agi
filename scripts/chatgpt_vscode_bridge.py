#!/usr/bin/env python3
"""
ChatGPT ↔ VS Code Bridge
ADHD Meta-System: 대화 → 자동 구현

Author: Shion_Core (Lua + Binoche_Observer)
Date: 2025-11-06
Philosophy: Connectivity > Depth
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re

# OpenAI API (optional)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not installed. Using rule-based extraction.")


class ConversationBridge:
    """ChatGPT 대화를 VS Code 액션으로 변환"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.conversation_log = workspace_root / "outputs" / "chatgpt_conversations.jsonl"
        self.conversation_log.parent.mkdir(parents=True, exist_ok=True)
    
    def capture_conversation(self, conversation_id: str, messages: List[Dict]) -> Dict:
        """대화 캡처 및 저장"""
        conv = {
            "id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "extracted_intent": self.extract_intent(messages)
        }
        
        with open(self.conversation_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(conv, ensure_ascii=False) + '\n')
        
        print(f"✅ Conversation captured: {conversation_id}")
        print(f"   Intent: {conv['extracted_intent']['type']}")
        
        return conv
    
    def extract_intent(self, messages: List[Dict]) -> Dict:
        """대화에서 의도 추출"""
        # 마지막 사용자 메시지
        user_messages = [m for m in messages if m.get('role') == 'user']
        if not user_messages:
            return {'type': 'unknown', 'content': '', 'confidence': 0.0}
        
        last_user_msg = user_messages[-1]['content']
        
        # 의도 분류 (키워드 기반)
        intents = {
            'create_file': [
                '파일 만들어', '파일 생성', 'create file', 
                '스크립트 만들어', 'script', '.py', '.md'
            ],
            'modify_code': [
                '코드 수정', '바꿔줘', 'modify', '변경', 'change',
                '리팩토링', 'refactor'
            ],
            'create_system': [
                '시스템 만들어', '구조 설계', 'architecture', 
                '아키텍처', '설계', 'design'
            ],
            'connect_tools': [
                '연결해줘', '통합', 'integrate', 'connect',
                'bridge', '브릿지', '연동'
            ],
            'automate': [
                '자동화', 'automate', '순환', 'loop',
                '자동으로', 'automatic'
            ],
            'learn': [
                '학습', 'learn', '패턴', 'pattern',
                '체화', 'embody'
            ]
        }
        
        for intent_type, keywords in intents.items():
            if any(kw.lower() in last_user_msg.lower() for kw in keywords):
                return {
                    'type': intent_type,
                    'content': last_user_msg,
                    'confidence': 0.8,
                    'matched_keywords': [kw for kw in keywords if kw.lower() in last_user_msg.lower()]
                }
        
        return {
            'type': 'unknown',
            'content': last_user_msg,
            'confidence': 0.3
        }


class IntentToActionTranslator:
    """의도를 VS Code 액션으로 변환"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
    
    def translate(self, intent: Dict) -> Dict:
        """의도 → 액션"""
        translators = {
            'create_file': self.generate_create_file_action,
            'modify_code': self.generate_modify_code_action,
            'create_system': self.generate_create_system_action,
            'connect_tools': self.generate_connect_tools_action,
            'automate': self.generate_automate_action,
            'learn': self.generate_learn_action
        }
        
        translator = translators.get(intent['type'])
        if translator:
            action = translator(intent['content'])
            action['intent'] = intent
            return action
        
        return {
            'action': 'manual',
            'reason': f"Unknown intent: {intent['type']}",
            'intent': intent
        }
    
    def generate_create_file_action(self, content: str) -> Dict:
        """파일 생성 액션"""
        # 파일명 추출 (간단한 휴리스틱)
        file_path = self._extract_file_path(content)
        
        return {
            'action': 'create_file',
            'file_path': file_path,
            'content_prompt': content,
            'auto_execute': True,
            'reason': 'File creation intent detected'
        }
    
    def generate_modify_code_action(self, content: str) -> Dict:
        """코드 수정 액션"""
        return {
            'action': 'modify_code',
            'target_file': self._extract_file_path(content),
            'modification_prompt': content,
            'auto_execute': False,  # 수정은 확인 필요
            'reason': 'Code modification intent detected'
        }
    
    def generate_create_system_action(self, content: str) -> Dict:
        """시스템 생성 액션"""
        return {
            'action': 'create_system',
            'system_description': content,
            'auto_execute': True,
            'reason': 'System architecture intent detected'
        }
    
    def generate_connect_tools_action(self, content: str) -> Dict:
        """도구 연결 액션"""
        tools = self._extract_tool_names(content)
        
        return {
            'action': 'connect_tools',
            'tools': tools,
            'connection_prompt': content,
            'auto_execute': True,
            'reason': 'Tool integration intent detected'
        }
    
    def generate_automate_action(self, content: str) -> Dict:
        """자동화 액션"""
        return {
            'action': 'automate',
            'automation_prompt': content,
            'auto_execute': True,
            'reason': 'Automation intent detected'
        }
    
    def generate_learn_action(self, content: str) -> Dict:
        """학습 액션"""
        return {
            'action': 'learn',
            'learning_prompt': content,
            'auto_execute': True,
            'reason': 'Learning intent detected'
        }
    
    def _extract_file_path(self, content: str) -> str:
        """파일 경로 추출"""
        # .py, .md 등 확장자 패턴 찾기
        patterns = [
            r'[\w/\\]+\.py',
            r'[\w/\\]+\.md',
            r'[\w/\\]+\.json',
            r'[\w/\\]+\.txt'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0)
        
        # 기본값
        return 'outputs/auto_generated_file.py'
    
    def _extract_tool_names(self, content: str) -> List[str]:
        """도구 이름 추출"""
        tools = ['vscode', 'chatgpt', 'cursor', 'cloud', 'github', 'claude']
        found_tools = []
        
        for tool in tools:
            if tool.lower() in content.lower():
                found_tools.append(tool)
        
        return found_tools if found_tools else ['unknown']


class AutoExecutionEngine:
    """액션을 자동으로 실행"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.execution_log = workspace_root / "outputs" / "execution_log.jsonl"
        self.execution_log.parent.mkdir(parents=True, exist_ok=True)
    
    def execute(self, action: Dict) -> Dict:
        """액션 실행"""
        if not action.get('auto_execute'):
            print(f"⏸️ Manual approval required for: {action['action']}")
            return {'status': 'skipped', 'reason': 'Manual approval required'}
        
        executors = {
            'create_file': self.execute_create_file,
            'modify_code': self.execute_modify_code,
            'create_system': self.execute_create_system,
            'connect_tools': self.execute_connect_tools,
            'automate': self.execute_automate,
            'learn': self.execute_learn
        }
        
        executor = executors.get(action['action'])
        if executor:
            try:
                result = executor(action)
                self._log_execution(action, result)
                return result
            except Exception as e:
                error_result = {'status': 'error', 'error': str(e)}
                self._log_execution(action, error_result)
                return error_result
        
        return {'status': 'unknown_action', 'action': action['action']}
    
    def execute_create_file(self, action: Dict) -> Dict:
        """파일 생성 실행"""
        file_path = self.workspace / action['file_path']
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 간단한 템플릿 생성
        content = self._generate_file_content(action)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ File created: {file_path}")
        return {'status': 'success', 'file': str(file_path)}
    
    def execute_modify_code(self, action: Dict) -> Dict:
        """코드 수정 실행"""
        print(f"⚠️ Code modification requires manual review")
        return {'status': 'manual_review_required'}
    
    def execute_create_system(self, action: Dict) -> Dict:
        """시스템 생성 실행"""
        # 간단한 시스템 구조 생성
        system_name = self._extract_system_name(action['system_description'])
        
        files_created = []
        
        # README
        readme_path = self.workspace / f"docs/{system_name}_ARCHITECTURE.md"
        readme_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {system_name} Architecture\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
            f.write(f"**Description**: {action['system_description']}\n\n")
            f.write("## Components\n\n")
            f.write("- Component A\n")
            f.write("- Component B\n")
        
        files_created.append(str(readme_path))
        
        # Main script
        script_path = self.workspace / f"scripts/{system_name.lower()}_system.py"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f'"""{system_name} System"""\n\n')
            f.write('class System:\n')
            f.write('    """Main system class"""\n')
            f.write('    pass\n')
        
        files_created.append(str(script_path))
        
        print(f"✅ System created: {len(files_created)} files")
        return {'status': 'success', 'files_created': files_created}
    
    def execute_connect_tools(self, action: Dict) -> Dict:
        """도구 연결 실행"""
        tools = action['tools']
        
        # 브릿지 파일 생성
        bridge_name = '_'.join(tools) + '_bridge'
        bridge_path = self.workspace / f"scripts/{bridge_name}.py"
        
        with open(bridge_path, 'w', encoding='utf-8') as f:
            f.write(f'"""Bridge: {" ↔ ".join(tools)}"""\n\n')
            
            for tool in tools:
                f.write(f'class {tool.capitalize()}Bridge:\n')
                f.write(f'    """Connect to {tool}"""\n')
                f.write('    pass\n\n')
        
        print(f"✅ Bridge created: {bridge_path}")
        return {'status': 'success', 'bridge': str(bridge_path)}
    
    def execute_automate(self, action: Dict) -> Dict:
        """자동화 실행"""
        auto_script = self.workspace / "scripts/automation_script.py"
        auto_script.parent.mkdir(parents=True, exist_ok=True)
        
        with open(auto_script, 'w', encoding='utf-8') as f:
            f.write('"""Automation Script"""\n\n')
            f.write(f'# {action["automation_prompt"]}\n\n')
            f.write('def automate():\n')
            f.write('    """Main automation logic"""\n')
            f.write('    pass\n\n')
            f.write('if __name__ == "__main__":\n')
            f.write('    automate()\n')
        
        print(f"✅ Automation script created: {auto_script}")
        return {'status': 'success', 'script': str(auto_script)}
    
    def execute_learn(self, action: Dict) -> Dict:
        """학습 실행"""
        # 학습 로그 기록
        learning_log = self.workspace / "memory/learning_log.jsonl"
        learning_log.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'prompt': action['learning_prompt'],
            'status': 'recorded'
        }
        
        with open(learning_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✅ Learning recorded")
        return {'status': 'success', 'log': str(learning_log)}
    
    def _generate_file_content(self, action: Dict) -> str:
        """파일 내용 생성"""
        prompt = action.get('content_prompt', '')
        
        # 간단한 템플릿
        if action['file_path'].endswith('.py'):
            return f'"""{prompt}"""\n\ndef main():\n    pass\n\nif __name__ == "__main__":\n    main()\n'
        elif action['file_path'].endswith('.md'):
            return f'# Auto-Generated Document\n\n**Generated**: {datetime.now().isoformat()}\n\n{prompt}\n'
        else:
            return f'{prompt}\n'
    
    def _extract_system_name(self, description: str) -> str:
        """시스템 이름 추출"""
        # 간단한 추출
        words = description.split()
        if len(words) > 0:
            return words[0].capitalize()
        return 'UnknownSystem'
    
    def _log_execution(self, action: Dict, result: Dict):
        """실행 로그 기록"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'result': result
        }
        
        with open(self.execution_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


class CircularEmbodimentEngine:
    """경험 → 학습 → 시스템 순환"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.experience_log = workspace_root / "memory/experience_log.jsonl"
        self.learned_patterns = workspace_root / "memory/learned_patterns.json"
        self.auto_systems = workspace_root / "memory/auto_systems.json"
        
        for path in [self.experience_log, self.learned_patterns, self.auto_systems]:
            path.parent.mkdir(parents=True, exist_ok=True)
    
    def record_experience(self, action: Dict, result: Dict):
        """경험 기록"""
        experience = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'result': result,
            'success': result.get('status') == 'success',
            'intent_type': action.get('intent', {}).get('type', 'unknown')
        }
        
        with open(self.experience_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(experience, ensure_ascii=False) + '\n')
        
        # 패턴 학습
        if experience['success']:
            self.learn_from_experience(experience)
    
    def learn_from_experience(self, experience: Dict):
        """경험에서 패턴 학습"""
        patterns = self._load_learned_patterns()
        
        pattern_key = f"{experience['action']['action']}_{experience['intent_type']}"
        
        if pattern_key not in patterns:
            patterns[pattern_key] = {
                'count': 0,
                'success_count': 0,
                'success_rate': 0.0,
                'template': experience['action'],
                'first_seen': experience['timestamp']
            }
        
        patterns[pattern_key]['count'] += 1
        if experience['success']:
            patterns[pattern_key]['success_count'] += 1
        
        patterns[pattern_key]['success_rate'] = (
            patterns[pattern_key]['success_count'] / patterns[pattern_key]['count']
        )
        
        self._save_learned_patterns(patterns)
        
        # 충분히 학습되면 자동 시스템으로 승격
        if (patterns[pattern_key]['count'] >= 5 and 
            patterns[pattern_key]['success_rate'] > 0.8):
            self.promote_to_auto_system(pattern_key, patterns[pattern_key])
    
    def promote_to_auto_system(self, pattern_key: str, pattern: Dict):
        """학습된 패턴을 자동 시스템으로 승격"""
        auto_systems = self._load_auto_systems()
        
        if pattern_key in auto_systems:
            return  # 이미 승격됨
        
        auto_systems[pattern_key] = {
            'template': pattern['template'],
            'auto_execute': True,
            'learned_from_experiences': pattern['count'],
            'confidence': pattern['success_rate'],
            'promoted_at': datetime.now().isoformat()
        }
        
        self._save_auto_systems(auto_systems)
        
        print(f"\n🌟 New auto-system learned: {pattern_key}")
        print(f"   Confidence: {pattern['success_rate']:.2f}")
        print(f"   From {pattern['count']} successful experiences")
    
    def _load_learned_patterns(self) -> Dict:
        """학습된 패턴 로드"""
        if self.learned_patterns.exists():
            with open(self.learned_patterns, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_learned_patterns(self, patterns: Dict):
        """학습된 패턴 저장"""
        with open(self.learned_patterns, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
    
    def _load_auto_systems(self) -> Dict:
        """자동 시스템 로드"""
        if self.auto_systems.exists():
            with open(self.auto_systems, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_auto_systems(self, systems: Dict):
        """자동 시스템 저장"""
        with open(self.auto_systems, 'w', encoding='utf-8') as f:
            json.dump(systems, f, indent=2, ensure_ascii=False)


def test_bridge():
    """테스트 실행"""
    workspace = Path("c:/workspace/agi")
    
    # 1. Conversation Bridge 테스트
    print("\n=== Test 1: Conversation Capture ===")
    bridge = ConversationBridge(workspace)
    
    conversation = bridge.capture_conversation(
        conversation_id="test_001",
        messages=[
            {"role": "user", "content": "ADHD 스타일 학습 시스템을 만들어줘"},
            {"role": "assistant", "content": "좋아요! 설계해볼게요..."}
        ]
    )
    
    # 2. Intent → Action 변환
    print("\n=== Test 2: Intent to Action ===")
    translator = IntentToActionTranslator(workspace)
    action = translator.translate(conversation['extracted_intent'])
    
    print(f"Action: {action['action']}")
    print(f"Auto-execute: {action.get('auto_execute', False)}")
    
    # 3. Auto Execution
    print("\n=== Test 3: Auto Execution ===")
    executor = AutoExecutionEngine(workspace)
    result = executor.execute(action)
    
    print(f"Result: {result}")
    
    # 4. Circular Embodiment
    print("\n=== Test 4: Learning Cycle ===")
    embodiment = CircularEmbodimentEngine(workspace)
    embodiment.record_experience(action, result)
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    test_bridge()
