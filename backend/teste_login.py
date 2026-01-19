import requests

response = requests.post("http://127.0.0.1:8080/v1/auth/login", json={
    "email": "tuliocarvalho31121981@gmail.com",
    "senha": "aloha123"
})

print("Status:", response.status_code)
print("Response:", response.json())
