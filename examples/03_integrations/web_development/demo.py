#!/usr/bin/env python3
"""
NLP2CMD Web Examples - Main Demo

Ten skrypt demonstruje jak NLP2CMD może służyć jako warstwa backend/DevOps
dla aplikacji webowych, konfigurując je za pomocą poleceń w języku naturalnym.

Przykłady:
1. Komunikator (real-time chat z WebSocket)
2. Strona kontaktu (formularz + email)
3. Klient email (podgląd IMAP)

Uruchomienie:
    python demo.py [--example 1|2|3|all]
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent / "shared"))

sys.path.append(str(Path(__file__).resolve().parents[2]))

from _example_helpers import print_separator

from nlp2cmd_web_controller import NLP2CMDWebController


async def demo_nlp_commands():
    """Interaktywna demonstracja poleceń NLP."""
    
    controller = NLP2CMDWebController()
    
    print_separator("🤖 NLP2CMD Web Controller - Interaktywna Demonstracja", width=70)
    print("\nWpisz polecenia w języku naturalnym (polskim lub angielskim).")
    print("Wpisz 'help' aby zobaczyć przykłady, 'quit' aby wyjść.\n")
    
    examples = [
        "Uruchom serwis czatu na porcie 8080",
        "Skonfiguruj email dla jan@gmail.com",
        "Stwórz formularz kontaktowy",
        "Pokaż status usług",
        "Skaluj czat do 3 replik",
        "Uruchom Redis dla cache",
        "Deploy bazy PostgreSQL",
    ]
    
    while True:
        try:
            command = input("\n📝 Twoje polecenie: ").strip()
            
            if not command:
                continue
            
            if command.lower() == 'quit':
                print("\n👋 Do zobaczenia!")
                break
            
            if command.lower() == 'help':
                print("\n📋 Przykładowe polecenia:")
                for i, ex in enumerate(examples, 1):
                    print(f"   {i}. {ex}")
                print("\n🔧 Zarządzanie kontenerami:")
                print("   status - pokaż status kontenerów")
                print("   logs - pokaż logi kontenerów")
                print("   logs follow - śledź logi na żywo")
                print("   stop - zatrzymaj wszystkie kontenery")
                continue
            
            # Handle container management commands
            if command.lower() == 'status':
                print(f"\n⚙️ Sprawdzanie statusu kontenerów...")
                print("-" * 50)
                
                status_result = await controller.get_container_status()
                if status_result.get('status') == 'success':
                    containers = status_result.get('containers', [])
                    if containers:
                        print(f"📦 Kontenery ({len(containers)}):")
                        for container in containers:
                            status_emoji = "✅" if "Up" in container.get('status', '') else "❌"
                            print(f"   {status_emoji} {container['name']}: {container['status']}")
                            if container.get('ports'):
                                print(f"      🌐 Porty: {container['ports']}")
                    else:
                        print("📦 Brak działających kontenerów")
                else:
                    print(f"❌ Błąd: {status_result.get('message')}")
                continue
            
            if command.lower() == 'logs':
                print(f"\n📋 Pobieranie logów kontenerów...")
                print("-" * 50)
                await controller.show_container_logs(follow=False, lines=20)
                continue
            
            if command.lower() == 'logs follow':
                print(f"\n📋 Śledzenie logów kontenerów (Ctrl+C aby przerwać)...")
                print("-" * 50)
                await controller.show_container_logs(follow=True)
                continue
            
            if command.lower() == 'stop':
                print(f"\n🛑 Zatrzymywanie kontenerów...")
                print("-" * 50)
                stop_result = await controller.stop_containers()
                if stop_result.get('status') == 'success':
                    print("✅ Kontenery zatrzymane pomyślnie")
                else:
                    print(f"❌ Błąd: {stop_result.get('message')}")
                continue
            
            # Execute command
            print(f"\n⚙️ Przetwarzanie: \"{command}\"")
            print("-" * 50)
            
            result = await controller.execute(command)
            
            # Pretty print result
            print(f"\n📊 Status: {result.get('status', 'unknown')}")
            
            if result.get('message'):
                print(f"💬 {result['message']}")
            
            if result.get('config'):
                print("\n⚙️ Konfiguracja:")
                for key, value in result['config'].items():
                    print(f"   {key}: {value}")
            
            if result.get('docker_compose'):
                print("\n🐳 Docker Compose wygenerowany")
                print("   (użyj pełnego przykładu aby zobaczyć szczegóły)")
            
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
                    
                    # Show recent logs
                    print(f"\n📋 Ostatnie logi kontenerów:")
                    await controller.show_container_logs(follow=False, lines=5)
                else:
                    print(f"   ❌ Błąd: {docker_result.get('message', 'Unknown error')}")
            
            if result.get('note'):
                print(f"\n📝 {result['note']}")
            
            if result.get('services'):
                print("\n📦 Aktywne usługi:")
                for name, info in result['services'].items():
                    print(f"   - {name}: port {info['port']} ({info['type']})")
            
            if result.get('examples'):
                print("\n💡 Przykłady:")
                for ex in result['examples']:
                    print(f"   • {ex}")
            
            # Automatically show generated files info
            if result.get('status') == 'success' and result.get('files_saved'):
                files_info = controller.get_generated_files_info()
                print(f"\n📁 Wygenerowane pliki w: {files_info['output_directory']}")
                if files_info['files']:
                    print(f"   Łącznie {files_info['total_files']} plików:")
                    for file_info in files_info['files']:
                        print(f"   📄 {file_info['name']} ({file_info['size']} bytes)")
                else:
                    print("   Brak plików")
            
            # Automatically save full deployment plan when services exist
            if len(controller.services) > 0:
                print("\n💾 Automatyczne zapisywanie pełnego planu deployment...")
                plan_result = await controller.save_full_deployment_plan()
                print(f"{plan_result['message']}")
                
                # Show all generated files
                files_info = controller.get_generated_files_info()
                if files_info['files']:
                    print(f"\n📁 Wszystkie wygenerowane pliki:")
                    for file_info in files_info['files']:
                        print(f"   📄 {file_info['name']} ({file_info['size']} bytes)")
                    
        except KeyboardInterrupt:
            print("\n\n👋 Przerwano.")
            break
        except Exception as e:
            print(f"\n❌ Błąd: {e}")


async def run_example(example_num: int):
    """Run specific example."""
    import importlib.util
    
    base_path = Path(__file__).parent
    
    if example_num == 1:
        print_separator("📌 PRZYKŁAD 1: Komunikator Real-Time", leading_newline=True, width=70)
        
        spec = importlib.util.spec_from_file_location(
            "chat_example", 
            base_path / "communicator" / "chat_example.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        await module.demo_chat_deployment()
        print("\n")
        await module.generate_chat_files()
        
    elif example_num == 2:
        print_separator("📌 PRZYKŁAD 2: Strona Kontaktowa", leading_newline=True, width=70)
        
        spec = importlib.util.spec_from_file_location(
            "contact_example", 
            base_path / "contact-page" / "contact_example.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        await module.demo_contact_deployment()
        print("\n")
        await module.generate_contact_files()
        
    elif example_num == 3:
        print_separator("📌 PRZYKŁAD 3: Klient Email", leading_newline=True, width=70)
        
        spec = importlib.util.spec_from_file_location(
            "email_example", 
            base_path / "email-client" / "email_example.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        await module.demo_email_deployment()
        print("\n")
        await module.generate_files()


async def main():
    parser = argparse.ArgumentParser(
        description="NLP2CMD Web Examples - demonstracja użycia NLP2CMD jako backend/DevOps"
    )
    parser.add_argument(
        "--example", "-e",
        type=str,
        choices=["1", "2", "3", "all", "interactive"],
        default="interactive",
        help="Który przykład uruchomić (1=chat, 2=contact, 3=email, all=wszystkie, interactive=tryb interaktywny)"
    )
    
    args = parser.parse_args()

    if args.example == "interactive" and (not sys.stdin.isatty() or "MAKELEVEL" in os.environ or "MAKEFLAGS" in os.environ):
        print("Non-interactive environment detected; skipping interactive web demo.")
        print("Re-run this script in a TTY (default) or use: python demo.py --example all")
        return
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     🚀 NLP2CMD Web Examples                                          ║
║                                                                      ║
║     Natural Language → Backend/DevOps Configuration                  ║
║                                                                      ║
║     Przykłady:                                                       ║
║     1. 💬 Komunikator (WebSocket + Redis)                           ║
║     2. 📧 Strona Kontaktu (PostgreSQL + SMTP)                       ║
║     3. 📬 Klient Email (IMAP + Redis)                               ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    if args.example == "interactive":
        await demo_nlp_commands()
    elif args.example == "all":
        await run_example(1)
        await run_example(2)
        await run_example(3)
        
        print_separator("✅ Wszystkie przykłady wygenerowane!", leading_newline=True, width=70)
        print("""
📁 Struktura projektu:
├── communicator/     → Uruchom: cd communicator && docker-compose up
├── contact-page/     → Uruchom: cd contact-page && docker-compose up
└── email-client/     → Uruchom: cd email-client && docker-compose up

🌐 Porty:
• Komunikator:  http://localhost:3000 (frontend), :8080 (API)
• Kontakt:      http://localhost:3001 (frontend), :8081 (API)
• Email:        http://localhost:3002 (frontend), :8082 (API)
""")
    else:
        await run_example(int(args.example))


if __name__ == "__main__":
    asyncio.run(main())
