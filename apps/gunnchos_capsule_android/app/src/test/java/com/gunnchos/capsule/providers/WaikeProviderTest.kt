package com.gunnchos.capsule.providers

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class WaikeProviderTest {
    @Test
    fun allowsHttpsAndLoopbackHttpOnly() {
        assertTrue(WaikeProvider.isAllowedHandoffUrl("https://hub.example.edu/"))
        assertTrue(WaikeProvider.isAllowedHandoffUrl("http://127.0.0.1:1420/"))
        assertTrue(WaikeProvider.isAllowedHandoffUrl("http://localhost:1420/"))
        assertFalse(WaikeProvider.isAllowedHandoffUrl("http://evil.example/"))
        assertFalse(WaikeProvider.isAllowedHandoffUrl(""))
        assertFalse(WaikeProvider.isAllowedHandoffUrl("ftp://127.0.0.1/"))
    }
}
