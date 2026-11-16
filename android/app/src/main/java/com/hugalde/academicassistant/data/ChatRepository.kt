package com.hugalde.academicassistant.data

import kotlin.coroutines.cancellation.CancellationException

interface ChatRepository {
    suspend fun send(sessionId: String, message: String): Result<ChatResponse>
}

class NetworkChatRepository(private val api: ChatApi) : ChatRepository {
    override suspend fun send(sessionId: String, message: String): Result<ChatResponse> =
        try {
            Result.success(api.chat(ChatRequest(sessionId, message)))
        } catch (e: CancellationException) {
            throw e // never swallow coroutine cancellation
        } catch (e: Exception) {
            Result.failure(e)
        }
}
