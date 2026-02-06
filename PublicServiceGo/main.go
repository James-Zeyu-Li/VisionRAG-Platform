package main

import (
	"VisionRAG/PublicServiceGo/config"
	"VisionRAG/PublicServiceGo/helper/mysql"
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
	conf := config.GetConfig()
	host := conf.MainConfig.Host
	port := conf.MainConfig.Port

	// 初始化 mysql
	if err := mysql.InitMysql(); err != nil {
		log.Println("InitMysql error: " + err.Error())
		return
	}

	// 初始化 redis
	redis.Init()
	log.Println("redis init success")

	log.Printf("Starting server on %s:%d\n", host, port)
	err := StartServer(host, port)
	if err != nil {
		panic(err)
	}
}
