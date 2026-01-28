#!/usr/bin/env python3
"""
Batch demo - execute all commands from prompt.txt automatically.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

sys.path.append(str(Path(__file__).resolve().parents[2]))

from _example_helpers import print_rule, print_separator

from nlp2cmd_web_controller import NLP2CMDWebController


async def run_batch_demo():
    """Run all commands from prompt.txt automatically."""
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║     🚀 NLP2CMD Batch Demo - All Commands from prompt.txt            ║")
    print("║                                                                      ║")
    print("║     Natural Language → DevOps Configuration + Testing               ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    
    print_separator(
        "🤖 NLP2CMD - Tryb Batch (wszystkie komendy z prompt.txt)",
        leading_newline=True,
        width=70,
    )
    
    # Read commands from prompt.txt
    prompt_file = Path("prompt.txt")
    if not prompt_file.exists():
        print(f"❌ Plik {prompt_file} nie istnieje!")
        return
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        commands = [line.strip() for line in f.readlines() if line.strip()]
    
    print(f"\n📋 Znaleziono {len(commands)} komend do wykonania:")
    for i, cmd in enumerate(commands, 1):
        print(f"   {i}. {cmd}")
    
    # Clean up any existing files
    import shutil
    if Path("./generated").exists():
        shutil.rmtree("./generated")
    
    # Initialize controller
    controller = NLP2CMDWebController(output_dir="./generated")
    
    print(f"\n🚀 Rozpoczynam wykonywanie komend...")
    print_rule(width=70, char="=")
    
    results = []
    
    for i, command in enumerate(commands, 1):
        print(f"\n📝 Komenda {i}/{len(commands)}: {command}")
        print("⚙️ Przetwarzanie...")
        print_rule()
        
        try:
            # Execute command
            result = await controller.execute(command)
            
            print(f"\n📊 Status: {result.get('status')}")
            print(f"💬 {result.get('message')}")
            
            # Show configuration if available
            if result.get('config'):
                print("\n⚙️ Konfiguracja:")
                for key, value in result['config'].items():
                    if key == 'env_vars':
                        print(f"   {key}:")
                        for k, v in value.items():
                            print(f"     {k}: {v}")
                    else:
                        print(f"   {key}: {value}")
            
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
                    print(f"\n🧪 Testowanie usług...")
                    await test_services(controller)
                else:
                    print(f"   ❌ Błąd Dockera: {docker_result.get('message', 'Unknown error')}")
            
            # Show saved files
            if result.get('files_saved'):
                print("\n💾 Zapisane pliki:")
                for file_type, file_path in result['files_saved'].items():
                    print(f"   📄 {file_type}: {file_path}")
            
            results.append({
                "command": command,
                "status": result.get('status'),
                "message": result.get('message'),
                "success": result.get('status') == 'success'
            })
            
        except Exception as e:
            print(f"❌ Błąd wykonania: {e}")
            results.append({
                "command": command,
                "status": "error",
                "message": str(e),
                "success": False
            })
        
        # Small delay between commands
        await asyncio.sleep(1)
    
    # Summary
    print_separator("📊 Podsumowanie wykonania", leading_newline=True, width=70)
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n✅ Pomyślne: {successful}/{total}")
    print(f"❌ Błędy: {total - successful}/{total}")
    
    print("\n📋 Szczegóły:")
    for i, result in enumerate(results, 1):
        status_emoji = "✅" if result['success'] else "❌"
        print(f"   {status_emoji} {i}. {result['command']}")
        print(f"      {result['message']}")
    
    # Show all generated files
    files_info = controller.get_generated_files_info()
    if files_info['files']:
        print(f"\n📁 Wszystkie wygenerowane pliki ({files_info['total_files']}):")
        for file_info in files_info['files']:
            print(f"   📄 {file_info['name']} ({file_info['size']} bytes)")
    
    # Final container status
    if controller.docker_manager:
        print(f"\n📦 Finalny status kontenerów:")
        status_result = await controller.get_container_status()
        if status_result.get('status') == 'success':
            containers = status_result.get('containers', [])
            for container in containers:
                status_emoji = "✅" if "Up" in container.get('status', '') else "❌"
                print(f"   {status_emoji} {container['name']}: {container['status']}")
    
    # Cleanup
    print(f"\n🧹 Sprzątanie...")
    if controller.docker_manager:
        await controller.stop_containers()
    
    if Path("./generated").exists():
        shutil.rmtree("./generated")
        print("✅ Pliki usunięte")
    
    print(f"\n🎉 Batch demo zakończone!")
    print(f"Wynik: {successful}/{total} komend wykonanych pomyślnie")


async def test_services(controller):
    """Test if services are working properly."""
    try:
        # Get container status
        status_result = await controller.get_container_status()
        if status_result.get('status') != 'success':
            print("   ❌ Nie można sprawdzić statusu kontenerów")
            return
        
        containers = status_result.get('containers', [])
        
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
                elif 'postgres' in name.lower():
                    await test_postgres_service(container)
            else:
                print(f"   ❌ {name}: nie działa ({status})")
    
    except Exception as e:
        print(f"   ❌ Błąd testu: {e}")


async def test_chat_service(container):
    """Test chat service (nginx)."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8080"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip() == "200":
            print("      ✅ Serwis czatu odpowiada (HTTP 200)")
        else:
            print(f"      ⚠️ Serwis czatu zwrócił kod: {result.stdout.strip()}")
    except Exception as e:
        print(f"      ❌ Błąd testu serwisu czatu: {e}")


async def test_redis_service(container):
    """Test Redis service."""
    import subprocess
    
    try:
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


async def test_postgres_service(container):
    """Test PostgreSQL service."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["docker", "exec", container['name'], "pg_isready", "-U", "nlp2cmd"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("      ✅ PostgreSQL gotowy")
        else:
            print(f"      ⚠️ PostgreSQL nie jest gotowy: {result.stderr}")
    except Exception as e:
        print(f"      ❌ Błąd testu PostgreSQL: {e}")


if __name__ == "__main__":
    if "MAKELEVEL" in os.environ or "MAKEFLAGS" in os.environ:
        print("Invoked under make; skipping web_development demo_batch.")
        print("Run directly with: python3 demo_batch.py")
        raise SystemExit(0)
    asyncio.run(run_batch_demo())
