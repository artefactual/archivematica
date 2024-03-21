package store

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"

	sqlc "github.com/artefactual/archivematica/hack/ccp/sqlc/mysql/sqlcmysql"

	"github.com/go-logr/logr"
	mysqldriver "github.com/go-sql-driver/mysql"
)

func connectToMySQL(logger logr.Logger, dsn string) (*sql.DB, error) {
	config, err := mysqldriver.ParseDSN(dsn)
	if err != nil {
		return nil, fmt.Errorf("error parsing dsn: %v (%s)", err, dsn)
	}
	config.Collation = "utf8mb4_unicode_ci"
	config.Loc = time.UTC
	config.ParseTime = true
	config.MultiStatements = true
	config.Params = map[string]string{
		"time_zone": "'+00:00'",
	}

	conn, err := mysqldriver.NewConnector(config)
	if err != nil {
		return nil, fmt.Errorf("error creating connector: %w", err)
	}

	db := sql.OpenDB(conn)

	// Set reasonable sizes on the built-in pool.
	db.SetMaxOpenConns(30)
	db.SetMaxIdleConns(30)
	db.SetConnMaxLifetime(time.Minute)

	var version string
	err = db.QueryRow("SELECT VERSION()").Scan(&version)
	if err != nil {
		return nil, err
	}

	logger.V(2).Info("Connected to MySQL.", "version", version)

	return db, nil
}

type mysqlStoreImpl struct {
	logger  logr.Logger
	pool    *sql.DB
	queries *sqlc.Queries
}

var _ Store = (*mysqlStoreImpl)(nil)

func newMySQLStore(logger logr.Logger, pool *sql.DB) (*mysqlStoreImpl, error) {
	queries, err := sqlc.Prepare(context.Background(), pool)
	if err != nil {
		return nil, err
	}

	return &mysqlStoreImpl{
		logger:  logger,
		pool:    pool,
		queries: queries,
	}, nil
}

func (s *mysqlStoreImpl) RemoveTransientData(ctx context.Context) error {
	conn, _ := s.pool.Conn(ctx)
	defer conn.Close()

	q := sqlc.New(conn)

	// q.GetLock(ctx)
	// defer q.ReleaseLock(ctx)

	if err := q.CleanUpActiveTasks(ctx); err != nil {
		return err
	}

	if err := q.CleanUpActiveTransfers(ctx); err != nil {
		return err
	}

	if err := q.CleanUpTasksWithAwaitingJobs(ctx); err != nil {
		return err
	}

	if err := q.CleanUpAwaitingJobs(ctx); err != nil {
		return err
	}

	if err := q.CleanUpActiveSIPs(ctx); err != nil {
		return err
	}

	if err := q.CleanUpActiveJobs(ctx); err != nil {
		return err
	}

	return nil
}

func (s *mysqlStoreImpl) Running() bool {
	return s != nil
}

func (s *mysqlStoreImpl) Close() error {
	var err error

	if s.pool != nil {
		err = errors.Join(err, s.pool.Close())
	}

	if s.queries != nil {
		err = errors.Join(err, s.queries.Close())
	}

	return err
}
