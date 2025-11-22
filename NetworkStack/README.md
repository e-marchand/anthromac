# NetworkStack - Modern Async Networking

A C++20 coroutine-based networking library providing high-level abstractions over low-level socket operations, with support for async TCP/UDP communication.

## Core Components
- Async TCP server/client with coroutines
- UDP socket support with async operations
- HTTP/1.1 request/response handling
- Zero-copy buffer management
- Automatic reconnection support
- Event-driven architecture

## Example
```cpp
#include "NetworkStack.hpp"
using namespace net;

// Async TCP Server
Task<void> run_server() {
    TcpServer server;
    co_await server.listen(8080);

    while (auto client = co_await server.accept()) {
        co_await client.send("Hello, World!\n");
        co_await client.close();
    }
}

// Async TCP Client
Task<void> run_client() {
    TcpClient client;
    co_await client.connect("localhost", 8080);

    auto data = co_await client.receive(1024);
    std::cout << "Received: " << data << std::endl;

    co_await client.close();
}
```

## Usage

### TCP Server
```cpp
#include "NetworkStack.hpp"
using namespace net;

Task<void> echo_server() {
    TcpServer server;
    co_await server.listen(9000);

    std::cout << "Server listening on port 9000" << std::endl;

    while (true) {
        auto client = co_await server.accept();
        std::cout << "Client connected" << std::endl;

        // Echo back what we receive
        while (true) {
            auto data = co_await client.receive(4096);
            if (data.empty()) break;  // Connection closed

            co_await client.send(data);
        }

        co_await client.close();
    }
}
```

### TCP Client
```cpp
Task<void> http_client() {
    TcpClient client;
    co_await client.connect("example.com", 80);

    std::string request =
        "GET / HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Connection: close\r\n\r\n";

    co_await client.send(request);

    std::string response;
    while (true) {
        auto data = co_await client.receive(4096);
        if (data.empty()) break;
        response += data;
    }

    std::cout << response << std::endl;
    co_await client.close();
}
```

### UDP Socket
```cpp
Task<void> udp_server() {
    UdpSocket socket;
    co_await socket.bind(5000);

    while (true) {
        auto [data, endpoint] = co_await socket.receive_from(1024);
        std::cout << "Received from " << endpoint.address()
                  << ":" << endpoint.port() << std::endl;

        co_await socket.send_to(data, endpoint);
    }
}

Task<void> udp_client() {
    UdpSocket socket;
    Endpoint server("localhost", 5000);

    co_await socket.send_to("Hello, UDP!", server);

    auto [response, from] = co_await socket.receive_from(1024);
    std::cout << "Response: " << response << std::endl;
}
```

### HTTP Server
```cpp
Task<void> simple_http_server() {
    HttpServer server;

    server.route("GET", "/", [](const HttpRequest& req) -> HttpResponse {
        return HttpResponse{
            .status = 200,
            .headers = {{"Content-Type", "text/html"}},
            .body = "<h1>Hello, World!</h1>"
        };
    });

    server.route("GET", "/api/data", [](const HttpRequest& req) -> HttpResponse {
        return HttpResponse{
            .status = 200,
            .headers = {{"Content-Type", "application/json"}},
            .body = R"({"message":"Hello from API"})"
        };
    });

    co_await server.listen(8080);
    std::cout << "HTTP Server running on http://localhost:8080" << std::endl;

    co_await server.run();
}
```

### Concurrent Connections
```cpp
Task<void> handle_client(TcpConnection client, int id) {
    std::cout << "Handling client " << id << std::endl;

    while (true) {
        auto data = co_await client.receive(1024);
        if (data.empty()) break;

        std::string response = "Echo: " + data;
        co_await client.send(response);
    }

    co_await client.close();
    std::cout << "Client " << id << " disconnected" << std::endl;
}

Task<void> concurrent_server() {
    TcpServer server;
    co_await server.listen(8080);

    int client_id = 0;
    while (true) {
        auto client = co_await server.accept();
        // Handle each client concurrently
        handle_client(std::move(client), client_id++).detach();
    }
}
```

## API Reference

### TcpServer
- `Task<void> listen(uint16_t port, const std::string& address = "0.0.0.0")` - Start listening
- `Task<TcpConnection> accept()` - Accept incoming connection
- `void close()` - Close server socket

### TcpClient / TcpConnection
- `Task<void> connect(const std::string& host, uint16_t port)` - Connect to server
- `Task<std::string> receive(size_t max_bytes)` - Receive data
- `Task<void> send(const std::string& data)` - Send data
- `Task<void> close()` - Close connection
- `bool is_connected() const` - Check connection status

### UdpSocket
- `Task<void> bind(uint16_t port, const std::string& address = "0.0.0.0")` - Bind to port
- `Task<std::pair<std::string, Endpoint>> receive_from(size_t max_bytes)` - Receive with source
- `Task<void> send_to(const std::string& data, const Endpoint& endpoint)` - Send to destination
- `void close()` - Close socket

### HttpServer
- `void route(const std::string& method, const std::string& path, Handler handler)` - Register route
- `Task<void> listen(uint16_t port)` - Start HTTP server
- `Task<void> run()` - Run server event loop

### HttpRequest
- `std::string method` - HTTP method (GET, POST, etc.)
- `std::string path` - Request path
- `std::unordered_map<std::string, std::string> headers` - Request headers
- `std::string body` - Request body

### HttpResponse
- `int status` - HTTP status code
- `std::unordered_map<std::string, std::string> headers` - Response headers
- `std::string body` - Response body

### Task<T>
- `co_await task` - Await task completion
- `void detach()` - Run task without waiting
- `T get()` - Get result (blocking)

## Building

### With CMake
```bash
cd NetworkStack
mkdir build && cd build
cmake ..
cmake --build .
./networkstack_example
```

## Features

### Async/Await with Coroutines
Uses C++20 coroutines for clean async code:
```cpp
co_await client.connect("localhost", 8080);
auto data = co_await client.receive(1024);
co_await client.send("response");
```

### Zero-Copy Buffers
Efficient buffer management with minimal copying:
- String views for received data
- Move semantics for large buffers
- Pooled buffers for frequent allocations

### Automatic Reconnection
Clients can automatically reconnect on connection loss:
```cpp
TcpClient client;
client.set_auto_reconnect(true, std::chrono::seconds(5));
```

### Event-Driven
Built on an event loop for efficient I/O multiplexing:
- Async I/O operations
- Non-blocking sockets
- Efficient polling with select/poll/epoll

## Use Cases

The NetworkStack is ideal for:
- **Microservices** - REST APIs, RPC servers
- **Chat servers** - Real-time messaging
- **Game servers** - Multiplayer networking
- **IoT devices** - Sensor data collection
- **Proxies** - HTTP/TCP proxies
- **Load balancers** - Traffic distribution

## Requirements
- C++20 compatible compiler with coroutine support
- POSIX sockets (Linux/macOS) or Winsock (Windows)
- CMake 3.15 or higher

## Thread Safety
- **TcpServer/TcpClient**: Not thread-safe (use one per thread)
- **Event loop**: Thread-safe for registration
- **Buffers**: Thread-safe with proper synchronization

## Platform Support
- **Linux**: Full support with epoll
- **macOS**: Full support with kqueue
- **Windows**: Full support with IOCP (via compatibility layer)

## Performance
- Handles 10,000+ concurrent connections
- Low latency async I/O
- Minimal memory overhead per connection
- Efficient buffer pooling

## Limitations
- Maximum pending connections: 128 (configurable)
- Maximum receive buffer size: 1MB (configurable)
- Coroutines require C++20 support
- Platform-specific features may vary
