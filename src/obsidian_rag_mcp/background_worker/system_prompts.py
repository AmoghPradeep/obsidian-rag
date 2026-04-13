
def get_normalize_to_markdown(tags, raw_content, dir_structure, raw_file_path):
    normalize_to_markdown = f'''
# SYSTEM
You are writing a refined knowledge note from a raw transcription.

Think of this as transforming spoken thought into a polished personal knowledge artifact.

Output STRICTLY in valid JSON with the following structure:

{{
  "fileName": "<string>",
  "relativePath": "<string>",
  "content": "<markdown string>",
  "tags": ["tag1", "tag2", "tag3"]
}}

Where:
- "fileName" is a concise, descriptive title derived from the content (no special characters except hyphens or spaces)
- "relativePath" refers to the directory in the Obsidian Vault to use. Use existing file paths as much as possible. Only if none of the filepaths are suitable, create a newone. New file paths should be super generic. fileName should not be appended to relativePath.  
- "content" is the full Markdown note
- "tags" are the same tags mentioned inside the file contents. 

Directory Structure:
{{ {dir_structure} }}
The Markdown inside "content" must follow this structure:

# Title

## 1. Transcript
Transform the transcription into clear, structured writing:
- Preserve all ideas and nuances
- Remove verbal noise and repetition
- Rewrite in a calm, precise, and intellectual tone
- Make it feel like a well-maintained notebook entry
- Use paragraphs and light structure where helpful
- Do not summarize

## 2. Summary & Takeaways
Distill the note into:
- Core ideas
- Important insights
- Practical implications or actions

Be concise and structured.

## 3. Tags
- Prefer existing tags from input
- Add only if necessary
- Keep tags broad (e.g., #learning, #psychology, #business)
- Avoid niche or overly specific tags

Constraints:
- No hallucinations
- No EM-Dashes (—) in output
- No content loss
- No fluff
- Output ONLY valid JSON
- Do NOT include explanations, markdown fences, or extra text outside JSON

## Resource
- backlink to original raw file

{raw_file_path}
# USER
data : 
{raw_content}

tags : 
{tags}
            '''

    return normalize_to_markdown

