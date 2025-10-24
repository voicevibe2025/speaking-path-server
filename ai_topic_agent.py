import os
import re
import json
import argparse
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

TOPICS_FILE = Path(r"C:/Users/user/AndroidStudioProjects/VoiceVibe2/django/apps/speaking_journey/management/commands/topics.py")
TTS_JS_FILE = Path(r"C:/Users/user/gemini-tts/tts.js")
DJANGO_DIR = Path(r"C:/Users/user/AndroidStudioProjects/VoiceVibe2/django")

DEFAULT_PROVIDER = os.environ.get("AGENT_LLM_PROVIDER", "gemini").lower()
DEFAULT_GEMINI_MODEL = os.environ.get("AGENT_GEMINI_MODEL", "gemini-2.5-pro")
DEFAULT_DEEPSEEK_MODEL = os.environ.get("AGENT_DEEPSEEK_MODEL", "deepseek-reasoner")

# --------------------- Utilities ---------------------

def load_env():
    # Load .env next to manage.py
    if load_dotenv:
        dotenv_path = DJANGO_DIR / ".env"
        if dotenv_path.exists():
            load_dotenv(dotenv_path)


def read_topics_file() -> str:
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        return f.read()


def write_topics_file(content: str):
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def _find_list_block(content: str, var_name: str) -> (int, int):
    m = re.search(rf"^\s*{re.escape(var_name)}\s*=\s*\[", content, flags=re.M)
    if not m:
        raise RuntimeError(f"Could not locate list for {var_name} in topics.py")
    start_br = content.find('[', m.start())
    i = start_br
    depth = 0
    in_str = False
    esc = False
    quote = ''
    while i < len(content):
        ch = content[i]
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == quote:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                quote = ch
            elif ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    return start_br, i
        i += 1
    raise RuntimeError(f"Unbalanced brackets for {var_name} in topics.py")


def get_titles_from_topics(level: str) -> List[str]:
    content = read_topics_file()
    var_name = f"{level.upper()}_TOPICS"
    start, end = _find_list_block(content, var_name)
    block = content[start:end + 1]
    pattern = r'[\"\']title[\"\']\s*:\s*[\"\']([^\"\']+)[\"\']'
    return re.findall(pattern, block)


def resolve_venv_python() -> List[str]:
    """Return the Python executable command list, preferring the project's venv on Windows."""
    # Windows venv default path
    win_venv = DJANGO_DIR / "venv" / "Scripts" / "python.exe"
    if win_venv.exists():
        return [str(win_venv)]
    # Fallback to generic 'python'
    return ["python"]


# --------------------- LLM Wrappers ---------------------

def _gemini_generate(prompt: str, model: str) -> str:
    # Prefer new google.genai, fallback to google.generativeai
    try:
        from google import genai as new_genai  # type: ignore
        client = new_genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        resp = client.models.generate_content(model=model, contents=prompt)
        text = getattr(resp, "text", None) or getattr(resp, "output_text", None)
        if not text and hasattr(resp, "candidates"):
            # Try candidates[0].content.parts[0].text style
            try:
                text = resp.candidates[0].content.parts[0].text
            except Exception:
                pass
        if not text:
            text = str(resp)
        return text
    except Exception:
        pass

    # Fallback old SDK
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        model_obj = genai.GenerativeModel(model)
        resp = model_obj.generate_content(prompt)
        return getattr(resp, "text", None) or str(resp)
    except Exception as e:
        raise RuntimeError(f"Gemini generation failed: {e}")


def _deepseek_generate(prompt: str, model: str) -> str:
    import requests
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY in environment")
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that outputs strictly in the requested JSON format with no extra commentary."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def llm_generate(prompt: str, provider: str, gemini_model: str, deepseek_model: str) -> str:
    provider = provider.lower()
    last_err: Optional[Exception] = None
    # Simple retry/backoff for transient protocol resets
    for attempt in range(3):
        try:
            if provider == "gemini":
                return _gemini_generate(prompt, gemini_model)
            elif provider == "deepseek":
                return _deepseek_generate(prompt, deepseek_model)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except Exception as e:
            last_err = e
            # backoff 1s, 3s then give up
            delay = 1 if attempt == 0 else 3
            print(f"LLM call failed (attempt {attempt+1}/3): {e}. Retrying in {delay}s...")
            time.sleep(delay)
    # All retries exhausted
    assert last_err is not None
    raise last_err


# --------------------- Prompt Builders ---------------------

def build_suggestion_prompt(existing_titles: List[str], count: int, level: str, refine: str = "") -> str:
    titles_str = "\n".join(f"- {t}" for t in existing_titles)
    level_lower = level.lower()
    cefr = {
        "beginner": "CEFR A1-A2",
        "intermediate": "CEFR B1",
        "advanced": "CEFR B2-C1",
    }.get(level_lower, "CEFR A2-B1")
    extra = ("\nAdditional instruction: " + refine.strip()) if refine and refine.strip() else ""
    return (
        "Suggest {count} new speaking practice topic titles tailored for {level} ESL learners.\n"
        "Avoid ANY overlap with this existing list of titles (case-insensitive):\n"
        f"{titles_str}\n\n"
        "Constraints:\n"
        "- Everyday scenarios for ESL learners\n"
        "- Keep titles 2-6 words, clear and distinct\n"
        "- No duplicates or near-duplicates\n"
        f"- Target difficulty: {cefr}\n"
        "Output strictly a minified JSON array of strings, e.g.:\n"
        "[\"Title A\",\"Title B\",...]\n"
        f"{extra}"
    ).format(count=count, level=level.capitalize())


def build_topic_content_prompt(title: str, level: str, refine: str = "") -> str:
    level_lower = level.lower()
    cefr = {
        "beginner": "CEFR A1-A2",
        "intermediate": "CEFR B1",
        "advanced": "CEFR B2-C1",
    }.get(level_lower, "CEFR A2-B1")
    extra = ("\nExtra constraints: " + refine.strip()) if refine and refine.strip() else ""
    return (
        "Generate a complete speaking practice topic as strict JSON with keys: "
        "title, description, material, conversation, vocabulary, fluency_practice_prompt.\n"
        f"Use this exact title: {json.dumps(title)}\n"
        "Rules:\n"
        "- description: 1-2 sentences, simple\n"
        "- material: 8-12 short example lines (strings)\n"
        "- conversation: 8-14 turns, list of objects with keys 'speaker' and 'text'.\n"
        "  Use only speakers 'A' and 'B'. Natural, helpful, culturally neutral.\n"
        "- vocabulary: 12-24 plain words/phrases (strings)\n"
        "- fluency_practice_prompt: a one-sentence prompt\n"
        f"- Keep difficulty around {cefr}\n"
        "- If extra constraints are provided, they override the defaults and must be followed strictly\n"
        "- DO NOT include any extra keys\n"
        "- Output strictly minified JSON only (no markdown)\n"
        "Example shape (minified): {\"title\":\"T\",\"description\":\"...\",\"material\":[""],\"conversation\":[{\"speaker\":\"A\",\"text\":\"...\"}],\"vocabulary\":[""],\"fluency_practice_prompt\":\"...\"}"
        f"{extra}"
    )


# --------------------- JSON Helpers ---------------------

def extract_json(text: str) -> str:
    """Extract a JSON object/array from text, stripping code fences if present."""
    text = text.strip()
    # Remove markdown fences if any
    if text.startswith("```"):
        # strip first line fence and last fence
        parts = text.split("\n")
        if parts:
            # remove first line
            parts = parts[1:]
        # remove trailing ``` if present
        if parts and parts[-1].strip().startswith("```"):
            parts = parts[:-1]
        text = "\n".join(parts).strip()
    # Try to locate a JSON object/array
    m = re.search(r"(\{.*\}|\[.*\])", text, flags=re.S)
    if m:
        return m.group(1)
    return text


def ensure_topic_schema(obj: Dict[str, Any]) -> Dict[str, Any]:
    required = ["title", "description", "material", "conversation", "vocabulary", "fluency_practice_prompt"]
    for k in required:
        if k not in obj:
            raise ValueError(f"Missing key in topic: {k}")
    if not isinstance(obj["material"], list):
        raise ValueError("material must be a list of strings")
    if not isinstance(obj["conversation"], list):
        raise ValueError("conversation must be a list of {speaker,text}")
    if not isinstance(obj["vocabulary"], list):
        raise ValueError("vocabulary must be a list of strings")
    return obj


# --------------------- File Editing ---------------------

def append_topics_to_file(new_topics: List[Dict[str, Any]], level: str):
    content = read_topics_file()
    var_name = f"{level.upper()}_TOPICS"
    start, end = _find_list_block(content, var_name)
    insert_pos = end

    # Build insertion string: each object pretty-printed and indented by 4 spaces, ending with a comma
    insert_chunks = []
    for obj in new_topics:
        obj_json = json.dumps(obj, ensure_ascii=False, indent=4)
        indented = "\n".join("    " + line for line in obj_json.splitlines())
        insert_chunks.append(indented + ",\n")
    insertion = "".join(insert_chunks)

    # Ensure there is a comma after the previous topic before we insert a new one
    i = insert_pos - 1
    while i >= 0 and content[i] in (" ", "\t", "\r", "\n"):
        i -= 1
    if i >= 0 and content[i] == '}':
        insertion = ",\n" + insertion

    new_content = content[:insert_pos] + insertion + content[insert_pos:]
    write_topics_file(new_content)


# --------------------- TTS.js Update ---------------------

def build_tts_prompt(topic_title: str, conversation: List[Dict[str, str]]) -> str:
    # Keep conversation speaker labels as 'A' and 'B' in the prompt
    lines = []
    header = f"TTS the following dialog about {topic_title}:"
    lines.append(header)
    for turn in conversation:
        spk = turn.get("speaker", "A")
        obj = {"speaker": spk, "text": turn.get("text", "").strip()}
        lines.append(json.dumps(obj, ensure_ascii=False))
    # indent each inner line by 12 spaces to match file style
    def line_suffix(i: int) -> str:
        # No comma after header (i==0) and no comma after last line
        if i == 0 or i == len(lines) - 1:
            return ""
        return ","
    inner = "\n".join((" " * 12) + l + line_suffix(i) for i, l in enumerate(lines))
    return f"const prompt = `\n{inner}\n`"


def update_tts_js(topic_title: str, conversation: List[Dict[str, str]], voice_a: str, voice_b: str):
    if not TTS_JS_FILE.exists():
        raise RuntimeError(f"tts.js not found at {TTS_JS_FILE}")
    with open(TTS_JS_FILE, "r", encoding="utf-8") as f:
        js = f.read()

    new_prompt_block = build_tts_prompt(topic_title, conversation)

    # Replace existing const prompt = `...`
    pattern = r"const\s+prompt\s*=\s*`[\s\S]*?`"
    new_js = re.sub(pattern, new_prompt_block, js, flags=re.S)

    # Replace the first two voiceName values in prebuiltVoiceConfig with voice_a and voice_b
    vn_pattern = re.compile(r'(prebuiltVoiceConfig:\s*\{\s*voiceName:\s*")([^"]+)("\s*\})', re.S)
    idx = {"i": 0}
    def _repl(m):
        i = idx["i"]
        idx["i"] += 1
        replacement = voice_a if i == 0 else voice_b
        return m.group(1) + replacement + m.group(3)
    new_js, _ = vn_pattern.subn(_repl, new_js, count=2)

    with open(TTS_JS_FILE, "w", encoding="utf-8") as f:
        f.write(new_js)


# --------------------- CLI Flow ---------------------

def tts_for_topic(tts_topic: Dict[str, Any], default_voice_a: str, default_voice_b: str):
    """Run the TTS flow for a single topic, with a try-again loop for changing voices."""
    title = tts_topic["title"]
    voice_a = default_voice_a
    voice_b = default_voice_b
    try:
        update_tts_js(title, tts_topic["conversation"], voice_a, voice_b)
        print(f"Updated tts.js prompt and voices for '{title}'.")
    except Exception as e:
        print(f"Failed to update tts.js for '{title}': {e}")
        return

    if prompt_yes_no(f"Run Node TTS for '{title}' now?"):
        while True:
            try:
                subprocess.run(["node", str(TTS_JS_FILE)], cwd=str(TTS_JS_FILE.parent), check=True)
                print("TTS generation completed. Check out.wav in the same folder.")
            except Exception as e:
                print(f"Failed to run Node TTS: {e}")

            again = prompt_yes_no("Are you happy with the TTS output? Want to try again? y/n")
            if again:
                # Let user try different voices
                voice_a = input("Enter voiceName for speaker A (e.g., Charon): ").strip() or voice_a
                voice_b = input("Enter voiceName for speaker B (e.g., Leda): ").strip() or voice_b
                try:
                    update_tts_js(title, tts_topic["conversation"], voice_a, voice_b)
                except Exception as e:
                    print(f"Failed to update tts.js with new voices: {e}")
                # Loop continues to run again
                continue
            else:
                break

def prompt_yes_no(msg: str) -> bool:
    while True:
        ans = input(f"{msg} (y/n): ").strip().lower()
        if ans in ("y", "yes"): return True
        if ans in ("n", "no"): return False
        print("Please answer y or n.")


def main():
    load_env()

    parser = argparse.ArgumentParser(description="AI Agent for automating speaking topics seeding")
    parser.add_argument("--provider", choices=["gemini", "deepseek"], default=DEFAULT_PROVIDER, help="LLM provider")
    parser.add_argument("--gemini-model", default=DEFAULT_GEMINI_MODEL)
    parser.add_argument("--deepseek-model", default=DEFAULT_DEEPSEEK_MODEL)
    parser.add_argument("--suggest-count", type=int, default=10, help="Number of topic title suggestions")
    parser.add_argument("--level", choices=[
        "BEGINNER", "INTERMEDIATE", "ADVANCED", "beginner", "intermediate", "advanced"
    ], help="Target English level list to update in topics.py")
    parser.add_argument("--refine", default="", help="Optional instruction to steer topic suggestions")
    args = parser.parse_args()

    provider = args.provider
    level = (args.level or "").strip()
    if not level:
        lvl_in = input("Choose level (BEGINNER/INTERMEDIATE/ADVANCED) [INTERMEDIATE]: ").strip()
        level = lvl_in or "INTERMEDIATE"
    level = level.upper()
    if level not in ("BEGINNER", "INTERMEDIATE", "ADVANCED"):
        print("Invalid level provided. Defaulting to INTERMEDIATE.")
        level = "INTERMEDIATE"

    print(f"Loading existing titles for {level}...")
    existing_titles = get_titles_from_topics(level)

    # 1) Suggest topics
    print(f"\nRequesting ~{args.suggest_count} {level.title()} topic suggestions from {provider}...")
    refine = (args.refine or "").strip()
    suggestion_prompt = build_suggestion_prompt(existing_titles, args.suggest_count, level, refine)
    raw = llm_generate(suggestion_prompt, provider, args.gemini_model, args.deepseek_model)
    try:
        suggestions = json.loads(extract_json(raw))
    except Exception:
        print("Model did not return clean JSON. Attempting fallback parsing...")
        suggestions = [s.strip(" -\n") for s in raw.splitlines() if s.strip()]
    # Deduplicate and filter overlaps with existing
    lower_existing = {t.lower() for t in existing_titles}
    uniq = []
    seen = set()
    for t in suggestions:
        if not isinstance(t, str):
            continue
        tl = t.strip()
        if not tl:
            continue
        key = tl.lower()
        if key in seen or key in lower_existing:
            continue
        seen.add(key)
        uniq.append(tl)
    suggestions = uniq[: args.suggest_count]

    if not suggestions:
        print("No suggestions produced. Exiting.")
        return

    print("\nSuggestions:")
    for i, t in enumerate(suggestions, 1):
        print(f" {i}. {t}")

    preselected: List[str] = []
    while True:
        refine_input = input("\nRefine suggestions with an instruction (or press Enter to keep): ").strip()
        if not refine_input:
            break
        if refine_input.lower() in ("done", "keep", "ok", "proceed", "next", "continue"):
            break
        if re.fullmatch(r"(?:\s*\d+\s*[ ,]?)+", refine_input):
            parts = re.split(r"[\s,]+", refine_input)
            tmp: List[str] = []
            for part in parts:
                if part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(suggestions):
                        tmp.append(suggestions[idx - 1])
            if tmp:
                preselected = tmp
                break
        m = re.match(r"^\s*select\s+(.+)$", refine_input, flags=re.I)
        if m:
            nums = m.group(1)
            parts = re.split(r"[\s,]+", nums)
            tmp: List[str] = []
            for part in parts:
                if part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(suggestions):
                        tmp.append(suggestions[idx - 1])
            if tmp:
                preselected = tmp
                break
        refine = refine_input
        print(f"\nRefining suggestions: {refine}")
        suggestion_prompt = build_suggestion_prompt(existing_titles, args.suggest_count, level, refine)
        raw = llm_generate(suggestion_prompt, provider, args.gemini_model, args.deepseek_model)
        try:
            suggestions = json.loads(extract_json(raw))
        except Exception:
            print("Model did not return clean JSON. Attempting fallback parsing...")
            suggestions = [s.strip(" -\n") for s in raw.splitlines() if s.strip()]
        lower_existing = {t.lower() for t in existing_titles}
        uniq = []
        seen = set()
        for t in suggestions:
            if not isinstance(t, str):
                continue
            tl = t.strip()
            if not tl:
                continue
            key = tl.lower()
            if key in seen or key in lower_existing:
                continue
            seen.add(key)
            uniq.append(tl)
        suggestions = uniq[: args.suggest_count]
        if not suggestions:
            print("No suggestions produced. Try another refinement or press Enter to keep previous list.")
            continue
        print("\nSuggestions:")
        for i, t in enumerate(suggestions, 1):
            print(f" {i}. {t}")

    # 2) Select one or more
    sel: List[str] = []
    if preselected:
        sel = preselected
    else:
        sel_raw = input("\nEnter the numbers of the topics to generate (e.g., 1,3,5): ").strip()
        if sel_raw:
            for part in re.split(r"[\s,]+", sel_raw):
                if part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(suggestions):
                        sel.append(suggestions[idx - 1])
    if not sel:
        print("No selection made. Exiting.")
        return

    # 3) Generate full content for each selected with optional refinement and append
    new_topics: List[Dict[str, Any]] = []
    stop_to_tts = False
    for title in sel:
        refine_content = ""
        current_obj: Optional[Dict[str, Any]] = None
        while True:
            print(f"\nGenerating content for: {title}")
            content_prompt = build_topic_content_prompt(title, level, refine_content)
            raw = llm_generate(content_prompt, provider, args.gemini_model, args.deepseek_model)
            try:
                obj = json.loads(extract_json(raw))
            except Exception as e:
                print(f"Failed to parse JSON for {title}: {e}\nRaw: {raw[:400]}...")
                break
            try:
                obj = ensure_topic_schema(obj)
            except Exception as e:
                print(f"Invalid schema for {title}: {e}")
                break
            current_obj = obj
            turns = len(current_obj.get("conversation", []))
            mat_n = len(current_obj.get("material", []))
            vocab_n = len(current_obj.get("vocabulary", []))
            print(f"Generated. Turns: {turns}, Material: {mat_n}, Vocabulary: {vocab_n}")
            ans = input(f"Refine content for '{title}' (enter instruction, or 'next'/'continue' to proceed to TTS): ").strip()
            if not ans:
                new_topics.append(current_obj)
                break
            if ans.lower() in ("continue", "next"):
                new_topics.append(current_obj)
                stop_to_tts = True
                break
            refine_content = ans
        if stop_to_tts:
            break

    if not new_topics:
        print("No valid topics generated. Exiting.")
        return

    print(f"\nAbout to append {len(new_topics)} topic(s) to {level}_TOPICS in topics.py.")
    proceed = prompt_yes_no("Proceed with appending?")
    if not proceed:
        print("Aborted by user.")
        return

    append_topics_to_file(new_topics, level)
    print(f"Appended successfully to {level}_TOPICS in topics.py")

    # 4) TTS step: allow ALL topics or single topic (single recommended to avoid rate limits)
    print("\nTTS preparation.")
    tts_topic = None
    if len(new_topics) > 1:
        tts_all = prompt_yes_no("Generate TTS for ALL newly added topics (one by one)?")
        if tts_all:
            # Ask default voices once
            voice_a = input("Enter voiceName for speaker A (e.g., Charon): ").strip() or "Charon"
            voice_b = input("Enter voiceName for speaker B (e.g., Leda): ").strip() or "Leda"
            for idx, t in enumerate(new_topics, 1):
                print(f"\n--- TTS {idx}/{len(new_topics)}: {t['title']} ---")
                tts_for_topic(t, voice_a, voice_b)
                # Small delay to be gentle with the API
                time.sleep(2)
        else:
            print("Select which of the newly added topics to use for TTS:")
            for i, t in enumerate(new_topics, 1):
                print(f" {i}. {t['title']}")
            choice = input("Enter a number: ").strip()
            try:
                c = int(choice)
                if 1 <= c <= len(new_topics):
                    tts_topic = new_topics[c - 1]
                else:
                    print("Invalid choice. Skipping TTS update.")
                    tts_topic = None
            except Exception:
                print("Invalid input. Skipping TTS update.")
                tts_topic = None
    else:
        tts_topic = new_topics[0]

    if tts_topic:
        # Single-topic flow using helper
        voice_a = input("Enter voiceName for speaker A (e.g., Charon): ").strip() or "Charon"
        voice_b = input("Enter voiceName for speaker B (e.g., Leda): ").strip() or "Leda"
        tts_for_topic(tts_topic, voice_a, voice_b)

    # 6) Seed topics in Django
    if prompt_yes_no("Run 'manage.py seed_speaking_topics' for this level using the project's venv?"):
        try:
            # Prefer venv Python if available
            py_cmd = resolve_venv_python() + ["manage.py", "seed_speaking_topics", "--level", level]
            result = subprocess.run(py_cmd, cwd=str(DJANGO_DIR), check=True)
        except Exception as e:
            print(f"Seeding failed: {e}")


if __name__ == "__main__":
    main()
