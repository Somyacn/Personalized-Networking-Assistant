import random
from typing import List

# Global variable to cache the GPT-2 generator pipeline
_generator = None

def _get_generator():
    """Lazily load the Hugging Face GPT-2 generation pipeline."""
    global _generator
    if _generator is None:
        try:
            from transformers import pipeline
            _generator = pipeline(
                "text-generation",
                model="gpt2"
            )
        except Exception as e:
            print(f"Failed to load Hugging Face GPT-2 generator: {e}")
            print("Falling back to template-based generator.")
            _generator = None
    return _generator

def _generate_by_templates(themes: List[str], user_interests: str) -> List[str]:
    """Fallback template-based conversation starter generator.
    Produces clean, highly structured, and relevant prompts instantly.
    """
    interests_list = [i.strip() for i in user_interests.split(",") if i.strip()]
    if not interests_list:
        interests_list = ["building new connections", "learning about the industry"]
        
    theme_str = themes[0] if themes else "this event"
    
    starters = []
    
    # Template bank
    t1 = [
        "Hi! I'm interested in {interest}. How do you see that impacting the future of {theme}?",
        "Hey! Are you working on anything related to {interest} in the {theme} space?",
        "Hello! I'm here to learn more about {theme}. I'm particularly interested in {interest}—what's your take on that area?"
    ]
    t2 = [
        "Hi there! What's the most exciting development you've seen recently in {theme}?",
        "Hey! It's a great event. What's your primary focus when it comes to {interest}?",
        "Hello! I'm exploring the overlap of {theme} and {interest}. Have you seen any interesting projects here?"
    ]
    t3 = [
        "Hi! How are you finding the event so far? I'd love to hear your thoughts on {interest} in relation to {theme}.",
        "Hey, nice to meet you. I'm focusing on {interest}. What area of {theme} are you involved in?",
        "Hello! I'm trying to connect with others interested in {theme} and {interest}. What projects are keeping you busy lately?"
    ]
    
    # Pick randomly
    i1 = random.choice(interests_list)
    i2 = random.choice(interests_list)
    i3 = random.choice(interests_list)
    
    starters.append(random.choice(t1).format(theme=theme_str, interest=i1))
    starters.append(random.choice(t2).format(theme=theme_str, interest=i2))
    starters.append(random.choice(t3).format(theme=theme_str, interest=i3))
    
    # Clean duplicates if any
    unique_starters = []
    for s in starters:
        if s not in unique_starters:
            unique_starters.append(s)
            
    # Ensure exactly 3 starters
    while len(unique_starters) < 3:
        i_extra = random.choice(interests_list)
        unique_starters.append(f"Hi! What brings you to this event? I'm hoping to chat about {i_extra}.")
        
    return unique_starters[:3]

def generate_conversation_starters(
    event_description: str,
    user_interests: str,
    themes: List[str],
    mock: bool = False
) -> List[str]:
    """Generates 3 networking conversation starters using GPT-2 or templates.
    
    Args:
        event_description: Description of the event.
        user_interests: Comma-separated user interests.
        themes: Extracted themes.
        mock: If True, bypasses GPT-2 and uses template-based generator.
    """
    if mock:
        return _generate_by_templates(themes, user_interests)
        
    generator = _get_generator()
    if generator is None:
        return _generate_by_templates(themes, user_interests)
        
    theme_str = ", ".join(themes) if themes else "General Networking"
    
    # Few-shot prompting tailored for GPT-2
    prompt = (
        "Context: Networking Event\n"
        "Themes: Technology, Design\n"
        "Interests: AI, graphic design\n"
        "Conversation Starters:\n"
        "1. \"Hi there! I'm curious how you think AI is changing the landscape for graphic designers?\"\n"
        "2. \"Hey! I'm really passionate about AI integration in products. What's your view on AI tools in Design?\"\n"
        "3. \"Hello! Are you working on any projects that bridge the gap between creative design and tech?\"\n\n"
        f"Context: Networking Event\n"
        f"Themes: {theme_str}\n"
        f"Interests: {user_interests}\n"
        "Conversation Starters:\n"
        "1. \""
    )
    
    try:
        # GPT-2 text generation
        outputs = generator(
            prompt,
            max_new_tokens=120,
            num_return_sequences=1,
            temperature=0.85,
            top_k=50,
            top_p=0.95,
            do_sample=True,
            pad_token_id=50256  # GPT-2 EOS token
        )
        
        generated_text = outputs[0]["generated_text"]
        # Extract the suffix generated after our prompt
        generation_suffix = generated_text[len(prompt) - 4:]  # Include the "1. \""
        
        # Split into lines and look for lines starting with numbers
        starters = []
        for line in generation_suffix.split("\n"):
            line = line.strip()
            # Look for numbered items: 1. "Starter" or "Starter"
            cleaned_line = re.sub(r'^\d+\.\s*', '', line)  # remove number prefixes like "1." or "2."
            cleaned_line = cleaned_line.strip('"').strip("'").strip()
            if cleaned_line and len(cleaned_line) > 15: # Filter out short junk lines
                # Remove ending quotes if any
                cleaned_line = re.sub(r'^["\']|["\']$', '', cleaned_line).strip()
                if cleaned_line and cleaned_line not in starters:
                    starters.append(cleaned_line)
                    
        # Filter starters that look like starters (start with Hi, Hey, Hello, What, Is, etc.)
        valid_starters = [s for s in starters if any(s.lower().startswith(x) for x in ["hi", "hey", "hello", "what", "how", "are", "do", "is", "have", "with", "so", "nice"])]
        
        # If we got at least 2 starters, we can fill the 3rd. Otherwise fallback.
        if len(valid_starters) >= 2:
            while len(valid_starters) < 3:
                # Add a template starter
                temp_starters = _generate_by_templates(themes, user_interests)
                for ts in temp_starters:
                    if ts not in valid_starters:
                        valid_starters.append(ts)
                        break
            return valid_starters[:3]
            
        print("GPT-2 generated text lacked structure or was incomplete. Falling back to template generation.")
        return _generate_by_templates(themes, user_interests)
        
    except Exception as e:
        print(f"Error during GPT-2 generation: {e}")
        return _generate_by_templates(themes, user_interests)
