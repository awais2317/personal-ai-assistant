"""
Personal AI Assistant Startup Script

This script helps you set up and run your personal AI assistant.
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Set up the environment for the AI assistant"""
    print("🤖 Personal AI Assistant Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("📝 Creating .env file from template...")
        
        # Copy from .env.example
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ .env file created from template")
        else:
            print("❌ .env.example file not found")
            return False
    
    # Check OpenAI API key
    from dotenv import load_dotenv
    load_dotenv()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or openai_key == "your_openai_api_key_here":
        print("\n⚠️  OpenAI API Key Required!")
        print("To use this AI assistant, you need an OpenAI API key.")
        print("\n📋 Steps to get your API key:")
        print("1. Go to https://platform.openai.com/api-keys")
        print("2. Log in or create an account")
        print("3. Click 'Create new secret key'")
        print("4. Copy the key and paste it below")
        
        new_key = input("\n🔑 Enter your OpenAI API key: ").strip()
        
        if new_key:
            # Update .env file
            with open(".env", "r") as f:
                content = f.read()
            
            content = content.replace(
                "OPENAI_API_KEY=your_openai_api_key_here",
                f"OPENAI_API_KEY={new_key}"
            )
            
            with open(".env", "w") as f:
                f.write(content)
            
            print("✅ OpenAI API key saved to .env file")
        else:
            print("❌ No API key provided. The assistant will not work without it.")
            return False
    else:
        print("✅ OpenAI API key found")
    
    # Create necessary directories
    for directory in ["uploads", "data", "templates", "static"]:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directory structure created")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    # Map package names to their import names
    package_imports = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn", 
        "openai": "openai",
        "streamlit": "streamlit",
        "pandas": "pandas",
        "numpy": "numpy",
        "python-dotenv": "dotenv"
    }
    
    missing_packages = []
    
    for package_name, import_name in package_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Install them with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All required packages are installed")
    return True

def start_services():
    """Start the AI assistant services"""
    print("\n🚀 Starting Personal AI Assistant...")
    print("=" * 50)
    
    print("📖 Available interfaces:")
    print("• API Server: http://localhost:8000")
    print("• API Documentation: http://localhost:8000/docs")
    print("• Web Interface: http://localhost:8501")
    
    choice = input("\n❓ What would you like to start?\n1. API Server only\n2. Web Interface only\n3. Both (recommended)\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        start_api_server()
    elif choice == "2":
        start_web_interface()
    elif choice == "3":
        print("\n🔄 Starting both services...")
        print("💡 Tip: The API server will start first, then the web interface in a new window")
        input("Press Enter to continue...")
        start_api_server(background=True)
        start_web_interface()
    else:
        print("❌ Invalid choice. Starting web interface by default...")
        start_web_interface()

def start_api_server(background=False):
    """Start the FastAPI server"""
    print("\n🌐 Starting API Server...")
    
    if background:
        import subprocess
        import sys
        subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ])
        print("✅ API Server started in background")
    else:
        os.system(f"{sys.executable} -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")

def start_web_interface():
    """Start the Streamlit web interface"""
    print("\n🖥️  Starting Web Interface...")
    print("💡 Your browser should open automatically")
    print("📱 If not, go to: http://localhost:8501")
    
    os.system(f"{sys.executable} -m streamlit run streamlit_app.py")

def main():
    """Main startup function"""
    print("🎯 Personal AI Assistant for Document Analysis & Business Intelligence")
    print("📄 Supports: XLS, Word, PDF files | 💼 Business analytics | 🎓 Research assistant")
    print()
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Setup failed. Please check the errors above")
        sys.exit(1)
    
    # Start services
    start_services()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Thanks for using Personal AI Assistant")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("💡 Try running the script again or check the error message above")
