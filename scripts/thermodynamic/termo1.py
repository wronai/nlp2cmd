import asyncio
from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator

async def main():
    generator = HybridThermodynamicGenerator()
    
    # Naturalny język → komendy DevOps
    queries = [
        "Pokaż wszystkie pody w namespace production",
        "Skaluj deployment api-server do 5 replik",
        "Znajdź logi z błędami z ostatniej godziny",
        "Uruchom backup bazy danych na S3",
    ]
    
    for query in queries:
        result = await generator.generate(query)
        print(f"Query: {query}")
        if result['source'] == 'dsl':
            print(f"Command: {result['result'].command}")
        else:
            print(f"Solution: {result['result'].decoded_output}")
        print()

if __name__ == "__main__":
    asyncio.run(main())