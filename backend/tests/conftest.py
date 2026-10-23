import os

# app.main створює застосунок під час імпорту — тести не ходять у мережу й не потребують ключів
os.environ["LLM_PROVIDER"] = "mock"
