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
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent / "shared"))

from nlp2cmd_web_controller import NLP2CMDWebController


async def demo_nlp_commands():
    """Interaktywna demonstracja poleceń NLP."""
    
    controller = NLP2CMDWebController()
    
    print("=" * 70)
    print("🤖 NLP2CMD Web Controller - Interaktywna Demonstracja")
    print("=" * 70)
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
            
            # Check if user wants to see generated files
            if result.get('status') == 'success' and result.get('files_saved'):
                show_files = input("\n🔍 Pokazać wygenerowane pliki? (t/n): ").strip().lower()
                if show_files in ['t', 'tak', 'yes', 'y']:
                    files_info = controller.get_generated_files_info()
                    print(f"\n📁 Wygenerowane pliki w: {files_info['output_directory']}")
                    if files_info['files']:
                        print(f"   Łącznie {files_info['total_files']} plików:")
                        for file_info in files_info['files']:
                            print(f"   📄 {file_info['name']} ({file_info['size']} bytes)")
                    else:
                        print("   Brak plików")
            
            # Check if user wants to save full deployment plan
            if len(controller.services) > 0:
                save_plan = input("\n💾 Zapisać pełny plan deployment? (t/n): ").strip().lower()
                if save_plan in ['t', 'tak', 'yes', 'y']:
                    plan_result = await controller.save_full_deployment_plan()
                    print(f"\n{plan_result['message']}")
                    print(f"📁 Pliki zapisane w: {plan_result['output_directory']}")
                    
                    # Show generated files
                    files_info = controller.get_generated_files_info()
                    if files_info['files']:
                        print(f"\n📁 Wygenerowane pliki:")
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
        print("\n" + "=" * 70)
        print("📌 PRZYKŁAD 1: Komunikator Real-Time")
        print("=" * 70)
        
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
        print("\n" + "=" * 70)
        print("📌 PRZYKŁAD 2: Strona Kontaktowa")
        print("=" * 70)
        
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
        print("\n" + "=" * 70)
        print("📌 PRZYKŁAD 3: Klient Email")
        print("=" * 70)
        
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
        
        print("\n" + "=" * 70)
        print("✅ Wszystkie przykłady wygenerowane!")
        print("=" * 70)
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
