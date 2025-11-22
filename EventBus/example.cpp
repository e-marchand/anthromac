#include "EventBus.hpp"
#include <iostream>
#include <string>
#include <chrono>
#include <thread>

using namespace events;

// Define custom event types
struct MouseEvent {
    int x, y;
    int button; // 1 = left, 2 = right, 3 = middle
};

struct KeyEvent {
    int key;
    bool pressed;
    std::string key_name;
};

struct PlayerEvent {
    std::string player_name;
    int score;
    enum class Type { Join, Leave, ScoreChange } type;
};

struct NetworkEvent {
    std::string message;
    int packet_id;
};

// Example 1: Basic event publishing and subscribing
void example_basic() {
    std::cout << "\n=== Example 1: Basic Usage ===" << std::endl;

    EventBus bus;

    // Subscribe to mouse events
    auto handle = bus.subscribe<MouseEvent>([](const MouseEvent& e) {
        std::cout << "Mouse clicked at (" << e.x << ", " << e.y
                  << "), button: " << e.button << std::endl;
    });

    // Publish some mouse events
    bus.publish(MouseEvent{100, 200, 1});
    bus.publish(MouseEvent{150, 250, 2});

    std::cout << "Subscriber count: " << bus.subscriber_count<MouseEvent>() << std::endl;

    // Unsubscribe
    bus.unsubscribe<MouseEvent>(handle);
    std::cout << "After unsubscribe, count: " << bus.subscriber_count<MouseEvent>() << std::endl;

    // This event won't be received
    bus.publish(MouseEvent{300, 400, 1});
}

// Example 2: Multiple subscribers
void example_multiple_subscribers() {
    std::cout << "\n=== Example 2: Multiple Subscribers ===" << std::endl;

    EventBus bus;

    // Multiple subscribers for the same event
    bus.subscribe<KeyEvent>([](const KeyEvent& e) {
        std::cout << "Handler 1: Key " << e.key_name
                  << (e.pressed ? " pressed" : " released") << std::endl;
    });

    bus.subscribe<KeyEvent>([](const KeyEvent& e) {
        std::cout << "Handler 2: Logging key event: " << e.key << std::endl;
    });

    bus.subscribe<KeyEvent>([](const KeyEvent& e) {
        std::cout << "Handler 3: Processing key input..." << std::endl;
    });

    // Publish a key event
    bus.publish(KeyEvent{65, true, "A"});

    std::cout << "Total subscribers: " << bus.subscriber_count<KeyEvent>() << std::endl;
}

// Example 3: Priority-based event handling
void example_priority() {
    std::cout << "\n=== Example 3: Priority-Based Handling ===" << std::endl;

    EventBus bus;

    // Subscribe with different priorities
    bus.subscribe<KeyEvent>([](const KeyEvent& e) {
        std::cout << "  [Normal Priority] Processing key: " << e.key_name << std::endl;
    }, EventPriority::Normal);

    bus.subscribe<KeyEvent>([](const KeyEvent& e) {
        std::cout << "  [High Priority] Intercepting key: " << e.key_name << std::endl;
    }, EventPriority::High);

    bus.subscribe<KeyEvent>([](const KeyEvent& e) {
        std::cout << "  [Low Priority] Logging key: " << e.key_name << std::endl;
    }, EventPriority::Low);

    // High priority handlers are called first
    std::cout << "\nPublishing key event (handlers called in priority order):" << std::endl;
    bus.publish(KeyEvent{27, true, "Escape"});
}

// Example 4: Scoped subscriptions (RAII)
void example_scoped() {
    std::cout << "\n=== Example 4: Scoped Subscriptions ===" << std::endl;

    EventBus bus;

    std::cout << "Subscribers before scope: " << bus.subscriber_count<MouseEvent>() << std::endl;

    {
        // Scoped subscription - automatically unsubscribes when going out of scope
        auto scoped1 = bus.subscribe_scoped<MouseEvent>([](const MouseEvent& e) {
            std::cout << "Scoped handler 1: (" << e.x << ", " << e.y << ")" << std::endl;
        });

        auto scoped2 = bus.subscribe_scoped<MouseEvent>([](const MouseEvent& e) {
            std::cout << "Scoped handler 2: Button " << e.button << std::endl;
        });

        std::cout << "Subscribers inside scope: " << bus.subscriber_count<MouseEvent>() << std::endl;

        bus.publish(MouseEvent{50, 75, 1});

        // scoped1 and scoped2 automatically unsubscribe here
    }

    std::cout << "Subscribers after scope: " << bus.subscriber_count<MouseEvent>() << std::endl;

    // This event won't be received
    bus.publish(MouseEvent{100, 100, 1});
}

// Example 5: Event filtering
void example_filtering() {
    std::cout << "\n=== Example 5: Event Filtering ===" << std::endl;

    EventBus bus;

    // Only handle left mouse button clicks (button == 1)
    bus.subscribe<MouseEvent>([](const MouseEvent& e) {
        std::cout << "Left button clicked at (" << e.x << ", " << e.y << ")" << std::endl;
    }, EventPriority::Normal, [](const MouseEvent& e) {
        return e.button == 1;
    });

    // Only handle right mouse button clicks (button == 2)
    bus.subscribe<MouseEvent>([](const MouseEvent& e) {
        std::cout << "Right button clicked at (" << e.x << ", " << e.y << ")" << std::endl;
    }, EventPriority::Normal, [](const MouseEvent& e) {
        return e.button == 2;
    });

    // Publish various mouse events
    std::cout << "\nPublishing left click:" << std::endl;
    bus.publish(MouseEvent{100, 100, 1});

    std::cout << "\nPublishing right click:" << std::endl;
    bus.publish(MouseEvent{200, 200, 2});

    std::cout << "\nPublishing middle click (no handlers):" << std::endl;
    bus.publish(MouseEvent{300, 300, 3});
}

// Example 6: Different event types
void example_multiple_event_types() {
    std::cout << "\n=== Example 6: Multiple Event Types ===" << std::endl;

    EventBus bus;

    // Subscribe to player events
    bus.subscribe<PlayerEvent>([](const PlayerEvent& e) {
        switch (e.type) {
            case PlayerEvent::Type::Join:
                std::cout << "Player " << e.player_name << " joined the game" << std::endl;
                break;
            case PlayerEvent::Type::Leave:
                std::cout << "Player " << e.player_name << " left the game" << std::endl;
                break;
            case PlayerEvent::Type::ScoreChange:
                std::cout << "Player " << e.player_name << " score: " << e.score << std::endl;
                break;
        }
    });

    // Subscribe to network events
    bus.subscribe<NetworkEvent>([](const NetworkEvent& e) {
        std::cout << "Network packet #" << e.packet_id << ": " << e.message << std::endl;
    });

    // Publish different event types
    bus.publish(PlayerEvent{"Alice", 0, PlayerEvent::Type::Join});
    bus.publish(PlayerEvent{"Bob", 0, PlayerEvent::Type::Join});
    bus.publish(NetworkEvent{"Connection established", 1});
    bus.publish(PlayerEvent{"Alice", 100, PlayerEvent::Type::ScoreChange});
    bus.publish(NetworkEvent{"Game data received", 2});
    bus.publish(PlayerEvent{"Bob", 75, PlayerEvent::Type::ScoreChange});
    bus.publish(PlayerEvent{"Alice", 100, PlayerEvent::Type::Leave});

    std::cout << "\nPlayer event subscribers: " << bus.subscriber_count<PlayerEvent>() << std::endl;
    std::cout << "Network event subscribers: " << bus.subscriber_count<NetworkEvent>() << std::endl;
}

// Example 7: Async event publishing
void example_async() {
    std::cout << "\n=== Example 7: Async Event Publishing ===" << std::endl;

    EventBus bus;

    bus.subscribe<NetworkEvent>([](const NetworkEvent& e) {
        std::cout << "Processing packet #" << e.packet_id << ": " << e.message << std::endl;
        // Simulate some processing time
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    });

    std::cout << "Publishing events asynchronously..." << std::endl;

    // Publish events asynchronously
    auto future1 = bus.publish_async(NetworkEvent{"Async message 1", 1});
    auto future2 = bus.publish_async(NetworkEvent{"Async message 2", 2});
    auto future3 = bus.publish_async(NetworkEvent{"Async message 3", 3});

    std::cout << "Main thread continues immediately..." << std::endl;

    // Wait for all async publishes to complete
    future1.wait();
    future2.wait();
    future3.wait();

    std::cout << "All async events processed" << std::endl;
}

// Example 8: Game-like scenario
void example_game_scenario() {
    std::cout << "\n=== Example 8: Game Scenario ===" << std::endl;

    EventBus bus;

    // Input system subscribes to key events
    bus.subscribe<KeyEvent>([](const KeyEvent& e) {
        if (e.pressed) {
            std::cout << "[Input System] Key pressed: " << e.key_name << std::endl;
        }
    }, EventPriority::High); // High priority for input

    // UI system subscribes to key events
    bus.subscribe<KeyEvent>([](const KeyEvent& e) {
        if (e.pressed && e.key_name == "Escape") {
            std::cout << "[UI System] Opening pause menu" << std::endl;
        }
    }, EventPriority::Normal);

    // Game logic subscribes to player events
    bus.subscribe<PlayerEvent>([](const PlayerEvent& e) {
        if (e.type == PlayerEvent::Type::ScoreChange) {
            std::cout << "[Game Logic] Updating leaderboard for "
                      << e.player_name << std::endl;
        }
    });

    // Audio system subscribes to player events
    bus.subscribe<PlayerEvent>([](const PlayerEvent& e) {
        if (e.type == PlayerEvent::Type::ScoreChange) {
            std::cout << "[Audio System] Playing score sound effect" << std::endl;
        }
    });

    // Simulate game events
    std::cout << "\nSimulating game session:" << std::endl;
    bus.publish(KeyEvent{87, true, "W"}); // W key
    bus.publish(PlayerEvent{"Player1", 50, PlayerEvent::Type::ScoreChange});
    bus.publish(KeyEvent{27, true, "Escape"}); // Escape key
    bus.publish(PlayerEvent{"Player1", 100, PlayerEvent::Type::ScoreChange});
}

int main() {
    std::cout << "=== EventBus Example Demo ===" << std::endl;

    example_basic();
    example_multiple_subscribers();
    example_priority();
    example_scoped();
    example_filtering();
    example_multiple_event_types();
    example_async();
    example_game_scenario();

    std::cout << "\n=== All examples completed ===" << std::endl;
    return 0;
}
