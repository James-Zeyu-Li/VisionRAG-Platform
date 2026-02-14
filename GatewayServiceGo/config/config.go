package config

import (
	"log"
	"os"
	"github.com/BurntSushi/toml"
)

type MainConfig struct {
	Port    int    `toml:"port"`
	AppName string `toml:"appName"`
	Host    string `toml:"host"`
}

type ServicesConfig struct {
	PublicServiceUrl string `toml:"publicServiceUrl"`
	ChatServiceUrl   string `toml:"chatServiceUrl"`
}

type JwtConfig struct {
	Key string `toml:"key"`
}

type Config struct {
	MainConfig     `toml:"mainConfig"`
	ServicesConfig `toml:"services"`
	JwtConfig      `toml:"jwtConfig"`
}

var config *Config

func InitConfig() error {
	if config == nil {
		config = new(Config)
	}
	if _, err := toml.DecodeFile("config/config.toml", config); err != nil {
		log.Printf("Error decoding config file: %v", err)
		return err
	}

	// 环境变量覆盖
	if url := os.Getenv("PUBLIC_SERVICE_URL"); url != "" {
		config.ServicesConfig.PublicServiceUrl = url
	}
	if url := os.Getenv("CHAT_SERVICE_URL"); url != "" {
		config.ServicesConfig.ChatServiceUrl = url
	}

	return nil
}

func GetConfig() *Config {
	if config == nil {
		_ = InitConfig()
	}
	return config
}
