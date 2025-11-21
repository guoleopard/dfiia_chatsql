<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const databaseTypes = ['mysql', 'postgresql', 'sqlserver']
const dbConfig = reactive({
  type: 'mysql',
  host: '192.168.8.8',
  port: 23306,
  database: 'dfemr3.0',
  username: 'root',
  password: 'mysql_R8xHji'
})

const ollamaConfig = reactive({
  apiUrl: 'http://localhost:11434',
  model: 'deepseek-r1:14b',
  temperature: 0.7,
  topP: 0.9,
  maxTokens: 512
})

const naturalLanguageInput = ref('')
const sqlResult = ref([])
const tableColumns = ref([])
const generatedSql = ref('')
const isLoading = ref(false)
const ollamaConfigVisible = ref(false)

// 连接数据库
const connectDatabase = async () => {
  try {
    isLoading.value = true
    const response = await fetch('http://localhost:8000/api/connect', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(dbConfig)
    })
    
    if (response.ok) {
      ElMessage.success('数据库连接成功')
    } else {
      const error = await response.json()
      ElMessage.error(`连接失败: ${error.detail}`)
    }
  } catch (error) {
    ElMessage.error(`连接失败: ${error.message}`)
  } finally {
    isLoading.value = false
  }
}

// 保存Ollama配置
const saveOllamaConfig = async () => {
  try {
    isLoading.value = true
    const response = await fetch('http://localhost:8000/api/ollama/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(ollamaConfig)
    })
    
    if (response.ok) {
      ElMessage.success('Ollama配置保存成功')
      ollamaConfigVisible.value = false
    } else {
      const error = await response.json()
      ElMessage.error(`保存失败: ${error.detail}`)
    }
  } catch (error) {
    ElMessage.error(`保存失败: ${error.message}`)
  } finally {
    isLoading.value = false
  }
}

// 获取Ollama配置
const getOllamaConfig = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/ollama/config')
    if (response.ok) {
      const config = await response.json()
      Object.assign(ollamaConfig, config)
    }
  } catch (error) {
    console.error('获取Ollama配置失败:', error)
  }
}

// 页面加载时获取Ollama配置
getOllamaConfig()

// 执行自然语言查询
const executeQuery = async () => {
  if (!naturalLanguageInput.value.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }
  
  try {
    isLoading.value = true
    const response = await fetch('http://localhost:8000/api/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: naturalLanguageInput.value
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      sqlResult.value = result.data
      tableColumns.value = result.columns.map(col => ({
        prop: col,
        label: col
      }))
      generatedSql.value = result.sql
      ElMessage.success('查询成功')
    } else {
      const error = await response.json()
      ElMessage.error(`查询失败: ${error.detail}`)
    }
  } catch (error) {
    ElMessage.error(`查询失败: ${error.message}`)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="chatsql-container">
    <header class="chatsql-header">
      <h1>ChatSQL - 自然语言转SQL工具</h1>
    </header>
    
    <main class="chatsql-main">
      <!-- 数据库连接配置 -->
      <div class="connection-section">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h2>数据库连接配置</h2>
          <el-button type="primary" @click="ollamaConfigVisible = true">
            Ollama配置
          </el-button>
        </div>
        <el-form :model="dbConfig" label-width="120px">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="数据库类型">
                <el-select v-model="dbConfig.type" placeholder="请选择数据库类型">
                  <el-option 
                    v-for="type in databaseTypes" 
                    :key="type" 
                    :label="type" 
                    :value="type"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="主机地址">
                <el-input v-model="dbConfig.host" placeholder="请输入主机地址" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="端口">
                <el-input v-model.number="dbConfig.port" placeholder="请输入端口" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="数据库名称">
                <el-input v-model="dbConfig.database" placeholder="请输入数据库名称" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="用户名">
                <el-input v-model="dbConfig.username" placeholder="请输入用户名" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="密码">
                <el-input v-model="dbConfig.password" type="password" placeholder="请输入密码" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item>
            <el-button type="primary" @click="connectDatabase" :loading="isLoading">
              连接数据库
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      
      <!-- Ollama配置弹窗 -->
      <el-dialog v-model="ollamaConfigVisible" title="Ollama配置" width="600px">
        <el-form :model="ollamaConfig" label-width="120px">
          <el-form-item label="API地址">
            <el-input v-model="ollamaConfig.apiUrl" placeholder="请输入Ollama API地址" />
          </el-form-item>
          
          <el-form-item label="模型名称">
            <el-input v-model="ollamaConfig.model" placeholder="请输入模型名称" />
          </el-form-item>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="Temperature">
                <el-slider v-model="ollamaConfig.temperature" :min="0" :max="1" :step="0.1" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="Top P">
                <el-slider v-model="ollamaConfig.topP" :min="0" :max="1" :step="0.1" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="Max Tokens">
                <el-input v-model.number="ollamaConfig.maxTokens" placeholder="请输入最大Token数" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="ollamaConfigVisible = false">取消</el-button>
            <el-button type="primary" @click="saveOllamaConfig" :loading="isLoading">
              保存
            </el-button>
          </span>
        </template>
      </el-dialog>
      
      <!-- 查询输入区域 -->
      <div class="query-section">
        <h2>自然语言查询</h2>
        <el-input
          v-model="naturalLanguageInput"
          type="textarea"
          :rows="3"
          placeholder="请输入您的查询需求，例如：'查询所有用户的姓名和邮箱'"
          style="margin-bottom: 10px"
        />
        <el-button type="primary" @click="executeQuery" :loading="isLoading" style="margin-right: 10px">
          执行查询
        </el-button>
      </div>
      
      <!-- 生成的SQL语句区域 -->
      <div class="sql-section" v-if="generatedSql">
        <h2>生成的SQL语句</h2>
        <el-input
          v-model="generatedSql"
          type="textarea"
          :rows="3"
          readonly
          style="margin-bottom: 10px"
        />
      </div>
      
      <!-- 查询结果区域 -->
      <div class="result-section" v-if="sqlResult.length > 0">
        <h2>查询结果</h2>
        <el-table :data="sqlResult" style="width: 100%">
          <el-table-column 
            v-for="column in tableColumns" 
            :key="column.prop" 
            :prop="column.prop" 
            :label="column.label"
          />
        </el-table>
      </div>
    </main>
  </div>
</template>

<style scoped>
.chatsql-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.chatsql-header {
  text-align: center;
  margin-bottom: 30px;
}

.chatsql-header h1 {
  color: #333;
  font-size: 28px;
  margin: 0;
}

.connection-section,
.query-section,
.result-section {
  background-color: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.connection-section h2,
.query-section h2,
.result-section h2 {
  color: #333;
  font-size: 20px;
  margin-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 10px;
}
</style>
