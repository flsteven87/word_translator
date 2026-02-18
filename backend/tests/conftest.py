import os

# Set test environment variables before any app imports trigger settings loading
os.environ.setdefault("OPENAI_API_KEY", "test-key-for-testing")
