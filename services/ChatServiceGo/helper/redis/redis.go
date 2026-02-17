package redis

import (
	"VisionRAG/ChatServiceGo/config"
	"VisionRAG/shared/cache"
	"context"
	"fmt"
	"strings"

	"github.com/redis/go-redis/v9"
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

// GenerateIndexName 生成索引名称 (例如: idx:rag:filename)
func GenerateIndexName(filename string) string {
	return fmt.Sprintf("idx:rag:%s", filename)
}

// GenerateIndexNamePrefix 生成 Key 前缀 (例如: rag:filename:)
func GenerateIndexNamePrefix(filename string) string {
	return fmt.Sprintf("rag:%s:", filename)
}

// InitRedisIndex 初始化 Redis 向量索引 (RediSearch)
func InitRedisIndex(ctx context.Context, filename string, dimension int) error {
	indexName := GenerateIndexName(filename)
	prefix := GenerateIndexNamePrefix(filename)

	// 检查索引是否存在
	_, err := Rdb.Do(ctx, "FT.INFO", indexName).Result()
	if err == nil {
		// 索引已存在
		return nil
	}

	// FT.CREATE idx:rag:filename ON HASH PREFIX 1 rag:filename:
	// SCHEMA vector VECTOR HNSW 6 TYPE FLOAT32 DIM dimension DISTANCE COSINE content TEXT
	args := []interface{}{
		"FT.CREATE", indexName,
		"ON", "HASH",
		"PREFIX", "1", prefix,
		"SCHEMA",
		"vector", "VECTOR", "HNSW", "6",
		"TYPE", "FLOAT32",
		"DIM", dimension,
		"DISTANCE", "COSINE",
		"content", "TEXT",
		"metadata", "TEXT",
	}

	return Rdb.Do(ctx, args...).Err()
}

// DeleteRedisIndex 删除索引及其数据
func DeleteRedisIndex(ctx context.Context, filename string) error {
	indexName := GenerateIndexName(filename)
	prefix := GenerateIndexNamePrefix(filename)

	// 1. 删除索引 (FT.DROPINDEX)
	Rdb.Do(ctx, "FT.DROPINDEX", indexName)

	// 2. 删除数据 (SCAN & DEL)
	iter := Rdb.Scan(ctx, 0, prefix+"*", 0).Iterator()
	for iter.Next(ctx) {
		if err := Rdb.Del(ctx, iter.Val()).Err(); err != nil {
			return err
		}
	}

	return iter.Err()
}

// GetUserFileName 获取干净的文件名
func GetUserFileName(fullPath string) string {
	parts := strings.Split(fullPath, "/")
	return parts[len(parts)-1]
}
