package com.hugalde.academicassistant.ui

import com.hugalde.academicassistant.data.ChatRepository
import com.hugalde.academicassistant.data.ChatResponse
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

private class FakeRepository(var result: Result<ChatResponse>) : ChatRepository {
    var calls = 0
    override suspend fun send(sessionId: String, message: String): Result<ChatResponse> {
        calls++
        return result
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class ChatViewModelTest {

    @Before
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun `successful send adds user and assistant messages`() {
        val repo = FakeRepository(Result.success(ChatResponse("You have 240 hours left.", listOf("get_social_service_status"))))
        val vm = ChatViewModel(repo, sessionId = "test")

        vm.send("  social service?  ")

        val state = vm.state.value
        assertEquals(listOf("social service?", "You have 240 hours left."), state.messages.map { it.text })
        assertEquals(listOf(true, false), state.messages.map { it.fromUser })
        assertEquals(listOf("get_social_service_status"), state.messages.last().toolsUsed)
        assertFalse(state.isLoading)
        assertNull(state.error)
    }

    @Test
    fun `failed send keeps the user message and reports an error`() {
        val vm = ChatViewModel(FakeRepository(Result.failure(RuntimeException("offline"))), sessionId = "test")

        vm.send("hello")

        assertEquals(1, vm.state.value.messages.size)
        assertNotNull(vm.state.value.error)
        assertFalse(vm.state.value.isLoading)
    }

    @Test
    fun `blank messages are ignored`() {
        val repo = FakeRepository(Result.success(ChatResponse("x")))
        val vm = ChatViewModel(repo, sessionId = "test")

        vm.send("   ")

        assertEquals(0, repo.calls)
        assertEquals(emptyList<ChatMessage>(), vm.state.value.messages)
    }

    @Test
    fun `dismissError clears the error`() {
        val vm = ChatViewModel(FakeRepository(Result.failure(RuntimeException("offline"))), sessionId = "test")
        vm.send("hello")

        vm.dismissError()

        assertNull(vm.state.value.error)
    }
}
