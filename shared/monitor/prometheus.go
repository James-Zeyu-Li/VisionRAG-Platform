package monitor

import (
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	httpRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"path", "method", "status"},
	)

	httpRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "Duration of HTTP requests in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"path", "method"},
	)

	// AI 推理耗时监控
	AIInferenceDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "ai_inference_duration_seconds",
			Help:    "Duration of AI model inference in seconds",
			Buckets: []float64{.1, .5, 1, 2, 5, 10, 30, 60}, // 针对 AI 响应较慢的情况自定义桶
		},
		[]string{"model_type", "method"}, // method 可以是 "sync" 或 "stream"
	)

	// AI Token 消耗监控
	AITokensUsage = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "ai_tokens_usage_total",
			Help: "Total number of AI tokens consumed",
		},
		[]string{"model_type", "token_type"}, // token_type 可以是 "prompt" 或 "completion"
	)
)

// PrometheusMiddleware 记录 Gin 框架的监控指标
func PrometheusMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.FullPath()
		if path == "" {
			path = "unknown"
		}
		method := c.Request.Method

		c.Next()

		duration := time.Since(start).Seconds()
		status := strconv.Itoa(c.Writer.Status())

		//.inc() atomic +=1
		httpRequestsTotal.WithLabelValues(path, method, status).Inc()

		// record duration
		httpRequestDuration.WithLabelValues(path, method).Observe(duration)

	}
}
