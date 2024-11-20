# FRAG Connector

## Get Started

### 1. Configure Environment Variables
Copy the provided example file `.env.example` to `.env` and update the values.

```bash
cp .env.example .env
```

#### Connector Configuration
- MY_CONNECTOR_NAME: Identifier for the connector
  - Default: `my-frag-connector`
- MY_CONNECTOR_FQDN: Fully qualified domain name of the connector
  - Default: `http://localhost`
- MY_CONNECTOR_PORT: Port number of the connector
  - Default: `8000`
- MY_CONNECTOR_API_KEY: API key for accessing the connector API
  - Default: `DefaultApiKey`

#### Authentication Configuration
- OAUTH_SERVER_URL: URL of the OAuth 2.0 server (Required)
- OAUTH_REALM_NAME: Keycloak realm name (Required)
- OAUTH_CLIENT_ID: Client ID issued by the authentication server (Required)
- OAUTH_CLIENT_SECRET: Client secret issued by the authentication server (Required)

#### Vector Database (Only for RAG Data Providers)
- VECTOR_DB_SERVICE: Service name of the vector database (e.g., `qdrant`, `pinecone`)
  - Default: `null`
- VECTOR_DB_URL: URL of the vector database
  - Default: `null`
- VECTOR_DB_API_KEY: API key for the vector database
  - Default: `null`
- VECTOR_DB_INDEX_NAME: Index / Collection name in the vector database
  - Default: `test-index`
- VECTOR_DB_METADATA_TEXT_KEY: Metadata key used for the document text in the vector database
  - Default: `text`

#### Large Language Model (LLM) (WIP)
- LLM_SERVICE: Name of the LLM service (e.g., OpenAI, Ollama)
  - Default: `null`
- LLM_API_KEY: API key for the LLM service
  - Default: `null`
- LLM_API_BASE_URL: Base URL of the LLM API
  - Default: `http://localhost:11434`

#### Internal JSON Files
- ASSETS_CONFIG_PATH: Path to the JSON file managing asset information
- CONNECTORS_CONFIG_PATH: Path to the JSON file managing connector information

### 2. Start the Container
Start the server using Docker Compose:

```bash
docker compose up -d
```

## API Documentation
Once the server is running, access the Swagger UI at `/docs` on the connector's URL for API details and testing.
