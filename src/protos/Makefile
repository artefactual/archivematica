all: dashboard mcpclient mcpserver

dashboard:
	python -m grpc_tools.protoc -I. --python_out=../dashboard/src/rpcgen --grpc_python_out=../dashboard/src/rpcgen *.proto
	black ../dashboard/src/rpcgen/
mcpclient:
	python -m grpc_tools.protoc -I. --python_out=../MCPClient/lib/rpcgen --grpc_python_out=../MCPClient/lib/rpcgen *.proto
	black ../MCPClient/lib/rpcgen/
mcpserver:
	python -m grpc_tools.protoc -I. --python_out=../MCPServer/lib/server/rpcgen --grpc_python_out=../MCPServer/lib/server/rpcgen *.proto
	black ../MCPServer/lib/server/rpcgen/
