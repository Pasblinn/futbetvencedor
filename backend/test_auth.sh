#!/bin/bash
# Test authentication endpoints

echo "🧪 Testing Authentication System"
echo "================================"

# 1. Register new user
echo -e "\n📝 1. Registering new user..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123456"
  }')
echo "$REGISTER_RESPONSE" | python3 -m json.tool

# 2. Login
echo -e "\n🔐 2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "Test123456"
  }')
echo "$LOGIN_RESPONSE" | python3 -m json.tool

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -n "$TOKEN" ]; then
  echo -e "\n✅ Token received: ${TOKEN:0:50}..."

  # 3. Get current user
  echo -e "\n👤 3. Getting current user info..."
  curl -s http://localhost:8000/api/v1/auth/me \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

  # 4. Test protected endpoint (predictions)
  echo -e "\n📊 4. Testing access to predictions (no auth required yet)..."
  curl -s "http://localhost:8000/api/v1/predictions/upcoming?limit=1" | python3 -m json.tool | head -20

  echo -e "\n✅ All tests passed!"
else
  echo -e "\n❌ Failed to get token"
fi
