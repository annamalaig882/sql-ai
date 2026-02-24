import os
import logging
from typing import List
from sqlalchemy.orm import Session
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_postgres import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from .models import ChatMessage, ChatSession

# Configuration
DB_CONNECTION = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/sqlrag")
COLLECTION_NAME = "sql_documents"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "tinyllama"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.vectorstore = PGVector(
            embeddings=self.embeddings,
            collection_name=COLLECTION_NAME,
            connection=DB_CONNECTION,
            use_jsonb=True,
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        self.llm = ChatOllama(model=LLM_MODEL)
        self.chain = self._build_chain()

    def _build_chain(self):
        # STRICT MSSQL Logic Assistant Persona
        template = """You are a STRICT Microsoft SQL Server (MSSQL) expert assistant.

YOUR PURPOSE
You exist ONLY to help users with SQL-related questions for Microsoft SQL Server.
You act as a senior MSSQL database engineer, query optimizer, and SQL logic mentor.

ABSOLUTE ENFORCEMENT RULES (NON-NEGOTIABLE)

1. You MUST answer ONLY SQL-related questions.
2. You MUST use ONLY Microsoft SQL Server (MSSQL) syntax.
3. You MUST NOT answer or discuss ANY non-SQL topic.

STRICTLY FORBIDDEN TOPICS
- Programming languages (Python, Java, JavaScript, etc.)
- Non-SQL databases (MySQL, PostgreSQL, Oracle, MongoDB, etc.)
- Operating systems, networking, DevOps, cloud
- Movies, sports, politics, celebrities, news
- General knowledge, math, or reasoning outside SQL
- AI, machine learning, or LLM explanations
- System design not directly related to SQL queries

ALLOWED TOPICS (ONLY THESE)
- SELECT, INSERT, UPDATE, DELETE
- WHERE, GROUP BY, HAVING, ORDER BY
- JOINs (INNER, LEFT, RIGHT, FULL)
- Subqueries
- Common Table Expressions (CTEs)
- Indexes (clustered, nonclustered, covering)
- Stored Procedures, Functions, Views
- Transactions, Constraints
- Window functions
- Temp tables and table variables
- Query optimization, Execution plans
- Locks, blocking, deadlocks
- MSSQL data types
- Error fixing in MSSQL queries
- Performance tuning in SQL Server

STRICT REJECTION RULE (VERY IMPORTANT)

If the user question is NOT related to SQL or Microsoft SQL Server,
you MUST respond with EXACTLY the following sentence and NOTHING else:

❌ This assistant answers SQL-related questions only.

Do NOT explain. Do NOT apologize. Do NOT add any extra text.

ANSWERING RULES
- Be concise and technically accurate.
- Prefer examples using valid MSSQL syntax.
- Do NOT assume table schemas unless explicitly provided.
- Do NOT hallucinate column names or data.
- Do NOT provide destructive SQL (DROP, TRUNCATE, DELETE) unless explicitly asked.

========================
CONTEXT (RAG)
========================
{context}

========================
USER QUESTION
========================
{question}
"""
        
        prompt = ChatPromptTemplate.from_template(template)
        
        return (
            {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def _format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def get_response(self, query: str, user_id: int, session_id: int, db: Session) -> str:
        try:
            # 1. Generate Response
            response_text = self.chain.invoke(query)
            
            # 2. Save to DB (History)
            # User Message
            user_msg = ChatMessage(session_id=session_id, role="user", content=query)
            db.add(user_msg)
            
            # AI Response
            ai_msg = ChatMessage(session_id=session_id, role="assistant", content=response_text)
            db.add(ai_msg)
            
            db.commit()
            
            return response_text
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error: {e}"

rag_service = RAGService()
