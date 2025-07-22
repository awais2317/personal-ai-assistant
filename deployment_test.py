"""
Quick deployment test script
Run this to verify your app is ready for deployment
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking deployment requirements...")
    
    issues = []
    
    # Check for required files
    required_files = [
        "app.py",
        "requirements.txt",
        ".streamlit/config.toml",
        ".streamlit/secrets.toml"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            issues.append(f"❌ Missing file: {file}")
        else:
            print(f"✅ Found: {file}")
    
    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        issues.append("❌ OpenAI API key not configured")
    else:
        print("✅ OpenAI API key configured")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 8:
        print(f"✅ Python version: {python_version.major}.{python_version.minor}")
    else:
        issues.append(f"❌ Python version {python_version.major}.{python_version.minor} not supported")
    
    return issues

def test_imports():
    """Test if all modules can be imported"""
    print("\n🧪 Testing imports...")
    
    issues = []
    modules_to_test = [
        "streamlit",
        "openai",
        "chromadb",
        "sentence_transformers",
        "pandas",
        "numpy"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            issues.append(f"❌ Cannot import {module}: {e}")
    
    return issues

def main():
    """Main test function"""
    print("🚀 Personal AI Assistant - Deployment Check\n")
    
    # Check requirements
    req_issues = check_requirements()
    
    # Test imports
    import_issues = test_imports()
    
    # Summary
    print("\n📋 Summary:")
    total_issues = len(req_issues) + len(import_issues)
    
    if total_issues == 0:
        print("🎉 All checks passed! Your app is ready for deployment.")
        print("\n🚀 Quick Deploy Steps:")
        print("1. Push code to GitHub")
        print("2. Go to share.streamlit.io")
        print("3. Connect your repo")
        print("4. Set main file: app.py")
        print("5. Add OpenAI API key to secrets")
        print("6. Deploy!")
    else:
        print(f"⚠️  Found {total_issues} issues that need to be fixed:")
        for issue in req_issues + import_issues:
            print(f"   {issue}")
        print("\nPlease fix these issues before deploying.")

if __name__ == "__main__":
    main()
