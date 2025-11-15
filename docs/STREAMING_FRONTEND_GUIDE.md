# Frontend Integration Guide for Streaming Chat

## Overview
This guide shows how to integrate the new streaming chat endpoint (`/send-stream`) into your React Native frontend for real-time, token-by-token response display.

---

## Why Streaming?

**Before (Non-Streaming):**
```
User sends message → [3-5 seconds of blank screen] → Full response appears
```

**After (Streaming):**
```
User sends message → "Entiendo" (0.3s) → "que te" (0.4s) → "sientas así..." (0.5s)
```

**Result:** User perceives instant response, reduced anxiety.

---

## Implementation

### Option 1: EventSource (Web/React Native Web)

```typescript
// src/services/chatService.ts
import { EventSourcePolyfill } from 'event-source-polyfill';

interface StreamEvent {
  type: 'metadata' | 'chunk' | 'complete' | 'error';
  data: any;
}

export async function sendMessageStreaming(
  message: string,
  token: string,
  onChunk: (text: string) => void,
  onComplete: (data: { session: any; quick_replies: any[] }) => void,
  onError: (error: string) => void
): Promise<void> {
  
  const eventSource = new EventSourcePolyfill(
    `${API_BASE_URL}/api/v1/chat/send-stream`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      method: 'POST',
      body: JSON.stringify({ message })
    }
  );

  eventSource.onmessage = (event) => {
    const parsed: StreamEvent = JSON.parse(event.data);

    switch (parsed.type) {
      case 'metadata':
        // Optional: show strategy info (Q2, Q3, enfoque)
        console.log('Strategy:', parsed.data);
        break;

      case 'chunk':
        // Append text chunk to UI
        onChunk(parsed.data.text);
        break;

      case 'complete':
        // Finalize message, show quick replies
        onComplete(parsed.data);
        eventSource.close();
        break;

      case 'error':
        onError(parsed.data.message);
        eventSource.close();
        break;
    }
  };

  eventSource.onerror = (error) => {
    console.error('EventSource error:', error);
    onError('Error de conexión. Intenta nuevamente.');
    eventSource.close();
  };
}
```

### Option 2: Fetch with ReadableStream (React Native)

```typescript
// src/services/chatService.ts
export async function sendMessageStreaming(
  message: string,
  token: string,
  onChunk: (text: string) => void,
  onComplete: (data: any) => void,
  onError: (error: string) => void
): Promise<void> {
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/send-stream`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader!.read();
      
      if (done) break;

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE events
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // Keep incomplete event in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const eventData = JSON.parse(line.substring(6));

          if (eventData.type === 'chunk') {
            onChunk(eventData.data.text);
          } else if (eventData.type === 'complete') {
            onComplete(eventData.data);
          } else if (eventData.type === 'error') {
            onError(eventData.data.message);
          }
        }
      }
    }

  } catch (error) {
    console.error('Streaming error:', error);
    onError('Error de conexión. Intenta nuevamente.');
  }
}
```

---

## React Component Example

```tsx
// src/screens/ChatScreen.tsx
import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, FlatList, TouchableOpacity } from 'react-native';
import { sendMessageStreaming } from '../services/chatService';

interface Message {
  id: string;
  role: 'user' | 'model';
  text: string;
  isStreaming?: boolean;
}

export default function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [quickReplies, setQuickReplies] = useState<any[]>([]);
  const flatListRef = useRef<FlatList>(null);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    // Create placeholder for AI response
    const aiMessageId = (Date.now() + 1).toString();
    const aiMessage: Message = {
      id: aiMessageId,
      role: 'model',
      text: '',
      isStreaming: true
    };

    setMessages(prev => [...prev, aiMessage]);

    // Start streaming
    await sendMessageStreaming(
      userMessage.text,
      'YOUR_AUTH_TOKEN',
      
      // onChunk: append text to AI message
      (chunk: string) => {
        setMessages(prev => prev.map(msg => 
          msg.id === aiMessageId
            ? { ...msg, text: msg.text + chunk }
            : msg
        ));
      },

      // onComplete: finalize message, show quick replies
      (data) => {
        setMessages(prev => prev.map(msg => 
          msg.id === aiMessageId
            ? { ...msg, isStreaming: false }
            : msg
        ));

        if (data.quick_replies) {
          setQuickReplies(data.quick_replies);
        }

        // Auto-scroll to bottom
        setTimeout(() => flatListRef.current?.scrollToEnd(), 100);
      },

      // onError
      (error) => {
        setMessages(prev => prev.map(msg => 
          msg.id === aiMessageId
            ? { ...msg, text: '❌ ' + error, isStreaming: false }
            : msg
        ));
      }
    );
  };

  return (
    <View style={{ flex: 1 }}>
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <View style={{
            alignSelf: item.role === 'user' ? 'flex-end' : 'flex-start',
            backgroundColor: item.role === 'user' ? '#007AFF' : '#E5E5EA',
            padding: 12,
            margin: 8,
            borderRadius: 16,
            maxWidth: '80%'
          }}>
            <Text style={{
              color: item.role === 'user' ? 'white' : 'black'
            }}>
              {item.text}
            </Text>
            {item.isStreaming && (
              <Text style={{ fontSize: 10, marginTop: 4 }}>✍️ escribiendo...</Text>
            )}
          </View>
        )}
      />

      {/* Quick Replies */}
      {quickReplies.length > 0 && (
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', padding: 8 }}>
          {quickReplies.map((reply, idx) => (
            <TouchableOpacity
              key={idx}
              onPress={() => {
                setInput(reply.value);
                setQuickReplies([]);
              }}
              style={{
                backgroundColor: '#F0F0F0',
                padding: 8,
                margin: 4,
                borderRadius: 12
              }}
            >
              <Text>{reply.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Input */}
      <View style={{ flexDirection: 'row', padding: 8 }}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="Escribe tu mensaje..."
          style={{
            flex: 1,
            borderWidth: 1,
            borderColor: '#CCC',
            borderRadius: 20,
            paddingHorizontal: 16,
            paddingVertical: 8
          }}
        />
        <TouchableOpacity onPress={handleSendMessage}>
          <Text style={{ fontSize: 24, marginLeft: 8 }}>➤</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
```

---

## Fallback Strategy

If streaming fails (network issues, old browsers), automatically fallback to non-streaming:

```typescript
export async function sendMessage(message: string, token: string): Promise<any> {
  try {
    // Try streaming first
    return await sendMessageStreaming(...);
  } catch (error) {
    console.warn('Streaming failed, using non-streaming fallback');
    
    // Fallback to traditional POST /send
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/send`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });

    return await response.json();
  }
}
```

---

## Testing

### Manual Test
```bash
# Terminal
curl -X POST http://localhost:8000/api/v1/chat/send-stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Estoy frustrado con mi ensayo"}' \
  --no-buffer

# Expected output (streaming):
data: {"type":"metadata","data":{"Q2":"A","Q3":"↓","enfoque":"promocion_eager"}}

data: {"type":"chunk","data":{"text":"Entiendo"}}

data: {"type":"chunk","data":{"text":" que te sientas"}}

data: {"type":"chunk","data":{"text":" frustrado..."}}

data: {"type":"complete","data":{"session":{...},"quick_replies":[...]}}
```

### Unit Test
```typescript
// __tests__/chatService.test.ts
import { sendMessageStreaming } from '../services/chatService';

test('streaming returns chunks progressively', async () => {
  const chunks: string[] = [];
  
  await sendMessageStreaming(
    'test message',
    'test_token',
    (chunk) => chunks.push(chunk),
    () => {},
    () => {}
  );

  expect(chunks.length).toBeGreaterThan(0);
  expect(chunks.join('')).toContain('Flou');
});
```

---

## Performance Tips

1. **Debounce rapid messages**: Prevent users from sending 10 messages in 1 second
   ```typescript
   const [isSending, setIsSending] = useState(false);
   
   if (isSending) return; // Block duplicate sends
   setIsSending(true);
   await sendMessageStreaming(...);
   setIsSending(false);
   ```

2. **Cancel previous stream**: If user sends new message before previous completes
   ```typescript
   const abortControllerRef = useRef<AbortController>();
   
   // In sendMessage:
   abortControllerRef.current?.abort();
   abortControllerRef.current = new AbortController();
   
   await fetch(..., { signal: abortControllerRef.current.signal });
   ```

3. **Optimize re-renders**: Use `React.memo` for message components
   ```typescript
   const MessageBubble = React.memo(({ message }: { message: Message }) => (
     <View>...</View>
   ));
   ```

---

## Troubleshooting

### Issue: "No chunks received"
**Solution:** Check that backend is using `stream=True` in Gemini call

### Issue: "EventSource not working in React Native"
**Solution:** Use fetch + ReadableStream instead (Option 2 above)

### Issue: "Messages appear out of order"
**Solution:** Use message IDs to ensure correct ordering

### Issue: "High memory usage"
**Solution:** Limit message history to last 50 messages
```typescript
const MAX_MESSAGES = 50;
setMessages(prev => [...prev, newMsg].slice(-MAX_MESSAGES));
```

---

## Next Steps

1. Implement streaming in your frontend using Option 2 (fetch + ReadableStream)
2. Add loading indicator while first chunk arrives
3. Test with slow network (throttle to 3G in DevTools)
4. Add error handling and retry logic
5. Monitor streaming success rate in analytics

---

## Additional Resources

- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [ReadableStream API](https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream)
- [React Native Fetch](https://reactnative.dev/docs/network)
