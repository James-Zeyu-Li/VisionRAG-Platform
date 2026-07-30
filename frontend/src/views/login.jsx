import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Snackbar,
  Alert
} from '@mui/material'
import api from '../utils/api'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' })

  const handleLogin = async (e) => {
    e.preventDefault()

    if (!username.trim()) {
      setToast({ open: true, message: '请输入用户名', severity: 'error' })
      return
    }
    if (password.length < 6) {
      setToast({ open: true, message: '密码长度不能少于6位', severity: 'error' })
      return
    }

    try {
      setLoading(true)
      const response = await api.post('/user/login', { username, password })
      if (response.data.status_code === 1000) {
        localStorage.setItem('token', response.data.token)
        setToast({ open: true, message: '登录成功', severity: 'success' })
        setTimeout(() => {
          navigate('/menu')
        }, 500)
      } else {
        setToast({ open: true, message: response.data.status_msg || '登录失败', severity: 'error' })
      }
    } catch (error) {
      console.error('Login error:', error)
      setToast({ open: true, message: '登录失败，请重试', severity: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        sx={{
          width: 420,
          borderRadius: 4,
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          p: 2
        }}
      >
        <CardContent>
          <Typography
            variant="h4"
            align="center"
            gutterBottom
            sx={{
              fontWeight: 600,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 3
            }}
          >
            登录
          </Typography>

          <Box component="form" onSubmit={handleLogin} sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            <TextField
              label="用户名"
              variant="outlined"
              fullWidth
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />

            <TextField
              label="密码"
              type="password"
              variant="outlined"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={loading}
              sx={{
                height: 48,
                borderRadius: 3,
                fontWeight: 600,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                mt: 1
              }}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : '登录'}
            </Button>

            <Button
              component={Link}
              to="/register"
              color="primary"
              sx={{ textTransform: 'none' }}
            >
              还没有账号？去注册
            </Button>
          </Box>
        </CardContent>
      </Card>

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
