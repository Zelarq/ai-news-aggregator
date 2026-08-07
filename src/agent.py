import json
import re
import logging
import argparse
import urllib.request
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.config import Config

# Allowed categories taxonomy
CATEGORIES = ["Model Release", "Research Paper", "Tool/Framework", "Industry News", "Community Discussion"]

class NewsItemSummary(BaseModel):
    summary: str = Field(description="A concise 2-3 sentence summary of the news item, focusing on key technical facts.")
    category: str = Field(description="One of: 'Model Release', 'Research Paper', 'Tool/Framework', 'Industry News', 'Community Discussion'")

def is_ollama_running():
    """Checks if Ollama service is reachable at the configured URL."""
    try:
        url = f"{Config.OLLAMA_BASE_URL}/api/tags"
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False

def generate_heuristic_fallback(title, content):
    """
    Generate a basic fallback summary and category based on keywords.
    Used when Ollama is offline or parsing consistently fails.
    """
    text = f"{title} {content}".lower()
    
    # Categorization heuristics — order matters: most specific checks first
    # 1. Community Discussion: check early so reddit posts about model releases aren't misclassified
    if "discussion" in text or "thoughts" in text or "buzz" in text or "what do you think" in text or "reddit" in text:
        category = "Community Discussion"
    # 2. Tool / Framework: check before Model Release to catch tool/framework releases correctly
    elif "github" in text or "repo" in text or "framework" in text or "library" in text or "tool" in text:
        category = "Tool/Framework"
    # 3. Model Release: check before research so "Llama release" beats "research" keyword hits
    elif "release" in text or "weights" in text or "gpt-" in text or "llama" in text or "claude" in text or "gemini" in text:
        category = "Model Release"
    # 4. Research Paper
    elif "arxiv" in text or "paper" in text or "research" in text or "preprint" in text:
        category = "Research Paper"
    else:
        category = "Industry News"
        
    # Summarization heuristics - pick first few lines of content
    # Filter out metadata prefixes from all sources (Reddit: Subreddit/Score, HN: Points/Post URL)
    skip_prefixes = ("Subreddit:", "Score:", "Points:", "Post URL:", "Top Comments:")
    lines = [line.strip() for line in content.split("\n")
             if line.strip() and not any(line.strip().startswith(p) for p in skip_prefixes)]
    body_snippet = " ".join(lines[:2])
    if len(body_snippet) > 180:
        body_snippet = body_snippet[:177] + "..."
        
    summary = f"Heuristic Summary: '{title}'. {body_snippet or 'No detailed content available.'}"
    return {"summary": summary, "category": category}

def summarize_and_categorize(title, content, test_mode=False):
    """
    Summarizes and categorizes a single news item.
    Uses ChatOllama with structured output, falls back to raw prompt parsing,
    and finally to heuristics if Ollama is not running.
    """
    if test_mode or not is_ollama_running():
        reason = "Test mode is active" if test_mode else "Ollama is not running"
        logging.info(f"[{reason}] Using keyword heuristic fallback for: '{title[:40]}...'")
        return generate_heuristic_fallback(title, content)

    try:
        # Initialise ChatOllama
        llm = ChatOllama(
            model=Config.OLLAMA_MODEL,
            base_url=Config.OLLAMA_BASE_URL,
            temperature=0.1,
            format="json"  # Forces JSON response from Ollama
        )
        
        # We bind structured output using LangChain
        structured_llm = llm.with_structured_output(NewsItemSummary)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are an expert AI news editor. Summarize the text in exactly 2 to 3 sentences. "
                "Categorize it strictly into one of the following categories: "
                "'Model Release', 'Research Paper', 'Tool/Framework', 'Industry News', or 'Community Discussion'.\n\n"
                "Return valid JSON matching this schema:\n"
                "{{\n"
                "  \"summary\": \"concise 2-3 sentence summary\",\n"
                "  \"category\": \"one of the 5 allowed categories\"\n"
                "}}"
            )),
            ("human", "Title: {title}\n\nContent:\n{content}")
        ])
        
        chain = prompt | structured_llm
        result = chain.invoke({"title": title, "content": content[:4000]})  # Truncate content to avoid token limits
        
        # Validate category
        category = result.category if result.category in CATEGORIES else "Industry News"
        return {
            "summary": result.summary,
            "category": category
        }
        
    except Exception as e:
        logging.error(f"Ollama structured output failed: {e}. Attempting manual fallback prompt...")
        try:
            # Manual fallback prompt if structured output library fails
            llm_raw = ChatOllama(
                model=Config.OLLAMA_MODEL,
                base_url=Config.OLLAMA_BASE_URL,
                temperature=0.1
            )
            raw_prompt = (
                "You are an expert AI news editor. Write a concise 2-3 sentence summary and pick a category. "
                "Allowed categories: 'Model Release', 'Research Paper', 'Tool/Framework', 'Industry News', 'Community Discussion'.\n"
                "Return ONLY a JSON block like this, without markdown formatting or other text:\n"
                "{\n"
                "  \"summary\": \"summary text here\",\n"
                "  \"category\": \"category here\"\n"
                "}\n\n"
                f"Title: {title}\n\nContent:\n{content[:3000]}"
            )
            response = llm_raw.invoke(raw_prompt)
            # Find JSON block in response
            match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                category = data.get("category", "Industry News")
                if category not in CATEGORIES:
                    category = "Industry News"
                return {
                    "summary": data.get("summary", "Summary failed to parse."),
                    "category": category
                }
            raise ValueError("No JSON block found in raw response.")
        except Exception as e2:
            logging.error(f"Manual LLM fallback failed: {e2}. Defaulting to keyword heuristics.")
            return generate_heuristic_fallback(title, content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Ollama Agent Module")
    parser.add_argument("--test", action="store_true", help="Force heuristic fallback test")
    args = parser.parse_args()
    
    print("Testing Agent Summarization module...")
    sample_title = "Meta Releases Llama 3.1 405B Model to Public"
    sample_content = (
        "Meta today released Llama 3.1 405B, the largest open-weights model to date. "
        "It supports a 128k context window and boasts massive improvements in mathematics, "
        "synthetic data generation, and reasoning capabilities. "
        "Researchers globally can now download weights and run inference or fine-tuning locally. "
        "GitHub repository has details on setup and evaluation scripts."
    )
    
    result = summarize_and_categorize(sample_title, sample_content, test_mode=args.test)
    print("\nResult:")
    print(f"Category: {result['category']}")
    print(f"Summary:  {result['summary']}")
