import { useEffect, useState } from 'react'
import Icon from '../design/icons/Icon'
import { EmptyState, SurfaceHeader } from '../design/primitives/SurfaceChrome'
import {
  deleteCreationDoc,
  listCreationDocs,
  newCreationId,
  saveCreationDoc,
  type CreationDoc,
} from '../platform/creationStore'
import { recordContinuity } from '../platform/continuityStore'

export default function CreationSurface({
  onError,
}: {
  onError: (msg: string | null) => void
}) {
  const [docs, setDocs] = useState<CreationDoc[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')

  const refresh = () => setDocs(listCreationDocs())

  useEffect(() => {
    refresh()
  }, [])

  const select = (doc: CreationDoc) => {
    setActiveId(doc.id)
    setTitle(doc.title)
    setBody(doc.body)
  }

  const createNew = () => {
    const id = newCreationId()
    setActiveId(id)
    setTitle('Untitled note')
    setBody('')
    onError(null)
  }

  const save = () => {
    if (!activeId) {
      onError('Create or open a note first')
      return
    }
    const saved = saveCreationDoc({ id: activeId, title, body })
    recordContinuity({
      id: `creation-${saved.id}`,
      domain: 'creation',
      title: saved.title,
      subtitle: 'Creation note',
      surface: 'creation',
      payload: { docId: saved.id },
    })
    refresh()
    onError(null)
  }

  const remove = () => {
    if (!activeId) return
    deleteCreationDoc(activeId)
    setActiveId(null)
    setTitle('')
    setBody('')
    refresh()
    onError(null)
  }

  return (
    <section className="cx2-panel vxp-creation" aria-labelledby="cx2-creation-title" data-testid="creation-surface">
      <SurfaceHeader
        titleId="cx2-creation-title"
        title="Creation"
        lead="Create, edit, and save local notes on Pixel. Heavy studio workflows can escalate later — this domain must exist."
      />

      <div className="vxp-creation-layout">
        <aside aria-label="Notes">
          <button type="button" className="cx2-action primary" onClick={createNew}>
            <Icon name="file" size={16} />
            <span>New note</span>
          </button>
          {docs.length === 0 ? (
            <EmptyState icon="empty" title="No notes yet" detail="Create a note to start. We will not invent drafts." />
          ) : (
            <ul className="cx2-list" aria-label="Saved notes">
              {docs.map((d) => (
                <li key={d.id} className="cx2-row">
                  <button type="button" className="vxp-space-card" onClick={() => select(d)}>
                    <Icon name="file" size={18} />
                    <span className="vxp-space-label">{d.title}</span>
                    <span className="vxp-space-purpose">{new Date(d.updatedAt).toLocaleString()}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className="vxp-creation-editor" role="region" aria-label="Editor">
          {!activeId ? (
            <EmptyState icon="file" title="Select or create a note" detail="Saved notes stay on this device." />
          ) : (
            <>
              <label htmlFor="creation-title">Title</label>
              <input
                id="creation-title"
                className="cx2-field"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                data-testid="creation-title"
              />
              <label htmlFor="creation-body">Body</label>
              <textarea
                id="creation-body"
                className="cx2-field"
                style={{ minHeight: 200 }}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                data-testid="creation-body"
              />
              <div className="cx2-actions">
                <button type="button" className="cx2-action primary" onClick={save} data-testid="creation-save">
                  <Icon name="backup" size={16} />
                  <span>Save</span>
                </button>
                <button type="button" className="cx2-action" onClick={remove}>
                  <Icon name="trash" size={16} />
                  <span>Delete</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  )
}
