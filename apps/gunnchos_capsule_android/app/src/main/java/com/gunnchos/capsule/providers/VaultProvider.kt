package com.gunnchos.capsule.providers

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * Vault via app-private storage + SAF/MediaStore mediation hooks.
 * No MANAGE_EXTERNAL_STORAGE in pilot.
 */
class VaultProvider(private val context: Context) {
    private val root: File
        get() = File(context.filesDir, "vault").also { if (!it.exists()) it.mkdirs() }

    fun handle(capability: String, payload: JSONObject?): JSONObject {
        val p = payload ?: JSONObject()
        return when (capability) {
            "vault_list", "files" -> list(p)
            "vault_op" -> op(p)
            "file_picker", "document_open" ->
                ok(
                    JSONObject()
                        .put("mode", "SAF")
                        .put("note", "Use Android document picker via host Activity result (pilot stub returns private list)"),
                )
            "document_create" -> create(p)
            "downloads" ->
                ok(JSONObject().put("dir", File(context.getExternalFilesDir(null), "Download").absolutePath))
            else -> fail("vault_unknown")
        }
    }

    private fun list(payload: JSONObject): JSONObject {
        val q = payload.optString("q", "").lowercase()
        val files = root.walkTopDown().filter { it.isFile }.map { f ->
            JSONObject()
                .put("id", f.relativeTo(root).path)
                .put("name", f.name)
                .put("size", f.length())
                .put("backend", "APP_PRIVATE")
        }.filter {
            q.isBlank() || it.getString("name").lowercase().contains(q)
        }.toList()
        return ok(JSONObject().put("files", JSONArray(files)).put("backend", "APP_PRIVATE+SAF"))
    }

    private fun create(payload: JSONObject): JSONObject {
        val name = sanitize(payload.optString("name", "note.txt"))
        val content = payload.optString("content", "")
        val dest = File(root, name)
        dest.parentFile?.mkdirs()
        dest.writeText(content)
        return ok(JSONObject().put("id", name).put("created", true))
    }

    private fun op(payload: JSONObject): JSONObject {
        val action = payload.optString("action", "")
        val id = sanitize(payload.optString("id", ""))
        val file = File(root, id)
        return when (action) {
            "create", "edit" -> {
                val content = payload.optString("content", if (file.exists()) file.readText() else "")
                file.parentFile?.mkdirs()
                file.writeText(content)
                ok(JSONObject().put("id", id).put("saved", true))
            }
            "delete" -> {
                if (file.exists()) file.delete()
                ok(JSONObject().put("deleted", true))
            }
            "rename", "move" -> {
                val to = sanitize(payload.optString("to", ""))
                val dest = File(root, to)
                dest.parentFile?.mkdirs()
                file.renameTo(dest)
                ok(JSONObject().put("id", to))
            }
            "share" -> {
                if (!file.exists()) return fail("not_found")
                val uri: Uri = FileProvider.getUriForFile(
                    context,
                    "${context.packageName}.files",
                    file,
                )
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_STREAM, uri)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                context.startActivity(Intent.createChooser(intent, "Share Vault file").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                ok(JSONObject().put("shared", true))
            }
            "import", "export" ->
                ok(JSONObject().put("mode", "SAF").put("note", "Owner completes SAF pick/create on device"))
            "reopen", "read" -> {
                if (!file.exists()) return fail("not_found")
                ok(JSONObject().put("id", id).put("content", file.readText()))
            }
            else -> fail("unknown_vault_op")
        }
    }

    private fun sanitize(name: String): String {
        val cleaned = name.replace("..", "").trim('/').trim()
        if (cleaned.isBlank()) throw IllegalArgumentException("invalid_path")
        return cleaned
    }

    private fun ok(result: JSONObject) = JSONObject().put("ok", true).put("result", result)
    private fun fail(msg: String) = JSONObject().put("ok", false).put("error", msg)
}
