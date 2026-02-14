package rabbitmq

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/streadway/amqp"
)

type UserEvent struct {
	EventType string    `json:"event_type"`
	UserID    uint      `json:"user_id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	Timestamp time.Time `json:"timestamp"`
}

func MQUserEvent(msg *amqp.Delivery) error {
	var event UserEvent
	err := json.Unmarshal(msg.Body, &event)
	if err != nil {
		fmt.Printf("Error unmarshaling user event: %v\n", err)
		return err
	}

	switch event.EventType {
	case "USER_REGISTERED":
		fmt.Printf(" [ChatService] New user joined! Welcome, %s (ID: %d)\n", event.Username, event.UserID)
	case "USER_LOGIN":
		fmt.Printf(" [ChatService MQ] Received login event. User: %s (ID: %d)\n", event.Username, event.UserID)
	}

	return nil
}
