package redis

import (
	"VisionRAG/ChatServiceGo/config"
	"context"
	"fmt"
	"log"
	"strconv"
	"strings"
	"time"

	"github.com/redis/go-redis/v9"
)

var Rdb *redis.Client

var ctx = context.Background()

func Init() {
	conf := config.GetConfig()
	host := conf.RedisConfig.RedisHost
	port := conf.RedisConfig.RedisPort
	password := conf.RedisConfig.RedisPassword
	db := conf.RedisDb
	addr := host + ":" + strconv.Itoa(port)

	Rdb = redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: password,
		DB:       db,
	})
}

// InitRedisIndex 初始化 Redis 向量索引
func InitRedisIndex(ctx context.Context, filename string, dimension int) error {
	indexName := GenerateIndexName(filename)

	// 检查索引是否存在
	_, err := Rdb.Do(ctx, "FT.INFO", indexName).Result()
	if err == nil {
		// 索引已存在，直接返回
		return nil
	}

	// 创建索引
	// FT.CREATE {index_name} ON HASH PREFIX 1 {prefix} SCHEMA {field_name} VECTOR {algorithm} {count} [{attribute_name} {attribute_value} ...]
	args := []interface{}{
		"FT.CREATE", indexName,
		"ON", "HASH",
		"PREFIX", "1", GenerateIndexNamePrefix(filename),
		"SCHEMA",
		"content", "TEXT",
		"metadata", "TEXT",
		"vector", "VECTOR", "FLAT", "6",
		"TYPE", "FLOAT32",
		"DIM", strconv.Itoa(dimension),
		"DISTANCE_METRIC", "COSINE",
	}

	err = Rdb.Do(ctx, args...).Err()
	if err != nil {
		return fmt.Errorf("failed to create redis index: %w", err)
	}

	log.Printf("Successfully created redis index: %s", indexName)
	return nil
}

// DeleteRedisIndex 删除 Redis 向量索引
func DeleteRedisIndex(ctx context.Context, filename string) error {
	indexName := GenerateIndexName(filename)
	// FT.DROPINDEX {index} [DD]
	// DD 表示同时删除文档内容
	err := Rdb.Do(ctx, "FT.DROPINDEX", indexName, "DD").Err()
	if err != nil && !strings.Contains(err.Error(), "Unknown Index name") {
		return fmt.Errorf("failed to drop redis index: %w", err)
	}
	return nil
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