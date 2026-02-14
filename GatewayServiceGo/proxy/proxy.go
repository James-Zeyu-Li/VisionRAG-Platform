package proxy

import (
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"time"

	"github.com/gin-gonic/gin"
)

// ProxyHandler 创建一个支持 Header 注入和流式转发的代理
func ProxyHandler(target string) gin.HandlerFunc {
	remote, err := url.Parse(target)
	if err != nil {
		log.Panicf("Failed to parse target URL %s: %v", target, err)
	}

	proxy := httputil.NewSingleHostReverseProxy(remote)

	// 自定义 Director：在转发前修改请求
	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)
		// 确保 Host 头正确设置
		req.Host = remote.Host
	}

	// 自定义超时控制 (适合 AI 长连接)
	proxy.Transport = &http.Transport{
		ResponseHeaderTimeout: 60 * time.Second,
		IdleConnTimeout:       90 * time.Second,
	}

	return func(c *gin.Context) {
		// 1. 从 Context 获取鉴权后的用户信息并注入 Header
		if username, exists := c.Get("userName"); exists {
			c.Request.Header.Set("X-User-Name", username.(string))
		}
		if userID, exists := c.Get("userID"); exists {
			c.Request.Header.Set("X-User-ID", userID.(string))
		}
		// 注入 Request-ID
		if rid, exists := c.Get("X-Request-ID"); exists {
			c.Request.Header.Set("X-Request-ID", rid.(string))
		}

		log.Printf("[Gateway Proxy] Forwarding %s %s to %s", c.Request.Method, c.Request.URL.Path, target)
		
		// 2. 执行转发
		proxy.ServeHTTP(c.Writer, c.Request)
	}
}
