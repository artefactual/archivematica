package python

import (
	"errors"
	"fmt"

	"go.starlark.net/starlark"
	"go.starlark.net/syntax"
)

func eval(literal string) (starlark.Value, error) {
	thread := &starlark.Thread{Name: "main"}

	fileOptions := syntax.FileOptions{
		Set:               false,
		While:             false,
		TopLevelControl:   false,
		GlobalReassign:    false,
		LoadBindsGlobally: false,
		Recursion:         false,
	}

	expr, err := fileOptions.ParseExpr("", literal, syntax.RetainComments)
	if err != nil {
		return nil, fmt.Errorf("parse expression: %v", err)
	}

	val, err := starlark.EvalExpr(thread, expr, nil)
	if err != nil {
		return nil, fmt.Errorf("eval expression: %v", err)
	}

	return val, nil
}

func EvalMap(literal string) (map[string]string, error) {
	val, err := eval(literal)
	if err != nil {
		return nil, err
	}

	dict, ok := val.(*starlark.Dict)
	if !ok {
		return nil, errors.New("literal is not a dict")
	}

	result := map[string]string{}
	for _, item := range dict.Items() {
		key, keyOk := starlark.AsString(item[0])
		value, valOk := starlark.AsString(item[1])
		if keyOk && valOk {
			result[key] = value
		}
	}

	return result, nil
}
