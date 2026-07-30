import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Snackbar,
  Alert
} from '@mui/material'
import ChatIcon from '@mui/icons-material/Chat'
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera'

export default function Menu() {
  const navigate = useNavigate()
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false)
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' })

  const confirmLogout = () => {
    localStorage.removeItem('token')
    setLogoutDialogOpen(false)
    setToast({ open: true, message: '退出登录成功', severity: 'success' })
    setTimeout(() => {
      navigate('/login')
    }, 400)
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <AppBar position="static" sx={{ background: 'rgba(255, 255, 255, 0.1)', backdropFilter: 'blur(10px)' }}>
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 600, color: '#fff' }}>
            AI应用平台
          </Typography>
          <Button
            variant="contained"
            color="error"
            onClick={() => setLogoutDialogOpen(true)}
            sx={{ borderRadius: 2 }}
          >
            退出登录
          </Button>
        </Toolbar>
      </AppBar>

      <Box
        sx={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          p: 3
        }}
      >
        <Grid container spacing={4} maxWidth={900} justifyContent="center">
          <Grid item xs={12} sm={6}>
            <Card
              onClick={() => navigate('/ai-chat')}
              sx={{
                cursor: 'pointer',
                borderRadius: 4,
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(15px)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-10px) scale(1.03)',
                  boxShadow: '0 20px 50px rgba(0, 0, 0, 0.2)',
                }
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 5, px: 3 }}>
                <ChatIcon sx={{ fontSize: 60, color: '#409eff', mb: 2 }} />
                <Typography variant="h5" sx={{ fontWeight: 600, color: '#2c3e50', mb: 1 }}>
                  AI聊天
                </Typography>
                <Typography variant="body1" sx={{ color: '#7f8c8d' }}>
                  与AI进行智能对话
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Card
              onClick={() => navigate('/image-recognition')}
              sx={{
                cursor: 'pointer',
                borderRadius: 4,
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(15px)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-10px) scale(1.03)',
                  boxShadow: '0 20px 50px rgba(0, 0, 0, 0.2)',
                }
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 5, px: 3 }}>
                <PhotoCameraIcon sx={{ fontSize: 60, color: '#67c23a', mb: 2 }} />
                <Typography variant="h5" sx={{ fontWeight: 600, color: '#2c3e50', mb: 1 }}>
                  图像识别
                </Typography>
                <Typography variant="body1" sx={{ color: '#7f8c8d' }}>
                  上传图片进行AI识别
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* 退出确认弹窗 */}
      <Dialog open={logoutDialogOpen} onClose={() => setLogoutDialogOpen(false)}>
        <DialogTitle>提示</DialogTitle>
        <DialogContent>
          <DialogContentText>确定要退出登录吗？</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLogoutDialogOpen(false)}>取消</Button>
          <Button onClick={confirmLogout} color="error" autoFocus>
            确定
          </Button>
        </DialogActions>
      </Dialog>

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
