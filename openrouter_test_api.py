"""
openrouter测试
"""
import requests
import json


def check_api_key():
  """To check the rate limit or credits left on an API key, make a GET request to https://openrouter.ai/api/v1/key"""
  response = requests.get(
    url="https://openrouter.ai/api/v1/key",
    headers={
      "Authorization": f"Bearer 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"
    }
  )

  print(json.dumps(response.json(), indent=2))


def api_test():
  response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
      "Authorization": "Bearer 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",
      "Content-Type": "application/json",
    },
    data=json.dumps({
      "model": "minimax/minimax-m2.5:free",
      "messages": [
        {
          "role": "user",
          "content": "Hello!"
        }
      ]
    })
  )

  data = response.json()
  print(data)
  print(data['choices'][0]['message']['content'])
  # Check which model was selected
  print('Model used:', data['model'])

check_api_key()