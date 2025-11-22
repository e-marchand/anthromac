#pragma once

#include <coroutine>
#include <string>
#include <string_view>
#include <memory>
#include <functional>
#include <unordered_map>
#include <optional>
#include <vector>
#include <stdexcept>
#include <cstring>

// Platform-specific includes
#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    using socket_t = SOCKET;
    #define INVALID_SOCKET_VALUE INVALID_SOCKET
    #define close_socket closesocket
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #include <fcntl.h>
    #include <netdb.h>
    using socket_t = int;
    #define INVALID_SOCKET_VALUE -1
    #define close_socket close
#endif

namespace net {

// Forward declarations
template<typename T>
class Task;

// Exception types
class NetworkError : public std::runtime_error {
public:
    explicit NetworkError(const std::string& msg) : std::runtime_error(msg) {}
};

// Endpoint representation
class Endpoint {
public:
    Endpoint() = default;
    Endpoint(const std::string& addr, uint16_t p) : address_(addr), port_(p) {}

    std::string address() const { return address_; }
    uint16_t port() const { return port_; }

    sockaddr_in to_sockaddr() const {
        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port_);
        inet_pton(AF_INET, address_.c_str(), &addr.sin_addr);
        return addr;
    }

    static Endpoint from_sockaddr(const sockaddr_in& addr) {
        char ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &addr.sin_addr, ip, INET_ADDRSTRLEN);
        return Endpoint(ip, ntohs(addr.sin_port));
    }

private:
    std::string address_;
    uint16_t port_ = 0;
};

// Task promise type for coroutines
template<typename T = void>
class Task {
public:
    struct promise_type {
        T value;
        std::exception_ptr exception;

        Task get_return_object() {
            return Task{std::coroutine_handle<promise_type>::from_promise(*this)};
        }

        std::suspend_never initial_suspend() { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }

        void unhandled_exception() {
            exception = std::current_exception();
        }

        template<typename U>
        void return_value(U&& val) {
            value = std::forward<U>(val);
        }
    };

    using handle_type = std::coroutine_handle<promise_type>;

    Task(handle_type h) : handle_(h) {}
    ~Task() {
        if (handle_) handle_.destroy();
    }

    Task(const Task&) = delete;
    Task& operator=(const Task&) = delete;

    Task(Task&& other) noexcept : handle_(other.handle_) {
        other.handle_ = nullptr;
    }

    Task& operator=(Task&& other) noexcept {
        if (this != &other) {
            if (handle_) handle_.destroy();
            handle_ = other.handle_;
            other.handle_ = nullptr;
        }
        return *this;
    }

    bool await_ready() { return handle_.done(); }
    void await_suspend(std::coroutine_handle<> awaiting) {}
    T await_resume() {
        if (handle_.promise().exception) {
            std::rethrow_exception(handle_.promise().exception);
        }
        return std::move(handle_.promise().value);
    }

    T get() {
        while (!handle_.done()) {
            handle_.resume();
        }
        return await_resume();
    }

    void detach() {
        // Fire and forget
        handle_ = nullptr;
    }

private:
    handle_type handle_;
};

// Specialization for void
template<>
class Task<void> {
public:
    struct promise_type {
        std::exception_ptr exception;

        Task get_return_object() {
            return Task{std::coroutine_handle<promise_type>::from_promise(*this)};
        }

        std::suspend_never initial_suspend() { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }

        void unhandled_exception() {
            exception = std::current_exception();
        }

        void return_void() {}
    };

    using handle_type = std::coroutine_handle<promise_type>;

    Task(handle_type h) : handle_(h) {}
    ~Task() {
        if (handle_) handle_.destroy();
    }

    Task(const Task&) = delete;
    Task& operator=(const Task&) = delete;

    Task(Task&& other) noexcept : handle_(other.handle_) {
        other.handle_ = nullptr;
    }

    Task& operator=(Task&& other) noexcept {
        if (this != &other) {
            if (handle_) handle_.destroy();
            handle_ = other.handle_;
            other.handle_ = nullptr;
        }
        return *this;
    }

    bool await_ready() { return handle_.done(); }
    void await_suspend(std::coroutine_handle<> awaiting) {}
    void await_resume() {
        if (handle_.promise().exception) {
            std::rethrow_exception(handle_.promise().exception);
        }
    }

    void get() {
        while (!handle_.done()) {
            handle_.resume();
        }
        await_resume();
    }

    void detach() {
        handle_ = nullptr;
    }

private:
    handle_type handle_;
};

// TCP Connection class
class TcpConnection {
public:
    TcpConnection() : socket_(INVALID_SOCKET_VALUE) {}

    explicit TcpConnection(socket_t sock) : socket_(sock) {}

    ~TcpConnection() {
        close();
    }

    TcpConnection(const TcpConnection&) = delete;
    TcpConnection& operator=(const TcpConnection&) = delete;

    TcpConnection(TcpConnection&& other) noexcept : socket_(other.socket_) {
        other.socket_ = INVALID_SOCKET_VALUE;
    }

    TcpConnection& operator=(TcpConnection&& other) noexcept {
        if (this != &other) {
            close();
            socket_ = other.socket_;
            other.socket_ = INVALID_SOCKET_VALUE;
        }
        return *this;
    }

    Task<std::string> receive(size_t max_bytes) {
        std::string buffer(max_bytes, '\0');
        ssize_t n = recv(socket_, buffer.data(), max_bytes, 0);

        if (n < 0) {
            throw NetworkError("recv failed");
        }

        buffer.resize(n);
        co_return buffer;
    }

    Task<void> send(const std::string& data) {
        size_t total_sent = 0;
        while (total_sent < data.size()) {
            ssize_t n = ::send(socket_, data.data() + total_sent,
                             data.size() - total_sent, 0);
            if (n < 0) {
                throw NetworkError("send failed");
            }
            total_sent += n;
        }
        co_return;
    }

    Task<void> close() {
        if (socket_ != INVALID_SOCKET_VALUE) {
            close_socket(socket_);
            socket_ = INVALID_SOCKET_VALUE;
        }
        co_return;
    }

    bool is_connected() const {
        return socket_ != INVALID_SOCKET_VALUE;
    }

    socket_t socket() const { return socket_; }

private:
    socket_t socket_;
};

// TCP Server class
class TcpServer {
public:
    TcpServer() : socket_(INVALID_SOCKET_VALUE) {}

    ~TcpServer() {
        close();
    }

    Task<void> listen(uint16_t port, const std::string& address = "0.0.0.0") {
        socket_ = socket(AF_INET, SOCK_STREAM, 0);
        if (socket_ == INVALID_SOCKET_VALUE) {
            throw NetworkError("Failed to create socket");
        }

        // Set SO_REUSEADDR
        int opt = 1;
        setsockopt(socket_, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        inet_pton(AF_INET, address.c_str(), &addr.sin_addr);

        if (bind(socket_, (sockaddr*)&addr, sizeof(addr)) < 0) {
            throw NetworkError("Failed to bind socket");
        }

        if (::listen(socket_, 128) < 0) {
            throw NetworkError("Failed to listen on socket");
        }

        co_return;
    }

    Task<TcpConnection> accept() {
        sockaddr_in client_addr{};
        socklen_t client_len = sizeof(client_addr);

        socket_t client_sock = ::accept(socket_, (sockaddr*)&client_addr, &client_len);
        if (client_sock == INVALID_SOCKET_VALUE) {
            throw NetworkError("Failed to accept connection");
        }

        co_return TcpConnection(client_sock);
    }

    void close() {
        if (socket_ != INVALID_SOCKET_VALUE) {
            close_socket(socket_);
            socket_ = INVALID_SOCKET_VALUE;
        }
    }

private:
    socket_t socket_;
};

// TCP Client class
class TcpClient : public TcpConnection {
public:
    Task<void> connect(const std::string& host, uint16_t port) {
        socket_t sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock == INVALID_SOCKET_VALUE) {
            throw NetworkError("Failed to create socket");
        }

        // Resolve hostname
        addrinfo hints{}, *result = nullptr;
        hints.ai_family = AF_INET;
        hints.ai_socktype = SOCK_STREAM;

        if (getaddrinfo(host.c_str(), std::to_string(port).c_str(), &hints, &result) != 0) {
            close_socket(sock);
            throw NetworkError("Failed to resolve hostname");
        }

        if (::connect(sock, result->ai_addr, result->ai_addrlen) < 0) {
            freeaddrinfo(result);
            close_socket(sock);
            throw NetworkError("Failed to connect");
        }

        freeaddrinfo(result);
        *this = TcpConnection(sock);

        co_return;
    }
};

// UDP Socket class
class UdpSocket {
public:
    UdpSocket() : socket_(INVALID_SOCKET_VALUE) {}

    ~UdpSocket() {
        close();
    }

    Task<void> bind(uint16_t port, const std::string& address = "0.0.0.0") {
        socket_ = socket(AF_INET, SOCK_DGRAM, 0);
        if (socket_ == INVALID_SOCKET_VALUE) {
            throw NetworkError("Failed to create socket");
        }

        sockaddr_in addr{};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        inet_pton(AF_INET, address.c_str(), &addr.sin_addr);

        if (::bind(socket_, (sockaddr*)&addr, sizeof(addr)) < 0) {
            throw NetworkError("Failed to bind socket");
        }

        co_return;
    }

    Task<std::pair<std::string, Endpoint>> receive_from(size_t max_bytes) {
        std::string buffer(max_bytes, '\0');
        sockaddr_in from_addr{};
        socklen_t from_len = sizeof(from_addr);

        ssize_t n = recvfrom(socket_, buffer.data(), max_bytes, 0,
                            (sockaddr*)&from_addr, &from_len);

        if (n < 0) {
            throw NetworkError("recvfrom failed");
        }

        buffer.resize(n);
        Endpoint endpoint = Endpoint::from_sockaddr(from_addr);

        co_return std::make_pair(std::move(buffer), endpoint);
    }

    Task<void> send_to(const std::string& data, const Endpoint& endpoint) {
        sockaddr_in addr = endpoint.to_sockaddr();

        ssize_t n = sendto(socket_, data.data(), data.size(), 0,
                          (sockaddr*)&addr, sizeof(addr));

        if (n < 0) {
            throw NetworkError("sendto failed");
        }

        co_return;
    }

    void close() {
        if (socket_ != INVALID_SOCKET_VALUE) {
            close_socket(socket_);
            socket_ = INVALID_SOCKET_VALUE;
        }
    }

private:
    socket_t socket_;
};

// HTTP Request/Response
struct HttpRequest {
    std::string method;
    std::string path;
    std::unordered_map<std::string, std::string> headers;
    std::string body;

    static HttpRequest parse(const std::string& raw) {
        HttpRequest req;
        size_t pos = 0;

        // Parse request line
        size_t end = raw.find("\r\n", pos);
        if (end == std::string::npos) {
            throw NetworkError("Invalid HTTP request");
        }

        std::string request_line = raw.substr(pos, end - pos);
        pos = end + 2;

        // Parse method and path
        size_t space1 = request_line.find(' ');
        size_t space2 = request_line.find(' ', space1 + 1);

        req.method = request_line.substr(0, space1);
        req.path = request_line.substr(space1 + 1, space2 - space1 - 1);

        // Parse headers
        while (true) {
            end = raw.find("\r\n", pos);
            if (end == std::string::npos) break;

            std::string line = raw.substr(pos, end - pos);
            pos = end + 2;

            if (line.empty()) break; // End of headers

            size_t colon = line.find(':');
            if (colon != std::string::npos) {
                std::string key = line.substr(0, colon);
                std::string value = line.substr(colon + 2); // Skip ": "
                req.headers[key] = value;
            }
        }

        // Body is the rest
        if (pos < raw.size()) {
            req.body = raw.substr(pos);
        }

        return req;
    }
};

struct HttpResponse {
    int status = 200;
    std::unordered_map<std::string, std::string> headers;
    std::string body;

    std::string to_string() const {
        std::string status_text = "OK";
        if (status == 404) status_text = "Not Found";
        else if (status == 500) status_text = "Internal Server Error";

        std::ostringstream oss;
        oss << "HTTP/1.1 " << status << " " << status_text << "\r\n";

        for (const auto& [key, value] : headers) {
            oss << key << ": " << value << "\r\n";
        }

        oss << "Content-Length: " << body.size() << "\r\n";
        oss << "\r\n";
        oss << body;

        return oss.str();
    }
};

// HTTP Server
class HttpServer {
public:
    using Handler = std::function<HttpResponse(const HttpRequest&)>;

    void route(const std::string& method, const std::string& path, Handler handler) {
        routes_[method + " " + path] = std::move(handler);
    }

    Task<void> listen(uint16_t port) {
        co_await server_.listen(port);
    }

    Task<void> run() {
        while (true) {
            auto client = co_await server_.accept();
            handle_client(std::move(client)).detach();
        }
    }

private:
    Task<void> handle_client(TcpConnection client) {
        try {
            auto request_data = co_await client.receive(8192);
            if (request_data.empty()) {
                co_return;
            }

            HttpRequest request = HttpRequest::parse(request_data);

            std::string route_key = request.method + " " + request.path;
            HttpResponse response;

            auto it = routes_.find(route_key);
            if (it != routes_.end()) {
                response = it->second(request);
            } else {
                response.status = 404;
                response.body = "Not Found";
            }

            co_await client.send(response.to_string());

        } catch (const std::exception& e) {
            // Ignore client errors
        }

        co_await client.close();
    }

    TcpServer server_;
    std::unordered_map<std::string, Handler> routes_;
};

} // namespace net
