package com.hugalde.academicassistant.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ChatRequest(
    @SerialName("session_id") val sessionId: String,
    val message: String,
)

@Serializable
data class ChatResponse(
    val reply: String,
    @SerialName("tools_used") val toolsUsed: List<String> = emptyList(),
    val provider: String = "",
)
