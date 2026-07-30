import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  CircularProgress,
  Snackbar,
  Alert
} from '@mui/material'
import api from '../utils/api'

export default function Register() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [captcha, setCaptcha] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [codeLoading, setCodeLoading] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' })

  const sendCode = async () => {
    if (!email.trim()) {
      setToast({ open: true, message: '请先输入邮箱', severity: 'warning' })
      return
    }
    try {
      setCodeLoading(true)
      const response = await api.post('/user/captcha', { email })
      if (response.data.status_code === 1000) {
        setToast({ open: true, message: '验证码发送成功', severity: 'success' })
        setCountdown(60)
        const timer = setInterval(() => {
          setCountdown((prev) => {
            if (prev <= 1) {
              clearInterval(timer)
              return 0
            }
            return prev - 1
          })
        }, 1000)
      } else {
        setToast({ open: true, message: response.data.status_msg || '验证码发送失败', severity: 'error' })
      }
    } catch (error) {
      console.error('Send code error:', error)
      setToast({ open: true, message: '验证码发送失败，请重试', severity: 'error' })
    } finally {
      setCodeLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()

    if (!email.trim()) {
      setToast({ open: true, message: '请输入邮箱', severity: 'error' })
      return
    }
    if (!captcha.trim()) {
      setToast({ open: true, message: '请输入验证码', severity: 'error' })
      return
    }
    if (password.length < 6) {
      setToast({ open: true, message: '密码长度不能少于6位', severity: 'error' })
      return
    }
    if (password !== confirmPassword) {
      setToast({ open: true, message: '两次输入密码不一致', severity: 'error' })
      return
    }

    try {
      setLoading(true)
      const response = await api.post('/user/register', {
        email,
        captcha,
        password
      })
      if (response.data.status_code === 1000) {
        setToast({ open: true, message: '注册成功，请登录', severity: 'success' })
        setTimeout(() => {
          navigate('/login')
        }, 800)
      } else {
        setToast({ open: true, message: response.data.status_msg || '注册失败', severity: 'error' })
      }
    } catch (error) {
      console.error('Register error:', error)
      setToast({ open: true, message: '注册失败，请重试', severity: 'error' })
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
            注册
          </Typography>

          <Box component="form" onSubmit={handleRegister} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="邮箱"
              type="email"
              variant="outlined"
              fullWidth
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <Grid container spacing={1}>
              <Grid item xs={7}>
                <TextField
                  label="验证码"
                  variant="outlined"
                  fullWidth
                  value={captcha}
                  onChange={(e) => setCaptcha(e.target.value)}
                />
              </Grid>
              <Grid item xs={5}>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={sendCode}
                  disabled={codeLoading || countdown > 0}
                  sx={{ height: 56, borderRadius: 2 }}
                >
                  {countdown > 0 ? `${countdown}s` : '发送验证码'}
                </Button>
              </Grid>
            </Grid>

            <TextField
              label="密码"
              type="password"
              variant="outlined"
              fullWidth
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <TextField
              label="确认密码"
              type="password"
              variant="outlined"
              fullWidth
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
              {loading ? <CircularProgress size={24} color="inherit" /> : '注册'}
            </Button>

            <Button
              component={Link}
              to="/login"
              color="primary"
              sx={{ textTransform: 'none' }}
            >
              已有账号？去登录
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
