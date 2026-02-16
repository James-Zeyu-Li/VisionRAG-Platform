package middleware

import (
	"VisionRAG/GatewayServiceGo/config"
	"fmt"
	"log"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

type MyClaims struct {
	UserID   uint   `json:"user_id"`
	Username string `json:"username"`
	jwt.RegisteredClaims
}

// Auth 网关统一鉴权中间件
func Auth() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 1. 生成 Request-ID 用于全链路追踪
		requestID := uuid.New().String()
		c.Set("X-Request-ID", requestID)
		c.Header("X-Request-ID", requestID)

		var token string
		authHeader := c.GetHeader("Authorization")
		if authHeader != "" && strings.HasPrefix(authHeader, "Bearer ") {
			token = strings.TrimPrefix(authHeader, "Bearer ")
		} else {
			token = c.Query("token")
		}

		if token == "" {
			log.Printf("[Gateway Auth] No token provided for request: %s", c.Request.URL.Path)
			c.JSON(http.StatusUnauthorized, gin.H{"status_code": 2006, "status_msg": "Unauthorized: No Token"})
			c.Abort()
			return
		}

		// 验证 Token
		key := config.GetConfig().JwtConfig.Key
		claims := &MyClaims{}
		t, err := jwt.ParseWithClaims(token, claims, func(token *jwt.Token) (interface{}, error) {
			return []byte(key), nil
		})

		if err != nil || !t.Valid {
			log.Printf("[Gateway Auth] Invalid token: %v", err)
			c.JSON(http.StatusUnauthorized, gin.H{"status_code": 2006, "status_msg": "Unauthorized: Invalid Token"})
			c.Abort()
			return
		}

		// 2. 将用户信息存入 Gin Context，供后续 Proxy 逻辑注入 Header
		c.Set("userName", claims.Username)
		c.Set("userID", fmt.Sprintf("%d", claims.UserID))
		
		log.Printf("[Gateway Auth] Success! User: %s, RequestID: %s", claims.Username, requestID)
		c.Next()
	}
}
