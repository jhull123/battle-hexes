class EventBus {
  constructor() {
    this.events = {};
  }

  on(event, listener) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(listener);
  }

  emit(event, ...args) {
    if (this.events[event]) {
      for (const listener of this.events[event]) {
        listener(...args);
      }
    }
  }
}

export const eventBus = new EventBus();