# ChatSQL-Backend

ChatSQL的后端服务，使用Python + FastAPI实现自然语言转SQL功能。

## 技术栈

- Python 3.10+
- FastAPI
- MySQL Connector/Python
- psycopg2 (PostgreSQL)
- pyodbc (SQL Server)
- ChromaDB (向量数据库)
- LangChain
- Ollama

## 功能

1. **数据库连接管理**：支持MySQL、PostgreSQL、SQL Server等数据库
2. **元数据读取**：自动读取数据库表结构和字段信息
3. **向量存储**：将数据库元数据存储到本地ChromaDB中
4. **自然语言转SQL**：使用Ollama本地模型将自然语言转换为SQL语句
5. **SQL执行**：执行生成的SQL语句并返回结果

## 安装步骤

### 1. 安装Python依赖

```bash
# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 安装Ollama

请参考Ollama官方文档安装：https://ollama.ai/

安装完成后，拉取所需的模型：

```bash
ollama pull llama2
```

### 3. 配置环境变量

复制`.env`文件并修改配置：

```bash
cp .env.example .env
```

编辑`.env`文件，配置数据库连接信息和Ollama模型。

## 运行项目

```bash
# 激活虚拟环境
venv\Scripts\activate

# 运行FastAPI服务
uvicorn main:app --reload
```

服务将在http://localhost:8000启动。

## API接口

### 1. 连接数据库

**POST** `/api/connect`

请求体：
```json
{
  "type": "mysql",
  "host": "localhost",
  "port": 3306,
  "database": "your_database",
  "username": "root",
  "password": "your_password"
}
```

### 2. 自然语言查询

**POST** `/api/query`

请求体：
```json
{
  "query": "查询所有用户的姓名和邮箱"
}
```

### 3. 执行SQL语句

**POST** `/api/execute_sql`

请求体：
```json
{
  "sql": "SELECT * FROM users"
}
```

### 4. 断开数据库连接

**POST** `/api/disconnect`

## 项目结构

```
ChatSQL-Backend/
├── main.py              # FastAPI应用主文件
├── requirements.txt     # Python依赖列表
├── .env                # 环境变量配置
├── venv/               # Python虚拟环境
└── chroma_db/          # ChromaDB数据存储目录
```

## 使用说明

1. 确保Ollama服务正在运行：`ollama serve`
2. 启动后端服务：`uvicorn main:app --reload`
3. 前端访问http://localhost:5173连接后端服务
4. 配置数据库连接信息并连接
5. 输入自然语言查询，系统将自动生成SQL并执行

## 注意事项

- 确保数据库用户具有足够的权限读取元数据和执行查询
- 第一次连接数据库时，系统会自动读取元数据并存储到ChromaDB
- 建议使用本地Ollama模型，避免网络延迟和隐私问题
