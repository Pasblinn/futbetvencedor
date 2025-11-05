#!/bin/bash
# Test rate limiting

echo "🧪 Testing Rate Limiting"
echo "======================="

echo -e "\n1. Testing health endpoint (limit: 200/min)..."
for i in {1..5}; do
  STATUS=$(curl -s -w "\n%{http_code}" http://localhost:8000/health | tail -1)
  echo "Request $i: HTTP $STATUS"
  sleep 0.1
done

echo -e "\n2. Testing root endpoint (limit: 20/min)..."
echo "Making 25 rapid requests (should get 429 after 20)..."
for i in {1..25}; do
  STATUS=$(curl -s -w "%{http_code}" -o /dev/null http://localhost:8000/)
  if [ "$STATUS" == "429" ]; then
    echo "Request $i: HTTP 429 ⚠️ Rate limit exceeded (as expected)"
    break
  else
    echo "Request $i: HTTP $STATUS ✓"
  fi
  sleep 0.1
done

echo -e "\n✅ Rate limiting test complete!"
echo "Note: Wait 60 seconds for rate limit to reset"
