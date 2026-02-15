package cache

import (
	"fmt"
	"github.com/go-redis/redis/v8"
)

type RedisConfig struct {
	Host     string
	Port     int
	Password string
	DB       int
}

func InitRedis(cfg RedisConfig) (*redis.Client, error) {
	addr := fmt.Sprintf("%s:%d", cfg.Host, cfg.Port)
	rdb := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: cfg.Password,
		DB:       cfg.DB,
	})

	// 测试连接
	return rdb, nil
}
