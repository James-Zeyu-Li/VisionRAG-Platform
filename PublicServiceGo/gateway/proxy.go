package gateway

import (
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"

	"github.com/gin-gonic/gin"
)

// ReverseProxy 返回一个 Gin 处理函数，将请求转发到指定的后端服务
func ReverseProxy(target string) gin.HandlerFunc {
	return func(c *gin.Context) {
		remote, err := url.Parse(target)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid target URL"})
			return
		}

		proxy := httputil.NewSingleHostReverseProxy(remote)

		// 修改请求头以确保后端服务能正确识别
		c.Request.Host = remote.Host
		c.Request.URL.Host = remote.Host
		c.Request.URL.Scheme = remote.Scheme

		// 如果路径包含 /api/v1，保持不变或根据需要处理
		// 目前前端 proxy 会把 /api 改写为 /api/v1，所以转发到后端的路径已经是正确的
		
		proxy.ServeHTTP(c.Writer, c.Request)
	}
}

// RegisterGatewayRoutes 注册网关转发路由
func RegisterGatewayRoutes(r *gin.Engine, chatServiceAddr string) {
	// 需要转发给 ChatServiceGo 的路径前缀
	chatPaths := []string{"/AI", "/image", "/file", "/session"}

	apiV1 := r.Group("/api/v1")
	{
		for _, path := range chatPaths {
			// 使用 Any 以支持 GET, POST 等所有方法
			apiV1.Any(path+"/*any", ReverseProxy(chatServiceAddr))
		}
	}
}
