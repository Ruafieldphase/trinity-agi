// Chat message type definition
export type Layer = 'conscious' | 'unconscious' | 'koa' | 'unified' | 'trinity';

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    layer?: Layer;
    timestamp: number;
    imageUrl?: string;
    audioUrl?: string;
}

// In-memory chat store
class ChatStore {
    private messages: ChatMessage[] = [];
    private listeners: Set<() => void> = new Set();

    addMessage(message: Omit<ChatMessage, 'id' | 'timestamp'>) {
        const newMessage: ChatMessage = {
            ...message,
            id: crypto.randomUUID(),
            timestamp: Date.now()
        };

        this.messages.push(newMessage);
        this.notifyListeners();
        return newMessage;
    }

    getMessages(): ChatMessage[] {
        return [...this.messages];
    }

    subscribe(listener: () => void) {
        this.listeners.add(listener);
        return () => {
            this.listeners.delete(listener);
        };
    }

    private notifyListeners() {
        this.listeners.forEach(listener => listener());
    }

    clear() {
        this.messages = [];
        this.notifyListeners();
    }
}

// Export singleton instance
export const chatStore = new ChatStore();
