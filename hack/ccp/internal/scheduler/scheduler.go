package scheduler

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/bufbuild/connect-go"
	"github.com/go-logr/logr"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"

	schedulerv1 "github.com/artefactual/archivematica/hack/ccp/internal/gen/archivematica/ccp/scheduler/v1"
	"github.com/artefactual/archivematica/hack/ccp/internal/gen/archivematica/ccp/scheduler/v1/schedulerv1connect"
)

type Server struct {
	logger logr.Logger
	server *http.Server
	ln     net.Listener
}

func New(logger logr.Logger) *Server {
	return &Server{
		logger: logger,
	}
}

func (s *Server) Run() error {
	mux := http.NewServeMux()
	mux.Handle(schedulerv1connect.NewSchedulerServiceHandler(
		s, connect.WithCompressMinBytes(1024),
	))

	addr := "localhost:11111"
	if port := os.Getenv("PORT"); port != "" {
		addr = ":" + port
	}

	s.server = &http.Server{
		Addr: addr,
		Handler: h2c.NewHandler(
			newCORS().Handler(mux),
			&http2.Server{},
		),
		ReadHeaderTimeout: time.Second,
		ReadTimeout:       5 * time.Minute,
		WriteTimeout:      5 * time.Minute,
		MaxHeaderBytes:    8 * 1024, // 8KiB
	}

	var err error
	if s.ln, err = net.Listen("tcp", addr); err != nil {
		return err
	}

	go func() {
		err := s.server.Serve(s.ln)
		if err != nil && err != http.ErrServerClosed {
			s.logger.Error(err, "Failed to start http.Server")
		}
	}()

	return nil
}

func (s *Server) Work(ctx context.Context, stream *connect.BidiStream[schedulerv1.WorkRequest, schedulerv1.WorkResponse]) error {
	for {
		if err := ctx.Err(); err != nil {
			return err
		}

		_, err := stream.Receive()
		if err != nil && errors.Is(err, io.EOF) {
			return nil
		} else if err != nil {
			return fmt.Errorf("receive request: %w", err)
		}

		resp := &schedulerv1.WorkResponse{
			Response: &schedulerv1.WorkResponse_NoJob_{
				NoJob: &schedulerv1.WorkResponse_NoJob{},
			},
		}

		if err := stream.Send(resp); err != nil {
			return fmt.Errorf("send response: %w", err)
		}
	}
}

func (s *Server) Close() error {
	ctx, cancel := context.WithTimeout(context.Background(), time.Second*10)
	defer cancel()

	if s.server != nil {
		s.server.Shutdown(ctx)
	}

	return nil
}
