import { useMemo, useState } from 'react'

const SEED = ['essays/notes.txt', 'captures/readme.md']

export default function VaultSurface({
  offline,
  onError,
}: {
  offline?: boolean
  onError: (msg: string | null) => void
}) {
  const [files, setFiles] = useState<string[]>(SEED)
  const [query, setQuery] = useState('')
  const [trash, setTrash] = useState<string[]>([])

  const visible = useMemo(
    () => files.filter((f) => f.toLowerCase().includes(query.toLowerCase())),
    [files, query],
  )

  const create = () => {
    const name = `docs/note-${files.length + 1}.txt`
    setFiles((f) => [name, ...f])
    onError(null)
  }

  const remove = (path: string) => {
    setFiles((f) => f.filter((x) => x !== path))
    setTrash((t) => [path, ...t])
  }

  return (
    <section className="cx2-panel" aria-labelledby="cx2-vault-title">
      <h1 id="cx2-vault-title">Vault</h1>
      <p className="lead">Browse, search, trash, and restore files. Backup and free-space health stay local-first.</p>
      <div className="cx2-actions">
        <button type="button" className="cx2-action primary" onClick={create}>New file</button>
        <button
          type="button"
          className="cx2-action"
          onClick={() => onError(offline ? 'Backup queued offline' : null)}
        >
          Backup
        </button>
        <button
          type="button"
          className="cx2-action"
          disabled={trash.length === 0}
          onClick={() => {
            if (!trash[0]) return
            const [first, ...rest] = trash
            setTrash(rest)
            setFiles((f) => [first, ...f])
          }}
        >
          Restore trash
        </button>
      </div>
      <label htmlFor="vault-search">Search Vault</label>{' '}
      <input
        id="vault-search"
        className="cx2-field"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search files"
      />
      {visible.length === 0 ? (
        <div className="cx2-empty" role="status">No files yet — create one or save from an app.</div>
      ) : (
        <ul className="cx2-list" aria-label="Vault files">
          {visible.map((f) => (
            <li key={f} className="cx2-row">
              <span>{f}</span>
              <button type="button" className="cx2-action" onClick={() => remove(f)} aria-label={`Move ${f} to trash`}>
                Trash
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
