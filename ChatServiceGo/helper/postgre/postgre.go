package postgre

import (
	"VisionRAG/ChatServiceGo/config"
	"VisionRAG/ChatServiceGo/model"
	"VisionRAG/shared/database"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

var DB *gorm.DB

func InitMysql() error {
	cfg := config.GetConfig().DBConfig

	db, err := database.InitDB(database.DBConfig{
		Host:     cfg.DBHost,
		Port:     cfg.DBPort,
		User:     cfg.DBUser,
		Password: cfg.DBPassword,
		DBName:   cfg.DBDatabaseName,
		SSLMode:  cfg.SSLMode,
	}, gin.Mode() == gin.DebugMode)

	if err != nil {
		return err
	}

	DB = db
	return migration()
}

func migration() error {
	return DB.AutoMigrate(
		new(model.Message),
		new(model.Session),
	)
}
