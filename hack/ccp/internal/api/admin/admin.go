package admin

import (
	"context"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/bufbuild/connect-go"
	"github.com/go-logr/logr"
	"golang.org/x/net/http2"
	"golang.org/x/net/http2/h2c"

	"github.com/artefactual/archivematica/hack/ccp/internal/api/corsutil"
	adminv1 "github.com/artefactual/archivematica/hack/ccp/internal/gen/archivematica/ccp/admin/v1"
	"github.com/artefactual/archivematica/hack/ccp/internal/gen/archivematica/ccp/admin/v1/adminv1connect"
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
	mux.Handle(adminv1connect.NewAdminServiceHandler(
		s, connect.WithCompressMinBytes(1024),
	))

	addr := "localhost:11112"
	if port := os.Getenv("PORT"); port != "" {
		addr = ":" + port
	}

	s.server = &http.Server{
		Addr: addr,
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
	if s.ln, err = net.Listen("tcp", addr); err != nil {
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

func (s *Server) AwaitingDecisions(ctx context.Context, req *connect.Request[adminv1.AwaitingDecisionsRequest]) (*connect.Response[adminv1.AwaitingDecisionsResponse], error) {
	return connect.NewResponse(&adminv1.AwaitingDecisionsResponse{}), nil
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
