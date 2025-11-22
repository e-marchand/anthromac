#pragma once

#include <functional>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <vector>
#include <typeindex>
#include <algorithm>
#include <future>
#include <queue>

namespace events {

// Event priority levels
enum class EventPriority {
    Low = 0,
    Normal = 1,
    High = 2
};

// Subscription handle for managing subscriptions
using SubscriptionHandle = size_t;

namespace detail {
    // Base class for type-erased event handlers
    class HandlerBase {
    public:
        virtual ~HandlerBase() = default;
        EventPriority priority;
        SubscriptionHandle handle;

        HandlerBase(EventPriority p, SubscriptionHandle h)
            : priority(p), handle(h) {}
    };

    // Templated handler with optional filter
    template<typename Event>
    class Handler : public HandlerBase {
    public:
        using Callback = std::function<void(const Event&)>;
        using Filter = std::function<bool(const Event&)>;

        Handler(Callback cb, EventPriority p, SubscriptionHandle h, Filter f = nullptr)
            : HandlerBase(p, h), callback(std::move(cb)), filter(std::move(f)) {}

        void invoke(const Event& event) {
            if (!filter || filter(event)) {
                callback(event);
            }
        }

    private:
        Callback callback;
        Filter filter;
    };
}

// Forward declaration
class EventBus;

// RAII wrapper for automatic unsubscription
template<typename Event>
class ScopedSubscription {
public:
    ScopedSubscription(EventBus* bus, SubscriptionHandle handle)
        : bus_(bus), handle_(handle), active_(true) {}

    ~ScopedSubscription();

    ScopedSubscription(const ScopedSubscription&) = delete;
    ScopedSubscription& operator=(const ScopedSubscription&) = delete;

    ScopedSubscription(ScopedSubscription&& other) noexcept
        : bus_(other.bus_), handle_(other.handle_), active_(other.active_) {
        other.active_ = false;
    }

    ScopedSubscription& operator=(ScopedSubscription&& other) noexcept {
        if (this != &other) {
            if (active_) {
                unsubscribe();
            }
            bus_ = other.bus_;
            handle_ = other.handle_;
            active_ = other.active_;
            other.active_ = false;
        }
        return *this;
    }

    void unsubscribe();

    SubscriptionHandle handle() const { return handle_; }

private:
    EventBus* bus_;
    SubscriptionHandle handle_;
    bool active_;
};

// Main EventBus class
class EventBus {
public:
    EventBus() : next_handle_(0) {}

    ~EventBus() {
        clear();
    }

    EventBus(const EventBus&) = delete;
    EventBus& operator=(const EventBus&) = delete;

    // Subscribe to an event type
    template<typename Event>
    SubscriptionHandle subscribe(
        std::function<void(const Event&)> callback,
        EventPriority priority = EventPriority::Normal
    ) {
        return subscribe_impl<Event>(std::move(callback), priority, nullptr);
    }

    // Subscribe with a filter
    template<typename Event>
    SubscriptionHandle subscribe(
        std::function<void(const Event&)> callback,
        EventPriority priority,
        std::function<bool(const Event&)> filter
    ) {
        return subscribe_impl<Event>(std::move(callback), priority, std::move(filter));
    }

    // Subscribe with RAII automatic unsubscription
    template<typename Event>
    ScopedSubscription<Event> subscribe_scoped(
        std::function<void(const Event&)> callback,
        EventPriority priority = EventPriority::Normal
    ) {
        auto handle = subscribe<Event>(std::move(callback), priority);
        return ScopedSubscription<Event>(this, handle);
    }

    // Publish an event synchronously
    template<typename Event>
    void publish(const Event& event) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto type = std::type_index(typeid(Event));
        auto it = handlers_.find(type);

        if (it == handlers_.end()) {
            return;
        }

        // Sort handlers by priority if needed
        auto& handler_list = it->second;
        if (needs_sort_[type]) {
            std::sort(handler_list.begin(), handler_list.end(),
                [](const auto& a, const auto& b) {
                    return static_cast<int>(a->priority) > static_cast<int>(b->priority);
                });
            needs_sort_[type] = false;
        }

        // Invoke all handlers
        for (const auto& handler_base : handler_list) {
            auto handler = static_cast<detail::Handler<Event>*>(handler_base.get());
            handler->invoke(event);
        }
    }

    // Publish an event asynchronously
    template<typename Event>
    std::future<void> publish_async(const Event& event) {
        return std::async(std::launch::async, [this, event]() {
            publish(event);
        });
    }

    // Unsubscribe a specific handler
    template<typename Event>
    void unsubscribe(SubscriptionHandle handle) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto type = std::type_index(typeid(Event));
        auto it = handlers_.find(type);

        if (it == handlers_.end()) {
            return;
        }

        auto& handler_list = it->second;
        handler_list.erase(
            std::remove_if(handler_list.begin(), handler_list.end(),
                [handle](const auto& h) { return h->handle == handle; }),
            handler_list.end()
        );

        if (handler_list.empty()) {
            handlers_.erase(it);
            needs_sort_.erase(type);
        }
    }

    // Clear all subscriptions
    void clear() {
        std::lock_guard<std::mutex> lock(mutex_);
        handlers_.clear();
        needs_sort_.clear();
    }

    // Get number of subscribers for an event type
    template<typename Event>
    size_t subscriber_count() const {
        std::lock_guard<std::mutex> lock(mutex_);

        auto type = std::type_index(typeid(Event));
        auto it = handlers_.find(type);

        return (it != handlers_.end()) ? it->second.size() : 0;
    }

    // Check if there are any subscribers for an event type
    template<typename Event>
    bool has_subscribers() const {
        return subscriber_count<Event>() > 0;
    }

private:
    template<typename Event>
    SubscriptionHandle subscribe_impl(
        std::function<void(const Event&)> callback,
        EventPriority priority,
        std::function<bool(const Event&)> filter
    ) {
        std::lock_guard<std::mutex> lock(mutex_);

        auto handle = next_handle_++;
        auto type = std::type_index(typeid(Event));

        auto handler = std::make_unique<detail::Handler<Event>>(
            std::move(callback),
            priority,
            handle,
            std::move(filter)
        );

        handlers_[type].push_back(std::move(handler));
        needs_sort_[type] = true;

        return handle;
    }

    mutable std::mutex mutex_;
    std::unordered_map<std::type_index, std::vector<std::unique_ptr<detail::HandlerBase>>> handlers_;
    std::unordered_map<std::type_index, bool> needs_sort_;
    SubscriptionHandle next_handle_;

    template<typename Event>
    friend class ScopedSubscription;
};

// ScopedSubscription implementation
template<typename Event>
ScopedSubscription<Event>::~ScopedSubscription() {
    if (active_) {
        unsubscribe();
    }
}

template<typename Event>
void ScopedSubscription<Event>::unsubscribe() {
    if (bus_ && active_) {
        bus_->unsubscribe<Event>(handle_);
        active_ = false;
    }
}

} // namespace events
