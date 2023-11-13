package services

import (
	"context"
	"fmt"
	"log"
	"net"

	"github.com/UWNetworksLab/app-defined-networks/envoy/pong_pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
)

// Pong implements the pong service
type Pong struct {
	name string
	port int
	pong.PongServiceServer
}

// NewPong returns a new server
func NewPong(name string, pongPort int, pongaddr string) *Pong {
	return &Pong{
		name:      name,
		port:      pongPort,
	}
}

// Run starts the Pong gRPC server and listens for incoming requests.
// It returns an error if the server fails to start or encounters an error.
func (s *Pong) Run() error {
	// Create a new gRPC server instance.
	srv := grpc.NewServer()

	// Register the Pong server implementation with the gRPC server.
	pong.RegisterPongServiceServer(srv, s)

	// Create a TCP listener that listens for incoming requests on the specified port.
	lis, err := net.Listen("tcp", fmt.Sprintf(":%d", s.port))
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	// (Optional) Log a message indicating that the server is running and listening on the specified port.
	log.Printf("pong server running at port: %d", s.port)

	// Start serving incoming requests using the registered implementation.
	return srv.Serve(lis)
}

func (s *Pong) Pong(ctx context.Context, req *pong.PongRequest) (*pong.PongResponse, error) {
	pongResponse := &pong.GetPongResponse{body: "pong response"}

	return pongResponse, err
}

func (s *Pong) PongEcho(ctx context.Context, req *pong.PongEchoRequest) (*pong.PongEchoResponse, error) {

	body := req.GetBody()
	pongEchoResponse := &pong.PongEchoResponse{body: body}

	return pongEchoResponse, err
}
