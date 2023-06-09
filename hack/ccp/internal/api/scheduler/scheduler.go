package scheduler

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"time"

	"github.com/bufbuild/connect-go"
	grpchealth "github.com/bufbuild/connect-grpchealth-go"
	grpcreflect "github.com/bufbuild/connect-grpcreflect-go"
	"github.com/go-logr/logr"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"

	"github.com/artefactual/archivematica/hack/ccp/internal/api/corsutil"
	schedulerv1 "github.com/artefactual/archivematica/hack/ccp/internal/gen/archivematica/ccp/scheduler/v1"
	"github.com/artefactual/archivematica/hack/ccp/internal/gen/archivematica/ccp/scheduler/v1/schedulerv1connect"
)

type Server struct {
	logger logr.Logger
	config Config
	server *http.Server
	ln     net.Listener
}

func New(logger logr.Logger, config Config) *Server {
	return &Server{
		logger: logger,
		config: config,
	}
}

func (s *Server) Run() error {
	compress1KB := connect.WithCompressMinBytes(1024)

	mux := http.NewServeMux()
	mux.Handle(schedulerv1connect.NewSchedulerServiceHandler(
		s, compress1KB,
	))
	mux.Handle(grpchealth.NewHandler(
		grpchealth.NewStaticChecker(schedulerv1connect.SchedulerServiceName),
		compress1KB,
	))
	mux.Handle(grpcreflect.NewHandlerV1(
		grpcreflect.NewStaticReflector(schedulerv1connect.SchedulerServiceName),
		compress1KB,
	))
	mux.Handle(grpcreflect.NewHandlerV1Alpha(
		grpcreflect.NewStaticReflector(schedulerv1connect.SchedulerServiceName),
		compress1KB,
	))

	s.server = &http.Server{
		Addr: s.config.Listen,
		Handler: h2c.NewHandler(
			corsutil.New().Handler(mux),
			&http2.Server{},
		),
		ReadHeaderTimeout: time.Second,
		ReadTimeout:       5 * time.Minute,
		WriteTimeout:      5 * time.Minute,
		MaxHeaderBytes:    8 * 1024, // 8KiB
	}

	var err error
	if s.ln, err = net.Listen("tcp", s.config.Listen); err != nil {
		return err
	}

	go func() {
		s.logger.Info("Listening...", "addr", s.ln.Addr())
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
		if err := s.server.Shutdown(ctx); err != nil {
			return err
		}
	}

	return nil
}
