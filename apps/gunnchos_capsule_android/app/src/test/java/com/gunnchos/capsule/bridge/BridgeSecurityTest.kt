package com.gunnchos.capsule.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class BridgeSecurityTest {
    @Test
    fun allowlistedCapabilityAccepted() {
        val raw = """{"id":"1","capability":"battery","origin":"file:///android_asset/shell/index.html"}"""
        val (obj, err) = BridgeSecurity.validateRequest(raw)
        assertNull(err)
        assertNotNull(obj)
        assertEquals("battery", obj!!.getString("capability"))
    }

    @Test
    fun unknownCapabilityRejected() {
        val raw = """{"id":"1","capability":"eval_all","origin":"file:///android_asset/shell/index.html"}"""
        val (obj, err) = BridgeSecurity.validateRequest(raw)
        assertNull(obj)
        assertEquals("capability_not_allowlisted", err)
    }

    @Test
    fun foreignOriginRejected() {
        val raw = """{"id":"1","capability":"battery","origin":"https://evil.example"}"""
        val (obj, err) = BridgeSecurity.validateRequest(raw)
        assertNull(obj)
        assertEquals("origin_rejected", err)
    }

    @Test
    fun forbiddenPayloadKeyRejected() {
        val raw =
            """{"id":"1","capability":"battery","origin":"file:///android_asset/shell/index.html","payload":{"eval":"1+1"}}"""
        val (obj, err) = BridgeSecurity.validateRequest(raw)
        assertNull(obj)
        assertEquals("forbidden_payload_key", err)
    }

    @Test
    fun okEnvelope() {
        val out = BridgeSecurity.ok("abc", mapOf("x" to 1).toString())
        assertTrue(out.contains("\"ok\":true"))
        assertTrue(out.contains("abc"))
    }
}
