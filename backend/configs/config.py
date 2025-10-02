# Database Configuration
DATABASE_URL = "sqlite:///./compliance_system.db"

# ML Model Configuration
LEGAL_BERT_MODEL = "nlpaueb/legal-bert-base-uncased"
MAX_SEQUENCE_LENGTH = 512
BATCH_SIZE = 8
LEARNING_RATE = 2e-5
NUM_EPOCHS = 3

# Ollama Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1"

# File Upload Configuration
UPLOAD_DIR = "./data/uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True

# Classification Labels
COMPLIANCE_LABELS = {
    0: "COMPLIANT",
    1: "NON_COMPLIANT", 
    2: "REQUIRES_REVIEW"
}

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"