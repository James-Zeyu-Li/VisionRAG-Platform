package rabbitmq

import (
	"encoding/json"
	"time"
)

type UserEvent struct {
	EventType string    `json:"event_type"`
	UserID    uint      `json:"user_id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	Timestamp time.Time `json:"timestamp"`
}

func GenerateUserRegisteredEvent(userID uint, username, email string) []byte {
	event := UserEvent{
		EventType: "USER_REGISTERED",
		UserID:    userID,
		Username:  username,
		Email:     email,
		Timestamp: time.Now(),
	}
	data, _ := json.Marshal(event)
	return data
}

func GenerateUserLoginEvent(userID uint, username string) []byte {
	event := UserEvent{
		EventType: "USER_LOGIN",
		UserID:    userID,
		Username:  username,
		Timestamp: time.Now(),
	}
	data, _ := json.Marshal(event)
	return data
}
