#!/bin/bash
# Script to test nlp2cmd commands safely in Docker container

set -e

IMAGE_NAME="nlp2cmd-test"
CONTAINER_NAME="nlp2cmd-test-container"

echo "🐳 Building Docker test image..."
docker build -f Dockerfile.test -t $IMAGE_NAME .

echo ""
echo "🚀 Starting test container..."
docker run --rm -it --name $CONTAINER_NAME $IMAGE_NAME /bin/bash -c '
set -e

echo "=========================================="
echo "🧪 Testing nlp2cmd commands in container"
echo "=========================================="

# Test 1: Process memory
echo ""
echo "📋 Test 1: znajdź proces z największym zużyciem RAM"
nlp2cmd -r "znajdz proces ktory pobiera najwiecej pamieci RAM" --auto-confirm

# Test 2: Disk usage
echo ""
echo "📋 Test 2: pokaż użycie dysku"
nlp2cmd -r "pokaz uzycie dysku" --auto-confirm

# Test 3: List files
echo ""
echo "📋 Test 3: pokaż pliki w katalogu"
nlp2cmd -r "lista plikow w /app" --auto-confirm

# Test 4: Find files
echo ""
echo "📋 Test 4: znajdź pliki .py"
nlp2cmd -r "znajdz pliki python" --auto-confirm

# Test 5: Cat file
echo ""
echo "📋 Test 5: pokaż zawartość pliku"
nlp2cmd -r "pokaz zawartosc pliku /app/test_data/test.txt" --auto-confirm

# Test 6: Head file
echo ""
echo "📋 Test 6: pierwsze linie pliku"
nlp2cmd -r "pokaz pierwsze 2 linie pliku /app/test_data/test.txt" --auto-confirm

# Test 7: wc count lines
echo ""
echo "📋 Test 7: policz linie w pliku"
nlp2cmd -r "policz linie w pliku /app/test_data/test.txt" --auto-confirm

# Test 8: Parse JSON
echo ""
echo "📋 Test 8: parsuj JSON"
nlp2cmd -r "parsuj json z pliku /app/test_data/test.json" --auto-confirm

# Test 9: Network info
echo ""
echo "📋 Test 9: pokaż adres IP"
nlp2cmd -r "pokaz adres ip" --auto-confirm

# Test 10: System info
echo ""
echo "📋 Test 10: info o CPU"
nlp2cmd -r "info o procesorze" --auto-confirm

echo ""
echo "=========================================="
echo "✅ All tests completed!"
echo "=========================================="
'

echo ""
echo "🧹 Cleanup complete"
