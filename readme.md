创建一个自然语言转sql项目，项目名称为ChatSQL
前端项目：
- 项目名称：ChatSQL-Frontend
- 技术栈：Vue3 + ElementPlus
- 功能：
  - 数据库连接配置，支持mysql、postgresql、sqlserver等数据库
  - 自然语言输入框
  - 执行sql语句的按钮
  - 以表格的形式显示sql执行结果的区域
后端项目：
- 项目名称：ChatSQL-Backend
- 技术栈：Python + FastAPI
- 功能：
  - 使用Python的虚拟环境，隔离项目依赖
  - 数据库连接配置，支持mysql、postgresql、sqlserver等数据库
  - 读取数据库元数据，包括数据库表、字段，存储到本地的向量数据库中，用于后续的自然语言解析
  - 选择本地的Ollama模型，接收前端发送的自然语言请求，将自然语言转换为sql语句 
  - 调用数据库执行sql语句
  - 将执行结果返回给前端