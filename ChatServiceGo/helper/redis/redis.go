package redis

import (
	"VisionRAG/ChatServiceGo/config"
	"VisionRAG/pkg/cache"
	"github.com/go-redis/redis/v8"
)

var Rdb *redis.Client

func Init() {
	conf := config.GetConfig()
	rdb, err := cache.InitRedis(cache.RedisConfig{
		Host:     conf.RedisConfig.RedisHost,
		Port:     conf.RedisConfig.RedisPort,
		Password: conf.RedisConfig.RedisPassword,
		DB:       conf.RedisConfig.RedisDb,
	})
	if err != nil {
		panic("Redis init failed: " + err.Error())
	}
	Rdb = rdb
}
