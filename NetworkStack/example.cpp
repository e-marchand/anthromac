#include "NetworkStack.hpp"
#include <iostream>
#include <thread>
#include <chrono>
#include <sstream>

using namespace net;

// Example 1: Simple Echo Server
Task<void> echo_server_example() {
    std::cout << "\n=== Example 1: Echo Server ===" << std::endl;
    std::cout << "Starting echo server on port 9000..." << std::endl;

    TcpServer server;
    co_await server.listen(9000);

    std::cout << "Server listening. Waiting for connection..." << std::endl;

    // Accept one connection and echo back
    auto client = co_await server.accept();
    std::cout << "Client connected!" << std::endl;

    auto data = co_await client.receive(1024);
    std::cout << "Received: " << data << std::endl;

    co_await client.send("Echo: " + data);
    std::cout << "Sent echo response" << std::endl;

    co_await client.close();
    server.close();
}

// Example 2: TCP Client
Task<void> tcp_client_example() {
    std::cout << "\n=== Example 2: TCP Client ===" << std::endl;

    TcpClient client;

    try {
        std::cout << "Connecting to server..." << std::endl;
        co_await client.connect("localhost", 9000);
        std::cout << "Connected!" << std::endl;

        std::string message = "Hello from client!";
        std::cout << "Sending: " << message << std::endl;
        co_await client.send(message);

        auto response = co_await client.receive(1024);
        std::cout << "Received: " << response << std::endl;

        co_await client.close();

    } catch (const NetworkError& e) {
        std::cerr << "Client error: " << e.what() << std::endl;
    }
}

// Example 3: Run Echo Server and Client Together
void example_echo_communication() {
    std::cout << "\n=== Example 3: Echo Communication ===" << std::endl;

    // Start server in a thread
    std::thread server_thread([]() {
        echo_server_example().get();
    });

    // Give server time to start
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    // Run client
    tcp_client_example().get();

    server_thread.join();
}

// Example 4: HTTP Server
Task<void> http_server_example() {
    std::cout << "\n=== Example 4: HTTP Server ===" << std::endl;

    HttpServer server;

    // Route 1: Home page
    server.route("GET", "/", [](const HttpRequest& req) -> HttpResponse {
        return HttpResponse{
            .status = 200,
            .headers = {{"Content-Type", "text/html"}},
            .body = "<html><body><h1>Hello, World!</h1><p>Welcome to NetworkStack HTTP Server</p></body></html>"
        };
    });

    // Route 2: API endpoint
    server.route("GET", "/api/status", [](const HttpRequest& req) -> HttpResponse {
        return HttpResponse{
            .status = 200,
            .headers = {{"Content-Type", "application/json"}},
            .body = R"({"status":"ok","message":"Server is running"})"
        };
    });

    // Route 3: Echo endpoint
    server.route("POST", "/api/echo", [](const HttpRequest& req) -> HttpResponse {
        return HttpResponse{
            .status = 200,
            .headers = {{"Content-Type", "text/plain"}},
            .body = "You sent: " + req.body
        };
    });

    std::cout << "HTTP Server starting on port 8080..." << std::endl;
    std::cout << "Visit http://localhost:8080/ in your browser" << std::endl;
    std::cout << "Press Ctrl+C to stop" << std::endl;

    co_await server.listen(8080);
    co_await server.run();
}

// Example 5: HTTP Client Request
Task<void> http_client_example() {
    std::cout << "\n=== Example 5: HTTP Client ===" << std::endl;

    TcpClient client;

    try {
        co_await client.connect("localhost", 8080);

        std::string request =
            "GET /api/status HTTP/1.1\r\n"
            "Host: localhost\r\n"
            "Connection: close\r\n\r\n";

        std::cout << "Sending HTTP request..." << std::endl;
        co_await client.send(request);

        std::string response;
        while (true) {
            auto chunk = co_await client.receive(1024);
            if (chunk.empty()) break;
            response += chunk;
        }

        std::cout << "HTTP Response:" << std::endl;
        std::cout << response << std::endl;

        co_await client.close();

    } catch (const NetworkError& e) {
        std::cerr << "HTTP client error: " << e.what() << std::endl;
    }
}

// Example 6: Test HTTP Server
void example_http_test() {
    std::cout << "\n=== Example 6: HTTP Server Test ===" << std::endl;

    // Start server in a thread
    std::thread server_thread([]() {
        http_server_example().get();
    });

    // Give server time to start
    std::this_thread::sleep_for(std::chrono::milliseconds(200));

    // Make a request
    http_client_example().get();

    std::cout << "\nServer still running. Press Ctrl+C to stop." << std::endl;

    // Keep server running
    server_thread.join();
}

// Example 7: UDP Echo Server
Task<void> udp_echo_server() {
    std::cout << "\n=== Example 7: UDP Echo Server ===" << std::endl;

    UdpSocket socket;
    co_await socket.bind(5000);

    std::cout << "UDP server listening on port 5000..." << std::endl;

    // Echo one message
    auto [data, endpoint] = co_await socket.receive_from(1024);
    std::cout << "Received from " << endpoint.address() << ":" << endpoint.port()
              << " - " << data << std::endl;

    std::string response = "Echo: " + data;
    co_await socket.send_to(response, endpoint);
    std::cout << "Sent echo response" << std::endl;

    socket.close();
}

// Example 8: UDP Client
Task<void> udp_client_example() {
    std::cout << "\n=== Example 8: UDP Client ===" << std::endl;

    UdpSocket socket;
    Endpoint server("127.0.0.1", 5000);

    std::string message = "Hello, UDP!";
    std::cout << "Sending: " << message << std::endl;
    co_await socket.send_to(message, server);

    auto [response, from] = co_await socket.receive_from(1024);
    std::cout << "Received from " << from.address() << ":" << from.port()
              << " - " << response << std::endl;

    socket.close();
}

// Example 9: UDP Communication
void example_udp_communication() {
    std::cout << "\n=== Example 9: UDP Communication ===" << std::endl;

    // Start server in a thread
    std::thread server_thread([]() {
        udp_echo_server().get();
    });

    // Give server time to start
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    // Run client
    udp_client_example().get();

    server_thread.join();
}

// Example 10: Multiple Clients (Concurrent)
Task<void> concurrent_echo_server() {
    std::cout << "\n=== Example 10: Concurrent Echo Server ===" << std::endl;

    TcpServer server;
    co_await server.listen(9001);

    std::cout << "Concurrent server listening on port 9001..." << std::endl;

    // Handle 3 clients
    for (int i = 0; i < 3; ++i) {
        auto client = co_await server.accept();
        std::cout << "Client " << i << " connected" << std::endl;

        auto data = co_await client.receive(1024);
        std::cout << "Client " << i << " sent: " << data << std::endl;

        co_await client.send("Response to client " + std::to_string(i));
        co_await client.close();
    }

    server.close();
}

Task<void> concurrent_client(int id) {
    TcpClient client;

    try {
        co_await client.connect("localhost", 9001);

        std::string message = "Hello from client " + std::to_string(id);
        co_await client.send(message);

        auto response = co_await client.receive(1024);
        std::cout << "Client " << id << " received: " << response << std::endl;

        co_await client.close();

    } catch (const NetworkError& e) {
        std::cerr << "Client " << id << " error: " << e.what() << std::endl;
    }
}

void example_concurrent_clients() {
    std::cout << "\n=== Example: Multiple Concurrent Clients ===" << std::endl;

    // Start server
    std::thread server_thread([]() {
        concurrent_echo_server().get();
    });

    // Give server time to start
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    // Start multiple clients
    std::vector<std::thread> client_threads;
    for (int i = 0; i < 3; ++i) {
        client_threads.emplace_back([i]() {
            std::this_thread::sleep_for(std::chrono::milliseconds(i * 50));
            concurrent_client(i).get();
        });
    }

    for (auto& t : client_threads) {
        t.join();
    }

    server_thread.join();
}

// Example 11: Simple demonstration without threads
Task<void> simple_demo() {
    std::cout << "\n=== Example 11: Simple Coroutine Demo ===" << std::endl;

    TcpServer server;
    co_await server.listen(9002);
    std::cout << "Server ready on port 9002" << std::endl;

    std::cout << "\nDemonstration complete! (Not accepting connections in demo mode)" << std::endl;
    server.close();
}

void show_menu() {
    std::cout << "\n" << std::string(50, '=') << std::endl;
    std::cout << "NetworkStack Examples Menu" << std::endl;
    std::cout << std::string(50, '=') << std::endl;
    std::cout << "1. Simple Echo Communication (TCP)" << std::endl;
    std::cout << "2. HTTP Server Test" << std::endl;
    std::cout << "3. UDP Communication" << std::endl;
    std::cout << "4. Concurrent Clients" << std::endl;
    std::cout << "5. Simple Coroutine Demo" << std::endl;
    std::cout << "0. Exit" << std::endl;
    std::cout << std::string(50, '=') << std::endl;
    std::cout << "Select example: ";
}

int main(int argc, char* argv[]) {
    std::cout << "=== NetworkStack Example Demo ===" << std::endl;

#ifdef _WIN32
    // Initialize Winsock on Windows
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed" << std::endl;
        return 1;
    }
#endif

    if (argc > 1) {
        std::string arg = argv[1];
        if (arg == "--http") {
            std::cout << "Starting HTTP server..." << std::endl;
            http_server_example().get();
        } else if (arg == "--demo") {
            simple_demo().get();
        } else {
            std::cout << "Usage: " << argv[0] << " [--http|--demo]" << std::endl;
        }
    } else {
        // Interactive menu
        while (true) {
            show_menu();

            int choice;
            std::cin >> choice;

            if (choice == 0) break;

            try {
                switch (choice) {
                    case 1:
                        example_echo_communication();
                        break;
                    case 2:
                        example_http_test();
                        break;
                    case 3:
                        example_udp_communication();
                        break;
                    case 4:
                        example_concurrent_clients();
                        break;
                    case 5:
                        simple_demo().get();
                        break;
                    default:
                        std::cout << "Invalid choice!" << std::endl;
                }
            } catch (const std::exception& e) {
                std::cerr << "Error: " << e.what() << std::endl;
            }

            std::cout << "\nPress Enter to continue...";
            std::cin.ignore();
            std::cin.get();
        }
    }

#ifdef _WIN32
    WSACleanup();
#endif

    std::cout << "\n=== All examples completed ===" << std::endl;
    return 0;
}
