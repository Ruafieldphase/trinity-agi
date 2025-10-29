#!/usr/bin/env python3
"""
?뙄 ?몃굹??- Vertex AI ?곌껐 ?뚯뒪???ㅽ겕由쏀듃
"""

import os
import json
from datetime import datetime

def test_google_ai_studio():
    """Google AI Studio API ?뚯뒪??""
    try:
        import google.generativeai as genai
        
        # API ???ㅼ젙 (?섍꼍蹂?섏뿉??
        api_key = os.getenv('GOOGLE_AI_STUDIO_API_KEY')
        if not api_key:
            return {
                "status": "NEED_API_KEY",
                "message": "Google AI Studio API ?ㅺ? ?꾩슂?⑸땲??,
                "action": "https://aistudio.google.com/app/apikey ?먯꽌 API ??諛쒓툒"
            }
        
        genai.configure(api_key=api_key)
        
        # 媛꾨떒???뚯뒪??        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello! This is a Vertex AI connection test.")
        
        return {
            "status": "SUCCESS",
            "message": "Google AI Studio ?곌껐 ?깃났!",
            "response_preview": response.text[:100] + "..."
        }
        
    except ImportError:
        return {
            "status": "INSTALL_NEEDED", 
            "message": "google-generativeai ?⑦궎吏 ?ㅼ튂 ?꾩슂",
            "action": "pip install google-generativeai"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"?곌껐 ?ㅻ쪟: {str(e)}"
        }

def test_vertex_ai():
    """Vertex AI ?곌껐 ?뚯뒪??""
    try:
        from google.cloud import aiplatform
        
        # ?꾨줈?앺듃 ?ㅼ젙
        aiplatform.init(
            project="naeda-genesis",
            location="asia-southeast2"
        )
        
        return {
            "status": "SUCCESS",
            "message": "Vertex AI ?곌껐 ?깃났!",
            "project": "naeda-genesis",
            "location": "asia-southeast2"
        }
        
    except Exception as e:
        return {
            "status": "ERROR", 
            "message": f"Vertex AI ?곌껐 ?ㅻ쪟: {str(e)}"
        }

def main():
    """?뙄 ?몃굹???곌껐 ?뚯뒪???ㅽ뻾"""
    print("?뙄 ?몃굹??- AI ?곌껐 ?뚯뒪???쒖옉...")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tester": "?몃굹??釉뚮━吏??,
        "tests": {}
    }
    
    # Google AI Studio ?뚯뒪??    print("\n?뱻 Google AI Studio ?뚯뒪??..")
    results["tests"]["google_ai_studio"] = test_google_ai_studio()
    print(f"   寃곌낵: {results['tests']['google_ai_studio']['status']}")
    
    # Vertex AI ?뚯뒪?? 
    print("\n?뙋 Vertex AI ?뚯뒪??..")
    results["tests"]["vertex_ai"] = test_vertex_ai()
    print(f"   寃곌낵: {results['tests']['vertex_ai']['status']}")
    
    # 寃곌낵 ???    with open('C:\\LLM_Unified\\connection_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n???뚯뒪???꾨즺! 寃곌낵 ??λ맖: connection_test_results.json")
    
    return results

if __name__ == "__main__":
    main()
