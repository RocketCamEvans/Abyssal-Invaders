# LLM Generation Evaluation Guide

## Overview

All LLM-generated content is automatically logged to `llm_generations.csv` in the root directory for manual evaluation and quality assessment.

## CSV Structure

The CSV file contains the following columns:

| Column | Description |
|--------|-------------|
| `timestamp` | When the generation occurred (YYYY-MM-DD HH:MM:SS) |
| `generation_type` | Type of content generated (see types below) |
| `model` | LLM model used (e.g., "gpt-3.5-turbo") |
| `temperature` | Temperature parameter used (0.0-1.0) |
| `max_tokens` | Maximum tokens requested |
| `character_count` | Actual character count of generated text |
| `generated_text` | The actual generated content |
| `prompt` | The prompt used (truncated to 200 chars if longer) |
| `fun_rating` | **EMPTY - For manual rating** |
| `within_character_limit` | **EMPTY - For manual evaluation** |

## Generation Types

The following generation types are logged:

- **`enemy_content`** - Enemy names and descriptions
- **`ally_content`** - Ally names and descriptions  
- **`room_content`** - Room names and descriptions
- **`battle_description`** - Combat encounter descriptions
- **`critical_hit`** - Critical hit flavor text
- **`combat_description`** - General combat descriptions

## Manual Evaluation Process

1. Open `llm_generations.csv` in Excel or Google Sheets
2. For each row, rate the following:

### Fun Rating
Rate 1-5 how engaging/fun/creative the generation is:
- **1** - Boring, generic, or inappropriate
- **2** - Somewhat bland, lacks creativity
- **3** - Acceptable, does the job
- **4** - Good, entertaining or creative
- **5** - Excellent, highly engaging and fun

### Within Character Limit
Evaluate if the generated text meets the character limit requirements:
- **YES** - Meets or is under the intended character limit
- **NO** - Exceeds the intended character limit
- **N/A** - No specific limit for this type

#### Character Limits by Type:
- **enemy_content**: Description should be ≤ 200 characters
- **battle_description**: Should be ≤ 200 characters  
- **critical_hit**: Should be ≤ 150 characters
- **ally_content**: No strict limit, but should be concise
- **room_content**: No strict limit, but 1-2 sentences
- **combat_description**: Should be brief (1-2 sentences)

## Using the Data

### Find Issues
Filter by:
- Low fun ratings (1-2) to identify boring generations
- "NO" in character limit to find prompt issues
- Specific generation types to evaluate consistency

### Improve Prompts
Use patterns in low-rated generations to:
1. Adjust temperature settings
2. Refine prompt instructions
3. Add more constraints or examples
4. Modify max_token limits

### Track Quality Over Time
- Compare different date ranges
- Test prompt changes and measure impact
- Identify which generation types need improvement

## Example Evaluation

```csv
timestamp,generation_type,model,temperature,max_tokens,character_count,generated_text,prompt,fun_rating,within_character_limit
2025-11-13 14:32:01,enemy_content,gpt-3.5-turbo,0.85,120,187,"{'name': 'Caffeinated Imp', 'description': 'A jittery demon powered by stolen coffee, zipping around with manic energy and hurling scalding espresso shots at intruders!'}","You are creating enemies for...",5,YES
2025-11-13 14:33:15,battle_description,gpt-3.5-turbo,0.8,60,156,"The Suited Vampire lunges with briefcase fangs bared as you dodge behind a toppled water cooler!","You are narrating a whimsical...",4,YES
```

## Notes

- The CSV is append-only - old entries are never deleted
- Thread-safe logging prevents data corruption during concurrent generations
- Long prompts are truncated to 200 characters in the log for readability
- All timestamps are in local server time
