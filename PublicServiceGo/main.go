package main

import (
	"VisionRAG/PublicServiceGo/config"
	"VisionRAG/PublicServiceGo/helper/postgre"
	"VisionRAG/PublicServiceGo/helper/rabbitmq"
	"VisionRAG/PublicServiceGo/helper/redis"
	"VisionRAG/PublicServiceGo/router"
	"fmt"
	"log"
)

func StartServer(addr string, port int) error {
	r := router.InitRouter()
	return r.Run(fmt.Sprintf("%s:%d", addr, port))
}

func main() {
	// 1. 初始化配置
	if err := config.InitConfig(); err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}
	
	conf := config.GetConfig()
	log.Printf("Connecting to DB at %s:%d as user %s", conf.DBConfig.DBHost, conf.DBConfig.DBPort, conf.DBConfig.DBUser)

	// 2. 初始化 postgres
	if err := postgre.InitMysql(); err != nil {
		log.Fatalf("CRITICAL: Database connection failed: %v", err)
	}

	// 3. 初始化其他组件
	redis.Init()
	log.Println("Redis init success")

	rabbitmq.InitRabbitMQ()
	log.Println("RabbitMQ init success")

	log.Printf("Starting server on %s:%d\n", conf.MainConfig.Host, conf.MainConfig.Port)
	if err := StartServer(conf.MainConfig.Host, conf.MainConfig.Port); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
