# Streaming Agent Example

> **Real-time streaming responses for better user experience**

---

## Overview

This example demonstrates how to implement streaming responses in AI agents, providing real-time feedback as tokens are generated.

**Why Streaming?**
- ✅ Immediate user feedback
- ✅ Better perceived performance
- ✅ More engaging user experience
- ✅ No waiting for complete response

---

## Features

🌊 **Real-Time Token Streaming** - See responses as they're generated  
⚡ **Instant Feedback** - No waiting for full responses  
🔧 **Streaming with Tool Calls** - Tools work seamlessly with streaming  
📊 **Progress Indicators** - Visual feedback during tool execution  
🎯 **Side-by-Side Comparison** - See streaming vs. blocking mode

---

## Prerequisites

- Python 3.10+
- OpenAI API key (**required** - streaming needs actual API calls)

---

## Setup

```bash
# 1. Navigate to example directory
cd examples/python-streaming

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

---

## Running the Example

```bash
python main.py
```

### What You'll See

```
🌊 Streaming Agent Demo
==========================================

Demo 1: Simple Question
==========================================
👤 YOU: Explain what AI agents are

🤖 AGENT: AI agents are software programs that can perceive their
environment, make decisions, and take actions to achieve specific
goals autonomously...
          ↑
          Tokens appear in real-time as generated!
```

---

## How Streaming Works

### Traditional (Blocking) Mode

```python
# User waits with no feedback
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Long question..."}],
    stream=False  # Wait for complete response
)

# Finally get response (could be 10-30 seconds later)
print(response.choices[0].message.content)
```

**User Experience:**
```
User: [asks question]
      ⏳ ⏳ ⏳ ⏳ ⏳ (waiting... no feedback)
Agent: [complete response appears]
```

### Streaming Mode

```python
# Start getting chunks immediately
stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Long question..."}],
    stream=True  # Get tokens as generated
)

# Process chunks as they arrive
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='', flush=True)
```

**User Experience:**
```
User: [asks question]
Agent: AI agents are [immediately starts appearing]
       software programs [tokens continue streaming]
       that can perceive... [user reading while more generates]
```

---

## Code Walkthrough

### 1. Basic Streaming

```python
response_stream = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
    stream=True  # Enable streaming!
)

# Process stream
for chunk in response_stream:
    delta = chunk.choices[0].delta
    
    if delta.content:
        # Print each token as it arrives
        print(delta.content, end='', flush=True)
```

**Key Points:**
- Set `stream=True`
- Iterate over response stream
- Access `delta.content` for each chunk
- Use `flush=True` for immediate display

---

### 2. Streaming with Tool Calls

Tool calls can also be streamed:

```python
tool_calls = []

for chunk in response_stream:
    delta = chunk.choices[0].delta
    
    # Collect streaming content
    if delta.content:
        print(delta.content, end='', flush=True)
    
    # Collect streaming tool calls
    if delta.tool_calls:
        for tool_call in delta.tool_calls:
            # Tool call data arrives in chunks too!
            # Build complete tool call from chunks
            ...
```

**Tool Call Streaming:**
- Function names arrive in chunks
- Arguments arrive character-by-character
- Reconstruct complete tool call before execution

---

### 3. Visual Indicators

Enhance UX with visual feedback:

```python
class StreamingDisplay:
    @staticmethod
    def show_spinner(message: str):
        """Show spinner during tool execution"""
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧']
        for frame in frames:
            print(f'\r{frame} {message}', end='', flush=True)
            time.sleep(0.1)
```

---

## When to Use Streaming

### ✅ Use Streaming When:

| Scenario | Why |
|----------|-----|
| **Long responses** | User doesn't wait with no feedback |
| **Chat interfaces** | More natural conversation flow |
| **Explanations/Essays** | User can start reading immediately |
| **Interactive apps** | Better perceived performance |
| **User-facing tools** | Professional, responsive feel |

### ❌ Don't Use Streaming When:

| Scenario | Why |
|----------|-----|
| **Background processing** | No user watching |
| **Batch operations** | No real-time requirements |
| **API integrations** | Other systems prefer complete responses |
| **Need complete response** | Can't process partial data |
| **Testing/debugging** | Easier to work with complete responses |

---

## Performance Comparison

### Perceived Performance

```
Blocking Mode:
└─ User waits 15s → Gets response → Total perceived wait: 15s

Streaming Mode:
└─ User sees first token at 0.5s → Reads while streaming → 
   Complete at 15s → Perceived wait: 0.5s!
```

**Result:** 30x better perceived performance!

### Actual Performance

Both modes take similar total time, but streaming:
- ✅ Starts showing results immediately
- ✅ Keeps user engaged
- ✅ Feels much faster
- ✅ Allows early termination if needed

---

## Advanced Patterns

### Pattern 1: Accumulate and Parse

```python
accumulated_response = []

for chunk in stream:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        accumulated_response.append(content)
        print(content, end='', flush=True)

# Parse complete response after streaming
full_response = ''.join(accumulated_response)
parsed_data = extract_data(full_response)
```

### Pattern 2: Progress Tracking

```python
total_tokens = 0

for chunk in stream:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        total_tokens += len(content.split())
        
        print(content, end='', flush=True)
        
        # Show progress
        if total_tokens % 20 == 0:
            print(f'\r[{total_tokens} tokens]', end='')
```

### Pattern 3: Early Termination

```python
max_tokens = 100
current_tokens = 0

for chunk in stream:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        print(content, end='', flush=True)
        
        current_tokens += len(content.split())
        
        if current_tokens >= max_tokens:
            break  # Stop streaming early
```

---

## Error Handling with Streaming

```python
try:
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end='', flush=True)
            
except Exception as e:
    print(f"\n❌ Streaming error: {e}")
    # Handle error gracefully
    # Maybe switch to non-streaming mode as fallback
```

**Key Points:**
- Errors can happen mid-stream
- Handle partial responses gracefully
- Consider fallback to non-streaming
- Always close stream properly

---

## Demos Included

### Demo 1: Simple Question
**Purpose:** Show basic streaming  
**What happens:** Simple question → streaming response  
**Focus:** Token-by-token generation

### Demo 2: Tool Usage
**Purpose:** Show streaming with tool calls  
**What happens:** Question → Tool execution → Streaming final response  
**Focus:** Tools work seamlessly with streaming

### Demo 3: Complex Task
**Purpose:** Show multi-step with streaming  
**What happens:** Complex task → Multiple tools → Detailed streaming response  
**Focus:** Streaming works for complex workflows

### Demo 4: Comparison
**Purpose:** Compare streaming vs. non-streaming  
**What happens:** Same question in both modes side-by-side  
**Focus:** See the UX difference

---

## Best Practices

### ✅ DO:

1. **Always use flush**
   ```python
   print(content, end='', flush=True)
   # flush=True ensures immediate display
   ```

2. **Show activity during tool calls**
   ```python
   print("🔧 Calling weather API...", end='', flush=True)
   result = call_weather_api()
   print(" ✅ Done")
   ```

3. **Handle errors mid-stream**
   ```python
   try:
       for chunk in stream:
           process(chunk)
   except Exception as e:
       print(f"\n⚠️  Stream interrupted: {e}")
   ```

4. **Provide visual feedback**
   ```python
   # Use spinners, progress bars, etc.
   show_spinner("Processing...")
   ```

### ❌ DON'T:

1. **Don't buffer unnecessarily**
   ```python
   # BAD: Defeats purpose of streaming
   chunks = list(stream)  # Waits for all chunks
   print(''.join(chunks))  # Then prints
   ```

2. **Don't forget error handling**
   ```python
   # BAD: Stream can break mid-response
   for chunk in stream:
       print(chunk.choices[0].delta.content)  # Could throw error!
   ```

3. **Don't use for batch processing**
   ```python
   # BAD: Streaming overhead with no benefit
   for item in 10000_items:
       stream_response(item)  # Use batch API instead
   ```

---

## Integration Examples

### Web Application (Flask)

```python
from flask import Flask, Response, stream_with_context

@app.route('/chat', methods=['POST'])
def chat():
    def generate():
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )
```

### Command Line (Rich Library)

```python
from rich.console import Console
from rich.live import Live

console = Console()

with Live(console=console) as live:
    response = []
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            response.append(chunk.choices[0].delta.content)
            live.update(''.join(response))
```

---

## Troubleshooting

### Issue: Chunks not appearing in real-time

**Solution:** Use `flush=True` in print
```python
print(content, end='', flush=True)  # Force immediate display
```

### Issue: Stream hangs or times out

**Solution:** Add timeout and error handling
```python
from openai import OpenAI, Timeout

try:
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True,
        timeout=30.0  # 30 second timeout
    )
except Timeout:
    print("Stream timed out")
```

### Issue: Tool calls incomplete

**Solution:** Accumulate tool call chunks properly
```python
# Tool calls stream in parts - must accumulate
tool_calls = []
for chunk in stream:
    if chunk.choices[0].delta.tool_calls:
        # Properly accumulate chunks
        update_tool_calls(tool_calls, chunk.choices[0].delta.tool_calls)
```

---

## Performance Tips

1. **Buffer size:** Don't print every single character
   ```python
   buffer = []
   for chunk in stream:
       buffer.append(chunk.choices[0].delta.content)
       if len(buffer) >= 5:  # Print every 5 chunks
           print(''.join(buffer), end='', flush=True)
           buffer = []
   ```

2. **Reduce network overhead:**
   ```python
   # Use faster model for streaming
   model="gpt-3.5-turbo"  # Faster than GPT-4
   ```

3. **Optimize tool calls:**
   ```python
   # Execute tools in parallel when possible
   import asyncio
   results = await asyncio.gather(*tool_calls)
   ```

---

## Learn More

- [OpenAI Streaming Guide](https://platform.openai.com/docs/api-reference/streaming)
- [Agent Architectures](../../docs/03-agent-architectures.md)
- [Error Handling Example](../python-error-handling/)

---

## Key Takeaways

✅ **Streaming = Better UX** - Users get immediate feedback  
✅ **Works with tools** - Tool calls can be streamed too  
✅ **Simple to implement** - Just set `stream=True`  
✅ **Use for user-facing** - Essential for chat/interactive apps  
✅ **Not for everything** - Batch processing doesn't need it

---

**Streaming transforms static responses into dynamic conversations!** 🌊

