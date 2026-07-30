import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  Button,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Snackbar,
  Alert
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import api from '../utils/api'

export default function ImageRecognition() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' })

  const fileInputRef = useRef(null)
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!selectedFile) return

    const file = selectedFile
    const imageUrl = URL.createObjectURL(file)

    // 追加用户上传图片消息
    const userMsg = {
      role: 'user',
      content: `已上传图片: ${file.name}`,
      imageUrl
    }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    const formData = new FormData()
    formData.append('image', file)

    try {
      const response = await api.post('/image/recognize', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      if (response.data && response.data.class_name) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `识别结果: ${response.data.class_name}` }
        ])
      } else {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `[错误] ${response.data.status_msg || '识别失败'}` }
        ])
      }
    } catch (error) {
      console.error('Upload error:', error)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `[错误] 无法连接到服务器或上传失败: ${error.message}` }
      ])
    } finally {
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      setLoading(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      {/* 左侧说明列表 */}
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
        <Box sx={{ p: 2, textCenter: 'center', borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
          <Typography variant="h6" align="center" sx={{ fontWeight: 600, color: '#2c3e50' }}>图像识别</Typography>
        </Box>
        <List>
          <ListItem disablePadding>
            <ListItemButton selected>
              <ListItemText primary="图像识别助手" />
            </ListItemButton>
          </ListItem>
        </List>
      </Paper>

      {/* 右侧主交互区 */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* 顶部 TopBar */}
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
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#2c3e50' }}>
            AI 图像识别助手
          </Typography>
        </Paper>

        {/* 消息历史与识别结果 */}
        <Box sx={{ flex: 1, p: 3, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {messages.map((msg, index) => (
            <Box
              key={index}
              sx={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '70%',
                p: 2,
                borderRadius: 3,
                background: msg.role === 'user'
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  : 'rgba(255, 255, 255, 0.95)',
                color: msg.role === 'user' ? '#fff' : '#2c3e50',
                boxShadow: '0 4px 15px rgba(0,0,0,0.06)'
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                {msg.role === 'user' ? '你' : 'AI'}:
              </Typography>
              <Typography variant="body1">{msg.content}</Typography>
              {msg.imageUrl && (
                <Box
                  component="img"
                  src={msg.imageUrl}
                  alt="上传的图片"
                  sx={{
                    maxWidth: 250,
                    borderRadius: 2,
                    mt: 1.5,
                    boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
                  }}
                />
              )}
            </Box>
          ))}
          <div ref={chatEndRef} />
        </Box>

        {/* 底部上传区 */}
        <Paper
          square
          sx={{
            p: 2.5,
            px: 3,
            background: 'rgba(255, 255, 255, 0.96)',
            borderTop: '1px solid rgba(0,0,0,0.06)'
          }}
        >
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Button
              variant="outlined"
              component="label"
              startIcon={<CloudUploadIcon />}
              sx={{ flex: 1, height: 50, borderRadius: 2 }}
            >
              {selectedFile ? selectedFile.name : '选择或上传图片文件'}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                hidden
                onChange={handleFileSelect}
              />
            </Button>

            <Button
              type="submit"
              variant="contained"
              disabled={!selectedFile || loading}
              sx={{
                height: 50,
                px: 4,
                borderRadius: 2,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              }}
            >
              {loading ? '识别中...' : '发送图片'}
            </Button>
          </Box>
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
