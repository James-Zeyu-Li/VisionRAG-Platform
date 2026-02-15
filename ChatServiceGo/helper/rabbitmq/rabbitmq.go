package rabbitmq

import (
	"VisionRAG/ChatServiceGo/config"
	"VisionRAG/pkg/queue"
	"fmt"
	"log"

	amqp "github.com/rabbitmq/amqp091-go"
)

var conn *amqp.Connection

func initConn() {
	c := config.GetConfig()
	connection, err := queue.NewConnection(queue.MQConfig{
		Host:     c.RabbitmqHost,
		Port:     c.RabbitmqPort,
		User:     c.RabbitmqUsername,
		Password: c.RabbitmqPassword,
		VHost:    c.RabbitmqVhost,
	})
	if err != nil {
		log.Fatalf("RabbitMQ connection failed: %v", err)
	}
	conn = connection
}

type RabbitMQ struct {
	*queue.RabbitMQ
}

func NewWorkRabbitMQ(queueName string) *RabbitMQ {
	if conn == nil {
		initConn()
	}
	
	baseMQ, err := queue.NewRabbitMQ(conn, "", queueName, queueName)
	if err != nil {
		panic("Failed to create RabbitMQ channel: " + err.Error())
	}
	
	return &RabbitMQ{baseMQ}
}

func (r *RabbitMQ) Consume(handle func(msg *amqp.Delivery) error) {
	q, err := r.RabbitMQ.DeclareQueue()
	if err != nil {
		panic(err)
	}

	msgs, err := r.RabbitMQ.GetChannel().Consume(q.Name, "", true, false, false, false, nil)
	if err != nil {
		panic(err)
	}

	for msg := range msgs {
		m := msg
		if err := handle(&m); err != nil {
			fmt.Println("Error handling message:", err.Error())
		}
	}
}

func (r *RabbitMQ) Destroy() {
	r.RabbitMQ.Destroy()
}
