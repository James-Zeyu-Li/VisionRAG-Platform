package rabbitmq

import (
	"VisionRAG/ChatServiceGo/config"
	"VisionRAG/shared/queue"
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

	// 声明队列
	err = baseMQ.DeclareQueue()
	if err != nil {
		panic("Failed to declare RabbitMQ queue: " + err.Error())
	}

	return &RabbitMQ{baseMQ}
}

func (r *RabbitMQ) Consume(handle func(msg *amqp.Delivery) error) {
	err := r.RabbitMQ.Consume(handle)
	if err != nil {
		log.Printf("Error starting consumer: %v", err)
	}
}

func (r *RabbitMQ) Destroy() {
	r.RabbitMQ.Destroy()
}
