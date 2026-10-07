package com.aigestion.mobile.pairing

import java.security.MessageDigest
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/**
 * PC <-> Pixel challenge-response pairing.
 *
 * The PC posts a challenge; the phone computes
 * HMAC-SHA256(challenge, PIXEL_TOKEN) and returns it.
 * The shared secret (PIXEL_TOKEN) is NEVER sent over the wire.
 * See skills/connectors/android/pairing.py for the PC side.
 */
object PairingManager {
    private const val HMAC_ALGORITHM = "HmacSHA256"

    /** Hex-encoded HMAC-SHA256 of the challenge using the shared token. */
    fun sign(challenge: String, token: String): String {
        val keySpec = SecretKeySpec(token.toByteArray(), HMAC_ALGORITHM)
        val mac = Mac.getInstance(HMAC_ALGORITHM)
        mac.init(keySpec)
        val raw = mac.doFinal(challenge.toByteArray())
        return raw.joinToString("") { "%02x".format(it) }
    }

    /** Fast fingerprint of a challenge for display (first 16 hex chars). */
    fun fingerprint(challenge: String): String =
        sha256(challenge).take(16)

    private fun sha256(input: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(input.toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
