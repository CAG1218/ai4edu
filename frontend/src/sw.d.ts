/**
 * Service Worker 类型声明
 * 为 src/sw.ts 提供完整的类型支持
 */

/// <reference lib="webworker" />

/** Workbox 插件接口 */
interface WorkboxPlugin {
  cacheWillUpdate?: (options: { request: Request; response: Response }) => Promise<Response | undefined>
  cacheDidUpdate?: (options: { cacheName: string; oldResponse: Response | undefined; newResponse: Response; request: Request }) => Promise<void>
  cachedResponseWillBeUsed?: (options: { cacheName: string; request: Request; matchOptions?: CacheQueryOptions; cachedResponse: Response | undefined }) => Promise<Response | undefined>
  requestWillFetch?: (options: { request: Request }) => Promise<Request>
  fetchDidSucceed?: (options: { request: Request; response: Response }) => Promise<Response>
  fetchDidFail?: (options: { request: Request; error: Error }) => Promise<void>
  handlerDidError?: (options: { request: Request; error: Error }) => Promise<Response>
  handlerWillStart?: (options: { request: Request }) => Promise<void>
  handlerDidRespond?: (options: { response: Response }) => Promise<void>
  handlerDidComplete?: (options: { request: Request; response: Response; error?: Error }) => Promise<void>
}

declare module 'workbox-precaching' {
  export function precacheAndRoute(entries: string[]): void
  export function cleanupOutdatedCaches(): void
}

declare module 'workbox-routing' {
  export function registerRoute(
    match: (options: { url: URL; request: Request; event: FetchEvent }) => boolean,
    handler: any
  ): void
}

declare module 'workbox-strategies' {
  export class NetworkFirst {
    constructor(options?: {
      cacheName?: string
      networkTimeoutSeconds?: number
      plugins?: WorkboxPlugin[]
    })
  }
  export class CacheFirst {
    constructor(options?: {
      cacheName?: string
      plugins?: WorkboxPlugin[]
    })
  }
  export class StaleWhileRevalidate {
    constructor(options?: {
      cacheName?: string
      plugins?: WorkboxPlugin[]
    })
  }
}

declare module 'workbox-expiration' {
  export class ExpirationPlugin {
    constructor(options?: {
      maxEntries?: number
      maxAgeSeconds?: number
    })
  }
}

declare module 'workbox-cacheable-response' {
  export class CacheableResponsePlugin {
    constructor(options?: {
      statuses?: number[]
    })
  }
}

declare module 'workbox-background-sync' {
  export class Queue {
    constructor(name: string, options?: {
      onSync?: (options: { queue: Queue }) => Promise<void>
    })
    pushRequest(options: { request: Request }): Promise<void>
    shiftRequest(): Promise<QueueEntry | undefined>
    unshiftRequest(entry: QueueEntry): Promise<void>
  }

  interface QueueEntry {
    request: Request
    timestamp: number
    metadata?: Record<string, unknown>
  }
}
