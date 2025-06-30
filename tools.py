import subprocess
import os
import platform
import webbrowser
import socket

# ============================================================================
# 🛠️ Essential Tools (Generic & Cross-Platform)
# ============================================================================

def run_command(command: str):
    """Execute any shell command cross-platform."""
    try:
        print(f"🚀 Executing: {command}")
        
        # Detect platform for helpful error messages
        is_windows = platform.system() == "Windows"
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout
        
        if result.stderr:
            output += f"\nError:\n{result.stderr}"
            
            # Provide helpful suggestions for common Windows issues
            if is_windows and "syntax of the command is incorrect" in result.stderr.lower():
                if "mkdir -p" in command:
                    output += "\n\n💡 Windows Tip: Try using individual mkdir commands instead of 'mkdir -p':"
                    output += "\n   Instead of: mkdir -p folder/subfolder"
                    output += "\n   Use: mkdir folder && mkdir folder\\subfolder"
                elif "touch" in command:
                    output += "\n\n💡 Windows Tip: Use 'echo. > filename' instead of 'touch filename':"
                    output += "\n   Instead of: touch file.txt"
                    output += "\n   Use: echo. > file.txt"
        
        # Check if command was successful
        if result.returncode == 0:
            print(f"✅ Command executed successfully")
            if "npm start" in command or "python manage.py runserver" in command or "uvicorn" in command:
                print(f"🌐 Server should be running! Check the output above for the local URL.")
        else:
            print(f"⚠️  Command completed with return code: {result.returncode}")
        
        return output
    except Exception as e:
        error_msg = f"❌ Exception: {str(e)}"
        print(error_msg)
        return error_msg

def read_file(filename: str):
    """Read and return the content of a file."""
    try:
        print(f"📖 Reading file: {filename}")
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_size = len(content)
        print(f"✅ Read file: {filename} ({file_size} characters)")
        
        return f"📄 File '{filename}' content ({file_size} characters):\n{content}"
    except Exception as e:
        error_msg = f"❌ Error reading '{filename}': {str(e)}"
        print(error_msg)
        return error_msg

def write_file(filename: str, content: str):
    """Write or overwrite content in a file."""
    try:
        # Ensure directory exists (only if there's a directory path)
        directory = os.path.dirname(filename)
        if directory:  # Only create directory if there's a path
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created directory: {directory}")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Get file size for feedback
        file_size = os.path.getsize(filename)
        print(f"✅ Created file: {filename} ({file_size} bytes)")
        
        return f"✅ Successfully created '{filename}' ({file_size} bytes)"
    except Exception as e:
        error_msg = f"❌ Error creating '{filename}': {str(e)}"
        print(error_msg)
        return error_msg

def open_browser(url: str):
    """Open a URL in the default browser."""
    try:
        print(f"🌐 Opening browser: {url}")
        webbrowser.open(url)
        print(f"✅ Opened {url} in browser")
        return f"✅ Opened {url} in browser"
    except Exception as e:
        error_msg = f"❌ Error opening URL: {str(e)}"
        print(error_msg)
        return error_msg

def run_project(project_type: str = "auto"):
    """Automatically detect and run the project based on its type"""
    try:
        print(f"🚀 Attempting to run project (type: {project_type})")
        
        # Auto-detect project type if not specified
        if project_type == "auto":
            project_type = detect_project_type()
        
        if project_type == "react":
            return run_react_project()
        elif project_type == "fastapi":
            return run_fastapi_project()
        elif project_type == "django":
            return run_django_project()
        elif project_type == "node":
            return run_node_project()
        elif project_type == "python":
            return run_python_project()
        else:
            return "❌ Unknown project type. Please specify: react, fastapi, django, node, python"
            
    except Exception as e:
        error_msg = f"❌ Error running project: {str(e)}"
        print(error_msg)
        return error_msg

def detect_project_type():
    """Auto-detect project type based on files in current directory"""
    try:
        if os.path.exists("package.json"):
            with open("package.json", "r") as f:
                content = f.read()
                if "react" in content.lower() or "vite" in content.lower():
                    return "react"
                else:
                    return "node"
        elif os.path.exists("requirements.txt"):
            with open("requirements.txt", "r") as f:
                content = f.read()
                if "fastapi" in content.lower():
                    return "fastapi"
                elif "django" in content.lower():
                    return "django"
                else:
                    return "python"
        elif os.path.exists("manage.py"):
            return "django"
        elif os.path.exists("main.py") or os.path.exists("app.py"):
            return "python"
        else:
            return "unknown"
    except Exception as e:
        print(f"⚠️  Error detecting project type: {e}")
        return "unknown"

def run_react_project():
    """Run a React project"""
    try:
        print("⚛️  Running React project...")
        
        # Check if node_modules exists, if not install dependencies
        if not os.path.exists("node_modules"):
            print("📦 Installing dependencies...")
            result = subprocess.run("npm install", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return f"❌ Failed to install dependencies: {result.stderr}"
        
        # Start the development server
        print("🌐 Starting React development server...")
        result = subprocess.run("npm start", shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return "✅ React project started successfully! Open http://localhost:3000 in your browser"
        else:
            return f"❌ Failed to start React project: {result.stderr}"
            
    except Exception as e:
        return f"❌ Error running React project: {str(e)}"

def run_fastapi_project():
    """Run a FastAPI project"""
    try:
        print("🚀 Running FastAPI project...")
        
        # Check if main.py exists
        if not os.path.exists("main.py"):
            return "❌ main.py not found. Please ensure FastAPI app is in main.py"
        
        # Install dependencies if needed
        print("📦 Installing FastAPI dependencies...")
        result = subprocess.run("pip install fastapi uvicorn", shell=True, capture_output=True, text=True)
        
        # Start the server
        print("🌐 Starting FastAPI server...")
        result = subprocess.run("uvicorn main:app --reload", shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return "✅ FastAPI project started successfully! Open http://localhost:8000 in your browser"
        else:
            return f"❌ Failed to start FastAPI project: {result.stderr}"
            
    except Exception as e:
        return f"❌ Error running FastAPI project: {str(e)}"

def run_django_project():
    """Run a Django project"""
    try:
        print("🐍 Running Django project...")
        
        # Check if manage.py exists
        if not os.path.exists("manage.py"):
            return "❌ manage.py not found. Please ensure this is a Django project"
        
        # Install Django if needed
        print("📦 Installing Django...")
        result = subprocess.run("pip install django", shell=True, capture_output=True, text=True)
        
        # Run migrations
        print("🔄 Running migrations...")
        result = subprocess.run("python manage.py migrate", shell=True, capture_output=True, text=True)
        
        # Start the server
        print("🌐 Starting Django server...")
        result = subprocess.run("python manage.py runserver", shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return "✅ Django project started successfully! Open http://localhost:8000 in your browser"
        else:
            return f"❌ Failed to start Django project: {result.stderr}"
            
    except Exception as e:
        return f"❌ Error running Django project: {str(e)}"

def run_node_project():
    """Run a Node.js project"""
    try:
        print("🟢 Running Node.js project...")
        
        # Check if package.json exists
        if not os.path.exists("package.json"):
            return "❌ package.json not found. Please ensure this is a Node.js project"
        
        # Install dependencies if needed
        if not os.path.exists("node_modules"):
            print("📦 Installing dependencies...")
            result = subprocess.run("npm install", shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                return f"❌ Failed to install dependencies: {result.stderr}"
        
        # Start the project
        print("🌐 Starting Node.js project...")
        result = subprocess.run("npm start", shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return "✅ Node.js project started successfully! Check console output for server URL"
        else:
            return f"❌ Failed to start Node.js project: {result.stderr}"
            
    except Exception as e:
        return f"❌ Error running Node.js project: {str(e)}"

def run_python_project():
    """Run a Python project"""
    try:
        print("🐍 Running Python project...")
        
        # Look for main Python files
        python_files = ["main.py", "app.py", "run.py", "server.py"]
        main_file = None
        
        for file in python_files:
            if os.path.exists(file):
                main_file = file
                break
        
        if not main_file:
            return "❌ No main Python file found (main.py, app.py, run.py, server.py)"
        
        # Run the Python file
        print(f"🚀 Running {main_file}...")
        result = subprocess.run(f"python {main_file}", shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return f"✅ Python project ({main_file}) started successfully!"
        else:
            return f"❌ Failed to run Python project: {result.stderr}"
            
    except Exception as e:
        return f"❌ Error running Python project: {str(e)}"

# ============================================================================
# Tool Registry (Simplified)
# ============================================================================

TOOL_REGISTRY = {
    "run_command": run_command,      # Execute any shell command
    "read_file": read_file,          # Read file contents
    "write_file": write_file,        # Write file contents
    "open_browser": open_browser,    # Open URL in browser
    "run_project": run_project,      # Auto-run project
}

# Example usage
if __name__ == "__main__":
    # Test the simplified tools
    print("Testing simplified tools...")
    print(write_file("test.txt", "Hello World"))
    print(read_file("test.txt"))
    print(run_command("dir" if platform.system() == "Windows" else "ls"))
    print(run_command("echo Hello from command"))
