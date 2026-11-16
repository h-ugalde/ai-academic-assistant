package com.hugalde.academicassistant.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.hugalde.academicassistant.data.ChatRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID

data class ChatMessage(
    val id: Long,
    val text: String,
    val fromUser: Boolean,
    val toolsUsed: List<String> = emptyList(),
)

data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
)

class ChatViewModel(
    private val repository: ChatRepository,
    private val sessionId: String = UUID.randomUUID().toString(),
) : ViewModel() {

    private val _state = MutableStateFlow(ChatUiState())
    val state: StateFlow<ChatUiState> = _state.asStateFlow()

    private var nextId = 0L

    fun send(text: String) {
        val message = text.trim()
        if (message.isEmpty() || _state.value.isLoading) return

        _state.update {
            it.copy(
                messages = it.messages + ChatMessage(nextId++, message, fromUser = true),
                isLoading = true,
                error = null,
            )
        }

        viewModelScope.launch {
            repository.send(sessionId, message)
                .onSuccess { response ->
                    _state.update {
                        it.copy(
                            messages = it.messages + ChatMessage(
                                id = nextId++,
                                text = response.reply,
                                fromUser = false,
                                toolsUsed = response.toolsUsed,
                            ),
                            isLoading = false,
                        )
                    }
                }
                .onFailure {
                    _state.update {
                        it.copy(isLoading = false, error = "Couldn't reach the assistant. Check your connection and try again.")
                    }
                }
        }
    }

    fun dismissError() = _state.update { it.copy(error = null) }

    companion object {
        fun factory(repository: ChatRepository): ViewModelProvider.Factory = viewModelFactory {
            initializer { ChatViewModel(repository) }
        }
    }
}
