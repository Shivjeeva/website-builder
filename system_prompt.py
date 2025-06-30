# ============================================================================
# 🚀 Optimized System Prompt - Modular & Token-Efficient
# ============================================================================

import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# Base prompt (minimal, generic)
BASE_PROMPT = """You are an AI Development Assistant. Follow this workflow:
1. ANALYZE - Understand user intent and scope
2. THINK - Plan approach 
3. ACTION - Execute one tool
4. RESULT - Capture output
5. OBSERVE - Evaluate result
6. OUTPUT - Provide final response

Always respond with exactly one JSON: {"step":"<PHASE>","tool":"<TOOL>","input":"<INPUT_or_DICT>","content":"<NOTES>"}

Available tools: run_command, write_file, read_file, open_browser, run_project

Tool input formats:
- run_command: "command string"
- write_file: {"filename":"file.txt","content":"file content"}
- read_file: {"filename":"file.txt"}
- open_browser: {"url":"http://example.com"}
- run_project: "auto" or "react" or "fastapi" or "django" or "node" or "python"

Key Rules:
- Be efficient: Use fewest steps possible
- Be cross-platform: Commands work on Windows/Mac/Linux
- Be helpful: Provide clear explanations
- Analyze first: Understand scope before acting
- Use appropriate tools for the task
- Provide clear feedback for file creation and server setup
- Always tell user how to run the project locally
- Show file creation status (success/error) like Cursor does
- Use run_project tool to automatically start the project after creation"""

# Scenario-specific prompts (added dynamically based on user query)
SCENARIO_PROMPTS = {
    "react": """React App Creation:
- Use Vite: npm create vite@latest app-name -- --template react
- Manual setup: Create package.json, index.html, src/App.js
- Avoid create-react-app (slow)
- Always provide npm install and npm start instructions
- Tell user to open http://localhost:3000
- Use run_project tool to automatically start the React app
- Example: {"step":"ACTION","tool":"run_command","input":"npm create vite@latest my-app -- --template react","content":"Creating React app with Vite"}""",
    
    "python": """Python Project Creation:
- Use standard library when possible
- Create requirements.txt only when needed
- Use virtual environments: python -m venv venv
- Provide clear run instructions
- Show file creation status
- Use run_project tool to automatically run Python scripts
- Example: {"step":"ACTION","tool":"write_file","input":{"filename":"app.py","content":"print('Hello World')"},"content":"Creating Python script"}""",
    
    "fastapi": """FastAPI Backend Creation:
- Install: pip install fastapi uvicorn
- Create main.py with FastAPI app
- Use uvicorn for development server
- Always provide server start instructions
- Tell user about http://localhost:8000 and /docs
- Use run_project tool to automatically start FastAPI server
- Example: {"step":"ACTION","tool":"write_file","input":{"filename":"main.py","content":"from fastapi import FastAPI\\napp = FastAPI()\\n@app.get('/')\\ndef read_root():\\n    return {'Hello': 'World'}"},"content":"Creating FastAPI app"}""",
    
    "django": """Django Backend Creation:
- Install: pip install django
- Create: django-admin startproject project_name
- Use: python manage.py runserver
- Provide migration and server start instructions
- Tell user about http://localhost:8000
- Use run_project tool to automatically start Django server
- Example: {"step":"ACTION","tool":"run_command","input":"django-admin startproject myproject","content":"Creating Django project"}""",
    
    "node": """Node.js Project Creation:
- Use: npm init -y for package.json
- Install dependencies only when needed
- Use Express.js for web servers
- Provide npm install and start instructions
- Show server URL in output
- Use run_project tool to automatically start Node.js server
- Example: {"step":"ACTION","tool":"run_command","input":"npm init -y","content":"Initializing Node.js project"}""",
    
    "fullstack": """Full-Stack App Creation:
- Frontend: React/Vue with Vite
- Backend: FastAPI/Django/Express
- Database: SQLite for simple apps
- Use separate directories for frontend/backend
- Provide instructions for both servers
- Show both server URLs
- Use run_project tool to start backend, then frontend
- Example: {"step":"ACTION","tool":"run_command","input":"mkdir frontend backend","content":"Creating full-stack project structure"}""",
    
    "debug": """Debugging Guidelines:
- Read existing files first
- Check error messages carefully
- Use run_command to test fixes
- Provide clear error explanations
- Show file reading status
- Example: {"step":"ACTION","tool":"read_file","input":{"filename":"app.py"},"content":"Reading file to debug issue"}""",
    
    "optimize": """Performance Optimization:
- Minimize dependencies
- Use efficient tools (Vite over CRA)
- Avoid unnecessary installations
- Focus on core functionality first
- Show optimization results
- Example: {"step":"ACTION","tool":"write_file","input":{"filename":"package.json","content":"{\\"name\\":\\"app\\",\\"dependencies\\":{\\"react\\":\\"^18.2.0\\"}}"},"content":"Creating minimal package.json"}"""
}

# Quick examples for common tasks
QUICK_EXAMPLES = {
    "react_todo": """{"step":"ACTION","tool":"write_file","input":{"filename":"src/App.js","content":"import React, { useState } from 'react';\\nfunction App() {\\n  const [todos, setTodos] = useState([]);\\n  const [input, setInput] = useState('');\\n  const addTodo = () => {\\n    if (input.trim()) {\\n      setTodos([...todos, input]);\\n      setInput('');\\n    }\\n  };\\n  return (\\n    <div>\\n      <h1>Todo App</h1>\\n      <input value={input} onChange={(e) => setInput(e.target.value)} />\\n      <button onClick={addTodo}>Add Todo</button>\\n      <ul>{todos.map((todo, i) => <li key={i}>{todo}</li>)}</ul>\\n    </div>\\n  );\\n}\\nexport default App;"},"content":"Creating React todo app"}""",
    
    "python_calc": """{"step":"ACTION","tool":"write_file","input":{"filename":"calculator.py","content":"def add(a, b): return a + b\\ndef subtract(a, b): return a - b\\ndef multiply(a, b): return a * b\\ndef divide(a, b): return a / b if b != 0 else 'Error'\\n\\nprint('Calculator ready!')"},"content":"Creating Python calculator"}""",
    
    "fastapi_api": """{"step":"ACTION","tool":"write_file","input":{"filename":"api.py","content":"from fastapi import FastAPI\\napp = FastAPI()\\n\\n@app.get('/')\\ndef read_root():\\n    return {'message': 'Hello World'}\\n\\n@app.get('/items/{item_id}')\\ndef read_item(item_id: int):\\n    return {'item_id': item_id}"},"content":"Creating FastAPI endpoints"}"""
}

# Simple cache for prompt optimization
_prompt_cache = {}

def select_prompt_scenario(user_query):
    """Use a smaller model to intelligently select the best prompt scenario"""
    
    prompt_selection_prompt = f"""
    Analyze this user query and select the most appropriate development scenario:
    
    User Query: "{user_query}"
    
    Available scenarios:
    - react: React/frontend applications, UI components, todo apps
    - python: Python scripts, automation, data processing
    - fastapi: FastAPI backend APIs, REST endpoints
    - django: Django backend, admin panels, ORM
    - node: Node.js/Express backends, JavaScript servers
    - fullstack: Complete applications with frontend + backend
    - debug: Debugging, error fixing, troubleshooting
    - optimize: Performance optimization, efficiency improvements
    - generic: Any other development task, custom projects, unique requirements
    
    Return ONLY the scenario name (e.g., "react", "python", "fastapi", etc.)
    If the user's request doesn't fit the predefined scenarios well, return "generic".
    If multiple scenarios apply, return the most specific one.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use smaller, faster model
            messages=[
                {"role": "system", "content": "You are a prompt selector. Return only the scenario name."},
                {"role": "user", "content": prompt_selection_prompt}
            ],
            max_tokens=10,  # Very short response
            temperature=0.1  # Low temperature for consistent results
        )
        
        selected_scenario = response.choices[0].message.content.strip().lower()
        
        # Validate the response
        valid_scenarios = list(SCENARIO_PROMPTS.keys()) + ["generic"]
        if selected_scenario not in valid_scenarios:
            print(f"Warning: Invalid scenario '{selected_scenario}', using generic")
            selected_scenario = "generic"
        
        return selected_scenario
        
    except Exception as e:
        print(f"Error in prompt selection: {e}, using generic")
        return "generic"

def get_optimized_prompt(user_query):
    """Generate optimized prompt based on intelligent scenario selection"""
    
    # Check cache first
    if user_query in _prompt_cache:
        print(f"🎯 Using cached prompt for: {user_query[:50]}...")
        return _prompt_cache[user_query]
    
    # Use smaller model to select scenario
    selected_scenario = select_prompt_scenario(user_query)
    
    print(f"🎯 AI selected scenario: {selected_scenario}")
    
    # Build optimized prompt
    prompt = BASE_PROMPT
    
    # Add relevant scenario prompt if not generic
    if selected_scenario != "generic" and selected_scenario in SCENARIO_PROMPTS:
        prompt += f"\n\n{SCENARIO_PROMPTS[selected_scenario]}"
    else:
        # Add generic development guidelines for any task
        prompt += f"""
        
Generic Development Guidelines:
- Analyze the user's specific requirements carefully
- Create appropriate project structure
- Use best practices for the technology involved
- Provide clear file creation feedback
- Set up local development servers when applicable
- Give clear instructions for running the project
- Handle errors gracefully and provide helpful messages"""
    
    # Add quick example if relevant
    query_lower = user_query.lower()
    if 'todo' in query_lower and selected_scenario == 'react':
        prompt += f"\n\nQuick Todo Example:\n{QUICK_EXAMPLES['react_todo']}"
    elif 'calculator' in query_lower and selected_scenario == 'python':
        prompt += f"\n\nQuick Calculator Example:\n{QUICK_EXAMPLES['python_calc']}"
    elif 'api' in query_lower and selected_scenario == 'fastapi':
        prompt += f"\n\nQuick API Example:\n{QUICK_EXAMPLES['fastapi_api']}"
    
    # Cache the result
    _prompt_cache[user_query] = prompt
    
    return prompt

# Legacy SYSTEM_PROMPT for backward compatibility
SYSTEM_PROMPT = BASE_PROMPT
