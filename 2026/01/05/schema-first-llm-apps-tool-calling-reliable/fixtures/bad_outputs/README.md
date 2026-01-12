# Bad Output Fixtures

This folder contains real examples of common LLM output failures. Use these to test your validation and repair logic.

## Files

- `trailing_comma.json` - JSON with trailing comma (common LLM mistake)
- `missing_field.json` - Missing required field (email)
- `wrong_type.json` - Wrong type (string instead of integer for priority)
- `invalid_enum.json` - Invalid enum value (not in allowed list)
- `extra_text.txt` - JSON wrapped in markdown code block with extra text
- `malformed.json` - Malformed JSON (missing closing brace)
- `invalid_email.json` - Invalid email format
- `out_of_range.json` - Value out of allowed range (priority > 5)

## Usage

```python
import json
from src.validator import extract_json, validate_output
from src.schemas import CustomerExtraction

# Load a bad output
with open("fixtures/bad_outputs/trailing_comma.json") as f:
    text = f.read()

# Try to extract and validate
data = extract_json(text)
if data:
    model, error = validate_output(data, CustomerExtraction)
    if error:
        print(f"Validation error: {error}")
```

## Testing Repair Logic

Use these fixtures to test that your repair loop can handle common failures:

```python
from src.repair_loop import repair_loop

def mock_llm_with_bad_output(prompt):
    # Return one of the bad outputs
    with open("fixtures/bad_outputs/trailing_comma.json") as f:
        return f.read()

result = repair_loop(
    "Extract customer info",
    CustomerExtraction,
    llm_call=mock_llm_with_bad_output,
    max_retries=2
)
```
