package com.hugalde.academicassistant

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.material3.MaterialTheme
import com.hugalde.academicassistant.data.ApiFactory
import com.hugalde.academicassistant.data.NetworkChatRepository
import com.hugalde.academicassistant.ui.ChatScreen
import com.hugalde.academicassistant.ui.ChatViewModel

class MainActivity : ComponentActivity() {

    private val viewModel: ChatViewModel by viewModels {
        ChatViewModel.factory(NetworkChatRepository(ApiFactory.create(BuildConfig.BASE_URL)))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MaterialTheme {
                ChatScreen(viewModel)
            }
        }
    }
}
