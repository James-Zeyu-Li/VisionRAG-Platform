package redis

import (
	"VisionRAG/PublicServiceGo/config"
	"VisionRAG/shared/cache"
	"context"
	"strings"
	"time"

	"github.com/go-redis/redis/v8"
)

var Rdb *redis.Client
var ctx = context.Background()

func Init() {
	conf := config.GetConfig()
	rdb, err := cache.InitRedis(cache.RedisConfig{
		Host:     conf.RedisConfig.RedisHost,
		Port:     conf.RedisConfig.RedisPort,
		Password: conf.RedisConfig.RedisPassword,
		DB:       conf.RedisDb,
	})
	if err != nil {
		panic("Redis init failed: " + err.Error())
	}
	Rdb = rdb
}

func SetCaptchaForEmail(email, captcha string) error {
	key := GenerateCaptcha(email)
	expire := 2 * time.Minute
	return Rdb.Set(ctx, key, captcha, expire).Err()
}

func CheckCaptchaForEmail(email, userInput string) (bool, error) {
	key := GenerateCaptcha(email)
	storedCaptcha, err := Rdb.Get(ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			return false, nil
		}
		return false, err
	}

	if strings.EqualFold(storedCaptcha, userInput) {
		_ = Rdb.Del(ctx, key).Err()
		return true, nil
	}
	return false, nil
}
