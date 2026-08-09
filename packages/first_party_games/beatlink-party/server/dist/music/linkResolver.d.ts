import type { LinkResolveResult, ProviderAuthStatus } from '@beatlink/shared';
export declare function getProviderAuthStatus(): ProviderAuthStatus;
/**
 * Resolve a pasted music link to metadata + playback eligibility.
 * Uses public oEmbed endpoints only (no audio download/streaming/rip).
 */
export declare function resolveLink(url: string): Promise<LinkResolveResult>;
//# sourceMappingURL=linkResolver.d.ts.map