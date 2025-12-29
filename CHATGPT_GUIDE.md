# ChatGPT Integration Guide

## Overview

HMATH AI now integrates ChatGPT to help you generate and optimize Python scripts for HWP (한글) automation.

## Features

### 1. **🤖 AI Generate**
Generate complete Python scripts based on natural language descriptions.

**How to use:**
1. Click the "🤖 AI Generate" button
2. Describe what you want the script to do
3. ChatGPT will generate a Python script automatically
4. Review and edit the generated code if needed
5. Click "Run" to execute

**Example prompts:**
- "처음에 '수학 문제'라는 제목을 입력하고, 그 아래에 이차방정식 공식을 LaTeX로 삽입해주세요"
- "학생 이름 목록을 입력받아서 각 이름마다 새로운 페이지를 생성하고 인사말을 추가해주세요"

### 2. **✨ AI Optimize**
Improve existing scripts with better code quality, efficiency, and readability.

**How to use:**
1. Write or load a script
2. Click the "✨ AI Optimize" button
3. (Optional) Provide optimization feedback
4. ChatGPT will optimize the script
5. Review the improved code

**Example feedback:**
- "Make the code more concise"
- "Add error handling"
- "Add comments explaining each step"

## Setup

### Prerequisites
- OpenAI API account (https://openai.com)
- Active API key with credits

### Configuration

#### Option 1: Environment Variable (Recommended)
```bash
# macOS/Linux
export OPENAI_API_KEY="sk-..."

# Windows (Command Prompt)
set OPENAI_API_KEY=sk-...

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-..."
```

Then restart the application.

#### Option 2: Code-based (Not recommended for production)
Modify the ChatGPTHelper initialization in your code to pass the API key directly.

### Installation

Install the required package:
```bash
pip install openai>=1.0.0
```

Or update all dependencies:
```bash
pip install -r requirements.txt
```

## Cost Considerations

- ChatGPT API uses OpenAI's GPT-3.5-turbo model
- Pricing depends on tokens used (input + output)
- Typical script generation: ~100-500 tokens (~$0.0001-0.0005)
- Check your usage and costs at https://platform.openai.com/account/usage

## Troubleshooting

### "ChatGPT API를 사용할 수 없습니다" Error

**Solutions:**
1. Check that OPENAI_API_KEY environment variable is set
2. Verify your API key is correct and not expired
3. Ensure you have credits in your OpenAI account
4. Restart the application after setting environment variables

### Generated scripts don't work

1. **Review the generated code** - ChatGPT may not perfectly understand context
2. **Provide more specific descriptions** - Be detailed about what you want
3. **Use example code** - Refer to the available functions:
   - `insert_text(text)` - Insert text
   - `insert_paragraph()` - Add paragraph break
   - `insert_equation(latex)` - Insert LaTeX equation
   - `insert_hwpeqn(hwpeqn)` - Insert HWP equation format
   - `insert_image(path)` - Insert image

### Slow responses

- OpenAI API calls may take a few seconds
- Network speed affects response time
- High traffic on OpenAI servers can cause delays
- Check your internet connection

## Best Practices

1. **Be specific in descriptions**
   - ❌ "Make a document"
   - ✅ "Create a document titled 'Math Problems' with 3 quadratic equations in LaTeX format"

2. **Test generated scripts**
   - Always review the code before running
   - Test on a non-critical document first

3. **Iterate and refine**
   - If the first attempt isn't perfect, refine and regenerate
   - Use "AI Optimize" to improve results

4. **Use templates as reference**
   - Check the template buttons to see example code
   - Use similar patterns in your descriptions

## Examples

### Example 1: Generate equation template
**Prompt:** "Create a script that writes the title 'Physics Formulas' and then inserts 5 important physics equations: E=mc², F=ma, P=IV, v=λf, and PV=nRT using LaTeX"

### Example 2: Optimize for clarity
**Code:**
```python
insert_text("Test\\r")
insert_paragraph()
insert_equation(r"x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}", font_size_pt=14.0)
```
**Feedback:** "Add comments and make it more readable"

## Limitations

- ChatGPT may occasionally generate imperfect code
- Complex automation logic may require manual refinement
- No real-time information (knowledge cutoff)
- Requires active internet connection

## Support

For issues or feature requests, visit: https://github.com/MisterKinn/hmath/issues
