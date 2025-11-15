declare module 'eventsource' {
  export default class EventSource {
    constructor(url: string, eventSourceInitDict?: any);
    onopen: ((this: EventSource, ev: any) => any) | null;
    onmessage: ((this: EventSource, ev: { data: string }) => any) | null;
    onerror: ((this: EventSource, ev: any) => any) | null;
    close(): void;
  }
  export interface MessageEvent { data: string }
}
