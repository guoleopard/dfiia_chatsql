from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import psycopg2
import pyodbc
import requests
from typing import Dict, List, Any
import os

app = FastAPI(title="ChatSQL Backend", version="1.0.0")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量存储数据库连接和元数据
db_connection = None
db_type = None
db_name = None
db_metadata = None

# 全局变量存储Ollama配置
ollama_config = {
    "api_url": "http://localhost:11434",
    "model": "llama2",
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 512
}

# 数据库连接配置模型
class DBConfig(BaseModel):
    type: str
    host: str
    port: int
    database: str
    username: str
    password: str

# 自然语言查询模型
class NLQuery(BaseModel):
    query: str

# Ollama配置模型
class OllamaConfig(BaseModel):
    apiUrl: str
    model: str
    temperature: float
    topP: float
    maxTokens: int

# 连接数据库
@app.post("/api/connect")
async def connect_database(config: DBConfig):
    global db_connection, db_type, db_name, db_metadata
    
    try:
        # 根据数据库类型创建连接
        if config.type == "mysql":
            db_connection = mysql.connector.connect(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.username,
                password=config.password
            )
        elif config.type == "postgresql":
            db_connection = psycopg2.connect(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.username,
                password=config.password
            )
        elif config.type == "sqlserver":
            db_connection = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={config.host},{config.port};DATABASE={config.database};UID={config.username};PWD={config.password}"
            )
        else:
            raise HTTPException(status_code=400, detail="不支持的数据库类型")
        
        db_type = config.type
        db_name = config.database
        
        # 读取数据库元数据
        db_metadata = await load_database_metadata()
        
        return {"message": "数据库连接成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"连接失败: {str(e)}")

# 读取数据库元数据
async def load_database_metadata():
    global db_connection, db_type
    
    if not db_connection:
        raise HTTPException(status_code=500, detail="数据库未连接")
    
    try:
        cursor = db_connection.cursor()
        metadata = {}
        
        # 获取所有表
        if db_type == "mysql":
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
        elif db_type == "postgresql":
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [table[0] for table in cursor.fetchall()]
        elif db_type == "sqlserver":
            cursor.execute("SELECT name FROM sys.tables")
            tables = [table[0] for table in cursor.fetchall()]
        
        # 为每个表获取字段信息
        for table in tables:
            if db_type == "mysql":
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                column_info = [f"{col[0]} {col[1]}" for col in columns]
            elif db_type == "postgresql":
                cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
                columns = cursor.fetchall()
                column_info = [f"{col[0]} {col[1]}" for col in columns]
            elif db_type == "sqlserver":
                cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'")
                columns = cursor.fetchall()
                column_info = [f"{col[0]} {col[1]}" for col in columns]
        
        metadata[table] = column_info
        
        cursor.close()
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取元数据失败: {str(e)}")

# 自然语言转SQL并执行
@app.post("/api/query")
async def natural_language_to_sql(query: NLQuery):
    global db_connection, db_type, db_name, db_metadata, ollama_config
    
    if not db_connection:
        raise HTTPException(status_code=500, detail="数据库未连接")
    
    try:
        # 构建提示词
        prompt = f"""
你是一个SQL专家，需要根据用户的自然语言查询生成准确的SQL语句。

数据库类型: {db_type}
数据库名称: {db_name}

数据库表结构:
{db_metadata}

用户查询: {query.query}

请生成符合以下要求的SQL语句:
1. 严格遵循{db_type}的SQL语法
2. 只返回SQL语句，不要添加任何解释或说明
3. 确保SQL语句准确无误，能够正确执行
4. 不要包含任何潜在的安全风险，如SQL注入
"""
        
        # 调用Ollama API生成SQL
        response = requests.post(
            f"{ollama_config['api_url']}/api/generate",
            json={
                "model": ollama_config["model"],
                "prompt": prompt,
                "temperature": ollama_config["temperature"],
                "top_p": ollama_config["top_p"],
                "max_tokens": ollama_config["max_tokens"],
                "stream": False
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"调用Ollama失败: {response.text}")
        
        # 解析Ollama返回的SQL语句
        sql = response.json()["response"].strip()
        
        # 执行SQL语句
        cursor = db_connection.cursor()
        cursor.execute(sql)
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description]
        
        # 获取结果
        result = cursor.fetchall()
        
        # 转换为字典列表
        data = [dict(zip(columns, row)) for row in result]
        
        cursor.close()
        
        return {"data": data, "columns": columns, "sql": sql}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

# 执行SQL语句
@app.post("/api/execute_sql")
async def execute_sql(sql: Dict[str, str]):
    global db_connection
    
    if not db_connection:
        raise HTTPException(status_code=500, detail="数据库未连接")
    
    try:
        cursor = db_connection.cursor()
        cursor.execute(sql["sql"])
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description]
        
        # 获取结果
        result = cursor.fetchall()
        
        # 转换为字典列表
        data = [dict(zip(columns, row)) for row in result]
        
        cursor.close()
        
        return {"data": data, "columns": columns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行SQL失败: {str(e)}")

# 保存Ollama配置
@app.post("/api/ollama/config")
async def save_ollama_config(config: OllamaConfig):
    global ollama_config
    
    try:
        ollama_config = {
            "api_url": config.apiUrl,
            "model": config.model,
            "temperature": config.temperature,
            "top_p": config.topP,
            "max_tokens": config.maxTokens
        }
        
        return {"message": "Ollama配置保存成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存Ollama配置失败: {str(e)}")

# 获取Ollama配置
@app.get("/api/ollama/config")
async def get_ollama_config():
    global ollama_config
    
    return {
        "apiUrl": ollama_config["api_url"],
        "model": ollama_config["model"],
        "temperature": ollama_config["temperature"],
        "topP": ollama_config["top_p"],
        "maxTokens": ollama_config["max_tokens"]
    }

# 断开数据库连接
@app.post("/api/disconnect")
async def disconnect_database():
    global db_connection, db_type, db_name, db_metadata
    
    if db_connection:
        db_connection.close()
        db_connection = None
        db_type = None
        db_name = None
        db_metadata = None
    
    return {"message": "数据库已断开连接"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
