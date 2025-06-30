import json
import re
from dotenv import load_dotenv
from openai import OpenAI
from system_prompt import get_optimized_prompt, SYSTEM_PROMPT
from tools import TOOL_REGISTRY

load_dotenv()

client = OpenAI()

def parse_json_response(response_text):
    """Parse JSON response from OpenAI, handling potential formatting issues"""
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response text: {response_text}")
        return None

def validate_command(command):
    """Validate command to prevent complex, potentially problematic commands"""
    if not isinstance(command, str):
        return True  # Not a string command, let it pass
    
    # Check for overly complex commands
    if command.count('&&') > 2:
        print(f"⚠️  Warning: Complex command detected with {command.count('&&')} operators")
        return False
    
    # Check for very long commands
    if len(command) > 200:
        print(f"⚠️  Warning: Very long command detected ({len(command)} characters)")
        return False
    
    # Check for potentially dangerous patterns
    dangerous_patterns = [
        'rm -rf',
        'del /s /q',
        'format',
        'chmod 777'
    ]
    
    for pattern in dangerous_patterns:
        if pattern in command.lower():
            print(f"⚠️  Warning: Potentially dangerous command detected: {pattern}")
            return False
    
    return True

def execute_tool(tool_name, input_data):
    """Execute the specified tool with given input"""
    if tool_name not in TOOL_REGISTRY:
        return f"Tool '{tool_name}' not found. Available tools: {list(TOOL_REGISTRY.keys())}"
    
    tool_function = TOOL_REGISTRY[tool_name]
    
    try:
        print(f"🔧 Executing {tool_name} with input: {input_data} (type: {type(input_data)})")
        
        # Validate commands before execution
        if tool_name == "run_command" and isinstance(input_data, str):
            if not validate_command(input_data):
                return f"❌ Command validation failed: Command too complex or potentially dangerous"
        
        # Handle different input formats
        if isinstance(input_data, dict):
            # For tools that expect multiple parameters
            print(f"📝 Using dict unpacking: {input_data}")
            result = tool_function(**input_data)
        elif isinstance(input_data, str):
            # For tools that expect a single string parameter
            print(f"📝 Using string parameter: {input_data}")
            result = tool_function(input_data)
        else:
            # For tools that expect a single parameter of other types
            print(f"📝 Using direct parameter: {input_data}")
            result = tool_function(input_data)
        
        return result
    except Exception as e:
        error_msg = f"Error executing tool '{tool_name}': {str(e)}"
        print(f"❌ {error_msg}")
        print(f"   Tool function: {tool_function}")
        print(f"   Input data: {input_data}")
        print(f"   Input type: {type(input_data)}")
        return error_msg

def summarize_steps(conversation_history, user_query):
    """Summarize multiple steps into a single step to optimize token usage"""
    summary_prompt = f"""
    Analyze the conversation history and create a simple, reliable single step to complete the task.
    
    User Query: {user_query}
    
    Conversation History:
    {json.dumps(conversation_history, indent=2)}
    
    IMPORTANT RULES:
    1. Create SIMPLE, SINGLE commands - avoid complex multi-step commands with && operators
    2. Focus on the most essential step to move the task forward
    3. Use write_file for creating files, run_command for simple commands
    4. Avoid trying to do everything in one command
    
    Return in JSON format:
    {{"step":"SUMMARY","tool":"tool_name","input":"simple_input","content":"description"}}
    
    Available tools: {list(TOOL_REGISTRY.keys())}
    
    Examples of GOOD inputs:
    - run_command: "npm create vite@latest my-app -- --template react"
    - write_file: {{"filename":"app.py","content":"print('Hello')"}}
    - run_command: "mkdir my-project"
    
    Examples of BAD inputs (avoid these):
    - run_command: "npm create vite@latest frontend -- --template react && cd frontend && npm install && npm install -D tailwindcss postcss autoprefixer && echo 'config' > postcss.config.js"
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are an efficient task optimizer. Create simple, reliable single steps. Avoid complex multi-step commands."},
                {"role": "user", "content": summary_prompt}
            ]
        )
        
        return parse_json_response(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in summarization: {e}")
        return None

def process_user_query(user_query, conversation_history=None):
    """Process user query step by step until OUTPUT is reached"""
    if conversation_history is None:
        conversation_history = []
    
    # Get optimized prompt based on user query (ONLY ONCE at the beginning)
    print("🎯 Analyzing user query and selecting optimal prompt...")
    optimized_prompt = get_optimized_prompt(user_query)
    print("✅ Prompt optimization complete!")
    
    messages = [
        {"role": "system", "content": optimized_prompt},
        *conversation_history,
        {"role": "user", "content": user_query}
    ]
    
    step_count = 0
    max_steps = 30  # Increased to prevent premature stopping
    steps_to_summarize = 10  # Threshold for summarization
    
    while step_count < max_steps:
        try:
            # Check if we need to summarize steps
            if step_count >= steps_to_summarize and step_count % steps_to_summarize == 0:
                print(f"\n🔄 Summary of last {steps_to_summarize} steps - Creating a simple, efficient step...")
                
                # Create summary of current conversation
                current_conversation = messages[1:]  # Exclude system prompt
                summarized_step = summarize_steps(current_conversation, user_query)
                
                if summarized_step:
                    print(f"📝 Created SUMMARY step: {summarized_step}")
                    
                    # Execute the summarized step
                    step = summarized_step.get("step", "").upper()
                    tool = summarized_step.get("tool", "")
                    input_data = summarized_step.get("input", "")
                    content = summarized_step.get("content", "")
                    
                    if step == "SUMMARY" and tool:
                        print(f"\n🚀 Executing summary step: {tool}")
                        result = execute_tool(tool, input_data)
                        print(f"✅ Summary step completed: {result}")
                        
                        # Add summarized result to conversation
                        summarized_message = {
                            "role": "assistant", 
                            "content": json.dumps(summarized_step)
                        }
                        messages.append(summarized_message)
                        
                        tool_result_message = {
                            "role": "user", 
                            "content": f"Summary of last {steps_to_summarize} steps completed successfully. Result: {result}"
                        }
                        messages.append(tool_result_message)
                        
                        # Continue with normal workflow instead of forcing OUTPUT
                        print(f"🔄 Continuing with normal workflow...")
                        step_count += 1
                        continue
                    else:
                        print(f"⚠️  Invalid summarized step, continuing normally...")
                else:
                    print(f"⚠️  Failed to create summarized step, continuing normally...")
            
            # Get response from OpenAI (using the same optimized prompt throughout)
            response = client.chat.completions.create(
                model="gpt-4.1",
                response_format={"type": "json_object"},
                messages=messages
            )
            
            response_content = response.choices[0].message.content
            print(f"\n--- Step {step_count + 1} ---")
            print(f"AI Response: {response_content}")
            
            # Parse the JSON response
            parsed_response = parse_json_response(response_content)
            if not parsed_response:
                print("Failed to parse response, stopping...")
                break
            
            # Add AI response to conversation
            messages.append({"role": "assistant", "content": response_content})
            
            # Check the step
            step = parsed_response.get("step", "").upper()
            tool = parsed_response.get("tool", "")
            input_data = parsed_response.get("input", "")
            content = parsed_response.get("content", "")
            
            print(f"Step: {step}")
            print(f"Tool: {tool}")
            print(f"Input: {input_data}")
            print(f"Content: {content}")
            
            # If it's an ACTION step, execute the tool
            if step == "ACTION" and tool:
                print(f"\nExecuting tool: {tool}")
                result = execute_tool(tool, input_data)
                print(f"Tool result: {result}")
                
                # Add tool result to conversation
                tool_result_message = {
                    "role": "user", 
                    "content": f"Tool '{tool}' executed with input '{input_data}'. Result: {result}"
                }
                messages.append(tool_result_message)
            
            # If it's OUTPUT step, we're done
            elif step == "OUTPUT":
                print(f"\n✅ Task completed! Final output: {content}")
                
                # Add server instructions if relevant
                server_instructions = get_server_instructions(user_query, conversation_history)
                if server_instructions:
                    print(f"\n🚀 {server_instructions}")
                
                # Update conversation history for next query
                conversation_history.extend([
                    {"role": "user", "content": user_query},
                    {"role": "assistant", "content": response_content}
                ])
                return True, conversation_history
            
            step_count += 1
            
        except Exception as e:
            print(f"Error in step {step_count + 1}: {e}")
            break
    
    if step_count >= max_steps:
        print("Maximum steps reached, stopping...")
    
    return False, conversation_history

def show_available_tools():
    """Display all available tools to the user"""
    print("\n��️ Available Tools (Enhanced):")
    print("=" * 50)
    
    tools_info = {
        "run_command": "Execute any shell command (cross-platform)",
        "write_file": "Write content to a file",
        "read_file": "Read file contents", 
        "open_browser": "Open URL in browser",
        "run_project": "Automatically detect and run any project (React, FastAPI, Django, Node.js, Python)"
    }
    
    for tool, description in tools_info.items():
        print(f"  • {tool}: {description}")
    
    print("\n💡 These 5 tools can handle any development task efficiently!")
    print("🚀 The run_project tool automatically detects and starts your project!")

def get_server_instructions(user_query, conversation_history):
    """Generate server instructions based on the project type and conversation history"""
    
    query_lower = user_query.lower()
    
    # Check for React/frontend projects
    if any(word in query_lower for word in ['react', 'frontend', 'ui', 'component', 'todo']):
        return """Your React app is ready! To run it:
1. Navigate to your project directory
2. Run: npm install (if not already done)
3. Run: npm start
4. Open http://localhost:3000 in your browser"""
    
    # Check for Python/FastAPI projects
    elif any(word in query_lower for word in ['fastapi', 'api', 'backend']):
        return """Your FastAPI backend is ready! To run it:
1. Navigate to your project directory
2. Run: pip install fastapi uvicorn
3. Run: uvicorn main:app --reload
4. Open http://localhost:8000 in your browser
5. API docs at http://localhost:8000/docs"""
    
    # Check for Django projects
    elif any(word in query_lower for word in ['django', 'admin']):
        return """Your Django project is ready! To run it:
1. Navigate to your project directory
2. Run: pip install django
3. Run: python manage.py migrate
4. Run: python manage.py runserver
5. Open http://localhost:8000 in your browser"""
    
    # Check for Node.js projects
    elif any(word in query_lower for word in ['node', 'express', 'javascript']):
        return """Your Node.js project is ready! To run it:
1. Navigate to your project directory
2. Run: npm install
3. Run: npm start (or node app.js)
4. Check the console output for the server URL"""
    
    # Check for full-stack projects
    elif any(word in query_lower for word in ['fullstack', 'full-stack', 'both frontend and backend']):
        return """Your full-stack app is ready! To run it:
1. Backend: Navigate to backend directory and run the server
2. Frontend: Navigate to frontend directory and run npm start
3. Check the console output for server URLs"""
    
    # Check for Python scripts
    elif any(word in query_lower for word in ['python', 'script', 'calculator']):
        return """Your Python script is ready! To run it:
1. Navigate to your project directory
2. Run: python your_script.py
3. Check the console output for results"""
    
    # Generic instructions
    else:
        return """Your project is ready! Check the files created above and run the appropriate commands to start your application."""

def main():
    """Main function to handle user interaction"""
    print("🤖 AI Development Assistant - Optimized Task Processor")
    print("=" * 60)
    print("💡 Workflow: ANALYZE → THINK → ACTION → RESULT → OBSERVE → OUTPUT")
    print("💡 Token optimization: AI-powered prompt selection + step summarization")
    print("💡 Smart summarization: Summary of last 10 steps (SUMMARY step)")
    print("💡 Type 'tools' to see all available tools")
    print("💡 Type 'quit' to exit")
    
    conversation_history = []
    
    while True:
        # Get user query
        user_query = input("\n💬 Enter your query: ").strip()
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if user_query.lower() == 'tools':
            show_available_tools()
            continue
        
        if not user_query:
            print("Please enter a valid query.")
            continue
        
        print(f"\n🔄 Processing: {user_query}")
        print("=" * 60)
        
        # Process the query
        success, conversation_history = process_user_query(user_query, conversation_history)
        
        if success:
            print("\n🎉 Task completed successfully!")

if __name__ == "__main__":
    main()






