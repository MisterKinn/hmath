#!/usr/bin/env python3
"""
Quick diagnostic tool for macOS 한글 integration.
Run this to check if everything is set up correctly.
"""

import sys
import platform

def check_platform():
    """Check if we're on macOS."""
    system = platform.system()
    print(f"🖥️  Platform: {system}")
    if system != "Darwin":
        print("   ⚠️  This is not macOS. Use Windows version instead.")
        return False
    print("   ✅ macOS detected")
    return True

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"\n🐍 Python: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ Python 3.8+ required")
        return False
    print("   ✅ Python version OK")
    return True

def check_dependencies():
    """Check required Python packages."""
    print("\n📦 Dependencies:")
    
    packages = {
        "PySide6": ("PySide6", "GUI framework"),
        "openai": ("openai", "AI integration"),
        "python-dotenv": ("dotenv", "Environment variables")
    }
    
    all_ok = True
    for pkg_name, (import_name, desc) in packages.items():
        try:
            __import__(import_name)
            print(f"   ✅ {pkg_name:20} - {desc}")
        except ImportError:
            print(f"   ❌ {pkg_name:20} - {desc} (NOT INSTALLED)")
            all_ok = False
    
    return all_ok

def check_hwp_backend():
    """Check if HWP backend is available."""
    print("\n🔧 HWP Backend:")
    try:
        from backend.hwp.hwp_macos import HwpMacOS
        print("   ✅ macOS backend available")
        
        hwp = HwpMacOS()
        print(f"   📱 App name: {hwp._app_name}")
        
        is_running = hwp.is_running()
        if is_running:
            print("   ✅ 한글 is running")
        else:
            print("   ⚠️  한글 is not running")
            print("      → Open 한글 and create a document to use the app")
        
        return True
    except Exception as e:
        print(f"   ❌ Backend error: {e}")
        return False

def check_env_file():
    """Check .env file."""
    print("\n🔑 Environment:")
    import os
    from pathlib import Path
    
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"   ✅ .env file found")
        
        # Check for API key
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key.startswith("sk-"):
            print(f"   ✅ OpenAI API key configured")
        else:
            print(f"   ⚠️  OpenAI API key not found or invalid")
            print(f"      → Add OPENAI_API_KEY=sk-... to .env file")
    else:
        print(f"   ⚠️  .env file not found")
        print(f"      → Create .env file with OPENAI_API_KEY=sk-...")
    
    return True

def main():
    """Run all diagnostic checks."""
    print("=" * 50)
    print("Formulite - macOS Diagnostic Tool")
    print("=" * 50)
    
    checks = [
        check_platform,
        check_python_version,
        check_dependencies,
        check_hwp_backend,
        check_env_file
    ]
    
    all_passed = all(check() for check in checks)
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All checks passed!")
        print("\n🚀 Ready to run: ./start_macos.sh")
    else:
        print("❌ Some checks failed")
        print("\n📖 See MACOS_SETUP.md for detailed instructions")
    print("=" * 50)

if __name__ == "__main__":
    main()

