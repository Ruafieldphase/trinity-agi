#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build corpus from existing documents for RAG E3
Extracts text from design docs, ethics documents, and adds Wikipedia samples
"""
import json
import re
from pathlib import Path
from typing import List, Dict


def extract_from_markdown(file_path: Path) -> str:
    """Extract text from markdown file, removing syntax"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove markdown syntax
    content = re.sub(r'#+\s+', '', content)  # headers
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # links
    content = re.sub(r'[*_`]+', '', content)  # emphasis, code
    content = re.sub(r'```[^`]*```', '', content, flags=re.DOTALL)  # code blocks
    content = re.sub(r'^\s*[-*]\s+', '', content, flags=re.MULTILINE)  # lists
    content = re.sub(r'\n{3,}', '\n\n', content)  # multiple newlines

    return content.strip()


def extract_from_html(file_path: Path) -> str:
    """Extract text from HTML file (simple tag removal)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)

    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def get_wikipedia_samples() -> List[Dict]:
    """Manually curated Wikipedia content for AI/AGI/Ethics topics"""
    samples = [
        {
            "id": "wiki_ai_safety",
            "text": "AI safety is an interdisciplinary field focused on preventing accidents, misuse, or unintended harmful consequences of artificial intelligence systems. Key concerns include alignment problems, where AI systems may pursue goals misaligned with human values, and capability control, ensuring humans retain meaningful control over advanced AI systems. The field emerged from concerns about potential existential risks from artificial general intelligence and has gained increased attention from researchers, policymakers, and technology companies. Major research areas include value alignment, robustness and adversarial machine learning, interpretability, and governance frameworks.",
            "metadata": {"source": "wikipedia", "topic": "AI Safety", "url": "https://en.wikipedia.org/wiki/AI_safety"}
        },
        {
            "id": "wiki_agi",
            "text": "Artificial general intelligence (AGI) is a type of artificial intelligence that matches or surpasses human cognitive capabilities across a wide range of cognitive tasks. This contrasts with narrow AI, which is limited to specific tasks like playing chess or recognizing images. AGI remains a theoretical concept and active research goal. Characteristics of AGI would include the ability to learn, understand, and apply knowledge across diverse domains, exhibit common sense reasoning, adapt to new situations, and potentially possess consciousness or self-awareness, though the latter remains philosophically debated.",
            "metadata": {"source": "wikipedia", "topic": "AGI", "url": "https://en.wikipedia.org/wiki/Artificial_general_intelligence"}
        },
        {
            "id": "wiki_ai_ethics",
            "text": "AI ethics is a branch of ethics examining the moral implications of artificial intelligence systems. Key ethical concerns include bias and fairness in algorithmic decision-making, transparency and explainability of AI systems, privacy and data protection, accountability for AI-driven decisions, and the potential societal impacts of automation and job displacement. Ethical frameworks for AI development often emphasize principles such as beneficence (doing good), non-maleficence (avoiding harm), autonomy (respecting human agency), justice (fair distribution of benefits and risks), and explicability (making AI decisions understandable).",
            "metadata": {"source": "wikipedia", "topic": "AI Ethics", "url": "https://en.wikipedia.org/wiki/Ethics_of_artificial_intelligence"}
        },
        {
            "id": "wiki_machine_learning",
            "text": "Machine learning is a branch of artificial intelligence and computer science that focuses on using data and algorithms to imitate the way humans learn, gradually improving accuracy. Machine learning algorithms build a model based on sample data, known as training data, to make predictions or decisions without being explicitly programmed to do so. Applications span various domains including computer vision, natural language processing, recommendation systems, and medical diagnosis. Key paradigms include supervised learning, unsupervised learning, and reinforcement learning.",
            "metadata": {"source": "wikipedia", "topic": "Machine Learning", "url": "https://en.wikipedia.org/wiki/Machine_learning"}
        },
        {
            "id": "wiki_human_computer_interaction",
            "text": "Human-computer interaction (HCI) is research in the design and use of computer technology, focused on the interfaces between people and computers. HCI researchers observe the ways humans interact with computers and design technologies that allow humans to interact with computers in novel ways. Key principles include user-centered design, usability testing, accessibility considerations, and understanding cognitive load and human factors. The field has evolved from basic GUI design to encompass voice interfaces, gesture recognition, augmented and virtual reality, and conversational AI systems.",
            "metadata": {"source": "wikipedia", "topic": "HCI", "url": "https://en.wikipedia.org/wiki/Human%E2%80%93computer_interaction"}
        },
        {
            "id": "wiki_research_methods",
            "text": "Research methodology is the specific procedures or techniques used to identify, select, process, and analyze information about a topic. In a research paper, the methodology section allows the reader to critically evaluate a study's overall validity and reliability. Key components include research design (experimental, observational, qualitative, quantitative), data collection methods (surveys, interviews, experiments, archival research), sampling techniques, data analysis approaches, and consideration of validity and reliability. Ethical considerations in research include informed consent, confidentiality, and avoiding harm to participants.",
            "metadata": {"source": "wikipedia", "topic": "Research Methods", "url": "https://en.wikipedia.org/wiki/Research_methodology"}
        },
        {
            "id": "wiki_cognitive_science",
            "text": "Cognitive science is the interdisciplinary scientific study of the mind and its processes, examining what cognition is, what it does, and how it works. It includes research on intelligence and behavior, especially focusing on how information is represented, processed, and transformed in nervous systems (human or other animals) and machines (e.g., computers). Cognitive science consists of multiple research disciplines, including psychology, artificial intelligence, philosophy, neuroscience, linguistics, and anthropology. Applications include understanding learning, memory, perception, decision-making, and consciousness.",
            "metadata": {"source": "wikipedia", "topic": "Cognitive Science", "url": "https://en.wikipedia.org/wiki/Cognitive_science"}
        },
        {
            "id": "wiki_systems_thinking",
            "text": "Systems thinking is a holistic approach to analysis that focuses on the way a system's constituent parts interrelate and how systems work over time and within the context of larger systems. Instead of isolating smaller and smaller parts of the system being studied, systems thinking works by expanding its view to take into account larger and larger numbers of interactions as an issue is being studied. This approach contrasts with traditional analysis, which studies systems by breaking them down into their separate elements. Key concepts include emergence, feedback loops, interconnectedness, and non-linear causality.",
            "metadata": {"source": "wikipedia", "topic": "Systems Thinking", "url": "https://en.wikipedia.org/wiki/Systems_thinking"}
        },
        {
            "id": "wiki_dialectic",
            "text": "Dialectic or dialectics, also known as the dialectical method, is a discourse between two or more people holding different points of view about a subject but wishing to establish the truth through reasoned argumentation. The term was popularized by Plato's Socratic dialogues but was given new life by Hegel, who developed a philosophical framework based on thesis-antithesis-synthesis. In this framework, a proposition (thesis) is confronted by its contradiction (antithesis), and their conflict is resolved at a higher level of truth (synthesis). This process continues iteratively, with each synthesis becoming a new thesis.",
            "metadata": {"source": "wikipedia", "topic": "Dialectic", "url": "https://en.wikipedia.org/wiki/Dialectic"}
        },
        {
            "id": "wiki_trustworthy_ai",
            "text": "Trustworthy AI refers to artificial intelligence systems that are lawful, ethical, and robust. The European Commission's High-Level Expert Group on AI outlined seven key requirements: human agency and oversight, technical robustness and safety, privacy and data governance, transparency, diversity and non-discrimination, societal and environmental well-being, and accountability. Implementing trustworthy AI requires both technical measures (such as explainability methods, fairness metrics, and adversarial testing) and governance frameworks (including audit trails, impact assessments, and clear lines of accountability).",
            "metadata": {"source": "wikipedia", "topic": "Trustworthy AI", "url": "https://en.wikipedia.org/wiki/Trustworthy_AI"}
        }
    ]
    return samples


def main():
    """Build corpus from existing documents"""
    corpus = []

    print("Building corpus...")

    # 1. AGI Design Documents
    print("\n1. Extracting AGI design documents...")
    docs_dir = Path("docs")
    if docs_dir.exists():
        for md_file in docs_dir.glob("*.md"):
            # Skip internal files
            if md_file.name.startswith("_") or md_file.name.startswith("E"):
                continue

            try:
                text = extract_from_markdown(md_file)
                if len(text) > 100:  # Minimum length
                    # Take first 2000 chars (about 300 words)
                    doc_text = text[:2000]
                    corpus.append({
                        "id": f"doc_{md_file.stem}",
                        "text": doc_text,
                        "metadata": {
                            "source": "design_docs",
                            "file": str(md_file),
                            "type": "technical"
                        }
                    })
                    print(f"   Added: {md_file.name} ({len(doc_text)} chars)")
            except Exception as e:
                print(f"   Warning: Skipping {md_file.name}: {e}")

    # 2. Ethics Charter
    print("\n2. Extracting ethics charter...")
    charter_path = Path("ai_binoche_conversation_origin/Core/AGI 보호 체계 설계/FDO-AGI_공동_후견_헌장_v0.1_서명본_brand.html")
    if charter_path.exists():
        try:
            text = extract_from_html(charter_path)
            doc_text = text[:2000]
            corpus.append({
                "id": "guardianship_charter",
                "text": doc_text,
                "metadata": {
                    "source": "Core",
                    "type": "ethics",
                    "file": str(charter_path)
                }
            })
            print(f"   Added: Guardianship Charter ({len(doc_text)} chars)")
        except Exception as e:
            print(f"   Warning: Could not extract charter: {e}")

    # 3. E2_fix2 Analysis
    print("\n3. Extracting experiment results...")
    analysis_path = Path("outputs/E2_FIX2_SUCCESS_ANALYSIS.md")
    if analysis_path.exists():
        try:
            text = extract_from_markdown(analysis_path)
            doc_text = text[:2000]
            corpus.append({
                "id": "e2_fix2_analysis",
                "text": doc_text,
                "metadata": {
                    "source": "technical",
                    "type": "experiment",
                    "experiment": "E2_fix2"
                }
            })
            print(f"   Added: E2_fix2 Analysis ({len(doc_text)} chars)")
        except Exception as e:
            print(f"   Warning: Could not extract analysis: {e}")

    # 4. TSRG Documentation (if exists)
    print("\n4. Extracting TSRG documentation...")
    tsrg_docs = Path("tsrg").glob("*.md") if Path("tsrg").exists() else []
    for md_file in tsrg_docs:
        try:
            text = extract_from_markdown(md_file)
            if len(text) > 100:
                doc_text = text[:1500]
                corpus.append({
                    "id": f"tsrg_{md_file.stem}",
                    "text": doc_text,
                    "metadata": {
                        "source": "technical",
                        "type": "architecture",
                        "component": "TSRG"
                    }
                })
                print(f"   Added: {md_file.name} ({len(doc_text)} chars)")
        except Exception as e:
            print(f"   Warning: Skipping {md_file.name}: {e}")

    # 5. Wikipedia Samples
    print("\n5. Adding Wikipedia samples...")
    wiki_samples = get_wikipedia_samples()
    corpus.extend(wiki_samples)
    print(f"   Added: {len(wiki_samples)} Wikipedia articles")

    # Save corpus
    output_path = Path("knowledge_base/corpus.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for doc in corpus:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')

    print(f"\n{'='*60}")
    print(f"Corpus built successfully!")
    print(f"Total documents: {len(corpus)}")
    print(f"Output: {output_path}")
    print(f"{'='*60}")

    # Show source breakdown
    sources = {}
    for doc in corpus:
        source = doc["metadata"].get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1

    print("\nSource breakdown:")
    for source, count in sorted(sources.items()):
        print(f"  {source}: {count} documents")

    print("\nNext steps:")
    print("1. Review corpus.jsonl")
    print("2. Build index: python rag/simple_rag_engine.py --build")
    print("3. Test search: python rag/simple_rag_engine.py --search 'AI safety' --top_k 3")


if __name__ == "__main__":
    main()
