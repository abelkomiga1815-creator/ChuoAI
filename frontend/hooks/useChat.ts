import { create } from 'zustand';
import { api } from '@/lib/api';
import type { Message, Source } from '@/types';

interface ChatState {
  messages: Message[];
  conversationId: string | null;
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;

  sendMessage: (content: string) => Promise<string | null>;
  regenerate: () => Promise<string | null>;
  setConversation: (id: string, messages: Message[]) => void;
  clearChat: () => void;
  stopGeneration: () => void;
}

let abortController: AbortController | null = null;

function getPreferredLanguage(): string {
  if (typeof window === 'undefined') return 'auto';
  return localStorage.getItem('chuoai-language') || 'auto';
}

async function streamAssistantReply(
  content: string,
  conversationId: string | null,
  set: (partial: Partial<ChatState> | ((state: ChatState) => Partial<ChatState>)) => void,
  get: () => ChatState
): Promise<string | null> {
  const assistantMessage: Message = {
    id: `temp-assistant-${Date.now()}`,
    role: 'ASSISTANT',
    content: '',
    createdAt: new Date().toISOString(),
  };

  set(({ messages }) => ({
    messages: [...messages, assistantMessage],
    isLoading: true,
    isStreaming: true,
    error: null,
  }));

  try {
    const controller = new AbortController();
    abortController = controller;

    const { conversationId: newConvId, sources } = await api.streamChat(
      content,
      conversationId || undefined,
      getPreferredLanguage(),
      (chunk) => {
        set(({ messages }) => {
          const updatedMessages = [...messages];
          const lastIndex = updatedMessages.length - 1;
          if (updatedMessages[lastIndex]?.role === 'ASSISTANT') {
            updatedMessages[lastIndex] = {
              ...updatedMessages[lastIndex],
              content: updatedMessages[lastIndex].content + chunk.content,
            };
          }
          return { messages: updatedMessages };
        });
      },
      controller.signal
    );
    abortController = null;

    set(({ messages }) => {
      const updatedMessages = [...messages];
      const lastIndex = updatedMessages.length - 1;
      if (updatedMessages[lastIndex]?.role === 'ASSISTANT') {
        updatedMessages[lastIndex] = {
          ...updatedMessages[lastIndex],
          sources,
        };
      }
      return {
        messages: updatedMessages,
        conversationId: newConvId,
        isLoading: false,
        isStreaming: false,
      };
    });
    return newConvId;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      set({ isLoading: false, isStreaming: false, error: null });
      return null;
    }
    set({
      isLoading: false,
      isStreaming: false,
      error: error instanceof Error ? error.message : 'An error occurred',
    });
    return null;
  } finally {
    abortController = null;
  }
}

export const useChat = create<ChatState>((set, get) => ({
  messages: [],
  conversationId: null,
  isLoading: false,
  isStreaming: false,
  error: null,

  sendMessage: async (content: string) => {
    const { conversationId } = get();

    const userMessage: Message = {
      id: `temp-user-${Date.now()}`,
      role: 'USER',
      content,
      createdAt: new Date().toISOString(),
    };

    set(({ messages }) => ({
      messages: [...messages, userMessage],
      isLoading: true,
      isStreaming: true,
      error: null,
    }));

    return streamAssistantReply(content, conversationId, set, get);
  },

  regenerate: async () => {
    const { messages, conversationId } = get();
    if (!messages.length) return null;

    const messagesWithoutLastAssistant = [...messages];
    const last = messagesWithoutLastAssistant[messagesWithoutLastAssistant.length - 1];
    if (last?.role !== 'ASSISTANT') return null;
    messagesWithoutLastAssistant.pop();

    const lastUser = [...messagesWithoutLastAssistant]
      .reverse()
      .find((m) => m.role === 'USER');
    if (!lastUser) return null;

    set({
      messages: messagesWithoutLastAssistant,
      isLoading: true,
      isStreaming: true,
      error: null,
    });

    return streamAssistantReply(lastUser.content, conversationId, set, get);
  },

  setConversation: (id: string, messages: Message[]) => {
    set({
      conversationId: id,
      messages,
      isLoading: false,
      isStreaming: false,
      error: null,
    });
  },

  clearChat: () => {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    set({
      messages: [],
      conversationId: null,
      isLoading: false,
      isStreaming: false,
      error: null,
    });
  },

  stopGeneration: () => {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    set({ isStreaming: false, isLoading: false });
  },
}));