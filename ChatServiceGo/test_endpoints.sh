#!/bin/bash

BASE_URL="http://localhost:9090/api/v1"
EMAIL="test@example.com"
PASSWORD="password123"

echo "1. Testing Captcha (Pre-requisite for Register)..."
curl -X POST "$BASE_URL/user/captcha" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\"}"
echo -e "\n\n"

# Note: In a real scenario, we'd need to fetch the captcha from Redis or Email.
# Since we are mocking/simplifying, we might need to manually check Redis or disable the check.
# For now, let's assume the user handles the captcha part or we use a hardcoded one if the code allows.
# But based on the code, it CHECKS redis.
# To make this script runnable without manual intervention, one would need to peek into Redis.
# checks logs for now.

echo "2. Testing Register..."
# You need to replace 'YOUR_CAPTCHA_HERE' with the actual code sent to email/redis
echo "Please verify the captcha in your email/logs and run the register command manually via Postman:"
echo "POST $BASE_URL/user/register"
echo "Body: {\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\", \"captcha\": \"YOUR_CAPTCHA_HERE\"}"
echo -e "\n"

echo "3. Testing Login..."
# Assuming a user 'testuser' exists (or use the one created above)
curl -X POST "$BASE_URL/user/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"testuser\", \"password\": \"$PASSWORD\"}"
echo -e "\n\n"

echo "4. Testing Create Session..."
curl -X POST "$BASE_URL/session/create?username=testuser" \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"My First Session\"}"
echo -e "\n"
