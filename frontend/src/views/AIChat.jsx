import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Button,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  TextField,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  Snackbar,
  Alert
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import SyncIcon from '@mui/icons-material/Sync'
import AttachFileIcon from '@mui/icons-material/AttachFile'
import VolumeUpIcon from '@mui/icons-material/VolumeUp'
import SendIcon from '@mui/icons-material/Send'
import api from '../utils/api'

export default function AIChat() {
  const navigate = useNavigate()

  // 状态变量
  const [sessions, setSessions] = useState({})
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [tempSession, setTempSession] = useState(false)
  const [currentMessages, setCurrentMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedModel, setSelectedModel] = useState('1')
  const [isStreaming, setIsStreaming] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' })

  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)

  // 校验登录状态与同步历史
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/login')
      return
    }
    syncHistory()
  }, [])

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentMessages])

  // 同步历史会话
  const syncHistory = async () => {
    try {
      const response = await api.get('/chat/history')
      if (response.data && response.data.status_code === 1000) {
        const backendSessions = response.data.sessions || {}
        setSessions(backendSessions)
        const sessionIds = Object.keys(backendSessions)
        if (sessionIds.length > 0 && (!currentSessionId || !backendSessions[currentSessionId])) {
          const firstId = sessionIds[0]
          setCurrentSessionId(firstId)
          setCurrentMessages(backendSessions[firstId].messages || [])
          setTempSession(false)
        }
        setToast({ open: true, message: '历史数据同步成功', severity: 'success' })
      }
    } catch (error) {
      console.error('Failed to sync history:', error)
      setToast({ open: true, message: '同步历史数据失败', severity: 'error' })
    }
  }

  // 切换会话
  const switchSession = (sessionId) => {
    setCurrentSessionId(sessionId)
    setCurrentMessages(sessions[sessionId]?.messages || [])
    setTempSession(false)
  }

  // 创建新会话
  const createNewSession = () => {
    const tempId = 'temp_' + Date.now()
    setCurrentSessionId(tempId)
    setCurrentMessages([])
    setTempSession(true)
  }

  // 播放 TTS 语音
  const playTTS = async (text) => {
    try {
      const response = await api.post('/tts/generate', { text }, { responseType: 'blob' })
      const audioUrl = URL.createObjectURL(response.data)
      const audio = new Audio(audioUrl)
      audio.play()
    } catch (error) {
      console.error('TTS error:', error)
      setToast({ open: true, message: 'TTS 播放失败', severity: 'error' })
    }
  }

  // 触发文件上传
  const triggerFileUpload = () => {
    fileInputRef.current?.click()
  }

  // 处理文档上传 (.md / .txt)
  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      setUploading(true)
      const response = await api.post('/rag/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      if (response.data && response.data.status_code === 1000) {
        setToast({ open: true, message: '文档上传成功并已解析放入知识库！', severity: 'success' })
      } else {
        setToast({ open: true, message: response.data.status_msg || '上传失败', severity: 'error' })
      }
    } catch (error) {
      console.error('File upload error:', error)
      setToast({ open: true, message: '文档上传失败', severity: 'error' })
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  // 发送消息 (支持 SSE 流式和非流式)
  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return

    const userText = inputMessage.trim()
    setInputMessage('')

    const updatedUserMessages = [
      ...currentMessages,
      { role: 'user', content: userText }
    ]
    setCurrentMessages(updatedUserMessages)

    setLoading(true)

    try {
      if (isStreaming) {
        // SSE 流式响应
        const token = localStorage.getItem('token')
        const url = tempSession || !currentSessionId
          ? '/api/AI/chat/send-stream-new-session'
          : '/api/AI/chat/send-stream'

        const requestBody = tempSession || !currentSessionId
          ? { question: userText, modelType: selectedModel }
          : { question: userText, modelType: selectedModel, sessionId: String(currentSessionId) }

        // 初始化一条 AI 的空消息用于打字机效果
        setCurrentMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '', meta: { status: 'streaming' } }
        ])

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token || ''}`
          },
          body: JSON.stringify(requestBody)
        })

        if (!response.ok) {
          throw new Error(`HTTP Error ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let assistantContent = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value, { stream: true })
          
          // 解析可能存在的 SSE data: 前缀
          const lines = chunk.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6).trim()
              try {
                const parsed = JSON.parse(dataStr)
                if (parsed.sessionId) {
                  setCurrentSessionId(parsed.sessionId)
                  setTempSession(false)
                }
              } catch {
                assistantContent += dataStr
              }
            } else if (line.trim() && !line.startsWith('event:')) {
              assistantContent += line
            }
          }

          // 打字机流式追加
          setCurrentMessages((prev) => {
            const next = [...prev]
            const lastIdx = next.length - 1
            if (lastIdx >= 0 && next[lastIdx].role === 'assistant') {
              next[lastIdx] = {
                ...next[lastIdx],
                content: assistantContent
              }
            }
            return next
          })
        }

        // 完成流式传输
        setCurrentMessages((prev) => {
          const next = [...prev]
          const lastIdx = next.length - 1
          if (lastIdx >= 0 && next[lastIdx].role === 'assistant') {
            next[lastIdx] = { ...next[lastIdx], meta: { status: 'done' } }
          }
          return next
        })

      } else {
        // 非流式响应
        const url = tempSession || !currentSessionId
          ? '/AI/chat/send-new-session'
          : '/AI/chat/send'

        const requestBody = tempSession || !currentSessionId
          ? { question: userText, modelType: selectedModel }
          : { question: userText, modelType: selectedModel, sessionId: String(currentSessionId) }

        const response = await api.post(url, requestBody)

        if (response.data && response.data.status_code === 1000) {
          const aiResponse = response.data.Information || response.data.response || '无内容'
          if (response.data.sessionId) {
            setCurrentSessionId(response.data.sessionId)
            setTempSession(false)
          }
          setCurrentMessages((prev) => [
            ...prev,
            { role: 'assistant', content: aiResponse }
          ])
        } else {
          setToast({ open: true, message: response.data.status_msg || '发送失败', severity: 'error' })
        }
      }
    } catch (error) {
      console.error('Send message error:', error)
      setToast({ open: true, message: `发送失败: ${error.message}`, severity: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      {/* 左侧会话列表 */}
      <Paper
        square
        sx={{
          width: 280,
          display: 'flex',
          flexDirection: 'column',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(15px)',
          borderRight: '1px solid rgba(0,0,0,0.08)'
        }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#2c3e50' }}>会话列表</Typography>
          <Button variant="outlined" size="small" onClick={createNewSession}>
            ＋ 新聊天
          </Button>
        </Box>
        <List sx={{ flex: 1, overflowY: 'auto' }}>
          {Object.keys(sessions).map((sId) => (
            <ListItem key={sId} disablePadding>
              <ListItemButton
                selected={currentSessionId === sId}
                onClick={() => switchSession(sId)}
              >
                <ListItemText primary={sessions[sId].name || `会话 ${sId}`} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Paper>

      {/* 右侧聊天区域 */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* 顶部工具栏 */}
        <Paper
          square
          sx={{
            p: 1.5,
            px: 3,
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(0,0,0,0.06)'
          }}
        >
          <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/menu')} sx={{ fontWeight: 600 }}>
            返回
          </Button>
          <Button
            startIcon={<SyncIcon />}
            variant="outlined"
            size="small"
            onClick={syncHistory}
            disabled={!currentSessionId || tempSession}
          >
            同步历史数据
          </Button>

          <Typography variant="body2">模型：</Typography>
          <Select
            size="small"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            sx={{ minWidth: 160 }}
          >
            <MenuItem value="1">阿里百炼</MenuItem>
            <MenuItem value="2">阿里百炼 RAG</MenuItem>
            <MenuItem value="3">阿里百炼 MCP</MenuItem>
            <MenuItem value="4">Ollama 本地大模型</MenuItem>
          </Select>

          <FormControlLabel
            control={
              <Checkbox
                checked={isStreaming}
                onChange={(e) => setIsStreaming(e.target.checked)}
              />
            }
            label="流式响应"
          />

          <Button
            startIcon={<AttachFileIcon />}
            variant="contained"
            color="secondary"
            size="small"
            onClick={triggerFileUpload}
            disabled={uploading}
          >
            上传文档(.md/.txt)
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".md,.txt,text/markdown,text/plain"
            style={{ display: 'none' }}
            onChange={handleFileUpload}
          />
        </Paper>

        {/* 消息历史区域 */}
        <Box sx={{ flex: 1, p: 3, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {currentMessages.map((msg, index) => (
            <Box
              key={index}
              sx={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '75%',
                p: 2,
                borderRadius: 3,
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  : 'rgba(255, 255, 255, 0.95)',
                color: msg.role === 'user' ? '#fff' : '#2c3e50',
                boxShadow: '0 4px 15px rgba(0,0,0,0.06)'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {msg.role === 'user' ? '你' : 'AI'}:
                </Typography>
                {msg.role === 'assistant' && (
                  <IconButton size="small" onClick={() => playTTS(msg.content)}>
                    <VolumeUpIcon fontSize="small" />
                  </IconButton>
                )}
              </Box>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {msg.content}
              </Typography>
            </Box>
          ))}
          <div ref={messagesEndRef} />
        </Box>

        {/* 底部输入框 */}
        <Paper
          square
          sx={{
            p: 2,
            px: 3,
            display: 'flex',
            gap: 2,
            background: 'rgba(255, 255, 255, 0.96)',
            borderTop: '1px solid rgba(0,0,0,0.06)'
          }}
        >
          <TextField
            fullWidth
            placeholder="请输入你的问题..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
            disabled={loading}
            multiline
            maxRows={4}
            size="small"
          />
          <Button
            variant="contained"
            endIcon={<SendIcon />}
            onClick={sendMessage}
            disabled={!inputMessage.trim() || loading}
            sx={{
              borderRadius: 5,
              px: 3,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            }}
          >
            {loading ? '发送中...' : '发送'}
          </Button>
        </Paper>
      </Box>

      <Snackbar
        open={toast.open}
        autoHideDuration={3000}
        onClose={() => setToast(prev => ({ ...prev, open: false }))}
      >
        <Alert severity={toast.severity} sx={{ width: '100%' }}>
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}
