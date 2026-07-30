package database

import (
	"fmt"
	"time"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

type DBConfig struct {
	Host       string
	Port       int
	User       string
	Password   string
	DBName     string
	SSLMode    string
	TimeZone   string
	MaxRetries int
	RetryDelay time.Duration
}

func InitDB(cfg DBConfig, isDebug bool) (*gorm.DB, error) {
	if cfg.SSLMode == "" {
		cfg.SSLMode = "disable"
	}
	if cfg.TimeZone == "" {
		cfg.TimeZone = "UTC"
	}
	if cfg.MaxRetries <= 0 {
		cfg.MaxRetries = 30
	}
	if cfg.RetryDelay <= 0 {
		cfg.RetryDelay = 2 * time.Second
	}

	dsn := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%d sslmode=%s TimeZone=%s",
		cfg.Host, cfg.User, cfg.Password, cfg.DBName, cfg.Port, cfg.SSLMode, cfg.TimeZone)

	// logging setup
	logLevel := logger.Default.LogMode(logger.Silent)
	if isDebug {
		logLevel = logger.Default.LogMode(logger.Info)
	}

	var lastErr error
	for attempt := 1; attempt <= cfg.MaxRetries; attempt++ {
		db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
			Logger: logLevel,
		})
		if err == nil {
			sqlDB, dbErr := db.DB()
			if dbErr == nil {
				pingErr := sqlDB.Ping()
				if pingErr == nil {
					// connection pool size
					sqlDB.SetMaxIdleConns(10)
					sqlDB.SetMaxOpenConns(100)
					sqlDB.SetConnMaxLifetime(time.Hour)
					return db, nil
				}
				lastErr = pingErr
				_ = sqlDB.Close()
			} else {
				lastErr = dbErr
			}
		} else {
			lastErr = err
		}

		if attempt < cfg.MaxRetries {
			time.Sleep(cfg.RetryDelay)
		}
	}

	return nil, fmt.Errorf("failed to initialize database after %d attempts: %w", cfg.MaxRetries, lastErr)
}
