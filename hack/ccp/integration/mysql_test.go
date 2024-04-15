package integration_test

import (
	"context"
	"database/sql"
	"testing"

	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/modules/mysql"
)

func useMySQL(t *testing.T) string {
	t.Helper()

	if useCompose {
		return "root:12345@tcp(127.0.0.1:62001)/MCP"
	}

	ctx := context.Background()

	container, err := mysql.RunContainer(ctx,
		testcontainers.WithImage("mysql:8.3.0"),
		mysql.WithDatabase("MCP"),
		mysql.WithUsername("root"),
		mysql.WithPassword("12345"),
		mysql.WithScripts("mcp.sql.bz2"),
	)
	if err != nil {
		t.Fatalf("Failed to start container: %s", err)
	}

	t.Cleanup(func() {
		if err := container.Terminate(ctx); err != nil {
			t.Logf("Failed to terminate container: %v", err)
		}
	})

	var (
		db  *sql.DB
		dsn string
	)
	dsn, err = container.ConnectionString(ctx)
	if err != nil {
		t.Fatalf("Failed to create connection string to MySQL server.")
	}
	db, err = sql.Open("mysql", dsn)
	if err != nil {
		t.Fatalf("Failed to connect to MySQL: %v", err)
	}
	defer db.Close()

	if err = db.Ping(); err != nil {
		t.Fatalf("Failed to ping MySQL: %v", err)
	}

	return dsn
}
