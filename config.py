"""Configuration for the job tracker."""

import os

# Set these via environment variables or a .env file (see .env.example)
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")

# Resume key skills for match scoring
RESUME_SKILLS = {
    "ml_core": ["xgboost", "gradient boosting", "h2o", "scikit-learn", "pytorch", "tensorflow",
                 "classification", "regression", "anomaly detection", "clustering", "forecasting",
                 "time series", "random forest", "lightgbm", "catboost"],
    "nlp_llm": ["llm", "rag", "nlp", "hugging face", "transformers", "prompt engineering",
                 "large language model", "generative ai", "gpt", "fine-tuning", "embeddings",
                 "langchain", "openai", "vector database"],
    "data_eng": ["pyspark", "spark", "bigquery", "sql", "hiveql", "databricks", "kafka",
                 "airflow", "dbt", "data pipeline", "etl", "feature engineering", "feature store"],
    "cloud_mlops": ["aws", "gcp", "sagemaker", "mlflow", "mlops", "model monitoring",
                    "drift detection", "a/b testing", "shadow deployment", "model registry",
                    "docker", "kubernetes", "ci/cd"],
    "domain": ["fraud detection", "risk modeling", "graph", "network analysis", "entity resolution",
               "fintech", "marketplace", "anomaly", "behavioral", "identity", "trust and safety",
               "computer vision", "geospatial", "autonomous"],
    "languages": ["python", "r", "sql", "scala"],
}

RESUME_EXPERIENCE_YEARS = 8  # Total relevant experience
TARGET_TC_LOW = 250000
TARGET_TC_HIGH = 350000
NEEDS_H1B = True

TARGET_ROLES = [
    "senior data scientist",
    "staff data scientist",
    "machine learning engineer",
    "senior machine learning engineer",
    "ai engineer",
    "senior ai engineer",
    "applied scientist",
    "senior applied scientist",
    "research scientist",
    "ml engineer",
    "data scientist",
]

MATCH_THRESHOLD = 0.80  # Only include jobs with >= 80% match
