/** Web Crypto helpers for encrypted workspace prototype — not OS full-disk encryption. */

export const ENCRYPTION_CLAIM =
  'prototype encrypted workspace, not OS full-disk encryption'

export const PBKDF2_ITERATIONS = 100_000
export const SALT_BYTES = 16
export const IV_BYTES = 12

export interface EncryptedEnvelope {
  version: 1
  claim: typeof ENCRYPTION_CLAIM
  algorithm: 'AES-GCM'
  kdf: 'PBKDF2-SHA256'
  kdfIterations: number
  salt: string
  iv: string
  ciphertext: string
  exportedAt: string
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = ''
  bytes.forEach(b => {
    binary += String.fromCharCode(b)
  })
  return btoa(binary)
}

function base64ToBytes(base64: string): Uint8Array {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i)
  }
  return bytes
}

export function generateSalt(): Uint8Array {
  return crypto.getRandomValues(new Uint8Array(SALT_BYTES))
}

export function generateIv(): Uint8Array {
  return crypto.getRandomValues(new Uint8Array(IV_BYTES))
}

export async function deriveKey(
  passphrase: string,
  salt: Uint8Array,
): Promise<CryptoKey> {
  const enc = new TextEncoder()
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    enc.encode(passphrase),
    'PBKDF2',
    false,
    ['deriveKey'],
  )
  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt,
      iterations: PBKDF2_ITERATIONS,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  )
}

export async function encryptPayload(
  payload: unknown,
  passphrase: string,
): Promise<EncryptedEnvelope> {
  const salt = generateSalt()
  const iv = generateIv()
  const key = await deriveKey(passphrase, salt)
  const enc = new TextEncoder()
  const plaintext = enc.encode(JSON.stringify(payload))
  const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, plaintext)
  return {
    version: 1,
    claim: ENCRYPTION_CLAIM,
    algorithm: 'AES-GCM',
    kdf: 'PBKDF2-SHA256',
    kdfIterations: PBKDF2_ITERATIONS,
    salt: bytesToBase64(salt),
    iv: bytesToBase64(iv),
    ciphertext: bytesToBase64(new Uint8Array(ciphertext)),
    exportedAt: new Date().toISOString(),
  }
}

export async function decryptPayload<T>(
  envelope: EncryptedEnvelope,
  passphrase: string,
): Promise<T> {
  if (envelope.version !== 1) throw new Error('Unsupported envelope version')
  const salt = base64ToBytes(envelope.salt)
  const iv = base64ToBytes(envelope.iv)
  const ciphertext = base64ToBytes(envelope.ciphertext)
  const key = await deriveKey(passphrase, salt)
  try {
    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      ciphertext,
    )
    const dec = new TextDecoder()
    return JSON.parse(dec.decode(decrypted)) as T
  } catch {
    throw new Error('Decryption failed — wrong passphrase or corrupted data')
  }
}

export function envelopeContainsPlaintext(
  envelope: EncryptedEnvelope,
  needle: string,
): boolean {
  const serialized = JSON.stringify(envelope)
  return serialized.includes(needle)
}
