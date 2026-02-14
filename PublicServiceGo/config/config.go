package config

import (
	"log"
	"os"
	"strconv"

	"github.com/BurntSushi/toml"
)

type MainConfig struct {
	Port    int    `toml:"port"`
	AppName string `toml:"appName"`
	Host    string `toml:"host"`
}

type EmailConfig struct {
	Authcode string `toml:"authcode"`
	Email    string `toml:"email"`
}

type RedisConfig struct {
	RedisPort     int    `toml:"port"`
	RedisDb       int    `toml:"db"`
	RedisHost     string `toml:"host"`
	RedisPassword string `toml:"password"`
}

type MysqlConfig struct {
	MysqlPort         int    `toml:"port"`
	MysqlHost         string `toml:"host"`
	MysqlUser         string `toml:"user"`
	MysqlPassword     string `toml:"password"`
	MysqlDatabaseName string `toml:"databaseName"`
	MysqlCharset      string `toml:"charset"`
}

type Rabbitmq struct {
	RabbitmqPort     int    `toml:"port"`
	RabbitmqHost     string `toml:"host"`
	RabbitmqUsername string `toml:"username"`
	RabbitmqPassword string `toml:"password"`
	RabbitmqVhost    string `toml:"vhost"`
}

type Config struct {
	EmailConfig  `toml:"emailConfig"`
	RedisConfig  `toml:"redisConfig"`
	MysqlConfig  `toml:"mysqlConfig"`
	MainConfig   `toml:"mainConfig"`
	Rabbitmq     `toml:"rabbitmqConfig"`
	JwtConfig          `toml:"jwtConfig"`
}

type RedisKeyConfig struct {
	CaptchaPrefix   string
	IndexName       string
	IndexNamePrefix string
}

var DefaultRedisKeyConfig = RedisKeyConfig{
	CaptchaPrefix:   "captcha:%s",
	IndexName:       "rag_docs:%s:idx",
	IndexNamePrefix: "rag_docs:%s:",
}

type JwtConfig struct {
	ExpireDuration int    `toml:"expire_duration"`
	Issuer         string `toml:"issuer"`
	Subject        string `toml:"subject"`
	Key            string `toml:"key"`
}


var config *Config

// Initiate configuration file
func InitConfig() error {
	if config == nil {
		config = new(Config)
	}
	// 1. 先加载文件配置
	if _, err := toml.DecodeFile("config/config.toml", config); err != nil {
		log.Printf("Warning: Could not decode config.toml: %v. Using defaults/env.", err)
	}

	// 2. 检查环境变量并覆盖 (用于 Docker 环境)
	if envHost := os.Getenv("MYSQL_HOST"); envHost != "" {
		config.MysqlConfig.MysqlHost = envHost
		log.Printf("Config: MYSQL_HOST overridden to %s", envHost)
	}
	if envPort := os.Getenv("MYSQL_PORT"); envPort != "" {
		if p, err := strconv.Atoi(envPort); err == nil {
			config.MysqlConfig.MysqlPort = p
			log.Printf("Config: MYSQL_PORT overridden to %d", p)
		}
	}
	if envHost := os.Getenv("REDIS_HOST"); envHost != "" {
		config.RedisConfig.RedisHost = envHost
		log.Printf("Config: REDIS_HOST overridden to %s", envHost)
	}
	if envHost := os.Getenv("RABBITMQ_HOST"); envHost != "" {
		config.Rabbitmq.RabbitmqHost = envHost
		log.Printf("Config: RABBITMQ_HOST overridden to %s", envHost)
	}

	return nil
}

func GetConfig() *Config {
	if config == nil {
		_ = InitConfig()
	}
	return config
}