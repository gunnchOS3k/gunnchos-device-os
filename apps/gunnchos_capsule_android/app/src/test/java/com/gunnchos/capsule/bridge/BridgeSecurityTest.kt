package com.gunnchos.capsule.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class BridgeSecurityTest {
    @Test
    fun appassetsOriginAllowed() {
        val raw =
            """{"id":"1","capability":"battery","origin":"https://appassets.androidplatform.net"}"""
        val (obj, err) = BridgeSecurity.validateRequest(raw)
        assertNull(err)
        assertNotNull(obj)
        assertEquals("battery", obj!!.getString("capability"))
    }

    @Test
    fun fileOriginRejected() {
        val raw =
            """{"id":"1","capability":"battery","origin":"file:///android_asset/shell/index.html"}"""
        val (obj, err) = BridgeSecurity.validateRequest(raw)
        assertNull(obj)
        assertEquals("origin_rejected", err)
    }

    @Test
    fun lookalikeOriginRejected() {
        val raw =
            """{"id":"1","capability":"battery","origin":"https://appassets.androidplatform.net.evil.example"}"""
        val (obj, err) = BridgeSecurity.validateRequest(raw)
        assertNull(obj)
        assertEquals("origin_rejected", err)
    }

    @Test
    fun subdomainLookalikeRejected() {
        assertFalse(BridgeSchemas.isOriginAllowed("https://evil.appassets.androidplatform.net"))
        assertFalse(BridgeSchemas.isOriginAllowed("https://appassets.androidplatform.net.attacker.test"))
        assertTrue(BridgeSchemas.isOriginAllowed("https://appassets.androidplatform.net"))
    }

    @Test
    fun unknownCapabilityRejected() {
        val raw =
            """{"id":"1","capability":"eval_all","origin":"https://appassets.androidplatform.net"}"""
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
            """{"id":"1","capability":"battery","origin":"https://appassets.androidplatform.net","payload":{"eval":"1+1"}}"""
        val (obj, err) = BridgeSecurity.validateRequest(raw)
        assertNull(obj)
        assertEquals("forbidden_payload_key", err)
    }

    @Test
    fun shellReadyCapabilityAllowlisted() {
        assertTrue("shell_ready" in BridgeSchemas.ALLOWED_CAPABILITIES)
        assertTrue("shell_boot_stage" in BridgeSchemas.ALLOWED_CAPABILITIES)
        assertTrue("shell_fatal" in BridgeSchemas.ALLOWED_CAPABILITIES)
    }

    @Test
    fun gamesListCapabilityAllowlisted() {
        assertTrue("games_list" in BridgeSchemas.ALLOWED_CAPABILITIES)
        assertTrue("games_launch" in BridgeSchemas.ALLOWED_CAPABILITIES)
        assertTrue("waike_launch" in BridgeSchemas.ALLOWED_CAPABILITIES)
        assertTrue("gunnchai_launch" in BridgeSchemas.ALLOWED_CAPABILITIES)
    }

    @Test
    fun okEnvelope() {
        val out = BridgeSecurity.ok("abc", mapOf("x" to 1).toString())
        assertTrue(out.contains("\"ok\":true"))
        assertTrue(out.contains("abc"))
    }
}
