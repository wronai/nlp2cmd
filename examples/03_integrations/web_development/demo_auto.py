#!/usr/bin/env python3
"""
Demo with automatic deployment and testing.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

sys.path.append(str(Path(__file__).resolve().parents[2]))

from _example_helpers import print_separator

from nlp2cmd_web_controller import NLP2CMDWebController


async def run_demo_with_test(interactive=False):
    """Run demo with automatic deployment and testing."""
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║     🚀 NLP2CMD Web Examples - Auto Demo & Test                      ║")
    print("║                                                                      ║")
    print("║     Natural Language → DevOps Configuration + Testing               ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    mode = "Interaktywny" if interactive else "Automatyczny"
    print_separator(f"🤖 NLP2CMD - Tryb {mode}", leading_newline=True, width=70)
    
    # Clean up any existing files
    import shutil
    if Path("./generated").exists():
        shutil.rmtree("./generated")
    
    # Initialize controller
    controller = NLP2CMDWebController(output_dir="./generated")
    
    # Default command
    command = "Uruchom serwis czatu na porcie 8080"
    
    print(f"\n📝 Domyślne polecenie: '{command}'")
    print("⚙️ Przetwarzanie...")
    print("-" * 50)
    
    # Execute command
    result = await controller.execute(command)
    
    print(f"\n📊 Status: {result.get('status')}")
    print(f"💬 {result.get('message')}")
    
    if result.get('config'):
        print("\n⚙️ Konfiguracja:")
        for key, value in result['config'].items():
            if key == 'env_vars':
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"     {k}: {v}")
            else:
                print(f"   {key}: {value}")
    
    if result.get('files_saved'):
        print("\n💾 Zapisane pliki:")
        for file_type, file_path in result['files_saved'].items():
            print(f"   📄 {file_type}: {file_path}")
    
    # Show Docker execution results
    if result.get('docker_execution'):
        docker_result = result['docker_execution']
        print(f"\n🐳 Docker: {docker_result.get('message', 'Unknown')}")
        
        if docker_result.get('status') == 'success':
            # Show container status
            if result.get('containers'):
                print(f"\n📦 Kontenery ({result.get('container_count', 0)}):")
                for container in result['containers']:
                    status_emoji = "✅" if "Up" in container.get('status', '') else "❌"
                    print(f"   {status_emoji} {container['name']}: {container['status']}")
                    if container.get('ports'):
                        print(f"      🌐 Porty: {container['ports']}")
            
            # Test services
            print("\n🧪 Testowanie usług...")
            await test_services(controller)
            
        else:
            print(f"   ❌ Błąd: {docker_result.get('message', 'Unknown error')}")
            print("\n🔧 Próba naprawy...")
            await troubleshoot_and_fix(controller, command)
    
    # Show generated files
    files_info = controller.get_generated_files_info()
    if files_info['files']:
        print(f"\n📁 Wygenerowane pliki w: {files_info['output_directory']}")
        print(f"   Łącznie {files_info['total_files']} plików:")
        for file_info in files_info['files']:
            print(f"   📄 {file_info['name']} ({file_info['size']} bytes)")
    
    # Interactive mode (only if requested)
    if interactive:
        await interactive_mode(controller)
    else:
        # Auto-stop services in non-interactive mode
        if controller.docker_manager:
            print("\n🛑 Automatyczne zatrzymywanie kontenerów...")
            await controller.stop_containers()
    
    # Final cleanup
    print("\n🧹 Final cleanup...")
    if Path("./generated").exists():
        shutil.rmtree("./generated")
        print("✅ Wygenerowane pliki usunięte")
    
    print("\n🎉 Demo zakończone!")


async def test_services(controller):
    """Test if services are working properly."""
    print("🔍 Sprawdzanie działania usług...")
    
    # Get container status
    status_result = await controller.get_container_status()
    if status_result.get('status') != 'success':
        print("❌ Nie można sprawdzić statusu kontenerów")
        return False
    
    containers = status_result.get('containers', [])
    all_healthy = True
    
    for container in containers:
        name = container['name']
        status = container['status']
        
        if 'Up' in status:
            print(f"   ✅ {name}: działa")
            
            # Test specific services
            if 'chat-service' in name.lower():
                await test_chat_service(container)
            elif 'redis' in name.lower():
                await test_redis_service(container)
        else:
            print(f"   ❌ {name}: nie działa ({status})")
            all_healthy = False
    
    return all_healthy


async def test_chat_service(container):
    """Test chat service (nginx)."""
    import subprocess
    import time
    
    print("   🌐 Testowanie serwisu czatu (nginx)...")
    
    # Wait a moment for service to start
    await asyncio.sleep(2)
    
    try:
        # Test if port 8080 is accessible
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8080"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip() == "200":
            print("      ✅ Serwis odpowiada na porcie 8080")
        else:
            print(f"      ⚠️ Serwis zwrócił kod: {result.stdout.strip()}")
    except subprocess.TimeoutExpired:
        print("      ⏰ Timeout podczas łączenia z serwisem")
    except Exception as e:
        print(f"      ❌ Błąd testu serwisu: {e}")


async def test_redis_service(container):
    """Test Redis service."""
    import subprocess
    
    print("   💾 Testowanie Redis...")
    
    try:
        # Test Redis connection
        result = subprocess.run(
            ["docker", "exec", container['name'], "redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if "PONG" in result.stdout:
            print("      ✅ Redis odpowiada (PONG)")
        else:
            print(f"      ❌ Redis nie odpowiada: {result.stdout}")
    except Exception as e:
        print(f"      ❌ Błąd testu Redis: {e}")


async def troubleshoot_and_fix(controller, original_command):
    """Troubleshoot and fix deployment issues."""
    print("🔧 Diagnozowanie problemów...")
    
    # Check if Docker is running
    try:
        import subprocess
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("❌ Docker nie działa. Uruchom Dockera.")
            return
    except Exception as e:
        print(f"❌ Błąd sprawdzania Dockera: {e}")
        return
    
    # Check generated files
    files_info = controller.get_generated_files_info()
    if not files_info['files']:
        print("❌ Brak wygenerowanych plików")
        return
    
    # Show Docker Compose file
    compose_file = None
    for file_info in files_info['files']:
        if 'docker-compose.yml' in file_info['name']:
            compose_file = Path(file_info['path'])
            break
    
    if compose_file and compose_file.exists():
        print(f"\n📄 Plik Docker Compose: {compose_file}")
        print("Zawartość:")
        with open(compose_file, 'r') as f:
            for i, line in enumerate(f.readlines()[:10], 1):
                print(f"   {i:2d}: {line.rstrip()}")
        
        # Try manual start
        print(f"\n🔧 Próba ręcznego uruchomienia...")
        try:
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "up", "-d"],
                cwd=compose_file.parent,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Usługi uruchomione ręcznie")
                # Test again
                await asyncio.sleep(3)
                await test_services(controller)
            else:
                print(f"❌ Ręczne uruchomienie nie powiodło się: {result.stderr}")
        except Exception as e:
            print(f"❌ Błąd ręcznego uruchomienia: {e}")


async def interactive_mode(controller):
    """Interactive mode for additional commands."""
    import sys
    
    print("\n" + "=" * 70)
    print("🎮 Tryb Interaktywny")
    print("=" * 70)
    print("Dostępne komendy:")
    print("  status - pokaż status kontenerów")
    print("  logs - pokaż logi kontenerów")
    print("  logs follow - śledź logi na żywo")
    print("  stop - zatrzymaj kontenery")
    print("  test - ponownie przetestuj usługi")
    print("  quit - wyjdź")
    
    # Check if we're in interactive mode
    if not sys.stdin.isatty():
        print("\n🤖 Tryb nieinteraktywny - kończę działanie")
        # Auto-stop services in non-interactive mode
        if controller.docker_manager:
            print("🛑 Automatyczne zatrzymywanie kontenerów...")
            await controller.stop_containers()
        return
    
    while True:
        try:
            command = input("\n📝 Twoje polecenie: ").strip()
            
            if not command:
                continue
            
            if command.lower() == 'quit':
                print("\n👋 Zatrzymywanie usług i wyjście...")
                if controller.docker_manager:
                    await controller.stop_containers()
                break
            
            if command.lower() == 'status':
                status_result = await controller.get_container_status()
                if status_result.get('status') == 'success':
                    containers = status_result.get('containers', [])
                    if containers:
                        print(f"\n📦 Kontenery ({len(containers)}):")
                        for container in containers:
                            status_emoji = "✅" if "Up" in container.get('status', '') else "❌"
                            print(f"   {status_emoji} {container['name']}: {container['status']}")
                    else:
                        print("\n📦 Brak działających kontenerów")
                else:
                    print(f"\n❌ Błąd: {status_result.get('message')}")
            
            elif command.lower() == 'logs':
                print(f"\n📋 Logi kontenerów:")
                await controller.show_container_logs(follow=False, lines=20)
            
            elif command.lower() == 'logs follow':
                print(f"\n📋 Śledzenie logów (Ctrl+C aby przerwać)...")
                await controller.show_container_logs(follow=True)
            
            elif command.lower() == 'stop':
                print(f"\n🛑 Zatrzymywanie kontenerów...")
                stop_result = await controller.stop_containers()
                if stop_result.get('status') == 'success':
                    print("✅ Kontenery zatrzymane")
                else:
                    print(f"❌ Błąd: {stop_result.get('message')}")
            
            elif command.lower() == 'test':
                print(f"\n🧪 Testowanie usług...")
                await test_services(controller)
            
            else:
                print(f"🤖 Wykonuję: {command}")
                result = await controller.execute(command)
                print(f"Status: {result.get('status')}")
                print(f"Message: {result.get('message')}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Przerwano.")
            break
        except Exception as e:
            print(f"\n❌ Błąd: {e}")
    
    # Cleanup on exit
    if controller.docker_manager:
        print("🛑 Zatrzymywanie kontenerów przed wyjściem...")
        await controller.stop_containers()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NLP2CMD Auto Demo & Test")
    parser.add_argument("--interactive", "-i", action="store_true", 
                       help="Run in interactive mode")
    args = parser.parse_args()
    
    asyncio.run(run_demo_with_test(interactive=args.interactive))
