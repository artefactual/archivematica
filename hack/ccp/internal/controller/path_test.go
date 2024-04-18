package controller

import (
	"testing"

	"github.com/google/uuid"
	"gotest.tools/v3/assert"
)

func TestUUIDFromPath(t *testing.T) {
	t.Parallel()

	tests := []struct {
		path string
		want uuid.UUID
	}{
		{
			path: "Test-773f0be9-b2ab-48ac-93d6-4c0b068cb7a4",
			want: uuid.MustParse("773f0be9-b2ab-48ac-93d6-4c0b068cb7a4"),
		},
		{
			path: "Test------------------------------------",
			want: uuid.Nil,
		},
		{
			path: "Test",
			want: uuid.Nil,
		},
	}
	for _, tt := range tests {
		t.Run("", func(t *testing.T) {
			t.Parallel()

			assert.Equal(t, uuidFromPath(tt.path), tt.want)
		})
	}
}

func TestJoinPath(t *testing.T) {
	t.Parallel()

	tests := []struct {
		elem []string
		want string
	}{
		{
			elem: []string{"a", "b", "c", "", ""},
			want: "a/b/c/",
		},
		{
			elem: []string{"a", "b", "c", ""},
			want: "a/b/c/",
		},
		{
			elem: []string{"a", "b", "c"},
			want: "a/b/c",
		},
		{
			elem: nil,
			want: "",
		},
	}
	for _, tt := range tests {
		t.Run("", func(t *testing.T) {
			t.Parallel()

			assert.Equal(t, joinPath(tt.elem...), tt.want)
		})
	}
}
